"""Arithmetic verification for explicit calculations in steps."""

from typing import Optional
from src.models.solution import SolutionTrace, ExtractedCalculation
from src.models.verification import ArithmeticCheckResult

class ArithmeticChecker:
    """Re-compute every extracted calculation and compare to claimed results."""

    def __init__(self, precision: int = 50, float_tolerance: float = 1e-10, timeout_per_calc_seconds: float = 5.0):
        """Initialize arithmetic checker.

        Args:
            precision: The precision to use for mpmath operations.
            float_tolerance: Tolerance for numerical comparisons.
            timeout_per_calc_seconds: Maximum time allowed per calculation.
        """
        self.precision = precision
        self.float_tolerance = float_tolerance
        self.timeout_per_calc_seconds = timeout_per_calc_seconds

    def check_all(self, trace: SolutionTrace) -> list[ArithmeticCheckResult]:
        """Check every calculation in the trace.

        Args:
            trace: The full SolutionTrace with parsed steps.

        Returns:
            A list of ArithmeticCheckResult for every calculation found.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")

    def check_single(self, calc: ExtractedCalculation) -> ArithmeticCheckResult:
        """Check one calculation.

        Args:
            calc: A single ExtractedCalculation object.

        Returns:
            The ArithmeticCheckResult indicating whether the computation matched.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")

    def _sanitize_expression(self, expression: str) -> str:
        """Convert human math to Python-evaluable form.
        Handle: C(n,k), n!, a^b, ×, ÷, commas, \\frac, \\sqrt, \\binom

        Args:
            expression: The human-readable mathematical expression.

        Returns:
            A string suitable for evaluation via SymPy/mpmath.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")

    def _safe_eval(self, sanitized_expr: str) -> Optional[str]:
        """Safely evaluate using sympy.sympify, NOT Python eval().
        Timeout after self.timeout_per_calc_seconds.

        Args:
            sanitized_expr: Evaluatable math string from _sanitize_expression.

        Returns:
            A string representation of the evaluated value, or None if failed/timeout.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")

    def _compare_results(self, claimed: str, computed: str) -> bool:
        """Compare with tolerance for floats, equivalent representations.

        Args:
            claimed: The result claimed by the solution trace.
            computed: The result returned by _safe_eval.

        Returns:
            True if the values are logically equivalent, False otherwise.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")
