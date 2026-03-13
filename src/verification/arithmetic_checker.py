"""Arithmetic verification for explicit calculations in steps."""

from typing import Optional, List
from src.models.trace import SolutionTrace, ExtractedCalculation, ArithmeticCheckResult

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

    def check_all(self, trace: SolutionTrace) -> List[ArithmeticCheckResult]:
        """Check every calculation in the trace."""
        raise NotImplementedError("Agent must implement this method.")

    def check_single(self, calc: ExtractedCalculation) -> ArithmeticCheckResult:
        """Check one calculation."""
        raise NotImplementedError("Agent must implement this method.")

    def _sanitize_expression(self, expression: str) -> str:
        """Convert human math to Python-evaluable form."""
        raise NotImplementedError("Agent must implement this method.")

    def _safe_eval(self, sanitized_expr: str) -> Optional[str]:
        """Safely evaluate using sympy.sympify, NOT Python eval()."""
        raise NotImplementedError("Agent must implement this method.")

    def _compare_results(self, claimed: str, computed: str) -> bool:
        """Compare with tolerance for floats, equivalent representations."""
        raise NotImplementedError("Agent must implement this method.")
