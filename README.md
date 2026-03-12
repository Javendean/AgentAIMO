# DeepResearcher v2

DeepResearcher v2 is an H100-optimized Python agent designed to solve complex mathematical problems (e.g., AIMO) through repeated generation, Tool-Integrated Reasoning (TIR) via Python code execution, and majority-vote consensus.

## Repository Layout

*   `agent/`: The core agent logic, including the prompt generator (`prompts.py`), sandbox execution (`sandbox.py`), and the main loop (`deep_researcher.py`).
*   `notebook/`: Deployment code intended to run within Kaggle notebooks, including environment preparation and fail-fast fallback logic.
*   `analysis/`: Local scripts for reviewing output (`research_data.jsonl`) and generating heuristic system prompt patches.
*   `docs/`: Extensive documentation auditing the repository's architecture, verification semantics, extraction ambiguities, and technical debt.
*   `tests/`: Unit tests for the agent components.

## Documentation First

This repository contains multiple overlapping scripts, archival data files, and parallel solver loops (most notably in `44-50*.ipynb`). Before contributing, adding features, or debugging failures, please consult the primary repository map and risk register:

**Start Here:**
1.  **[docs/README.md](docs/README.md)** - Guide to the repository's documentation and audit summaries.
2.  **[docs/BLINDSPOT_EXECUTIVE_SUMMARY.md](docs/BLINDSPOT_EXECUTIVE_SUMMARY.md)** - A concise summary of the critical logical flaws and hidden dependencies in the codebase.
3.  **[docs/REPO_MAP.md](docs/REPO_MAP.md)** - Explains the divergence between the core package and root-level exploratory notebooks.

## Key Architectural Notes

*   **Verification is Execution:** The current agent equates a Python script running without crashing as a "verified" attempt. This is a known risk (BS-VER-001) that conflates syntactic validity with mathematical truth.
*   **Answer Extraction is Exact:** The majority vote tallying mechanism compares extracted strings identically without canonicalization or LaTeX normalization.
*   **Sandbox is Limited:** The python execution sandbox relies on a software blocklist and is not a true security container. It is designed to stop accidental OOMs or simple infinite loops, not determined breakouts.