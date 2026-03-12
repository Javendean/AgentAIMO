"""
Test Suite for DeepResearcher v2 Agent

Tests cover:
    1. Sandbox security (blocking dangerous operations)
    2. Prompt generation (v2 prompts with balanced prompting, NL verify)
    3. Chat template selection (Qwen vs Llama auto-detect)
    4. Answer extraction from solutions
    5. NL verdict extraction
    6. Dry-run pipeline with majority voting
    7. Timer enforcement
    8. Dynamic time allocation

Run:
    python -m pytest tests/test_agent.py -v
    -- or --
    python tests/test_agent.py
"""

import json
import sys
import time
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.sandbox import run_verification, extract_code_blocks, SAFETY_PREAMBLE
from agent.prompts import (
    build_system_prompt,
    build_generate_prompt,
    build_verify_prompt,
    build_nl_verify_prompt,
    build_correct_prompt,
    extract_answer,
    extract_nl_verdict,
    detect_model_family,
    format_chat_prompt,
)
from agent.deep_researcher import DeepResearcher, TimeLimitExceeded


# =============================================================================
# Test Counters
# =============================================================================

_passed = 0
_failed = 0

# Note on Testing Blindspots:
# 1. Lack of robust mocking for `vLLM` inference. Dry runs test pipeline glue but NOT token generation logic.
# 2. Hardcoded timeouts in tests are prone to flakiness in CI environments.
# 3. Code verification tests rely on exact string matches, making them brittle to minor Python output changes.
# 4. No coverage checking configured.

def assert_true(condition, msg=""):
    """Assert a boolean condition and update the global test counters."""
    global _passed, _failed
    if condition:
        _passed += 1
    else:
        _failed += 1
        print(f"  [FAIL] {msg}")


def assert_equal(actual, expected, msg=""):
    """Assert two values are equal."""
    assert_true(actual == expected, f"{msg}: expected {expected!r}, got {actual!r}")


def assert_in(needle, haystack, msg=""):
    """Assert a string contains a substring."""
    assert_true(needle in haystack, f"{msg}: {needle!r} not found")


def assert_not_none(val, msg=""):
    """Assert a value is not None."""
    assert_true(val is not None, f"{msg}: was None")


# =============================================================================
# Sandbox Tests
# =============================================================================

def test_sandbox_blocks_os():
    print("[TEST] Sandbox blocks os.system")
    _, output = run_verification("```python\nimport os\nos.system('whoami')\n```")
    assert_in("BLOCKED", output.upper(), "os.system should be blocked")

def test_sandbox_blocks_subprocess():
    print("[TEST] Sandbox blocks subprocess")
    _, output = run_verification("```python\nimport subprocess\n```")
    assert_in("BLOCKED", output.upper(), "subprocess should be blocked")

def test_sandbox_blocks_file_io():
    print("[TEST] Sandbox blocks file I/O")
    _, output = run_verification("```python\nf = open('/etc/passwd')\n```")
    assert_in("BLOCKED", output.upper(), "open() should be blocked")

def test_sandbox_allows_math():
    print("[TEST] Sandbox allows math operations")
    passed, output = run_verification(
        "```python\nimport math\nprint(math.factorial(10))\n```"
    )
    assert_true(passed, "math.factorial should work")
    assert_in("3628800", output, "factorial(10) = 3628800")

def test_sandbox_allows_sympy():
    print("[TEST] Sandbox allows sympy")

    passed, output = run_verification(
        "```python\nfrom sympy import isprime\nprint(isprime(17))\n```"
    )
    # BLINDSPOT / KNOWN BUG:
    # On newer versions of Python (like 3.12+), SymPy internals load modules (e.g., `ctypes`, `os`, `shutil`)
    # that are strictly blocked by the `_BLOCKED_MODULES` set in `agent/sandbox.py`.
    # As a result, this test will fail on newer environments even though `sympy` is conceptually "allowed".
    # Because our instructions are to document bugs rather than fix them, this test will currently
    # fail when executed.
    assert_true(passed, "sympy should work")

def test_sandbox_timeout():
    print("[TEST] Sandbox enforces timeout")
    passed, output = run_verification(
        "```python\nwhile True: pass\n```",
        timeout=2,
    )
    assert_true(not passed, "Infinite loop should timeout")

def test_code_block_extraction():
    print("[TEST] Code block extraction")
    text = """
Here's my solution:
```python
x = 42
print(x)
```
And another:
```python
y = 100
```
    """
    blocks = extract_code_blocks(text)
    assert_equal(len(blocks), 2, "Should find 2 code blocks")

def test_blocked_modules_coverage():
    print("[TEST] Blocked modules list is comprehensive")
    critical = {"os", "subprocess", "shutil", "socket", "http", "urllib"}
    for mod in critical:
        assert_in(f"'{mod}'", SAFETY_PREAMBLE, f"{mod} should be blocked")


# =============================================================================
# Prompt Tests (v2)
# =============================================================================

