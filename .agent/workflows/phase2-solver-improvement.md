---
name: phase2-solver-improvement
description: Improve the gpt-oss-120B inference script for AIMO3
---

# Phase 2: Solver Improvement

## Context
The submission model is gpt-oss-120B running on Kaggle H100.
We are improving the INFERENCE SCRIPT, not the model weights.

## Architecture Reference
Module skeletons are in src/solver/. Each contains typed stubs with
implementation notes.

## Key modules
- inference_engine.py: VLLMEngine for Kaggle, abstract base for flexibility
- python_executor.py: Sandboxed code execution for tool-integrated reasoning
- sampling_strategy.py: Multi-temperature diverse sampling
- answer_selector.py: Verification-weighted answer selection

## Implementation Order
1. python_executor.py (independent, critical for tool use)
2. sampling_strategy.py (independent)
3. inference_engine.py (may need existing solver code as reference)
4. answer_selector.py (depends on verification models from Phase 1)

## Carry forward from existing code
- Check docs/IMPLEMENTATION_BRIEF.md Section 1 for working prompts
  and solver interfaces that must be preserved
- The new InferenceEngine must handle at least every input format
  the old agent/solver.py handled
