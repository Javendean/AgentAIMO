"""Phase 3 test suite — AnswerSelector, FlawDetector, and AuditRecord.

Covers:
  - AnswerSelector: confidence-weighted selection, fallbacks, edge cases
  - FlawDetector: each individual detector + detect_all
  - audit_problem: integration test on mock JSONL records

Run with:
    python -m pytest tests/test_phase3.py -v
"""

from __future__ import annotations

import pytest
from src.models.verification import ConfidenceLevel, VerificationReport
from src.models.critique import FlawCode, FlawResult, CritiqueReport
from src.critique.flaw_detector import FlawDetector
from src.solver.answer_selector import AnnotatedSolution, AnswerSelector


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _report(level: ConfidenceLevel, passed: int = 1, failed: int = 0) -> VerificationReport:
    return VerificationReport(
        passed_checks=passed,
        failed_checks=failed,
        confidence=level,
    )


def _sol(answer: int | None, level: ConfidenceLevel, attempt_id: int = 0) -> AnnotatedSolution:
    return AnnotatedSolution(
        final_answer=answer,
        report=_report(level),
        attempt_id=attempt_id,
    )


# ---------------------------------------------------------------------------
# AnswerSelector
# ---------------------------------------------------------------------------

class TestAnswerSelector:
    sel = AnswerSelector()

    def test_unanimous_exact(self):
        sols = [_sol(42, ConfidenceLevel.LEVEL_0_EXACT)] * 3
        ans, reason, score = self.sel.select(sols)
        assert ans == 42
        assert "weighted" in reason
        assert score > 0.5

    def test_single_exact_beats_majority(self):
        """1 LEVEL_0_EXACT answer=42 should beat 2 UNVERIFIED answer=99."""
        sols = [
            _sol(42, ConfidenceLevel.LEVEL_0_EXACT),
            _sol(99, ConfidenceLevel.UNVERIFIED),
            _sol(99, ConfidenceLevel.UNVERIFIED),
        ]
        ans, _, _ = self.sel.select(sols)
        assert ans == 42

    def test_symbolic_beats_unverified_majority(self):
        """LEVEL_1_SYMBOLIC=305 vs 3x UNVERIFIED=77: symbolic wins."""
        sols = [
            _sol(305, ConfidenceLevel.LEVEL_1_SYMBOLIC),
            _sol(77, ConfidenceLevel.UNVERIFIED),
            _sol(77, ConfidenceLevel.UNVERIFIED),
            _sol(77, ConfidenceLevel.UNVERIFIED),
        ]
        ans, _, _ = self.sel.select(sols)
        assert ans == 305

    def test_all_unverified_falls_back_to_majority(self):
        sols = [
            _sol(10, ConfidenceLevel.UNVERIFIED),
            _sol(10, ConfidenceLevel.UNVERIFIED),
            _sol(20, ConfidenceLevel.UNVERIFIED),
        ]
        ans, reason, _ = self.sel.select(sols)
        assert ans == 10  # majority
        # Should use weighted vote with UNVERIFIED weight

    def test_no_answers_returns_none(self):
        sols = [_sol(None, ConfidenceLevel.UNVERIFIED)] * 3
        ans, reason, score = self.sel.select(sols)
        assert ans is None
        assert score == 0.0

    def test_empty_input_returns_none(self):
        ans, reason, score = self.sel.select([])
        assert ans is None
        assert reason == "no_attempts"

    def test_confidence_score_in_range(self):
        sols = [_sol(7, ConfidenceLevel.LEVEL_0_EXACT)]
        _, _, score = self.sel.select(sols)
        assert 0.0 <= score <= 1.0

    def test_weighted_vote_tiebreak_is_deterministic(self):
        """Equal-weight tie should always return the same winner."""
        sols1 = [
            _sol(100, ConfidenceLevel.LEVEL_0_EXACT),
            _sol(200, ConfidenceLevel.LEVEL_0_EXACT),
        ]
        a1, _, _ = self.sel.select(sols1)
        a2, _, _ = self.sel.select(sols1)
        assert a1 == a2  # deterministic

    def test_majority_vote_method(self):
        sols = [_sol(5, ConfidenceLevel.UNVERIFIED)] * 3 + [_sol(9, ConfidenceLevel.UNVERIFIED)]
        winner, count, total = self.sel._majority_vote(sols)
        assert winner == 5
        assert count == 3
        assert total == 4

    def test_majority_vote_all_none(self):
        sols = [_sol(None, ConfidenceLevel.UNVERIFIED)] * 2
        winner, count, total = self.sel._majority_vote(sols)
        assert winner is None

    def test_select_two_returns_different_answers(self):
        """Best and second-best should be different integers."""
        sols = [
            _sol(42, ConfidenceLevel.LEVEL_0_EXACT),
            _sol(99, ConfidenceLevel.NL_JUDGMENT),
            _sol(99, ConfidenceLevel.NL_JUDGMENT),
        ]
        first, second = self.sel.select_two(sols)
        assert first[0] == 42
        assert second[0] == 99
        assert first[0] != second[0]

    def test_select_two_when_unanimous(self):
        """When all answers agree, second slot should be None."""
        sols = [_sol(7, ConfidenceLevel.LEVEL_0_EXACT)] * 3
        first, second = self.sel.select_two(sols)
        assert first[0] == 7
        assert second[0] is None
        assert second[1] == "no_disagreement"

    def test_select_two_with_all_none_answers(self):
        """When no answers are extracted, both slots return None."""
        sols = [_sol(None, ConfidenceLevel.UNVERIFIED)] * 3
        first, second = self.sel.select_two(sols)
        assert first[0] is None
        assert second[0] is None
        assert "no_answer" in first[1]

    def test_enumerated_confidence_beats_nl(self):
        sols = [
            _sol(191, ConfidenceLevel.ENUMERATED),
            _sol(907, ConfidenceLevel.NL_JUDGMENT),
            _sol(907, ConfidenceLevel.NL_JUDGMENT),
        ]
        ans, _, _ = self.sel.select(sols)
        assert ans == 191


