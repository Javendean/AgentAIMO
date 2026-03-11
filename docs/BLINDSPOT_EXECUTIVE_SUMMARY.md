# Blindspots Executive Summary

This repository implements the DeepResearcher v2 agent, an H100-optimized system for solving math problems via majority voting and Tool-Integrated Reasoning (TIR). While the code demonstrates advanced pipeline logic (wave-based voting, GenSelect fallbacks, canary testing), our docs-only audit has identified severe structural and semantic blindspots that jeopardize its reliability, extensibility, and correctness.

## Most Dangerous Blindspots
1. **Conflation of Execution Success with Truth (BS-VER-001):** The sandbox marks any Python block that runs without a crash as `verification_passed = True`. The majority voter then gives these answers a $2\times$ weight. The system actively rewards syntactically correct hallucinations.
2. **Brittle, Raw String Answer Extraction (BS-ANS-001):** Answers are extracted using permissive regex and matched via exact string comparison without normalization. "42", "42.0", and "\frac{84}{2}" fracture the vote, improperly triggering GenSelect fallbacks.
3. **Architectural Divergence (Notebook vs Package) (BS-ARC-001):** The Kaggle notebook (`44-50...ipynb`) implements a complete, parallel `AIMO3Solver` loop that bypasses `agent/deep_researcher.py` entirely, while `notebook/kaggle_notebook.py` imports the package logic but wraps it in fail-fast and hardware-specific constraints.
4. **Proxy Metrics Optimized over Ground Truth (BS-EVA-001):** `analysis/analyze_results.py` generates auto-patches based entirely on self-reported `solved` booleans and trace metadata, lacking integration with actual AIMO ground truth.
5. **Confirmation Bias in NL Verifier (BS-VER-002):** The agent asks the same LLM to critique its own flawed reasoning, leading to rubber-stamp approvals, or forces self-correction loops based on string-matching heuristics.

## Most Likely Misleading Impressions
- **"Verification":** Reading the logs or dataclasses (`verification_passed: bool`) suggests the math was formally checked. It was merely executed.
- **"Sandbox Safety":** The Python sandbox heavily restricts imports and OS calls via a preamble but does not implement a true OS-level jailbreak prevention mechanism.
- **"Single Source of Truth":** The existence of two fully distinct solvers in the root implies an unresolved tension between local development and Kaggle competition constraints.

## Trust Map
**Trust the Docs On:**
- Python execution mechanics and extraction bounds.
- Token and time budget constraints within the `deep_researcher.py` loop.
- The structure of the generated `.jsonl` artifacts.

**Do Not Trust the Docs On:**
- The definition of "solved" or "correct".
- The claim that the agent "verifies" its logic.
- The assumption that `agent/` is the sole entrypoint for competition runs.

## Top 5 Implementation Prerequisites (Before Expanding Architecture)
1. **Implement Answer Normalization:** Build a canonicalization layer (whitespace, basic math equiv, LaTeX stripping) *before* `collections.Counter` tallies votes.
2. **Disentangle Execution from Correctness:** Refactor the `Attempt` dataclass to separate `code_executed_successfully` from `mathematically_verified`.
3. **Consolidate Solvers:** Deprecate or merge the duplicate solver logic found in the root `.ipynb` notebook into the core package.
4. **Ground Truth Integration:** Modify the analysis pipeline to score results against actual mathematical truth datasets rather than self-reported success.
5. **Strengthen Sandbox:** Document its limitations and implement stricter AST-level or unprivileged-user isolation before introducing generalized tool use.
