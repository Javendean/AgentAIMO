"""Solution models."""

from dataclasses import dataclass, field
from enum import Enum


class StepType(Enum):
    """Types of steps in a solution trace."""
    CALCULATION = "CALCULATION"
    LOGIC = "LOGIC"
    CODE = "CODE"
    ASSUMPTION = "ASSUMPTION"


@dataclass(frozen=True)
class ExtractedCalculation:
    """An explicit calculation extracted from a step."""
    expression: str
    result: str


@dataclass(frozen=True)
class SolutionStep:
    """A step in a solution trace."""
    step_num: int
    text: str
    step_type: StepType
    calculations: list[ExtractedCalculation] = field(default_factory=list)


@dataclass
class SolutionTrace:
    """A solution trace for a problem."""
    raw_text: str
    steps: list[SolutionStep] = field(default_factory=list)
    final_answer: int | None = None

    @property
    def is_parsed(self) -> bool:
        """Check if trace has been parsed into steps."""
        return len(self.steps) > 0

    @property
    def has_valid_answer(self) -> bool:
        """Check if trace has a valid answer."""
        return self.final_answer is not None and 0 <= self.final_answer <= 99999
