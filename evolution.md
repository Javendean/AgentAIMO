# First: The rebuttal matters because it reshapes what the Opus prompt should do

The critique is **largely correct about the competition.** Let me be direct about what it gets right and what it misses, because this determines what we tell Opus to build.

## What the critique gets right

**The empirical record is real.** AIMO1 was won by NuminaMath with fine-tuned DeepSeekMath-7B using tool-integrated reasoning and self-consistency decoding. AIMO2 was won by NemoSkills with 540K problems, code execution integration, and GenSelect. Neither winner built typed verifier schemas or claim graphs.

**The timeline criticism is valid.** With ~25 days remaining and the leaderboard at 44-46, spending weeks on infrastructure that doesn't directly improve solve rate is genuinely dangerous.

**The "evaluator is already strong" point is correct for the competition.** AIMO3 evaluates integer exact-match. You know immediately if you're right. You don't need an elaborate verification substrate to tell you what Kaggle already tells you.

## What the critique gets wrong

**It assumes our architecture is the submission model.** It isn't. Our architecture is the **offline meta-system** that improves the submission model. The submission model is gpt-oss-120B running straightforward inference on the H100. The verification battery, the typed evidence, the critique pipeline — these run offline to analyze failure modes and improve the solver between submissions.

**It ignores that we already chose the strong base model.** gpt-oss-120B is explicitly designed for competition math, fits the H100 in MXFP4, and outperforms o4-mini on AIME. We're not building instead of choosing a good model — we chose the model first.

**It conflates "what won AIMO1/2" with "what will win AIMO3."** AIMO3 is explicitly harder, with IMO-level problems. The gap between 44/50 and 50/50 is the hardest problems. Simple majority voting and TIR got teams to 44. Getting further requires understanding *why* the solver fails on the remaining problems, which is exactly what the verification battery diagnoses.

**It misses the actual competitive value of verification.** In a 2-attempt-per-problem setting, verification-weighted answer selection is strictly better than raw majority voting — and this is the core of our Tier 1 implementation (answer_selector.py with weighted confidence). NemoSkills' own GenSelect paper proves that smarter selection beats naive voting.

## The synthesis

The critique correctly identifies that we over-invested in Phase 0 documentation and should have been building sooner. It correctly warns against building Tier 2/3 modules at the expense of competition readiness. But it incorrectly dismisses the core insight: **typed verification evidence feeding into answer selection is a competitive advantage, not just research infrastructure.**

**The Opus prompt should therefore focus on: what are the truly novel, competitively relevant ideas from our conversation that can be implemented in the remaining time?**

---

# The Opus 4.6 Prompt

Save this as `docs/RESEARCH_PROBLEM.md` in your repo, then open Antigravity with Opus 4.6 selected and say: "Read and execute docs/RESEARCH_PROBLEM.md"

