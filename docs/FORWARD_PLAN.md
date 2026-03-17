# AgentAIMO — Forward Plan (Revised)

**Created:** 2026-03-13  
**Deadline:** April 8, 2026 (~26 days)  
**Sources:** `evidence.md`, `evolution.md`, `docs/CODEBASE_ANALYSIS.md`, repo audit

---

## 0. The Corrected Mental Model

The original forward plan treated this as a pure docs-then-build repo restructuring. That was wrong. `evolution.md` corrects the framing:

**This project is two systems, not one.**

| System | What | Runs Where | Goal |
|---|---|---|---|
| **Submission** | gpt-oss-120B + TIR + answer selection | Kaggle H100 (inference) | Score points on April 8 |
| **Meta-system** | Verification battery, audit runner, offline optimizer | Local / offline | Improve the submission between runs |

Every prior critique of "too much infrastructure" applies only if you confuse the meta-system for the submission. The meta-system's job is not to run on the H100 — it is to close the feedback loop between submissions by diagnosing *why* the solver fails and improving its behavior offline.

The 6 documented bugs in `CODEBASE_ANALYSIS.md` fall primarily in the meta-system. Fixing them makes the feedback loop trustworthy. A broken feedback loop means every submission is effectively guessing.

---

## 1. The Novel Contribution (what this system adds over AIMO1/2 winners)

NuminaMath (AIMO1): fine-tuned 7B + TIR + majority vote.  
NemoSkills (AIMO2): GenSelect (learned text-based selector) + 540K training problems.

**Our addition:** decompose each solution trace into mechanically verifiable and non-verifiable components, compute **typed confidence signals** per component, and feed those signals into answer selection.

This is strictly more informative than majority voting (treats all traces as exchangeable) and strictly more trustworthy than GenSelect (which operates on surface text, not structured evidence). The theoretical framing is in `evolution.md` §§ Idea 2 and The Core Research Problem.

The **open research problem** at the heart of this: given a finite verification compute budget B, how do you allocate checks across N traces and M verifiable claims per trace to maximally improve selection accuracy? This is a stochastic scheduling problem with information-dependent rewards (formalised in `evolution.md` §§ The Research Question for GPT-5.4 Pro).

---

## 2. What Exists and What Is Broken

### Exists (production code in `agent/`)
- `deep_researcher.py` — multi-wave generation, TIR loop, consensus
- `prompts.py` — template engine, topic classification, answer extraction
- `sandbox.py` — subprocess code execution

### Documented Critical Bugs (from `docs/CODEBASE_ANALYSIS.md`)

| # | Bug | Impact | Fixes In |
|---|---|---|---|
| 1 | Execution success ≠ math correctness | Verifier rubber-stamps wrong answers | Phase 1B |
| 2 | Canary brittleness + data leakage | Model downgrade on valid outputs | Phase 0 |
| 3 | Brittle regex answer extraction | Corrupts majority voting consensus | Phase 1A |
| 4 | Superficial error patching | Feedback loop is semantically blind | Phase 2 |
| 5 | Pass-through NL verifier | Formatting failures auto-approve wrong answers | Phase 1B |
| 6 | Naive topic classification | Wrong strategy hints injected | Phase 1A |

