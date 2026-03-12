"""Data models for solving schemas and their validation."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SchemaTrigger:
    """Conditions under which a schema should be applied.

    Attributes:
        category: Broad category type.
        keywords: Required keywords to activate.
        structural_pattern: Regex or AST pattern.
        negative_indicators: Keywords that suppress activation.
    """
    category: str = "any"
    keywords: tuple[str, ...] = ()
    structural_pattern: str = ""
    negative_indicators: tuple[str, ...] = ()


@dataclass
class SchemaStep:
    """A logical step to be followed when enacting a schema.

    Attributes:
        index: Ordered step sequence.
        instruction: NL instruction given to solver.
        mathematical_content: Equations or relations describing the step.
        verification_hint: Clue on how to automatically verify this step.
        prerequisites: Previous step indices this one relies on.
    """
    index: int
    instruction: str
    mathematical_content: str = ""
    verification_hint: str = ""
    prerequisites: list[int] = field(default_factory=list)


@dataclass
class SchemaValidation:
    """Historical performance metrics of a schema.

    Attributes:
        train_problems_tested: Total training problems where applied.
        train_accuracy_with: Solve rate when schema is used.
        train_accuracy_without: Solve rate when schema is inactive.
        validation_problems_tested: Total eval problems tested.
        validation_accuracy_with: Solve rate when schema is used.
        validation_accuracy_without: Solve rate when schema is inactive.
    """
    train_problems_tested: int = 0
    train_accuracy_with: float = 0.0
    train_accuracy_without: float = 0.0
    validation_problems_tested: int = 0
    validation_accuracy_with: float = 0.0
    validation_accuracy_without: float = 0.0

    @property
    def is_validated(self) -> bool:
        """Whether schema has proven significantly useful.

        Returns:
            bool: True if tested on >=5 eval problems and provides a lift.
        """
        return (self.validation_problems_tested >= 5 and
                self.validation_accuracy_with > self.validation_accuracy_without)

    @property
    def validation_delta(self) -> float:
        """The absolute difference in solve rate during validation.

        Returns:
            float: Lift in accuracy (with - without).
        """
        return self.validation_accuracy_with - self.validation_accuracy_without


@dataclass
class Schema:
    """A reusable solving tactic for mathematical problems.

    Attributes:
        schema_id: Unique identifier.
        name: Human-readable name.
        description: Explanation of what it achieves.
        trigger: Activation constraints.
        steps: Logical instruction sequence.
        source_problems: Problem IDs that inspired this schema.
        validation: Historical performance data.
        version: Revision counter.
    """
    schema_id: str
    name: str
    description: str
    trigger: SchemaTrigger
    steps: list[SchemaStep]
    source_problems: list[str]
    validation: Optional[SchemaValidation] = None
    version: int = 1
