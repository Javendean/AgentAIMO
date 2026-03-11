# Fact vs Inference

This document delineates the epistemological boundaries of our blindspot analysis. It explicitly separates what we know to be true from the source code versus what we suspect based on architectural patterns or legacy artifacts.

## 1. Code-Backed Facts
These claims are proven by direct inspection of the current source code (`agent/`, `tests/`, `analysis/`, `notebook/`).

*   **BS-VER-001 (Execution Conflated with Correctness):** `agent/sandbox.py:run_verification` returns a single boolean (`all_passed`) which is strictly `True` if `returncode == 0`. `deep_researcher.py` uses this to double the weight of a generated answer.
*   **BS-ANS-001 (Raw String Vote Fracturing):** `agent/prompts.py:extract_answer` uses `re.search` to pull the raw string from the LLM output. There is no normalization (e.g., stripping whitespace or standardizing LaTeX) before `collections.Counter` tallies votes in `deep_researcher.py`.
*   **BS-ARC-001 (Divergent Notebook Solver Loop):** The root file `44-50-aimo3-skills-optional-luck-required.ipynb` contains a complete `AIMO3Solver` class that duplicates the logic of `agent/deep_researcher.py`, including its own API calls, voting mechanism, and entropy calculation.
*   **BS-SEC-001 (Weak Python Sandbox Isolation):** `agent/sandbox.py` uses a Python `SAFETY_PREAMBLE` to overwrite built-ins and block modules like `os` and `subprocess`, but it runs in the same user space as the parent process.

## 2. Strong Inferences
These claims are based on strong architectural patterns, consistent naming conventions, and the interaction between multiple files.

*   **BS-EVA-001 (Proxy Metrics Drive Auto-Patching):** `analysis/analyze_results.py` generates `prompt_patch.txt` by analyzing the `solved` boolean in `research_data.jsonl`. We strongly infer that this `solved` field is self-reported by the agent's logic (since it is generated during the run), rather than verified against an external ground-truth dataset like AIMO.
*   **BS-ARC-002 (Unclear Package Entrypoint):** The Kaggle notebook (`notebook/kaggle_notebook.py`) imports `DeepResearcher` and sets up offline wheels. We strongly infer this is the intended deployment script, while the root `44-50*.ipynb` notebook is an older, divergent experiment.
*   **BS-VER-002 (Confirmation Bias in NL Verifier):** The agent prompts the LLM to critique its own reasoning traces (`agent/deep_researcher.py`). We strongly infer that an LLM asked to evaluate text it just generated is highly prone to rubber-stamping it as "CORRECT".

## 3. Weak Suspicions
These claims arise from the presence of unstructured or legacy artifacts that cannot be definitively traced to a current pipeline step.

*   **BS-DAT-001 (Artifact Provenance Ambiguity):** Files like `research_data2.jsonl`, `dpo_correction_dataset_v4.jsonl`, and various `pdf_abstracts.txt` exist in the root directory. We suspect these are outputs from older or parallel research efforts, but we cannot confirm whether they are still actively consumed by downstream scripts like `create_preference_dataset.py`.
*   **BS-UNK-006 (What is `fix_lines_16_91.py` doing?):** The script name implies a highly specific, rigid patch. We suspect it is a fragile, one-off utility that could break if the underlying files are modified.

## 4. Unresolved Unknowns
These are critical questions that cannot be answered without dynamic execution, external context, or human clarification.

*   **BS-UNK-001 (Does Kaggle Enforce Offline Wheels?):** The deployment script `notebook/kaggle_notebook.py` uninstalls packages and reinstalls vLLM from `aimo-vllm-wheels`. We do not know if this is strictly required for the current Kaggle environment or if it is legacy logic.
*   **BS-UNK-004 (Is the Fail-Fast Swap to 72B tested?):** `notebook/kaggle_notebook.py` includes logic to delete the 120B model and swap to a 72B model if the canary test fails. We do not know if this complex state-transition has ever been robustly tested.

## Corrections to Earlier Documentation
*   The `agent/sandbox.py` docstring claims to prevent "memory bombs that could OOM the Kaggle container". Based on the implementation, the sandbox only enforces time limits (`subprocess.run(timeout=...)`); it does not enforce strict memory cgroups. This claim in the current docs is likely overstated.
