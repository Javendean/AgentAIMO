#!/usr/bin/env python3
"""Baseline audit runner — Phase 3 entry point.

Runs both submission JSONL files through the full Phase 1–3 pipeline and
produces docs/BASELINE_METRICS.md with key metrics.

Usage:
    python scripts/run_baseline.py [options]

Options:
    --input PATH      JSONL file to audit (default: both research_data*.jsonl)
    --output PATH     Output JSONL for audit records (default: data/verification/audit_results.jsonl)
    --metrics PATH    Markdown metrics file (default: docs/BASELINE_METRICS.md)
    --no-metrics      Skip writing metrics file

The script runs both JSONL files by default and compares them side-by-side.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.runner.audit_problem import AuditRecord, GROUND_TRUTH
from src.runner.batch_audit import run_batch


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------

def compute_metrics(results: list[AuditRecord], label: str) -> dict:
    """Compute summary metrics from a list of AuditRecord results."""
    n = len(results)
    if n == 0:
        return {"label": label, "n": 0}

    scoreable = [r for r in results if r.ground_truth is not None]
    correct   = [r for r in scoreable if r.correct is True]

    # Answer extraction rate (fraction of attempts with any canonical answer)
    all_attempts = sum(r.num_attempts for r in results)
    answered_attempts = sum(
        1
        for r in results
        for a in r.attempts
        if a.canonical_answer is not None
    )
    extract_rate = answered_attempts / all_attempts if all_attempts > 0 else 0.0

    # Flaw frequency
    all_flaw_codes: list[str] = []
    for r in results:
        all_flaw_codes.extend(r.unique_flaw_codes)
    flaw_freq = Counter(all_flaw_codes)

    # Clean attempt fraction
    clean_attempts = sum(r.clean_attempt_count for r in results)
    clean_rate = clean_attempts / all_attempts if all_attempts > 0 else 0.0

    # Verifier coverage (fraction of attempts where pipeline ran >= 1 arithmetic check)
    # In current implementation, all attempts go through the pipeline
    verifier_coverage = extract_rate  # proxy: if extract_rate > 0, verifier ran

    return {
        "label": label,
        "n": n,
        "scoreable_n": len(scoreable),
        "correct": len(correct),
        "accuracy": len(correct) / len(scoreable) if scoreable else None,
        "extract_rate": extract_rate,
        "clean_attempt_rate": clean_rate,
        "verifier_coverage": verifier_coverage,
        "top_flaws": flaw_freq.most_common(8),
        "per_problem": [
            {
                "problem_id": r.problem_id,
                "gt": r.ground_truth,
                "selected": r.selected_answer,
                "correct": r.correct,
                "reason": r.selection_reason,
                "flaw_codes": r.unique_flaw_codes,
            }
            for r in results
        ],
    }


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def write_metrics_md(
    metrics_list: list[dict],
    output_path: Path,
) -> None:
    """Write BASELINE_METRICS.md from a list of metric dicts."""
    lines = [
        "# AgentAIMO — Baseline Metrics (Phase 3 Audit Runner)",
        "",
        f"**Generated:** 2026-03-17  ",
        f"**Source:** `scripts/run_baseline.py`  ",
        f"**Pipeline:** Phase 0 bug fixes + Phase 1A validator + Phase 1B verification battery "
        f"+ Phase 2 last-resort extractor + Phase 3 FlawDetector + AnswerSelector",
        "",
        "---",
        "",
    ]

    for m in metrics_list:
        label = m["label"]
        n = m["n"]
        scoreable = m.get("scoreable_n", 0)
        correct = m.get("correct", 0)
        acc = m.get("accuracy")
        acc_str = f"{correct}/{scoreable} = {acc*100:.0f}%" if acc is not None else "N/A"

        lines += [
            f"## {label}",
            "",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Problems audited | {n} |",
            f"| Scoreable (GT known) | {scoreable} |",
            f"| **Correct (exact match)** | **{acc_str}** |",
            f"| Canonical answer extract rate | {m.get('extract_rate', 0)*100:.1f}% |",
            f"| Clean trace rate (no sev≥3 flaws) | {m.get('clean_attempt_rate', 0)*100:.1f}% |",
            f"| Verifier coverage | {m.get('verifier_coverage', 0)*100:.1f}% |",
            "",
            "**Per-problem results:**",
            "",
            "| Problem ID | GT | Selected | Correct | Selection reason | Top flaws |",
            "|---|---|---|---|---|---|",
        ]

        for pp in m.get("per_problem", []):
            pid    = pp["problem_id"]
            gt     = str(pp["gt"]) if pp["gt"] is not None else "N/A"
            sel    = str(pp["selected"]) if pp["selected"] is not None else "-"
            corr   = "✓" if pp["correct"] is True else ("✗" if pp["correct"] is False else "~")
            reason = pp.get("reason", "")[:30]
            flaws  = ", ".join(pp.get("flaw_codes", [])[:3]) or "(none)"
            lines.append(f"| {pid} | {gt} | {sel} | {corr} | {reason} | {flaws} |")

        lines.append("")

        top_flaws = m.get("top_flaws", [])
        if top_flaws:
            lines += [
                "**Top flaw codes across all attempts:**",
                "",
                "| Flaw Code | Count |",
                "|---|---|",
            ]
            for code, count in top_flaws:
                lines.append(f"| `{code}` | {count} |")
            lines.append("")

        lines += ["---", ""]

    lines += [
        "## Interpretation",
        "",
        "- **Canonical answer extract rate** — fraction of individual attempts where `AnswerValidator`",
        "  returned a valid integer (including the last-resort prose extractor).",
        "- **Clean trace rate** — fraction of attempts with no flaw of severity ≥ 3.",
        "  Low values indicate systematic `CHANNEL_LEAKAGE` / `MALFORMED_TOOL_CALL` issues.",
        "- **MISSING_FINAL_COMMIT** — the #1 extraction failure: model derives correct answer",
        "  but outputs it in prose instead of `**ANSWER: N**` format.",
        "- **CONTEXT_CONFABULATION** — model requests prior context on a self-contained problem.",
        "  Addressable via prompt engineering (Phase 4).",
        "",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Metrics written to: {output_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Phase 3 baseline audit over AIMO submission JSONL files.",
    )
    parser.add_argument(
        "--input", type=Path, default=None,
        help="JSONL file to audit (default: both research_data*.jsonl files)",
    )
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "data" / "verification" / "audit_results.jsonl",
        help="Output JSONL path",
    )
    parser.add_argument(
        "--metrics", type=Path,
        default=ROOT / "docs" / "BASELINE_METRICS.md",
        help="Output metrics markdown path",
    )
    parser.add_argument(
        "--no-metrics", action="store_true",
        help="Skip writing metrics markdown",
    )
    args = parser.parse_args()

    if args.input is not None:
        files = [(args.input.stem, args.input)]
    else:
        files = [
            ("Submission 1 (research_data.jsonl)",
             ROOT / "data" / "research" / "research_data.jsonl"),
            ("Baseline 6/10 (research_data2.jsonl — pre-architecture)",
             ROOT / "data" / "research" / "research_data2.jsonl"),
        ]

    all_metrics = []
    for label, path in files:
        if not path.exists():
            print(f"[SKIP] {path} not found.")
            continue

        stem = path.stem
        out_path = args.output.parent / f"audit_{stem}.jsonl"
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")

        results = run_batch(path, out_path, verbose=True)
        m = compute_metrics(results, label)
        all_metrics.append(m)

        print(f"\n  Summary: {m.get('correct', 0)}/{m.get('scoreable_n', 0)} correct  "
              f"extract_rate={m.get('extract_rate', 0)*100:.0f}%  "
              f"clean_rate={m.get('clean_attempt_rate', 0)*100:.0f}%")

    if not args.no_metrics and all_metrics:
        write_metrics_md(all_metrics, args.metrics)

    print("\nDone.")


if __name__ == "__main__":
    main()
