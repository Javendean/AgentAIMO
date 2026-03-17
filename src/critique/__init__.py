"""src/critique — Offline NL flaw detection for AgentAIMO.

Modules:
    flaw_detector   — Regex + heuristic detector for the top flaw codes
                      from data/research/annotated_traces{,.yml}.

Phase 3 implementation. No live model API calls — fully reproducible offline.
"""

from src.critique.flaw_detector import FlawDetector

__all__ = ["FlawDetector"]
