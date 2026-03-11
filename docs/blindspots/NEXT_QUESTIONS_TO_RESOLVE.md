# Next Questions to Resolve

This document turns the identified blindspots into a practical investigation checklist. It outlines the immediate steps to resolve the most critical ambiguities and technical debt in the current codebase before expanding the architecture.

## 1. Top Immediate Questions to Answer Before Implementation

*   **Q1: How do we decouple execution success from mathematical truth?** (Resolves BS-VER-001)
    *   *Why:* The agent is currently rewarding itself for executing trivial Python code (like `print("Hello")`), inflating its self-reported success rate and creating synthetic consensus.
    *   *Next Step:* Refactor the `Attempt` dataclass to use an enum (e.g., `code_executed_successfully`, `mathematically_verified`) instead of a single `verification_passed` boolean. Update the voting weights to only apply to mathematical verification.
*   **Q2: What is the correct canonicalization strategy for extracted answers?** (Resolves BS-ANS-001)
    *   *Why:* The agent currently fractures votes by treating `"42"`, `"42.0"`, and `"\frac{84}{2}"` as completely separate answers, artificially lowering its confidence and triggering unnecessary GenSelect fallbacks.
    *   *Next Step:* Implement a comprehensive normalization function in `agent/prompts.py` that strips whitespace, handles LaTeX, and evaluates basic mathematical equivalence before passing the answers to `collections.Counter`.
*   **Q3: Which solver loop is the actual canonical source of truth?** (Resolves BS-ARC-001)
    *   *Why:* The root directory contains a complete, independent `AIMO3Solver` implementation (`44-50-aimo3-skills-optional-luck-required.ipynb`), while the `notebook/kaggle_notebook.py` uses the package code (`agent/deep_researcher.py`).
    *   *Next Step:* Ask the author or examine Kaggle submission logs to determine which file is actively deployed. Delete or clearly archive the legacy implementation.

## 2. Top Questions to Answer Before Moving Files

*   **Q4: Do downstream scripts depend on the hardcoded paths in the root directory?** (Resolves BS-DAT-001)
    *   *Why:* Before cleaning up the root directory (moving `.jsonl` files to `data/` and scripts to `scripts/`), we must ensure that we don't break data pipelines.
    *   *Next Step:* Use `grep` to trace all references to `research_data.jsonl`, `dpo_correction_dataset_v4.jsonl`, and other artifacts. Refactor scripts like `create_preference_dataset.py` to use parameterized inputs.
*   **Q5: Is the prompt patch pipeline robust enough for path changes?** (Resolves BS-UNK-008)
    *   *Why:* `analysis/analyze_results.py` generates `prompt_patch.txt`, which is then read by `notebook/kaggle_notebook.py`.
    *   *Next Step:* Ensure that the generation and consumption of this patch file use absolute or configurable paths rather than relying on current working directory assumptions.

## 3. Top Questions to Answer Before Adding Specialists (e.g., DeepSeek-R1, O1)

*   **Q6: Can we eliminate the "confirmation bias" in the Natural Language Verifier?** (Resolves BS-VER-002)
    *   *Why:* Currently, the same model that generates an answer evaluates its own reasoning, leading to rubber-stamp approvals.
    *   *Next Step:* Implement routing logic to send NL Verification tasks specifically to a stronger, specialized reasoning model (like O1 or R1) rather than the default generator model.
*   **Q7: How do we fix the GenSelect truncation penalty?** (Resolves BS-ANS-003)
    *   *Why:* GenSelect arbitrarily truncates reasoning traces to the last 2000 characters before asking an LLM to judge them.
    *   *Next Step:* Implement an intelligent summarization model or preserve both the premise and the conclusion rather than blindly slicing the string.

## 4. Top Questions to Answer Before Adding DSPy/OpenEvolve/LLM Judges

*   **Q8: How do we establish a ground-truth evaluation loop?** (Resolves BS-EVA-002)
    *   *Why:* `analyze_results.py` generates auto-patches based entirely on self-reported `solved` flags. Any automated search algorithm will quickly overfit to this proxy metric (Reward Hacking).
    *   *Next Step:* Integrate a known AIMO dataset with answers and build a local pytest suite or LightEval harness that compares the agent's normalized output directly to the ground truth.
*   **Q9: How do we prevent pathological prompt injections?** (Resolves BS-RWD-002)
    *   *Why:* The auto-patching mechanism appends LLM-generated text directly to the `SYSTEM_PROMPT`.
    *   *Next Step:* Implement human-in-the-loop validation or a strict validation schema for generated patches before they are committed to the execution environment.