"""Problem and metadata data models."""

import enum
from dataclasses import dataclass, field
from typing import Optional


class ProblemCategory(enum.Enum):
    """Categories of mathematical problems."""
    ALGEBRA = "algebra"
    COMBINATORICS = "combinatorics"
    GEOMETRY = "geometry"
    NUMBER_THEORY = "number_theory"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProblemMetadata:
    """Metadata about a problem's source and classification.

    Attributes:
        source: Origin (e.g., "aimo3_public", "aime_2024").
        problem_id: Unique identifier within source.
        category: Mathematical category.
        difficulty_estimate: Float in [0, 1] where 1 is hardest. None if unknown.
        ground_truth_answer: Known correct answer if available. None for competition.
        tags: Free-form tags (e.g., ("vieta_jumping", "modular_arithmetic")).
    """
    source: str
    problem_id: str
    category: ProblemCategory = ProblemCategory.UNKNOWN
    difficulty_estimate: Optional[float] = None
    ground_truth_answer: Optional[int] = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Problem:
    """A single competition problem.

    Attributes:
        text: Full natural language problem statement.
        metadata: Classification and source information.
        raw_latex: Original LaTeX if available.
    """
    text: str
    metadata: ProblemMetadata
    raw_latex: Optional[str] = None

    def __post_init__(self) -> None:
        """Validates problem data after initialization.

        Raises:
            ValueError: If text is empty or ground_truth_answer is out of bounds.
        """
        if not self.text:
            raise ValueError("Problem text cannot be empty.")

        if self.metadata.ground_truth_answer is not None:
            ans = self.metadata.ground_truth_answer
            if not (0 <= ans <= 99999):
                raise ValueError(f"Ground truth answer {ans} must be in [0, 99999].")
