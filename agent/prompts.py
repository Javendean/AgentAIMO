"""
Prompt Templates for the DeepResearcher Agent (v2).

Upgraded prompts for the AIMO3 competition with:
- Balanced prompting (anti-confirmation bias, from Gemini Deep Think)
- Tool-Integrated Reasoning (TIR) support
- Natural Language Verifier prompt
- Multiple chat template support (Qwen + Llama)
- Higher token budget awareness

The PATCH_SLOT in the system prompt is where "System Prompt Patches" from
the local analysis pipeline get injected between runs.
"""

import re


# =============================================================================
# CHAT TEMPLATES — Auto-detect model family and format correctly
# =============================================================================

def detect_model_family(model_path: str) -> str:
    """Detect model family from path/name for correct chat template.

    Args:
        model_path (str): The file path or name of the model being used.

    Returns:
        str: A string indicating the detected model family ('qwen' or 'llama').
             Defaults to 'qwen' if the family cannot be explicitly determined.
    """
    path_lower = model_path.lower()
    if "qwen" in path_lower or "qwq" in path_lower or "klear" in path_lower:
        return "qwen"
    elif "llama" in path_lower or "meta" in path_lower:
        return "llama"
    elif "deepseek" in path_lower:
        # DeepSeek-R1-Distill-Qwen → qwen, DeepSeek-R1-Distill-Llama → llama
        if "qwen" in path_lower:
            return "qwen"
        elif "llama" in path_lower:
            return "llama"
        return "qwen"  # Default DeepSeek to Qwen template
    return "qwen"  # Safe default


def format_chat_prompt(
    system_prompt: str,
    user_prompt: str,
    model_family: str = "qwen",
    assistant_prefix: str = "",
) -> str:
    """Format a chat prompt using the correct template for the model family.

    Args:
        system_prompt (str): The system prompt text.
        user_prompt (str): The user prompt text.
        model_family (str, optional): The target model family ('qwen' or 'llama'). Defaults to "qwen".
        assistant_prefix (str, optional): Optional text to pre-fill the assistant's response. Defaults to "".

    Returns:
        str: The fully formatted chat prompt string ready for inference.
    """
    if model_family == "qwen":
        return _format_qwen(system_prompt, user_prompt, assistant_prefix)
    elif model_family == "llama":
        return _format_llama(system_prompt, user_prompt, assistant_prefix)
    else:
        return _format_qwen(system_prompt, user_prompt, assistant_prefix)


def _format_qwen(system: str, user: str, asst_prefix: str = "") -> str:
    """Qwen / Qwen2.5 / QwQ / DeepSeek-R1-Distill-Qwen chat template.

    Args:
        system (str): The system prompt text.
        user (str): The user prompt text.
        asst_prefix (str, optional): Optional text to pre-fill the assistant's response. Defaults to "".

    Returns:
        str: The formatted Qwen-style chat prompt.
    """
    prompt = (
        f"<|im_start|>system\n{system}<|im_end|>\n"
        f"<|im_start|>user\n{user}<|im_end|>\n"
        f"<|im_start|>assistant\n{asst_prefix}"
    )
    return prompt


def _format_llama(system: str, user: str, asst_prefix: str = "") -> str:
    """Llama 3 / DeepSeek-R1-Distill-Llama chat template.

    Args:
        system (str): The system prompt text.
        user (str): The user prompt text.
        asst_prefix (str, optional): Optional text to pre-fill the assistant's response. Defaults to "".

    Returns:
        str: The formatted Llama-style chat prompt.
    """
    prompt = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        f"{system}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n"
        f"{user}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        f"{asst_prefix}"
    )
    return prompt


def format_tir_continuation(
    model_family: str,
    execution_result: str,
) -> str:
    """Format code execution output for Tool-Integrated Reasoning (TIR) injection mid-generation.

    Args:
        model_family (str): The model family, though currently unused in the formatting logic.
        execution_result (str): The string output from the executed Python code.

    Returns:
        str: A markdown block containing the execution output, formatted for the model to continue generation.
    """
    # This is injected as if the assistant paused and received tool output
    result_block = f"\n```output\n{execution_result}\n```\n"
    return result_block


# =============================================================================
# SYSTEM PROMPT — The agent's identity and reasoning instructions (v2)
# =============================================================================

