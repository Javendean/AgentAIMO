# Math Olympiad Data Annotation Rubric

## Overview
This rubric defines the strict standards for "5/5" quality in Math Olympiad data annotation, modeled after guidelines from OutlierAI, Scale AI, and Mercor.

---

## 1. Correctness & Truthfulness (The "Gold Standard")
*   **Criterion**: The solution must be mathematically precise and factually flawless.
*   **5/5 Requirement**:
    *   Result is correct (checked against ground truth or verified via code).
    *   No "hallucinated" constraints or imaginary variables.
    *   Code executes without *any* errors (SyntaxError, runtime error).
    *   **Crucial**: If the model makes a mistake, it *must* catch it. A solution that makes a mistake and fixes it is better than a solution that hides it.

## 2. Reasoning & Chain of Thought (Deep Research)
*   **Criterion**: The "Inner Monologue" or reasoning trace must demonstrate *metacognition*.
*   **5/5 Requirement**:
    *   **Explicit Self-Correction**: The thought process must show the model "pausing" to verify critical steps.
        *   *Bad*: "I will use Python."
        *   *Good*: "I will use Python. *Wait, I need to ensure I import `numpy` before using it. Let me check the environment constraints.*"
    *   **Justification**: Every major logical leap must be justified. "I assume X because Y."
    *   **Completeness**: No skipped steps. The trace must connect the problem statement to the final code.

## 3. Formatting & Style (Strict Guidelines)
*   **Criterion**: Professional, academic presentation.
*   **5/5 Requirement**:
    *   **LaTeX Usage**:
        *   Inline math: `$x^2$` (using single dollars).
        *   Display math: `$$ \frac{a}{b} $$` (using double dollars).
        *   **NO** `\( ... \)` or `\[ ... \]` unless explicitly requested.
        *   **Python Strings**: MUST use raw strings `r'...'` for any LaTeX content to prevent `unicode error`.
    *   **Markdown Code Blocks**:
        *   Code must be strictly fenced: ` ```python ... ``` `.
        *   **NO** nested backticks inside the block.
    *   **Tone**:
        *   Objective, impersonal, professional.
        *   **Forbidden**: "Hope this helps!", "Sure! Here is the answer.", "Let's dive in!".
        *   **Required**: Direct statements. "The solution is derived as follows..."

## 4. Code Quality (Production Ready)
*   **Criterion**: The code must be robust, readable, and executable.
*   **5/5 Requirement**:
    *   **Imports**: All redundant imports removed.
    *   **Variables**: Descriptive names (`total_distance` vs `x`).
    *   **Comments**: "Why" comments, not just "What" annotations.
    *   **Output**: The code *must* print the final answer clearly.

---

## 5. Scoring Table (Likert Scale)

| Rating | Definition |
| :--- | :--- |
| **1/5 (Bad)** | Syntax Error, Hallucination, Wrong Answer. |
| **2/5 (Poor)** | Correct Answer but poor reasoning or bad formatting (e.g. no LaTeX). |
| **3/5 (Okay)** | Correct and readable, but lacks deep justification or self-correction. |
| **4/5 (Good)** | Strong solution, good formatting. Minor style nitpicks. |
| **5/5 (Amazing)** | Flawless. Includes "Wait..." self-correction, perfect LaTeX, raw strings, professional tone. |
