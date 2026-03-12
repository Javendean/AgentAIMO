---
description: Core project identity and constraints for AgentAIMO
activation: always
---

# Project Identity

This is the AgentAIMO project — a meta-system for the AIMO3 Kaggle math competition.

## Hard Constraints (never violate)
- Competition deadline: April 8, 2026
- Submission model: gpt-oss-120B on 1x H100 80GB
- All code must be Apache 2.0 compatible and publicly shareable
- Answer format: integer 0-99999
- No internet access during Kaggle inference
- No Lean/formal verification at inference time (VRAM is filled by model)

## Current Phase
Check the file STATUS.md in project root for the current phase and priorities.
If STATUS.md does not exist, assume Phase 1 (verification battery implementation).
