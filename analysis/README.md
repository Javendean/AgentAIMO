# Analysis Module (`analysis/`)

This directory contains the local analysis pipeline for grading the output JSONL files produced by the DeepResearcher agent during a Kaggle H100 sprint.

## Components
*   `analyze_results.py`: Reads the agent's output (`research_data.jsonl`), computes aggregate statistics (solve rates, time spent, failure patterns), and auto-generates a "System Prompt Patch" designed to fix common mistakes in future runs.

## Known Blindspots & Bugs
1.  **Trusting the Agent's Self-Reporting**: The `solve_rate` metric blindly trusts the `solved=True` flag in the traces. If the agent successfully executed a bad piece of code and extracted a hallucinated answer, the script counts it as a "solve." It does not compare against ground-truth problem answers.
2.  **Rigid Patch Generation**: The auto-generated system prompt patches (`generate_patch`) rely on hardcoded thresholds (e.g., "if syntax errors > 2, tell the model to check parentheses"). This is superficial and misses deeper logical breakdown patterns.
3.  **Lack of Semantic Analysis**: The failure clustering only looks for specific keywords in standard error outputs (e.g., "NameError", "TIMEOUT"). It does not understand *why* the model failed mathematically.