### Exists (meta-system, partial)
- `analysis/analyze_results.py` — reads JSONL, patches prompts (surface-level only, bug #4)
- `scripts/` — 20 utility scripts, status unknown

### Missing (all of the verification substrate)
- Typed `VerifierResult` — not built
- Canonical answer channel — not built  
- Confidence-weighted answer selector — not built
- Audit runner — not built
- `docs/RISK_REGISTER.md`, `REPO_MAP.md`, `LEGACY_ARTIFACT_INVENTORY.md`, and 5 other promised docs — not built

---

## 3. The 26-Day Plan

With April 8 as hard deadline, phases must overlap and each must produce something that immediately improves the next submission. The rule: **every phase must close at least one documented bug AND unlock one measurable experiment.**

---

### Phase 0 — Patch Critical Submission Blockers (Days 1–3)

These are bugs in the live submission path that cost points *right now*, independent of the meta-system.

**Bug #2 — Canary test:**
- Fix the format mismatch between `run_canary_test` (expects `\boxed{809}`) and `prompts.py` (instructs `**ANSWER: 809**`).
- Replace the static AIME 2024 canary problem with a non-memorizable synthetic problem of equivalent difficulty.
- File: `notebook/kaggle_notebook.py`

**Bug #3 — Answer extraction (partial fix):**
- Tighten the `extract_answer` regex to extract only the integer token, not the full trailing phrase.
- Add 10 golden test cases covering the documented brittle formats.
- File: `agent/prompts.py`, `tests/test_agent.py`

**Deliverable:** A submission that no longer spontaneously downgrades from 120B to 72B and no longer corrupts majority votes on well-formed outputs.

---

### Phase 1A — Canonical Answer Channel (Days 3–8)

**Hypothesis:** A non-trivial fraction of answer-selection errors come from extraction brittleness, not reasoning failure.

**Build:**
```
audit/
  models/answer.py              # RawAnswerCandidate, CanonicalAnswer dataclasses
  parsing/answer_extractor.py   # typed extraction: integer, fraction, set
  parsing/answer_canonicalizer.py  # normalizes to int with validation
  tests/test_answer_extraction.py  # golden set, ≥ 15 format variants
```

**Ablation:** Run old extractor vs. new on `data/research/*.jsonl`. Log and save:
```jsonl
{"problem_id": ..., "raw_text": ..., "old_extracted": ..., "new_canonical": ..., "gold_int": ..., "match": ...}
```
Output: `research/outputs/answer_canonicalization_eval.jsonl`

**Bugs closed:** #3 (fully), #6 (improved by canonical int constraint).  
**Experiment unlocked:** How much error is extraction vs. reasoning?

---

### Phase 1B — Typed Verifier Results (Days 5–12)

This is the most important phase. It is the technical foundation of the novel contribution.

**Hypothesis:** Collapsing heterogeneous verification into a boolean degrades selection quality and obscures the true source of failure.

**Build:**
```
audit/
  models/verifier.py            # VerifierKind enum, VerifierStatus enum, VerifierResult dataclass
  verifiers/exact_answer.py     # compares canonical answer to gold (LEVEL_0_EXACT)
  verifiers/python_exec.py      # wraps sandbox; NEVER passes on returncode==0 alone
  verifiers/symbolic_check.py   # SymPy identity/equation verification (LEVEL_1_SYMBOLIC)
  verifiers/brute_force.py      # exhaustive enumeration for small-domain claims
  tests/test_verifiers.py
```

**The `ConfidenceLevel` taxonomy** (from `evolution.md` §§ Idea 2):

| Level | Name | Meaning |
|---|---|---|
| 0 | EXACT | Deterministic recomputation confirms the specific value |
| 1 | SYMBOLIC | SymPy / CAS confirms algebraic identity |
| 2 | FORMAL | Lean kernel acceptance (offline only, Kimina-Prover) |
| — | ENUMERATED | Brute-force checked all cases in bounded domain |
| — | NL_JUDGMENT | LLM review (weakest — never sole signal) |
| — | UNVERIFIED | No mechanical check attempted |

**Key constraint on `python_exec` verifier:** Must check that executed output contains or implies the candidate answer. `returncode == 0` with irrelevant stdout is `VerifierStatus.SUSPICIOUS`, not `PASS`. This directly fixes bugs #1 and #5.

**Ablation:** For each problem in the golden set, compare:
1. Majority vote (current)
2. Boolean pass/fail (current hidden behavior)  
3. Typed verifier feature vector → weighted selection

Output: `research/outputs/verifier_typed_eval.jsonl`

**Bugs closed:** #1, #5.  
**Experiment unlocked:** First direct test of the core research claim.

---

### Phase 2 — Confidence-Weighted Answer Selector (Days 10–17)

**This is the directly leaderboard-relevant implementation** of the research contribution.

**Build:**
```
audit/
  selection/answer_selector.py    # weights traces by typed verifier evidence
  selection/two_attempt_policy.py # maps confidence distribution to safe/speculative pair
```

**The selection algorithm** (to be formalized by GPT-5.4 Pro via the open problem in `evolution.md`):
- For each trace T_i, compute a confidence score from its `VerifierResult[]`
- Weight answers by confidence, not raw count
- For the two-attempt structure: attempt 1 = highest-confidence answer, attempt 2 = highest-confidence *among disagreeing* traces (maximally informative second attempt)

**The open problem** (stochastic verification budget allocation — see `evolution.md` §§ The Research Question for GPT-5.4 Pro) determines the *optimal* version of this selector. The greedy version (verify all, then weight) is implemented first; the budget-optimal version is the research target.

**Ablation:** Compare against AIMO2 winner's GenSelect on the same 50+ practice problems.

**Bugs closed:** #4 (selection is now semantically grounded, not surface-patching).  
**Experiment unlocked:** Direct comparison vs. NemoSkills GenSelect selection quality.

---

### Phase 3 — Offline Audit Runner + Feedback Loop (Days 14–22)

Turn the substrate into an end-to-end improvement system.

**Build:**
```
audit/
  runner/audit_problem.py        # single-problem audit: generate → verify → select → log
  runner/batch_audit.py          # run audit over a problem set
  runner/run_baseline.py         # entry point, produces metrics
```

**Minimum JSONL output schema per attempt:**
```jsonl
{
  "problem_id": ...,
  "attempt_id": ...,
  "canonical_answer": ...,
  "verifier_results": [...],
  "confidence_score": ...,
  "selected": true/false,
  "gold_answer": ...,
  "correct": true/false
}
```

**Baseline metrics reported to `docs/BASELINE_METRICS.md`:**
- Valid canonical answer rate
- Exact match rate (per problem type: algebra, combinatorics, geometry, number theory)
- Verifier coverage rate (fraction of traces with ≥ 1 non-trivial check)
- Confidence-weighted selector accuracy vs. majority vote accuracy

**Why this matters for the submission:** This loop replaces `analysis/analyze_results.py`'s surface-level text patching (bug #4) with a semantically grounded diagnosis. The output drives the next prompt improvement, not a string search over error messages.

---

### Phase 4 — Offline Optimizers (Days 18–26, parallel with competition submissions)

These are the higher-risk, higher-reward components. They run in parallel with submission preparation, not as prerequisites.

**DSPy prompt optimizer:**
- Wrap the generation + verification + selection pipeline as a DSPy module
- Optimizer: `BootstrapFewShot` or `MIPRO` over the practice problem set
- Tune: system prompt, warm-up scaffolding template, sampling temperature
- Deliverable: evolved prompt artifacts for next submission

**OpenEvolve code evolution (if time permits):**
- Optimization target: entire `audit/` pipeline (sampling strategy, verifier thresholds, time allocation)
- Evaluation function: exact match rate on golden set
- This is the most ambitious component; only begin if Phases 0–3 are stable

**Offline specialists (pre-computed, not inference-time):**
- Kimina-Prover: generate LEVEL_2_FORMAL verified micro-theorems for retrieval library
- AlphaGeometry2 DDAR: verify geometry subclaims, generate few-shot examples
- regress-lm: train difficulty predictor on (problem_text → solve_probability) for time allocation

---

## 4. The Remaining Docs (do not block phases on them)

The original plan required 7 docs before any code. Given 26 days, reorder: docs get written *alongside* phases, capturing what was found, not as prerequisites.

| Doc | Written When |
|---|---|
| `docs/RISK_REGISTER.md` | After Phase 0 (bugs documented, not fixed by docs) |
| `docs/LEGACY_ARTIFACT_INVENTORY.md` | After Phase 0 (scripts classified live/archival/delete) |
| `docs/REPO_MAP.md` | After Phase 1A (structure stabilizes) |
| `docs/ANSWER_EXTRACTION_AUDIT.md` | Output of Phase 1A ablation |
| `docs/VERIFICATION_AUDIT.md` | Output of Phase 1B ablation |
| `docs/BASELINE_METRICS.md` | Output of Phase 3 |
| `scripts/README.md` | Alongside Phase 0 |

---

## 5. The Research Track (running in parallel)

Every implementation phase emits a logged evaluation artifact (per `evidence.md` §§ 6). These accumulate into the empirical basis for `docs/RESEARCH_MANUSCRIPT.md` — the Opus 4.6 deliverable specified in `evolution.md`.

**The flagship research problem** (preserved verbatim from `evolution.md`):
> *Given multiple candidate solution traces to a hidden short-answer Olympiad problem, can a system select the correct final answer better by conditioning on typed verifier outcomes and structured evidence than by majority voting, raw self-consistency, or generative selection alone?*

**The open problem for GPT-5.4 Pro** (the budget-optimal verification allocation stochastic scheduling problem) should be submitted to it once Phase 1B is complete and real verification timing data exists. The warm-up/curved-space structure is already specified in `evolution.md` §§ The Research Question for GPT-5.4 Pro.

---

## 6. What Not to Build (hard constraints)

- **No full claim/evidence graph before the answer selector works.** The claim graph is intellectually exciting but not leaderboard-relevant until selection quality is demonstrated.
- **No monolithic confidence ontologies.** The `ConfidenceLevel` taxonomy is purposely narrow.
- **No DSPy/OpenEvolve before the evaluation signal is trustworthy.** Running an optimizer over a broken metric is worse than not optimizing at all.
- **No NL-only verification as the primary signal.** Aletheia's results (68.5% of 700 open Erdős problems fundamentally wrong) prove the ceiling. NL verdict is `UNVERIFIED` quality until supported by mechanical checks.
- **No returning to the old `src/` architecture family.**
- **No submission improvements that bypass the audit runner.** Every change to the solver must be measurable through the runner before submission.

---

## 7. Sequencing Summary

```
Days 1–3:   Phase 0    — Canary fix, regex tightening (submit improved baseline)
Days 3–8:   Phase 1A   — Canonical answer channel + ablation
Days 5–12:  Phase 1B   — Typed verifier results + selection ablation  [OVERLAP]
Days 10–17: Phase 2    — Confidence-weighted selector + two-attempt policy
Days 14–22: Phase 3    — Audit runner + feedback loop + BASELINE_METRICS.md
Days 18–26: Phase 4    — DSPy optimizer, offline specialists (parallel)
             + Submit RESEARCH_MANUSCRIPT.md prompt to Opus 4.6

April 8:    COMPETITION DEADLINE
```

Phases 1A and 1B overlap deliberately — the typed verifier depends on the canonical answer type, not on the full extractor being perfect.

---

## 8. The Decision That Changes Everything

The original forward plan was conservative and docs-first. `evolution.md` adds the deadline and establishes that the core contribution (typed verification → weighted selection) is both competitively urgent and research-novel. The revised plan front-loads bug fixes that affect the submission, builds the typed verifier substrate as the central technical contribution, and treats the remaining docs as outputs of the implementation process rather than prerequisites to it.

The fundamental principle from `evidence.md` is preserved:
> **Every implementation phase must unlock a new measurable experiment.**

The fundamental constraint from `evolution.md` is added:
> **Every implementation phase must also improve the next submission.**