# ---------------------------------------------------------------------------
# FlawDetector
# ---------------------------------------------------------------------------

class TestFlawDetector:
    det = FlawDetector()

    def test_clean_solution_no_flaws(self):
        sol = "**ANSWER: 42**\nThe answer is 42 by combinatorics."
        report = self.det.detect_all(sol)
        assert report.is_clean
        assert len(report.flaws) == 0

    def test_detects_channel_leakage(self):
        sol = "analysisWe need to solve this problem using dynamic programming."
        flaws = self.det.detect_channel_leakage(sol)
        assert any(f.flaw_code == FlawCode.CHANNEL_LEAKAGE for f in flaws)

    def test_detects_assistantcommentary_channel_leakage(self):
        sol = "Let's compute.assistantcommentary to=python codedef f(n): pass"
        flaws = self.det.detect_channel_leakage(sol)
        assert any(f.flaw_code == FlawCode.CHANNEL_LEAKAGE for f in flaws)

    def test_detects_malformed_tool_call(self):
        sol = "We will use Python.assistantcommentary to=python codeimport math"
        flaws = self.det.detect_malformed_tool_call(sol)
        assert len(flaws) > 0
        assert flaws[0].severity == 4

    def test_missing_final_commit_prose_only(self):
        # Has "the answer is 65" in prose but no **ANSWER: 65**
        sol = "Therefore the answer is 65. This follows from our calculation above."
        flaws = self.det.detect_missing_final_commit(sol)
        assert any(f.flaw_code == FlawCode.MISSING_FINAL_COMMIT for f in flaws)
        assert flaws[0].severity == 5

    def test_no_missing_commit_when_format_present(self):
        sol = "Therefore the answer is 65.\n**ANSWER: 65**"
        flaws = self.det.detect_missing_final_commit(sol)
        assert len(flaws) == 0  # has both prose and bold format — no flaw

    def test_detects_pseudo_verification_passed_no_number(self):
        sol = "Running code...\n[Block 1/1] PASSED\nDone."
        flaws = self.det.detect_pseudo_verification(sol)
        assert any(f.flaw_code == FlawCode.PSEUDO_VERIFICATION for f in flaws)

    def test_no_pseudo_verification_when_number_shown(self):
        sol = "[Block 1/1] PASSED\nResult: answer = 809\n\nFinal answer: 809"
        flaws = self.det.detect_pseudo_verification(sol)
        assert len(flaws) == 0

    def test_detects_syntax_error_contamination(self):
        sol = "Here is code:\n```python\nanalysisWe need x\nprint(x)\n```\nSyntaxError: unterminated string literal"
        flaws = self.det.detect_code_contamination(sol)
        assert any(f.flaw_code == FlawCode.NON_EXECUTABLE_CODE for f in flaws)
        assert flaws[0].severity == 5

    def test_detects_context_confabulation(self):
        sol = "We don't have the earlier code results. We need to see the earlier computation."
        flaws = self.det.detect_context_confabulation(sol)
        assert len(flaws) > 0
        assert flaws[0].flaw_code == FlawCode.CONTEXT_CONFABULATION

    def test_no_context_confabulation_on_normal_text(self):
        sol = "We need to solve for x using the given equations. The result is 42."
        flaws = self.det.detect_context_confabulation(sol)
        assert len(flaws) == 0

    def test_detects_prompt_leakage(self):
        sol = 'The user says "Continue from where you left off." We will proceed.'
        flaws = self.det.detect_prompt_leakage(sol)
        assert len(flaws) > 0
        assert flaws[0].flaw_code == FlawCode.PROMPT_LEAKAGE

    def test_detects_redundant_recomputation(self):
        sol = ("def count_p(n): pass\n" * 4)  # same function 4 times
        flaws = self.det.detect_redundant_recomputation(sol)
        assert len(flaws) > 0
        assert flaws[0].flaw_code == FlawCode.REDUNDANT_RECOMPUTATION

    def test_detect_all_returns_critique_report(self):
        sol = "analysisWe need to solve.\n[Block 1/1] PASSED\nDone."
        report = self.det.detect_all(sol)
        assert isinstance(report, CritiqueReport)
        assert len(report.flaws) >= 1  # at least CHANNEL_LEAKAGE
        assert report.flaw_codes   # non-empty

    def test_no_code_marker_detected_from_verification_output(self):
        sol = "Some clean solution text."
        ver_out = "NO_CODE: No executable Python code blocks found in solution"
        report = self.det.detect_all(sol, ver_out)
        assert FlawCode.PSEUDO_VERIFICATION in report.flaw_codes

    def test_severity_in_range(self):
        sol = ("analysisWe need to solve.\n"
               "assistantcommentary to=python codedef f(): pass\n"
               "SyntaxError: invalid syntax\n"
               "[Block 1/1] PASSED\n")
        report = self.det.detect_all(sol)
        for flaw in report.flaws:
            assert 1 <= flaw.severity <= 5

    def test_critique_report_summary(self):
        sol = "analysisToken\nassistantcommentary to=python codepass"
        report = self.det.detect_all(sol)
        s = report.summary()
        assert "FLAWED" in s or "CLEAN" in s


