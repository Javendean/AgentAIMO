"""Tests for shared data models."""

import unittest
from dataclasses import FrozenInstanceError

from src.models import (
    ProblemCategory, ProblemMetadata, Problem,
    StepType, ExtractedCalculation, SolutionStep, SolutionTrace,
    ConfidenceLevel, VerificationMethod, VerificationResult,
    ArithmeticCheckResult, SymbolicCheckResult, BruteForceResult,
    CounterexampleResult, VerificationReport,
    CritiqueSeverity, CritiqueItem, Critique, AnnotatedSolution, HumanReviewItem,
    SchemaTrigger, SchemaStep, SchemaValidation, Schema,
    APICallRecord, CostSummary
)


class TestProblemModels(unittest.TestCase):
    def test_enums(self):
        self.assertEqual(ProblemCategory.ALGEBRA.value, "algebra")

    def test_problem_instantiation_and_validation(self):
        metadata = ProblemMetadata(
            source="aimo",
            problem_id="p1",
            ground_truth_answer=42
        )
        problem = Problem(text="Solve this", metadata=metadata)

        self.assertEqual(problem.text, "Solve this")
        self.assertEqual(problem.metadata.ground_truth_answer, 42)

    def test_problem_validation_rejection(self):
        metadata = ProblemMetadata(source="aimo", problem_id="p1")

        with self.assertRaises(ValueError):
            Problem(text="", metadata=metadata)

        bad_metadata = ProblemMetadata(source="aimo", problem_id="p2", ground_truth_answer=-1)
        with self.assertRaises(ValueError):
            Problem(text="Solve this", metadata=bad_metadata)

        bad_metadata2 = ProblemMetadata(source="aimo", problem_id="p3", ground_truth_answer=100000)
        with self.assertRaises(ValueError):
            Problem(text="Solve this", metadata=bad_metadata2)

    def test_frozen_dataclasses(self):
        metadata = ProblemMetadata(source="aimo", problem_id="p1")
        problem = Problem(text="Solve this", metadata=metadata)

        with self.assertRaises(FrozenInstanceError):
            problem.text = "New text"

        with self.assertRaises(FrozenInstanceError):
            metadata.source = "new_source"


class TestSolutionModels(unittest.TestCase):
    def test_enums(self):
        self.assertEqual(StepType.ARITHMETIC.value, "arithmetic")

    def test_solution_properties(self):
        trace = SolutionTrace(problem_id="p1", raw_text="text")
        self.assertFalse(trace.is_parsed)
        self.assertFalse(trace.has_valid_answer)

        trace.steps.append(SolutionStep(index=0, text="step 1"))
        self.assertTrue(trace.is_parsed)

        trace.final_answer = 42
        self.assertTrue(trace.has_valid_answer)

        trace.final_answer = -1
        self.assertFalse(trace.has_valid_answer)

        trace.final_answer = 100000
        self.assertFalse(trace.has_valid_answer)

        trace.final_answer = "42"  # Not an int
        self.assertFalse(trace.has_valid_answer)


class TestVerificationModels(unittest.TestCase):
    def test_enums(self):
        self.assertEqual(ConfidenceLevel.LEVEL_0_EXACT.value, "exact_match")
        self.assertEqual(VerificationMethod.EXACT_MATCH.value, "exact_match")

    def test_report_properties(self):
        report = VerificationReport(problem_id="p1")
        self.assertEqual(report.pass_rate, 0.0)
        self.assertFalse(report.has_failures)

        report.total_checks_passed = 3
        report.total_checks_failed = 1
        self.assertEqual(report.pass_rate, 0.75)
        self.assertTrue(report.has_failures)


class TestCritiqueModels(unittest.TestCase):
    def test_enums(self):
        self.assertEqual(CritiqueSeverity.FATAL.value, "fatal")

    def test_critique_properties(self):
        critique = Critique(problem_id="p1", attempt_index=0, critic_model="m1")
        self.assertFalse(critique.has_fatal_flaws)

        critique.items.append(CritiqueItem(
            step_index=0, severity=CritiqueSeverity.FATAL, category="c", description="d"
        ))
        self.assertTrue(critique.has_fatal_flaws)
        self.assertEqual(len(critique.fatal_items), 1)
        self.assertEqual(len(critique.major_items), 0)

        critique.items.append(CritiqueItem(
            step_index=1, severity=CritiqueSeverity.MAJOR, category="c", description="d"
        ))
        self.assertEqual(len(critique.major_items), 1)

    def test_annotated_solution_properties(self):
        sol = AnnotatedSolution(problem_id="p1", attempt_index=0, final_answer=42)
        self.assertTrue(sol.critics_agree)
        self.assertFalse(sol.deterministic_and_nl_agree)

        c1 = Critique(problem_id="p1", attempt_index=0, critic_model="m1", overall_judgment="good")
        c2 = Critique(problem_id="p1", attempt_index=0, critic_model="m2", overall_judgment="bad")
        sol.critiques = [c1, c2]
        self.assertFalse(sol.critics_agree)

        c2.overall_judgment = "good"
        self.assertTrue(sol.critics_agree)

        report = VerificationReport(problem_id="p1")
        report.total_checks_failed = 0
        sol.verification_report = report
        self.assertTrue(sol.deterministic_and_nl_agree)


class TestSchemaModels(unittest.TestCase):
    def test_schema_properties(self):
        validation = SchemaValidation()
        self.assertFalse(validation.is_validated)
        self.assertEqual(validation.validation_delta, 0.0)

        validation.validation_problems_tested = 5
        validation.validation_accuracy_with = 0.8
        validation.validation_accuracy_without = 0.5
        self.assertTrue(validation.is_validated)
        self.assertAlmostEqual(validation.validation_delta, 0.3)


class TestCostModels(unittest.TestCase):
    def test_cost_properties(self):
        record = APICallRecord(
            model_name="gpt-4", endpoint="/v1/chat", tokens_in=10, tokens_out=20, cost_usd=0.1, wall_time_seconds=1.0
        )
        self.assertEqual(record.total_tokens, 30)

if __name__ == '__main__':
    unittest.main()
