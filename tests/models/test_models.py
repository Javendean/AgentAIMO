"""Tests for the data models."""

import pytest

from src.models.problem import Problem, ProblemMetadata, ProblemCategory
from src.models.solution import SolutionTrace, SolutionStep, StepType, ExtractedCalculation
from src.models.verification import ConfidenceLevel, VerificationReport, Critique, SchemaValidation


class TestProblem:
    def test_valid_problem_creation(self):
        """Test creating a valid Problem."""
        metadata = ProblemMetadata(
            source="test", problem_id="1", category=ProblemCategory.ALGEBRA, difficulty=0.5
        )
        problem = Problem(text="2 + 2 = ?", metadata=metadata, ground_truth=4)
        assert problem.text == "2 + 2 = ?"
        assert problem.metadata.source == "test"
        assert problem.ground_truth == 4

    def test_empty_text_raises(self):
        """Test that empty problem text raises a ValueError."""
        metadata = ProblemMetadata(
            source="test", problem_id="1", category=ProblemCategory.ALGEBRA, difficulty=0.5
        )
        with pytest.raises(ValueError, match="Problem text cannot be empty"):
            Problem(text="", metadata=metadata, ground_truth=4)
        with pytest.raises(ValueError, match="Problem text cannot be empty"):
            Problem(text="   ", metadata=metadata, ground_truth=4)

    def test_answer_out_of_range_raises(self):
        """Test that an answer out of the 0-99999 range raises a ValueError."""
        metadata = ProblemMetadata(
            source="test", problem_id="1", category=ProblemCategory.ALGEBRA, difficulty=0.5
        )
        with pytest.raises(ValueError, match="Answer must be an integer from 0-99999"):
            Problem(text="Test", metadata=metadata, ground_truth=-1)
        with pytest.raises(ValueError, match="Answer must be an integer from 0-99999"):
            Problem(text="Test", metadata=metadata, ground_truth=100000)

    def test_frozen_immutable(self):
        """Test that Problem and ProblemMetadata are immutable."""
        metadata = ProblemMetadata(
            source="test", problem_id="1", category=ProblemCategory.ALGEBRA, difficulty=0.5
        )
        problem = Problem(text="Test", metadata=metadata, ground_truth=4)

        from dataclasses import FrozenInstanceError
        with pytest.raises(FrozenInstanceError):
            problem.text = "New text"

        with pytest.raises(FrozenInstanceError):
            problem.metadata.source = "new_source"


class TestSolutionTrace:
    def test_valid_trace_creation(self):
        """Test creating a valid SolutionTrace."""
        step = SolutionStep(step_num=1, text="Step 1", step_type=StepType.LOGIC)
        trace = SolutionTrace(raw_text="Step 1", steps=[step], final_answer=5)
        assert trace.raw_text == "Step 1"
        assert len(trace.steps) == 1
        assert trace.final_answer == 5

    def test_is_parsed_property(self):
        """Test the is_parsed property."""
        unparsed_trace = SolutionTrace(raw_text="Unparsed text")
        assert not unparsed_trace.is_parsed

        step = SolutionStep(step_num=1, text="Step 1", step_type=StepType.LOGIC)
        parsed_trace = SolutionTrace(raw_text="Step 1", steps=[step])
        assert parsed_trace.is_parsed

    def test_has_valid_answer_property(self):
        """Test the has_valid_answer property."""
        trace_no_answer = SolutionTrace(raw_text="Test")
        assert not trace_no_answer.has_valid_answer

        trace_valid = SolutionTrace(raw_text="Test", final_answer=123)
        assert trace_valid.has_valid_answer

    def test_invalid_answer_detected(self):
        """Test that an invalid answer makes has_valid_answer return False."""
        trace_negative = SolutionTrace(raw_text="Test", final_answer=-5)
        assert not trace_negative.has_valid_answer

        trace_too_large = SolutionTrace(raw_text="Test", final_answer=100000)
        assert not trace_too_large.has_valid_answer


class TestConfidenceLevel:
    def test_all_levels_exist(self):
        """Test that all confidence levels exist."""
        expected_levels = {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}
        actual_levels = {level.name for level in ConfidenceLevel}
        assert expected_levels == actual_levels


class TestVerificationReport:
    def test_pass_rate_calculation(self):
        """Test pass_rate property."""
        report = VerificationReport(passed_checks=8, failed_checks=2)
        assert report.pass_rate == 0.8

    def test_has_failures_property(self):
        """Test has_failures property."""
        clean_report = VerificationReport(passed_checks=10, failed_checks=0)
        assert not clean_report.has_failures

        failed_report = VerificationReport(passed_checks=5, failed_checks=1)
        assert failed_report.has_failures

    def test_empty_report_defaults(self):
        """Test defaults and pass_rate for an empty report."""
        report = VerificationReport()
        assert report.passed_checks == 0
        assert report.failed_checks == 0
        assert report.confidence == ConfidenceLevel.UNKNOWN
        assert report.pass_rate == 0.0
        assert not report.has_failures


class TestCritique:
    def test_has_fatal_flaws(self):
        """Test has_fatal_flaws property."""
        clean_critique = Critique()
        assert not clean_critique.has_fatal_flaws

        flawed_critique = Critique(fatal_flaws=["Logic error in step 2."])
        assert flawed_critique.has_fatal_flaws

    def test_critics_agree_property(self):
        """Test critics_agree property."""
        agreeing_critique = Critique(critic_agreements=5, critic_disagreements=2)
        assert agreeing_critique.critics_agree

        disagreeing_critique = Critique(critic_agreements=2, critic_disagreements=5)
        assert not disagreeing_critique.critics_agree

        tied_critique = Critique(critic_agreements=3, critic_disagreements=3)
        assert not tied_critique.critics_agree


class TestSchemaValidation:
    def test_is_validated_logic(self):
        """Test is_validated_logic property."""
        validation_pass = SchemaValidation(problem_count=10)
        assert validation_pass.is_validated_logic

        validation_pass_more = SchemaValidation(problem_count=15)
        assert validation_pass_more.is_validated_logic

    def test_insufficient_problems_not_validated(self):
        """Test that insufficient problems fails validation."""
        validation_fail = SchemaValidation(problem_count=9)
        assert not validation_fail.is_validated_logic

        validation_fail_empty = SchemaValidation(problem_count=0)
        assert not validation_fail_empty.is_validated_logic
