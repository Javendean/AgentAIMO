"""Evaluation function for OpenEvolve."""

from pathlib import Path
from typing import Any

from src.models.problem import Problem


class AIMOEvaluator:
    """Evaluate candidate solver scripts against a problem set."""

    def __init__(
        self,
        problems: list[Problem],
        storage: Any = None,
        timeout_per_problem_seconds: float = 300.0,
        total_timeout_seconds: float = 3600.0,
    ) -> None:
        self.problems = problems
        self.storage = storage
        self.timeout_per_problem_seconds = timeout_per_problem_seconds
        self.total_timeout_seconds = total_timeout_seconds

    def evaluate(self, candidate_script_path: Path) -> dict[str, float]:
        """Dynamically import candidate, run on problems, return metrics dict.

        Metrics: accuracy, avg_time_per_problem, timeout_rate, error_rate, total_wall_time.
        SAFETY: run in subprocess if possible.
        """
        raise NotImplementedError("Evaluation logic to be implemented.")

    def _safe_import_candidate(self, script_path: Path) -> Any:
        """importlib.util.spec_from_file_location. Validate solve() exists."""
        raise NotImplementedError("Safe import logic to be implemented.")
