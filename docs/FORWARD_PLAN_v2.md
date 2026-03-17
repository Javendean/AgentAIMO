# AgentAIMO — Forward Plan v2 (Post-Merge)

**Created:** 2026-03-13  
**Supersedes:** `docs/FORWARD_PLAN.md` (pre-merge, now stale)  
**Deadline:** April 8, 2026 (~25 days remaining)  
**Sources:** All `docs/*.md`, `evolution.md`, `evidence.md`, `.agent/workflows/*`, `src/**/*.py`, `agent/*.py`

---

## 0. What Changed Since v1

The original FORWARD_PLAN was written before the triage merge that landed 4 commits on `main`:

| Commit | What it added |
|---|---|
| `0c0b924` | 4 audit docs (ANSWER_EXTRACTION_AUDIT, BLINDSPOT_EXECUTIVE_SUMMARY, VERIFICATION_AUDIT, MOVE_CANDIDATES) |
| `57e6ca4` | RISK_REGISTER, REPO_MAP |
| `82533b7` | Complete `src/` module tree: `models/`, `verification/`, `solver/`, `optimization/` |
| `ec34569` | `.agent/` config (rules, workflows, skills) + `data/` scaffold |

**Three critical conflicts** in v1 are now resolved:

1. **`audit/` → `src/`**: v1 proposed building in `audit/`. The stubs now live in `src/`. This plan uses `src/` exclusively.
2. **"Missing docs"**: v1 listed 7 docs as unwritten. Six now exist on `main`. Section 4 of v1 is obsolete.
3. **`.agent/workflows/` alignment**: The workflows define implementation order per phase. This plan defers to them as the canonical execution guide and provides only the strategic framing here.

---

## 1. The Two Systems (unchanged from v1 — this framing is correct)

| System | What | Runs Where | Goal |
|---|---|---|---|
| **Submission** | gpt-oss-120B + TIR + answer selection | Kaggle H100 (inference) | Score points on April 8 |
| **Meta-system** | Verification battery, audit runner, offline optimizer | Local / offline | Improve the submission between runs |

---

## 2. Current State of the Codebase

### Production code (live, runs on Kaggle)

| File | LOC | Role | Known Bugs |
|---|---|---|---|
| `agent/deep_researcher.py` | ~600 | Orchestration: wave generation, majority vote, GenSelect, self-correction | Bug #1 (exec≠truth), Bug #5 (NL pass-through) |
| `agent/prompts.py` | 548 | All prompts, answer extraction, topic classification | Bug #3 (regex), Bug #6 (keyword topic) |
| `agent/sandbox.py` | ~200 | Subprocess code execution | Bug #1 (returncode==0 rubber-stamp), RISK-04 (weak isolation) |
| `notebook/kaggle_notebook.py` | ~300 | Kaggle entrypoint, canary test, model fallback | Bug #2 (canary format mismatch) |

### Module stubs (merged, all `NotImplementedError`)

| Package | Modules | Purpose |
|---|---|---|
| `src/models/` | `problem.py`, `solution.py`, `verification.py` | Typed dataclasses: Problem, SolutionTrace, VerificationReport, ConfidenceLevel |
| `src/verification/` | `arithmetic_checker.py`, `symbolic_checker.py`, `brute_force_checker.py`, `counterexample_search.py`, `answer_validator.py`, `solution_parser.py`, `__init__.py` | Deterministic verification battery |
| `src/solver/` | `inference_engine.py`, `python_executor.py`, `sampling_strategy.py`, `answer_selector.py`, `__init__.py` | Solver components |
| `src/optimization/` | `eval_function.py`, `evolve_runner.py`, `__init__.py` | OpenEvolve integration |

### Documentation (exists on `main`)

| Doc | Content | Still needed? |
|---|---|---|
| `CODEBASE_ANALYSIS.md` | 6 bugs identified | ✅ Reference |
| `ANSWER_EXTRACTION_AUDIT.md` | 3 extraction risks + no normalization | ✅ Reference |
| `VERIFICATION_AUDIT.md` | Exec↔truth conflation + recommended typed states | ✅ Reference |
| `BLINDSPOT_EXECUTIVE_SUMMARY.md` | 5 top-level blindspots | ✅ Reference |
| `RISK_REGISTER.md` | 8 risks with recommended actions | ✅ Reference |
| `REPO_MAP.md` | File trust map | ✅ Reference |
| `MOVE_CANDIDATES.md` | Root cleanup manifest | ✅ Execution pending |
| `FORWARD_PLAN.md` (v1) | Pre-merge plan | ❌ Superseded by this doc |

