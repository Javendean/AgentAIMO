# AgentAIMO — Baseline Metrics (Phase 3 Audit Runner)

**Generated:** 2026-03-17  
**Source:** `scripts/run_baseline.py`  
**Pipeline:** Phase 0 bug fixes + Phase 1A validator + Phase 1B verification battery + Phase 2 last-resort extractor + Phase 3 FlawDetector + AnswerSelector

---

## Submission 1 (research_data.jsonl)

| Metric | Value |
|---|---|
| Problems audited | 10 |
| Scoreable (GT known) | 8 |
| **Correct (exact match)** | **3/8 = 38%** |
| Canonical answer extract rate | 5.6% |
| Clean trace rate (no sev≥3 flaws) | 0.0% |
| Verifier coverage | 5.6% |

**Per-problem results:**

| Problem ID | GT | Selected | Correct | Selection reason | Top flaws |
|---|---|---|---|---|---|
| aime_2024_1 | 204 | 204 | ✓ | confidence_weighted_vote | CHANNEL_LEAKAGE, MALFORMED_TOOL_CALL, MISSING_FINAL_COMMIT |
| aime_2024_2 | 25 | 25 | ✓ | confidence_weighted_vote | CHANNEL_LEAKAGE, MALFORMED_TOOL_CALL, MISSING_FINAL_COMMIT |
| aime_2024_3 | 809 | - | ✗ | no_answer_extracted | CHANNEL_LEAKAGE, MALFORMED_TOOL_CALL, PROMPT_LEAKAGE |
| aime_2024_4 | 65 | 65 | ✓ | confidence_weighted_vote | CHANNEL_LEAKAGE, MALFORMED_TOOL_CALL, MISSING_FINAL_COMMIT |
| aime_2024_5 | 104 | - | ✗ | no_answer_extracted | CHANNEL_LEAKAGE, MALFORMED_TOOL_CALL, PSEUDO_VERIFICATION |
| imo_2023_1 | N/A | - | ~ | no_answer_extracted | CHANNEL_LEAKAGE, MALFORMED_TOOL_CALL, PSEUDO_VERIFICATION |
| imo_2023_2 | N/A | 2 | ~ | confidence_weighted_vote | CHANNEL_LEAKAGE, CONTEXT_CONFABULATION, MALFORMED_TOOL_CALL |
| putnam_2023_a1 | 18 | - | ✗ | no_answer_extracted | CHANNEL_LEAKAGE, MALFORMED_TOOL_CALL, PSEUDO_VERIFICATION |
| aime_2023_1 | 907 | - | ✗ | no_answer_extracted | CHANNEL_LEAKAGE, MALFORMED_TOOL_CALL, PSEUDO_VERIFICATION |
| aime_2023_10 | 772 | - | ✗ | no_answer_extracted | CHANNEL_LEAKAGE, MALFORMED_TOOL_CALL, PSEUDO_VERIFICATION |

**Top flaw codes across all attempts:**

| Flaw Code | Count |
|---|---|
| `CHANNEL_LEAKAGE` | 10 |
| `MALFORMED_TOOL_CALL` | 10 |
| `PSEUDO_VERIFICATION` | 10 |
| `MISSING_FINAL_COMMIT` | 3 |
| `PROMPT_LEAKAGE` | 1 |
| `CONTEXT_CONFABULATION` | 1 |

---

## Baseline 6/10 (research_data2.jsonl — pre-architecture)

| Metric | Value |
|---|---|
| Problems audited | 10 |
| Scoreable (GT known) | 8 |
| **Correct (exact match)** | **6/8 = 75%** |
| Canonical answer extract rate | 21.1% |
| Clean trace rate (no sev≥3 flaws) | 0.0% |
| Verifier coverage | 21.1% |

**Per-problem results:**

| Problem ID | GT | Selected | Correct | Selection reason | Top flaws |
|---|---|---|---|---|---|
| aime_2024_1 | 204 | 204 | ✓ | confidence_weighted_vote | CHANNEL_LEAKAGE, CONTEXT_CONFABULATION, MALFORMED_TOOL_CALL |
| aime_2024_2 | 25 | 25 | ✓ | confidence_weighted_vote | CHANNEL_LEAKAGE, CONTEXT_CONFABULATION, MALFORMED_TOOL_CALL |
| aime_2024_3 | 809 | 809 | ✓ | confidence_weighted_vote | CHANNEL_LEAKAGE, CONTEXT_CONFABULATION, MALFORMED_TOOL_CALL |
| aime_2024_4 | 65 | 65 | ✓ | confidence_weighted_vote | CHANNEL_LEAKAGE, CONTEXT_CONFABULATION, MALFORMED_TOOL_CALL |
| aime_2024_5 | 104 | - | ✗ | no_answer_extracted | CHANNEL_LEAKAGE, CONTEXT_CONFABULATION, MALFORMED_TOOL_CALL |
| imo_2023_1 | N/A | - | ~ | no_answer_extracted | CHANNEL_LEAKAGE, PSEUDO_VERIFICATION |
| imo_2023_2 | N/A | - | ~ | no_answer_extracted | CHANNEL_LEAKAGE, CONTEXT_CONFABULATION, MALFORMED_TOOL_CALL |
| putnam_2023_a1 | 18 | 18 | ✓ | confidence_weighted_vote | CHANNEL_LEAKAGE, CONTEXT_CONFABULATION, MALFORMED_TOOL_CALL |
| aime_2023_1 | 907 | - | ✗ | no_answer_extracted | CHANNEL_LEAKAGE, CONTEXT_CONFABULATION, MALFORMED_TOOL_CALL |
| aime_2023_10 | 772 | 772 | ✓ | confidence_weighted_vote | CHANNEL_LEAKAGE, CONTEXT_CONFABULATION, MALFORMED_TOOL_CALL |

**Top flaw codes across all attempts:**

| Flaw Code | Count |
|---|---|
| `CHANNEL_LEAKAGE` | 10 |
| `CONTEXT_CONFABULATION` | 9 |
| `MALFORMED_TOOL_CALL` | 9 |
| `PROMPT_LEAKAGE` | 8 |
| `PSEUDO_VERIFICATION` | 7 |
| `NON_EXECUTABLE_CODE` | 6 |
| `MISSING_FINAL_COMMIT` | 3 |
| `REDUNDANT_RECOMPUTATION` | 2 |

---

## Interpretation

- **Canonical answer extract rate** — fraction of individual attempts where `AnswerValidator`
  returned a valid integer (including the last-resort prose extractor).
- **Clean trace rate** — fraction of attempts with no flaw of severity ≥ 3.
  Low values indicate systematic `CHANNEL_LEAKAGE` / `MALFORMED_TOOL_CALL` issues.
- **MISSING_FINAL_COMMIT** — the #1 extraction failure: model derives correct answer
  but outputs it in prose instead of `**ANSWER: N**` format.
- **CONTEXT_CONFABULATION** — model requests prior context on a self-contained problem.
  Addressable via prompt engineering (Phase 4).
