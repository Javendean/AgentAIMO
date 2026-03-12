---
name: phase1-verification-battery
description: Build the deterministic mathematical verification battery
---

# Phase 1: Deterministic Verification Battery

This is the HIGHEST-ROI component. Build it thoroughly.

## Architecture Reference
All module skeletons with complete type signatures, dataclass definitions,
and method stubs are in src/verification/. Each file contains NotImplementedError
stubs with detailed implementation notes in docstrings.

## Implementation Order
1. src/verification/arithmetic_checker.py (no internal dependencies)
2. src/verification/symbolic_checker.py (no internal dependencies)
3. src/verification/brute_force_checker.py (no internal dependencies)
4. src/verification/counterexample_search.py (no internal dependencies)
5. src/verification/answer_validator.py (no internal dependencies)
6. src/verification/solution_parser.py (complex NLP — may need Claude model)
7. src/verification/pipeline.py (depends on ALL above)
8. tests/verification/ (comprehensive tests for all modules)

Steps 1-5 can be implemented in parallel.
Steps 6-7 must be sequential after 1-5.
Step 8 can partially parallel with 6-7.

## For each module
1. Read the skeleton file completely
2. Implement every method marked with raise NotImplementedError
3. Follow the implementation notes in each method's docstring exactly
4. Write corresponding tests in tests/verification/
5. Run pytest on the module before moving to next

## Completion criteria
- All NotImplementedError stubs replaced with working implementations
- All tests pass
- pytest --tb=short shows green across all verification tests
