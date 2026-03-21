# Ablation Results — P4-A Phase (Prompt Changes)

**Generated:** 2026-03-21
**Task:** P4-B1 — Document extract_rate before/after P4-A2 prompt changes
**Source data:** `data/verification/audit_research_data.jsonl`, `data/verification/audit_research_data2.jsonl`
**Script:** `scripts/ablation_extraction.py` (requires `data/research/research_data*.jsonl` — see note below)

---

## Summary

| Dataset | Before P4-A2 | Target (P4-A2) | Status |
|---|---|---|---|
| Submission 1 (`research_data.jsonl`) | **5.6%** | ≥ 10% | Pending live inference |
| Baseline 6/10 (`research_data2.jsonl`) | **21.1%** | **≥ 40%** | Pending live inference |

The target extract rate of ≥ 40% on `research_data2.jsonl` **has not yet been measured** after the P4-A2 changes. See [Diagnostic Note](#diagnostic-note-why-after-rate-is-not-yet-measured).

---

## Before P4-A2 — Per-Problem Extract Rates

### Submission 1 (107 total attempts across 10 problems)

| Problem | GT | Attempts | Extracted | Rate | Correct |
|---|---|---|---|---|---|
| `aime_2024_1` | 204 | 8 | 2 | 25% | ✓ |
| `aime_2024_2` | 25 | 4 | 2 | 50% | ✓ |
| `aime_2024_3` | 809 | 13 | 0 | **0%** | ✗ |
| `aime_2024_4` | 65 | 4 | 1 | 25% | ✓ |
| `aime_2024_5` | 104 | 13 | 0 | **0%** | ✗ |
| `imo_2023_1` | N/A | 13 | 0 | 0% | ~ |
| `imo_2023_2` | N/A | 13 | 1 | 8% | ~ |
| `putnam_2023_a1` | 18 | 13 | 0 | **0%** | ✗ |
| `aime_2023_1` | 907 | 13 | 0 | **0%** | ✗ |
| `aime_2023_10` | 772 | 13 | 0 | **0%** | ✗ |
| **TOTAL** | | **107** | **6** | **5.6%** | **3/8 = 38%** |

**Top flaw codes (problem-level frequency):**

| Flaw | Problems affected |
|---|---|
| `CHANNEL_LEAKAGE` | 10/10 |
| `MALFORMED_TOOL_CALL` | 10/10 |
| `PSEUDO_VERIFICATION` | 10/10 |
| `MISSING_FINAL_COMMIT` | 3/10 |
| `PROMPT_LEAKAGE` | 1/10 |
| `CONTEXT_CONFABULATION` | 1/10 |

### Baseline 6/10 (57 total attempts across 10 problems)

| Problem | GT | Attempts | Extracted | Rate | Correct |
|---|---|---|---|---|---|
| `aime_2024_1` | 204 | 3 | 3 | 100% | ✓ |
| `aime_2024_2` | 25 | 8 | 2 | 25% | ✓ |
| `aime_2024_3` | 809 | 13 | 2 | 15% | ✓ |
| `aime_2024_4` | 65 | 3 | 3 | 100% | ✓ |
| `aime_2024_5` | 104 | 13 | 0 | **0%** | ✗ |
| `imo_2023_1` | N/A | 1 | 0 | 0% | ~ |
| `imo_2023_2` | N/A | 13 | 0 | 0% | ~ |
| `putnam_2023_a1` | 18 | 1 | 1 | 100% | ✓ |
| `aime_2023_1` | 907 | 1 | 0 | **0%** | ✗ |
| `aime_2023_10` | 772 | 1 | 1 | 100% | ✓ |
| **TOTAL** | | **57** | **12** | **21.1%** | **6/8 = 75%** |

**Top flaw codes (problem-level frequency):**

| Flaw | Problems affected |
|---|---|
| `CHANNEL_LEAKAGE` | 10/10 |
| `CONTEXT_CONFABULATION` | 9/10 |
| `MALFORMED_TOOL_CALL` | 9/10 |
| `PROMPT_LEAKAGE` | 8/10 |
| `PSEUDO_VERIFICATION` | 7/10 |
| `NON_EXECUTABLE_CODE` | 6/10 |
| `MISSING_FINAL_COMMIT` | 3/10 |
| `REDUNDANT_RECOMPUTATION` | 2/10 |

---

## P4-A2 Prompt Changes (What Was Done)

Three new sections were added to `SYSTEM_PROMPT` in `agent/prompts.py` before the `{patch_slot}` placeholder:

### 1. `## Self-Contained Problem Policy` → targets `CONTEXT_CONFABULATION`
```
This problem is fully self-contained. Do NOT ask for prior context, do NOT reference
earlier results, do NOT say "continue from where you left off". Solve it completely
from scratch.
```

**Expected impact:** `CONTEXT_CONFABULATION` appears in 1/10 Submission 1 problems and 9/10 Baseline problems. Addressing this directly should prevent 0-extraction attempts caused by the model stalling on context requests.

### 2. `## Answer Format (MANDATORY)` → targets `MISSING_FINAL_COMMIT`
```
When you have determined the final answer, you MUST write it on its own line in exactly
this format: **ANSWER: N** (where N is the integer, no other text).
Do NOT write answers like "the answer is N" or "m+n = N". Only the **ANSWER: N** format
will be recorded.
```

**Expected impact:** `MISSING_FINAL_COMMIT` appeared in 3/10 problems on both datasets. The new section is more prominent than the buried step 7 in the original numbered list.

### 3. `## Output Cleanliness` → targets `CHANNEL_LEAKAGE`
```
Do not include internal tool syntax like 'assistantcommentary to=python' in your response.
Use standard markdown code blocks (```python) for any code.
```

**Expected impact:** `CHANNEL_LEAKAGE` appears in 10/10 problems on both datasets. This is the most universal flaw. Directly naming the leaking tokens (`assistantcommentary`) may help, but `CHANNEL_LEAKAGE` is likely infrastructure-level and not fully addressable via prompt alone.

---

## Diagnostic Note: Why "After" Rate Is Not Yet Measured

The ablation script (`scripts/ablation_extraction.py`) requires raw solution trace JSONL files at:
- `data/research/research_data.jsonl`
- `data/research/research_data2.jsonl`

These files contain the raw `solution_text` for each inference attempt. **They are not present in the repository** — they are generated only by running actual model inference on Kaggle. This is by design: the CLAUDE.md rules prohibit live model API calls in offline modules.

**The before metrics above** were computed from the Phase 3 audit records in `data/verification/`, which contain pre-parsed `canonical_answer` fields from the same traces.

**To measure the "after" rate**, a new Kaggle submission must be run with the P4-A2 prompt changes, and the resulting `research_data*.jsonl` files re-audited with `python scripts/run_baseline.py`.

### Why the 40% target may be feasible

On the Baseline dataset (21.1% before), the extraction failures have a clear pattern:

- `aime_2024_5` (13 attempts, 0 extracted): 0% rate is a **solver quality problem** — the model never arrives at the answer, regardless of output format. Prompt changes alone cannot fix this.
- `imo_2023_2` (13 attempts, 0 extracted): non-integer-answer problem; extraction is not applicable.
- `aime_2023_1` (1 attempt, 0 extracted): single attempt with `CONTEXT_CONFABULATION` — P4-A2 directly targets this.

If `CONTEXT_CONFABULATION` suppression converts even 50% of previously-failing attempts into extractable outputs, the Baseline extract rate would increase from 21% toward 35–45%.

### Why the 40% target may be difficult

- `CHANNEL_LEAKAGE` is present in 100% of problems across both datasets. This is likely a model output artifact (the model echoes internal tool syntax) that a system prompt addition may only partially suppress.
- `aime_2024_5` and `aime_2024_3` (Submission 1) require the model to actually solve the problem correctly — no extraction improvement can compensate for 0 correct answers in 13 attempts.

---

## Next Steps

1. **Run a new Kaggle submission** with P4-A2 prompt changes in `agent/prompts.py`.
2. **Save traces** to `data/research/research_data_p4a.jsonl`.
3. **Re-run audit**: `python scripts/run_baseline.py` against the new traces.
4. **Re-run ablation**: `python scripts/ablation_extraction.py` after placing the new JSONL at the expected path.
5. Compare extract rate against the 21.1% baseline to verify the ≥ 40% target.