### Infrastructure

| What | Where | Status |
|---|---|---|
| Agent rules | `.agent/rules/00–03` | Ready (project identity, code standards, math verification standards, GitNexus) |
| Phase workflows | `.agent/workflows/phase1–4, util-openevolve-run` | Ready to execute |
| Skills | `.agent/skills/` (math-verifier, geometry-checker, lean-translator, schema-miner) | Registered |
| Data scaffold | `data/{annotations,critiques,problems,traces,verification}/` | Empty, `.gitkeep` in place |
| Tests | `tests/test_agent.py`, `tests/test_hallucination_fix.py` | Sparse, no mocking (RISK-08) |

---

## 3. The Bug-Fix-to-Phase Mapping

Every documented bug has an exact location in production code and a specific stub in `src/` that replaces the broken behavior. This table is the implementation contract:

| Bug # | Description | Production location (broken) | `src/` replacement (stub) | Phase |
|---|---|---|---|---|
| #1 | Exec success ≠ math correctness | `sandbox.py` → `run_verification` returns `True` on `returncode==0` | `src/verification/arithmetic_checker.py`, `symbolic_checker.py` → typed `VerificationReport` | 1B |
| #2 | Canary format mismatch → model downgrade | `notebook/kaggle_notebook.py` → `run_canary_test` expects `\boxed{809}` but prompt says `**ANSWER: 809**` | Direct fix in `kaggle_notebook.py` | 0 |
| #3 | Regex answer extraction too permissive | `agent/prompts.py:506–517` → `r"\*\*ANSWER:\s*(.+?)\*\*"` captures prose | `src/verification/answer_validator.py` → typed extraction + canonicalization | 1A |
| #4 | Superficial error patching | `analysis/analyze_results.py` → string-matches "NameError", "TIMEOUT" | `src/solver/answer_selector.py` → confidence-weighted selection replaces prompt-patching | 2 |
| #5 | NL verifier pass-through | `agent/prompts.py:546–547` → defaults to `True` on format failure | `src/verification/solution_parser.py` → structured parse, never default-pass | 1B |
| #6 | Naive topic classification | `agent/prompts.py:276–305` → keyword matching | Not critical path — improve after Phase 2 | 3+ |

---

## 4. The 25-Day Plan

### Design Principles (carried from v1)
- **Every phase closes ≥1 documented bug AND unlocks ≥1 measurable experiment.**
- **Every phase must also improve the next Kaggle submission.**
- `.agent/workflows/` contain the detailed step-by-step execution guide per phase. This document provides the *strategic* framing, sequencing rationale, and success criteria.

---

### Phase 0 — Patch Submission Blockers (Days 1–3)

**Target bugs:** #2, #3 (partial)

**Changes — all in production code, no `src/` involvement:**

| File | Change |
|---|---|
| `notebook/kaggle_notebook.py` | Fix canary test to accept `**ANSWER: 809**` format. Replace static AIME 2024 problem with a synthetic, non-memorizable canary of equivalent difficulty. |
| `agent/prompts.py` L506–517 | Tighten `extract_answer` regex: capture only the integer token, not trailing prose. Change `(.+?)` to `(\d+)` with fallback `([\d,]+)`. |
| `tests/test_agent.py` | Add ≥10 golden test cases covering: polluted answers, missing answers, multi-answer traces, LaTeX-formatted answers, whitespace variants. |

**Deliverable:** Submit an improved baseline that no longer self-downgrades to 72B and no longer fractures majority votes.

**Success criteria:**
- All 10 golden extraction tests pass
- Canary test passes with the model's actual output format

**Experiment unlocked:** Before/after accuracy comparison on the existing `research_data.jsonl` traces.

---

### Phase 1A — Canonical Answer Channel (Days 3–8)

**Target bugs:** #3 (full fix)  
**Execution guide:** `.agent/workflows/phase1-verification-battery.md` (steps 5: `answer_validator.py`)

**Changes:**

