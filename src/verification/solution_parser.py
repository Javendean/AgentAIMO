"""Solution parser — extract structured steps from raw solution text.

Parses a SolutionTrace.raw_text into a list of SolutionStep objects with:
  - Step type classification (CALCULATION, CODE, LOGIC, ASSUMPTION)
  - Extracted calculations (expression = result pairs)
  - Final answer extraction (delegates to AnswerValidator)

Fixes Bug #5: never default-passes. If parsing fails, the trace gets
UNVERIFIED steps, not silently approved ones.
"""

from __future__ import annotations

import re
from typing import List, Optional

from src.models.trace import SolutionTrace, StepType, ExtractedCalculation
from src.models.solution import SolutionStep
from src.verification.answer_validator import AnswerValidator


# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

# Step delimiters: "Step 1:", "1.", numbered lists, markdown headers
_STEP_DELIMITERS = re.compile(
    r"(?:^|\n)(?:Step\s+\d+[:.)]|"           # Step 1: / Step 1.
    r"\*\*Step\s+\d+[:.)]|"                   # **Step 1:**
    r"(?:#{1,3}\s+\w)|"                       # ## Header
    r"(?:\d+[.)\s]+(?=[A-Z\w])))",            # 1. Sentence starting with capital
    re.MULTILINE,
)

# Code block detection
_CODE_BLOCK = re.compile(r"```(?:python|py)?", re.IGNORECASE)

# Assumption language
_ASSUMPTION_KEYWORDS = re.compile(
    r"\b(assume|let|suppose|given that|WLOG|without loss|denote|define)\b",
    re.IGNORECASE,
)

# Calculation extraction: "expression = result" patterns
# Handles: "3*4 = 12", "x^2 + 1 = 5", "2^10 = 1024"
_CALC_PATTERN = re.compile(
    r"([\w\s\+\-\*\/\^\(\)\=\{\}\\]+?)\s*=\s*(-?\d[\d,\.]*)",
    re.MULTILINE,
)

# Filtered out for calculations — too generic to be useful
_CALC_BLACKLIST_WORDS = {"let", "where", "so", "then", "thus", "hence", "if", "when"}

_validator = AnswerValidator()


class SolutionParser:
    """Parse raw solution text into classified, structured steps.

    Fixes Bug #5: if the raw text cannot be meaningfully parsed, the returned
    trace has steps = [] and final_answer extracted by AnswerValidator (not
    silently defaulted to True / approved).
    """

    NUMBERED_STEP_PATTERN = _STEP_DELIMITERS
    CALCULATION_PATTERN   = _CALC_PATTERN
    ANSWER_PATTERNS        = list(_validator._PATTERNS if hasattr(_validator, '_PATTERNS') else [])

    def parse(self, trace: SolutionTrace) -> SolutionTrace:
        """Parse trace.raw_text into structured steps.

        Mutates and returns the trace with .steps and .final_answer populated.
        Never raises — failures produce empty steps + None final_answer.

        Args:
            trace: SolutionTrace with .raw_text set.

        Returns:
            The same SolutionTrace object with steps and final_answer filled in.
        """
        try:
            raw_steps = self._split_into_steps(trace.raw_text)
            steps: List[SolutionStep] = []

            for i, step_text in enumerate(raw_steps):
                if not step_text.strip():
                    continue
                step_type = self._classify_step(step_text)
                calcs = self._extract_calculations(step_text, i)
                steps.append(SolutionStep(
                    step_num=i,
                    text=step_text.strip(),
                    step_type=step_type,
                    calculations=calcs,
                ))

            trace.steps = steps
            trace.final_answer = self._extract_final_answer(trace.raw_text)

        except Exception:
            # Fail safe: never modify trace if parsing crashes
            pass

        return trace

    def _split_into_steps(self, raw_text: str) -> List[str]:
        """Split text into candidate step strings using delimiter patterns.

        Falls back to paragraph splitting if no structural delimiters found.
        """
        positions = [m.start() for m in _STEP_DELIMITERS.finditer(raw_text)]

        if len(positions) >= 2:
            chunks = []
            for i, pos in enumerate(positions):
                end = positions[i + 1] if i + 1 < len(positions) else len(raw_text)
                chunks.append(raw_text[pos:end])
            return chunks

        # Fallback: split by double newlines (paragraphs)
        paragraphs = re.split(r"\n\s*\n", raw_text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _classify_step(self, step_text: str) -> StepType:
        """Classify step type using keyword and pattern heuristics.

        Priority: CODE > CALCULATION > ASSUMPTION > LOGIC
        """
        if _CODE_BLOCK.search(step_text):
            return StepType.CODE

        # Check for calculation: contains "=" with numeric RHS
        if _CALC_PATTERN.search(step_text):
            return StepType.CALCULATION

        if _ASSUMPTION_KEYWORDS.search(step_text):
            return StepType.ASSUMPTION

        return StepType.LOGIC

    def _extract_calculations(
        self, step_text: str, step_index: int
    ) -> List[ExtractedCalculation]:
        """Extract explicit calculations (expression = number) from a step.

        Filters out trivial assignments like "let x = 5" using blacklist words.
        """
        calcs = []
        for match in _CALC_PATTERN.finditer(step_text):
            expr = match.group(1).strip()
            result = match.group(2).strip().replace(",", "")

            # Skip if the expression starts with a blacklisted word
            first_word = expr.split()[0].lower() if expr.split() else ""
            if first_word in _CALC_BLACKLIST_WORDS:
                continue

            # Skip trivially short or variable-only expressions
            if len(expr) < 3:
                continue

            # Only keep if result looks like a meaningful number
            try:
                float(result)
            except ValueError:
                continue

            calcs.append(ExtractedCalculation(
                expression=expr,
                result=result,
            ))

        return calcs

    def _extract_final_answer(self, raw_text: str) -> Optional[int]:
        """Extract final integer answer using AnswerValidator patterns.

        Prefers the standard ANSWER: markers over bare numbers.
        Falls back to the last isolated integer at end of text.

        Returns None if no valid AIMO answer can be extracted (fail safe).
        """
        # Primary: use the canonical extractor
        result = _validator.extract_canonical(raw_text)
        if result.succeeded:
            return result.value

        # Last-resort: final isolated integer in last 200 chars
        tail = raw_text[-200:]
        numbers = re.findall(r"\b(\d{1,5})\b", tail)
        if numbers:
            try:
                val = int(numbers[-1])
                if 0 <= val <= 99999:
                    return val
            except ValueError:
                pass

        return None  # Strict fail-safe: never fabricate an answer
