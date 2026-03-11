# Future Reward Hacking and Overfitting

This document focuses on future risks if we add schema mining, DSPy, OpenEvolve, LLM judges, or self-improvement loops.

- Blindspot ID: BS-RWD-001
- Title: Syntactic Overfitting
- Category: Future Reward Hacking and Overfitting
- Severity: high
- Confidence: strong inference
- Status: strong inference
- Why this is a blindspot: The agent evaluates generated answers using a binary proxy metric: `verification_passed`. This boolean is `True` if a code block runs without crashing.
- Evidence:
  - `agent/sandbox.py:run_verification` returns a single boolean.
  - `agent/deep_researcher.py:_majority_vote`: `weight = 2 if passed else 1`
- What could be misleading: A future optimization framework (e.g., DSPy or OpenEvolve) designed to maximize "solved" or "verified" states will rapidly learn to write syntactically valid but mathematically meaningless code to artificially double its vote weight and increase its perceived success rate.
- Potential consequence: The agent will degrade into a code-generator that solves nothing but passes all internal metrics. Optimization loops will "succeed" by hacking the proxy metric rather than actually improving logical reasoning.
- How to verify or falsify it: Implement a naive reinforcement learning loop that rewards the agent for maximizing `verification_passed` and observe whether it starts outputting `print("verified")` instead of proving theorems.
- Recommended next step: Separate "execution success" from "mathematical correctness" using strong assertions or independent mathematical verification before introducing reward optimization.
- Blocks future work? yes

- Blindspot ID: BS-RWD-002
- Title: Patch Injection Vulnerability
- Category: Future Reward Hacking and Overfitting
- Severity: medium
- Confidence: strong inference
- Status: strong inference
- Why this is a blindspot: The analysis pipeline `analyze_results.py` generates auto-patches (`prompt_patch.txt`) that are injected directly into the `SYSTEM_PROMPT`.
- Evidence:
  - `notebook/kaggle_notebook.py` loads `prompt_patch.txt` and appends it.
  - `analysis/analyze_results.py` automatically generates the text.
- What could be misleading: By appending strings dynamically without constraints, the prompt could be systematically corrupted or driven into pathological modes. If the analysis script misinterprets failure modes (due to coarse schemas or lack of ground truth), it will write bad patches.
- Potential consequence: An LLM judge reviewing self-reported `solved` flags will iteratively corrupt the prompt patch with increasingly bizarre instructions to chase local maxima, leading to brittle system behavior that fails catastrophic edge cases on unseen AIMO datasets.
- How to verify or falsify it: Run `analyze_results.py` on a dataset where the model hallucinated syntax errors and observe whether the generated patch is overly specific or nonsensical.
- Recommended next step: Require human-in-the-loop approval for all `prompt_patch.txt` generation before injecting it into the Kaggle environment, or strictly validate the generated text against a held-out test set.
- Blocks future work? yes