def test_system_prompt_no_patch():
    print("[TEST] System prompt without patches")
    prompt = build_system_prompt()
    assert_in("world-class mathematician", prompt, "Identity check")
    assert_in("Anti-Confirmation Bias", prompt, "Balanced prompting present")
    assert_in("DISPROVE", prompt, "Anti-confirmation bias instruction")
    assert_in("Domain-Specific Patches", prompt, "Patch slot present")

def test_system_prompt_with_patch():
    print("[TEST] System prompt with patches")
    patch = "## Custom Rule\n- Always check modular arithmetic"
    prompt = build_system_prompt(patch)
    assert_in("Custom Rule", prompt, "Patch should be injected")
    assert_true("No patches loaded" not in prompt, "Default should be replaced")

def test_generate_prompt():
    print("[TEST] Generate prompt (v2)")
    prompt = build_generate_prompt("Find the sum of 1 to 100")
    assert_in("Find the sum", prompt, "Problem text present")
    assert_in("disprove", prompt.lower(), "Anti-confirmation bias in gen prompt")
    assert_in("two possible approaches", prompt.lower(), "Multiple approaches")

def test_verify_prompt():
    print("[TEST] Verify prompt")
    prompt = build_verify_prompt("Problem X", "Solution Y")
    assert_in("DIFFERENT method", prompt, "Alt method request")
    assert_in("VERIFIED: True", prompt, "Expected output format")

def test_nl_verify_prompt():
    print("[TEST] Natural Language Verify prompt")
    prompt = build_nl_verify_prompt("Problem X", "Solution Y")
    assert_in("VERDICT: CORRECT", prompt, "Expected verdict format")
    assert_in("VERDICT: ERROR", prompt, "Expected error format")
    assert_in("logical errors", prompt.lower(), "Logic check")
    assert_in("unstated assumptions", prompt.lower(), "Assumption check")

def test_correct_prompt():
    print("[TEST] Correct prompt (v2)")
    prompt = build_correct_prompt("Problem", "Old solution", "Error msg")
    assert_in("different", prompt.lower(), "Should suggest different approach")
    assert_in("disprove", prompt.lower(), "Anti-confirmation bias")


# =============================================================================
# Chat Template Tests
# =============================================================================

def test_detect_model_family_qwen():
    print("[TEST] Detect model family — Qwen")
    assert_equal(detect_model_family("deepseek-r1-distill-qwen-32b-awq"), "qwen")
    assert_equal(detect_model_family("/models/QwQ-32B/"), "qwen")
    assert_equal(detect_model_family("Klear-Reasoner-8B"), "qwen")

def test_detect_model_family_llama():
    print("[TEST] Detect model family — Llama")
    assert_equal(detect_model_family("deepseek-r1-distill-llama-70b-awq"), "llama")
    assert_equal(detect_model_family("/models/Meta-Llama-3/"), "llama")

def test_qwen_chat_template():
    print("[TEST] Qwen chat template format")
    prompt = format_chat_prompt("System", "User", model_family="qwen")
    assert_in("<|im_start|>system", prompt, "Qwen system tag")
    assert_in("<|im_end|>", prompt, "Qwen end tag")
    assert_in("<|im_start|>assistant", prompt, "Qwen assistant tag")

def test_llama_chat_template():
    print("[TEST] Llama chat template format")
    prompt = format_chat_prompt("System", "User", model_family="llama")
    assert_in("<|begin_of_text|>", prompt, "Llama begin tag")
    assert_in("<|start_header_id|>system<|end_header_id|>", prompt, "Llama system tag")
    assert_in("<|eot_id|>", prompt, "Llama end tag")


# =============================================================================
# Answer Extraction Tests
# =============================================================================

def test_extract_answer_bold():
    print("[TEST] Extract answer — bold format")
    answer = extract_answer("The answer is **ANSWER: 42**")
    assert_equal(answer, "42", "Should extract 42")

def test_extract_answer_no_bold():
    print("[TEST] Extract answer — plain format")
    answer = extract_answer("ANSWER: 123\n")
    assert_equal(answer, "123", "Should extract 123")

def test_extract_answer_none():
    print("[TEST] Extract answer — no answer present")
    answer = extract_answer("Just some text without an answer")
    assert_true(answer is None, "Should return None")

def test_extract_nl_verdict_correct():
    print("[TEST] NL verdict — correct")
    ok, msg = extract_nl_verdict("After review, **VERDICT: CORRECT**")
    assert_true(ok, "Should be correct")

def test_extract_nl_verdict_error():
    print("[TEST] NL verdict — error")
    ok, msg = extract_nl_verdict("**VERDICT: ERROR** Sign error in step 3")
    assert_true(not ok, "Should be error")
    assert_in("Sign error", msg, "Should include error description")


# =============================================================================
# DeepResearcher v2 Tests
# =============================================================================

