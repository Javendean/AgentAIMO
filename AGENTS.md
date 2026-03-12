# Agents & AI Contributors

This file provides crucial context for any LLM agent or autonomous coding system operating in this repository.

## 1. Do Not Assume Code Is Truth

The most critical insight about this repository is the **Verification Conflation**.
*   **Fact:** The `verification_passed` boolean in `agent/deep_researcher.py` and `agent/sandbox.py` *only* means a Python subprocess ran without crashing.
*   **Rule:** Never treat "code executed successfully" as equivalent to "the math is correct." Do not build new logic that blindly maximizes `verification_passed` without adding true mathematical checks, or you will cause syntactic overfitting.

## 2. Architecture Divergence

*   **Fact:** There are two distinct solver loops in this repository.
    1.  `agent/deep_researcher.py`: The core package module.
    2.  `44-50-aimo3-skills-optional-luck-required.ipynb`: A root-level notebook containing an entirely parallel, active implementation of the `AIMO3Solver` loop with its own entropy and answer selection mechanics.
*   **Rule:** When asked to implement a feature or fix a bug, you must explicitly clarify with the user *which* solver path you are modifying. Do not assume `agent/` is the sole entry point.

## 3. Answer Canonicalization

*   **Fact:** `agent/prompts.py` uses simple regex (e.g., `\*\*ANSWER:(.+)\*\*`) and exact string matching (`collections.Counter`).
*   **Rule:** "42" and "42.0" will split the vote. If you are touching the vote selection or extraction pipelines, you must account for lack of whitespace/LaTeX normalization.

## 4. Documentation First

This repository is heavily documented with "Blindspot Illuminations."
*   **Rule:** Before modifying the core loops or the evaluation metrics in `analysis/analyze_results.py`, read the corresponding markdown files in `docs/blindspots/` and `docs/RISK_REGISTER.md` to understand the known technical debt, hidden dependencies, and proxy metric vulnerabilities you might accidentally trigger.

## 5. Artifacts and Noise

*   **Fact:** The root directory is heavily polluted with `.jsonl` dumps, chat transcripts, and one-off Python scripts (`fix_lines_16_91.py`, etc.).
*   **Rule:** Do not assume a script in the root directory is actively used or well-tested. Consult `docs/LEGACY_ARTIFACT_INVENTORY.md` before moving or deleting data files, as downstream scripts (like `create_preference_dataset.py`) may rely on hardcoded paths.

## 6. General Coding Conventions

*   Use Google-style docstrings for Python source code.
*   Do not perform broad directory restructuring without explicit planning and permission.
*   If you encounter an ambiguity in evaluation metrics (e.g., "solved" vs "ground truth"), clearly state the limitation in your response.
