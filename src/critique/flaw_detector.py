"""Offline NL flaw detector for AgentAIMO solution traces.

Implements the flaw taxonomy from the annotated trace files:
    data/research/annotated_traces       (pipe-format, aime_2024_3)
    data/research/annotated_traces.yml   (YAML,        aime_2023_1)

No live model API calls. All detection is regex + heuristic pattern matching.
Runs entirely offline — safe to use inside the Kaggle notebook if needed.

Phase 3 implementation.
"""

from __future__ import annotations

import re
from typing import Optional

from src.models.critique import FlawCode, FlawResult, CritiqueReport

# ---------------------------------------------------------------------------
# Compiled patterns from annotated trace analysis
# ---------------------------------------------------------------------------

# CHANNEL_LEAKAGE / PROTOCOL_TOKEN_LEAKAGE (severity 2)
_CHANNEL_LEAKe = re.compile(
    r"(?:"
    r"(?:^|\s)analysis(?:We|The|I|[A-Z])|"  # 'analysis' prefix token (beginning of sentence)
    r"assistantcommentary\s+to=python|"       # tool marker — can appear anywhere mid-sentence
    r"assistantanalysis\s+to=python"          # variant tool marker
    r")",
    re.IGNORECASE | re.MULTILINE,
)

# MALFORMED_TOOL_CALL (severity 4) — assistantcommentary inside prose
_MALFORMED_TOOL = re.compile(
    r"(?:assistantcommentary|assistantanalysis)\s+to=python\s+code",
    re.IGNORECASE,
)

# MISSING_FINAL_COMMIT (severity 5) — has prose answer phrase but no **ANSWER: N**
# Triggered when a prose answer phrase exists but the strict bolded format does not
_BOLD_ANSWER = re.compile(r"\*\*ANSWER:\s*\d{1,6}\*\*", re.IGNORECASE)
_PROSE_ANSWER = re.compile(
    r"(?:the answer is|answer:|so the answer|therefore the answer)\s*\d{1,6}",
    re.IGNORECASE,
)

# PSEUDO_VERIFICATION (severity 4) — PASSED block with no numeric output shown
_BLOCK_PASSED = re.compile(
    r"\[Block\s+\d+/\d+\]\s+PASSED",
    re.IGNORECASE,
)
_NUMBER_NEAR_PASSED = re.compile(
    r"\[Block\s+\d+/\d+\]\s+PASSED[\s\S]{0,200}\d{3,}",
)

# NON_EXECUTABLE_CODE / code contamination (severity 5)
# A SyntaxError in verification output → prose was injected into code
_SYNTAX_ERROR_IN_OUTPUT = re.compile(
    r"SyntaxError:\s*(?:unterminated|invalid syntax|unexpected|EOL)",
    re.IGNORECASE,
)

# CONTEXT_CONFABULATION (severity 4) — asks for missing prior context
_CONTEXT_CONFAB = re.compile(
    r"(?:we don'?t have|don'?t have (?:earlier|prior|the)|"
    r"need to (?:see|find|get) (?:the earlier|prior|earlier)|"
    r"without (?:earlier|prior) (?:code|results|context)|"
    r"continue from where (?:we|you) left off)",
    re.IGNORECASE,
)

# NONTERMINATING_WORKFLOW (severity 3) — keeps restarting after answer known
_RESTART_KEYWORDS = re.compile(
    r"(?:let'?s (?:re-?derive|restart|redo|start over)|"
    r"going back to|we should re-?compute)",
    re.IGNORECASE,
)

# REDUNDANT_RECOMPUTATION (severity 3) — same function defined multiple times
_FUNC_DEF = re.compile(r"def\s+(\w+)\s*\(", re.MULTILINE)

# PROMPT_LEAKAGE (severity 4) — user instruction text in solution
_PROMPT_LEAK = re.compile(
    r'(?:The user says[:\s]+"|'
    r'Continue from where you left off|'
    r'Do NOT re-derive what you have|'
    r'Use the code results above)',
    re.IGNORECASE,
)

