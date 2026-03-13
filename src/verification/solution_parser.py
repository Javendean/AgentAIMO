"""Solution parser for extracting structured steps from raw mathematical solutions."""

import re
from typing import Optional, List
from src.models.trace import SolutionTrace, StepType, ExtractedCalculation

class SolutionParser:
    """Parse raw solution text into classified, structured steps."""

    NUMBERED_STEP_PATTERN = re.compile(r"")
    CALCULATION_PATTERN = re.compile(r"")
    ANSWER_PATTERNS = [re.compile(r"")]

    def parse(self, trace: SolutionTrace) -> SolutionTrace:
        """Parse raw solution trace into structured steps."""
        raise NotImplementedError("Agent must implement this method.")

    def _split_into_steps(self, raw_text: str) -> List[str]:
        """Split text into candidate step strings."""
        raise NotImplementedError("Agent must implement this method.")

    def _classify_step(self, step_text: str) -> StepType:
        """Classify step type using keyword heuristics."""
        raise NotImplementedError("Agent must implement this method.")

    def _extract_calculations(self, step_text: str, step_index: int) -> List[ExtractedCalculation]:
        """Extract all explicit calculations. Handle: C(n,k), n!, a^b, LaTeX."""
        raise NotImplementedError("Agent must implement this method.")

    def _extract_final_answer(self, raw_text: str) -> Optional[int]:
        """Extract final integer answer. Prefer \\boxed{} > 'answer is' > last number."""
        raise NotImplementedError("Agent must implement this method.")
