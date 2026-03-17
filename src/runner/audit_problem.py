"""Per-problem audit pipeline for AgentAIMO.

Given one JSONL record from the submission data, runs all Phase 1–3
modules to produce a typed AuditRecord.

Pipeline per attempt:
  1. SolutionParser   → SolutionTrace (steps + extracted answer)
  2. ArithmeticChecker → arithmetic VerificationResult list  
  3. AnswerValidator  → canonical ExtractionResult
  4. FlawDetector     → CritiqueReport (offline flaw codes)
  5. AnswerSelector   → best answer + confidence across all attempts

Phase 3 implementation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from src.models.critique import CritiqueReport
from src.models.solution import SolutionTrace
from src.models.verification import ConfidenceLevel, VerificationReport
from src.critique.flaw_detector import FlawDetector
from src.verification.answer_validator import AnswerValidator, ExtractionResult
from src.verification.arithmetic_checker import ArithmeticChecker
from src.verification.pipeline import VerificationPipeline, PipelineResult
from src.solver.answer_selector import AnnotatedSolution, AnswerSelector


# ---------------------------------------------------------------------------
# Typed output schema — matches FORWARD_PLAN_v2.md §Phase 3
# ---------------------------------------------------------------------------

@dataclass
class AttemptAudit:
    """Audit result for a single attempt within a problem."""
    attempt_id: int
    canonical_answer: Optional[int]          # Extracted integer answer
    extraction_pattern: str                  # Which pattern succeeded
    extraction_confidence: str               # ConfidenceLevel value string
    verifier_results: list[dict]             # [{kind, status, confidence}]
    verification_report: VerificationReport
    critique_report: CritiqueReport
    flaw_codes: list[str]
    flaw_severity_total: int
    is_clean_trace: bool                     # No severity >= 3 flaws


@dataclass
class AuditRecord:
    """Full audit result for one problem record from the JSONL.

    Matches the FORWARD_PLAN_v2.md output schema:
    {
      "problem_id": ..., "attempt_id": ..., "canonical_answer": ...,
      "verifier_results": [...], "confidence_score": ...,
      "selected": ..., "gold_answer": ..., "correct": ...
    }
    """
    problem_id: str
    problem_text: str
    ground_truth: Optional[int]              # From GROUND_TRUTH map (may be None)
    num_attempts: int
    attempts: list[AttemptAudit] = field(default_factory=list)

    # Selected answer (from AnswerSelector)
    selected_answer: Optional[int] = None
    selection_reason: str = ""
    confidence_score: float = 0.0

    # Correctness (only valid when ground_truth is not None)
    correct: Optional[bool] = None

    # Aggregate flaw statistics
    total_flaws: int = 0
    unique_flaw_codes: list[str] = field(default_factory=list)
    clean_attempt_count: int = 0

    # Runtime
    audit_duration_seconds: float = 0.0

    def to_jsonl_dict(self) -> dict:
        """Serialize to the FORWARD_PLAN_v2 output schema."""
        return {
            "problem_id": self.problem_id,
            "ground_truth": self.ground_truth,
            "selected_answer": self.selected_answer,
            "selection_reason": self.selection_reason,
            "confidence_score": round(self.confidence_score, 4),
            "correct": self.correct,
            "num_attempts": self.num_attempts,
            "clean_attempts": self.clean_attempt_count,
            "total_flaws": self.total_flaws,
            "unique_flaw_codes": sorted(self.unique_flaw_codes),
            "attempt_answers": [
                {
                    "attempt_id": a.attempt_id,
                    "canonical_answer": a.canonical_answer,
                    "extraction_pattern": a.extraction_pattern,
                    "extraction_confidence": a.extraction_confidence,
                    "flaw_codes": a.flaw_codes,
                    "flaw_severity_total": a.flaw_severity_total,
                }
                for a in self.attempts
            ],
            "audit_duration_seconds": round(self.audit_duration_seconds, 3),
        }


# ---------------------------------------------------------------------------
# Ground truth (same as ablation_extraction.py)
# ---------------------------------------------------------------------------

GROUND_TRUTH: dict[str, int] = {
    "aime_2024_1":    204,
    "aime_2024_2":     25,
    "aime_2024_3":    809,   # Note: ablation confirmed actual answer is 809
    "aime_2024_4":     65,
    "aime_2024_5":    104,
    "aime_2023_1":    907,
    "aime_2023_10":   772,
    "putnam_2023_a1":  18,
}


# ---------------------------------------------------------------------------
# Per-problem auditor
# ---------------------------------------------------------------------------

_validator  = AnswerValidator()
_arithmetic  = ArithmeticChecker()
_pipeline   = VerificationPipeline()
_flaw_det   = FlawDetector()
_selector   = AnswerSelector()


def audit_problem(record: dict) -> AuditRecord:
    """Audit one JSONL problem record through the full Phase 1–3 pipeline.

    Args:
        record: One dict loaded from research_data.jsonl or research_data2.jsonl.

    Returns:
        AuditRecord with per-attempt breakdown and aggregate stats.
    """
    t0 = time.monotonic()
    pid = record.get("problem_id", "unknown")
    problem_text = record.get("problem_text", "")
    ground_truth = GROUND_TRUTH.get(pid)

    attempts_key = "attempts" if "attempts" in record else "meaningful_attempts"
    raw_attempts = record.get(attempts_key, [])

    attempt_audits: list[AttemptAudit] = []
    annotated_solutions: list[AnnotatedSolution] = []

    for i, raw in enumerate(raw_attempts):
        sol_text  = raw.get("solution_text", "") or ""
        ver_text  = raw.get("verification_output", "") or ""

        # 1. Run the full verification pipeline (parser + arithmetic + answer)
        #    Pipeline expects a SolutionTrace, not a raw string.
        trace = SolutionTrace(raw_text=sol_text)
        pipe_result: PipelineResult = _pipeline.run(trace)

        # 1b. Extract canonical answer with metadata (extraction_pattern, confidence)
        extraction: ExtractionResult = _validator.extract_canonical(sol_text)

        # 2. Flaw detection (offline, no model call)
        critique: CritiqueReport = _flaw_det.detect_all(sol_text, ver_text)

        # 3. Build verifier_results list for the JSON output
        verifier_results = [
            {
                "kind":    "ARITHMETIC",
                "status":  pipe_result.report.confidence.value,
                "passed":  pipe_result.report.passed_checks,
                "failed":  pipe_result.report.failed_checks,
            }
        ]

        attempt_audit = AttemptAudit(
            attempt_id=i,
            canonical_answer=extraction.value,
            extraction_pattern=extraction.pattern if extraction.succeeded else "none",
            extraction_confidence=extraction.confidence.value,
            verifier_results=verifier_results,
            verification_report=pipe_result.report,
            critique_report=critique,
            flaw_codes=sorted(critique.flaw_codes),
            flaw_severity_total=critique.severity_total,
            is_clean_trace=critique.is_clean,
        )
        attempt_audits.append(attempt_audit)

        # Build AnnotatedSolution for AnswerSelector
        annotated_solutions.append(AnnotatedSolution(
            final_answer=extraction.value,
            report=pipe_result.report,
            attempt_id=i,
            raw_text=sol_text,
        ))

    # 4. AnswerSelector picks the best answer across attempts
    selected, reason, confidence = _selector.select(annotated_solutions)

    # 5. Score correctness
    correct: Optional[bool] = None
    if ground_truth is not None:
        correct = (selected == ground_truth)

    # 6. Aggregate flaw stats
    all_codes: set[str] = set()
    for a in attempt_audits:
        all_codes.update(a.flaw_codes)
    total_flaws   = sum(a.flaw_severity_total for a in attempt_audits)
    clean_count   = sum(1 for a in attempt_audits if a.is_clean_trace)

    elapsed = time.monotonic() - t0

    return AuditRecord(
        problem_id=pid,
        problem_text=problem_text[:200],  # truncate for JSON safety
        ground_truth=ground_truth,
        num_attempts=len(raw_attempts),
        attempts=attempt_audits,
        selected_answer=selected,
        selection_reason=reason,
        confidence_score=confidence,
        correct=correct,
        total_flaws=total_flaws,
        unique_flaw_codes=sorted(all_codes),
        clean_attempt_count=clean_count,
        audit_duration_seconds=elapsed,
    )
