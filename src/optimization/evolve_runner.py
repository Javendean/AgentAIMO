"""OpenEvolve runner for optimization campaigns."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class OpenEvolveConfig:
    """Configuration for an OpenEvolve optimization run."""
    initial_program_path: Path
    eval_function_path: Path
    output_dir: Path = Path("src/optimization/evolved")
    population_size: int = 15
    max_iterations: int = 100
    llm_models: list[str] = field(default_factory=lambda: ["gpt-oss-20b", "gpt-oss-120b"])
    cost_ceiling_usd: float = 50.0
    protected_functions: list[str] = field(default_factory=list)
    protected_imports: list[str] = field(default_factory=list)


class OpenEvolveRunner:
    """Runner for OpenEvolve optimization campaigns."""

    def __init__(self, config: OpenEvolveConfig) -> None:
        """Initialize runner with config."""
        self.config = config

    def run(self) -> dict[str, Any]:
        """Execute evolution campaign.

        Returns:
            dict with best_score, baseline_score, improvement,
            best_program_path, iterations, cost.
        """
        raise NotImplementedError("Runner execution to be implemented.")

    def validate_candidate(self, candidate_path: Path) -> tuple[bool, str]:
        """Check protected functions unchanged, valid Python, no forbidden ops."""
        raise NotImplementedError("Validation logic to be implemented.")

    def diff_against_baseline(self, candidate_path: Path) -> str:
        """Unified diff for human review."""
        raise NotImplementedError("Diff logic to be implemented.")
