"""Verification and correctness checking models."""

import enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Any


class ConfidenceLevel(enum.Enum):
    """Levels of confidence in a verification result."""
    LEVEL_0_EXACT = "exact_match"
    LEVEL_1_SYMBOLIC = "symbolic_verified"
    LEVEL_2_FORMAL = "formal_verified"
    LEVEL_3_NL_PASS = "nl_verified"
    LEVEL_4_SPECULATIVE = "speculative"
    UNVERIFIED = "unverified"


class VerificationMethod(enum.Enum):
    """Methods used to verify mathematical claims."""
    EXACT_MATCH = "exact_match"
    ARITHMETIC_RECOMPUTE = "arithmetic_recompute"
    SYMPY_SYMBOLIC = "sympy_symbolic"
    NUMERICAL_SPOT_CHECK = "numerical_spot_check"
    BRUTE_FORCE_ENUMERATE = "brute_force_enumerate"
    COUNTEREXAMPLE_SEARCH = "counterexample_search"
    SAGE_MATH = "sage_math"
    LEAN_KERNEL = "lean_kernel"
    NL_CRITIC = "nl_critic"
    PYTHON_EXECUTION = "python_execution"


@dataclass
class VerificationResult:
    """The outcome of a single verification attempt.

    Attributes:
        method: VerificationMethod used.
        target: Target of verification.
        passed: Whether it passed (True), failed (False), or was inconclusive (None).
        confidence: Level of confidence in this result.
        details: Explanation of the verification.
        evidence: Optional evidence data.
        wall_time_seconds: Time taken to verify.
    """
    method: VerificationMethod
    target: str
    passed: Optional[bool]
    confidence: ConfidenceLevel
    details: str
    evidence: Any = None
    wall_time_seconds: float = 0.0


@dataclass
class ArithmeticCheckResult:
    """The result of recomputing an arithmetic operation.

    Attributes:
        step_index: Source step.
        expression: Expression evaluated.
        claimed_result: Expected result.
        recomputed_result: Actual result.
        matches: If actual matched expected.
        error_message: Any error raised during computation.
    """
    step_index: int
    expression: str
    claimed_result: str
    recomputed_result: Optional[str] = None
    matches: Optional[bool] = None
    error_message: Optional[str] = None


@dataclass
class SymbolicCheckResult:
    """The outcome of checking an algebraic identity or simplification.

    Attributes:
        step_index: Source step.
        claim_text: Claim being checked.
        method_used: The engine/method used.
        verified: Whether it verified as true.
        sympy_output: Resulting SymPy output.
        num_test_points: Test points used if checking numerically.
        failing_point: Counter-example point if any.
    """
    step_index: int
    claim_text: str
    method_used: str
    verified: Optional[bool] = None
    sympy_output: Optional[str] = None
    num_test_points: int = 0
    failing_point: Optional[str] = None


@dataclass
class BruteForceResult:
    """Result of enumerating all cases to check a claim.

    Attributes:
        step_index: Source step.
        claim_text: Claim being checked.
        parameter_range: Scope of brute force search.
        total_cases_checked: Number of cases evaluated.
        all_passed: If all cases held true.
        failing_case: First failing case.
        wall_time_seconds: Time taken.
    """
    step_index: int
    claim_text: str
    parameter_range: str
    total_cases_checked: int = 0
    all_passed: Optional[bool] = None
    failing_case: Optional[str] = None
    wall_time_seconds: float = 0.0


@dataclass
class CounterexampleResult:
    """Result of searching for counterexamples to a claim.

    Attributes:
        step_index: Source step.
        claim_text: Claim being searched.
        search_strategy: Strategy employed.
        num_attempts: Number of search iterations.
        counterexample_found: True if a counterexample was found.
        counterexample: The counterexample itself.
        wall_time_seconds: Time taken.
    """
    step_index: int
    claim_text: str
    search_strategy: str
    num_attempts: int = 0
    counterexample_found: bool = False
    counterexample: Optional[str] = None
    wall_time_seconds: float = 0.0


@dataclass
class VerificationReport:
    """Aggregated verification results for one solution trace.
    Primary output of the verification battery.

    Attributes:
        problem_id: Source problem ID.
        attempt_index: Attempt sequence number.
        overall_confidence: Aggregate confidence.
        answer_verified: Is final answer proven correct?
        arithmetic_results: Checks on arithmetic operations.
        symbolic_results: Checks on algebraic statements.
        brute_force_results: Checks relying on enumeration.
        counterexample_results: Checks seeking counterexamples.
        step_verdicts: Overall step verification map {index: (passed, confidence, rationale)}.
        unverifiable_steps: Steps that could not be verified.
        total_checks_run: Number of checks run.
        total_checks_passed: Checks that returned True.
        total_checks_failed: Checks that returned False.
        total_checks_inconclusive: Checks that returned None.
        total_wall_time_seconds: Time taken by all checks.
        timestamp: Time of report generation.
    """
    problem_id: str
    attempt_index: int = 0
    overall_confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    answer_verified: Optional[bool] = None
    arithmetic_results: list[ArithmeticCheckResult] = field(default_factory=list)
    symbolic_results: list[SymbolicCheckResult] = field(default_factory=list)
    brute_force_results: list[BruteForceResult] = field(default_factory=list)
    counterexample_results: list[CounterexampleResult] = field(default_factory=list)
    step_verdicts: dict[int, tuple[Optional[bool], ConfidenceLevel, str]] = field(default_factory=dict)
    unverifiable_steps: list[int] = field(default_factory=list)
    total_checks_run: int = 0
    total_checks_passed: int = 0
    total_checks_failed: int = 0
    total_checks_inconclusive: int = 0
    total_wall_time_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def pass_rate(self) -> float:
        """The ratio of passing checks to total decided checks.

        Returns:
            float: passed / (passed + failed), 0.0 if no checks.
        """
        denom = self.total_checks_passed + self.total_checks_failed
        if denom == 0:
            return 0.0
        return self.total_checks_passed / denom

    @property
    def has_failures(self) -> bool:
        """Whether there is at least one failed check.

        Returns:
            bool: True if failures exist, False otherwise.
        """
        return self.total_checks_failed > 0
