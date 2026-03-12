"""AgentAIMO pytest fixtures."""

import pytest

from src.models.problem import Problem, ProblemMetadata, ProblemCategory
from src.models.solution import (
    SolutionTrace,
    SolutionStep,
    StepType,
    ExtractedCalculation,
)


@pytest.fixture
def sample_problem_with_answer() -> Problem:
    """Remainder when 2^100 divided by 7. Answer: 2."""
    metadata = ProblemMetadata(
        source="test_fixture",
        problem_id="test_001",
        category=ProblemCategory.NUMBER_THEORY,
        difficulty=0.3,
    )
    return Problem(
        text="What is the remainder when $2^{100}$ is divided by 7?",
        metadata=metadata,
        ground_truth=2,
    )


@pytest.fixture
def sample_correct_trace() -> SolutionTrace:
    """Correct solution using Fermat's Little Theorem. final_answer=2."""
    raw_text = (
        "By Fermat's Little Theorem, 2^6 ≡ 1 mod 7. "
        "We have 100 = 6*16 + 4. "
        "Then 2^100 = (2^6)^16 * 2^4 ≡ 1^16 * 16 ≡ 2 mod 7. "
        "Therefore, the remainder is 2. \\boxed{2}"
    )

    steps = [
        SolutionStep(
            step_num=1,
            text="By Fermat's Little Theorem, 2^6 ≡ 1 mod 7.",
            step_type=StepType.LOGIC,
            calculations=[ExtractedCalculation(expression="2**6 % 7", result="1")]
        ),
        SolutionStep(
            step_num=2,
            text="We have 100 = 6*16 + 4.",
            step_type=StepType.CALCULATION,
            calculations=[ExtractedCalculation(expression="6 * 16 + 4", result="100")]
        ),
        SolutionStep(
            step_num=3,
            text="Then 2^100 = (2^6)^16 * 2^4",
            step_type=StepType.LOGIC,
        ),
        SolutionStep(
            step_num=4,
            text="1^16 * 16 = 16",
            step_type=StepType.CALCULATION,
            calculations=[ExtractedCalculation(expression="1**16 * 16", result="16")]
        ),
        SolutionStep(
            step_num=5,
            text="16 ≡ 2 mod 7",
            step_type=StepType.CALCULATION,
            calculations=[ExtractedCalculation(expression="16 % 7", result="2")]
        ),
        SolutionStep(
            step_num=6,
            text="Therefore, the remainder is 2. \\boxed{2}",
            step_type=StepType.LOGIC,
        ),
    ]

    return SolutionTrace(
        raw_text=raw_text,
        steps=steps,
        final_answer=2,
    )


@pytest.fixture
def sample_incorrect_trace() -> SolutionTrace:
    """INCORRECT solution with deliberate error: 100=6*16+3 (should be +4). final_answer=1."""
    raw_text = (
        "By Fermat's Little Theorem, 2^6 ≡ 1 mod 7. "
        "We have 100 = 6*16 + 3. "
        "Then 2^100 = (2^6)^16 * 2^3 ≡ 1^16 * 8 ≡ 1 mod 7. "
        "Therefore, the remainder is 1. \\boxed{1}"
    )

    steps = [
        SolutionStep(
            step_num=1,
            text="By Fermat's Little Theorem, 2^6 ≡ 1 mod 7.",
            step_type=StepType.LOGIC,
            calculations=[ExtractedCalculation(expression="2**6 % 7", result="1")]
        ),
        SolutionStep(
            step_num=2,
            text="We have 100 = 6*16 + 3.",
            step_type=StepType.CALCULATION,
            calculations=[ExtractedCalculation(expression="6 * 16 + 3", result="100")]
        ),
        SolutionStep(
            step_num=3,
            text="Then 2^100 = (2^6)^16 * 2^3",
            step_type=StepType.LOGIC,
        ),
        SolutionStep(
            step_num=4,
            text="1^16 * 8 = 8",
            step_type=StepType.CALCULATION,
            calculations=[ExtractedCalculation(expression="1**16 * 8", result="8")]
        ),
        SolutionStep(
            step_num=5,
            text="8 ≡ 1 mod 7",
            step_type=StepType.CALCULATION,
            calculations=[ExtractedCalculation(expression="8 % 7", result="1")]
        ),
        SolutionStep(
            step_num=6,
            text="Therefore, the remainder is 1. \\boxed{1}",
            step_type=StepType.LOGIC,
        ),
    ]

    return SolutionTrace(
        raw_text=raw_text,
        steps=steps,
        final_answer=1,
    )


@pytest.fixture
def sample_aime_problem() -> Problem:
    """Harder problem without ground truth for stress testing."""
    metadata = ProblemMetadata(
        source="aime_2024",
        problem_id="aime_001",
        category=ProblemCategory.COMBINATORICS,
        difficulty=0.9,
    )
    return Problem(
        text=r"A sequence of numbers is defined by $a_0 = 1$, $a_1 = 2$, and $a_n = a_{n-1} + a_{n-2}$ for $n \ge 2$. Find the remainder when $a_{2024}$ is divided by 100.",
        metadata=metadata,
        ground_truth=None,
    )


@pytest.fixture
def calculation_samples() -> list[tuple[str, str, bool]]:
    """(expression, claimed_result, should_match) for arithmetic testing.

    At least 10 cases: simple arithmetic, C(n,k), factorials, exponents,
    modular arithmetic, and deliberately WRONG results.
    """
    return [
        ("10 * 9 * 8 / (3 * 2 * 1)", "120", True),
        ("2**10", "1024", True),
        ("C(10, 3)", "120", True),
        ("5!", "120", True),
        ("C(10, 3) * 2**7", "15360", True),
        ("2**10", "1023", False),
        ("17 mod 5", "2", True),
        ("3**3 + 4**3", "91", True),
        ("3**3 + 4**3", "90", False),
        ("100 / 7", "14.2857", True),
    ]
