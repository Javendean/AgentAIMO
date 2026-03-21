# RalphTUI Operating Instructions — AgentAIMO

**Written:** 2026-03-21
**Purpose:** Operational guide for RalphTUI to run continuous research and codebase evolution for AIMO 3.
**Audience:** RalphTUI agent loop (read automatically at session start)

---

## 0. What You Are Doing

You are running the **offline meta-system** for an AI math olympiad competition solver. The competition ends **April 8, 2026**. Every improvement you make to the codebase should move the solver closer to answering more problems correctly.

The **submission model** (gpt-oss-120B on a Kaggle H100) is separate from this codebase. This codebase is the **research and improvement infrastructure**:
- Detects failure modes via the verification battery
- Selects answers using typed confidence signals
- Runs ablation experiments to quantify improvements
- Produces artifacts (prompts, schemas, selection policies) that feed back into the submission

**Your job:** Complete tasks from `prd.json`, in priority order, without breaking the test suite.

---

## 1. The Two-Agent Strategy

**Use Codex for the default agent.** Codex is fast and cheap. Reserve Claude (Opus) for the tasks explicitly tagged `"agent": "claude"` in `prd.json`. This is non-negotiable — Claude quota is limited and must not be wasted on routine implementation.

### When to use Codex
- Implementing stubs that have clear specifications
- Running scripts and capturing output
- Writing tests for well-understood behavior
- Executing straightforward refactors
- Cleaning up files, updating docs with known content
- Any task where the *what* is fully specified and the *how* is unambiguous

### When to use Claude (Opus)
- Formulating or solving genuinely open mathematical problems
- Diagnosing subtle failures where the root cause is unknown
- Designing algorithms where the correctness argument is non-trivial
- Tasks explicitly labeled `"agent": "claude"` in prd.json
- When Codex has failed 2+ times on the same task and the blocker requires reasoning about the problem domain

### When to use Claude (Sonnet)
- Architecture reviews where the scope is medium complexity
- Debugging sessions where Codex produced incorrect code and a second opinion is needed
- Writing detailed diagnostic reports (D-tier tasks where Opus is overkill)

### Never
- Never use Claude Haiku — this project has no latency-sensitive path that warrants it
- Never use Claude for tasks that Codex can do in one pass (file writes, test execution, simple refactors)
- Never make live model API calls inside tests or offline modules

---

## 2. Before Every Task: The Pre-Task Protocol

Before starting any task:

1. **Run tests** to confirm baseline is green:
   ```bash
   python -m pytest tests/ --tb=short -q
   ```
   If tests are failing, **stop**. Do not attempt the task. Report the failure and which test is broken.

2. **Check gitnexus impact** for any symbol you plan to modify:
   ```
   gitnexus_impact({target: "symbolName", direction: "upstream"})
   ```
   If blast radius is HIGH or CRITICAL — list all affected files and **pause for human approval** before proceeding.

3. **Read the file** before editing it. Never write to a file you haven't read in this session.

4. **Check prd.json** for the task's `dependsOn` list. If a dependency is not `completed`, **do not start the task**. Pick the next available task instead.

---

## 3. After Every Task: The Post-Task Protocol

After completing any task:

1. **Run tests**:
   ```bash
   python -m pytest tests/ --tb=short -q
   ```
   If tests fail, **do not mark the task complete**. Revert the change if you cannot identify the fix within 3 attempts.

2. **Run gitnexus re-index** after any commit:
   ```bash
   npx gitnexus analyze
   ```

3. **Update prd.json**: Mark the task `"status": "completed"`.

4. **Check if a downstream task is now unblocked** and select it next.

---

## 4. Task Execution Rules

### Code quality
- All new code goes in `src/` — fill existing stubs, never create parallel implementations
- Every new module needs ≥3 passing tests before the task is marked complete
- Never remove an existing test
- Never suppress errors with `try/except pass`
- No live model API calls in tests or offline modules

### Architecture constraints (never violate)
- `ConfidenceLevel` hierarchy: `LEVEL_0_EXACT > LEVEL_1_SYMBOLIC > ENUMERATED > NL_JUDGMENT > UNVERIFIED`
- `pipeline.run()` takes `SolutionTrace(raw_text=sol_text)` — NOT a raw string
- The Kaggle notebook is at `notebook/kaggle_notebook.py` — read it before touching it
- `test_sandbox_allows_sympy` is a known skip on Python 3.12 — ignore this failure

