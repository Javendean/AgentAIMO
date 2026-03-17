"""Confidence-weighted answer selector for AgentAIMO.

Replaces the raw Counter-based majority vote in deep_researcher.py with a
typed, confidence-aware selection policy. Implements Bug #4 fix from
FORWARD_PLAN_v2.md: superficial vote tallying → typed VerificationReport weighting.

Selection hierarchy (highest → lowest priority):
  1. Answers with LEVEL_0_EXACT verification — weighted sum, highest wins
  2. Answers with LEVEL_1_SYMBOLIC / ENUMERATED verification — weighted sum
  3. Majority vote among all answers regardless of confidence
  4. If all else fails: single answer with highest individual confidence

Phase 3 implementation of the stub in src/solver/answer_selector.py.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Optional

from src.models.verification import ConfidenceLevel, VerificationReport


# ---------------------------------------------------------------------------
# Typed input: a single verified solution attempt
# ---------------------------------------------------------------------------

@dataclass
class AnnotatedSolution:
    """One solution attempt with extracted answer and verification metadata.

    Produced by the VerificationPipeline for each attempt in a problem record.
    """
    final_answer: Optional[int]          # Extracted canonical integer (or None)
    report: VerificationReport           # Typed verification result
    attempt_id: int = 0                  # 0-indexed attempt number
    raw_text: str = ""                   # Solution text (for debugging)


# ---------------------------------------------------------------------------
# Weight map: ConfidenceLevel → vote weight
# ---------------------------------------------------------------------------

_WEIGHTS: dict[str, float] = {
    ConfidenceLevel.LEVEL_0_EXACT.value:    10.0,
    ConfidenceLevel.LEVEL_1_SYMBOLIC.value:  5.0,
    ConfidenceLevel.LEVEL_2_FORMAL.value:   4.0,
    ConfidenceLevel.ENUMERATED.value:        4.0,
    ConfidenceLevel.NL_JUDGMENT.value:       1.0,
    ConfidenceLevel.UNVERIFIED.value:        0.1,
}


def _weight(report: VerificationReport) -> float:
    return _WEIGHTS.get(report.confidence.value, 0.1)


# ---------------------------------------------------------------------------
# AnswerSelector
# ---------------------------------------------------------------------------

class AnswerSelector:
    """Select the best final answer from a list of verified solution attempts.

    Phase 3 full implementation — replaces NotImplementedError stubs.
    """

    def select(
        self,
        annotated_solutions: list[AnnotatedSolution],
    ) -> tuple[Optional[int], str, float]:
        """Return (best_answer, reason, confidence_score).

        Args:
            annotated_solutions: All attempts for one problem, already parsed+verified.

        Returns:
            Tuple of:
                best_answer  — The selected integer answer, or None if nothing found.
                reason       — Short human-readable string explaining why.
                confidence   — Normalised score in [0, 1].
        """
        if not annotated_solutions:
            return None, "no_attempts", 0.0

        # Only consider solutions with a valid extracted answer
        with_answer = [s for s in annotated_solutions if s.final_answer is not None]
        if not with_answer:
            return None, "no_answer_extracted", 0.0

        # --- Strategy 1: weighted vote among solutions with strong verification ---
        strong = [s for s in with_answer
                  if s.report.confidence in (
                      ConfidenceLevel.LEVEL_0_EXACT,
                      ConfidenceLevel.LEVEL_1_SYMBOLIC,
                      ConfidenceLevel.LEVEL_2_FORMAL,
                      ConfidenceLevel.ENUMERATED,
                  )]
        if strong:
            answer, score = self._weighted_vote(strong)
            if answer is not None:
                # Normalise score against the maximum weight * number of attempts
                max_possible = _WEIGHTS[ConfidenceLevel.LEVEL_0_EXACT.value] * len(strong)
                normalised = min(score / max_possible, 1.0) if max_possible > 0 else 0.0
                return answer, "confidence_weighted_vote", normalised

        # --- Strategy 2: weighted vote over all answers (includes NL_JUDGMENT) ---
        answer, score = self._weighted_vote(with_answer)
        if answer is not None:
            max_possible = _WEIGHTS[ConfidenceLevel.LEVEL_0_EXACT.value] * len(with_answer)
            normalised = min(score / max_possible, 1.0) if max_possible > 0 else 0.0
            return answer, "weak_weighted_vote", normalised

        # --- Strategy 3: plain majority vote (shouldn't usually reach here) ---
        maj_answer, maj_count, total = self._majority_vote(with_answer)
        if maj_answer is not None:
            return maj_answer, "majority_vote", maj_count / total
        return None, "vote_tie_unresolved", 0.0

    def _majority_vote(
        self,
        solutions: list[AnnotatedSolution],
    ) -> tuple[Optional[int], int, int]:
        """Plain Counter majority vote.

        Returns (winner, winner_count, total_count).
        """
        if not solutions:
            return None, 0, 0
        counts: Counter[int] = Counter(
            s.final_answer for s in solutions if s.final_answer is not None
        )
        if not counts:
            return None, 0, len(solutions)
        winner, count = counts.most_common(1)[0]
        return winner, count, len(solutions)

    def _weighted_vote(
        self,
        solutions: list[AnnotatedSolution],
    ) -> tuple[Optional[int], float]:
        """Weighted Counter vote.

        Each vote is worth _weight(report). Returns (winner, winner_weight_sum).
        """
        if not solutions:
            return None, 0.0
        weighted: dict[int, float] = {}
        for s in solutions:
            if s.final_answer is None:
                continue
            w = _weight(s.report)
            weighted[s.final_answer] = weighted.get(s.final_answer, 0.0) + w
        if not weighted:
            return None, 0.0
        winner = max(weighted, key=lambda k: weighted[k])
        return winner, weighted[winner]
