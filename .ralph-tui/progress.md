# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

- **AnswerSelector minimal integration**: When building `AnnotatedSolution` from `Attempt` objects
  without real verification, use `VerificationReport(passed_checks=1 if answer is not None else 0,
  confidence=ConfidenceLevel.NL_JUDGMENT)` as the fallback report. All attempts get equal weight=1.0.

- **deep_researcher.py src/ import guard**: Use `try/except ImportError` with a boolean flag
  (`_ANSWER_SELECTOR_AVAILABLE`) to keep `deep_researcher.py` working even if `src/` is not on
  the path (e.g., older Kaggle deployments without the new codebase).

- **Attempt.extracted_answer is str|None**: `extract_answer()` returns a string like "42", not an int.
  Always convert with `int(att.extracted_answer)` when building `AnnotatedSolution.final_answer`.

---

## 2026-03-21 - P4-A2

- **What was implemented**: Added 3 instruction sections to `SYSTEM_PROMPT` in `agent/prompts.py` to address the top flaw codes from `BASELINE_METRICS.md`: `CONTEXT_CONFABULATION`, `MISSING_FINAL_COMMIT`, and `CHANNEL_LEAKAGE`.

- **Files changed**:
  - `agent/prompts.py` — added 3 new sections before `{patch_slot}`:
    - `## Self-Contained Problem Policy` — addresses `CONTEXT_CONFABULATION` (do not ask for prior context, solve from scratch)
    - `## Answer Format (MANDATORY)` — strengthens `MISSING_FINAL_COMMIT` (must use `**ANSWER: N**`, no prose variants)
    - `## Output Cleanliness` — addresses `CHANNEL_LEAKAGE` (no internal tool syntax like `assistantcommentary to=python`)

- **Learnings**:
  - SYSTEM_PROMPT already had step 7 "State your final answer clearly" but it was buried in a numbered list and not strongly worded. The new `## Answer Format (MANDATORY)` section is more prominent and explicit.
  - The 15 pre-existing failures in `test_verification_battery.py` remain unchanged — not caused by this task.

---

## 2026-03-21 - P4-A1

- **What was implemented**: Swapped Counter/majority_vote with `AnswerSelector.select()` in the
  final answer selection path of `deep_researcher.py`, and added a Cell 7 post-processing block
  to `notebook/kaggle_notebook.py` that calls `selector.select()` on saved JSONL traces.

- **Files changed**:
  - `agent/deep_researcher.py` — added `AnswerSelector` import (with `ImportError` guard + flag),
    replaced the raw `Counter.most_common()` final selection with `_AnswerSelector().select()`.
    Early-stopping consensus (wave-based) unchanged — that's a different concern.
  - `notebook/kaggle_notebook.py` — added Cell 7: imports `AnswerSelector`, iterates JSONL output,
    builds `AnnotatedSolution` list per trace, calls `selector.select()`, saves re-selected answers
    to `_reselected.jsonl`.

- **Learnings**:
  - The notebook itself had no Counter/majority_vote — that logic lived entirely in
    `deep_researcher.py._majority_vote()`. The task description pointed at the notebook but the
    actual implementation was one level deeper.
  - `Attempt.extracted_answer` is `str|None` ("42"), not `int|None`. Must cast to `int` for
    `AnnotatedSolution.final_answer`.
  - 15 pre-existing test failures in `test_verification_battery.py` (arithmetic/symbolic checkers)
    exist before this task and are not related to P4-A1.
  - `test_agent.py` and `test_hallucination_fix.py` fail to collect due to missing vllm dependency
    (Kaggle-only). Use `--ignore` when running tests locally.

---

