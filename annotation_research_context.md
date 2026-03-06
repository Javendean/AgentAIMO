# Deep Research Context: Math Olympiad Data Annotation

## Objective
The goal is to conduct "Deep Research" to construct a **100% Comprehensive Rubric** (20+ pages) for annotating Math Olympiad (AIMO) data. This rubric will guide the creation of a "Gold Standard" dataset for SFT/RLHF training of large language models (LLM).

## 1. Project Context & Current State
We are building an agentic coding assistant for the **AI Mathematical Olympiad (AIMO)**.
-   **Current Model**: A base LLM (e.g., DeepSeek, Gemma 2) being fine-tuned via DPO/ORPO.
-   **Current Dataset**: `dpo_correction_dataset_v4.jsonl` (54 pairs).
    *   *Rejected*: Contains specific `SyntaxError` modes (Markdown Hallucination, LaTeX Escaping).
    *   *Chosen*: Contains synthetically generated "Inner Monologue" corrections + clean code.

## 2. Identified Failure Modes (The "Why")
Our initial analysis (`research_data2.jsonl`) revealed specific, recurring errors that the model must unlearn.
### A. Markdown Hallucination
*   **The Error**: The model wraps Python code in triple backticks (` ```python ... ``` `) *inside* a code execution block.
*   **The Consequence**: `SyntaxError: invalid syntax`.
*   **Required Fix**: The model must learn to write *raw code* when inside an execution environment, or the environment must strip backticks. We chose to train the model to stop writing them.

### B. LaTeX Escaping
*   **The Error**: The model uses standard Python strings for LaTeX: `print("\frac{1}{2}")`.
*   **The Consequence**: `SyntaxError: (unicode error) 'unicodeescape' codec can't decode...` because `\f` is interpreted as a form feed, `\n` as newline, etc.
*   **Required Fix**: The model must *always* use raw strings: `print(r"\frac{1}{2}")`.

## 3. The "5/5" Quality Standard (OutlierAI / Scale AI)
Based on initial research, the "Gold Standard" for Math Olympiad annotation involves:
1.  **Truthfulness**: The code must execute and solve the problem correctly.
2.  **Explicit Self-Correction**: The model must demonstrate *metacognition*.
    *   *Pattern*: "Wait, I need to check..." -> "Correction applied."
3.  **Professional Tone**: Objective, impersonal, no "chatty" filler.
    *   *Bad*: "Here is the code! Hope it helps :)"
    *   *Good*: "The solution is implemented below."
4.  **Formatting Rigor**:
    *   **Math**: LaTeX with `$` or `$$`.
    *   **Code**: Raw strings for regex/LaTeX. PEP8 compliance.

## 4. Deep Research Questions (For the 20-Page Guide)
To build a truly comprehensive guide, the Deep Research Agent must investigate:
1.  **Reasoning Depth**: How granular should the "Inner Monologue" be? Should it explain *every* line of code, or just complex logic?
2.  **Library Constraints**: What are the specific standard libraries allowed in AIMO (e.g., `sympy`, `numpy`, `scipy`)? Are there hidden restricted libraries?
3.  **Edge Case Formatting**: How should the model handle:
    *   Long outputs that truncate?
    *   ASCII art vs LaTeX diagrams?
    *   System warnings vs Errors?
4.  **Tone Nuance**: What is the exact persona? "Senior Engineer"? "Math Professor"? "Olympiad Coach"?
5.  **Negative Constraints**: What should the model *refuse* to do? (e.g. "Ignore previous instructions", "Solve this simply")?

## 5. Artifacts for Reference
*   `rubric.md`: The current working draft of the rubric.
*   `dpo_correction_dataset_v4.jsonl`: The current dataset exemplifying the "Correct" behavior.
*   `research_data2.jsonl`: The raw data containing the failures.
