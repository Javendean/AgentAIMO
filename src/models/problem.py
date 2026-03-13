"""Problem models."""

from dataclasses import dataclass
from enum import Enum


class ProblemCategory(Enum):
    """Categories of math problems."""
    NUMBER_THEORY = "NUMBER_THEORY"
    ALGEBRA = "ALGEBRA"
    GEOMETRY = "GEOMETRY"
    COMBINATORICS = "COMBINATORICS"
    PROBABILITY = "PROBABILITY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ProblemMetadata:
    """Metadata for a problem."""
    source: str
    problem_id: str
    category: ProblemCategory
    difficulty: float


@dataclass(frozen=True)
class Problem:
    """A math problem to be solved."""
    text: str
    metadata: ProblemMetadata
    ground_truth: int | None = None

    def __post_init__(self) -> None:
        """Validate the problem."""
        if not self.text.strip():
            raise ValueError("Problem text cannot be empty.")
        if self.ground_truth is not None and not (0 <= self.ground_truth <= 99999):
            raise ValueError("Answer must be an integer from 0-99999.")
