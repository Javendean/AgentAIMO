# Verification Semantics Audit

This document audits the current mechanisms for verifying, checking, and validating the agent's mathematical reasoning and code execution.

---

## 1. Code Verification (Sandbox Execution)
**Files & Functions Involved:**
*   `agent/sandbox.py` -> `execute_code`, `extract_code_blocks`, `run_verification`
*   `agent/deep_researcher.py` -> `_generate_with_tir`, `_majority_vote`, `_research_problem_inner`

**Current Methodology:**
The `run_verification` function extracts all Python code blocks from a generation and executes them sequentially in a sandboxed subprocess. It returns a boolean (`all_passed`) which is strictly `True` if `returncode == 0` for all blocks.

**Critical Conflation Risk:**
The architecture explicitly conflates **"Execution Success"** with **"Mathematical Correctness."**
*   In `deep_researcher.py` (`_majority_vote`), an answer receives a $2\times$ weight in the consensus tally simply because its associated code executed without crashing: `weight = 2 if passed else 1`.
*   The `Attempt` dataclass stores this as `verification_passed: bool`, masking the distinction between a syntactically correct script and a mathematically sound proof.
*   If the model is asked to find the roots of a complex polynomial and writes ````python print("Hello") ````, the sandbox will mark `verification_passed = True`.

---

## 2. Natural Language Verification (NL Review)
**Files & Functions Involved:**
*   `agent/prompts.py` -> `NL_VERIFY_PROMPT`, `extract_nl_verdict`
*   `agent/deep_researcher.py` -> `_nl_verify`, `_research_problem_inner`

**Current Methodology:**
After a consensus answer is found via majority vote (or during self-correction), the agent optionally prompts the LLM to review the winning reasoning trace for "logical errors, unstated assumptions, and mathematical mistakes." The output is parsed for `VERDICT: CORRECT` or `VERDICT: ERROR`.

**Identified Flaws in Flow:**
*   **Rubber-Stamp Bias:** The same underlying model used to generate the flawed reasoning is immediately asked to critique it. This frequently leads to a rubber-stamp approval (confirmation bias).
*   **Pass-Through Failure:** If the NL verifier model hallucinates the output format and fails to include the exact `VERDICT:` strings, `extract_nl_verdict` silently defaults to `True, "No clear verdict (treating as pass)"`.
*   **Weak Influence:** If the NL Verifier flags an error on the consensus answer, the agent strips the consensus flag and forces a self-correction loop. However, because it uses the exact same `Attempt` logic, it is highly prone to spinning in circles without actually changing its mathematical approach.

---

## 3. Coarse Trace Schemas
**Files Involved:**
*   `agent/deep_researcher.py` -> `Attempt`, `ResearchTrace`

**Current Methodology:**
The `Attempt` dataclass tracks verification via a single boolean field: `verification_passed`. The `ResearchTrace` object tracks overall success via a single boolean field: `solved`.

**Identified Limitations:**
These schemas are far too coarse. They fail to capture *why* an attempt passed or failed, severely limiting the ability of downstream analysis pipelines (like `analysis/analyze_results.py`) to accurately identify and patch mathematical weaknesses.

---

## 4. Recommended Future Verification States
To resolve the conflation between execution success and mathematical correctness, future iterations should adopt a strongly typed distinction for verification outcomes.

**Proposed Enum/Types:**
1.  **`code_executed_successfully`**: The code block ran without throwing a Python exception (`returncode == 0`). No mathematical validity is implied.
2.  **`checker_assertion_passed`**: The code specifically contained `assert` statements or programmatic checks verifying an invariant, and those checks passed.
3.  **`independent_verifier_passed`**: A separate, strictly configured model (or specialized math engine like Lean/SymPy configured securely) verified the intermediate steps.
4.  **`formal_certificate_passed`**: The proof was validated by an automated theorem prover.
5.  **`nl_reviewer_flagged`**: The Natural Language Verifier explicitly identified a logical jump, unstated assumption, or calculation error.
6.  **`unresolved`**: The verification state is unknown or the checker timed out/crashed.