| File | Change |
|---|---|
| `src/verification/answer_validator.py` | Implement `validate_format()`, `validate_against_truth()`, `cross_consistency_check()`. Replace `extract_answer` in production as the canonical extraction path. |
| `src/models/solution.py` | Ensure `ExtractedCalculation` and `SolutionStep` dataclasses support the answer format taxonomy (integer, fraction, set). |
| `tests/test_answer_extraction.py` (NEW) | ≥15 format variants. Include: polluted prose, LaTeX fractions, multi-answer, `\boxed{}`, negative integers, zero, five-digit boundary (99999). |

**Ablation (produces data):**
Run old `extract_answer` vs. new `answer_validator` over `research_data.jsonl`:
```
data/verification/answer_canonicalization_eval.jsonl
```
Schema: `{"problem_id", "raw_text", "old_extracted", "new_canonical", "gold_int", "match"}`

**Success criteria:**
- 100% of golden test cases pass
- Ablation log quantifies extraction-caused errors vs. reasoning errors

---

### Phase 1B — Typed Verification Battery (Days 5–14)

**Target bugs:** #1, #5  
**Execution guide:** `.agent/workflows/phase1-verification-battery.md` (full workflow)

This is the **most important phase** and the **most ambitious**. The `.agent/workflows/` specifies the implementation order:

1. `src/verification/arithmetic_checker.py` — safe eval, expression sanitization, result comparison
2. `src/verification/symbolic_checker.py` — SymPy identity/inequality checks, numerical spot-checks
3. `src/verification/brute_force_checker.py` — exhaustive enumeration for bounded domains
4. `src/verification/counterexample_search.py` — systematic + random candidate generation
5. `src/verification/answer_validator.py` — (done in Phase 1A)
6. `src/verification/solution_parser.py` — step classification, calculation extraction (hardest module)
7. Pipeline integration (new file: `src/verification/pipeline.py`)

**The ConfidenceLevel taxonomy** is already defined in `src/models/verification.py`:

| Level | Name | Meaning |
|---|---|---|
| 0 | EXACT | Deterministic recomputation confirms the value |
| 1 | SYMBOLIC | CAS confirms algebraic identity |
| 2 | FORMAL | Lean kernel acceptance (offline only) |
| — | ENUMERATED | Brute-force checked all cases |
| — | NL_JUDGMENT | LLM review (weakest — never sole signal) |
| — | UNVERIFIED | No mechanical check attempted |

**Key constraint on the python execution verifier:** A `returncode == 0` with irrelevant stdout must produce `VerifierStatus.SUSPICIOUS`, not `PASS`. This is the direct fix for bugs #1 and #5.

**Timeline note:** This phase has 9 days allocated (vs. 7 in v1). Steps 1–4 are parallelizable. Step 6 (`solution_parser.py`) is the hardest — it requires LaTeX-aware NLP and may need a simpler first implementation. A fallback: implement steps 1–5 + 7 first, leaving `solution_parser` as a LEVEL_3 (NL-based) component initially.

**Success criteria:**
- All `NotImplementedError` stubs replaced in steps 1–5 and 7
- Each checker has ≥3 known-answer test cases + ≥1 deliberately wrong input
- Pipeline can produce a `VerificationReport` for a trace

---

### Phase 2 — Confidence-Weighted Answer Selector (Days 12–19)

**Target bugs:** #4  
**Execution guide:** `.agent/workflows/phase2-solver-improvement.md` (step 4: `answer_selector.py`)

**Changes:**

| File | Change |
|---|---|
| `src/solver/answer_selector.py` | Implement `select_best_answer()` using typed `VerificationReport[]` from Phase 1B. Weight answers by confidence level, not raw count. |
| `src/solver/sampling_strategy.py` | Implement `SamplingConfig` for multi-temperature diverse sampling. |
| NEW: two-attempt policy | For the AIMO3 two-attempt structure: attempt 1 = highest-confidence answer; attempt 2 = highest-confidence *disagreeing* answer. |

**Integration point with production code:**
The new `answer_selector` must produce the same output type that `deep_researcher.py:_majority_vote` currently returns. The integration path:
1. `deep_researcher.py` calls `answer_selector.select_best_answer(traces, verification_reports)` instead of `Counter` tallying
2. Production code gains typed confidence signals without full rewrite

**Ablation (produces data):**
Compare on ≥30 practice problems:
1. Current majority vote (string counting)
2. Confidence-weighted selection
3. (If feasible) GenSelect baseline

