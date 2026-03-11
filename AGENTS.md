# AGENTS.md

## Project status

This repository is in an early restructuring and audit phase.

Your current job is NOT to maximize feature velocity.
Your current job is to improve clarity, structure, and trustworthiness.

Primary goals, in order:
1. Make the repository understandable.
2. Separate production-like code from experiments and noise.
3. Make answer extraction deterministic.
4. Make verification semantics explicit and typed.
5. Only after the above, prepare for specialists, routing, and self-improvement systems.

## Current phase rules

Unless the task explicitly says otherwise, assume we are in a docs-first review phase.

In this phase:
- Prefer documentation, inventories, maps, and tests over broad logic changes.
- Do not perform architectural rewrites unless explicitly requested.
- Do not opportunistically fix many bugs during review.
- If you find issues, document them precisely.

## Hard rules

1. Never treat "code executed successfully" as equivalent to "math verified".
2. Never collapse execution success, checker success, and proof/certificate success into one boolean.
3. Never use an LLM-style judgment as the primary truth signal.
4. Never mutate raw data artifacts just to add commentary.
5. Never broadly move files without first documenting what is being moved and why.
6. Never delete uncertain files outright; move them only with a manifest or document them for future review.
7. Never assume notebooks are authoritative implementations.
8. Never make broad changes without a written plan and impact summary.
9. If a task is review-focused, do not mix in speculative feature work.
10. If more than ~10 files would change meaningfully, stop and ask for confirmation.

## Python documentation style

Use Google-style docstrings for new or materially edited Python code.

Prefer:
- concise one-line summary
- Args
- Returns
- Raises when relevant
- Notes only when needed

Do not add filler docstrings to trivial code.

## Non-source file documentation policy

For notebooks (`.ipynb`):
- If the notebook is active and important, add a top markdown cell summarizing:
  - purpose
  - inputs
  - outputs
  - status (experimental / active / archival)
- If the notebook is archival or noisy, prefer documenting it in markdown files instead of editing it.

For data/text artifacts (`.jsonl`, `.txt`, transcript dumps, raw exports):
- Prefer directory-level documentation and final analysis docs.
- Do not modify machine-generated or raw data files solely to add commentary.

## Directory documentation naming

Use `README.md` inside major directories when directory-level documentation is needed.

Preferred examples:
- `audit/README.md`
- `submission/README.md`
- `research/README.md`
- `docs/README.md`

## Review deliverables

When asked to review/analyze, prefer creating markdown artifacts under `docs/`.

Common deliverables include:
- `docs/CODEBASE_ANALYSIS.md`
- `docs/REPO_MAP.md`
- `docs/RISK_REGISTER.md`
- `docs/ANSWER_EXTRACTION_AUDIT.md`
- `docs/VERIFICATION_AUDIT.md`
- `docs/LEGACY_ARTIFACT_INVENTORY.md`
- `docs/MOVE_CANDIDATES.md`

## Refactor discipline

Before making edits:
1. State the plan.
2. List files to inspect.
3. List files to edit.
4. State risks.
5. Keep the patch minimal.

After making edits:
1. Summarize changed files.
2. State what was intentionally not changed.
3. Run the narrowest useful validation/tests.
4. Report unresolved concerns.

## Repository intent

The long-term target architecture is:
- an offline audit-and-improvement system for AIMO-style math solver outputs
- deterministic answer canonicalization
- typed claim graph / evidence graph
- explicit verifier registry
- specialist interfaces added only after metrics are trustworthy

That means:
- truthful structure beats cleverness
- typed outputs beat prose
- reproducibility beats ambitious scope

## What to prioritize when uncertain

If uncertain between two options, prefer the one that:
- reduces ambiguity
- preserves reversibility
- improves testability
- avoids reward hacking
- avoids overfitting to noisy artifacts

## Stop conditions

Stop and ask for review if:
- the task appears to require large architectural rewrites
- the import graph is unclear
- notebook and package code disagree about the canonical implementation
- raw data files appear to be inputs to live code
- verification semantics are ambiguous and could be broken by a refactor
