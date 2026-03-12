# Engineering Risk Register

This document tracks identified architectural, logical, and environmental risks within the DeepResearcher codebase.

---

### RISK-01: Verification Semantics Conflation
*   **Severity:** High
*   **Affected Files:** `agent/sandbox.py` (`run_verification`), `agent/deep_researcher.py`
*   **Why it Matters:** The system equates "Python code executed without throwing an exception" (`returncode == 0`) with "mathematical logic verified."
*   **Likely Consequence:** If the model hallucinates an incorrect mathematical derivation but writes trivial Python code (like `print(2+2)`), the system tags the attempt as `verification_passed=True`. This poisons the majority vote tally by artificially boosting the weight of bad reasoning.
*   **Recommended Next Action:** Decouple execution success from verification success by introducing typed checker outputs (e.g., `code_executed_successfully` vs `checker_assertion_passed`).
*   **Phase:** Implementation-phase issue

---

### RISK-02: Answer Extraction Ambiguity and Pollution
*   **Severity:** High
*   **Affected Files:** `agent/prompts.py` (`extract_answer`), `agent/deep_researcher.py`
*   **Why it Matters:** The regex `r"\*\*ANSWER:\s*(.+?)\*\*"` is extremely permissive. If the model outputs `**ANSWER: 42 because x > 0**`, the entire phrase is extracted. Furthermore, no normalization is applied (so `"42"` and `"42.0"` are tracked as different answers).
*   **Likely Consequence:** The majority voting mechanism relies on exact string matches. Polluted or un-normalized answers will fracture the vote tally, causing the agent to falsely believe no consensus was reached, triggering expensive and unnecessary fallback loops.
*   **Recommended Next Action:** Implement a robust answer canonicalization pipeline before tallying votes to strip punctuation, handle LaTeX equivalents, and reject trailing prose.
*   **Phase:** Implementation-phase issue

---

### RISK-03: Notebook / Mainline Divergence
*   **Severity:** Medium
*   **Affected Files:** `notebook/kaggle_notebook.py`, `agent/deep_researcher.py`
*   **Why it Matters:** The `kaggle_notebook.py` script acts as the true `main.py` for production runs. It contains hardcoded, critical branching logic (the "Canary Test") to determine whether to use the primary 120B model or fall back to a 72B model.
*   **Likely Consequence:** Because this logic lives outside the testable `agent/` package, changes to the core agent may not be reflected in Kaggle runs, and the Canary Test cannot be covered by standard continuous integration tests.
*   **Recommended Next Action:** Refactor the Kaggle notebook logic into a standardized entry point within the `agent` package, isolating environment setup from the core reasoning flow.
*   **Phase:** Implementation-phase issue

---

### RISK-04: Weak Sandbox Security (Local-Path/Portability Risks)
*   **Severity:** Medium
*   **Affected Files:** `agent/sandbox.py`
*   **Why it Matters:** The sandbox relies on basic Python-level module blocklisting via `builtins.__import__`. To support math libraries like `sympy`, it leaves modules like `ctypes`, `threading`, and `gc` completely unblocked.
*   **Likely Consequence:** An adversarial or highly hallucinating LLM could use C-extensions or reflection to bypass the sandbox, potentially crashing the Kaggle container or accessing local files.
*   **Recommended Next Action:** Move from a Python-level blocklist to robust OS-level containerization (e.g., Docker, gVisor) for executing untrusted code.
*   **Phase:** Implementation-phase issue

---

### RISK-05: Weak Regression Coverage
*   **Severity:** High
*   **Affected Files:** `tests/test_agent.py`, `tests/test_hallucination_fix.py`
*   **Why it Matters:** The test suite is extremely sparse. It only performs shallow "dry runs" without mocking varying LLM responses.
*   **Likely Consequence:** The recursive logic of the self-correction loops, GenSelect pathways, and threshold consensus checks are virtually untested. Refactoring `deep_researcher.py` carries a high risk of introducing silent logical regressions.
*   **Recommended Next Action:** Implement unit tests that mock `vLLM` outputs to ensure the orchestration loops route correctly under simulated failures and edge cases.
*   **Phase:** Implementation-phase issue

---

### RISK-06: Noisy Artifact / Dataset Confusion
*   **Severity:** Low
*   **Affected Files:** Root directory (`*.jsonl`, `*.txt`, `*.py`)
*   **Why it Matters:** The root directory is heavily polluted with a mix of production code, legacy experimental scripts, generated DPO datasets, and raw text dumps.
*   **Likely Consequence:** High cognitive overhead for developers. Increased risk of accidentally modifying or deleting critical training datasets or configuration files (like `prompt_patch.txt`).
*   **Recommended Next Action:** Execute a structural cleanup based on the `docs/MOVE_CANDIDATES.md` manifest to cleanly separate source code from data.
*   **Phase:** Implementation-phase issue

---

### RISK-07: Overfitting / Reward-Hacking from Future Schema Mining
*   **Severity:** Medium
*   **Affected Files:** `analysis/analyze_results.py`
*   **Why it Matters:** The local analysis pipeline generates "System Prompt Patches" based on hardcoded mechanical heuristics (e.g., if `SyntaxError` count > 2, add a rule to check parentheses).
*   **Likely Consequence:** If this feedback loop is automated, the model may learn to "hack" the mechanical metrics—for instance, by outputting valid Python code that does absolutely no math, solely to avoid the `SyntaxError` feedback penalty.
*   **Recommended Next Action:** Enhance the analysis pipeline to evaluate the semantic correctness of the reasoning trace, rather than just parsing Python error logs.
*   **Phase:** Implementation-phase issue