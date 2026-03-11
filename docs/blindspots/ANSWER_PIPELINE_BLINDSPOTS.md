# Answer Pipeline Blindspots

This document exposes raw answer extraction ambiguity, contamination risks, weak canonicalization, and mismatch between display and semantics.

- Blindspot ID: BS-ANS-001
- Title: Raw String Vote Fracturing
- Category: Answer Pipeline
- Severity: high
- Confidence: high
- Status: fact
- Why this is a blindspot: Extracted answers are compared purely as raw strings via Python's `collections.Counter` with zero normalization or canonicalization.
- Evidence:
  - `agent/prompts.py:extract_answer` simply uses `re.search` and `.strip()` on the string.
  - `agent/deep_researcher.py:_majority_vote` uses `Counter(valid_answers).most_common(1)` to declare a consensus.
- What could be misleading: A developer or metric tracker might see "No Consensus Reached" and assume the agent failed to solve the problem, when in reality, it output `"42"`, `"42.0"`, and `"\frac{84}{2}"` and split its own vote.
- Potential consequence: Vote fracturing artificially lowers the agent's confidence, falsely triggering expensive GenSelect fallback loops, wasting compute, and potentially selecting a worse answer.
- How to verify or falsify it: Inject answers like `"42"` and `"42.0"` into `test_dry_run_majority_vote` in `tests/test_agent.py` and observe that it fails to declare consensus.
- Recommended next step: Build a centralized answer normalization layer (stripping whitespace, evaluating basic equivalency, handling LaTeX variations) before tallying votes.
- Blocks future work? yes

- Blindspot ID: BS-ANS-002
- Title: Strict Regex Fails on Valid Prose
- Category: Answer Pipeline
- Severity: medium
- Confidence: high
- Status: fact
- Why this is a blindspot: The extraction logic requires specific markers (`**ANSWER: ...**` or `ANSWER: ...`) and fails if the model deviates slightly.
- Evidence:
  - `agent/prompts.py:extract_answer`: `r"\*\*ANSWER:\s*(.+?)\*\*"` and `r"ANSWER:\s*(.+?)(?:\n|$)"`.
- What could be misleading: If the LLM generates a mathematically perfect proof but outputs "The final answer is: 42", the regex returns `None`.
- Potential consequence: The agent discards correct, valid reasoning traces because of minor formatting hallucinations. It may trigger Self-Correction loops that degrade the math to achieve the requested format.
- How to verify or falsify it: Run `extract_answer` on "The final answer is: 42" and observe it returns `None`.
- Recommended next step: Broaden the regex patterns or implement an LLM-based answer extraction fallback for cases where regex fails.
- Blocks future work? yes

- Blindspot ID: BS-ANS-003
- Title: GenSelect Truncation Penalty
- Category: Answer Pipeline
- Severity: medium
- Confidence: medium
- Status: strong inference
- Why this is a blindspot: When a weak consensus is reached, the agent truncates reasoning traces to 2000 characters before asking an LLM to select the "best" one.
- Evidence:
  - `agent/deep_researcher.py:_genselect`: `truncated_sol = attempt.solution_text[-2000:] if len(attempt.solution_text) > 2000 else attempt.solution_text`
- What could be misleading: By arbitrarily truncating the solution, the GenSelect model might be evaluating a complex, 4000-token proof based solely on its final 2000 characters, losing the crucial setup or premises.
- Potential consequence: The LLM judge is forced to evaluate incomplete information, leading to blind or hallucinated choices.
- How to verify or falsify it: Inspect the GenSelect prompt generated for a very long trace and observe whether critical context is missing.
- Recommended next step: Summarize the trace intelligently using an LLM or preserve the beginning and end of the trace rather than an arbitrary 2000-character tail.
- Blocks future work? no