> [!WARNING]
> **Status Disclaimer (2026-03-13):** This document is advisory, **not descriptive**.
> Its framing of "past the repo archaeology stage" was aspirational at time of writing.
> As of the above date, Gate 0 (docs audit) is **incomplete** — 8 of 9 referenced documents do not exist.
> Treat this as a strategy reference, not a status report. See `docs/FORWARD_PLAN.md` for the current ground-truth plan.

Those are both excellent instincts.

## Short answer

1. **Yes — you should absolutely evolve the Opus prompt to include your actual repo state and findings so far.** Otherwise Opus will produce an elegant but partially generic strategy document.

2. **The best move forward is to implement only the parts that simultaneously improve the system *and* generate publishable/defensible experimental evidence.** That means: build the **minimal audit substrate first**, and make every phase produce:
   - a measurable hypothesis,
   - an ablation,
   - logged artifacts,
   - and a reusable dataset/result.

The key is to stop thinking in terms of “implement architecture” and start thinking in terms of:

> **implement the smallest component that creates a new experimental lever.**

---

# 1) How to tailor the Opus prompt to your actual results

Your current prompt is strong, but it is still too “clean-room.”  
Opus should be forced to reason from:

- the repo you actually have,
- the docs you actually merged,
- the failed branch family you decided not to use,
- and the constraints you actually face.

## What to add to the prompt

Add a **project-specific context pack** before the main task.

You want Opus to know:

### A. What is already true in the repo
Tell it explicitly:

- `main` now contains:
  - `AGENTS.md`
  - `docs/CODEBASE_ANALYSIS.md`
  - `docs/REPO_MAP.md`
  - `docs/RISK_REGISTER.md`
  - `docs/ANSWER_EXTRACTION_AUDIT.md`
  - `docs/VERIFICATION_AUDIT.md`
  - `docs/LEGACY_ARTIFACT_INVENTORY.md`
  - `docs/MOVE_CANDIDATES.md`
  - `docs/BLINDSPOT_EXECUTIVE_SUMMARY.md`
  - selected `docs/blindspots/*`

### B. What the repo analysis has already established
Summarize the strongest findings, e.g.:

- current answer extraction is too permissive / historically brittle
- execution success has been conflated with mathematical verification
- analysis metrics have relied too much on self-reported trace fields
- notebook/package divergence is real
- the old `src/` architecture branch family was rejected as premature and semantically wrong
- the current intended direction is an additive `audit/`-first substrate

### C. What has already been rejected
This is important because otherwise Opus may reinvent bad paths.

Tell it explicitly that you do **not** want:

- monolithic confidence ontologies
- `src/` as the new primary architecture
- premature solver/optimizer stacks
- broad architecture spray before substrate
- a giant `.agent/` config universe as the core design
- fake completeness
- broad feature work before canonical answer + verifier semantics

### D. What compute and tooling you actually have
Include:
- H100-class inference access
- local Antigravity
- ability to use strong frontier models offline for design/review
- but finite competition time

### E. What your actual question is
Make Opus answer:

> “Given the evidence already gathered in this repo, what is the best research/implementation path now?”

Not just “what is the ideal architecture?”

---

## Best way to inject this context

I would prepend a section like this to the prompt:

---

### **PROJECT-SPECIFIC CONTEXT YOU MUST TREAT AS TRUE**

- The repository has already undergone multiple documentation/audit passes.
- The current merged documentation establishes:
  - brittle answer extraction is a real issue,
  - execution-success vs correctness conflation is a real issue,
  - notebook/package divergence is a real issue,
  - root artifact clutter is real,
  - the previous `src/`-based architecture branch family was rejected as premature and misaligned.
- The intended next architectural direction is:
  - additive,
  - audit-first,
  - centered on canonical answers, typed verifier results, claim/evidence artifacts, and a baseline audit runner.
- Do NOT propose returning to the old `src/` architecture family unless you make an extremely strong case.
- Do NOT assume the repo needs another broad documentation pass.
- Treat the current problem as:
  1. selecting the narrowest set of truly load-bearing innovations,
  2. implementing them in a way that produces real experimental evidence,
  3. and sequencing them so they improve both competition readiness and research value.

You must treat this project as being past the “repo archaeology” stage and entering the “careful substrate implementation” stage.

---

That one section will make Opus much more grounded.

---

# 2) What is the best move forward with implementation?

## The key principle
Implement in a way that every step yields both:

- **system value**
- **research value**

That means every implementation phase should answer:

1. What hypothesis are we testing?
2. What artifact does this phase create?
3. What metrics does it unlock?
4. What future ideas become safely testable because of it?

---

# 3) The best implementation strategy: dual-track

You should not run one monolithic plan.  
You should run **two tightly coupled tracks**:

