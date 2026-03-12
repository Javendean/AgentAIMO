"""Solution generation and extraction data models."""

import enum
from dataclasses import dataclass, field
from typing import Optional


class StepType(enum.Enum):
    """Types of logical steps within a solution trace."""
    ARITHMETIC = "arithmetic"
    ALGEBRAIC_IDENTITY = "algebraic"
    INEQUALITY_CLAIM = "inequality"
    SUBSTITUTION = "substitution"
    CASE_SPLIT = "case_split"
    COUNTING = "counting"
    LOGICAL_DEDUCTION = "logical"
    GEOMETRIC_CLAIM = "geometric"
    FINAL_ANSWER = "final_answer"
    NARRATIVE = "narrative"
    UNKNOWN = "unknown"


@dataclass
class ExtractedCalculation:
    """A single arithmetic or algebraic operation extracted from a step.

    Attributes:
        expression: The mathematical expression extracted.
        claimed_result: The result claimed by the model.
        step_index: The index of the step where this was extracted.
        context: Optional surrounding context text.
    """
    expression: str
    claimed_result: str
    step_index: int
    context: str = ""


@dataclass
class SolutionStep:
    """A single logical step within a solution trace.

    Attributes:
        index: Step index in the solution sequence.
        text: The text content of the step.
        step_type: Type of logical reasoning step.
        calculations: Any extracted mathematical calculations.
        depends_on: List of previous step indices this step logically depends on.
    """
    index: int
    text: str
    step_type: StepType = StepType.UNKNOWN
    calculations: list[ExtractedCalculation] = field(default_factory=list)
    depends_on: list[int] = field(default_factory=list)


@dataclass
class SolutionTrace:
    """A complete solution attempt for one problem.

    Attributes:
        problem_id: ID of the problem being solved.
        raw_text: The full raw output text from the model.
        steps: The parsed logical steps.
        final_answer: Extracted final integer answer.
        model_id: Model identifier used to generate.
        temperature: Temperature setting.
        generation_time_seconds: Wall time taken to generate.
        token_count: Number of tokens generated.
        attempt_index: Index of this attempt among multiple trials.
    """
    problem_id: str
    raw_text: str
    steps: list[SolutionStep] = field(default_factory=list)
    final_answer: Optional[int] = None
    model_id: str = ""
    temperature: float = 0.0
    generation_time_seconds: float = 0.0
    token_count: int = 0
    attempt_index: int = 0

    @property
    def is_parsed(self) -> bool:
        """Whether the solution has been successfully parsed into steps.

        Returns:
            bool: True if there is at least one parsed step, False otherwise.
        """
        return len(self.steps) > 0

    @property
    def has_valid_answer(self) -> bool:
        """Whether a valid integer final answer in [0, 99999] was extracted.

        Returns:
            bool: True if answer is valid, False otherwise.
        """
        if self.final_answer is None:
            return False
        if not isinstance(self.final_answer, int):
            return False
        return 0 <= self.final_answer <= 99999