### The gitnexus rules (from .agent/rules/03-gitnexus.md)
- MUST run `gitnexus_impact` before modifying any function, class, or method
- MUST run `gitnexus_detect_changes()` before committing
- MUST warn if impact analysis returns HIGH or CRITICAL risk
- Never rename symbols with find-and-replace — use `gitnexus_rename`

---

## 5. Per-Task Agent Selection Reference

| Task ID | Agent | Model | Reasoning |
|---------|-------|-------|-----------|
| P4-A1 | Codex | o4-mini | Clear spec: swap Counter for AnswerSelector. Mechanical. |
| P4-A2 | Codex | o4-mini | Clear spec: add 3 prompt phrases. Copy from PHASE4_HANDOFF.md. |
| P4-B1 | Codex | o4-mini | Run a script, write a doc. No reasoning required. |
| P4-C1 | Codex | o4-mini | Implement select_two() — spec is in PHASE4_HANDOFF.md Track C. |
| P4-C2 | Codex | o4-mini | Wire select_two into notebook. Mechanical integration. |
| P4-D1 | Claude | opus | Open math problem: budget-aware scheduling formalization. Requires extended thinking. |
| P4-D2 | Claude | opus | Unknown root cause diagnosis. Requires tracing + reasoning. |
| P4-E1 | Codex | o4-mini | Run a script, update a file. |
| P4-F1 | Claude | sonnet | Implement non-trivial stubs with mathematical precision needed. |
| P4-G1 | Codex | o4-mini | Safe file moves. No reasoning. |

---

## 6. Codex Task Prompt Template

When building a Codex prompt, always include:

```
You are working on AgentAIMO, an AIMO 3 competition math solver (Python, pytest).
Deadline: April 8, 2026. The test suite must stay green: python -m pytest tests/ --tb=short -q

CRITICAL RULES:
- All new code goes in src/ — fill existing stubs, no parallel implementations
- Every new module needs ≥3 passing tests before completion
- Never remove an existing test; never use try/except pass
- ConfidenceLevel hierarchy: LEVEL_0_EXACT > LEVEL_1_SYMBOLIC > ENUMERATED > NL_JUDGMENT > UNVERIFIED
- No live model API calls in tests

Read these files before starting:
[list task-specific files from prd.json]

Task: [task description from prd.json]

Acceptance criteria:
[acceptance criteria from prd.json]

After finishing:
1. Run: python -m pytest tests/ --tb=short -q
2. Report test count and any failures
3. Run: npx gitnexus analyze
```

---

## 7. Claude Task Prompt Template

When building a Claude prompt, always include:

```
You are a research scientist and senior engineer on AgentAIMO, an AIMO 3 competition math solver.
Deadline: April 8, 2026. Test suite: 159/159 tests must stay green.

Use extended thinking. Think step by step before producing any output.

Project architecture:
- Submission model: gpt-oss-120B (Kaggle H100, not accessible here)
- Offline meta-system: src/ modules (verification battery, answer selector, audit runner)
- All new code in src/, tests in tests/
- ConfidenceLevel: LEVEL_0_EXACT > LEVEL_1_SYMBOLIC > ENUMERATED > NL_JUDGMENT > UNVERIFIED

Read before starting:
@docs/FORWARD_PLAN_v2.md
@docs/PHASE4_HANDOFF.md
[task-specific files]

Task: [task description from prd.json]

Be critical. If the problem has a simpler solution than what's described, say so.
If the approach has a flaw, identify it before implementing.
If you need to use gitnexus: gitnexus_impact, gitnexus_context, gitnexus_query are available.

Acceptance criteria:
[acceptance criteria from prd.json]
```

---

## 8. Failure Handling

### If Codex fails after 2 attempts on the same task
1. Save Codex's last output and error to `docs/agent_failures/TASK-ID_YYYYMMDD.md`
2. Escalate: run the task with Claude (Sonnet) instead
3. Add a note to prd.json: `"escalatedFrom": "codex"`

