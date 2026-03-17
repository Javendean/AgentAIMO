"""Phase 1A test suite: Canonical Answer Extraction and Validation.

Covers 15+ format variants for ExtractionResult, plus all three
AnswerValidator validation methods and the cross_consistency checker.

Run:
    python -m pytest tests/test_answer_extraction.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.verification.answer_validator import (
    AnswerValidator,
    ExtractionResult,
    extract_canonical_answer,
)
from src.models.verification import ConfidenceLevel
from src.models.trace import VerificationStatus, SolutionTrace
from src.models.problem import Problem, ProblemMetadata, ProblemCategory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def validator():
    return AnswerValidator()


def make_problem(ground_truth: int | None = None) -> Problem:
    return Problem(
        text="Find the answer.",
        metadata=ProblemMetadata(
            source="test",
            problem_id="t1",
            category=ProblemCategory.UNKNOWN,
            difficulty=0.5,
        ),
        ground_truth=ground_truth,
    )


def make_trace(answer: int | None) -> SolutionTrace:
    return SolutionTrace(raw_text="", final_answer=answer)


# ===========================================================================
# 1. extract_canonical — format variants
# ===========================================================================

class TestExtractCanonical:

    # --- Bold closed patterns ---

    def test_bold_clean_integer(self, validator):
        r = validator.extract_canonical("**ANSWER: 42**")
        assert r.value == 42
        assert r.pattern == "bold_closed"
        assert r.confidence == ConfidenceLevel.LEVEL_0_EXACT

    def test_bold_with_leading_reasoning(self, validator):
        r = validator.extract_canonical(
            "After careful analysis...\n\nTherefore **ANSWER: 808**"
        )
        assert r.value == 808

    def test_bold_with_trailing_newline(self, validator):
        r = validator.extract_canonical("**ANSWER: 12345**\n")
        assert r.value == 12345

    def test_bold_zero(self, validator):
        r = validator.extract_canonical("**ANSWER: 0**")
        assert r.value == 0

    def test_bold_max_valid(self, validator):
        r = validator.extract_canonical("**ANSWER: 99999**")
        assert r.value == 99999

    def test_bold_case_insensitive(self, validator):
        r = validator.extract_canonical("**answer: 7**")
        assert r.value == 7

    # --- Bold open (no closing **) ---

    def test_bold_open_eol(self, validator):
        r = validator.extract_canonical("**ANSWER: 333\n")
        assert r.value == 333

    def test_bold_open_eof(self, validator):
        r = validator.extract_canonical("**ANSWER: 999")
        # Falls through bold_closed (no **), bold_open requires \n or $
        assert r.value == 999

    # --- Plain (no bold) ---

    def test_plain_no_bold(self, validator):
        r = validator.extract_canonical("ANSWER: 7\n")
        assert r.value == 7
        assert r.pattern == "plain"

    def test_plain_with_spaces(self, validator):
        r = validator.extract_canonical("ANSWER:   42 \n")
        assert r.value == 42

    # --- LaTeX boxed ---

    def test_boxed_format(self, validator):
        r = validator.extract_canonical(r"Therefore \boxed{808} is correct.")
        assert r.value == 808
        assert r.pattern == "boxed"

    def test_boxed_five_digit(self, validator):
        r = validator.extract_canonical(r"\boxed{54321}")
        assert r.value == 54321

    # --- Rejection cases ---

    def test_reject_over_range(self, validator):
        r = validator.extract_canonical("**ANSWER: 100000**")
        assert r.value is None
        assert r.confidence == ConfidenceLevel.UNVERIFIED

    def test_reject_text_answer(self, validator):
        r = validator.extract_canonical("**ANSWER: forty-two**")
        assert r.value is None

    def test_reject_empty_tag(self, validator):
        r = validator.extract_canonical("**ANSWER: **")
        assert r.value is None

    def test_reject_no_marker(self, validator):
        r = validator.extract_canonical("The answer is probably 42 based on my work.")
        assert r.value is None

    def test_prose_pollution_not_captured(self, validator):
        # Old regex captured "42 because x=2" — new must not
        r = validator.extract_canonical("**ANSWER: 42 because x=2**")
        # Either None (no match at all) or 42 (integer captured before space)
        # What must NOT happen: a string containing prose
        assert r.value != 42 or r.raw_match is None or "because" not in (r.raw_match or "")

    def test_multi_answer_uses_first(self, validator):
        # Two valid answers in text — should take the first match in pattern order
        r = validator.extract_canonical("**ANSWER: 10**\n\nWait actually **ANSWER: 20**")
        assert r.value == 10  # First bold_closed match wins

    def test_leading_whitespace(self, validator):
        r = validator.extract_canonical("\n\n\n**ANSWER: 808**")
        assert r.value == 808

    # --- ExtractionResult API ---

    def test_succeeded_property_true(self, validator):
        r = validator.extract_canonical("**ANSWER: 1**")
        assert r.succeeded is True

    def test_succeeded_property_false(self, validator):
        r = validator.extract_canonical("No answer here")
        assert r.succeeded is False

    def test_str_representation(self, validator):
        r = validator.extract_canonical("**ANSWER: 42**")
        s = str(r)
        assert "42" in s

    # --- Convenience function ---

    def test_extract_canonical_answer_returns_string(self):
        assert extract_canonical_answer("**ANSWER: 7**") == "7"

    def test_extract_canonical_answer_returns_none(self):
        assert extract_canonical_answer("nothing") is None


# ===========================================================================
# 2. validate_format
# ===========================================================================

class TestValidateFormat:

    def test_valid_integer(self, validator):
        vr = validator.validate_format(42)
        assert vr.status == VerificationStatus.PASS
        assert vr.confidence == ConfidenceLevel.LEVEL_0_EXACT

    def test_zero_is_valid(self, validator):
        vr = validator.validate_format(0)
        assert vr.status == VerificationStatus.PASS

    def test_max_boundary(self, validator):
        vr = validator.validate_format(99999)
        assert vr.status == VerificationStatus.PASS

    def test_none_fails(self, validator):
        vr = validator.validate_format(None)
        assert vr.status == VerificationStatus.FAIL

    def test_negative_fails(self, validator):
        vr = validator.validate_format(-1)
        assert vr.status == VerificationStatus.FAIL

    def test_overflow_fails(self, validator):
        vr = validator.validate_format(100000)
        assert vr.status == VerificationStatus.FAIL
        assert vr.confidence == ConfidenceLevel.LEVEL_0_EXACT  # deterministic check

    def test_non_int_fails(self, validator):
        vr = validator.validate_format("42")  # type: ignore
        assert vr.status == VerificationStatus.FAIL


# ===========================================================================
# 3. validate_against_ground_truth
# ===========================================================================

class TestValidateAgainstGroundTruth:

    def test_correct_answer(self, validator):
        problem = make_problem(ground_truth=42)
        vr = validator.validate_against_ground_truth(42, problem)
        assert vr.status == VerificationStatus.PASS
        assert vr.confidence == ConfidenceLevel.LEVEL_0_EXACT
        assert vr.detail["answer"] == 42

    def test_wrong_answer(self, validator):
        problem = make_problem(ground_truth=42)
        vr = validator.validate_against_ground_truth(99, problem)
        assert vr.status == VerificationStatus.FAIL
        assert vr.confidence == ConfidenceLevel.LEVEL_0_EXACT

    def test_no_ground_truth(self, validator):
        problem = make_problem(ground_truth=None)
        vr = validator.validate_against_ground_truth(42, problem)
        assert vr.status == VerificationStatus.SKIPPED
        assert vr.confidence == ConfidenceLevel.UNVERIFIED

    def test_none_answer_with_truth(self, validator):
        problem = make_problem(ground_truth=42)
        vr = validator.validate_against_ground_truth(None, problem)
        assert vr.status == VerificationStatus.FAIL


# ===========================================================================
# 4. validate_cross_consistency
# ===========================================================================

class TestValidateCrossConsistency:

    def test_unanimous(self, validator):
        traces = [make_trace(42)] * 5
        vr = validator.validate_cross_consistency(traces)
        assert vr.status == VerificationStatus.PASS
        assert vr.detail["answer"] == 42
        assert vr.detail["plurality_fraction"] == 1.0

    def test_majority_3_of_5(self, validator):
        traces = [make_trace(42)] * 3 + [make_trace(99)] * 2
        vr = validator.validate_cross_consistency(traces)
        assert vr.status == VerificationStatus.PASS
        assert vr.detail["answer"] == 42

    def test_no_majority_suspicious(self, validator):
        traces = [make_trace(1), make_trace(2), make_trace(3)]
        vr = validator.validate_cross_consistency(traces)
        assert vr.status == VerificationStatus.SUSPICIOUS

    def test_all_none_answers(self, validator):
        traces = [make_trace(None)] * 4
        vr = validator.validate_cross_consistency(traces)
        assert vr.status == VerificationStatus.FAIL

    def test_empty_traces(self, validator):
        vr = validator.validate_cross_consistency([])
        assert vr.status == VerificationStatus.FAIL

    def test_votes_detail_populated(self, validator):
        traces = [make_trace(42)] * 3 + [make_trace(99)]
        vr = validator.validate_cross_consistency(traces)
        assert "42" in vr.detail["votes"]
        assert vr.detail["votes"]["42"] == 3

    def test_mixed_valid_and_none(self, validator):
        # 2 traces have None, 3 have 42 — should still find majority
        traces = [make_trace(42)] * 3 + [make_trace(None)] * 2
        vr = validator.validate_cross_consistency(traces)
        # 3 out of 5 traces provided, 3 valid → 42 is plurality of valid answers
        # But total traces = 5, so 42 has 3/5 = 60% → PASS
        assert vr.detail["answer"] == 42


# ===========================================================================
# 5. ConfidenceLevel ordering
# ===========================================================================

class TestConfidenceLevel:

    def test_level_0_stronger_than_level_1(self):
        from src.models.verification import ConfidenceLevel
        assert ConfidenceLevel.LEVEL_0_EXACT > ConfidenceLevel.LEVEL_1_SYMBOLIC

    def test_level_1_stronger_than_nl(self):
        from src.models.verification import ConfidenceLevel
        assert ConfidenceLevel.LEVEL_1_SYMBOLIC > ConfidenceLevel.NL_JUDGMENT

    def test_unverified_weakest(self):
        from src.models.verification import ConfidenceLevel
        assert ConfidenceLevel.UNVERIFIED < ConfidenceLevel.NL_JUDGMENT

    def test_enumerated_same_strength_as_formal(self):
        from src.models.verification import ConfidenceLevel
        assert ConfidenceLevel.ENUMERATED.strength == ConfidenceLevel.LEVEL_2_FORMAL.strength
