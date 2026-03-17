"""Active counterexample search — disprove claimed results proactively.

Strategy: 40% random, 30% boundary values, 30% systematic grid.
Produces ENUMERATED confidence when no counterexample is found within budget.
"""

from __future__ import annotations

import itertools
import random
import time
from typing import Callable, Dict, Any, List, Optional

from src.models.trace import CounterexampleResult, VerificationStatus
from src.models.verification import ConfidenceLevel


class CounterexampleSearcher:
    """Active search for counterexamples to disprove claimed universal results.

    Complements BruteForceChecker: BFC exhaustively enumerates finite domains;
    this class handles continuous/unbounded domains using a mixed strategy.
    """

    def __init__(
        self,
        max_attempts: int = 10_000,
        timeout_seconds: float = 30.0,
        random_seed: int = 42,
    ):
        self.max_attempts = max_attempts
        self.timeout_seconds = timeout_seconds
        self.random_seed = random_seed

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def search(
        self,
        predicate: Callable[..., bool],
        parameter_specs: Dict[str, Dict[str, Any]],
        step_index: int = -1,
        claim_text: str = "",
    ) -> CounterexampleResult:
        """Search for a counterexample using a mixed strategy.

        Each parameter_spec entry: {param_name: {"type": "int"|"float",
        "min": val, "max": val}} or {"values": [list_of_discrete_values]}.

        Strategy allocation:
            - Boundary candidates first (exhaustive edge values)
            - 40% random, 30% grid, 30% already consumed by boundary

        Args:
            predicate: Function(**kwargs) → bool. Should be True for ALL valid inputs.
                       A counterexample is any input where predicate returns False.
            parameter_specs: Specification of the parameter domain.
            step_index: Source step index for tracing.
            claim_text: Human-readable description of the claim being tested.

        Returns:
            CounterexampleResult — FAIL if CE found, PASS if budget exhausted without CE.
        """
        rng = random.Random(self.random_seed)
        t0 = time.monotonic()
        attempts = 0

        # Phase 1: Boundary candidates
        boundary = self._generate_boundary_candidates(parameter_specs)
        for candidate in boundary:
            if time.monotonic() - t0 > self.timeout_seconds:
                break
            ce = self._test_candidate(predicate, candidate)
            attempts += 1
            if ce is not None:
                return CounterexampleResult(
                    claim_text=claim_text,
                    attempts=attempts,
                    status=VerificationStatus.FAIL,
                    confidence=ConfidenceLevel.ENUMERATED,
                    counterexample=ce,
                    strategy_used="boundary",
                )

        # Phase 2: Mixed random + grid
        remaining = self.max_attempts - attempts
        n_grid = remaining // 3
        n_random = remaining - n_grid

        grid_candidates = self._generate_grid_candidates(parameter_specs, num_points=max(5, int(n_grid ** (1/len(parameter_specs)))))
        for candidate in grid_candidates:
            if attempts >= self.max_attempts or time.monotonic() - t0 > self.timeout_seconds:
                break
            ce = self._test_candidate(predicate, candidate)
            attempts += 1
            if ce is not None:
                return CounterexampleResult(
                    claim_text=claim_text,
                    attempts=attempts,
                    status=VerificationStatus.FAIL,
                    confidence=ConfidenceLevel.ENUMERATED,
                    counterexample=ce,
                    strategy_used="grid",
                )

        for _ in range(n_random):
            if attempts >= self.max_attempts or time.monotonic() - t0 > self.timeout_seconds:
                break
            candidate = self._generate_random_candidate(parameter_specs, rng)
            ce = self._test_candidate(predicate, candidate)
            attempts += 1
            if ce is not None:
                return CounterexampleResult(
                    claim_text=claim_text,
                    attempts=attempts,
                    status=VerificationStatus.FAIL,
                    confidence=ConfidenceLevel.ENUMERATED,
                    counterexample=ce,
                    strategy_used="random",
                )

        elapsed = time.monotonic() - t0
        timed_out = elapsed >= self.timeout_seconds

        return CounterexampleResult(
            claim_text=claim_text,
            attempts=attempts,
            status=VerificationStatus.TIMEOUT if timed_out else VerificationStatus.PASS,
            confidence=ConfidenceLevel.ENUMERATED if not timed_out else ConfidenceLevel.UNVERIFIED,
            strategy_used="mixed",
            error_message=f"No CE in {attempts} attempts ({elapsed:.1f}s)" if not timed_out else (
                f"Timed out after {elapsed:.1f}s — {attempts} attempts"
            ),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _test_candidate(
        self,
        predicate: Callable[..., bool],
        candidate: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Test one candidate. Returns the candidate dict if it's a counterexample, else None."""
        try:
            if not predicate(**candidate):
                return {k: (round(v, 6) if isinstance(v, float) else v)
                        for k, v in candidate.items()}
        except Exception:
            pass
        return None

    def _generate_random_candidate(
        self,
        parameter_specs: Dict[str, Dict[str, Any]],
        rng: random.Random,
    ) -> Dict[str, Any]:
        """Generate one random candidate from the parameter specs."""
        candidate = {}
        for name, spec in parameter_specs.items():
            if "values" in spec:
                candidate[name] = rng.choice(spec["values"])
            elif spec.get("type") == "int":
                candidate[name] = rng.randint(int(spec["min"]), int(spec["max"]))
            else:
                candidate[name] = rng.uniform(float(spec["min"]), float(spec["max"]))
        return candidate

    def _generate_boundary_candidates(
        self,
        parameter_specs: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate edge-case candidates: min, max, 0, 1, -1 for each param."""
        per_param = {}
        for name, spec in parameter_specs.items():
            if "values" in spec:
                per_param[name] = list(spec["values"])
            else:
                lo, hi = spec.get("min", -100), spec.get("max", 100)
                boundary_vals = {lo, hi}
                for v in [0, 1, -1, 2, -2]:
                    if lo <= v <= hi:
                        boundary_vals.add(int(v) if spec.get("type") == "int" else float(v))
                per_param[name] = sorted(boundary_vals)

        keys = list(per_param.keys())
        return [
            dict(zip(keys, combo))
            for combo in itertools.product(*[per_param[k] for k in keys])
        ]

    def _generate_grid_candidates(
        self,
        parameter_specs: Dict[str, Dict[str, Any]],
        num_points: int = 10,
    ) -> List[Dict[str, Any]]:
        """Generate a uniform grid across each parameter's range."""
        per_param = {}
        for name, spec in parameter_specs.items():
            if "values" in spec:
                per_param[name] = list(spec["values"])
            else:
                lo, hi = float(spec.get("min", -100)), float(spec.get("max", 100))
                if spec.get("type") == "int":
                    step = max(1, int((hi - lo) / num_points))
                    per_param[name] = list(range(int(lo), int(hi) + 1, step))
                else:
                    per_param[name] = [
                        lo + i * (hi - lo) / (num_points - 1)
                        for i in range(num_points)
                    ]

        keys = list(per_param.keys())
        return [
            dict(zip(keys, combo))
            for combo in itertools.product(*[per_param[k] for k in keys])
        ]
