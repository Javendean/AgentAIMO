"""
Local Analysis Pipeline: Grade H100 Sprint Results

Run this LOCALLY after downloading research_data.jsonl from Kaggle.
Analyzes success rates, identifies failure patterns, and generates
"System Prompt Patches" for the next H100 sprint.

Usage:
    python analyze_results.py research_data.jsonl
    python analyze_results.py research_data.jsonl --output-patch prompt_patch.txt
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def load_traces(path: str) -> list[dict]:
    """Load JSONL research traces."""
    traces = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                traces.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[WARN] Malformed JSON on line {line_num}: {e}")
    return traces


def analyze(traces: list[dict]) -> dict:
    """Compute comprehensive statistics from research traces."""
    total = len(traces)
    solved = sum(1 for t in traces if t.get("solved", False))

    # By source
    by_source = defaultdict(lambda: {"total": 0, "solved": 0})
    for t in traces:
        src = t.get("source", "unknown")
        by_source[src]["total"] += 1
        if t.get("solved"):
            by_source[src]["solved"] += 1

    # By difficulty
    by_difficulty = defaultdict(lambda: {"total": 0, "solved": 0})
    for t in traces:
        diff = t.get("difficulty", "unknown")
        by_difficulty[diff]["total"] += 1
        if t.get("solved"):
            by_difficulty[diff]["solved"] += 1

    # Attempt distribution
    attempt_counts = Counter()
    for t in traces:
        attempt_counts[t.get("total_attempts", 0)] += 1

    # Timing
    durations = [t.get("total_duration_seconds", 0) for t in traces]
    avg_duration = sum(durations) / len(durations) if durations else 0

    # Failure analysis
    failure_patterns = Counter()
    for t in traces:
        if not t.get("solved"):
            for attempt in t.get("attempts", []):
                output = attempt.get("verification_output", "")
                if "TIMEOUT" in output:
                    failure_patterns["timeout"] += 1
                elif "NO_CODE" in output:
                    failure_patterns["no_code_generated"] += 1
                elif "SANDBOX ERROR" in output:
                    failure_patterns["sandbox_error"] += 1
                elif "SyntaxError" in output:
                    failure_patterns["syntax_error"] += 1
                elif "NameError" in output:
                    failure_patterns["name_error"] += 1
                elif "TypeError" in output:
                    failure_patterns["type_error"] += 1
                elif "ZeroDivisionError" in output:
                    failure_patterns["division_by_zero"] += 1
                elif "FAILED" in output:
                    failure_patterns["verification_failed"] += 1
                else:
                    failure_patterns["other"] += 1

    return {
        "total": total,
        "solved": solved,
        "solve_rate": solved / total if total > 0 else 0,
        "by_source": dict(by_source),
        "by_difficulty": dict(by_difficulty),
        "attempt_distribution": dict(sorted(attempt_counts.items())),
        "avg_duration_seconds": avg_duration,
        "failure_patterns": dict(failure_patterns.most_common()),
    }


def generate_patch(stats: dict, traces: list[dict]) -> str:
    """Generate a System Prompt Patch based on failure analysis."""
    lines = ["## Domain-Specific Patches (Auto-Generated from Sprint Analysis)", ""]

    # Add patches for common failure patterns
    patterns = stats.get("failure_patterns", {})

    if patterns.get("no_code_generated", 0) > 0:
        lines.append(
            "- **CRITICAL**: Always include a Python verification code block. "
            "Every solution MUST contain at least one ```python ... ``` block."
        )

    if patterns.get("syntax_error", 0) > 2:
        lines.append(
            "- **WARNING**: Frequent Python syntax errors detected. "
            "Double-check indentation, parentheses, and f-string syntax."
        )

    if patterns.get("timeout", 0) > 2:
        lines.append(
            "- **WARNING**: Code execution timeouts detected. "
            "Avoid brute-force loops over large ranges. Use mathematical shortcuts."
        )

    if patterns.get("division_by_zero", 0) > 0:
        lines.append(
            "- **CAUTION**: Division by zero errors occurred. "
            "Always check denominators before dividing."
        )

    if patterns.get("name_error", 0) > 2:
        lines.append(
            "- **WARNING**: Undefined variable errors detected. "
            "Ensure all variables are defined before use in code blocks."
        )

    # Add patches for weak problem categories
    by_source = stats.get("by_source", {})
    for source, data in by_source.items():
        if data["total"] >= 3:
            rate = data["solved"] / data["total"]
            if rate < 0.3:
                lines.append(
                    f"- **WEAK AREA**: {source} problems ({rate:.0%} solve rate). "
                    f"Pay extra attention to this problem type."
                )

    by_difficulty = stats.get("by_difficulty", {})
    for diff, data in by_difficulty.items():
        if data["total"] >= 3:
            rate = data["solved"] / data["total"]
            if rate < 0.3:
                lines.append(
                    f"- **WEAK AREA**: Difficulty '{diff}' ({rate:.0%} solve rate). "
                    f"Consider breaking these into smaller sub-problems."
                )

    if len(lines) <= 2:
        lines.append("(No critical patterns detected — baseline is performing well)")

    return "\n".join(lines)


def print_report(stats: dict):
    """Print a human-readable analysis report."""
    print("=" * 60)
    print("RESEARCH SPRINT ANALYSIS REPORT")
    print("=" * 60)

    print(f"\n  Total problems:  {stats['total']}")
    print(f"  Solved:          {stats['solved']}")
    print(f"  Solve rate:      {stats['solve_rate']:.1%}")
    print(f"  Avg time/prob:   {stats['avg_duration_seconds']:.1f}s")

    print("\n--- By Source ---")
    for source, data in stats["by_source"].items():
        rate = data["solved"] / data["total"] if data["total"] > 0 else 0
        print(f"  {source:20s}  {data['solved']}/{data['total']} ({rate:.0%})")

    print("\n--- By Difficulty ---")
    for diff, data in stats["by_difficulty"].items():
        rate = data["solved"] / data["total"] if data["total"] > 0 else 0
        print(f"  {diff:20s}  {data['solved']}/{data['total']} ({rate:.0%})")

    print("\n--- Attempt Distribution ---")
    for attempts, count in stats["attempt_distribution"].items():
        bar = "#" * count
        print(f"  {attempts} attempts:  {count} {bar}")

    print("\n--- Failure Patterns ---")
    for pattern, count in stats["failure_patterns"].items():
        print(f"  {pattern:25s}  {count}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze DeepResearcher H100 sprint results"
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to research_data.jsonl from Kaggle",
    )
    parser.add_argument(
        "--output-patch",
        type=str,
        default="prompt_patch.txt",
        help="Path to write the generated System Prompt Patch",
    )
    parser.add_argument(
        "--output-stats",
        type=str,
        default=None,
        help="Path to write detailed stats as JSON",
    )
    args = parser.parse_args()

    traces = load_traces(args.input_file)
    if not traces:
        print("[ERROR] No traces loaded. Check the input file.")
        sys.exit(1)

    stats = analyze(traces)
    print_report(stats)

    # Generate and save the prompt patch
    patch = generate_patch(stats, traces)
    Path(args.output_patch).write_text(patch, encoding="utf-8")
    print(f"\n[OK] System Prompt Patch saved to: {args.output_patch}")
    print("     Upload this file to your Kaggle problems dataset for the next sprint.")

    # Optionally save detailed stats
    if args.output_stats:
        Path(args.output_stats).write_text(
            json.dumps(stats, indent=2), encoding="utf-8"
        )
        print(f"[OK] Detailed stats saved to: {args.output_stats}")


if __name__ == "__main__":
    main()
