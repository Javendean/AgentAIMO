# Repository Map

This document maps the structural state of the repository as it currently exists, identifying production areas, experimental zones, and structural divergence.

## 1. Production-Like Code (Core Package)

The `agent/` directory houses the primary Python package for the DeepResearcher H100-Optimized Math Research Agent. This is the core logic engine.

*   `agent/__init__.py`: Package initialization.
*   `agent/deep_researcher.py`: The main controller managing the research loop, multi-sampling (majority voting), dynamic time allocation, Tool-Integrated Reasoning (TIR) orchestration, and fallback loops.
*   `agent/prompts.py`: Prompt templating engine, including heuristic topic classification and model family auto-detection.
*   `agent/sandbox.py`: Sandboxed subprocess environment for Python execution.

## 2. Execution Harness (Mainline/Notebook Divergence)

The `notebook/` directory contains the mainline entry points meant for the Kaggle platform.

*   `notebook/kaggle_notebook.py`: The Kaggle execution script. It handles offline environment setup, initializes the `DeepResearcher`, and contains hardcoded fallback logic (the "Canary Test").
*   **Divergence Risk:** The Kaggle notebook acts as `main.py` but is structurally isolated from `agent/`. Critical logic (like testing whether the 120B model is hallucinating via the Canary Test) lives in the notebook rather than the package, making it difficult to test or run locally without modification.

## 3. Analysis and Grading Pipeline

The `analysis/` directory contains the offline grading tools.

*   `analysis/analyze_results.py`: Parses JSONL outputs to compute success metrics, identify failure patterns, and auto-generate prompt patches.

## 4. Test Suite

The `tests/` directory contains the unit test suite.

*   `tests/test_agent.py`: Tests sandbox security blocks, prompt extraction, and runs a mock pipeline dry-run.
*   `tests/test_hallucination_fix.py`: Specific test for `assistantcommentary` parsing.

## 5. Experimental / Research Code (Root Level)

The root directory contains a significant number of one-off utilities, data preparation scripts, and context optimizers. These are mixed-purpose and lack organization.

*   **Context/Formatting:** `optimize_context.py`, `maximize_density.py`, `process_context_final.py`, `process_context_final_v2.py`, `split_dense_context.py`
*   **Dataset Handling:** `chunk_research_data.py`, `clean_research_data.py`, `create_preference_dataset.py`, `verify_context.py`
*   **Analysis/Debugging:** `analyze_failures.py`, `extract_syntax_errors.py`, `verify_solved.py`, `test_safeguard.py`
*   **Web/API:** `extract_top_leaderboard.py`, `scrape_candidate_notebooks.py`
*   **Packaging:** `create_submission_zip.py`, `inspect_zip.py`
*   **Unclear/Suspicious:** `fix_lines_16_91.py`, `filter_notebooks.py`

## 6. Noisy / Archival Artifacts (Root Level)

The root directory is heavily populated with generated data, transcript dumps, and text files.

*   **Datasets:** `*.jsonl` files (e.g., `research_data.jsonl`, `dpo_correction_dataset.jsonl`)
*   **Transcripts:** `GeminiChat.txt`, `BrowserChat.txt`
*   **Text Extracts/Notes:** `pdf1.txt`, `pdf_abstracts.txt`, `annotation_research_context.md`, `rubric.md`, `prompt_patch.txt`
*   **Notebooks:** `44-50-aimo3-skills-optional-luck-required.ipynb`

## 7. Future Restructuring Candidates

*   **Mainline Unification:** Refactoring the logic in `notebook/kaggle_notebook.py` into a testable `agent/main.py` entry point.
*   **Root Cleanup:** Sweeping all root-level experimental `.py` scripts into a `scripts/` directory.
*   **Data Partitioning:** Moving all `.jsonl` and `.txt` files into structured `data/raw/` and `data/processed/` directories.