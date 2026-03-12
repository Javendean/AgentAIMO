# GEMINI.md — AgentAIMO Project Context

## Project Summary
This is a competitive mathematics AI system targeting the AIMO3 Kaggle competition.
The submission model runs gpt-oss-120B on a single NVIDIA H100 (80GB VRAM).
The meta-system (this repo) builds offline verification, critique, optimization,
and inference script tooling.

## Competition Constraints
- Deadline: April 8, 2026
- Hardware at inference: 1x NVIDIA H100 80GB
- Answer format: integer 0-99999
- Two submission attempts per problem
- 110 original problems (algebra, combinatorics, geometry, number theory)
- All code and data must be made public to qualify for prizes
- Top public scores as of March 2026: 46 and 45

## Available Compute (offline)
- Google Colab Pro for Education: 100 compute units/month
- Google Cloud: up to 24 N4 vCPU + 640GB memory
- Local: Alienware Aurora R8, 8GB GPU VRAM, 16GB RAM
- Kaggle: 1x H100 80GB (competition notebooks)
- APIs: DeepSeek-V3.2-Speciale, GPT-5.4 Pro (budget-limited)

## Key Dependencies
- OpenEvolve (github.com/algorithmicsuperintelligence/openevolve)
- AlphaGeometryRE (github.com/foldl/AlphaGeometryRE)
- DSPy (stanfordnlp/dspy)
- SymPy, NumPy, mpmath (symbolic/numeric verification)
- Lean 4 + Mathlib (offline only, never at inference time)

## Standards
- Python 3.10+, type hints on all functions
- Google-style docstrings
- Every verification function must have unit tests
- No Lean or formal compilation at Kaggle inference time
- All API calls must have retry logic, timeout handling, and cost logging

## Code Intelligence
This project uses GitNexus MCP for structural codebase awareness.
The agent has access to tools: query, impact, context, search, processes.
Always use the impact tool before refactoring any existing code.
Re-index with npx gitnexus analyze after creating new modules.
