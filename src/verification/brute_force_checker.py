"""Brute-force verification by exhaustive enumeration of finite domains.

Produces ENUMERATED confidence — stronger than NL_JUDGMENT but weaker than
LEVEL_0_EXACT (which requires exact recomputation of a specific value).
"""

from __future__ import annotations

import itertools
import time
from typing import Callable, Dict, Any, Optional

from src.models.trace import BruteForceResult, VerificationStatus
from src.models.verification import ConfidenceLevel


class BruteForceChecker:
    """Exhaustive enumeration for claims over finite integer domains.

    All four check methods share a common enumeration engine. The domain
    is expressed as {param_name: range_or_list} where values must be iterable.

    Example parameter_ranges:
        {"n": range(1, 101), "k": range(0, 10)}
        {"x": [0, 1, 2, 3, 4, 5]}
    """

    def __init__(
        self,
        max_cases: int = 1_000_000,
        timeout_seconds: float = 60.0,
    ):
        self.max_cases = max_cases
        self.timeout_seconds = timeout_seconds

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def check_counting_claim(
        self,
        predicate: Callable[..., bool],
        parameter_ranges: Dict[str, Any],
        claimed_count: int,
        step_index: int = -1,
    ) -> BruteForceResult:
        """Count instances satisfying predicate and compare to claimed_count.

        Args:
            predicate: Function(**kwargs) → bool.
            parameter_ranges: {param: iterable} defining the domain.
            claimed_count: The count the solution claims.
            step_index: Source step index for tracing.

        Returns:
            BruteForceResult with PASS if count matches, FAIL otherwise.
        """
        count, domain_size, timed_out, witness = 0, 0, False, None
        t0 = time.monotonic()

        for combo in self._iter_domain(parameter_ranges):
            if time.monotonic() - t0 > self.timeout_seconds:
                timed_out = True
                break
            if domain_size >= self.max_cases:
                break
            domain_size += 1
            try:
                if predicate(**combo):
                    count += 1
                    if witness is None:
                        witness = dict(combo)  # first example
            except Exception:
                pass

        if timed_out:
            return BruteForceResult(
                check_type="counting",
                domain_size=domain_size,
                status=VerificationStatus.TIMEOUT,
                claimed_value=claimed_count,
                found_value=count,
                error_message=f"Timed out after {self.timeout_seconds}s ({domain_size} cases)",
            )

        ok = (count == claimed_count)
        return BruteForceResult(
            check_type="counting",
            domain_size=domain_size,
            status=VerificationStatus.PASS if ok else VerificationStatus.FAIL,
            confidence=ConfidenceLevel.ENUMERATED,
            claimed_value=claimed_count,
            found_value=count,
            witness=witness,
            error_message="" if ok else (
                f"Claimed count={claimed_count} but enumeration found {count}"
            ),
        )

    def check_universal_claim(
        self,
        predicate: Callable[..., bool],
        parameter_ranges: Dict[str, Any],
        step_index: int = -1,
    ) -> BruteForceResult:
        """Verify a 'for all' claim — short-circuit on first failure.

        Args:
            predicate: Function(**kwargs) → bool (should be True for all).
            parameter_ranges: {param: iterable}.

        Returns:
            BruteForceResult with PASS if predicate holds everywhere,
            FAIL (with witness = first failing case) otherwise.
        """
        domain_size, t0 = 0, time.monotonic()

        for combo in self._iter_domain(parameter_ranges):
            if time.monotonic() - t0 > self.timeout_seconds:
                return BruteForceResult(
                    check_type="universal",
                    domain_size=domain_size,
                    status=VerificationStatus.TIMEOUT,
                    error_message=f"Timed out after {domain_size} cases",
                )
            if domain_size >= self.max_cases:
                break
            domain_size += 1
            try:
                if not predicate(**combo):
                    return BruteForceResult(
                        check_type="universal",
                        domain_size=domain_size,
                        status=VerificationStatus.FAIL,
                        confidence=ConfidenceLevel.ENUMERATED,
                        witness=dict(combo),
                        error_message=f"Universal claim fails at {combo}",
                    )
            except Exception:
                pass

        return BruteForceResult(
            check_type="universal",
            domain_size=domain_size,
            status=VerificationStatus.PASS,
            confidence=ConfidenceLevel.ENUMERATED,
        )

    def check_optimization_claim(
        self,
        objective: Callable[..., float],
        parameter_ranges: Dict[str, Any],
        claimed_optimum: float,
        optimization_type: str,
        step_index: int = -1,
    ) -> BruteForceResult:
        """Check that claimed_optimum is indeed the max or min of objective.

        Args:
            objective: Function(**kwargs) → float.
            parameter_ranges: {param: iterable}.
            claimed_optimum: The value the solution claims is the optimum.
            optimization_type: "max" or "min".

        Returns:
            BruteForceResult with PASS if no better value found, FAIL otherwise.
        """
        best, best_at = None, None
        domain_size, t0 = 0, time.monotonic()

        for combo in self._iter_domain(parameter_ranges):
            if time.monotonic() - t0 > self.timeout_seconds:
                break
            if domain_size >= self.max_cases:
                break
            domain_size += 1
            try:
                val = float(objective(**combo))
                if best is None:
                    best, best_at = val, dict(combo)
                elif optimization_type == "max" and val > best:
                    best, best_at = val, dict(combo)
                elif optimization_type == "min" and val < best:
                    best, best_at = val, dict(combo)
            except Exception:
                pass

        if best is None:
            return BruteForceResult(
                check_type="optimization",
                domain_size=domain_size,
                status=VerificationStatus.ERROR,
                error_message="No evaluable cases in domain",
            )

        ok = abs(best - claimed_optimum) < 1e-9
        return BruteForceResult(
            check_type="optimization",
            domain_size=domain_size,
            status=VerificationStatus.PASS if ok else VerificationStatus.FAIL,
            confidence=ConfidenceLevel.ENUMERATED,
            claimed_value=int(claimed_optimum) if claimed_optimum == int(claimed_optimum) else None,
            found_value=int(best) if best == int(best) else None,
            witness=best_at,
            error_message="" if ok else (
                f"Claimed {optimization_type}={claimed_optimum} but found {best} at {best_at}"
            ),
        )

    def check_existence_claim(
        self,
        predicate: Callable[..., bool],
        parameter_ranges: Dict[str, Any],
        step_index: int = -1,
    ) -> BruteForceResult:
        """Verify existence — short-circuit on first success.

        Args:
            predicate: Function(**kwargs) → bool (True = witness found).
            parameter_ranges: {param: iterable}.

        Returns:
            BruteForceResult with PASS + witness if found, FAIL otherwise.
        """
        domain_size, t0 = 0, time.monotonic()

        for combo in self._iter_domain(parameter_ranges):
            if time.monotonic() - t0 > self.timeout_seconds:
                return BruteForceResult(
                    check_type="existence",
                    domain_size=domain_size,
                    status=VerificationStatus.TIMEOUT,
                    error_message=f"Timed out after {domain_size} cases — existence not confirmed",
                )
            if domain_size >= self.max_cases:
                break
            domain_size += 1
            try:
                if predicate(**combo):
                    return BruteForceResult(
                        check_type="existence",
                        domain_size=domain_size,
                        status=VerificationStatus.PASS,
                        confidence=ConfidenceLevel.ENUMERATED,
                        witness=dict(combo),
                    )
            except Exception:
                pass

        return BruteForceResult(
            check_type="existence",
            domain_size=domain_size,
            status=VerificationStatus.FAIL,
            confidence=ConfidenceLevel.ENUMERATED,
            error_message=f"No witness found in {domain_size} cases",
        )

    # ------------------------------------------------------------------
    # Domain iteration helper
    # ------------------------------------------------------------------

    def _iter_domain(self, parameter_ranges: Dict[str, Any]):
        """Yield all combinations of parameter values as dicts."""
        keys = list(parameter_ranges.keys())
        for combo in itertools.product(*[parameter_ranges[k] for k in keys]):
            yield dict(zip(keys, combo))
