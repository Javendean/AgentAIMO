# Notebook Module (`notebook/`)

This directory contains the scripts meant to be copy-pasted or uploaded to Kaggle to execute the actual AIMO3 research sprints.

## Components
*   `kaggle_notebook.py`: The main execution script. It uninstalls conflicting packages, installs `vLLM` offline, runs a preliminary "Canary Test," and then kicks off the `DeepResearcher` over the problem set.

## Known Blindspots & Bugs
1.  **Canary Test Brittleness**: The `run_canary_test` function is dangerously rigid. It expects the model to output exactly `\\boxed{809}`. If the model outputs `ANSWER: 809`, the canary fails and forces the system onto a backup 72B model, wasting the primary 120B model entirely.
2.  **Canary Test Data Leakage**: Because the canary is a static AIME 2024 problem, a model trained heavily on contest math might output the right answer from memory instantly, bypassing the logic check the canary is trying to enforce.
3.  **Environment Assumption**: The offline pip installation steps assume a very specific Kaggle container environment and pre-uploaded `vllm` wheels. Any upstream Kaggle image changes can silently break this script.