SYSTEM_PROMPT = """\
You are a world-class mathematician competing in the AI Mathematical Olympiad.
Your goal is to solve competition-level math problems with perfect accuracy.

## Reasoning Protocol

1. **Read carefully.** Identify what is being asked. Note ALL constraints.
2. **Plan multiple approaches.** Consider at least 2 different solution \
strategies before committing. Briefly outline each.
3. **Show all work.** Write out every step of your reasoning. Never skip steps.
4. **Verify as you go.** After each major step, sanity-check the result.
5. **Write Python verification code.** You MUST write Python code in \
```python ... ``` blocks to verify your reasoning computationally. This is \
mandatory, not optional. The code will be executed and the output shown to you.
6. **Challenge your answer.** Before accepting, briefly try to find a \
counterexample or a flaw in your reasoning. If you fail to disprove it, \
your confidence should increase.
7. **State your final answer clearly** on its own line in the format:
   **ANSWER: [your answer]**

## Mathematical Tools Available
- Python with `math`, `sympy`, `itertools`, `functools`, `fractions`, `decimal`
- NumPy for numerical computation
- No file I/O, no network access, no external libraries beyond the above

## Common Pitfalls to Avoid
- Off-by-one errors in counting problems
- Forgetting edge cases (n=0, n=1, empty sets)
- Confusing permutations with combinations
- Not checking all cases in modular arithmetic
- Assuming commutativity/associativity where it doesn't hold
- Circular reasoning: ensure your proof doesn't assume what it's proving
- Sign errors in algebraic manipulation
- Forgetting to check that a solution actually satisfies the original constraints

## CRITICAL Rules (Mistake Prevention)
1. **NEVER do arithmetic in your head.** Even simple calculations like 7×13 \
MUST be verified in a Python code block. Mental arithmetic in long reasoning \
chains is the #1 source of propagated errors. Always ```python print(7*13) ```.
2. **Before finalizing, run this edge case checklist:**
   - Did I consider x=0? Negative values? The trivial case?
   - Did I check boundary conditions at the extremes of the domain?
   - Does my answer satisfy ALL original constraints (re-read the problem)?
   - If the problem asks "find ALL solutions," did I prove there are no others?
3. **Never assume functional forms without proof.** If you try f(x)=ax+b and \
it works, you have NOT proven it is the ONLY solution. You must show no other \
form is possible, or your answer gets 0 points even if correct.
4. **For combinatorics with state transitions:** Explicitly look for an \
INVARIANT — a quantity that does not change under the allowed operations. \
Test candidate invariants in code before building your proof around one.

## Technical Constraints (Code Execution)
1. **NO Nested Backticks**: Do NOT put ` ```python ` or ` ``` ` inside your \
code blocks. This breaks the parsing engine.
2. **Raw Strings for LaTeX**: When printing LaTeX or regex, ALWAYS use raw \
strings `r"..."` to prevent `SyntaxError: unicode error`.
   - BAD: `print("\\frac{{1}}{{2}}")` (Crashes)
   - GOOD: `print(r"\\frac{{1}}{{2}}")` (Works)
3. **Complete Code**: Do not truncate or summarize code. It must be executable.

## Anti-Confirmation Bias Protocol
When you reach a candidate answer:
1. Spend 2-3 sentences attempting to DISPROVE your answer
2. Try at least one edge case or boundary value
3. If your disproof attempt fails, state why and accept the answer
4. If your disproof succeeds, revise your approach entirely

{patch_slot}
"""

# Placeholder for injecting learned rules from local analysis
PATCH_SLOT_DEFAULT = """\
## Domain-Specific Patches
(No patches loaded — this is the baseline prompt)
"""


# =============================================================================
# TOPIC-SPECIFIC PATCHES — Inject strategy hints based on problem type
# =============================================================================

TOPIC_PATCHES = {
    "algebra": """\
## Algebra-Specific Strategies
- Try substitution first for systems of equations
- For polynomials, consider Vieta's formulas and factor theorem
- For inequalities, try AM-GM, Cauchy-Schwarz, or Jensen's inequality
- For functional equations, test f(x)=ax+b but PROVE uniqueness
- Check if the problem has symmetry you can exploit""",

    "combinatorics": """\
## Combinatorics-Specific Strategies
- Search for an INVARIANT or MONOVARIANT first
- Consider bijections to simpler counting problems
- Try small cases (n=1,2,3) first, then generalize with induction
- Apply pigeonhole principle when items > containers
- For coloring/tiling: look for parity arguments""",

    "geometry": """\
## Geometry-Specific Strategies
- Try coordinate geometry if the problem has specific labeled points
- Use trigonometric identities for angle-based problems
- Apply Stewart's theorem, power of a point, or radical axes
- For optimization, look at reflection principles
- Use the law of cosines / law of sines as computational tools""",

    "number_theory": """\
## Number Theory-Specific Strategies
- Check modular arithmetic for divisibility constraints
- Factor the expression and analyze prime factor structure
- Apply Fermat's little theorem, Euler's theorem as appropriate
- For Diophantine equations, bound the solutions then check
- Use Legendre's formula for prime factorizations of factorials""",
}