## Track A — Competition substrate track
Build the minimum needed to improve system reliability fast.

## Track B — Research artifact track
For every piece of substrate, produce a reproducible experiment and dataset/log format.

That way the same work contributes to:
- competition quality,
- publishable insight,
- and future optimizer systems.

---

# 4) The right implementation order now

This is the sequence I think is strongest.

---

## Phase 0 — Freeze project memory
Before coding, create the repo-resident memory layer.

### Build
- `README.md`
- `STATUS.md`
- `docs/architecture/TARGET_ARCHITECTURE.md`
- `docs/architecture/INTERFACE_BLUEPRINT.md`
- `docs/architecture/PHASE_PLAN.md`
- `docs/architecture/DECISION_LOG.md`
- `instructions/*`

### Research contribution
This is not a paper contribution by itself, but it prevents design drift and makes later experiments reproducible.

### Deliverable
A stable implementation contract.

---

## Phase 1 — Canonical answer channel
This is the first real implementation phase.

### Build
- `RawAnswerCandidate`
- `CanonicalAnswer`
- answer extractor
- answer canonicalizer
- tests
- a small golden set of bad/good answer formats

### Why this matters competitively
It directly improves:
- answer parsing reliability,
- answer selection correctness,
- and evaluation consistency.

### Why this matters for research
It gives you your first concrete study:

## Research question 1
**How much leaderboard-relevant error in short-answer systems comes from answer-channel brittleness rather than reasoning failure?**

### Experimental output
Create a dataset of:
- raw solver outputs
- extracted candidates
- canonicalization status
- gold answer (if available offline)
- contamination type

### Paper-worthy angle
This is small, but very real. It can support a short empirical section in a larger paper.

---

## Phase 2 — Typed verifier results
This is the most important conceptual phase.

### Build
- `VerifierKind`
- `VerifierStatus`
- `VerifierResult`
- exact-answer verifier
- python-exec verifier
- brute-force verifier stub
- symbolic verifier stub
- tests

### Why this matters competitively
It helps you stop making category mistakes like:
- “code ran, therefore answer is good”
- “reviewer liked it, therefore it is verified”

### Why this matters for research
This phase unlocks a strong research question:

## Research question 2
**How much does collapsing heterogeneous checks into a single boolean degrade answer selection and self-improvement?**

### Experimental output
For every candidate solution, log:
- which verifiers ran
- what status each returned
- what evidence was produced
- what the final answer was
- whether the candidate was correct

### Paper-worthy angle
You can compare:
- boolean verification
- confidence-score aggregation
- typed status features

for downstream selection quality.

This is significantly more interesting than generic repo engineering.

---

## Phase 3 — Claim/evidence graph
This is where the architecture starts becoming truly novel.

### Build
- `Claim`
- `EvidenceRef`
- `ClaimGraph`
- `AttemptRecord`
- minimal claim extractor
- serialization
- tests

### Keep it narrow
At first:
- final-answer claim
- maybe a few explicit arithmetic or marked claims
- no full NLP proof graph yet

### Why this matters competitively
Indirectly:
- makes candidate inspection better
- supports specialist interfaces
- improves later selection/routing

### Why this matters for research
This unlocks the strongest medium-term question.

## Research question 3
**Can short-answer mathematical systems benefit from machine-checkable claim decomposition even when the benchmark only scores the final answer?**

That is a serious and interesting question.

### Experimental output
A corpus of:
- solver traces
- extracted claims
- verifier attachments
- unresolved portions
- correctness labels

### Paper-worthy angle
This is where you start to get publishable system contribution territory.

---

## Phase 4 — Baseline audit runner
Now make the substrate executable end-to-end.

### Build
- `audit_problem.py`
- `batch_audit.py`
- `run_audit_baseline.py`
- golden set
- result JSONL schema
- baseline metrics

### Metrics
At minimum:
- valid canonical answer rate
- invalid answer format rate
- exact match rate
- verifier coverage rate
- unresolved claim fraction

### Why this matters competitively
This gives you a way to debug hidden-data-like behavior offline.

### Why this matters for research
This turns the architecture from design into experiment.

---

# 5) What should be the first truly novel research target?

If you want the implementation to contribute to research, you need one flagship problem that the substrate is built to study.

## My recommendation
The best flagship research problem is:

# **Evidence-Aware Generative Answer Selection for Hidden Olympiad Tasks**

Not generic “better solver.”  
Not generic “better verifier.”  
Not generic “build a graph.”

Specifically:

> Given multiple candidate solution traces to a hidden short-answer Olympiad problem, can a system select the correct final answer better by conditioning on typed verifier outcomes and structured evidence than by majority voting, raw self-consistency, or generative selection alone?

This is the right target because it sits at the intersection of:

- AIMO-winning practice (selection matters),
- your architecture (typed audit substrate matters),
- and publishable novelty.

