# Tests Module (`tests/`)

Contains the test suite verifying the behavior of the `agent` module.

## Components
*   `test_agent.py`: A monolithic test file checking sandbox security rules, prompt formatting, extraction logic, and a full mock dry-run of the DeepResearcher.
*   `test_hallucination_fix.py`: A specific test verifying that the agent can recover from hallucinated tool-call formats (`assistantcommentary`).

## Known Blindspots & Bugs
1.  **No Inference Mocking**: The tests perform "dry runs" but do not mock LLM outputs. This means the tests verify the python pipeline glue, but completely fail to test how the agent handles complex, multiline reasoning chains or unexpected model formatting variations.
2.  **Flaky Timeouts**: Timeouts are hardcoded in test cases. Depending on the CI runner's load, these tests may randomly fail.
3.  **Brittle Assertions**: Tests heavily rely on exact string matching (`assert_in("VERDICT: CORRECT", ...)`). Minor tweaks to prompt templates will break the test suite.
4.  **No Coverage Enforcement**: There are no tools or metrics configured to ensure edge-cases in `deep_researcher.py` are actually tested.