# Keywords used for automatic topic classification
_TOPIC_KEYWORDS = {
    "algebra": [
        "polynomial", "equation", "inequality", "root", "coefficient",
        "variable", "solve for", "function f", "f(x)", "real number",
        "complex number", "quadratic", "cubic", "system of equations",
    ],
    "combinatorics": [
        "color", "tiling", "tiled", "tile", "permut", "combin", "arrange",
        "board", "grid", "graph", "path", "tournament", "game", "strategy",
        "player", "move", "winning", "sequence of moves", "bijection",
        "counting", "how many ways",
    ],
    "geometry": [
        "triangle", "circle", "angle", "perpendicular", "parallel",
        "midpoint", "circumscri", "inscri", "tangent", "chord",
        "area", "perimeter", "diameter", "radius", "polygon",
    ],
    "number_theory": [
        "divisible", "prime", "gcd", "lcm", "modulo", "remainder",
        "integer", "digit", "factorial", "coprime", "congruent",
        "divides", "perfect square", "perfect cube",
    ],
}


def classify_topic(problem_text: str) -> str | None:
    """Classify a math problem into a topic via keyword matching.

    Args:
        problem_text (str): The text of the math problem to classify.

    Returns:
        str | None: The topic key (e.g., "algebra") if classified with at least
                    2 matching keywords, or None if uncertain.

    Note:
        Blindspot: Simple keyword matching is highly brittle. Words like 'variable'
        might appear in geometry or combinatorics problems, leading to misclassification.
    """
    text_lower = problem_text.lower()
    scores = {}
    for topic, keywords in _TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[topic] = score

    if not scores:
        return None

    # Return topic with highest keyword match count
    best_topic = max(scores, key=scores.get)
    # Only classify if we have at least 2 matching keywords (avoid false positives)
    if scores[best_topic] >= 2:
        return best_topic
    return None


# =============================================================================
# GENERATE PROMPT — Initial solution generation (v2)
# =============================================================================

GENERATE_PROMPT = """\
Solve the following competition math problem. Think step-by-step, show all \
your work, and write Python code to verify your computations.

## Problem
{problem_text}

## Instructions
1. Analyze the problem carefully. Identify all constraints and what is asked.
2. Consider at least two possible approaches. Briefly outline why you chose one.
3. Execute the solution with full mathematical rigor.
4. Write Python code blocks to verify intermediate results and your final answer.
5. Before stating your answer, briefly attempt to disprove it (edge cases, \
boundary values, or alternative reasoning).
6. State your final answer as: **ANSWER: [value]**

Important: Your Python code will be executed and the output returned to you. \
Use this to check your work.
"""


# =============================================================================
# VERIFY PROMPT — Ask model to write verification code
# =============================================================================

VERIFY_PROMPT = """\
You previously proposed this solution to a math problem:

## Problem
{problem_text}

## Your Previous Solution
{solution}

## Task
Write a Python program that independently verifies whether the answer is \
correct. The program should:
1. Solve the problem from scratch using a DIFFERENT method if possible
2. Compare its result with your proposed answer
3. Print "VERIFIED: True" if correct, "VERIFIED: False" if not
4. If the answer is wrong, print what the correct answer should be

Wrap your code in a ```python ... ``` block.
"""


# =============================================================================
# NATURAL LANGUAGE VERIFIER — Catch logic errors code can't detect
# =============================================================================

NL_VERIFY_PROMPT = """\
You are a rigorous mathematical reviewer. Carefully review the following \
solution for logical errors, unstated assumptions, and mathematical mistakes.

## Problem
{problem_text}

## Solution Under Review
{solution}

## Your Task
1. Check each logical step for validity
2. Identify any unstated assumptions
3. Look for common mistakes (sign errors, off-by-one, incorrect formula usage)
4. Verify the final answer is consistent with ALL problem constraints

If the solution is correct, respond with: **VERDICT: CORRECT**
If you find errors, respond with: **VERDICT: ERROR** followed by a \
description of the specific flaw.
"""


# =============================================================================
# SELF-CORRECT PROMPT — Fix errors based on verification feedback (v2)
# =============================================================================

