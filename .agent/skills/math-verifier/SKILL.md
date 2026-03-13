---
name: math-verifier
description: >
  Activated when the user asks to verify, check, or validate a mathematical
  claim, solution, proof step, or competition answer.
---

# Math Verifier Skill

When verifying any mathematical claim, follow the verification hierarchy
in .agent/rules/02-math-verification-standards.md.

## Procedure
1. First attempt DETERMINISTIC verification (SymPy, brute force, counterexample)
2. Only if deterministic methods are inapplicable, use NL critique
3. Always assign a confidence level to every result
4. Never claim verified without specifying the method used

## Tools Available
- src/verification/arithmetic_checker.py
- src/verification/symbolic_checker.py
- src/verification/brute_force_checker.py
- src/verification/counterexample_search.py
- src/verification/answer_validator.py
- src/verification/pipeline.py