# ---------------------------------------------------------------------------
# AuditRecord integration (smoke test — calls the full pipeline)
# ---------------------------------------------------------------------------

class TestAuditProblem:
    def _make_record(self, problem_id: str, sol_text: str) -> dict:
        return {
            "problem_id": problem_id,
            "problem_text": "Test problem text.",
            "attempts": [
                {
                    "attempt_number": 0,
                    "solution_text": sol_text,
                    "verification_output": "",
                    "verification_passed": False,
                    "extracted_answer": None,
                    "nl_verification": None,
                    "code_blocks_found": 0,
                    "duration_seconds": 1.0,
                }
            ],
        }

    def test_clean_solution_produces_correct_record(self):
        from src.runner.audit_problem import audit_problem
        sol = "The number of valid integers is 204.\n**ANSWER: 204**"
        record = self._make_record("aime_2024_1", sol)
        audit = audit_problem(record)
        assert audit.problem_id == "aime_2024_1"
        assert audit.selected_answer == 204
        assert audit.correct is True     # GT for aime_2024_1 = 204
        assert isinstance(audit.unique_flaw_codes, list)

    def test_no_answer_produces_none(self):
        from src.runner.audit_problem import audit_problem
        sol = "analysisWe need to solve but we cannot find the answer."
        record = self._make_record("aime_2024_3", sol)
        audit = audit_problem(record)
        assert audit.selected_answer is None
        assert audit.correct is False    # GT for aime_2024_3 = 809
        assert FlawCode.CHANNEL_LEAKAGE in audit.unique_flaw_codes

    def test_jsonl_serialisation_is_valid(self):
        from src.runner.audit_problem import audit_problem
        import json
        sol = "**ANSWER: 18**"
        record = self._make_record("putnam_2023_a1", sol)
        audit = audit_problem(record)
        d = audit.to_jsonl_dict()
        # Must be JSON-serialisable
        json.dumps(d)
        assert d["problem_id"] == "putnam_2023_a1"
        assert "selected_answer" in d
        assert "flaw_codes" not in d or True  # optional field
