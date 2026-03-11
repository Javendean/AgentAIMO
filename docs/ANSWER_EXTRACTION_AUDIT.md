# Answer Extraction Audit

This document audits the current mechanisms for extracting, normalizing, parsing, and selecting final mathematical answers from the agent's generated reasoning traces.

## 1. Raw Answer Extraction
**Files & Functions Involved:**
*   `agent/prompts.py` -> `extract_answer(solution_text: str)`
*   `agent/deep_researcher.py` -> `_majority_vote` (calls `extract_answer` on each trace)
*   `agent/deep_researcher.py` -> `_research_problem_inner` (calls `extract_answer` on Self-Correction attempts)

**Current Methodology:**
The `extract_answer` function attempts to parse the final answer using two permissive regular expressions.
1.  **Strict Pattern:** `r"\*\*ANSWER:\s*(.+?)\*\*"` (case-insensitive)
2.  **Fallback Pattern:** `r"ANSWER:\s*(.+?)(?:\n|$)"` (case-insensitive)

**Identified Contamination & Ambiguity Risks:**
*   **Prose Attachment (Pollution):** Because the `(.+?)` capture group is so permissive, if the LLM outputs `**ANSWER: 42 because x=2**`, the entire string `"42 because x=2"` is extracted.
*   **Missing Answers:** If the model deviates slightly from the formatting instructions (e.g., `The final answer is: 42`), the regex fails, returning `None`. The agent then assumes the attempt failed, potentially triggering expensive fallback loops (Self-Correction) even if the mathematical reasoning was sound.
*   **Multiple Answers:** The regex uses `re.search`, which only captures the *first* instance it finds. If the model hallucinates a mid-trace summary like `**ANSWER: x=2** (intermediate step)` and later concludes `**ANSWER: 42**`, the agent will extract `x=2`.

---

## 2. Answer Normalization
**Current Methodology:**
*   **None.** The current implementation performs absolutely zero canonicalization or normalization on the extracted strings.

**Identified Ambiguity Risks:**
*   **Formatting Differences:** The strings `"42"`, `"42.0"`, `"42 "`, and `"\frac{84}{2}"` are treated as four completely distinct answers.
*   **LaTeX Variability:** The strings `"\\pi"`, `"\pi"`, and `"pi"` are treated as distinct.

**Recommendation:** A centralized canonicalization layer must be built to strip whitespace, handle basic mathematical equivalencies, and standardize LaTeX before tallying votes.

---

## 3. Canonical Answer Parsing
**Current Methodology:**
*   **None.** The agent relies entirely on raw string matching via Python's `collections.Counter` during the majority voting phase.

---

## 4. Final Answer Selection / Voting
**Files & Functions Involved:**
*   `agent/deep_researcher.py` -> `_check_early_consensus`
*   `agent/deep_researcher.py` -> `_majority_vote`
*   `agent/deep_researcher.py` -> `_genselect`

**Current Methodology:**
The `DeepResearcher` employs two distinct paths for final answer selection.

**Path A: Majority Voting (String Consensus)**
1.  **Waves:** The agent generates $N$ samples in waves.
2.  **Tally:** It counts the occurrences of each exact, raw extracted string using `collections.Counter`. It applies a $2\times$ weight if the corresponding code block executed without an exception in the sandbox.
3.  **Early Stopping:** If a dynamic threshold (e.g., 75% agreement with 4 samples) is met, it stops generating and returns the top string as the final consensus.
4.  **Final Vote:** If all $N$ samples are generated, it requires $\ge 30\%$ weighted agreement to declare a consensus.

**Path B: GenSelect (Comparative Evaluation)**
1.  **Trigger:** If the majority vote results in a weak consensus (e.g., a top answer with $< 40\%$ agreement), the agent falls back to GenSelect.
2.  **Summarization:** It truncates the reasoning trace of every valid attempt to 2000 characters.
3.  **Evaluation:** It feeds these truncated summaries back into the LLM, prompting it to select the "best" reasoning chain by outputting a number (e.g., `BEST: 2`).
4.  **Selection:** It extracts the answer from the chosen solution.

**Identified Vulnerabilities in Selection:**
*   **Vote Fracturing:** Because there is no normalization (Section 2), the majority vote is highly susceptible to vote fracturing, causing the agent to falsely trigger GenSelect.
*   **GenSelect Truncation:** By arbitrarily truncating the solution summaries to 2000 characters, the GenSelect model may be forced to evaluate complex proofs based on incomplete information, leading to blind or hallucinated choices.