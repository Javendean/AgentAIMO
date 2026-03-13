# Repository Map

This document provides a structural map of the repository as it currently exists, categorizing files by their apparent purpose and highlighting areas that require manual review or future cleanup.

## 1. Production-Like Code (Core Package)

| Path | Purpose | Trust Level |
| :--- | :--- | :--- |
| `agent/__init__.py` | Package root | High |
| `agent/deep_researcher.py` | Primary orchestration loop, majority voting, GenSelect, self-correction | High |
| `agent/prompts.py` | All prompt templates and answer extraction logic | High |
| `agent/sandbox.py` | Python code execution in a sandboxed subprocess | High |
| `agent/topic_classifier.py` | Naive keyword-based topic classifer | Medium (known bug) |
| `agent/tool_executor.py` | Thin wrapper around sandbox for TIR | High |

## 2. Execution Harness (Mainline/Notebook Divergence)

| Path | Purpose | Trust Level |
| :--- | :--- | :--- |
| `notebook/kaggle_notebook.py` | **Actual Kaggle submission entrypoint**. Canary test, model selection, time budgeting | High (critical) |
| `44-50-aimo3-skills-optional-luck-required.ipynb` | **Parallel AIMO3Solver** – completely separate, competing solver loop. Not archival. | High (diverging) |

## 3. Analysis and Grading Pipeline

| Path | Purpose | Trust Level |
| :--- | :--- | :--- |
| `analysis/analyze_results.py` | Reads `.jsonl` logs, generates `prompt_patch.txt` | Medium (self-reports) |
| `analysis/` (other files) | Supporting analysis tooling | Low-medium |

## 4. Test Suite

| Path | Purpose | Trust Level |
| :--- | :--- | :--- |
| `tests/test_agent.py` | Shallow dry-run tests; no LLM mocking | Low (known sparse) |
| `tests/test_hallucination_fix.py` | Stub test for hallucination fixes | Low |

## 5. Experimental / Research Code (Root Level)

These files are present in the root and appear to be one-off research or data-prep scripts. They may reference hardcoded paths.

- `analyze_failures.py`, `create_preference_dataset.py`, `clean_research_data.py`
- `chunk_research_data.py`, `extract_syntax_errors.py`, `extract_top_leaderboard.py`
- `filter_notebooks.py`, `scrape_candidate_notebooks.py`, `create_submission_zip.py`
- `process_pdf_v2.py`, `process_context_final.py`, `process_context_final_v2.py`
- `verify_context.py`, `verify_solved.py`, `test_safeguard.py`
- `optimize_context.py`, `maximize_density.py`, `fix_lines_16_91.py`, `split_dense_context.py`, `inspect_zip.py`

## 6. Noisy / Archival Artifacts (Root Level)

These files have no programmatic role and should be relocated per `docs/MOVE_CANDIDATES.md`.

- **Chat transcripts:** `GeminiChat.txt`, `BrowserChat.txt`
- **PDF extracts:** `pdf1.txt`, `pdf2.txt`, `pdf3.txt`, `pdf_abstracts.txt`, `2511.01846v1_Part1.txt`
- **Research notes:** `annotation_research_context.md`, `mcts_rubric_analysis.md`, `rubric.md`
- **Generated data:** `research_data.jsonl`, `research_data2.jsonl`, `research_data2.jsonl.bak`
- **DPO datasets:** `dpo_correction_dataset.jsonl`, `dpo_correction_dataset_v2.jsonl`, `dpo_correction_dataset_v3.jsonl`, `dpo_correction_dataset_v4.jsonl`
- **Scratch files:** `c2_sorted_check.txt`, `new_context_content.txt`, `syntax_errors.txt`, `prompt_patch.txt`

## 7. Future Restructuring Candidates

See `docs/MOVE_CANDIDATES.md` for the full restructuring plan with risk ratings. Summary:
- The `src/` directory is reserved for the new typed module architecture.
- Scripts should move to `scripts/`.
- Data should move to `data/`.
- Archival noise should move to `_attic/`.