CORRECT_PROMPT = """\
Your previous solution to the following problem had errors during verification.

## Problem
{problem_text}

## Your Previous Solution
{previous_solution}

## Verification Error
{error_message}

## Task
1. Carefully analyze what went wrong
2. Identify the specific mathematical or logical error
3. Consider whether your entire approach was wrong, or just a calculation error
4. Produce a corrected solution with full reasoning
5. Write NEW Python verification code to confirm the corrected answer
6. Before accepting, try to disprove your new answer
7. State your corrected final answer as: **ANSWER: [value]**

Do NOT repeat the same approach if it fundamentally failed. Try a different \
strategy if needed.
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def build_system_prompt(patch_text: str | None = None) -> str:
    """Build the full system prompt with optional patches.

    Args:
        patch_text (str | None, optional): Custom instructions to inject into the system prompt.
                                           Defaults to None.

    Returns:
        str: The complete system prompt text.
    """
    patch = patch_text if patch_text else PATCH_SLOT_DEFAULT
    return SYSTEM_PROMPT.format(patch_slot=patch)


def build_generate_prompt(problem_text: str) -> str:
    """Build the generation prompt for a problem.

    Args:
        problem_text (str): The math problem to be solved.

    Returns:
        str: The generation prompt asking the model to solve the problem.
    """
    return GENERATE_PROMPT.format(problem_text=problem_text)


def build_verify_prompt(problem_text: str, solution: str) -> str:
    """Build the verification prompt.

    Args:
        problem_text (str): The math problem.
        solution (str): The proposed solution text.

    Returns:
        str: The prompt asking the model to verify the proposed solution.
    """
    return VERIFY_PROMPT.format(problem_text=problem_text, solution=solution)


def build_nl_verify_prompt(problem_text: str, solution: str) -> str:
    """Build the natural language verifier prompt.

    Args:
        problem_text (str): The math problem.
        solution (str): The proposed solution text.

    Returns:
        str: The prompt asking the model to perform a rigorous NL review of the solution.
    """
    return NL_VERIFY_PROMPT.format(problem_text=problem_text, solution=solution)


def build_correct_prompt(
    problem_text: str, previous_solution: str, error_message: str
) -> str:
    """Build the self-correction prompt.

    Args:
        problem_text (str): The math problem.
        previous_solution (str): The incorrect solution that needs correction.
        error_message (str): The error details from sandbox execution or NL verifier.

    Returns:
        str: The self-correction prompt guiding the model to fix the mistakes.
    """
    return CORRECT_PROMPT.format(
        problem_text=problem_text,
        previous_solution=previous_solution,
        error_message=error_message,
    )


def extract_answer(solution_text: str) -> str | None:
    """Extract the final integer answer from a solution text.

    AIMO answers are non-negative integers in the range [0, 99999].
    Only extracts clean integer tokens — rejects prose-polluted answers
    that would fracture the majority-vote counter.

    Patterns tried in order:
      1. ``**ANSWER: 42**``  (bold, with closing markers)
      2. ``**ANSWER: 42``    (bold, model truncated before closing **)
      3. ``ANSWER: 42``      (no bold markers)
      4. ``\\boxed{42}``     (LaTeX boxed format)

    Args:
        solution_text (str): The full text of the model's generated solution.

    Returns:
        str | None: The integer string (e.g. ``"42"``), or None if no valid
        integer in [0, 99999] can be extracted.
    """
    # Pattern 1 & 2: **ANSWER: N** or **ANSWER: N
    match = re.search(
        r"\*\*ANSWER:\s*(\d{1,6})(?:\*\*|\s*$|\s*\n)",
        solution_text, re.IGNORECASE | re.MULTILINE
    )
    if match:
        val = int(match.group(1))
        return str(val) if 0 <= val <= 99999 else None

    # Pattern 3: ANSWER: N (no bold markers)
    match = re.search(
        r"ANSWER:\s*(\d{1,6})(?:\s|$|\n)",
        solution_text, re.IGNORECASE
    )
    if match:
        val = int(match.group(1))
        return str(val) if 0 <= val <= 99999 else None

    # Pattern 4: \boxed{N}
    match = re.search(r"\\boxed\{(\d{1,6})\}", solution_text)
    if match:
        val = int(match.group(1))
        return str(val) if 0 <= val <= 99999 else None

    return None


def extract_nl_verdict(verifier_output: str) -> tuple[bool, str]:
    """Extract the verdict from the natural language verifier.

    Fails safe: if the verifier model does not produce a recognisable
    ``VERDICT:`` tag, the function returns ``False`` (reject). A verifier
    that cannot communicate its decision should never silently approve.

    Args:
        verifier_output (str): The output generated by the NL verifier prompt.

    Returns:
        tuple[bool, str]: A tuple where the first element is True only when
        ``VERDICT: CORRECT`` was explicitly found, and the second element is
        an explanation or error message.
    """
    if "VERDICT: CORRECT" in verifier_output.upper():
        return True, "NL Verifier: Solution is correct"

    match = re.search(
        r"VERDICT:\s*ERROR\s*(.*)", verifier_output, re.IGNORECASE | re.DOTALL
    )
    if match:
        return False, f"NL Verifier found error: {match.group(1).strip()[:500]}"

    # Fail-safe: unclear or hallucinated format → reject, never silently approve.
    return False, "NL Verifier: Unclear output format — treated as UNVERIFIED (fail-safe)"
