# AgentAIMO — Claude Code Context

## Project
AIMO 3 competition math solver. Python, pytest. Deadline: April 8 2026.

## Commands
```bash
# Run all tests (must stay green)
python -m pytest tests/ --tb=short -q

# Run specific Phase tests
python -m pytest tests/test_phase3.py -v
python -m pytest tests/test_answer_extraction.py -v
python -m pytest tests/test_verification_battery.py -v

# Run the baseline audit (produces docs/BASELINE_METRICS.md)
python scripts/run_baseline.py

# Run ablation comparison
python scripts/ablation_extraction.py
```

## Code rules
- All new code goes in `src/` — fill existing stubs, don't create parallel implementations
- Tests go in `tests/` — every new module needs ≥3 passing tests before commit
- Never remove an existing test; never suppress errors with try/except pass
- `ConfidenceLevel` hierarchy MUST be respected: LEVEL_0_EXACT > LEVEL_1_SYMBOLIC > ENUMERATED > NL_JUDGMENT > UNVERIFIED
- No live model API calls in tests or offline modules

## Architecture (read before changing anything)
@docs/FORWARD_PLAN_v2.md
@docs/PHASE4_HANDOFF.md

## Current state: Phase 3 complete, Phase 4 in progress
- 159/159 tests passing (run `python -m pytest tests/ -q` to verify)
- `docs/BASELINE_METRICS.md` has the current accuracy numbers
- `data/verification/audit_research_data*.jsonl` have per-problem audit records

## Gotchas
- `pipeline.run()` takes a `SolutionTrace(raw_text=sol_text)` — NOT a raw string
- The Kaggle notebook is at `notebook/kaggle_notebook.py` — do NOT edit without reading it first
- `test_sandbox_allows_sympy` is a known skip on Python 3.12 — this is expected
