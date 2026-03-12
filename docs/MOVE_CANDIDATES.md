# Move Candidates Manifest

This document proposes a future restructuring plan to cleanly separate active source code from data artifacts, research materials, and legacy noise.

**Important Note:** This is a *recommendation* document only. No files have been moved in the current task. Moving these files carries varying degrees of risk depending on whether hardcoded paths exist in the Python scripts or Kaggle notebooks.

---

## 1. High Priority (Safe Moves)
These are static, manual text dumps or chat transcripts that are highly unlikely to be referenced by any programmatic pipeline.

| Current Path | Proposed Location | Why | Risk Level |
| :--- | :--- | :--- | :--- |
| `BrowserChat.txt` | `_attic/noise/` | Unstructured manual export, creates root clutter. | Safe |
| `GeminiChat.txt` | `_attic/noise/` | Unstructured manual export, creates root clutter. | Safe |
| `c2_sorted_check.txt` | `_attic/noise/` | Looks like a manual terminal output or diff. | Safe |
| `new_context_content.txt` | `_attic/noise/` | Unclear scratchpad file. | Safe |
| `research_data2.jsonl.bak` | `_attic/noise/` | Redundant backup file. | Safe |

---

## 2. Medium Priority (Research / Raw Materials)
These files represent valuable research inputs (like academic papers or manual notes) but do not belong in the root directory.

| Current Path | Proposed Location | Why | Risk Level |
| :--- | :--- | :--- | :--- |
| `2511.01846v1_Part1.txt` | `research/raw/` | Academic paper text extract. | Safe |
| `pdf1.txt`, `pdf2.txt`, `pdf3.txt` | `research/raw/` | PDF text extracts. | Safe |
| `pdf_abstracts.txt` | `research/raw/` | PDF text extracts. | Safe |
| `annotation_research_context.md` | `research/docs/` | Conceptual documentation. | Safe |
| `mcts_rubric_analysis.md` | `research/docs/` | Conceptual documentation. | Safe |
| `Refining LLM Rubric for Human Reasoning.md`| `research/docs/` | Conceptual documentation. | Safe |
| `rubric.md` | `research/docs/` | Grading guidelines. | Safe |

*Note: The root-level notebook `44-50-aimo3-skills-optional-luck-required.ipynb` has been explicitly removed from the "Moderate" move candidate list, as it represents a fully active parallel `AIMO3Solver` workflow rather than legacy or exploratory noise. It should not be moved until the core architecture is formally unified.*

---

## 3. High Risk (Data Pipelines & Executables)
These files are generated datasets or the utility scripts that generate them. Moving them is highly likely to break hardcoded relative paths inside the scripts (e.g., `with open("research_data.jsonl")`).

| Current Path | Proposed Location | Why | Risk Level |
| :--- | :--- | :--- | :--- |
| `research_data.jsonl` | `data/raw/` | Core system output. | Risky (Referenced implicitly by analysis scripts) |
| `dpo_correction_dataset*.jsonl` | `data/processed/` | Downstream training artifacts. | Risky (Likely referenced by a trainer script not present here) |
| `create_preference_dataset.py` | `scripts/` | Data pipeline utility. | Risky (Will need internal path updates) |
| `clean_research_data.py` | `scripts/` | Data pipeline utility. | Risky (Will need internal path updates) |
| `analyze_failures.py` | `scripts/` | Analysis utility. | Risky (Will need internal path updates) |
| `create_submission_zip.py` | `scripts/` | Kaggle packaging utility. | Risky (Likely assumes it is running from root to zip the `agent/` folder) |
| `prompt_patch.txt` | `agent/configs/` | The auto-generated patch file. | Risky (Referenced by `analyze_results.py` and `kaggle_notebook.py`) |

### Recommended Migration Strategy
When implementing these moves in a future phase:
1. Create the target directories (`_attic/noise/`, `research/raw/`, `data/raw/`, `scripts/`).
2. Move the **Safe** tier first.
3. Move the **Moderate** tier next, inspecting the Jupyter notebook for broken links.
4. For the **Risky** tier, use an IDE or `grep` to trace all references to `research_data.jsonl` and `prompt_patch.txt` before moving them, ensuring that scripts are updated to use absolute paths (via `pathlib`) or parameterized arguments.