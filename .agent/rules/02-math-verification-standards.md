---
description: Standards for mathematical verification code
activation: always
---

# Mathematical Verification Standards

## Hierarchy of Trust (use the strongest applicable method)
1. Deterministic exact match — answer equals known ground truth
2. Symbolic verification — SymPy confirms algebraic identity/inequality
3. Numerical spot-check — evaluate at 50+ random points
4. Brute-force enumeration — exhaust all cases for small parameter values
5. Counterexample search — systematic + random search for violations
6. CAS cross-check — SageMath or Mathematica confirms result
7. NL critique — LLM-based review (lowest trust; always flag confidence level)

## Confidence Levels (annotate every verification result)
- LEVEL_0_EXACT: answer matches known ground truth (deterministic)
- LEVEL_1_SYMBOLIC: all numeric/algebraic subclaims pass CAS + brute force
- LEVEL_2_FORMAL: Lean-verified subgoals (offline only)
- LEVEL_3_NL_PASS: NL verifier passed (useful but fallible)
- LEVEL_4_SPECULATIVE: schema/pattern extracted (needs human review)
- UNVERIFIED: no verification attempted or possible

## Anti-Hallucination Rules
- Never claim a proof step is verified based only on NL judgment
- Always attempt programmatic verification before NL verification
- If a step cannot be programmatically verified, label it UNVERIFIED
- Cross-check NL critics: if two frontier models disagree, escalate to human
- Never treat code executed successfully as equivalent to math verified
- Never collapse execution success, checker success, and proof success into one boolean
