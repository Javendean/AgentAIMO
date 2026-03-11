# Notebook and Branch Divergence Blindspots

This document exposes divergence between notebook and package code, local-vs-GitHub mismatch risks, and notebook-specific logic.

- Blindspot ID: BS-DIV-001
- Title: `notebook/` vs `44-50*.ipynb` Divergence
- Category: Notebook and Branch Divergence
- Severity: high
- Confidence: high
- Status: fact
- Why this is a blindspot: The intended deployment script `notebook/kaggle_notebook.py` imports `DeepResearcher` from the package, but the root directory contains a completely separate, seemingly active notebook `44-50-aimo3-skills-optional-luck-required.ipynb` that implements a custom `AIMO3Solver`.
- Evidence:
  - `notebook/kaggle_notebook.py` imports `agent.deep_researcher.DeepResearcher`.
  - `44-50-aimo3-skills-optional-luck-required.ipynb` defines `class AIMO3Solver` with similar but divergent logic (e.g., `_compute_mean_entropy`, wave-based generation).
- What could be misleading: A reader might assume that the two files represent the same execution logic, just in different formats. In reality, they are two different implementations of the core algorithm.
- Potential consequence: Changes to `agent/deep_researcher.py` will not affect submissions made using the root notebook. Conversely, improvements made in the root notebook are invisible to the package code.
- How to verify or falsify it: Compare the implementation of `_select_answer` in the root notebook with `_majority_vote` in `agent/deep_researcher.py`.
- Recommended next step: Determine which solver is canonical and delete or clearly archive the other.
- Blocks future work? yes

- Blindspot ID: BS-DIV-002
- Title: Fail-Fast Logic Missing from Package
- Category: Notebook and Branch Divergence
- Severity: medium
- Confidence: high
- Status: fact
- Why this is a blindspot: The deployment notebook `notebook/kaggle_notebook.py` contains critical "fail-fast" logic (canary testing and swapping from a 120B model to a 72B model) that does not exist in the core package `agent/deep_researcher.py`.
- Evidence:
  - `notebook/kaggle_notebook.py:run_canary_test` and the subsequent "KILL SWITCH" and "SWAP TO QWEN-72B" logic.
- What could be misleading: A developer running the package code locally might assume they are running the identical fault-tolerant system used on Kaggle, but they are missing the canary test entirely.
- Potential consequence: The package code is brittle to model logic collapse or hardware OOMs, while the notebook deployment script attempts to handle them. This creates a local-vs-production mismatch.
- How to verify or falsify it: Search for `run_canary_test` or model swapping logic within `agent/`.
- Recommended next step: Move the canary testing and fail-fast fallback logic into the `DeepResearcher` class itself, making it configurable.
- Blocks future work? no