---
name: phase3-nl-critique-loop
description: Build the natural language critique and revision pipeline
---

# Phase 3: NL Critique Loop

## Architecture Reference
Module skeletons are in src/critique/. Each contains typed stubs.

## Key modules
- critic_client.py: API wrapper for DeepSeek-V3.2-Speciale + GPT-5.4 Pro
- critique_pipeline.py: Dual-model cross-checking orchestration
- revision_pipeline.py: Revise solutions based on critique feedback

## Dependencies
- src/utils/api_client.py MUST be implemented first (Phase 1 or 2)
- src/models/critique.py data models must exist (created in skeleton)
- src/models/verification.py must exist (critique consumes VerificationReport)

## Implementation Order
1. Ensure src/utils/api_client.py is complete
2. src/critique/critic_client.py
3. src/critique/critique_pipeline.py
4. src/critique/revision_pipeline.py (needs inference engine from Phase 2)
