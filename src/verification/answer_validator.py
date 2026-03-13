"""Final answer validation module."""

from typing import Optional, List
from src.models.problem import Problem
from src.models.trace import SolutionTrace, VerificationResult

class AnswerValidator:
    """Validate final answer format, range, and cross-solution consistency."""

    def validate_format(self, answer: Optional[int]) -> VerificationResult:
        """Check integer, in range [0, 99999].

        Args:
            answer: The extracted integer answer to evaluate.

        Returns:
            Verification result asserting that the format fits expected conventions.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")

    def validate_against_ground_truth(self, answer: Optional[int], problem: Problem) -> VerificationResult:
        """Check against known answer if available. LEVEL_0_EXACT confidence.

        Args:
            answer: Answer generated.
            problem: Reference context which contains real truth constraints.

        Returns:
            The verification result detailing the truth correspondence.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")

    def validate_cross_consistency(self, traces: List[SolutionTrace]) -> VerificationResult:
        """Check if multiple attempts agree. Report {answer: count} distribution.

        Args:
            traces: The list of multiple traces corresponding to the same context.

        Returns:
            The collective verification assessment indicating solution distributions.

        Raises:
            NotImplementedError: Agent must implement this method.
        """
        raise NotImplementedError("Agent must implement this method.")
