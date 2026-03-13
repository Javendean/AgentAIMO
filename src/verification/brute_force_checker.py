"""Brute force verification by enumerating small finite domains."""

from typing import Callable, Dict, Any
from src.models.trace import BruteForceResult

class BruteForceChecker:
    """Exhaustive enumeration for claims over finite domains."""

    def __init__(self, max_cases: int = 1_000_000, timeout_seconds: float = 60.0):
        self.max_cases = max_cases
        self.timeout_seconds = timeout_seconds

    def check_counting_claim(self, predicate: Callable[..., bool], parameter_ranges: Dict[str, Any],
                             claimed_count: int, step_index: int = -1) -> 'BruteForceResult':
        """Verify counting claim by enumeration."""
        raise NotImplementedError("Agent must implement this method.")

    def check_universal_claim(self, predicate: Callable[..., bool], parameter_ranges: Dict[str, Any],
                              step_index: int = -1) -> 'BruteForceResult':
        """Verify 'for all' claim. Short-circuit on first failure."""
        raise NotImplementedError("Agent must implement this method.")

    def check_optimization_claim(self, objective: Callable[..., float], parameter_ranges: Dict[str, Any],
                                 claimed_optimum: float, optimization_type: str,
                                 step_index: int = -1) -> 'BruteForceResult':
        """Verify max/min claim by exhaustive search."""
        raise NotImplementedError("Agent must implement this method.")

    def check_existence_claim(self, predicate: Callable[..., bool], parameter_ranges: Dict[str, Any],
                              step_index: int = -1) -> 'BruteForceResult':
        """Verify existence. Short-circuit on first success."""
        raise NotImplementedError("Agent must implement this method.")
