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
        """Parse raw solution trace into structured steps.

        Implementation notes for agent:
        1. Split raw_text into steps using _split_into_steps()
        2. For each step: classify type, extract calculations, infer dependencies
        3. Extract final_answer using ANSWER_PATTERNS
        4. Return new SolutionTrace with steps populated

        Args:
            trace: Raw SolutionTrace containing raw_text.

        Returns:
            A new SolutionTrace with parsed steps.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")

    def _split_into_steps(self, raw_text: str) -> List[str]:
        """Split text into candidate step strings.
        Try numbered patterns first, fall back to double-newline, then sentence.

        Args:
            raw_text: The full text of the solution.

        Returns:
            A list of step strings.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")

    def _classify_step(self, step_text: str) -> StepType:
        """Classify step type using keyword heuristics.

        Args:
            step_text: The text of a single step.

        Returns:
            The StepType classification of the step.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")

    def _extract_calculations(self, step_text: str, step_index: int) -> List[ExtractedCalculation]:
        """Extract all explicit calculations. Handle: C(n,k), n!, a^b, LaTeX.

        Args:
            step_text: The text of a single step.
            step_index: The index of the step in the overall solution.

        Returns:
            A list of ExtractedCalculation objects found in the step.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")

    def _extract_final_answer(self, raw_text: str) -> Optional[int]:
        """Extract final integer answer. Prefer \\boxed{} > 'answer is' > last number.

        Args:
            raw_text: The full text of the solution.

        Returns:
            The final integer answer if found, otherwise None.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")