### If Claude fails on a reasoning task
1. Save Claude's output
2. Break the task into smaller subtasks
3. Warm-up: have Claude solve a simpler related problem first (per evolution.md §Idea 3)
4. Add the simpler warm-up task to prd.json before the original task

### If tests break after a task
1. Immediately revert: identify which file the task modified and restore its previous content
2. Do NOT mark the task complete
3. Add the test failure details to the task description
4. Re-attempt with a more conservative approach (smaller change, test-first)

### If gitnexus reports HIGH/CRITICAL risk
1. Do NOT proceed
2. List all affected files explicitly in the task log
3. Pause and request human review
4. Only proceed after human approval is recorded in prd.json under `"approvals"`

---

## 9. Continuous Improvement Loop

After completing all tasks in prd.json that are currently unblocked:

1. **Run the full baseline audit**:
   ```bash
   python scripts/run_baseline.py
   ```

2. **Compare** the new `docs/BASELINE_METRICS.md` to the previous run.

3. **Identify the biggest remaining failure mode** from the per-problem table.

4. **Create a new task** in prd.json targeting that failure mode. Assign agent based on complexity.

5. **Repeat**.

This loop is the core of the research process. Every iteration should produce:
- A measurable improvement in correct answer rate, OR
- A documented diagnostic that explains why improvement requires a different approach

---

## 10. What Not to Build (Hard Constraints)

From `docs/FORWARD_PLAN_v2.md §5`:

1. No full claim/evidence graph before the answer selector works — **answer selector is now working**
2. No monolithic confidence ontologies — the 6-level `ConfidenceLevel` taxonomy is fixed
3. No DSPy/OpenEvolve until Phase 3 evaluation signal is trustworthy — **Phase 3 is done, this constraint is lifted**
4. No NL-only verification as primary signal — NL verdict = `NL_JUDGMENT` (weakest level)
5. No dual architecture — all code in `src/`, production use via notebook calling into `src/`
6. No submission changes that bypass the audit runner — always run `python scripts/run_baseline.py` after notebook changes

---

## 11. Key File Map

```
notebook/kaggle_notebook.py          ← Production submission (Track A)
src/solver/answer_selector.py        ← AnswerSelector (extend with select_two)
src/solver/inference_engine.py       ← Stub (Track D only)
src/solver/sampling_strategy.py      ← Stub (Track D only)
src/verification/answer_validator.py ← Canonical extraction
agent/prompts.py                     ← All prompts + extract_answer
agent/deep_researcher.py             ← Orchestration
tests/test_phase3.py                 ← Phase 3 tests (add select_two tests here)
docs/BASELINE_METRICS.md             ← Regenerate with: python scripts/run_baseline.py
prd.json                             ← Task list for RalphTUI
```

---

## 12. RalphTUI CLI Quick Reference

```bash
# Install (one-time, already done)
cd /home/user/ralph-tui && bun run build

# Run with default agent (Codex) on prd.json
cd /home/user/AgentAIMO
/home/user/ralph-tui/dist/cli.js run --prd ./prd.json

# Run a specific task with Claude Opus (for D-tier tasks)
/home/user/ralph-tui/dist/cli.js run --prd ./prd.json --agent claude --model opus

# Run a specific task with Claude Sonnet
/home/user/ralph-tui/dist/cli.js run --prd ./prd.json --agent claude --model sonnet

# Check session status
/home/user/ralph-tui/dist/cli.js status

# Resume after pause/crash
/home/user/ralph-tui/dist/cli.js resume

# View logs from last iteration
/home/user/ralph-tui/dist/cli.js logs

# Override max iterations (for controlled runs)
/home/user/ralph-tui/dist/cli.js run --prd ./prd.json --iterations 3
```

---

## 13. Success Metrics (what "done" looks like for Phase 4)

| Metric | Current | Target |
|--------|---------|--------|
| Tests passing | 159/159 | ≥159/159 (never regress) |
| research_data.jsonl correct | 3/8 = 38% | ≥5/8 = 63% |
| research_data2.jsonl extract rate | 21.1% | ≥40% |
| MISSING_FINAL_COMMIT rate | 38% | <15% |
| CONTEXT_CONFABULATION rate | 90% | <30% |
| Notebook uses AnswerSelector | No | Yes |
| select_two() implemented | No | Yes |

When all targets are met: submit the improved notebook to Kaggle and record the public score.
