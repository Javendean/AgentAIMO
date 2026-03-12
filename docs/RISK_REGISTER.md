# Engineering Risk Register

This document tracks identified architectural, logical, and environmental risks within the DeepResearcher repository.

---

### RISK-01: Verification Semantics Conflation
*   **Severity:** High
*   **Affected Files:** `agent/sandbox.py`, `agent/deep_researcher.py`
*   **Why it Matters:** The agent fundamentally equates "code executed successfully" (`returncode == 0`) with "the mathematical logic is verified." The sandbox only catches Python exceptions, not flawed mathematical reasoning or irrelevant code.
*   **Likely Consequence:** The model will hallucinate an incorrect mathematical derivation, write trivial Python code (like `print(2+2)`), and the system will tag the attempt as `verification_passed=True`, leading to false positives and poisoning the majority vote.
*   **Recommended Next Action:** Decouple execution success from verification success. Introduce typed checker outputs (e.g., `code_executed_successfully` vs `checker_assertion_passed`).
*   **Phase:** Implementation-phase issue

---

### RISK-02: Answer Extraction Ambiguity and Pollution
*   **Severity:** High
*   **Affected Files:** `agent/prompts.py` (`extract_answer`), `agent/deep_researcher.py`
*   **Why it Matters:** The regex `r"\*\*ANSWER:\s*(.+?)\*\*"` is overly permissive. If the model appends prose (e.g., `**ANSWER: 42 because x is positive**`), the extracted string is polluted.
*   **Likely Consequence:** The majority voting mechanism (`Counter`) relies on exact string matches. Polluted answers will fracture the vote tally, causing the agent to falsely believe no consensus was reached, triggering unnecessary and expensive fallback loops.
*   **Recommended Next Action:** Implement a robust answer canonicalization pipeline before tallying votes. Strip trailing punctuation, normalize LaTeX strings, and handle equivalent mathematical forms (e.g., `1/2` vs `0.5`).
*   **Phase:** Implementation-phase issue

---

### RISK-03: Notebook / Mainline Divergence
*   **Severity:** Medium
*   **Affected Files:** `notebook/kaggle_notebook.py`, `44-50-aimo3-skills-optional-luck-required.ipynb`, `agent/deep_researcher.py`
*   **Why it Matters:** The `kaggle_notebook.py` script acts as the true `main.py` for production runs, but it lives outside the core package and contains hardcoded, critical logic (the "Canary Test") that determines whether the 120B model or the 72B model is used. The root notebook (`44-50...ipynb`) is NOT archival noise—it introduces massive package-vs-notebook divergence by housing an entirely parallel `AIMO3Solver` loop.
*   **Likely Consequence:** Changes to the core agent package may not be reflected or tested properly against the Kaggle execution harness, and future developers may mistakenly rely on or edit the completely separate solver loop present in the notebook.
*   **Recommended Next Action:** Treat the root-level notebook divergence explicitly. Standardize the execution loop into `agent/` and unify the execution path to remove the two competing implementation workflows. Additionally, abstract the fail-fast canary logic into a testable format.
*   **Phase:** Implementation-phase issue

---

### RISK-04: Weak Sandbox Security (Local-Path / Portability Risks)
*   **Severity:** Medium
*   **Affected Files:** `agent/sandbox.py`
*   **Why it Matters:** The sandbox relies on simple Python-level string matching and module blocklisting (via `builtins.__import__`). This provides weak, Python-level isolation rather than an actual security boundary.
*   **Likely Consequence:** A sophisticated LLM could bypass the blocklist using standard Python reflection (e.g., navigating `__subclasses__`) to break out of the sandbox, execute arbitrary host commands, or access the file system.
*   **Recommended Next Action:** If full isolation is required, move from a Python-level blocklist to a robust OS-level containerization solution (e.g., Docker, gVisor) for executing untrusted code, or utilize a restricted AST execution engine.
*   **Phase:** Implementation-phase issue

---

### RISK-05: Brittle Regex Parsing
*   **Severity:** High
*   **Affected Files:** `agent/sandbox.py` (`extract_code_blocks`)
*   **Why it Matters:** The regex `r"```(?:python|py)\s*\n(.*?)```"` stops at the first closing backticks. If the LLM generates nested backticks (despite instructions not to), the code block is prematurely truncated.
*   **Likely Consequence:** Truncated code blocks will inevitably fail with a `SyntaxError` in the sandbox, forcing the agent into expensive self-correction loops for a formatting error rather than a logical error.
*   **Recommended Next Action:** Replace simple regex matching with a robust markdown parser capable of handling nested blocks and edge cases.
*   **Phase:** Implementation-phase issue

---

### RISK-06: Noisy Artifact / Dataset Confusion
*   **Severity:** Low
*   **Affected Files:** Root directory (`*.jsonl`, `*.txt`, `*.py`)
*   **Why it Matters:** The root directory is heavily polluted with generated datasets, DPO artifacts, raw text dumps, and experimental scripts that have no clear organization.
*   **Likely Consequence:** New developers (or AI agents) will struggle to distinguish between active production code, legacy experimental scripts, and critical training artifacts. This increases the risk of accidentally deleting or modifying important data.
*   **Recommended Next Action:** Execute the manifest defined in `docs/MOVE_CANDIDATES.md` to cleanly separate source code from data and archival materials.
*   **Phase:** Implementation-phase issue

---

### RISK-07: Overfitting / Reward-Hacking from Future Schema Mining
*   **Severity:** Medium
*   **Affected Files:** `analysis/analyze_results.py`
*   **Why it Matters:** The local analysis pipeline currently generates "System Prompt Patches" based on hardcoded heuristics (e.g., counting `SyntaxError` strings in the sandbox output).
*   **Likely Consequence:** If this feedback loop is automated further without semantic understanding, the model will likely learn to "hack" the metric—for instance, by outputting code that runs perfectly but does no math, solely to avoid the `SyntaxError` feedback penalty in the system prompt.
*   **Recommended Next Action:** Enhance the analysis pipeline to evaluate the semantic correctness of the reasoning trace, not just the mechanical execution state of the sandbox.
*   **Phase:** Implementation-phase issue

---

### RISK-08: Weak Regression Coverage
*   **Severity:** High
*   **Affected Files:** `tests/test_agent.py`, `tests/test_hallucination_fix.py`
*   **Why it Matters:** The test suite is extremely sparse. It only performs shallow dry runs without mocking LLM responses or verifying the actual recursive logic of the self-correction loops.
*   **Likely Consequence:** Refactoring the core logic (e.g., modifying `_research_problem_inner`) carries a very high risk of introducing silent regressions, as the current tests only verify basic prompt string formatting and sandbox blocklists.
*   **Recommended Next Action:** Implement robust unit tests mocking `vllm` to ensure majority voting, GenSelect, and self-correction loops route correctly under different mocked LLM behaviors.
*   **Phase:** Implementation-phase issue