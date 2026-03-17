"""Shared trace and verification result models.

This module contains the typed dataclasses used by the verification battery:
VerificationResult, ArithmeticCheckResult, SymbolicCheckResult, and SolutionTrace.
All stubs in src/verification/ import from here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List

from src.models.solution import SolutionTrace, ExtractedCalculation, SolutionStep, StepType  # re-export
from src.models.problem import Problem  # re-export
from src.models.verification import ConfidenceLevel  # re-export


# ---------------------------------------------------------------------------
# Verification status enumeration
# ---------------------------------------------------------------------------

class VerificationStatus(Enum):
    """Outcome of a single verification check."""
    PASS = "PASS"
    FAIL = "FAIL"
    SUSPICIOUS = "SUSPICIOUS"   # Code ran but output unrelated to claimed answer
    TIMEOUT = "TIMEOUT"         # Checker exceeded time budget
    ERROR = "ERROR"             # Checker itself crashed
    SKIPPED = "SKIPPED"         # No applicable check for this trace type


# ---------------------------------------------------------------------------
# Generic verification result (used by AnswerValidator)
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    """The outcome of any single verification check."""
    status: VerificationStatus
    confidence: ConfidenceLevel
    message: str = ""
    detail: Optional[dict] = None   # Checker-specific structured data


# ---------------------------------------------------------------------------
# Arithmetic checker result
# ---------------------------------------------------------------------------

@dataclass
class ArithmeticCheckResult:
    """Result of checking one extracted calculation against recomputation."""
    expression: str
    claimed_result: str
    computed_result: Optional[str]
    status: VerificationStatus
    confidence: ConfidenceLevel = ConfidenceLevel.LEVEL_0_EXACT
    error_message: str = ""

    @property
    def passed(self) -> bool:
        return self.status == VerificationStatus.PASS


# ---------------------------------------------------------------------------
# Symbolic checker result
# ---------------------------------------------------------------------------

@dataclass
class SymbolicCheckResult:
    """Result of a SymPy-based symbolic verification."""
    check_type: str                  # "identity", "inequality", "substitution"
    expression_lhs: str
    expression_rhs: str
    status: VerificationStatus
    confidence: ConfidenceLevel = ConfidenceLevel.LEVEL_1_SYMBOLIC
    counterexample: Optional[dict] = None   # {var_name: value} if counterexample found
    error_message: str = ""

    @property
    def passed(self) -> bool:
        return self.status == VerificationStatus.PASS


# ---------------------------------------------------------------------------
# Brute-force checker result
# ---------------------------------------------------------------------------

@dataclass
class BruteForceResult:
    """Result of an exhaustive enumeration check."""
    check_type: str                 # "counting", "universal", "optimization", "existence"
    domain_size: int                # Total cases enumerated
    status: VerificationStatus
    confidence: ConfidenceLevel = ConfidenceLevel.ENUMERATED
    claimed_value: Optional[int] = None     # The value the solution claimed
    found_value: Optional[int] = None       # What enumeration actually found
    witness: Optional[dict] = None          # {var: val} for existence / first-failure
    error_message: str = ""

    @property
    def passed(self) -> bool:
        return self.status == VerificationStatus.PASS


# ---------------------------------------------------------------------------
# Counterexample search result
# ---------------------------------------------------------------------------

@dataclass
class CounterexampleResult:
    """Result of an active counterexample search."""
    claim_text: str
    attempts: int
    status: VerificationStatus      # PASS = no CE found; FAIL = CE found; TIMEOUT
    confidence: ConfidenceLevel = ConfidenceLevel.ENUMERATED
    counterexample: Optional[dict] = None   # {var: val} if found
    strategy_used: str = ""         # "random", "boundary", "grid", "mixed"
    error_message: str = ""

    @property
    def found_counterexample(self) -> bool:
        return self.counterexample is not None
