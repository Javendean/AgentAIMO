# Move Candidates Plan

This document outlines a conservative, risk-adjusted plan for restructuring the repository to separate active code from archived artifacts.

---

## 1. Proposed Minimal Target Structure

To isolate the active packages from the legacy noise, the following minimal top-level directories should be established:

```text
agent/          ← active code (unchanged)
analysis/       ← active code (unchanged)
tests/          ← active tests (unchanged)
docs/           ← audit documents (unchanged)
archive/        ← legacy artifacts and noise (new)
notebooks/      ← divergent or experimental notebooks (new)
```

---

## 2. Batch 1: Safe Operations (Zero Risk)

The following files are guaranteed safe to move. They are not imported by any Python file, are not referenced by any hardcoded `open()` paths, and moving them will break zero tests.

**Rollback Strategy:** `git revert HEAD` (or specifically `git checkout HEAD^1 -- <file>`)

| Current Path | Proposed Target | Justification |
| :--- | :--- | :--- |
| `BrowserChat.txt` | `archive/` | Unreferenced manual text transcript. |
| `GeminiChat.txt` | `archive/` | Unreferenced manual text transcript. |
| `c2_sorted_check.txt` | `archive/` | Unreferenced debug output dump. |
| `research_data2.jsonl.bak` | `archive/` | Unreferenced backup file. |
| `syntax_errors.txt` | `archive/` | Unreferenced text dump. |
| `analysis/analysis_report.txt`| `archive/` | Unreferenced output dump from `analyze_results.py`. |
| `extract_top_leaderboard.py` | `archive/` | Unreferenced standalone web scraper. |
| `extract_syntax_errors.py` | `archive/` | Unreferenced single-use regex script. |
| `fix_lines_16_91.py` | `archive/` | Unreferenced, highly specific string replacement hack. |

---

## 3. Batch 2: Moderate Risk (Notebooks & Research Scripts)

These files appear to be standalone, but moving them might break local developer workflows if they have terminal aliases pointing to the root directory.

**Rollback Strategy:** `git revert HEAD`

| Current Path | Proposed Target | Justification / Risk |
| :--- | :--- | :--- |
| `44-50-aimo3-skills-optional-luck-required.ipynb` | `notebooks/` | This massive notebook duplicates the core `agent/` architecture. It is safe to move structurally, but it contains unique Kaggle evaluation logic that must be extracted to the main `agent/` package before it is archived entirely. |
| `2511.01846v1_Part1.txt` | `archive/` | Unreferenced raw PDF text. |
| `pdf1.txt`, `pdf2.txt`, `pdf3.txt` | `archive/` | Unreferenced raw PDF texts. |
| `pdf_abstracts.txt` | `archive/` | Unreferenced text extracts. |
| `annotation_research_context.md` | `archive/` | Unreferenced conceptual markdown. |
| `mcts_rubric_analysis.md` | `archive/` | Unreferenced conceptual markdown. |
| `Refining LLM Rubric for Human Reasoning.md`| `archive/` | Unreferenced conceptual markdown. |
| `rubric.md` | `archive/` | Unreferenced grading markdown. |

---

## 4. Batch 3: Requires Refactoring Before Move (High Risk)

**DO NOT MOVE** these files in a simple `git mv` commit. They contain hardcoded relative paths or are implicitly relied upon by other scripts. Moving them will immediately break the scripts that depend on them.

| Current Path | Blocking Dependency | Required Action Before Move |
| :--- | :--- | :--- |
| `dpo_correction_dataset_v4.jsonl` | `create_preference_dataset.py` | Update `open('dpo_correction_dataset_v4.jsonl', 'w')` to accept an output path argument via `argparse`. |
| `research_data2.jsonl` | `verify_solved.py` | Update `open('research_data2.jsonl', 'r')` to use `argparse`. |
| `create_submission_zip.py` | Relies on being run from repo root | Update the script's `os.walk` to target `Path(__file__).parent.parent / "agent"` instead of assuming the current working directory. |
| `prompt_patch.txt` | `analysis/analyze_results.py` | Ensure the Kaggle notebook's expected upload path matches the new target location (e.g., `agent/configs/prompt_patch.txt`). |

---

## 5. Batch 4: Human Decision Required (Uncertain)

The purpose of these files is ambiguous or overlaps with existing core modules.

| Current Path | Question to Resolve |
| :--- | :--- |
| `test_safeguard.py` | Should this be formally integrated into `tests/test_agent.py`, or is it an obsolete scratchpad that should be archived? |
| `analyze_failures.py` | This script seems to overlap with `analysis/analyze_results.py`. Should they be merged into a single CLI tool? |
| `new_context_content.txt` | What pipeline generates or consumes this scratchpad text? |

---

**This plan requires human review before any operations are executed. No files will be moved by this task.**