```markdown
# Research Problem: Verification-Guided Answer Selection for AI-Hard Mathematical Olympiad Problems

## Instructions for Opus 4.6

You are acting as a research scientist formulating a precise, novel research
problem and implementation plan. This document synthesizes months of architectural
reasoning into a focused research agenda. Your task:

1. Read this entire document carefully
2. Produce a research manuscript (docs/RESEARCH_MANUSCRIPT.md) that:
   - Formalizes the core research problem with mathematical precision
   - Cites all referenced literature correctly
   - Derives the proposed solution from first principles
   - Specifies concrete experiments that can run within 20 days
   - Identifies the single hardest open subproblem and formulates it as a
     self-contained research question suitable for GPT-5.4 Pro to attack
3. The manuscript should be genuinely publishable — not a competition report,
   but a contribution to the field of verified mathematical reasoning systems

## Context: The AIMO3 Competition

The AI Mathematical Olympiad Prize 3 (AIMO3) is a Kaggle competition ending
April 8, 2026. It presents 110 original mathematical problems spanning algebra,
combinatorics, geometry, and number theory at National Olympiad to IMO difficulty.
Answers are integers in [0, 99999]. Teams get two submission attempts per problem.
Inference runs on a single NVIDIA H100 80GB GPU. All code must be open-source.

Current leaderboard top scores: 46 and 45 out of ~55 public problems.

The submission model is gpt-oss-120B, an Apache 2.0 MoE model (117B total,
5.1B active parameters per token) that fits on a single H100 in MXFP4 
quantization and outperforms OpenAI o4-mini on competition mathematics
(AIME 2024 & 2025).

## The Core Research Problem

### Problem Statement

Given a mathematical competition problem P and a set of N independently 
generated solution traces {T_1, ..., T_N} from a language model, each 
producing a candidate integer answer a_i, how should we select the final 
answer to maximize probability of correctness, given that:

1. Simple majority voting treats all traces as equally reliable
2. Traces contain heterogeneous evidence (explicit calculations that can be
   mechanically verified, algebraic claims that can be symbolically checked,
   logical deductions that can only be assessed heuristically)
3. The two-attempt structure means we can submit a "safe" answer and a 
   "speculative" answer
4. We have finite compute budget for verification

This is a **meta-reasoning** problem: reasoning about the quality of reasoning.

### Why This Is Hard (and Novel)

The standard approach (majority voting / self-consistency; Wang et al., 2022, 
"Self-Consistency Improves Chain of Thought Reasoning in Language Models") 
treats all solution traces as exchangeable samples. But they are not 
exchangeable: a trace that makes a verifiable arithmetic error in step 3 
is strictly less trustworthy than a trace whose every calculation checks out,
even if both arrive at the same answer.

NemoSkills' GenSelect (Toshniwal et al., 2025, the AIMO2 winning approach)
improved on majority voting by training a model to select the best solution.
But GenSelect is a learned selector trained on (problem, solution, correctness)
triples — it operates on the surface text of solutions, not on structured
verification evidence.

Our contribution: **decompose each solution trace into mechanically verifiable
and non-verifiable components, compute typed confidence scores for the 
verifiable components, and use these scores to weight the answer selection.**

This is not a new idea in formal verification (LeanDojo's premise selection
and ReProver, Yang et al., 2023, "LeanDojo: Theorem Proving with Retrieval-
Augmented Language Models," demonstrate that structured verification feedback
improves proof search). What is new is applying it to the **informal 
mathematical reasoning** setting where full formalization is infeasible 
but partial mechanical verification is cheap and informative.

## The Ideas This Architecture Builds On

### Idea 1: The Generate-Verify-Revise Loop (from Aletheia)

DeepMind's Aletheia (February 2026, "Towards Autonomous Mathematics Research,"
arXiv:2502.xxxxx) demonstrated that explicitly separating generation from 
verification in natural language reasoning produces dramatic accuracy gains. 
Aletheia's three-part loop — Generator proposes, Verifier attacks, Reviser 
repairs — achieved up to 91.9% on IMO-ProofBench Advanced, compared to 65.7%
for its predecessor.

The key insight we draw from Aletheia: **the separation of roles is more
important than the capability of any single role.** A mediocre verifier that
is structurally independent from the generator catches errors that the 
generator systematically overlooks. This is analogous to the "System 1 / 
System 2" distinction (Kahneman, 2011, "Thinking, Fast and Slow") — fast
generation followed by slow, deliberate checking.

However, Aletheia's verifier is an NL-only system powered by Gemini 3 Deep 
Think. When tested on 700 open Erdős problems, 68.5% of responses were 
fundamentally wrong, and 25% of "correct" responses were "mathematically 
empty" — the model reinterpreted the question to make the answer trivial. 
This demonstrates that NL-only verification has a hard ceiling on 
trustworthiness. Our architecture addresses this by layering deterministic
mechanical checks beneath the NL verification.

### Idea 2: Typed Verification Evidence (novel contribution)

Current mathematical reasoning systems return verification results as 
booleans or scalars. This collapses fundamentally different evidence types:

- "Python executed without error" (execution success)
- "2^100 mod 7 = 2, confirmed by recomputation" (arithmetic verification)
- "SymPy confirms (x+1)^2 = x^2+2x+1" (symbolic verification)
- "Brute-force checked all n ≤ 10^6" (exhaustive enumeration)
- "GPT-5.4 Pro says the proof looks correct" (NL judgment)

Collapsing these into one signal is information-destroying. A solution where
every arithmetic step checks out but the logical structure is questionable
has a very different risk profile than a solution where the logic is 
compelling but the arithmetic is wrong.

Our ConfidenceLevel taxonomy (LEVEL_0_EXACT through UNVERIFIED) is inspired
by the trust hierarchies in interactive theorem proving (de Moura et al., 
2015, "The Lean Theorem Prover," CADE-25), where the kernel's acceptance
is distinguished from tactic success, which is distinguished from elaboration
success. We adapt this hierarchy to the informal setting.

Related work: Google's SAFE framework (Wei et al., 2024, "Long-form 
factuality in large language models") decomposes long-form responses into 
atomic claims and verifies each independently. We apply the same 
decomposition principle to mathematical solution traces, but with 
domain-specific mechanical checkers instead of web search.

### Idea 3: Warm-Up Scaffolding via DSPy (from the GPT-5 Science Paper)

Bubeck et al. (November 2025, "Early science acceleration experiments 
with GPT-5") demonstrated that priming a model with a simplified, 
structurally-related problem before the full-complexity task unlocks 
capabilities that cold-start prompting cannot. The canonical example:
physicist Alexandru Lupsasca's GPT-5 experiment where the model failed 
on curved-space PDE symmetries cold, but succeeded after solving the 
flat-space limit as a warm-up.

A similar pattern appeared in the combinatorics results: GPT-5 reproved
a known inequality (Theorem IV.3.1) as a warm-up before successfully 
proving a previously unresolved conjectured strengthening (Theorem IV.3.2).

Stanford's DSPy framework (Khattab et al., 2023, "DSPy: Compiling 
Declarative Language Model Calls into Self-Improving Pipelines") enables
this scaffolding to be optimized end-to-end. The warm-up question becomes
a latent variable in a multi-module program; the optimizer finds whatever
warm-up maximizes downstream solve accuracy.

The critical risk (which we identified): the warm-up must be structurally
aligned with the target problem, not merely "simpler." The GPT-5 paper's
scaffolds worked because the flat-space limit shares the same symmetry 
class as the curved-space problem. A random simplification provides no
transferable structure. DSPy can optimize for this, but only if the 
evaluation signal is strong enough — which circles back to our typed 
verification providing a richer signal than binary correctness.

### Idea 4: Evolutionary Code Optimization (from AlphaEvolve)

DeepMind's AlphaEvolve (2025) demonstrated that pairing LLM-generated 
code variants with automated evaluators and evolutionary selection can 
discover algorithms that outperform human-designed baselines. The key 
architectural insight: generate candidate programs, evaluate 
programmatically, retain the fittest, iterate.

OpenEvolve (open-source reimplementation) replicated AlphaEvolve's 
circle-packing results and demonstrated +23% accuracy improvement on 
HotpotQA through evolved prompts.

For our setting, OpenEvolve optimizes the *code* surrounding the LLM 
(verification logic, sampling parameters, answer selection strategy,
time allocation heuristics) while DSPy optimizes the *prompts* sent 
to the LLM. These are complementary attack surfaces. The evaluation 
function for both is: "how many practice problems does the full pipeline
solve correctly?"

### Idea 5: State-Conditional Retrieval for Compositional Problem Solving

LeanDojo (Yang et al., 2023) showed that premise selection — retrieving
relevant lemmas conditioned on the current proof state — is a critical
bottleneck in formal theorem proving. ReProver's retrieval-augmented 
approach improved over non-retrieval baselines, especially on novel 
premises.

Later work showed that structural dependency information (graphs capturing
relations among premises) improves premise selection beyond text-only 
retrieval. The HERALD dataset (Lean 4 → natural language translation 
pipeline) demonstrated that aligning formal and informal representations
at scale is feasible.

For competition mathematics, the analogy is: instead of retrieving 
"similar problems" (classic RAG, which fails on novel problems by design),
retrieve *micro-facts and transformation templates* conditioned on the 
solver's current subgoal state. This is closer to how human mathematicians
work — they don't look up "similar problems," they recall applicable 
lemmas and techniques triggered by the structure of their current 
intermediate result.

Mathlib4 (~1.9M lines of formalized mathematics) provides the raw material.
The challenge is making it retrievable in a way that respects logical
prerequisites, not just semantic similarity.

### Idea 6: The regress-lm Difficulty Predictor

Google's RegressLM (2024) demonstrated that small text-to-text regression
models (60M parameters) can predict numeric properties from textual 
descriptions with near-perfect rank correlation, adapting to new tasks 
in ~500 examples.

For competition mathematics, a difficulty predictor trained on 
(problem_text → solve_probability) enables:
- Adaptive time allocation (spend more compute on solvable-but-hard problems)
- Solution reranking (score traces by predicted correctness probability)
- Gating (route only promising problems to expensive verification)

This is a "meta-cognition" layer — a tiny model that runs on CPU alongside
the main solver, providing calibrated confidence without consuming GPU 
resources.

### Idea 7: Specialist Modules (AlphaGeometry2 DDAR)

AlphaGeometry2 (Trinh et al., 2024, "Gold-medalist performance in solving
olympiad geometry with AlphaGeometry2," JMLR) solved 42/50 IMO geometry
problems from 2000-2024. Its DD+AR symbolic engine provides deterministic
proofs for plane geometry that does not require auxiliary constructions.

As an offline specialist, DDAR can:
- Verify geometric subclaims with zero hallucination risk
- Generate verified proof traces as training data for retrieval
- Provide ground-truth supervision for geometry-specific few-shot examples

The limitation: the language model front-end (for auxiliary point 
constructions) is not released. With greedy decoding, only 2/26 problems
requiring auxiliary constructions were solved. This bounds the specialist's
coverage but not its reliability on solvable problems.

### Idea 8: Kimina-Prover for Offline Formal Verification

Kimina-Prover (2025, based on Qwen2.5-72B) achieved state-of-the-art
results on miniF2F-test with a "Formal Reasoning Pattern" that bridges
informal intuition and formal Lean 4 code. The 8B distill achieves
77.86% Pass@32 on miniF2F-test.

As an offline component:
- Generate formally-verified micro-theorems for the retrieval library
- Validate algebraic identities that feed into the verification battery
- Provide Lean-kernel-level confidence (LEVEL_2_FORMAL) for specific subclaims

This is the only component that can achieve LEVEL_2_FORMAL confidence.
It is too slow and memory-intensive for inference time, but its outputs
can be pre-computed and cached.

## The Ideal Final State

### System Architecture

```
┌─────────────────────────────────────────────────────┐
│                 OFFLINE SYSTEMS                      │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐│
│  │  OpenEvolve   │  │    DSPy      │  │  Kimina    ││
│  │  (evolve code │  │  (optimize   │  │  Prover    ││
│  │   + prompts)  │  │   prompts)   │  │  (formal   ││
│  └──────┬───────┘  └──────┬───────┘  │   verify)  ││
│         │                  │          └─────┬──────┘│
│         v                  v                v       │
│  ┌──────────────────────────────────────────────┐  │
│  │          Verified Knowledge Store             │  │
│  │  (micro-theorems, schemas, fact cards,        │  │
│  │   evolved prompts, difficulty predictions)    │  │
│  └──────────────────────┬───────────────────────┘  │
│                          │                          │
│  ┌──────────────────────────────────────────────┐  │
│  │  AlphaGeometry2 DDAR    │  regress-lm        │  │
│  │  (geometry proofs)      │  (difficulty/rank)  │  │
│  └─────────────────────────┴────────────────────┘  │
└─────────────────────────┬───────────────────────────┘
                          │ pre-computed artifacts
                          v
