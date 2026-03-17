"""src/runner — Audit runner package for AgentAIMO.

Modules:
    audit_problem  — Per-problem audit pipeline (parser → verifier → flaw detector → selector)
    batch_audit    — Batch runner over a JSONL file

Phase 3 implementation.
"""

from src.runner.audit_problem import audit_problem, AuditRecord, AttemptAudit
from src.runner.batch_audit import run_batch

__all__ = ["audit_problem", "run_batch", "AuditRecord", "AttemptAudit"]