```
data/verification/selector_comparison_eval.jsonl
```

**Success criteria:**
- `answer_selector.select_best_answer()` returns the correct answer *more often* than `Counter` on the practice set
- The ablation log shows per-problem comparison

---

### Phase 3 — Audit Runner + Feedback Loop (Days 16–22)

**Changes:**

| File | Change |
|---|---|
| NEW: `src/runner/audit_problem.py` | Single-problem audit: generate → verify → select → log |
| NEW: `src/runner/batch_audit.py` | Run audit over a problem set |
| NEW: `src/runner/run_baseline.py` | Entry point, produces metrics |

**Output schema per attempt:**
```jsonl
{
  "problem_id": "...",
  "attempt_id": "...",
  "canonical_answer": 42,
  "verifier_results": [{"kind": "ARITHMETIC", "status": "PASS", "confidence": "LEVEL_0_EXACT"}],
  "confidence_score": 0.95,
  "selected": true,
  "gold_answer": 42,
  "correct": true
}
```

**Deliverable:** `docs/BASELINE_METRICS.md` with:
- Valid canonical answer rate
- Exact match rate by topic
- Verifier coverage rate (fraction of traces with ≥1 non-trivial check)
- Confidence-weighted selector accuracy vs. majority vote

**Success criteria:**
- Runner completes a full pass over ≥30 problems without crashing
- Metrics document is generated and shows measurable signal

---

### Phase 4 — Optimization + Submission Prep (Days 20–25, parallel)

**Execution guide:** `.agent/workflows/phase4-hardening.md`, `.agent/workflows/util-openevolve-run.md`

**Track A — Submission hardening (mandatory):**
1. Clean Kaggle notebook: integrate `answer_selector` and verification pipeline
2. Time budget optimization: profile verification overhead
3. Final human review

**Track B — Offline optimization (stretch, begin only if Phases 0–3 are stable):**
- `src/optimization/eval_function.py` → implement evaluation metric
- `src/optimization/evolve_runner.py` → OpenEvolve integration
- DSPy prompt tuning over practice problems

**Track C — Root cleanup (low priority, safe moves only):**
- Execute Safe tier of `docs/MOVE_CANDIDATES.md` (chat logs, .bak files → `_attic/noise/`)
- Do not touch Risky tier until after competition

---

## 5. What Not to Build (hard constraints, preserved from v1)

1. **No full claim/evidence graph** before the answer selector works
2. **No monolithic confidence ontologies** — the `ConfidenceLevel` taxonomy is intentionally narrow
3. **No DSPy/OpenEvolve** before the evaluation signal from Phase 3 is trustworthy
4. **No NL-only verification as primary signal** — NL verdict is `UNVERIFIED` quality
5. **No dual architecture** — all new code goes in `src/`, production integration via `agent/` calling into `src/`
6. **No submission changes that bypass the audit runner** after Phase 3

---

## 6. Sequencing Summary

```
Days 1–3:   Phase 0    — Canary fix, regex tightening (submit improved baseline)
Days 3–8:   Phase 1A   — Canonical answer channel + ablation
Days 5–14:  Phase 1B   — Typed verification battery (6 checkers + pipeline) [OVERLAP with 1A]
Days 12–19: Phase 2    — Confidence-weighted selector + two-attempt policy
Days 16–22: Phase 3    — Audit runner + feedback loop + BASELINE_METRICS
Days 20–25: Phase 4    — Submission hardening + optimization (parallel tracks)

April 8:    COMPETITION DEADLINE
```

---

## 7. Canonical Authority

| Question | Answer |
|---|---|
| Where does new code go? | `src/` (fill existing stubs) |
| What guides step-by-step implementation? | `.agent/workflows/phase*.md` |
| What guides strategic decisions? | This document (`FORWARD_PLAN_v2.md`) |
| What constrains code quality? | `.agent/rules/01-code-standards.md` |
| What constrains verification design? | `.agent/rules/02-math-verification-standards.md` |
| Where does evaluation data go? | `data/verification/` |
| Where do test results go? | `data/traces/` |

---

## 8. The Principle (unchanged)

> **Every implementation phase must unlock a new measurable experiment.**
> — `evidence.md`

> **Every implementation phase must also improve the next submission.**
> — `evolution.md`
