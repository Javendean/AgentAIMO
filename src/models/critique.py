"""Critique data models for AgentAIMO.

Typed dataclasses produced by the FlawDetector (src/critique/flaw_detector.py).
Complements VerificationReport (mechanical checks) with NL-level flaw detection.

Phase 3 implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet


# ---------------------------------------------------------------------------
# Flaw taxonomy (sourced from annotated traces)
# ---------------------------------------------------------------------------

class FlawCode:
    """String constants for flaw codes from the annotated trace taxonomy.

    Source files:
        data/research/annotated_traces       — pipe-format, aime_2024_3
        data/research/annotated_traces.yml   — YAML,        aime_2023_1

    High-frequency codes that the FlawDetector checks for offline:
    """
    # Structural / protocol violations
    CHANNEL_LEAKAGE           = "CHANNEL_LEAKAGE"           # analysis... / assistantcommentary tokens
    PROMPT_LEAKAGE            = "PROMPT_LEAKAGE"            # User instructions in answer field
    NON_ATOMIC_FIELD          = "NON_ATOMIC_FIELD"          # Planning text in a supposed answer field
    TRUNCATED_TEXT            = "TRUNCATED_TEXT"            # Field ends mid-sentence

    # Execution quality
    MISSING_FINAL_COMMIT      = "MISSING_FINAL_COMMIT"      # Answer derived but never committed
    PSEUDO_VERIFICATION       = "PSEUDO_VERIFICATION"       # PASSED without showing computed value
    NON_EXECUTABLE_CODE       = "NON_EXECUTABLE_CODE"       # Prose injected into code block → SyntaxError
    MALFORMED_TOOL_CALL       = "MALFORMED_TOOL_CALL"       # assistantcommentary embedded in prose
    RESULT_NOT_SURFACED       = "RESULT_NOT_SURFACED"       # Computed result not printed/used

    # Reasoning quality
    CONTEXT_CONFABULATION     = "CONTEXT_CONFABULATION"     # Asks for missing prior context
    NONTERMINATING_WORKFLOW   = "NONTERMINATING_WORKFLOW"   # Keeps re-solving after answer known
    REDUNDANT_RECOMPUTATION   = "REDUNDANT_RECOMPUTATION"   # Same computation done multiple times
    WRONG_ANSWER              = "WRONG_ANSWER"              # Numeric conclusion is wrong (GT needed)
    FALSE_STATUS              = "FALSE_STATUS"              # solved/verification_passed contradicts content

    # Math correctness (annotation-only, not auto-detectable)
    COUNTING_ERROR            = "COUNTING_ERROR"
    INVALID_CONDITIONING      = "INVALID_CONDITIONING"
    PERSON_COUNT_ERROR        = "PERSON_COUNT_ERROR"
    BAD_DENOMINATOR           = "BAD_DENOMINATOR"
    BAD_NUMERATOR             = "BAD_NUMERATOR"
    UNSUPPORTED_PATTERN       = "UNSUPPORTED_PATTERN_GENERALIZATION"
    TERMINOLOGY_ERROR         = "TERMINOLOGY_ERROR"


# ---------------------------------------------------------------------------
# Typed results
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FlawResult:
    """One detected flaw instance within a solution text.

    Severity scale (matches annotated trace convention):
        5 = Critical — directly causes wrong answer or complete failure
        4 = Major    — corrupts key structural field
        3 = Moderate — degrades quality noticeably
        2 = Minor    — nuisance, doesn't change math
        1 = Cosmetic — style issue only
    """
    flaw_code: str          # One of the FlawCode constants
    severity: int           # 1–5
    excerpt: str            # Short substring that triggered the detection (≤80 chars)
    note: str               # Human-readable explanation


@dataclass
class CritiqueReport:
    """Aggregate critique for one solution attempt.

    Produced by FlawDetector.detect_all().
    Intended to sit alongside VerificationReport in the AuditRecord.
    """
    solution_text: str
    flaws: list[FlawResult] = field(default_factory=list)

    @property
    def flaw_codes(self) -> FrozenSet[str]:
        """Unique set of flaw codes found."""
        return frozenset(f.flaw_code for f in self.flaws)

    @property
    def severity_total(self) -> int:
        """Sum of all flaw severities. Higher = worse trace."""
        return sum(f.severity for f in self.flaws)

    @property
    def max_severity(self) -> int:
        """Highest single flaw severity (0 if no flaws)."""
        return max((f.severity for f in self.flaws), default=0)

    @property
    def is_clean(self) -> bool:
        """True if no flaws with severity ≥ 3. A clean trace has minor issues only."""
        return self.max_severity < 3

    @property
    def has_critical(self) -> bool:
        """True if any flaw has severity 5."""
        return any(f.severity == 5 for f in self.flaws)

    def summary(self) -> str:
        """One-line summary for logging."""
        if not self.flaws:
            return "CLEAN"
        codes = ", ".join(sorted(self.flaw_codes))
        return f"FLAWED(severity={self.severity_total}, codes=[{codes}])"
