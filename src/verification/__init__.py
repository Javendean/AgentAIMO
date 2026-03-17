"""Mathematical verification battery for AgentAIMO.

Imports are guarded per-module to avoid cascading failures from stubs
that are not yet implemented. Import each checker directly when needed.

Phase 1A complete:
    - AnswerValidator: fully implemented

Phase 1B (stubs — not yet imported here):
    - ArithmeticChecker, SymbolicChecker, BruteForceChecker,
      CounterexampleSearcher, SolutionParser, VerificationPipeline
"""

from src.verification.answer_validator import AnswerValidator, ExtractionResult, extract_canonical_answer

__all__ = [
    "AnswerValidator",
    "ExtractionResult",
    "extract_canonical_answer",
]
