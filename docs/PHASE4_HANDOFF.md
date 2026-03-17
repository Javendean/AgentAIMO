# Phase 4 Handoff — AgentAIMO

**Date:** 2026-03-17  
**Competition deadline:** April 8 2026  
**For:** Claude Code  
**From:** Previous session (Antigravity agent)

---

## What Was Built (Phases 0–3)

### Current test count: 159/159 passing
```bash
python -m pytest tests/ -q   # verify this first
```

| Phase | Commits | What |
|---|---|---|
| 0 | Initial | Bug fixes: regex tightening, canary test, 74 tests |
| 1A | `7551334` | `AnswerValidator` — typed answer extraction with 5 confidence levels |
| 1B | `c57a4cc` | Typed verification battery — 6 checkers + pipeline |
| 2 | `(phase2)` | Ablation study + `_last_resort_extract()` prose-only extractor |
| 3 | `9f48db7` | `AnswerSelector` + `FlawDetector` + audit runner + `BASELINE_METRICS.md` |

### Baseline accuracy (from `docs/BASELINE_METRICS.md`)
| Dataset | Correct | Extract rate | Clean traces |
|---|---|---|---|
| `research_data.jsonl` (Submission 1) | 3/8 = 38% | 5.6% | **0%** |
| `research_data2.jsonl` (Baseline 6/10) | 6/8 = 75% | 21.1% | **0%** |

---

## What Phase 4 Needs to Do

The competition deadline is April 8. Phase 4 has three mandatory tracks and one stretch track. **Do Track A first — it directly improves the next submission.**

---

## Track A — Kaggle Notebook Integration (MANDATORY, do this first)

**Goal:** Replace the current `Counter`-based majority vote in the submitted notebook with the new `AnswerSelector` and prompt changes.

**Key files to read first:**
- `notebook/kaggle_notebook.py` — the production submission code
- `src/solver/answer_selector.py` — the new AnswerSelector (Phase 3)
- `docs/BASELINE_METRICS.md` — confirms what's broken and why

**The two changes needed:**

### Change 1: Swap majority vote for AnswerSelector

Find `_majority_vote` or `Counter` usage in `notebook/kaggle_notebook.py` and replace with:
```python
from src.solver.answer_selector import AnswerSelector, AnnotatedSolution
from src.models.verification import VerificationReport, ConfidenceLevel

selector = AnswerSelector()

# Build AnnotatedSolution list from existing attempts
annotated = [
    AnnotatedSolution(
        final_answer=attempt.extracted_answer,   # int or None
        report=attempt.verification_report,       # VerificationReport
        attempt_id=i,
    )
    for i, attempt in enumerate(attempts)
]
best_answer, reason, confidence = selector.select(annotated)
```

**Important:** The notebook may not have `VerificationReport` objects yet — if it doesn't, build minimal ones:
```python
# Minimal report for each attempt based on extraction confidence
report = VerificationReport(
    passed_checks=1 if attempt.extracted_answer is not None else 0,
    confidence=ConfidenceLevel.NL_JUDGMENT,  # conservative fallback
)
```

### Change 2: Add prompt reinforcement for the 3 top flaw codes

Every solution attempt uses a system/user prompt. Add these phrases to the prompt. They address the top flaw codes from `BASELINE_METRICS.md`:

```
IMPORTANT: This problem is fully self-contained. Do NOT ask for prior context, 
do NOT reference earlier results, do NOT say "continue from where you left off".
Solve it completely from scratch.

When you have determined the final answer, you MUST write it on its own line 
in exactly this format: **ANSWER: N** (where N is the integer, no other text).

Do NOT write answers like "the answer is N" or "m+n = N". Only the 
**ANSWER: N** format will be recorded.
```

This directly addresses:
- `CONTEXT_CONFABULATION` (100% rate on baseline) — "self-contained, don't ask for prior context"
- `MISSING_FINAL_COMMIT` — "you MUST write **ANSWER: N**"
- `CHANNEL_LEAKAGE` — may reduce `analysis...` token leakage as a side effect

**Verification after Track A:**
```bash
# Re-run ablation to confirm extract rate improves
python scripts/ablation_extraction.py

# Expected: extract_rate on research_data2.jsonl should increase from 21% toward 50%+
# Expected: MISSING_FINAL_COMMIT count should drop
```

---

## Track B — Prompt Hardening (do after Track A is verified)

The annotated trace files document exactly what the model does wrong:
- `data/research/annotated_traces` — `aime_2024_3` (pipe format)
- `data/research/annotated_traces.yml` — `aime_2023_1` (YAML format, canonical format)

