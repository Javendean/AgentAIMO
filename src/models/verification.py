"""Verification models — confidence taxonomy and verification report.

ConfidenceLevel is the typed evidence taxonomy defined in evolution.md §§ Idea 2
and FORWARD_PLAN_v2.md §3. All verification modules MUST produce one of these
levels; they must never collapse to a boolean.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ConfidenceLevel(Enum):
    """Typed evidence taxonomy for verification outcomes.

    Ordered from strongest (LEVEL_0_EXACT) to weakest (UNVERIFIED).
    Use .strength property to compare programmatically.

    Levels:
        LEVEL_0_EXACT:    Deterministic recomputation confirms the value.
                          Python eval / arithmetic recomputation matched.
        LEVEL_1_SYMBOLIC: CAS (SymPy) confirms algebraic identity or equation.
        LEVEL_2_FORMAL:   Lean kernel acceptance (offline only — Kimina-Prover).
        ENUMERATED:       Brute-force checked all cases in a bounded domain.
        NL_JUDGMENT:      LLM review only — weakest signal, never sole selector.
        UNVERIFIED:       No mechanical check was attempted or possible.
    """
    LEVEL_0_EXACT    = "LEVEL_0_EXACT"
    LEVEL_1_SYMBOLIC = "LEVEL_1_SYMBOLIC"
    LEVEL_2_FORMAL   = "LEVEL_2_FORMAL"
    ENUMERATED       = "ENUMERATED"
    NL_JUDGMENT      = "NL_JUDGMENT"
    UNVERIFIED       = "UNVERIFIED"

    @property
    def strength(self) -> int:
        """Numeric strength for comparison (higher = stronger evidence)."""
        return {
            "LEVEL_0_EXACT":    5,
            "LEVEL_1_SYMBOLIC": 4,
            "LEVEL_2_FORMAL":   3,
            "ENUMERATED":       3,
            "NL_JUDGMENT":      1,
            "UNVERIFIED":       0,
        }[self.value]

    def __lt__(self, other: ConfidenceLevel) -> bool:
        return self.strength < other.strength

    def __le__(self, other: ConfidenceLevel) -> bool:
        return self.strength <= other.strength


@dataclass(frozen=True)
class VerificationReport:
    """Aggregate report produced by the verification pipeline for one trace.

    Contains the number of checks at each confidence level and an overall
    confidence rolled up to the strongest level with a PASS result.
    """
    passed_checks: int = 0
    failed_checks: int = 0
    suspicious_checks: int = 0
    # Strongest confidence level among all passing checks
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    # Structured breakdown: {ConfidenceLevel.value: {"pass": N, "fail": N}}
    breakdown: dict = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        """Fraction of checks that passed (suspicious counts against)."""
        total = self.passed_checks + self.failed_checks + self.suspicious_checks
        return self.passed_checks / total if total > 0 else 0.0

    @property
    def has_failures(self) -> bool:
        return self.failed_checks > 0 or self.suspicious_checks > 0

    @property
    def total_checks(self) -> int:
        return self.passed_checks + self.failed_checks + self.suspicious_checks