# NO_CODE (severity 4) — verification claimed but no code blocks found
_NO_CODE_MARKER = re.compile(r"NO_CODE:\s*No executable", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _excerpt(text: str, match: re.Match, max_len: int = 70) -> str:
    """Return a short excerpt around a regex match."""
    start = max(0, match.start() - 10)
    end = min(len(text), match.end() + 20)
    raw = text[start:end].replace("\n", " ").strip()
    return raw[:max_len]


# ---------------------------------------------------------------------------
# FlawDetector
# ---------------------------------------------------------------------------

class FlawDetector:
    """Offline pattern-based flaw detector for AIMO solution traces.

    Each detect_* method returns a list of FlawResult (possibly empty).
    detect_all() runs all individual detectors and returns the combined list.

    Design constraints (from .agent/rules/02-math-verification-standards.md):
        - No live model API calls.
        - Never return a false-positive that could cause a correct solution to
          be rejected. All detectors prefer false-negatives over false-positives.
        - Severity follows the annotated trace scale (1-5).
    """

    def detect_channel_leakage(self, solution_text: str) -> list[FlawResult]:
        """Detect `analysis...` / `assistantcommentary` protocol tokens in prose."""
        results = []
        for m in _CHANNEL_LEAKe.finditer(solution_text):
            results.append(FlawResult(
                flaw_code=FlawCode.CHANNEL_LEAKAGE,
                severity=2,
                excerpt=_excerpt(solution_text, m),
                note="Internal protocol token leaked into user-visible reasoning.",
            ))
            break  # flag once per solution; don't flood with every occurrence
        return results

    def detect_malformed_tool_call(self, solution_text: str) -> list[FlawResult]:
        """Detect `assistantcommentary to=python code` embedded in prose."""
        results = []
        for m in _MALFORMED_TOOL.finditer(solution_text):
            results.append(FlawResult(
                flaw_code=FlawCode.MALFORMED_TOOL_CALL,
                severity=4,
                excerpt=_excerpt(solution_text, m),
                note="Tool invocation syntax embedded in plain prose; not executable.",
            ))
            break
        return results

    def detect_missing_final_commit(self, solution_text: str) -> list[FlawResult]:
        """Detect: prose answer phrase exists but no **ANSWER: N** format present.

        Ablation context: this is the #1 reason the model produces 0 extractions
        even when it derives the correct answer internally.
        """
        has_bold = bool(_BOLD_ANSWER.search(solution_text))
        has_prose = bool(_PROSE_ANSWER.search(solution_text))
        if has_prose and not has_bold:
            return [FlawResult(
                flaw_code=FlawCode.MISSING_FINAL_COMMIT,
                severity=5,
                excerpt="(prose answer found but no **ANSWER: N** format)",
                note="Solution contains 'the answer is N' in prose but omits **ANSWER: N** format.",
            )]
        return []

    def detect_pseudo_verification(self, solution_text: str) -> list[FlawResult]:
        """Detect [Block N/N] PASSED without a meaningful numeric result nearby."""
        results = []
        for m in _BLOCK_PASSED.finditer(solution_text):
            # Check if there are 3+ digit numbers within 200 chars after PASSED
            has_number = bool(_NUMBER_NEAR_PASSED.match(solution_text, m.start()))
            if not has_number:
                results.append(FlawResult(
                    flaw_code=FlawCode.PSEUDO_VERIFICATION,
                    severity=4,
                    excerpt=_excerpt(solution_text, m),
                    note="Verification reports PASSED but shows no computed value — rubber-stamp.",
                ))
                break
        return results

    def detect_code_contamination(self, solution_text: str) -> list[FlawResult]:
        """Detect prose-into-code contamination by checking for SyntaxErrors."""
        results = []
        for m in _SYNTAX_ERROR_IN_OUTPUT.finditer(solution_text):
            results.append(FlawResult(
                flaw_code=FlawCode.NON_EXECUTABLE_CODE,
                severity=5,
                excerpt=_excerpt(solution_text, m),
                note="SyntaxError in output strongly suggests prose was injected into code block.",
            ))
            break
        return results

    def detect_context_confabulation(self, solution_text: str) -> list[FlawResult]:
        """Detect model asking for missing prior context on a self-contained problem."""
        results = []
        for m in _CONTEXT_CONFAB.finditer(solution_text):
            results.append(FlawResult(
                flaw_code=FlawCode.CONTEXT_CONFABULATION,
                severity=4,
                excerpt=_excerpt(solution_text, m),
                note="Model requests missing context rather than solving the given problem.",
            ))
            break
        return results

    def detect_prompt_leakage(self, solution_text: str) -> list[FlawResult]:
        """Detect user-instruction text appearing inside the solution."""
        results = []
        for m in _PROMPT_LEAK.finditer(solution_text):
            results.append(FlawResult(
                flaw_code=FlawCode.PROMPT_LEAKAGE,
                severity=4,
                excerpt=_excerpt(solution_text, m),
                note="User-instruction text leaked into the model's reasoning or answer fields.",
            ))
            break
        return results

    def detect_no_code(self, verification_output: str) -> list[FlawResult]:
        """Detect: verification pipeline found no executable code (NO_CODE sentinel)."""
        results = []
        if _NO_CODE_MARKER.search(verification_output):
            results.append(FlawResult(
                flaw_code=FlawCode.PSEUDO_VERIFICATION,
                severity=4,
                excerpt="NO_CODE: No executable Python code blocks found",
                note="Verification was invoked but no valid code was present to execute.",
            ))
        return results

    def detect_redundant_recomputation(self, solution_text: str) -> list[FlawResult]:
        """Detect repeated function definitions — indicator of redundant re-solves."""
        func_names = [m.group(1) for m in _FUNC_DEF.finditer(solution_text)]
        counts = {}
        for name in func_names:
            counts[name] = counts.get(name, 0) + 1
        duplicated = [n for n, c in counts.items() if c >= 3]
        if duplicated:
            return [FlawResult(
                flaw_code=FlawCode.REDUNDANT_RECOMPUTATION,
                severity=3,
                excerpt=f"Functions defined 3+ times: {duplicated[:3]}",
                note="Same function defined multiple times — model is restarting the same computation.",
            )]
        return []

    def detect_all(
        self,
        solution_text: str,
        verification_output: str = "",
    ) -> CritiqueReport:
        """Run all detectors and return a CritiqueReport.

        Args:
            solution_text:       Raw solution text from one attempt.
            verification_output: The attempt's verification_output field (may be empty).

        Returns:
            CritiqueReport aggregating all found flaws.
        """
        flaws: list[FlawResult] = []
        flaws += self.detect_channel_leakage(solution_text)
        flaws += self.detect_malformed_tool_call(solution_text)
        flaws += self.detect_missing_final_commit(solution_text)
        flaws += self.detect_pseudo_verification(solution_text)
        flaws += self.detect_code_contamination(solution_text)
        flaws += self.detect_context_confabulation(solution_text)
        flaws += self.detect_prompt_leakage(solution_text)
        flaws += self.detect_redundant_recomputation(solution_text)
        if verification_output:
            flaws += self.detect_no_code(verification_output)
        return CritiqueReport(solution_text=solution_text, flaws=flaws)
