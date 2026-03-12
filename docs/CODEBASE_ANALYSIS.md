# Codebase Analysis: AIMO3 DeepResearcher Agent

## 1. Architectural Overview

The DeepResearcher v2 is a single-node Python agent designed for a 3-hour Kaggle GPU sprint to solve competition-level math problems. It leverages vLLM for high-throughput inference (optimized for H100s) and operates entirely offline.

The architecture is composed of three main phases:
1.  **Generation Phase (Majority Voting)**: The agent samples $N$ parallel solutions. It employs Tool-Integrated Reasoning (TIR) to run generated Python code mid-generation, injecting the results back into the model's context window.
2.  **Verification Phase (GenSelect & NL Verify)**: If a clear consensus isn't reached, it prompts the model to select the best reasoning chain. It also optionally asks the model to review the logic in plain English (NL Verification).
3.  **Correction Phase (Self-Correction)**: If consensus fails entirely, the agent takes the best-performing attempt and recursively prompts itself to fix errors identified by the code sandbox or the NL Verifier.

The results of this sprint are stored in `research_data.jsonl`, which is later processed locally by the `analysis` pipeline to generate "System Prompt Patches" for subsequent runs.

---

## 2. Component Breakdown

### 2.1 `agent/deep_researcher.py`
The core controller. It initializes vLLM, manages dynamic time allocation per problem (scaling by difficulty), coordinates the multi-wave generation strategy to save compute on early consensus, and orchestrates the GenSelect and Self-Correction fallback loops.

### 2.2 `agent/prompts.py`
The templating engine. It injects `System Prompt Patches`, auto-detects model families (Qwen vs. Llama) to apply the correct chat template, and classifies problems into topics (Algebra, Geometry, etc.) using keyword matching to inject domain-specific strategy hints.

### 2.3 `agent/sandbox.py`
The execution environment. It uses `subprocess` to run LLM-generated Python code blocks. It applies a `SAFETY_PREAMBLE` to restrict dangerous modules (`os`, `subprocess`, `socket`) and overrides builtins like `open` to prevent the agent from breaking out of the Kaggle container or consuming too much memory/time.

### 2.4 `analysis/analyze_results.py`
The offline grading script. It reads `research_data.jsonl`, aggregates success rates by problem source/difficulty, counts failure types (e.g., Timeout, SyntaxError), and outputs a markdown file (`prompt_patch.txt`) with rudimentary warnings to append to the system prompt in the next run.

### 2.5 `notebook/kaggle_notebook.py`
The Kaggle execution harness. It handles offline pip installations, runs a "Canary Test" to ensure the environment isn't throttling the 120B primary model, and falls back to a 72B model if necessary. It strictly manages the 3-hour time constraint to prevent idle quota drain.

---

## 3. Data Flow

1.  **Input:** A Kaggle dataset of math problems (`problems_v1.jsonl`) is loaded into memory by `kaggle_notebook.py`.
2.  **Inference:** `deep_researcher.py` queries vLLM.
3.  **TIR Loop:** When vLLM generates ` ```python ... ``` `, generation pauses. `sandbox.py` extracts the code, runs it, and the stdout/stderr is appended to the prompt context. vLLM resumes generation.
4.  **Consensus:** Extracted answers are tallied.
5.  **Output:** A detailed `ResearchTrace` object (containing attempts, code output, and total duration) is dumped to `research_data.jsonl`.
6.  **Analysis:** Post-run, `analyze_results.py` parses the JSONL and outputs a new `prompt_patch.txt` to be uploaded for the next Kaggle sprint.

---

## 4. Critical Bugs, Blindspots, and Failures

The following flaws were identified during a painstaking review of the codebase. These issues undermine the agent's reliability and its ability to definitively prove mathematical correctness.

### 4.1 The "Execution Success" Fallacy
**Location:** `agent/sandbox.py` -> `run_verification`
*   **The Flaw:** The system equates "code ran without crashing" (`returncode == 0`) with "the mathematical logic is verified." If the agent is asked to find the area of a circle and writes `print(2 + 2)`, the sandbox returns `True`.
*   **Impact:** The agent can easily hallucinate a completely wrong final answer, write trivial or irrelevant code that executes perfectly, and the system will tag the attempt as `verification_passed=True`.

### 4.2 Canary Test Brittleness and Data Leakage
**Location:** `notebook/kaggle_notebook.py` -> `run_canary_test`
*   **The Flaw (Brittleness):** The canary expects the exact output `\boxed{809}`. If the model outputs `**ANSWER: 809**` (which is what `prompts.py` actually instructs the model to do!), the canary fails. This triggers an immediate, catastrophic fallback from the 120B model to the 72B model.
*   **The Flaw (Leakage):** The canary problem is a well-known static AIME 2024 problem. A sufficiently trained math model will answer it instantly from its training weights without running any complex reasoning. This defeats the purpose of checking kernel inference speeds or quantization degradation on complex reasoning chains.

### 4.3 Brittle Regex Parsing
**Location:** `agent/sandbox.py` -> `extract_code_blocks` & `agent/prompts.py` -> `extract_answer`
*   **The Flaw (Code):** The regex `r"```(?:python|py)\s*\n(.*?)```"` breaks if the model nests backticks. The parser truncates the code block prematurely, causing a guaranteed `SyntaxError` in the sandbox.
*   **The Flaw (Answers):** The regex `r"\*\*ANSWER:\s*(.+?)\*\*"` is overly permissive. If the model outputs `**ANSWER: 42 because x=2**`, the extracted answer is the entire string, destroying the majority voting consensus logic which relies on exact string matches.

### 4.4 Superficial Error Patching
**Location:** `analysis/analyze_results.py` -> `generate_patch`
*   **The Flaw:** The analysis script looks for literal strings like "NameError" or "TIMEOUT" in the sandbox output to generate system prompt patches. It has no semantic understanding of *why* the model failed mathematically.
*   **Impact:** Telling the model "Double-check indentation" because a `SyntaxError` occurred does not fix the underlying inability to model a complex combinatorics state machine. The self-correction loop is highly likely to spin its wheels repeating the same logical errors.

### 4.5 The "Pass-Through" NL Verifier
**Location:** `agent/prompts.py` -> `extract_nl_verdict`
*   **The Flaw:** If the NL verifier model fails to output either `VERDICT: CORRECT` or `VERDICT: ERROR`, the fallback logic simply returns `True, "No clear verdict (treating as pass)"`.
*   **Impact:** Any formatting hallucination by the verifier automatically rubber-stamps a potentially flawed mathematical solution as correct.

### 4.6 Naive Topic Classification
**Location:** `agent/prompts.py` -> `classify_topic`
*   **The Flaw:** The function uses rudimentary keyword matching to inject topic patches. For example, if a geometry problem asks "How many ways can you arrange tiles on a polygon grid?", the words "arrange" and "grid" might cause it to be classified as combinatorics, injecting entirely wrong strategy hints into the context window.