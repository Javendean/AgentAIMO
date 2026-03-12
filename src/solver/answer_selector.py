"""Answer selection module for AgentAIMO."""

from typing import Optional, Tuple, List, Any

AnnotatedSolution = Any


class AnswerSelector:
    """Select best answer from annotated solution attempts.

    Hierarchy: LEVEL_0_EXACT > LEVEL_1_SYMBOLIC with critic agreement >
    majority vote among symbolic > majority vote all > highest confidence.
    """

    def select(self, annotated_solutions: List[AnnotatedSolution]) -> Tuple[Optional[int], str, float]:
        """Returns the best answer, reason, and confidence score.

        Args:
            annotated_solutions: A list of annotated solution attempts.

        Returns:
            A tuple containing the answer (if any), reason, and confidence score.
        """
        raise NotImplementedError

    def _majority_vote(self, solutions: List[AnnotatedSolution]) -> Tuple[Optional[int], int, int]:
        """Perform majority vote on the given solutions.

        Args:
            solutions: A list of annotated solution attempts.

        Returns:
            A tuple of the majority answer, the vote count, and total votes.
        """
        raise NotImplementedError

    def _weighted_vote(self, solutions: List[AnnotatedSolution]) -> Tuple[Optional[int], float]:
        """Perform a weighted vote based on solution levels.

        Weights: LEVEL_0=10, LEVEL_1=5, LEVEL_2=4, LEVEL_3=2, LEVEL_4=0.5, UNVERIFIED=0.1

        Args:
            solutions: A list of annotated solution attempts.

        Returns:
            A tuple of the weighted answer and its score.
        """
        raise NotImplementedError
