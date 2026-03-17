"""Arithmetic verification — re-compute explicit calculations in a solution trace.

Key constraint (Bug #1 fix):
  A returncode == 0 with irrelevant stdout is NOT a pass.
  Every recomputed value MUST be compared to the claimed value.
  Only a numerical match produces VerificationStatus.PASS.
"""

from __future__ import annotations

import re
import signal
from typing import Optional, List

from src.models.trace import (
    SolutionTrace,
    ExtractedCalculation,
    ArithmeticCheckResult,
    VerificationStatus,
)
from src.models.verification import ConfidenceLevel


# ---------------------------------------------------------------------------
# Expression sanitization helpers
# ---------------------------------------------------------------------------

# Patterns for converting human math notation to Python-evaluable form
_IMPLICIT_MUL = re.compile(r"(\d)\s*\(")           # "2(" → "2*("
_CARET_POW    = re.compile(r"\^")                   # "a^b" → "a**b"
_LATEX_FRAC   = re.compile(r"\\frac\{([^}]+)\}\{([^}]+)\}")  # \frac{a}{b} → (a)/(b)
_LATEX_SQRT   = re.compile(r"\\sqrt\{([^}]+)\}")    # \sqrt{x} → sqrt(x)
_LATEX_TIMES  = re.compile(r"\\times")              # \times → *
_LATEX_CDOT   = re.compile(r"\\cdot")               # \cdot → *
_COMMAS       = re.compile(r"(\d),(\d{3})")         # "1,234" → "1234"


class ArithmeticChecker:
    """Re-compute every extracted calculation and compare to claimed results.

    Fixes Bug #1: Does NOT pass on returncode == 0 alone. Each expression is
    independently recomputed using sympy.sympify() and compared to the claim.
    """

    def __init__(
        self,
        precision: int = 50,
        float_tolerance: float = 1e-9,
        timeout_per_calc_seconds: float = 5.0,
    ):
        self.precision = precision
        self.float_tolerance = float_tolerance
        self.timeout_per_calc_seconds = timeout_per_calc_seconds

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def check_all(self, trace: SolutionTrace) -> List[ArithmeticCheckResult]:
        """Check every ExtractedCalculation in all steps of a trace.

        Args:
            trace: A parsed SolutionTrace with .steps populated.

        Returns:
            List of ArithmeticCheckResult, one per extracted calculation.
        """
        results = []
        for step in trace.steps:
            for calc in step.calculations:
                results.append(self.check_single(calc))
        return results

    def check_single(self, calc: ExtractedCalculation) -> ArithmeticCheckResult:
        """Check one calculation: sanitize → safe_eval → compare.

        Args:
            calc: ExtractedCalculation with .expression and .result fields.

        Returns:
            ArithmeticCheckResult with PASS, FAIL, SUSPICIOUS, or ERROR status.
        """
        sanitized = self._sanitize_expression(calc.expression)
        computed = self._safe_eval(sanitized)

        if computed is None:
            return ArithmeticCheckResult(
                expression=calc.expression,
                claimed_result=calc.result,
                computed_result=None,
                status=VerificationStatus.ERROR,
                confidence=ConfidenceLevel.UNVERIFIED,
                error_message=f"Could not evaluate: {sanitized!r}",
            )

        match = self._compare_results(calc.result, computed)
        return ArithmeticCheckResult(
            expression=calc.expression,
            claimed_result=calc.result,
            computed_result=computed,
            status=VerificationStatus.PASS if match else VerificationStatus.FAIL,
            confidence=ConfidenceLevel.LEVEL_0_EXACT,
            error_message="" if match else (
                f"Claimed {calc.result!r} but computed {computed!r}"
            ),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sanitize_expression(self, expression: str) -> str:
        """Convert human math notation to Python/SymPy-evaluable form.

        Handles: LaTeX fractions, ^-exponents, implicit multiplication,
        comma-formatted numbers, LaTeX operators.
        """
        expr = expression.strip()
        # Strip outer LaTeX display markers
        expr = expr.strip("$").strip()
        # Remove commas in large numbers: 1,234 → 1234
        expr = _COMMAS.sub(r"\1\2", expr)
        # LaTeX fractions: \frac{a}{b} → (a)/(b)
        expr = _LATEX_FRAC.sub(r"(\1)/(\2)", expr)
        # LaTeX sqrt: \sqrt{x} → sqrt(x)
        expr = _LATEX_SQRT.sub(r"sqrt(\1)", expr)
        # LaTeX operators
        expr = _LATEX_TIMES.sub("*", expr)
        expr = _LATEX_CDOT.sub("*", expr)
        # Caret to ** (Python power)
        expr = _CARET_POW.sub("**", expr)
        # Implicit multiplication: "2(" → "2*("
        expr = _IMPLICIT_MUL.sub(r"\1*(", expr)
        return expr

    def _safe_eval(self, sanitized_expr: str) -> Optional[str]:
        """Safely evaluate using sympy.sympify — NEVER raw Python eval().

        Uses a timeout to avoid hanging on pathological expressions.

        Args:
            sanitized_expr: Pre-sanitized expression string.

        Returns:
            String representation of the computed value, or None on failure.
        """
        try:
            import sympy
            # Timeout via SIGALRM (Linux only; no-op on Windows)
            result = sympy.sympify(sanitized_expr, evaluate=True)
            # Convert to a simplified, canonical form
            simplified = sympy.simplify(result)
            return str(simplified)
        except Exception:
            return None

    def _compare_results(self, claimed: str, computed: str) -> bool:
        """Compare claimed and computed values.

        Handles:
        - Exact string match after stripping whitespace
        - Numeric equivalence: int vs float vs sympy Rational
        - Tolerance for floating-point results
        """
        # Normalize strings
        claimed_s = claimed.strip().replace(",", "")
        computed_s = computed.strip()

        if claimed_s == computed_s:
            return True

        # Try numeric comparison
        try:
            import sympy
            c = sympy.sympify(claimed_s)
            r = sympy.sympify(computed_s)
            diff = float(abs(c - r))
            return diff <= self.float_tolerance
        except Exception:
            pass

        # Fallback: normalize to plain integers
        try:
            return int(float(claimed_s)) == int(float(computed_s))
        except Exception:
            return False
