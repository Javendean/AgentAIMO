"""Batch audit runner for AgentAIMO.

Runs audit_problem() over all records in a JSONL file and streams
results to an output JSONL file.

Phase 3 implementation.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from src.runner.audit_problem import audit_problem, AuditRecord


def run_batch(
    input_path: Path,
    output_path: Path,
    verbose: bool = True,
) -> list[AuditRecord]:
    """Audit all records in input_path, stream results to output_path.

    Args:
        input_path:  JSONL file with problem records.
        output_path: JSONL file to write AuditRecord dicts to.
        verbose:     Print per-problem progress if True.

    Returns:
        List of all AuditRecord objects (also written to output_path).
    """
    records = [
        json.loads(line)
        for line in input_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    results: list[AuditRecord] = []
    t0 = time.monotonic()

    with open(output_path, "w", encoding="utf-8") as out:
        for n, record in enumerate(records, 1):
            pid = record.get("problem_id", f"record_{n}")
            if verbose:
                print(f"  [{n}/{len(records)}] Auditing {pid}...", end=" ", flush=True)

            try:
                result = audit_problem(record)
            except Exception as exc:
                if verbose:
                    print(f"ERROR: {exc}")
                continue

            results.append(result)
            out.write(json.dumps(result.to_jsonl_dict(), default=str) + "\n")
            out.flush()

            if verbose:
                status = ("CORRECT" if result.correct is True
                          else "WRONG"   if result.correct is False
                          else "UNSCORED")
                ans = result.selected_answer if result.selected_answer is not None else "-"
                flaws = len(result.unique_flaw_codes)
                print(f"{status}  answer={ans}  flaws={flaws}")

    elapsed = time.monotonic() - t0
    if verbose:
        print(f"\n  Batch complete: {len(results)}/{len(records)} records "
              f"in {elapsed:.1f}s")
        print(f"  Output: {output_path}")

    return results
