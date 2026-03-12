"""Models for LLM critiques and human review data."""

import enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from src.models.verification import ConfidenceLevel, VerificationReport


class CritiqueSeverity(enum.Enum):
    """The severity of a flaw found in a step."""
    FATAL = "fatal"
    MAJOR = "major"
    MINOR = "minor"
    SUGGESTION = "suggestion"
    NO_FLAW = "no_flaw"


@dataclass
class CritiqueItem:
    """A single piece of critique directed at a solution step.

    Attributes:
        step_index: Source step.
        severity: Severity of the flaw.
        category: Type of flaw.
        description: Textual description.
        suggested_fix: Optional proposed fix.
        critic_model: Model that generated the critique.
    """
    step_index: int
    severity: CritiqueSeverity
    category: str
    description: str
    suggested_fix: str = ""
    critic_model: str = ""


@dataclass
class Critique:
    """A full critique on an attempted solution trace.

    Attributes:
        problem_id: Source problem ID.
        attempt_index: Attempt sequence number.
        critic_model: Model that generated the critique.
        items: List of critique points.
        overall_judgment: High-level classification (e.g., "uncertain").
        confidence_in_judgment: Float from 0.0 to 1.0.
        raw_response: The entire raw model output.
        cost_usd: Estimated cost of generation.
        wall_time_seconds: Generation time.
        timestamp: Time of generation.
    """
    problem_id: str
    attempt_index: int
    critic_model: str
    items: list[CritiqueItem] = field(default_factory=list)
    overall_judgment: str = "uncertain"
    confidence_in_judgment: float = 0.0
    raw_response: str = ""
    cost_usd: float = 0.0
    wall_time_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def has_fatal_flaws(self) -> bool:
        """Whether there is at least one fatal flaw identified.

        Returns:
            bool: True if fatal flaw exists, False otherwise.
        """
        return len(self.fatal_items) > 0

    @property
    def fatal_items(self) -> list[CritiqueItem]:
        """List of items with FATAL severity.

        Returns:
            list[CritiqueItem]: The FATAL items.
        """
        return [item for item in self.items if item.severity == CritiqueSeverity.FATAL]

    @property
    def major_items(self) -> list[CritiqueItem]:
        """List of items with MAJOR severity.

        Returns:
            list[CritiqueItem]: The MAJOR items.
        """
        return [item for item in self.items if item.severity == CritiqueSeverity.MAJOR]


@dataclass
class AnnotatedSolution:
    """A solution annotated with its critiques and verification results.

    Attributes:
        problem_id: Source problem ID.
        attempt_index: Attempt sequence number.
        final_answer: Extracted final integer answer.
        verification_report: Associated automated checks report.
        critiques: Model critiques.
        combined_confidence: Reconciled confidence.
        is_selected: If selected as best option.
        selection_reason: Justification for selection.
        human_review_needed: Whether human intervention is requested.
        human_review_reason: Reason for requiring human.
    """
    problem_id: str
    attempt_index: int
    final_answer: Optional[int]
    verification_report: Optional[VerificationReport] = None
    critiques: list[Critique] = field(default_factory=list)
    combined_confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    is_selected: bool = False
    selection_reason: str = ""
    human_review_needed: bool = False
    human_review_reason: str = ""

    @property
    def critics_agree(self) -> bool:
        """Whether all collected critiques have the exact same judgment.

        Returns:
            bool: True if all agree, False if they conflict or none exist.
        """
        if not self.critiques:
            return True
        first_judgment = self.critiques[0].overall_judgment
        return all(c.overall_judgment == first_judgment for c in self.critiques)

    @property
    def deterministic_and_nl_agree(self) -> bool:
        """Whether verification pass/fail matches NL criticism pass/fail.

        Returns:
            bool: True if they align.
        """
        if self.verification_report is None or not self.critiques:
            return False

        ver_pass = (self.verification_report.has_failures is False)
        # simplistic agreement map
        critic_pass = all(not c.has_fatal_flaws and not c.major_items for c in self.critiques)
        return ver_pass == critic_pass


@dataclass
class HumanReviewItem:
    """A work item for a human math reviewer.

    Attributes:
        problem_id: Source problem ID.
        attempt_index: Attempt sequence number.
        reason: Justification for assigning review.
        annotated_solution: The contested solution trace.
        priority: Prioritization string.
        resolved: Whether human verdict is submitted.
        human_verdict: The human's verdict text.
        timestamp: Time item created.
    """
    problem_id: str
    attempt_index: int
    reason: str
    annotated_solution: AnnotatedSolution
    priority: str = "medium"
    resolved: bool = False
    human_verdict: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
