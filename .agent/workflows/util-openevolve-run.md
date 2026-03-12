---
name: util-openevolve-run
description: Configure and execute an OpenEvolve optimization run
---

# Utility: OpenEvolve Run

## Prerequisites
- OpenEvolve installed (pip install openevolve)
- Target script to optimize identified
- Evaluation function defined with clear numeric metric
- Compute budget approved by human

## Steps
1. Prepare evaluation function in src/optimization/eval_function.py
2. Create OpenEvolve config in configs/openevolve_config.yaml
3. Run with monitoring and hard cost ceiling
4. Validate evolved artifacts (diff against baseline, run tests)
5. Present diff to human for approval before merging

## What OpenEvolve should optimize
- Inference script parameters (temperature, sampling, selection)
- Verification logic and thresholds
- Prompt templates

## What OpenEvolve must NOT change
- Function signatures and API contracts
- Safety checks and validation logic
- External API configurations
