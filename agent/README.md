# Agent Module (`agent/`)

The `agent/` directory houses the core logic for the DeepResearcher H100-Optimized Math Research Agent. This module is responsible for problem-solving reasoning, communicating with LLMs (via vLLM), executing Python verification code, and selecting final answers.

## Components
*   `deep_researcher.py`: The main entrypoint. Manages time budgets, multi-sampling (majority voting), and the recursive retry/correction loop.
*   `prompts.py`: Handles templating and routing logic for prompts sent to the LLM. It detects model families to apply the correct chat template and constructs prompts for generation, verification, and correction.
*   `sandbox.py`: Extracts and securely executes Python blocks proposed by the model.

## Known Blindspots & Bugs
1.  **"Execution Success" vs. "Mathematical Validity"**: The sandbox verifies that code runs without exceptions (`sandbox.py`). It **does not** verify that the code implements correct mathematical logic for the problem at hand.
2.  **Brittle Parsing**: `extract_code_blocks` relies on regex that fails if backticks are nested. Similarly, `extract_answer` can easily capture trailing reasoning text if the LLM slightly deviates from the formatting instructions (`**ANSWER: ...**`).
3.  **Sandbox Security**: `sandbox.py` relies on `sys.modules` blocking and a basic `SAFETY_PREAMBLE`. This is a weak sandbox, built to stop accidental infinite loops or basic file reads, not adversarial code execution.
4.  **Keyword Heuristics**: `classify_topic` in `prompts.py` uses crude keyword matching. Generic words like "variable" or "grid" can easily misclassify algebraic or geometric problems.
5.  **NL Verifier Fallback**: If the natural language verifier (`extract_nl_verdict`) outputs an ambiguous response, it currently defaults to "pass," negating its own purpose.
