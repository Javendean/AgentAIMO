# Repository Documentation Map

This directory contains various audits, analyses, and documentation files meant to expose the current technical state of the DeepResearcher repository.

## How to use these docs

When interacting with this codebase or referencing these documents, it is important to distinguish between different types of information:

*   **Code-Backed Facts:** If a document cites a specific file, class, or Python execution behavior (e.g., `agent/sandbox.py` blocking `os`), it represents the current factual state of the system.
*   **Audit Summaries:** Documents like `VERIFICATION_AUDIT.md` and `ANSWER_EXTRACTION_AUDIT.md` synthesize behavior across multiple files. They identify logical flaws and architectural mismatches (e.g., execution success vs. correctness). Treat these as load-bearing context before attempting major feature implementation.
*   **Artifact Triage Recommendations:** Documents like `LEGACY_ARTIFACT_INVENTORY.md` and `MOVE_CANDIDATES.md` list unstructured `.txt` and `.jsonl` files in the root. Treat these as "weak suspicions" about the repository's history rather than strict facts. Follow these recommendations when cleaning the repository, but verify paths before deleting anything.

## Documentation Index

1.  **[REPO_MAP.md](REPO_MAP.md)**: A high-level overview of the active packages, notebooks, and noise in the repository. Look here first to understand the divergence between local code and the Kaggle notebooks.
2.  **[RISK_REGISTER.md](RISK_REGISTER.md)**: A prioritized list of implementation-phase risks, such as weak sandbox security, metric overfitting, and brittle extraction logic.
3.  **[BLINDSPOT_EXECUTIVE_SUMMARY.md](BLINDSPOT_EXECUTIVE_SUMMARY.md)**: A one-page summary of the most dangerous unknown-unknowns in the codebase (generated during the blindspot illumination pass).
4.  **[blindspots/](blindspots/)**: A detailed directory containing specific breakdowns of architectural, metric, and artifact blindspots, categorized by severity and confidence.
5.  **[VERIFICATION_AUDIT.md](VERIFICATION_AUDIT.md)**: A deep dive into why the agent frequently falsely validates its own bad math.
6.  **[ANSWER_EXTRACTION_AUDIT.md](ANSWER_EXTRACTION_AUDIT.md)**: A deep dive into the regex extraction and why lack of canonicalization fractures the majority vote.
7.  **[LEGACY_ARTIFACT_INVENTORY.md](LEGACY_ARTIFACT_INVENTORY.md) & [MOVE_CANDIDATES.md](MOVE_CANDIDATES.md)**: Triage lists for cleaning up the root directory.