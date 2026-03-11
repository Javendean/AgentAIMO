# Architectural Blindspots

This document exposes unclear system boundaries, hidden drift, competing implementations, and dead subsystems.

- Blindspot ID: BS-ARC-001
- Title: Divergent Notebook Solver Loop
- Category: Architecture
- Severity: high
- Confidence: high
- Status: fact
- Why this is a blindspot: There is a completely parallel solver implementation (`AIMO3Solver`) in the root directory that duplicates the core logic of `agent/deep_researcher.py`.
- Evidence:
  - `44-50-aimo3-skills-optional-luck-required.ipynb` contains a full implementation of `AIMO3Solver`, wave-based generation, entropy calculation, voting, and tool execution.
  - `notebook/kaggle_notebook.py` imports `DeepResearcher` from `agent/deep_researcher.py` and runs it.
- What could be misleading: A developer reading `agent/deep_researcher.py` might assume it is the sole entrypoint for the competition, unaware that a completely different solver was used or is being used.
- Potential consequence: Any bug fixes or feature additions (like DSPy or specialized routers) added to the package code will not apply to the `AIMO3Solver` notebook, leading to silent regressions in Kaggle submissions.
- How to verify or falsify it: Ask the author which file is the canonical source of truth for the Kaggle submission.
- Recommended next step: Deprecate one of the solver loops or merge the `AIMO3Solver` features (like entropy tracking) into `agent/deep_researcher.py`.
- Blocks future work? yes

- Blindspot ID: BS-ARC-002
- Title: Unclear Package Entrypoint and Hardcoded Paths
- Category: Architecture
- Severity: medium
- Confidence: medium
- Status: strong inference
- Why this is a blindspot: The intended deployment script (`notebook/kaggle_notebook.py`) relies on hardcoded absolute paths specific to the Kaggle environment (e.g., `/kaggle/input/aimo-agent-code/`).
- Evidence:
  - `notebook/kaggle_notebook.py`: `sys.path.insert(0, "/kaggle/input/aimo-agent-code/")`
  - `notebook/kaggle_notebook.py`: `PROBLEMS_PATH = "/kaggle/input/aimo-problems/problems_v1.jsonl"`
- What could be misleading: A developer running the code locally might encounter `ModuleNotFoundError` or `FileNotFoundError` because the environment structure is tightly coupled to Kaggle's specific dataset mounting scheme.
- Potential consequence: Local testing and CI pipelines will fail unless they replicate the exact `/kaggle/input/...` directory structure.
- How to verify or falsify it: Attempt to run the agent pipeline locally without modifying `notebook/kaggle_notebook.py`.
- Recommended next step: Refactor the entrypoint to use relative imports (`pathlib`) or parameterized arguments for datasets.
- Blocks future work? yes