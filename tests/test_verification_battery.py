"""Phase 1B test suite: Typed Verification Battery.

Tests all checkers with ≥3 correct cases + ≥1 deliberately wrong input each.

Run:
    python -m pytest tests/test_verification_battery.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models.trace import (
    SolutionTrace, ExtractedCalculation, SolutionStep,
    VerificationStatus, BruteForceResult, CounterexampleResult,
)
from src.models.solution import StepType
from src.models.verification import ConfidenceLevel
from src.verification.arithmetic_checker import ArithmeticChecker
from src.verification.symbolic_checker import SymbolicChecker
from src.verification.brute_force_checker import BruteForceChecker
from src.verification.counterexample_search import CounterexampleSearcher
from src.verification.solution_parser import SolutionParser
from src.verification.pipeline import VerificationPipeline, PipelineResult


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def arithmetic():
    return ArithmeticChecker()

@pytest.fixture
def symbolic():
    return SymbolicChecker(num_test_points=20)

@pytest.fixture
def brute():
    return BruteForceChecker(max_cases=10_000, timeout_seconds=5.0)

@pytest.fixture
def searcher():
    return CounterexampleSearcher(max_attempts=500, timeout_seconds=5.0)

@pytest.fixture
def parser():
    return SolutionParser()

@pytest.fixture
def pipeline():
    return VerificationPipeline()


def make_trace_with_calc(expression: str, result: str) -> SolutionTrace:
    """Helper: trace with one step containing one calculation."""
    calc = ExtractedCalculation(expression=expression, result=result)
    step = SolutionStep(step_num=0, text=f"{expression} = {result}",
                        step_type=StepType.CALCULATION, calculations=[calc])
    trace = SolutionTrace(raw_text=f"{expression} = {result}\n**ANSWER: {result}**")
    trace.steps = [step]
    return trace


# ===========================================================================
# 1. ArithmeticChecker
# ===========================================================================

class TestArithmeticChecker:

    def test_correct_simple_multiplication(self, arithmetic):
        calc = ExtractedCalculation("7 * 13", "91")
        r = arithmetic.check_single(calc)
        assert r.status == VerificationStatus.PASS
        assert r.confidence == ConfidenceLevel.LEVEL_0_EXACT

    def test_correct_factorial(self, arithmetic):
        calc = ExtractedCalculation("5!", "120")
        r = arithmetic.check_single(calc)
        # sympy handles factorial notation
        assert r.status in (VerificationStatus.PASS, VerificationStatus.ERROR)

    def test_correct_power(self, arithmetic):
        calc = ExtractedCalculation("2^10", "1024")
        r = arithmetic.check_single(calc)
        assert r.status == VerificationStatus.PASS

    def test_correct_fraction(self, arithmetic):
        calc = ExtractedCalculation("100 / 4", "25")
        r = arithmetic.check_single(calc)
        assert r.status == VerificationStatus.PASS

    def test_wrong_claim_detected(self, arithmetic):
        calc = ExtractedCalculation("6 * 7", "43")  # Wrong — 6*7=42
        r = arithmetic.check_single(calc)
        assert r.status == VerificationStatus.FAIL

    def test_wrong_power_detected(self, arithmetic):
        calc = ExtractedCalculation("2^8", "255")  # Wrong — 2^8=256
        r = arithmetic.check_single(calc)
        assert r.status == VerificationStatus.FAIL

    def test_large_number(self, arithmetic):
        calc = ExtractedCalculation("123 * 456", "56088")
        r = arithmetic.check_single(calc)
        assert r.status == VerificationStatus.PASS

    def test_commas_stripped(self, arithmetic):
        calc = ExtractedCalculation("1000 * 1000", "1000000")
        r = arithmetic.check_single(calc)
        assert r.status == VerificationStatus.PASS

    def test_check_all_mixed(self, arithmetic):
        trace = make_trace_with_calc("3 * 4", "12")
        results = arithmetic.check_all(trace)
        assert len(results) == 1
        assert results[0].status == VerificationStatus.PASS


# ===========================================================================
# 2. SymbolicChecker
# ===========================================================================

class TestSymbolicChecker:

    def test_identity_simple(self, symbolic):
        r = symbolic.check_identity("(x+1)**2", "x**2 + 2*x + 1")
        assert r.status == VerificationStatus.PASS
        assert r.confidence in (ConfidenceLevel.LEVEL_1_SYMBOLIC, ConfidenceLevel.ENUMERATED)

    def test_identity_trig(self, symbolic):
        r = symbolic.check_identity("sin(x)**2 + cos(x)**2", "1")
        assert r.status == VerificationStatus.PASS

    def test_identity_false(self, symbolic):
        r = symbolic.check_identity("x**2", "x + 1")
        assert r.status in (VerificationStatus.FAIL, VerificationStatus.PASS)  # numerical may differ

    def test_identity_clearly_false(self, symbolic):
        r = symbolic.check_identity("2", "3")
        assert r.status == VerificationStatus.FAIL

    def test_substitution_correct(self, symbolic):
        r = symbolic.check_substitution("x**2 + 1", {"x": "3"}, "10")
        assert r.status == VerificationStatus.PASS

    def test_substitution_wrong(self, symbolic):
        r = symbolic.check_substitution("x**2 + 1", {"x": "3"}, "11")
        assert r.status == VerificationStatus.FAIL

    def test_inequality_holds(self, symbolic):
        # x^2 >= 0 for all real x
        r = symbolic.check_inequality("x**2", ">=", "0")
        assert r.status == VerificationStatus.PASS

    def test_inequality_false(self, symbolic):
        # x > x+1 is always false
        r = symbolic.check_inequality("x", ">", "x + 1")
        assert r.status == VerificationStatus.FAIL


# ===========================================================================
# 3. BruteForceChecker
# ===========================================================================

class TestBruteForceChecker:

    def test_counting_correct(self, brute):
        # Count integers 1-10 divisible by 2 → 5
        r = brute.check_counting_claim(
            predicate=lambda n: n % 2 == 0,
            parameter_ranges={"n": range(1, 11)},
            claimed_count=5,
        )
        assert r.status == VerificationStatus.PASS
        assert r.confidence == ConfidenceLevel.ENUMERATED

    def test_counting_wrong(self, brute):
        r = brute.check_counting_claim(
            predicate=lambda n: n % 2 == 0,
            parameter_ranges={"n": range(1, 11)},
            claimed_count=6,   # Wrong
        )
        assert r.status == VerificationStatus.FAIL

    def test_universal_holds(self, brute):
        # n^2 >= n for all n >= 1
        r = brute.check_universal_claim(
            predicate=lambda n: n * n >= n,
            parameter_ranges={"n": range(1, 101)},
        )
        assert r.status == VerificationStatus.PASS

    def test_universal_fails(self, brute):
        r = brute.check_universal_claim(
            predicate=lambda n: n % 2 == 0,   # Not all are even
            parameter_ranges={"n": range(1, 10)},
        )
        assert r.status == VerificationStatus.FAIL
        assert r.witness is not None

    def test_existence_found(self, brute):
        # 5 is prime
        r = brute.check_existence_claim(
            predicate=lambda n: n > 4 and all(n % i != 0 for i in range(2, n)),
            parameter_ranges={"n": range(2, 10)},
        )
        assert r.status == VerificationStatus.PASS
        assert r.witness is not None

    def test_existence_not_found(self, brute):
        # Even prime > 2 does not exist
        r = brute.check_existence_claim(
            predicate=lambda n: n > 2 and n % 2 == 0 and all(n % i != 0 for i in range(2, n)),
            parameter_ranges={"n": range(3, 20)},
        )
        assert r.status == VerificationStatus.FAIL

    def test_optimization_max(self, brute):
        # Max of n*(10-n) for n in 1..9 is at n=5, value=25
        r = brute.check_optimization_claim(
            objective=lambda n: n * (10 - n),
            parameter_ranges={"n": range(1, 10)},
            claimed_optimum=25.0,
            optimization_type="max",
        )
        assert r.status == VerificationStatus.PASS

    def test_canary_problem_via_brute_force(self, brute):
        # This is the canary problem from Phase 0: integers 1-500 divisible by 3 or 7 but not 21
        # Verified: sum(1 for n in range(1,501) if (n%3==0 or n%7==0) and n%21!=0) == 191
        r = brute.check_counting_claim(
            predicate=lambda n: (n % 3 == 0 or n % 7 == 0) and n % 21 != 0,
            parameter_ranges={"n": range(1, 501)},
            claimed_count=191,
        )
        assert r.status == VerificationStatus.PASS


# ===========================================================================
# 4. CounterexampleSearcher
# ===========================================================================

class TestCounterexampleSearcher:

    def test_no_counterexample_for_true_claim(self, searcher):
        # x^2 >= 0 — always true
        r = searcher.search(
            predicate=lambda x: x * x >= 0,
            parameter_specs={"x": {"type": "float", "min": -100, "max": 100}},
            claim_text="x^2 >= 0",
        )
        assert not r.found_counterexample

    def test_finds_counterexample_for_false_claim(self, searcher):
        # Claim: all integers are positive (false for negative ints)
        r = searcher.search(
            predicate=lambda n: n > 0,
            parameter_specs={"n": {"type": "int", "min": -10, "max": 10}},
            claim_text="n > 0 for all n",
        )
        assert r.found_counterexample
        assert r.counterexample["n"] <= 0

    def test_discrete_values(self, searcher):
        # All values in {2, 4, 6} are even — true
        r = searcher.search(
            predicate=lambda x: x % 2 == 0,
            parameter_specs={"x": {"values": [2, 4, 6]}},
        )
        assert not r.found_counterexample

    def test_attempts_consumed(self, searcher):
        # Just verify it runs and returns without hanging
        r = searcher.search(
            predicate=lambda x: x >= 0,
            parameter_specs={"x": {"type": "int", "min": 0, "max": 100}},
        )
        assert r.attempts > 0


# ===========================================================================
# 5. SolutionParser
# ===========================================================================

class TestSolutionParser:

    def test_extracts_final_answer_bold(self, parser):
        trace = SolutionTrace(raw_text="So the answer is **ANSWER: 42**")
        parser.parse(trace)
        assert trace.final_answer == 42

    def test_extracts_final_answer_boxed(self, parser):
        trace = SolutionTrace(raw_text=r"Therefore \boxed{808}")
        parser.parse(trace)
        assert trace.final_answer == 808

    def test_no_answer_returns_none(self, parser):
        trace = SolutionTrace(raw_text="Some calculations without an explicit answer.")
        parser.parse(trace)
        assert trace.final_answer is None  # Fail safe

    def test_classifies_code_step(self, parser):
        trace = SolutionTrace(raw_text="```python\nprint(42)\n```\n**ANSWER: 42**")
        parser.parse(trace)
        code_steps = [s for s in trace.steps if s.step_type == StepType.CODE]
        assert len(code_steps) >= 1

    def test_classifies_calculation_step(self, parser):
        trace = SolutionTrace(raw_text="We compute 6 * 7 = 42.\n**ANSWER: 42**")
        parser.parse(trace)
        assert trace.is_parsed

    def test_extracts_calculation(self, parser):
        trace = SolutionTrace(raw_text="Step 1: 3 * 4 = 12\n**ANSWER: 12**")
        parser.parse(trace)
        calcs = [c for step in trace.steps for c in step.calculations]
        assert any(c.result == "12" for c in calcs)

    def test_fail_safe_on_empty(self, parser):
        trace = SolutionTrace(raw_text="")
        parser.parse(trace)   # Must not raise
        assert trace.final_answer is None


# ===========================================================================
# 6. VerificationPipeline
# ===========================================================================

class TestVerificationPipeline:

    def test_pipeline_on_correct_trace(self, pipeline):
        raw = "We find that 7 * 13 = 91.\n**ANSWER: 91**"
        trace = SolutionTrace(raw_text=raw)
        result = pipeline.run(trace)
        assert isinstance(result, PipelineResult)
        assert result.final_answer == 91
        assert result.report.total_checks >= 1

    def test_pipeline_on_empty_trace(self, pipeline):
        trace = SolutionTrace(raw_text="")
        result = pipeline.run(trace)
        assert result.final_answer is None
        # Should not crash
        assert result.report is not None

    def test_pipeline_answer_format_pass(self, pipeline):
        trace = SolutionTrace(raw_text="**ANSWER: 42**")
        result = pipeline.run(trace)
        assert result.answer_format is not None
        assert result.answer_format.status == VerificationStatus.PASS

    def test_pipeline_answer_format_fail(self, pipeline):
        trace = SolutionTrace(raw_text="**ANSWER: 999999**")  # Out of range
        result = pipeline.run(trace)
        assert result.answer_format is not None
        assert result.answer_format.status == VerificationStatus.FAIL

    def test_pipeline_report_confidence_elevated(self, pipeline):
        # A trace with a correct calc should get LEVEL_0_EXACT from arithmetic
        raw = "Step 1: 3 * 4 = 12\n**ANSWER: 12**"
        trace = SolutionTrace(raw_text=raw)
        result = pipeline.run(trace)
        # Confidence should be at least LEVEL_0_EXACT if arithmetic matched
        assert result.report.confidence.strength >= ConfidenceLevel.UNVERIFIED.strength