def test_dry_run_majority_vote():
    print("[TEST] Dry run with majority voting")
    researcher = DeepResearcher(
        model_path="deepseek-r1-distill-qwen-32b-awq",
        time_limit_hours=1.0,
        num_samples=4,
        max_retries=2,
        enable_tir=False,
        enable_nl_verify=False,
        dry_run=True,
    )
    assert_equal(researcher.model_family, "qwen", "Should detect Qwen family")

    problems = [
        {
            "id": "test_1",
            "problem_text": "What is 6 * 7?",
            "source": "test",
            "difficulty": "easy",
        }
    ]

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
        output_path = f.name

    summary = researcher.run(problems, output_path)

    assert_true(summary["attempted"] == 1, "Should attempt 1 problem")
    assert_equal(summary["model_family"], "qwen", "Summary should include model family")
    assert_true("strategies" in summary, "Summary should include strategy counts")

    # Verify JSONL output
    with open(output_path, "r") as f:
        traces = [json.loads(line) for line in f if line.strip()]
    assert_equal(len(traces), 1, "Should have 1 trace")
    assert_true(len(traces[0]["attempts"]) >= 1, "Should have at least 1 attempt")
    assert_true("majority_vote_answers" in traces[0], "Should include vote counts")

    Path(output_path).unlink(missing_ok=True)

def test_dry_run_full_pipeline():
    print("[TEST] Dry run full pipeline (v2)")
    researcher = DeepResearcher(
        model_path="deepseek-r1-distill-qwen-32b",
        time_limit_hours=0.5,
        num_samples=3,
        max_retries=2,
        enable_tir=False,
        enable_nl_verify=False,
        dry_run=True,
    )

    problems = [
        {"id": "p1", "problem_text": "Find 2+2", "source": "test", "difficulty": "easy"},
        {"id": "p2", "problem_text": "Find 3+3", "source": "test", "difficulty": "medium"},
    ]

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
        output_path = f.name

    summary = researcher.run(problems, output_path)

    assert_true(summary["attempted"] == 2, "Should attempt 2 problems")
    assert_true(summary["elapsed_seconds"] > 0, "Should have elapsed time")

    # Verify JSONL has 2 lines
    with open(output_path, "r") as f:
        lines = [l for l in f if l.strip()]
    assert_equal(len(lines), 2, "JSONL should have 2 lines")

    # Verify summary file exists
    summary_path = str(Path(output_path).with_suffix(".summary.json"))
    assert_true(Path(summary_path).exists(), "Summary JSON should exist")

    Path(output_path).unlink(missing_ok=True)
    Path(summary_path).unlink(missing_ok=True)

def test_timer_enforcement():
    print("[TEST] Timer enforcement")
    researcher = DeepResearcher(
        model_path="test-model-qwen",
        time_limit_hours=0.0001,  # ~0.36 seconds
        dry_run=True,
    )
    researcher.start_time = time.time() - 10  # Pretend 10s elapsed

    try:
        researcher._check_timer()
        assert_true(False, "Should have raised TimeLimitExceeded")
    except TimeLimitExceeded:
        assert_true(True, "Timer enforcement works")

def test_dynamic_time_allocation():
    print("[TEST] Dynamic time allocation")
    researcher = DeepResearcher(
        model_path="test-model",
        time_limit_hours=1.0,
        dry_run=True,
    )
    researcher.start_time = time.time()

    # Easy problem should get less time
    easy_budget = researcher._compute_time_budget(10, "easy")
    hard_budget = researcher._compute_time_budget(10, "hard")
    assert_true(hard_budget > easy_budget, "Hard problems should get more time")


# =============================================================================
# Main Runner
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("DeepResearcher v2 — Test Suite")
    print("=" * 50)

    # Sandbox tests
    test_sandbox_blocks_os()
    test_sandbox_blocks_subprocess()
    test_sandbox_blocks_file_io()
    test_sandbox_allows_math()
    test_sandbox_allows_sympy()
    test_sandbox_timeout()
    test_code_block_extraction()
    test_blocked_modules_coverage()

    # Prompt tests
    test_system_prompt_no_patch()
    test_system_prompt_with_patch()
    test_generate_prompt()
    test_verify_prompt()
    test_nl_verify_prompt()
    test_correct_prompt()

    # Chat template tests
    test_detect_model_family_qwen()
    test_detect_model_family_llama()
    test_qwen_chat_template()
    test_llama_chat_template()

    # Answer extraction tests
    test_extract_answer_bold()
    test_extract_answer_no_bold()
    test_extract_answer_none()
    test_extract_nl_verdict_correct()
    test_extract_nl_verdict_error()

    # DeepResearcher v2 tests
    test_dry_run_majority_vote()
    test_dry_run_full_pipeline()
    test_timer_enforcement()
    test_dynamic_time_allocation()

    print("\n" + "=" * 50)
    print(f"Results: {_passed}/{_passed + _failed} passed, {_failed} failed")
    print("=" * 50)

    sys.exit(1 if _failed > 0 else 0)