**Top 3 actionable flaw codes (from `BASELINE_METRICS.md`):**

| Flaw | Rate | Fix |
|---|---|---|
| `CHANNEL_LEAKAGE` | 100% | `analysis...` / `assistantcommentary` tokens in output. Add to system prompt: "Do not output any internal tool markers or tokens. Your response must be clean human-readable text." |
| `MISSING_FINAL_COMMIT` | 38% | Already covered in Track A prompt change |
| `CONTEXT_CONFABULATION` | 90% | Already covered in Track A prompt change |

**Also add:**
```
Do NOT include internal tool syntax like 'assistantcommentary to=python' in your 
response. Use standard markdown code blocks (```python) for any code.
```

---

## Track C — Answer Selector → Confidence-Weighted Two-Attempt Policy

**Goal:** For the AIMO3 two-attempt structure, use the AnswerSelector to pick:
- Attempt 1: highest-confidence answer (already done by AnswerSelector.select())
- Attempt 2: highest-confidence **disagreeing** answer

**Implementation:** Add to `src/solver/answer_selector.py`:
```python
def select_two(
    self,
    annotated_solutions: list[AnnotatedSolution],
) -> tuple[tuple[Optional[int], str, float], tuple[Optional[int], str, float]]:
    """Return (best_answer, second_best_disagreeing_answer) for two-attempt policy."""
    first = self.select(annotated_solutions)
    if first[0] is None:
        return first, (None, "no_answer", 0.0)
    
    # Find best answer that disagrees with first
    disagreeing = [s for s in annotated_solutions 
                   if s.final_answer is not None and s.final_answer != first[0]]
    second = self.select(disagreeing) if disagreeing else (None, "no_disagreement", 0.0)
    return first, second
```

**Tests to add to `tests/test_phase3.py`:**
- `test_select_two_returns_different_answers()`
- `test_select_two_when_unanimous()`  # second should be None

---

## Track D — Stretch: Solver Improvement

Only start if Tracks A–C are complete and there's time before April 8.

**The real bottleneck** is that `aime_2024_3` (GT=809) and `aime_2024_5` (GT=104) have 0 extractions — the model never arrives at the correct answer. This is a solver quality problem, not an extraction problem.

**Related files:**
- `src/solver/inference_engine.py` — stub, needs implementation
- `src/solver/sampling_strategy.py` — stub for multi-temperature sampling
- `.agent/workflows/util-openevolve-run.md` — if doing prompt optimization

---

## Key Architecture Rules (DO NOT VIOLATE)

From `docs/FORWARD_PLAN_v2.md §5`:

1. No full claim/evidence graph before answer selector works ← already works
2. No monolithic confidence ontologies — `ConfidenceLevel` has 6 levels, keep it
3. **No DSPy/OpenEvolve before Phase 3 evaluation signal is trustworthy** ← Phase 3 is now done, signal exists
4. No NL-only verification as primary signal — NL verdict = `NL_JUDGMENT` (weakest)
5. No dual architecture — all code in `src/`, production use via notebook calling into `src/`
6. **No submission changes that bypass the audit runner** — run `python scripts/run_baseline.py` after any notebook change

---

## File Map for Phase 4

```
notebook/kaggle_notebook.py          ← CHANGE THIS (Track A)
src/solver/answer_selector.py        ← EXTEND THIS (Track C: select_two)
src/solver/inference_engine.py       ← Stub — only touch for Track D
src/solver/sampling_strategy.py      ← Stub — only touch for Track D

tests/test_phase3.py                 ← ADD tests for Track C changes
docs/BASELINE_METRICS.md             ← Regenerated by: python scripts/run_baseline.py
data/research/research_data*.jsonl   ← Input data for ablation/audit
data/verification/audit_*.jsonl      ← Output from audit runner — do not commit large files
```

---

## How to Verify You're Done

After each Track, run:
```bash
# 1. All tests pass
python -m pytest tests/ -q

# 2. Baseline metrics improve (compare to BASELINE_METRICS.md numbers above)
python scripts/run_baseline.py

# 3. Ablation shows extract_rate improved
python scripts/ablation_extraction.py
```

**Success criteria for Track A (prompt changes):**
- `MISSING_FINAL_COMMIT` flaw count drops to < 50% of problems
- Extract rate on `research_data2.jsonl` increases from 21% to ≥ 40%

**Success criteria for full Phase 4:**
- Kaggle notebook runs end-to-end without crashing
- `AnswerSelector` is used for final answer selection
- All 159+ tests still pass
- `BASELINE_METRICS.md` shows ≥ 5/8 correct on `research_data.jsonl`
