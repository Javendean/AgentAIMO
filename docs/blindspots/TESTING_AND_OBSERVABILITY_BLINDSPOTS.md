# Testing and Observability Blindspots

This document exposes what tests actually protect, what areas lack tests, tests that encode wrong assumptions, and missing instrumentation.

- Blindspot ID: BS-TST-001
- Title: Missing Answer Normalization Tests
- Category: Testing and Observability
- Severity: medium
- Confidence: high
- Status: fact
- Why this is a blindspot: The test suite (`tests/test_agent.py`) tests `extract_answer` strictly for its ability to pull out a matching string but does not test it against any realistic answer variations, formatting quirks, or LaTeX equivalencies.
- Evidence:
  - `tests/test_agent.py:test_extract_answer_bold`: tests `**ANSWER: 42**`.
  - `tests/test_agent.py:test_extract_answer_none`: tests no matching string.
  - The suite fundamentally lacks canonicalization tests (e.g., `"42"` vs `"42.0"` vs `"\frac{84}{2}"`).
- What could be misleading: A passing test suite gives a false sense of security that the agent's vote tallying is robust.
- Potential consequence: Changes to `extract_answer` might inadvertently regress the agent's performance in subtle ways that the test suite is entirely blind to.
- How to verify or falsify it: Examine `tests/test_agent.py` for any tests that cover answer normalization.
- Recommended next step: Add robust canonicalization to the extraction pipeline and write comprehensive tests covering LaTeX formatting and whitespace variations.
- Blocks future work? yes

- Blindspot ID: BS-TST-002
- Title: Tests Do Not Cover GenSelect Flow
- Category: Testing and Observability
- Severity: medium
- Confidence: high
- Status: fact
- Why this is a blindspot: The GenSelect fallback (which is triggered when a majority vote fractures) is completely untested.
- Evidence:
  - `tests/test_agent.py:test_dry_run_majority_vote` tests the standard voting path.
  - There is no test for `_genselect`, including its arbitrary truncation logic (`-2000:` characters).
- What could be misleading: A developer assumes the system gracefully falls back to GenSelect because it is a defined method, unaware that this entire complex flow is essentially a black box.
- Potential consequence: Any bugs introduced in GenSelect (e.g., prompt parsing failures, truncation dropping crucial context) will go completely undetected by the test suite until a full, 3-hour local run is executed.
- How to verify or falsify it: Search for `_genselect` in `tests/`.
- Recommended next step: Write robust unit tests specifically for the GenSelect fallback logic, ensuring the truncation strategy and prompt format are preserved.
- Blocks future work? no