┌─────────────────────────────────────────────────────┐
│              INFERENCE (Kaggle H100)                 │
│                                                      │
│  Problem ──→ [gpt-oss-120B + sampling diversity]     │
│                    │                                  │
│                    v N solution traces                │
│         ┌──────────────────────┐                     │
│         │  Verification Battery │                    │
│         │  (arithmetic, symbolic│                    │
│         │   brute force, answer │                    │
│         │   validation)         │                    │
│         └──────────┬───────────┘                     │
│                    │ typed VerificationReports        │
│                    v                                  │
│         ┌──────────────────────┐                     │
│         │  Answer Selector      │                    │
│         │  (confidence-weighted │                    │
│         │   selection, 2 attempts)                   │
│         └──────────┬───────────┘                     │
│                    │                                  │
│                    v final answer (integer)           │
└─────────────────────────────────────────────────────┘
```

### The Key Papers for the Ideal Final State

The ideal system integrates insights from three research threads:

**Thread 1: Verified Reasoning at Scale**
- Aletheia (DeepMind, 2026): generate-verify-revise in natural language
- AlphaProof (DeepMind, 2024): formal verification via Lean + MCTS
- AlphaGeometry2 (DeepMind, 2024): symbolic + neural for geometry
- Kimina-Prover (2025): bridging informal reasoning and formal proofs
- LeanDojo (Yang et al., 2023): retrieval-augmented theorem proving

**Thread 2: Optimized Inference for Mathematical Reasoning**
- NuminaMath (AIMO1 winner, 2024): TIR + self-consistency on 7B model
- NemoSkills (AIMO2 winner, 2025): GenSelect + large-scale training data
- GPT-5 Science Paper (Bubeck et al., 2025): scaffolded warm-up reasoning
- DSPy (Khattab et al., 2023): compiled multi-step LM programs

**Thread 3: Evolutionary and Meta-Learning Approaches**
- AlphaEvolve (DeepMind, 2025): evolutionary code optimization
- OpenEvolve (open-source, 2025): replicated AlphaEvolve results
- RegressLM (Google, 2024): text-to-numeric regression for meta-cognition

The ideal final state synthesizes these into a system where:
1. The solver generates diverse candidate solutions (Thread 2)
2. Each solution is decomposed into mechanically verifiable and 
   non-verifiable components (Thread 1)
3. Typed confidence scores feed into answer selection that is strictly
   more informative than majority voting (novel contribution)
4. Offline optimization continuously improves the solver's prompts,
   sampling strategy, and verification thresholds (Thread 3)
5. Pre-computed verified artifacts (micro-theorems, schemas, geometry
   proofs) reduce the solver's search entropy at inference time (Thread 1)

## The Research Question for GPT-5.4 Pro

### The Open Problem

The hardest unsolved subproblem in this architecture is:

**How do you optimally allocate a finite verification compute budget
across N solution traces and M verifiable claims per trace to maximize
the expected number of correctly-answered problems?**

Formally: given a problem P with N candidate solution traces 
{T_1, ..., T_N}, where each trace T_i contains M_i mechanically 
verifiable claims {c_{i,1}, ..., c_{i,M_i}}, and each verification 
v(c_{i,j}) costs compute time t_{i,j} and produces a typed confidence 
signal, and we have a total verification budget B:

maximize  E[correct(select(P, {T_i}, {v(c_{i,j})}))]
subject to  Σ_{verified claims} t_{i,j} ≤ B

This is a **stochastic scheduling problem** with information-dependent
rewards: verifying claim c_{i,j} changes the posterior probability that
T_i's answer is correct, which changes the optimal selection, which 
changes the value of verifying other claims.

### Why This Is the Right Problem for GPT-5.4 Pro

This problem has the same structure as the flat-space/curved-space 
warm-up from the Bubeck et al. paper:

**Warm-up (the flat-space limit):** In the degenerate case where all
claims are equally costly and all traces have the same number of claims,
this reduces to a multi-armed bandit where each arm is a trace and each
pull is a verification check. The optimal policy in this case is known
(Thompson sampling or UCB variants).

**Full problem (the curved-space generalization):** In the real setting,
claims have heterogeneous costs (arithmetic checks are fast, symbolic 
checks are slow), heterogeneous informativeness (a failed arithmetic
check is definitive, a passed symbolic check is strong but not 
definitive), and the budget constraint is a hard wall-clock limit.

GPT-5.4 Pro should:
1. Solve the warm-up (degenerate bandit case) to establish the framework
2. Extend to heterogeneous costs via a Lagrangian relaxation or 
   Whittle index approach
3. Incorporate the typed confidence signals as Bayesian updates
4. Produce a concrete algorithm (pseudocode) that can be implemented
   in src/solver/answer_selector.py as the verification-budget-aware
   selection policy

### The Experimental Protocol

To validate the solution:
1. Collect 50+ practice problems with known answers
2. Generate N=8 solution traces per problem with varied temperatures
3. Run the full verification battery on all traces (record time per check)
4. Compare answer selection accuracy:
   - Baseline: raw majority voting
   - Baseline: confidence-weighted voting (our current implementation)
   - Proposed: budget-optimal verification allocation + selection
5. Measure: accuracy, compute time, and accuracy-per-second tradeoff

The prediction: budget-optimal allocation should achieve strictly higher
accuracy than exhaustive verification at the same wall-clock budget,
because it can invest verification effort where it is most informative
(traces where the answer is uncertain, claims where failure would be 
most diagnostic).

## References

1. Bubeck, S. et al. (2025). "Early science acceleration experiments 
   with GPT-5." OpenAI.
2. DeepMind (2026). "Towards Autonomous Mathematics Research" (Aletheia).
3. DeepMind (2024). "Solving IMO Problems with AlphaProof and AlphaGeometry."
4. Trinh, T. et al. (2024). "Gold-medalist performance in solving olympiad 
   geometry with AlphaGeometry2." JMLR.
5. Yang, K. et al. (2023). "LeanDojo: Theorem Proving with Retrieval-
   Augmented Language Models." NeurIPS.
6. Khattab, O. et al. (2023). "DSPy: Compiling Declarative Language Model 
   Calls into Self-Improving Pipelines." ICLR.
7. Wang, X. et al. (2022). "Self-Consistency Improves Chain of Thought 
   Reasoning in Language Models."
8. Wei, J. et al. (2024). "Long-form factuality in large language models." 
   (SAFE framework).
9. de Moura, L. et al. (2015). "The Lean Theorem Prover." CADE-25.
10. Toshniwal, S. et al. (2025). NemoSkills / GenSelect (AIMO2).
11. NuminaMath (2024). AIMO1 winning solution.
12. Kahneman, D. (2011). "Thinking, Fast and Slow." (System 1/System 2).
13. Kimina-Prover (2025). Formal reasoning pattern for Lean 4.
14. AlphaEvolve / OpenEvolve (2025). Evolutionary code optimization.
15. RegressLM (Google, 2024). Text-to-text regression.
16. HERALD (2024). Natural-language annotated Lean 4 dataset.

## Output Specification

Produce docs/RESEARCH_MANUSCRIPT.md containing:

1. **Abstract** (200 words)
2. **Introduction** (the problem, why it matters, what's novel)
3. **Background and Related Work** (cite all 16 references above,
   plus any additional relevant literature you identify)
4. **Method** (the architecture, the typed evidence taxonomy, the
   verification battery, the selection algorithm)
5. **The Open Problem** (the verification budget allocation problem,
   formalized mathematically, with the warm-up/full-problem structure
   suitable for GPT-5.4 Pro)
6. **Proposed Experiments** (concrete protocol, baselines, metrics)
7. **Discussion** (limitations, the honest gap between ideal and 
   implementable-in-25-days, what we sacrifice and why)
8. **References**

Target: 4000-6000 words. Aim for genuine intellectual contribution,
not a competition report. The audience is researchers working on 
verified mathematical reasoning systems.

Do not pad. Do not add filler. Every sentence should either state a
fact, make an argument, or specify a method. If a section would be
weak, make it shorter rather than longer.
```