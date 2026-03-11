"""
Sandboxed Python Code Execution for the DeepResearcher Agent.

Executes Python code extracted from LLM-generated solutions in an isolated
subprocess with strict timeouts and safety restrictions. This prevents:
- Infinite loops from consuming the 3-hour H100 sprint
- Dangerous operations (file I/O, network, system commands)
- Memory bombs that could OOM the Kaggle container

Usage:
    from agent.sandbox import execute_code
    success, output, error = execute_code("print(2 + 2)")
"""

import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


# Code that gets injected BEFORE the user's code to restrict dangerous operations
SAFETY_PREAMBLE = textwrap.dedent("""\
import builtins
import sys

# Block dangerous builtins
_blocked = ['exec', 'eval', 'compile', '__import__']
# We allow __import__ for math/sympy but block dangerous modules below

# Block dangerous modules
_BLOCKED_MODULES = {
    'os', 'subprocess', 'shutil', 'pathlib',
    'socket', 'http', 'urllib', 'requests',
    'ctypes', 'multiprocessing', 'threading',
    'signal', 'resource', 'gc',
}

_original_import = builtins.__import__

def _safe_import(name, *args, **kwargs):
    top_level = name.split('.')[0]
    if top_level in _BLOCKED_MODULES:
        raise ImportError(f"Module '{name}' is blocked in sandbox")
    return _original_import(name, *args, **kwargs)

builtins.__import__ = _safe_import

# Block file operations
_original_open = builtins.open
def _blocked_open(*args, **kwargs):
    raise PermissionError("File I/O is blocked in sandbox")
builtins.open = _blocked_open

# Limit output to prevent memory bombs
_output_count = 0
_MAX_OUTPUT_LINES = 200
_original_print = builtins.print
def _limited_print(*args, **kwargs):
    global _output_count
    _output_count += 1
    if _output_count > _MAX_OUTPUT_LINES:
        raise RuntimeError(f"Output limit exceeded ({_MAX_OUTPUT_LINES} lines)")
    _original_print(*args, **kwargs)
builtins.print = _limited_print
""")


def execute_code(
    code: str,
    timeout: int = 30,
    max_output_bytes: int = 50_000,
) -> tuple[bool, str, str]:
    """Execute Python code in a sandboxed subprocess.

    Args:
        code (str): Python code string to execute.
        timeout (int, optional): Maximum execution time in seconds (default: 30).
        max_output_bytes (int, optional): Max bytes of stdout/stderr to capture (default: 50,000).

    Returns:
        tuple[bool, str, str]: A tuple of (success, stdout, stderr).
                               `success` is True if the code ran without errors (returncode == 0).

    Note:
        Blindspot: The sandbox relies on Python-level restrictions (`sys.modules`, overriding builtins)
        and environment stripping. This is NOT a secure sandbox against malicious code.
        It is only designed to prevent accidents (like infinite loops or simple file I/O).
        A sophisticated model could easily bypass this using reflection or C-extensions.
    """
    # Combine safety preamble with user code
    full_code = SAFETY_PREAMBLE + "\n# === USER CODE BELOW ===\n" + code

    # Write to a temporary file (subprocess can't handle very long -c args)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(full_code)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            # Limit memory via ulimit is Linux-only; Kaggle is Linux
            env={"PATH": "", "HOME": "/tmp", "PYTHONPATH": ""},
        )

        stdout = result.stdout[:max_output_bytes]
        stderr = result.stderr[:max_output_bytes]
        success = result.returncode == 0

        return success, stdout, stderr

    except subprocess.TimeoutExpired:
        return False, "", f"TIMEOUT: Code execution exceeded {timeout}s limit"

    except Exception as e:
        return False, "", f"SANDBOX ERROR: {type(e).__name__}: {str(e)}"

    finally:
        # Clean up temp file
        try:
            Path(tmp_path).unlink()
        except OSError:
            pass


def extract_code_blocks(text: str) -> list[str]:
    """Extract Python code blocks from LLM-generated markdown text.

    Handles both ` ```python ... ``` ` and ` ``` ... ``` ` blocks, as well
    as hallucinated `assistantcommentary` tags.

    Args:
        text (str): The markdown text containing code blocks.

    Returns:
        list[str]: A list of extracted Python code strings.

    Note:
        Blindspot: The regex `r"```(?:python|py)\\s*\\n(.*?)```"` stops at the first ` ``` `.
        If the model outputs nested backticks (despite instructions not to), it will truncate
        the code. The backup keyword-based matching for generic blocks is also very brittle.
    """
    import re

    blocks = []

    # Match ```python ... ``` blocks (most common from DeepSeek-R1)
    pattern = r"```(?:python|py)\s*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    blocks.extend(matches)

    # If no python-tagged blocks found, try generic ``` blocks
    if not blocks:
        pattern = r"```\s*\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        # Filter to blocks that look like Python (contain common keywords)
        python_keywords = {"import ", "def ", "print(", "for ", "if ", "while ", "="}
        for match in matches:
            if any(kw in match for kw in python_keywords):
                blocks.append(match)

    # [Parser Adapter] Support hallucinated 'assistantcommentary' format
    # Example: "assistantcommentary to=python codeprint(1)"
    if not blocks:
        # Look for the specific header the 20B model uses
        # We capture everything after the header until end of string (or next header? model usually does one)
        pattern = r"assistantcommentary to=python code\s*(.*)"
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        blocks.extend(matches)

    # [Runtime Safeguard] Strip nested backticks that break the interpreter
    # The model often hallucinates ```python ... ``` inside the block
    cleaned_blocks = []
    for block in blocks:
        # Remove lines that are just ``` or ```python
        lines = block.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                continue
            cleaned_lines.append(line)
        cleaned_blocks.append('\n'.join(cleaned_lines))

    return cleaned_blocks


def run_verification(solution_text: str, timeout: int = 30) -> tuple[bool, str]:
    """Extract and execute all code blocks from a solution.

    Args:
        solution_text (str): The full text of the model's generated solution.
        timeout (int, optional): The timeout in seconds for executing each block. Defaults to 30.

    Returns:
        tuple[bool, str]: A tuple of (all_passed, combined_output).
                          `all_passed` is True if all extracted code blocks executed without error.
                          `combined_output` contains the concatenated stdout and stderr.

    Note:
        Critical Assumption: This merely checks if the code executed without throwing an exception.
        "Code executed successfully" IS NOT equivalent to "math verified". The model might write code
        that evaluates `2+2` but answers a complex geometry question, and this function would return True.
    """
    blocks = extract_code_blocks(solution_text)

    if not blocks:
        return False, "NO_CODE: No executable Python code blocks found in solution"

    all_outputs = []
    all_passed = True

    for i, code in enumerate(blocks):
        success, stdout, stderr = execute_code(code, timeout=timeout)

        block_label = f"[Block {i + 1}/{len(blocks)}]"

        if success:
            output = f"{block_label} PASSED"
            if stdout.strip():
                output += f"\n  Output: {stdout.strip()}"
        else:
            all_passed = False
            output = f"{block_label} FAILED"
            if stderr.strip():
                output += f"\n  Error: {stderr.strip()}"

        all_outputs.append(output)

    combined = "\n".join(all_outputs)
    return all_passed, combined
