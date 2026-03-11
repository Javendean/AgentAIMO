# Evaluation and Metrics Blindspots

This document exposes metrics without ground truth, trace fields that may be trusted too much, weak regression coverage, and leakage risks in evaluation.

- Blindspot ID: BS-EVA-001
- Title: Proxy Metrics Drive Auto-Patching
- Category: Evaluation
- Severity: high
- Confidence: strong inference
- Status: strong inference
- Why this is a blindspot: `analysis/analyze_results.py` generates auto-patches (`prompt_patch.txt`) based entirely on self-reported `solved` booleans and trace metadata.
- Evidence:
  - `analysis/analyze_results.py:analyze`: `solved = sum(1 for t in traces if t.get("solved", False))`
- What could be misleading: A user reading the analysis output (e.g., "50% success rate") assumes the generated system prompt patches are optimizing for true mathematical accuracy against a ground truth dataset like AIMO.
- Potential consequence: Because the agent conflates "code execution success" with "mathematical correctness" (BS-VER-001) and forces consensus string matching without normalization (BS-ANS-001), the auto-patcher is highly vulnerable to optimizing for the wrong thing—syntactic correctness or verbose code execution over actual math solving.
- How to verify or falsify it: Cross-reference the `research_data.jsonl` output with the actual AIMO evaluation dataset and calculate the discrepancy between the self-reported `solved` boolean and the actual success rate.
- Recommended next step: Integrate an independent ground-truth evaluation step into `analyze_results.py` before generating `prompt_patch.txt`.
- Blocks future work? yes

- Blindspot ID: BS-EVA-002
- Title: Missing Ground Truth Integration
- Category: Evaluation
- Severity: high
- Confidence: fact
- Status: fact
- Why this is a blindspot: There is no independent benchmark discipline or ground-truth verification pipeline within the repository.
- Evidence:
  - `analysis/analyze_results.py` only counts `solved` directly from the `research_data.jsonl` trace output.
  - The Kaggle notebook environment uses `aimo_3_inference_server` but the local loop has no equivalent accuracy check.
- What could be misleading: By optimizing against proxy metrics, the system might appear to improve over iterations while actually degenerating in true problem-solving capabilities (Reward Hacking).
- Potential consequence: If the team continues running the agent based on self-reported metrics, it will inevitably overfit to superficial trace features.
- How to verify or falsify it: Attempt to run a local evaluation suite that automatically checks the agent's final answers against known solutions. No such suite exists.
- Recommended next step: Implement a rigorous evaluation framework (like LightEval or a custom pytest suite) that compares the final answer against ground truth.
- Blocks future work? no