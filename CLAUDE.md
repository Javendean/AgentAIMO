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
- Tests: run `python -m pytest tests/ -q` to verify current count (never trust a cached number)
- `docs/BASELINE_METRICS.md` has the current accuracy numbers
- `data/verification/audit_research_data*.jsonl` have per-problem audit records
- Task queue: `prd.json` (RalphTUI format) — check this for pending Phase 4 work
- RalphTUI config: `.ralph-tui/config.toml` — Codex is default, Claude for complex tasks
- RalphTUI instructions: `docs/RALPHTUI_INSTRUCTIONS.md`

## Branch
Develop on `claude/configure-ralphtui-claude-M4WRa` unless told otherwise.
Never push to main without explicit permission.

## Gotchas
- `pipeline.run()` takes a `SolutionTrace(raw_text=sol_text)` — NOT a raw string
- The Kaggle notebook is at `notebook/kaggle_notebook.py` — do NOT edit without reading it first
- `test_sandbox_allows_sympy` is a known skip on Python 3.12 — this is expected

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **AgentAIMO** (750 symbols, 1850 relationships, 29 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/AgentAIMO/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/AgentAIMO/context` | Codebase overview, check index freshness |
| `gitnexus://repo/AgentAIMO/clusters` | All functional areas |
| `gitnexus://repo/AgentAIMO/processes` | All execution flows |
| `gitnexus://repo/AgentAIMO/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
