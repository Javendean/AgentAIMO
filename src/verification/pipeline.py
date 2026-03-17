"""Verification pipeline — orchestrate all checkers on a single solution trace.

The pipeline runs:
  1. SolutionParser    → structured steps + extracted calculations + final answer
  2. ArithmeticChecker → re-compute all extracted calculations
  3. AnswerValidator   → validate final answer format + cross-consistency

It produces a VerificationReport summarizing all check outcomes.
SymbolicChecker, BruteForceChecker, CounterexampleSearcher are available as
optional passes (not run by default — each requires caller-supplied claims).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from src.models.trace import (
    SolutionTrace,
    ArithmeticCheckResult,
    VerificationResult,
    VerificationStatus,
)
from src.models.verification import ConfidenceLevel, VerificationReport
from src.verification.answer_validator import AnswerValidator
from src.verification.arithmetic_checker import ArithmeticChecker
from src.verification.solution_parser import SolutionParser


@dataclass
class PipelineResult:
    """Full result of running the verification pipeline on one trace.

    Attributes:
        trace:              The parsed and annotated SolutionTrace.
        arithmetic_results: One ArithmeticCheckResult per extracted calculation.
        answer_format:      Format validation of the final answer.
        report:             Aggregated VerificationReport.
    """
    trace: SolutionTrace
    arithmetic_results: List[ArithmeticCheckResult] = field(default_factory=list)
    answer_format: Optional[VerificationResult] = None
    report: VerificationReport = field(
        default_factory=lambda: VerificationReport(confidence=ConfidenceLevel.UNVERIFIED)
    )

    @property
    def final_answer(self) -> Optional[int]:
        return self.trace.final_answer

    @property
    def passed(self) -> bool:
        return self.report.pass_rate >= 0.5 and not self.report.has_failures


class VerificationPipeline:
    """Orchestrate the verification battery for one SolutionTrace.

    The pipeline is deliberately conservative:
      - A trace with no parseable calculations gets UNVERIFIED, not PASS.
      - A trace where ≥1 arithmetic check fails gets a failing report.
      - The answer format check is always run.
    """

    def __init__(
        self,
        parser: Optional[SolutionParser] = None,
        arithmetic: Optional[ArithmeticChecker] = None,
        validator: Optional[AnswerValidator] = None,
        run_arithmetic: bool = True,
    ):
        self.parser     = parser     or SolutionParser()
        self.arithmetic = arithmetic or ArithmeticChecker()
        self.validator  = validator  or AnswerValidator()
        self.run_arithmetic = run_arithmetic

    def run(self, trace: SolutionTrace) -> PipelineResult:
        """Run the full pipeline on a single solution trace.

        Args:
            trace: SolutionTrace with raw_text populated.

        Returns:
            PipelineResult with populated arithmetic results and VerificationReport.
        """
        # Step 1: Parse
        self.parser.parse(trace)

        result = PipelineResult(trace=trace)

        # Step 2: Arithmetic checks
        if self.run_arithmetic and trace.is_parsed:
            result.arithmetic_results = self.arithmetic.check_all(trace)

        # Step 3: Validate final answer format
        result.answer_format = self.validator.validate_format(trace.final_answer)

        # Step 4: Build VerificationReport
        result.report = self._build_report(result)

        return result

    def _build_report(self, result: PipelineResult) -> VerificationReport:
        """Aggregate all check outcomes into a VerificationReport."""
        passed = failed = suspicious = 0
        strongest = ConfidenceLevel.UNVERIFIED
        breakdown: dict = {}

        all_checks: List[tuple] = []

        # Arithmetic checks
        for ac in result.arithmetic_results:
            all_checks.append((ac.status, ac.confidence))

        # Answer format check
        if result.answer_format:
            all_checks.append((result.answer_format.status, result.answer_format.confidence))

        for status, confidence in all_checks:
            level = confidence.value
            if level not in breakdown:
                breakdown[level] = {"pass": 0, "fail": 0, "suspicious": 0}

            if status == VerificationStatus.PASS:
                passed += 1
                breakdown[level]["pass"] += 1
                if confidence.strength > strongest.strength:
                    strongest = confidence
            elif status == VerificationStatus.FAIL:
                failed += 1
                breakdown[level]["fail"] += 1
            elif status == VerificationStatus.SUSPICIOUS:
                suspicious += 1
                breakdown[level]["suspicious"] = breakdown[level].get("suspicious", 0) + 1
            # TIMEOUT / ERROR / SKIPPED don't count toward pass/fail

        return VerificationReport(
            passed_checks=passed,
            failed_checks=failed,
            suspicious_checks=suspicious,
            confidence=strongest,
            breakdown=breakdown,
        )
