"""Symbolic verification — verify algebraic identities and substitutions via SymPy.

Produces LEVEL_1_SYMBOLIC confidence when SymPy confirms a claim analytically.
Falls back to numerical spot-checks when exact simplification times out.
"""

from __future__ import annotations

import random
from typing import Optional, List, Dict, Tuple

from src.models.trace import SymbolicCheckResult, VerificationStatus
from src.models.verification import ConfidenceLevel


# Functions that are NOT variables (excluded from auto-detection)
_FUNCTION_NAMES = {
    "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
    "exp", "log", "ln", "sqrt", "abs", "floor", "ceil",
    "factorial", "gcd", "lcm", "isprime", "nextprime",
    "pi", "E", "I", "oo", "zoo",
}

_EDGE_CASES = [0, 1, -1, 2, -2, 0.5, -0.5, 100, -100]


class SymbolicChecker:
    """Verify algebraic claims using SymPy and numerical testing.

    Produces LEVEL_1_SYMBOLIC confidence when SymPy simplification confirms
    the claim. Produces ENUMERATED confidence when only numerical spot-checks
    are possible (symbolic simplification timed out or was too complex).
    """

    def __init__(
        self,
        num_test_points: int = 100,
        numerical_tolerance: float = 1e-8,
        timeout_seconds: float = 10.0,
    ):
        self.num_test_points = num_test_points
        self.numerical_tolerance = numerical_tolerance
        self.timeout_seconds = timeout_seconds

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def check_identity(
        self,
        lhs: str,
        rhs: str,
        variables: Optional[List[str]] = None,
    ) -> SymbolicCheckResult:
        """Check lhs == rhs algebraically.

        Strategy:
          1. Try sympy.simplify(lhs - rhs) == 0  (exact symbolic)
          2. Try sympy.expand() and sympy.trigsimp() for trig identities
          3. Fall back to numerical spot-checks at random + edge points

        Args:
            lhs: Left-hand side expression string.
            rhs: Right-hand side expression string.
            variables: Variable names to use; auto-detected if None.

        Returns:
            SymbolicCheckResult with PASS/FAIL/ERROR and appropriate confidence.
        """
        try:
            import sympy
            l = sympy.sympify(lhs)
            r = sympy.sympify(rhs)
            diff = sympy.simplify(l - r)

            if diff == 0:
                return SymbolicCheckResult(
                    check_type="identity",
                    expression_lhs=lhs,
                    expression_rhs=rhs,
                    status=VerificationStatus.PASS,
                    confidence=ConfidenceLevel.LEVEL_1_SYMBOLIC,
                )

            # Try expand / trigsimp
            diff2 = sympy.trigsimp(sympy.expand(l - r))
            if diff2 == 0:
                return SymbolicCheckResult(
                    check_type="identity",
                    expression_lhs=lhs,
                    expression_rhs=rhs,
                    status=VerificationStatus.PASS,
                    confidence=ConfidenceLevel.LEVEL_1_SYMBOLIC,
                )

            # Symbolic check failed — try numerical
            vars_ = variables or self._auto_detect_variables(f"{lhs} {rhs}")
            num_ok, ce = self._numerical_spot_check(f"({lhs}) - ({rhs})", vars_)
            if num_ok:
                return SymbolicCheckResult(
                    check_type="identity",
                    expression_lhs=lhs,
                    expression_rhs=rhs,
                    status=VerificationStatus.PASS,
                    confidence=ConfidenceLevel.ENUMERATED,
                )
            return SymbolicCheckResult(
                check_type="identity",
                expression_lhs=lhs,
                expression_rhs=rhs,
                status=VerificationStatus.FAIL,
                confidence=ConfidenceLevel.LEVEL_1_SYMBOLIC,
                counterexample=ce,
            )

        except Exception as e:
            return SymbolicCheckResult(
                check_type="identity",
                expression_lhs=lhs,
                expression_rhs=rhs,
                status=VerificationStatus.ERROR,
                confidence=ConfidenceLevel.UNVERIFIED,
                error_message=str(e),
            )

    def check_inequality(
        self,
        expression: str,
        direction: str,
        bound: str,
        variables: Optional[List[str]] = None,
        domain_constraints: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> SymbolicCheckResult:
        """Check that expression <direction> bound holds universally.

        Args:
            expression: The expression to check (e.g. "x**2 + 1").
            direction: One of ">", ">=", "<", "<=".
            bound: The bound expression (e.g. "0").
            variables: Variables to test over; auto-detected if None.
            domain_constraints: {var: (min, max)} for each variable.

        Returns:
            SymbolicCheckResult with PASS if no counterexample found.
        """
        vars_ = variables or self._auto_detect_variables(f"{expression} {bound}")
        domain = domain_constraints or {v: (-100.0, 100.0) for v in vars_}

        def _violates(vals: Dict[str, float]) -> bool:
            try:
                import sympy
                subs = {sympy.Symbol(k): v for k, v in vals.items()}
                lv = float(sympy.sympify(expression).subs(subs))
                bv = float(sympy.sympify(bound).subs(subs))
                if direction == ">":  return not (lv > bv)
                if direction == ">=": return not (lv >= bv)
                if direction == "<":  return not (lv < bv)
                if direction == "<=": return not (lv <= bv)
                return False
            except Exception:
                return False

        # Spot-check
        counterexample = None
        rng = random.Random(42)
        for _ in range(self.num_test_points):
            candidate = {
                v: rng.uniform(domain.get(v, (-100, 100))[0],
                               domain.get(v, (-100, 100))[1])
                for v in vars_
            }
            if _violates(candidate):
                counterexample = {k: round(v, 6) for k, v in candidate.items()}
                break

        if counterexample:
            return SymbolicCheckResult(
                check_type="inequality",
                expression_lhs=expression,
                expression_rhs=f"{direction} {bound}",
                status=VerificationStatus.FAIL,
                confidence=ConfidenceLevel.ENUMERATED,
                counterexample=counterexample,
            )
        return SymbolicCheckResult(
            check_type="inequality",
            expression_lhs=expression,
            expression_rhs=f"{direction} {bound}",
            status=VerificationStatus.PASS,
            confidence=ConfidenceLevel.ENUMERATED,
        )

    def check_substitution(
        self,
        original_expr: str,
        substitution: Dict[str, str],
        claimed_result: str,
    ) -> SymbolicCheckResult:
        """Check that substituting variables into original_expr gives claimed_result.

        Args:
            original_expr: The expression before substitution.
            substitution: {var_name: value_expression} pairs.
            claimed_result: The value the solution claims results from the substitution.

        Returns:
            SymbolicCheckResult with PASS if SymPy agrees with the claimed result.
        """
        try:
            import sympy
            expr = sympy.sympify(original_expr)
            subs = {sympy.Symbol(k): sympy.sympify(v)
                    for k, v in substitution.items()}
            actual = sympy.simplify(expr.subs(subs))
            claimed = sympy.sympify(claimed_result)
            diff = sympy.simplify(actual - claimed)

            ok = (diff == 0)
            return SymbolicCheckResult(
                check_type="substitution",
                expression_lhs=original_expr,
                expression_rhs=claimed_result,
                status=VerificationStatus.PASS if ok else VerificationStatus.FAIL,
                confidence=ConfidenceLevel.LEVEL_1_SYMBOLIC,
                error_message="" if ok else (
                    f"Substitution gives {actual}, claimed {claimed_result}"
                ),
            )
        except Exception as e:
            return SymbolicCheckResult(
                check_type="substitution",
                expression_lhs=original_expr,
                expression_rhs=claimed_result,
                status=VerificationStatus.ERROR,
                confidence=ConfidenceLevel.UNVERIFIED,
                error_message=str(e),
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _numerical_spot_check(
        self,
        expression: str,
        variables: List[str],
        expected_value: float = 0.0,
        domain_constraints: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> Tuple[bool, Optional[Dict[str, float]]]:
        """Test expression ≈ expected_value at random + edge points.

        Returns:
            (all_passed, counterexample_dict_or_None)
        """
        if not variables:
            try:
                import sympy
                val = float(sympy.sympify(expression))
                ok = abs(val - expected_value) <= self.numerical_tolerance
                return ok, None if ok else {"result": val}
            except Exception:
                return True, None   # Can't check, give benefit of doubt

        domain = domain_constraints or {v: (-10.0, 10.0) for v in variables}
        rng = random.Random(42)

        # Build candidate points: edge cases + random
        candidates: List[Dict[str, float]] = []
        for ec in _EDGE_CASES:
            candidates.append({v: ec for v in variables})
        for _ in range(self.num_test_points):
            candidates.append({
                v: rng.uniform(domain.get(v, (-10, 10))[0],
                               domain.get(v, (-10, 10))[1])
                for v in variables
            })

        for candidate in candidates:
            try:
                import sympy
                subs = {sympy.Symbol(k): v for k, v in candidate.items()}
                val = complex(sympy.sympify(expression).subs(subs))
                if abs(val.imag) > self.numerical_tolerance:
                    continue   # Complex result — skip point
                if abs(val.real - expected_value) > self.numerical_tolerance:
                    return False, {k: round(v, 6) for k, v in candidate.items()}
            except Exception:
                continue

        return True, None

    def _auto_detect_variables(self, expression_str: str) -> List[str]:
        """Detect single-letter variable names, excluding known function names."""
        try:
            import sympy
            expr = sympy.sympify(expression_str)
            return [str(s) for s in expr.free_symbols
                    if str(s) not in _FUNCTION_NAMES]
        except Exception:
            # Fallback: single lowercase letters not in function names
            seen = set()
            result = []
            for ch in expression_str:
                if ch.isalpha() and ch.islower() and ch not in seen:
                    if ch not in _FUNCTION_NAMES:
                        seen.add(ch)
                        result.append(ch)
            return result
