"""Canonical answer validation module for AIMO.

This module is the single authoritative extraction and validation path for
final answers. It replaces the regex in agent/prompts.py::extract_answer as
the typed, testable canonical channel.

All AIMO answers are non-negative integers in [0, 99999].

Usage:
    validator = AnswerValidator()

    # Extract a canonical integer from raw model output
    result = validator.extract_canonical(raw_text)
    # result: ExtractionResult with .value (int|None) and .confidence

    # Validate format only (no ground truth needed)
    vr = validator.validate_format(42)
    # vr: VerificationResult with status PASS/FAIL and confidence LEVEL_0_EXACT

    # Check against known answer (for ablation / evaluation)
    vr = validator.validate_against_ground_truth(42, problem)
    # vr: VerificationResult with status PASS/FAIL and confidence LEVEL_0_EXACT

    # Cross-check consistency across multiple solution traces
    vr = validator.validate_cross_consistency(traces)
    # vr: VerificationResult with detail = {answer: count, ...}
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional, List

from src.models.problem import Problem
from src.models.trace import SolutionTrace, VerificationResult, VerificationStatus
from src.models.verification import ConfidenceLevel


# ---------------------------------------------------------------------------
# AIMO answer domain
# ---------------------------------------------------------------------------

AIMO_MIN = 0
AIMO_MAX = 99999


# ---------------------------------------------------------------------------
# Extraction result — typed wrapper around the raw extracted value
# ---------------------------------------------------------------------------

@dataclass
class ExtractionResult:
    """Result of attempting to extract a canonical integer answer from text.

    Attributes:
        value:      The extracted integer, or None if extraction failed.
        raw_match:  The raw string that was matched (for debugging).
        pattern:    Which pattern succeeded (e.g. 'bold', 'plain', 'boxed').
        confidence: Confidence level; always LEVEL_0_EXACT if value is not None
                    (extraction is deterministic), UNVERIFIED if None.
    """
    value: Optional[int]
    raw_match: Optional[str] = None
    pattern: Optional[str] = None
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED

    @property
    def succeeded(self) -> bool:
        return self.value is not None

    def __str__(self) -> str:
        if self.succeeded:
            return f"ExtractionResult(value={self.value}, pattern={self.pattern!r})"
        return "ExtractionResult(value=None)"


# ---------------------------------------------------------------------------
# Compiled extraction patterns (order matters — first match wins)
# ---------------------------------------------------------------------------

_PATTERNS = [
    # 1. **ANSWER: 42** (bold with closing **)
    ("bold_closed",  re.compile(
        r"\*\*ANSWER:\s*(\d{1,6})\*\*",
        re.IGNORECASE,
    )),
    # 2. **ANSWER: 42  (bold, model truncated before closing **)
    #    Must be at end-of-line or end-of-string to avoid false matches
    ("bold_open",    re.compile(
        r"\*\*ANSWER:\s*(\d{1,6})\s*(?:\n|$)",
        re.IGNORECASE | re.MULTILINE,
    )),
    # 3. ANSWER: 42  (no bold markers)
    ("plain",        re.compile(
        r"(?<!\w)ANSWER:\s*(\d{1,6})(?:\s|$|\n)",
        re.IGNORECASE,
    )),
    # 4. \boxed{42}  (LaTeX format — common in reasoning traces)
    ("boxed",        re.compile(
        r"\\boxed\{(\d{1,6})\}",
    )),
]


# ---------------------------------------------------------------------------
# Main validator class
# ---------------------------------------------------------------------------

class AnswerValidator:
    """Canonical extraction and validation pipeline for AIMO final answers.

    Replaces the bare regex in agent/prompts.py::extract_answer with typed,
    testable, fail-safe extraction + three validation methods.
    """

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    def extract_canonical(self, solution_text: str) -> ExtractionResult:
        """Extract the final integer answer from a solution trace.

        Tries the patterns in _PATTERNS order. Returns the first match whose
        numeric value falls in [AIMO_MIN, AIMO_MAX]. Never raises.

        Args:
            solution_text: Full text of the model's generated solution.

        Returns:
            ExtractionResult with value=int if successful, value=None otherwise.
        """
        for name, pattern in _PATTERNS:
            match = pattern.search(solution_text)
            if match:
                try:
                    val = int(match.group(1))
                except (ValueError, IndexError):
                    continue
                if AIMO_MIN <= val <= AIMO_MAX:
                    return ExtractionResult(
                        value=val,
                        raw_match=match.group(0).strip(),
                        pattern=name,
                        confidence=ConfidenceLevel.LEVEL_0_EXACT,
                    )
        return ExtractionResult(value=None, confidence=ConfidenceLevel.UNVERIFIED)

    # ------------------------------------------------------------------
    # Validation methods
    # ------------------------------------------------------------------

    def validate_format(self, answer: Optional[int]) -> VerificationResult:
        """Check that answer is a non-negative integer in [0, 99999].

        This is a pure format check — no ground truth needed. Produces
        LEVEL_0_EXACT confidence because the check is deterministic.

        Args:
            answer: The extracted integer answer to validate (may be None).

        Returns:
            VerificationResult with status PASS or FAIL.
        """
        if answer is None:
            return VerificationResult(
                status=VerificationStatus.FAIL,
                confidence=ConfidenceLevel.UNVERIFIED,
                message="No answer extracted — extraction failed.",
            )
        if not isinstance(answer, int):
            return VerificationResult(
                status=VerificationStatus.FAIL,
                confidence=ConfidenceLevel.UNVERIFIED,
                message=f"Answer is not an integer: {type(answer).__name__}",
            )
        if not (AIMO_MIN <= answer <= AIMO_MAX):
            return VerificationResult(
                status=VerificationStatus.FAIL,
                confidence=ConfidenceLevel.LEVEL_0_EXACT,
                message=f"Answer {answer} out of AIMO range [{AIMO_MIN}, {AIMO_MAX}].",
            )
        return VerificationResult(
            status=VerificationStatus.PASS,
            confidence=ConfidenceLevel.LEVEL_0_EXACT,
            message=f"Answer {answer} is a valid AIMO integer.",
        )

    def validate_against_ground_truth(
        self, answer: Optional[int], problem: Problem
    ) -> VerificationResult:
        """Check answer against the problem's known ground truth, if available.

        LEVEL_0_EXACT confidence when truth is present and matches.
        UNVERIFIED when problem has no ground_truth (competition setting).

        Args:
            answer:  The candidate integer answer.
            problem: Problem dataclass; problem.ground_truth may be None.

        Returns:
            VerificationResult with PASS/FAIL or SKIPPED if no truth available.
        """
        if problem.ground_truth is None:
            return VerificationResult(
                status=VerificationStatus.SKIPPED,
                confidence=ConfidenceLevel.UNVERIFIED,
                message="Problem has no ground truth — validation skipped.",
            )
        if answer is None:
            return VerificationResult(
                status=VerificationStatus.FAIL,
                confidence=ConfidenceLevel.UNVERIFIED,
                message="No answer to compare against ground truth.",
            )
        if answer == problem.ground_truth:
            return VerificationResult(
                status=VerificationStatus.PASS,
                confidence=ConfidenceLevel.LEVEL_0_EXACT,
                message=f"Answer {answer} matches ground truth {problem.ground_truth}.",
                detail={"answer": answer, "ground_truth": problem.ground_truth},
            )
        return VerificationResult(
            status=VerificationStatus.FAIL,
            confidence=ConfidenceLevel.LEVEL_0_EXACT,
            message=(
                f"Answer {answer} does NOT match ground truth {problem.ground_truth}."
            ),
            detail={"answer": answer, "ground_truth": problem.ground_truth},
        )

    def validate_cross_consistency(
        self, traces: List[SolutionTrace]
    ) -> VerificationResult:
        """Check agreement across multiple solution traces for the same problem.

        Counts how many distinct canonical answers appear across all traces,
        and reports the plurality answer and the vote distribution.

        Args:
            traces: List of SolutionTrace objects for the same problem.

        Returns:
            VerificationResult with:
              - PASS if ≥50% of traces agree on a single answer
              - SUSPICIOUS if no majority (high disagreement)
              - FAIL if no trace produced a valid answer
            detail contains {"answer": int, "votes": {str(answer): count}, "total": N}
        """
        if not traces:
            return VerificationResult(
                status=VerificationStatus.FAIL,
                confidence=ConfidenceLevel.UNVERIFIED,
                message="No traces provided.",
            )

        # Collect valid answers from traces
        answers = [t.final_answer for t in traces if t.final_answer is not None]
        total = len(traces)

        if not answers:
            return VerificationResult(
                status=VerificationStatus.FAIL,
                confidence=ConfidenceLevel.UNVERIFIED,
                message=f"All {total} traces failed to produce a valid answer.",
                detail={"votes": {}, "total": total},
            )

        vote_counts = Counter(answers)
        plurality_answer, plurality_votes = vote_counts.most_common(1)[0]
        vote_fraction = plurality_votes / total
        votes_str = {str(k): v for k, v in vote_counts.items()}

        if vote_fraction >= 0.5:
            return VerificationResult(
                status=VerificationStatus.PASS,
                confidence=ConfidenceLevel.LEVEL_0_EXACT,
                message=(
                    f"Plurality answer {plurality_answer} has {plurality_votes}/{total} "
                    f"votes ({vote_fraction:.0%})."
                ),
                detail={
                    "answer": plurality_answer,
                    "votes": votes_str,
                    "total": total,
                    "plurality_fraction": vote_fraction,
                },
            )
        else:
            return VerificationResult(
                status=VerificationStatus.SUSPICIOUS,
                confidence=ConfidenceLevel.UNVERIFIED,
                message=(
                    f"No majority — best answer {plurality_answer} has only "
                    f"{plurality_votes}/{total} votes ({vote_fraction:.0%}). "
                    f"High disagreement across traces."
                ),
                detail={
                    "answer": plurality_answer,
                    "votes": votes_str,
                    "total": total,
                    "plurality_fraction": vote_fraction,
                },
            )


# ---------------------------------------------------------------------------
# Convenience function — drop-in replacement for agent/prompts.py::extract_answer
# ---------------------------------------------------------------------------

_validator = AnswerValidator()


def extract_canonical_answer(solution_text: str) -> Optional[str]:
    """Drop-in replacement for agent/prompts.py::extract_answer.

    Returns the integer as a string (matching the existing interface) or None.
    Internally uses the typed AnswerValidator for testable, consistent extraction.

    Args:
        solution_text: Full model output text.

    Returns:
        str (e.g. "42") if a valid answer was extracted, None otherwise.
    """
    result = _validator.extract_canonical(solution_text)
    return str(result.value) if result.succeeded else None
