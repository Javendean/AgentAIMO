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

## 2026-03-21 - P4-C2
- **What was implemented**: Updated Cell 7 in `notebook/kaggle_notebook.py` to use `selector.select_two()` instead of `selector.select()`. Attempt 1 = highest-confidence answer; Attempt 2 = highest-confidence disagreeing answer. Fallback: when `second_answer is None`, use first answer for both attempts (with original reason/confidence).
- **Files changed**:
  - `notebook/kaggle_notebook.py` — rewrote Cell 7 body: replaced `selector.select()` call with `selector.select_two()`, unpacked both tuples, added None-fallback for attempt 2, updated output record schema (`attempt_1`, `attempt_2` keys).
- **Learnings:**
  - `select_two()` was already implemented (P4-C1) — this task was purely the notebook integration.
  - The fallback logic reuses `_second_reason` before falling back to `_reason` to preserve the "no_disagreement" signal in the log.
  - Pre-existing 15 failures in `test_verification_battery.py` are unrelated and unchanged.
---

## 2026-03-21 - P4-C1
- **What was implemented**: Added `select_two()` method to `AnswerSelector` per PHASE4_HANDOFF.md Track C. Returns `(best, second_best_disagreeing)` as two `(answer, reason, confidence)` tuples. Added 3 new tests.
- **Files changed**:
  - `src/solver/answer_selector.py` — added `select_two()` between `select()` and `_majority_vote()`
  - `tests/test_phase3.py` — added `test_select_two_returns_different_answers`, `test_select_two_when_unanimous`, `test_select_two_with_all_none_answers`
- **Learnings:**
  - `select()` returns `"no_answer_extracted"` (not `"no_answer"`) when no answers are found — test must use `"no_answer" in first[1]` or match the exact string
  - Tests must be run with `PYTHONPATH=/home/user/AgentAIMO` since there's no package install; `pytest` itself is at `/root/.local/bin/pytest`
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

