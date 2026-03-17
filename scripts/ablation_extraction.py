#!/usr/bin/env python3
"""Phase 2 Ablation Runner — Old vs New Answer Extraction.

Scores both submission JSONL files with:
  - OLD extractor (prose-permissive regex, as originally in prompts.py)
  - NEW extractor (AnswerValidator.extract_canonical — integer-only)

Then compares majority-vote results against the known ground-truth answers
to quantify the extraction improvement.

Usage:
    python scripts/ablation_extraction.py

Output:
    Prints a per-problem table + aggregate metrics.
    Writes data/ablation_results.json for further analysis.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.verification.answer_validator import AnswerValidator

# ---------------------------------------------------------------------------
# Ground truth for AIME 2024 I + 2023 I, Putnam 2023 A1, IMO 2023.
# These are all publicly available. Competition answers are integers.
# ---------------------------------------------------------------------------

GROUND_TRUTH: dict[str, int] = {
    # AIME 2024 I  (public)
    "aime_2024_1":   204,   # Aya walk problem: 204 minutes
    "aime_2024_2":    25,   # xy=25
    "aime_2024_3":   116,   # Known answer
    "aime_2024_4":    65,   # Probability problem
    "aime_2024_5":   104,   # Known answer
    # AIME 2023 I  (public)
    "aime_2023_1":   907,   # m+n=907
    "aime_2023_10":  772,   # Known answer
    # Putnam 2023
    "putnam_2023_a1": 18,
    # IMO 2023 — non-integer answers, cannot score integer extraction
    "imo_2023_1":   None,
    "imo_2023_2":   None,
}

# ---------------------------------------------------------------------------
# Old extractor — mirrors the BROKEN original regex in prompts.py
# Captures prose after "ANSWER:" including trailing words
# ---------------------------------------------------------------------------

_OLD_BOLD_RE    = re.compile(r"\*\*ANSWER:\s*(.+?)\*\*", re.IGNORECASE | re.DOTALL)
_OLD_PLAIN_RE   = re.compile(r"ANSWER:\s*(.+?)(?:\n|$)", re.IGNORECASE)
_OLD_BOXED_RE   = re.compile(r"\\boxed\{(.+?)\}", re.DOTALL)


def extract_old(solution_text: str) -> str | None:
    """Old permissive extraction — equivalent to the pre-Phase-0 regex."""
    m = _OLD_BOLD_RE.search(solution_text)
    if m:
        return m.group(1).strip()
    m = _OLD_PLAIN_RE.search(solution_text)
    if m:
        return m.group(1).strip()
    m = _OLD_BOXED_RE.search(solution_text)
    if m:
        return m.group(1).strip()
    return None


# ---------------------------------------------------------------------------
# New extractor
# ---------------------------------------------------------------------------

_validator = AnswerValidator()


def extract_new(solution_text: str) -> int | None:
    """New integer-only extraction via AnswerValidator."""
    result = _validator.extract_canonical(solution_text)
    return result.value if result.succeeded else None


# ---------------------------------------------------------------------------
# Majority vote helper
# ---------------------------------------------------------------------------

def majority_vote_int(answers: list[int | None]) -> int | None:
    """Return the plurality integer answer (None if all failed)."""
    valid = [a for a in answers if a is not None]
    if not valid:
        return None
    counts = Counter(valid)
    return counts.most_common(1)[0][0]


def majority_vote_str(answers: list[str | None]) -> str | None:
    """Return the plurality string answer."""
    valid = [a for a in answers if a is not None]
    if not valid:
        return None
    counts = Counter(valid)
    return counts.most_common(1)[0][0]


# ---------------------------------------------------------------------------
# Per-problem analysis result
# ---------------------------------------------------------------------------

@dataclass
class ProblemAblation:
    problem_id: str
    source: str
    ground_truth: int | None        # None for non-integer-answer problems
    num_attempts: int
    # Old extractor
    old_raw_answers: list           # Raw strings captured by old regex
    old_majority: str | None        # Old majority-vote string result
    old_correct: bool | None        # None = can't score (non-integer problem)
    old_extract_rate: float         # Fraction of attempts where old got ANY answer
    # New extractor
    new_raw_answers: list           # Integer answers from new validator (None = failed)
    new_majority: int | None        # New majority-vote integer
    new_correct: bool | None        # None = can't score
    new_extract_rate: float         # Fraction of attempts where new got ANY answer
    # Delta
    improved: bool                  # New correct where old was wrong (or None)
    regressed: bool                 # Old correct where new is wrong


# ---------------------------------------------------------------------------
# Core ablation logic
# ---------------------------------------------------------------------------

def analyze_record(record: dict) -> ProblemAblation:
    pid = record["problem_id"]
    attempts_key = "attempts" if "attempts" in record else "meaningful_attempts"
    attempts = record.get(attempts_key, [])

    gt = GROUND_TRUTH.get(pid)

    old_answers, new_answers = [], []

    for attempt in attempts:
        sol = attempt.get("solution_text", "") or ""
        old_answers.append(extract_old(sol))
        new_answers.append(extract_new(sol))

    n = max(len(attempts), 1)
    old_extract_rate = sum(1 for a in old_answers if a is not None) / n
    new_extract_rate = sum(1 for a in new_answers if a is not None) / n

    old_majority = majority_vote_str(old_answers)
    new_majority = majority_vote_int(new_answers)

    # Score old: try to parse as single integer
    def score_old(maj: str | None, truth: int | None) -> bool | None:
        if truth is None or maj is None:
            return None
        # Try to find the integer in the string
        nums = re.findall(r"\b(\d{1,6})\b", maj)
        if not nums:
            return False
        # If majority string IS just a number, compare directly
        try:
            val = int(nums[0])
            return val == truth
        except ValueError:
            return False

    # Score new: direct integer comparison
    def score_new(maj: int | None, truth: int | None) -> bool | None:
        if truth is None:
            return None
        if maj is None:
            return False
        return maj == truth

    old_correct = score_old(old_majority, gt)
    new_correct = score_new(new_majority, gt)

    # Delta logic
    # improved: new is correct AND (old was wrong or None)
    improved = bool(new_correct is True and old_correct is not True)
    # regressed: old was correct AND new is wrong
    regressed = bool(old_correct is True and new_correct is not True)

    return ProblemAblation(
        problem_id=pid,
        source=record.get("source", "?"),
        ground_truth=gt,
        num_attempts=len(attempts),
        old_raw_answers=[str(a)[:60] if a else None for a in old_answers],
        old_majority=str(old_majority)[:80] if old_majority else None,
        old_correct=old_correct,
        old_extract_rate=old_extract_rate,
        new_raw_answers=new_answers,
        new_majority=new_majority,
        new_correct=new_correct,
        new_extract_rate=new_extract_rate,
        improved=improved,
        regressed=regressed,
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_results(label: str, results: list[ProblemAblation]):
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")

    scoreable = [r for r in results if r.ground_truth is not None]
    non_scoreable = [r for r in results if r.ground_truth is None]

    # Per-problem table
    hdr = f"{'Problem':<20} {'GT':>6} {'Old Ans':>30} {'✔Old':>5} {'New Ans':>7} {'✔New':>5} {'Δ':>4}"
    print(hdr)
    print("-" * len(hdr))

    for r in results:
        gt_s = str(r.ground_truth) if r.ground_truth is not None else "N/A"
        old_s = (str(r.old_majority)[:28] if r.old_majority else "-")
        new_s = (str(r.new_majority) if r.new_majority is not None else "-")

        def sym(v):
            if v is True: return "YES"
            if v is False: return " NO"
            return "  ~"

        delta = ""
        if r.improved: delta = "++"
        elif r.regressed: delta = "--"

        print(f"{r.problem_id:<20} {gt_s:>6} {old_s:>30} {sym(r.old_correct):>5} {new_s:>7} {sym(r.new_correct):>5} {delta:>4}")

    if scoreable:
        print()
        old_scored  = [r for r in scoreable if r.old_correct is not None]
        new_scored  = [r for r in scoreable if r.new_correct is not None]
        old_correct = sum(1 for r in scoreable if r.old_correct is True)
        new_correct = sum(1 for r in scoreable if r.new_correct is True)
        n = len(scoreable)

        print(f"\n  Scoreable problems:  {n}")
        print(f"  Old correct:         {old_correct}/{n}  ({old_correct/n*100:.0f}%)")
        print(f"  New correct:         {new_correct}/{n}  ({new_correct/n*100:.0f}%)")
        print(f"  Improved  (+):       {sum(1 for r in scoreable if r.improved)}")
        print(f"  Regressed (-):       {sum(1 for r in scoreable if r.regressed)}")
        avg_old_er = sum(r.old_extract_rate for r in results) / max(len(results), 1)
        avg_new_er = sum(r.new_extract_rate for r in results) / max(len(results), 1)
        print(f"  Old extract rate:    {avg_old_er*100:.0f}%  (fraction of attempts with any answer)")
        print(f"  New extract rate:    {avg_new_er*100:.0f}%")

    if non_scoreable:
        print(f"\n  Non-integer-answer problems (not scored): {[r.problem_id for r in non_scoreable]}")

    return {
        "label": label,
        "scoreable_n": len(scoreable),
        "old_correct": sum(1 for r in scoreable if r.old_correct is True),
        "new_correct": sum(1 for r in scoreable if r.new_correct is True),
        "improved": sum(1 for r in scoreable if r.improved),
        "regressed": sum(1 for r in scoreable if r.regressed),
        "avg_old_extract_rate": sum(r.old_extract_rate for r in results) / max(len(results), 1),
        "avg_new_extract_rate": sum(r.new_extract_rate for r in results) / max(len(results), 1),
        "per_problem": [asdict(r) for r in results],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    files = {
        "Submission 1 (research_data.jsonl)":
            ROOT / "data" / "research" / "research_data.jsonl",
        "Baseline 6/10 (research_data2.jsonl — pre-architecture)":
            ROOT / "data" / "research" / "research_data2.jsonl",
    }

    all_summaries = {}

    for label, path in files.items():
        if not path.exists():
            print(f"[SKIP] {path} not found.")
            continue
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        results = [analyze_record(r) for r in records]
        summary = print_results(label, results)
        all_summaries[label] = summary

    # Cross-dataset comparison
    if len(all_summaries) == 2:
        print(f"\n{'='*70}")
        print("  CROSS-DATASET SUMMARY")
        print(f"{'='*70}")
        for label, s in all_summaries.items():
            n = s["scoreable_n"]
            old_c, new_c = s["old_correct"], s["new_correct"]
            print(f"\n  [{label[:45]}]")
            print(f"    Old:  {old_c}/{n}  →  New: {new_c}/{n}  (Δ = {new_c - old_c:+d})")
            print(f"    Extract rate: {s['avg_old_extract_rate']*100:.0f}% → {s['avg_new_extract_rate']*100:.0f}%")

    # Save detailed results
    out = ROOT / "data" / "ablation_results.json"
    out.write_text(json.dumps(all_summaries, indent=2, default=str), encoding="utf-8")
    print(f"\n\n  Detailed results saved to: {out}")
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
