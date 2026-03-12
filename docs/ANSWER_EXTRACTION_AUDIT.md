# Answer Extraction Audit

This document audits the current mechanisms for extracting, normalizing, parsing, and selecting final mathematical answers from the agent's generated reasoning traces.

## 1. Raw Answer Extraction
**Files & Functions Involved:**
*   `agent/prompts.py` -> `extract_answer(solution_text: str)`
*   `agent/deep_researcher.py` -> `_majority_vote` (calls `extract_answer` on each trace)
*   `agent/deep_researcher.py` -> `_research_problem_inner` (calls `extract_answer` during Self-Correction)

**Current Methodology:**
The `extract_answer` function attempts to parse the final answer using regular expressions.
1.  **Strict Pattern:** `r"\*\*ANSWER:\s*(.+?)\*\*"` (case-insensitive)
2.  **Fallback Pattern:** `r"ANSWER:\s*(.+?)(?:\n|$)"` (case-insensitive)

**Identified Contamination & Ambiguity Risks:**
*   **Prose Attachment (Pollution):** The capture group `(.+?)` is non-greedy but bounded only by the closing `**` or newline. If the LLM outputs `**ANSWER: 42 because x > 0**`, the entire string `"42 because x > 0"` is extracted.
*   **Missing Answers:** If the model outputs `The final answer is: 42`, the regex fails entirely, returning `None`. The agent assumes the attempt failed, triggering expensive fallback loops even if the math was correct.
*   **Multiple Answers:** `re.search` only captures the *first* instance. If the model hallucinates an intermediate summary like `**ANSWER: x=2**` and later concludes `**ANSWER: 42**`, the agent will extract `x=2`.

---

## 2. Answer Normalization
**Current Methodology:**
*   **None.** The current implementation performs zero canonicalization or normalization on the extracted strings.

**Identified Ambiguity Risks:**
*   **Formatting Differences:** `"42"`, `"42.0"`, `"42 "`, and `"\frac{84}{2}"` are treated as distinct.
*   **LaTeX Variability:** `"\\pi"`, `"\pi"`, and `"pi"` are treated as distinct.

**Recommendation:** A canonicalization layer must be built to strip whitespace, handle basic mathematical equivalencies, and standardize LaTeX before tallying votes.

---

## 3. Canonical Answer Parsing
**Current Methodology:**
*   **None.** The agent relies entirely on raw string hashing via Python's `collections.Counter`. It does not attempt to parse the string into a numerical type (e.g., `int`, `float`, or `sympy.Expr`) to verify equivalency.

---

## 4. Final Answer Selection / Voting
**Files & Functions Involved:**
*   `agent/deep_researcher.py` -> `_check_early_consensus`
*   `agent/deep_researcher.py` -> `_majority_vote`
*   `agent/deep_researcher.py` -> `_genselect`

**Current Methodology:**
The repository currently implements **multiple** answer paths.

**Path A: Majority Voting (String Consensus)**
1.  **Generation:** The agent generates N samples.
2.  **Tally:** It counts the exact occurrences of each raw extracted string. It applies a 2x weight if the trace's code block executed without an exception in the sandbox.
3.  **Early Stopping:** If a dynamic threshold (e.g., 75% agreement with 4 samples) is met, it returns the top string as consensus.
4.  **Final Vote:** Otherwise, it requires $\ge 30\%$ weighted agreement to declare a consensus.

**Path B: GenSelect (Comparative Evaluation)**
1.  **Trigger:** If the majority vote results in a weak consensus ($< 40\%$ agreement), the agent routes to GenSelect.
2.  **Summarization:** It truncates the reasoning trace of every valid attempt to 2000 characters.
3.  **Evaluation:** It feeds these truncated summaries back into the LLM, prompting it to select the "best" reasoning chain by outputting a number (e.g., `BEST: 2`).
4.  **Selection:** It extracts the answer from the LLM's chosen solution.

**Identified Vulnerabilities in Selection:**
*   **Vote Fracturing:** Because there is no canonical normalization (Section 2), the majority vote is highly susceptible to vote fracturing, which falsely triggers Path B.
*   **GenSelect Blindness:** Truncating complex mathematical proofs to 2000 characters forces the GenSelect evaluator to make blind choices based on incomplete information, significantly raising the hallucination risk.