---

## Why this is better than some other ideas
### Better than “claim graph for its own sake”
Because selection is leaderboard-relevant.

### Better than “full warm-up generator” first
Because warm-up generation is fascinating but riskier and less directly measurable early.

### Better than “specialist orchestration” first
Because specialist interfaces are useful, but selection quality is the cleaner first lever.

### Better than “full OpenEvolve/DSPy” first
Because you need trustworthy metrics before optimizer systems.

---

# 6) How to implement so results contribute to research

This is the part many people miss.

## Every implementation phase should produce four outputs

### 1. Code artifact
The module itself.

### 2. Evaluation artifact
A JSONL/Parquet log of inputs, outputs, statuses, timings, and labels.

### 3. Analysis notebook/script
A reproducible script that summarizes what changed.

### 4. Ablation definition
A precise comparison against a simpler baseline.

---

## Example: answer canonicalization phase

### Code artifact
`audit/parsing/answer_canonicalizer.py`

### Evaluation artifact
`research/outputs/answer_canonicalization_eval.jsonl`

Each row:
- problem_id
- attempt_id
- raw_text
- raw_candidates
- canonical_status
- canonical_int
- gold_int
- matched_gold
- contamination_type

### Analysis script
`research/experiments/answer_channel/analyze_canonicalization.py`

### Ablation
Compare:
- old extraction logic
- new canonicalizer

That is how implementation becomes research.

---

## Example: typed verifier phase

### Evaluation artifact rows
- attempt_id
- claim_id
- verifier_kind
- verifier_status
- evidence_type
- candidate_final_answer
- final correctness
- selected/not selected

### Ablations
Compare selection quality using:
1. majority vote
2. generative selector only
3. boolean verifier pass/fail
4. typed verifier feature set

That is a real research contribution.

---

# 7) How Opus should be used now

Use Opus 4.6 **not** to implement code directly first.

Use it for **three very specific outputs**:

## A. Final architecture decision memo
Force it to decide:
- what to build now
- what to delay
- what the flagship research problem is
- what the narrowest viable novelty is

## B. Experiment matrix
Ask it to convert the architecture into:
- hypotheses
- baselines
- ablations
- metrics
- expected failure modes

## C. Implementation contract
Ask it to produce:
- exact interfaces
- exact files
- exact success criteria
- exact anti-goals

Then use Antigravity to implement those contracts.

That’s much better than having Opus freestyle implementation.

---

# 8) The best implementation move forward, concretely

Here is what I would actually do next.

---

## Step 1 — Have Opus produce a decision-quality architecture memo tailored to your repo
Use the improved prompt with your actual context.

## Step 2 — Ask Opus for a second deliverable:
### “Convert your own recommendation into:
- a 2-week implementation track
- a 4-week competition track
- and a 3-month research track”

## Step 3 — Start Antigravity implementation with only:
- root memory files
- architecture docs
- instructions
- `audit/models/answer.py`
- `audit/parsing/answer_extractor.py`
- `audit/parsing/answer_canonicalizer.py`
- tests

## Step 4 — Immediately instrument it for research
Do not “implement first, research later.”

Make the first code produce logs.

## Step 5 — Build typed verifier results next
Then instrument again.

## Step 6 — Build a minimal answer-selector experiment
Before claim graph gets too elaborate, run the first selection study.

---

# 9) The biggest trap to avoid now

The trap is:

> building a substrate that is elegant but not experimentally productive.

To avoid that, every phase must answer:

- What experiment becomes possible only because this phase now exists?

If the answer is “none,” the phase is too abstract.

---

# 10) My recommended refined framing for Opus

Here is the conceptual reframing I’d use:

> “Do not design an architecture for its own sake. Design the minimum infrastructure necessary to make evidence-aware answer selection, specialist routing, and scaffolded mathematical reasoning scientifically testable.”

That will force much better output.

---

# 11) Practical answer to your two thoughts

## Thought 1: Tailor the prompt to the results gathered so far
**Yes, absolutely.**  
Do this now. Otherwise Opus will duplicate reasoning you already paid for.

## Thought 2: Best move forward with implementation so results contribute to research
**Build only what creates new measurable experiments.**  
That means:

1. root memory files
2. canonical answer channel
3. typed verifier results
4. minimal claim/evidence graph
5. baseline audit runner
6. first evidence-aware answer-selection experiment

That is the highest-value path.

---

# 12) My strongest recommendation

If I had to compress all of this into one instruction:

> **Use Opus to define the flagship research problem and experiment matrix; use Antigravity to implement the smallest substrate that makes that problem testable; and require every implementation phase to emit a reusable evaluation artifact and ablation.**

That is the best way to make implementation contribute directly to research instead of becoming architecture theater.