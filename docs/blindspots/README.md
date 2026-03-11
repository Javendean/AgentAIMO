# DeepResearcher Blindspot Analysis

This directory (`docs/blindspots/`) serves as a comprehensive "blindspot illumination" pass for the DeepResearcher repository. It is a strictly docs-only exercise designed to expose every meaningful blindspot, ambiguity, hidden dependency, misleading surface impression, and unknown-unknown risk in the current codebase.

## Purpose

The goal is to provide a high-trust map of what a developer or an agent might be missing when working with this repository. It acts as an epistemological boundary layer, preventing the assumption that "code executed successfully" is equivalent to "math verified," or that a generic directory name accurately describes its contents.

## How to Read These Docs

Start with the **[Executive Summary](../BLINDSPOT_EXECUTIVE_SUMMARY.md)** for a 1-page overview of the most critical issues.
Then, proceed to the **[Blindspot Index](BLINDSPOT_INDEX.md)** to browse specific risks by category.
Finally, read the **[Fact vs. Inference](FACT_VS_INFERENCE.md)** document to understand the epistemological boundaries of our analysis.

## Epistemological Definitions

Throughout these documents, we distinguish claims using the following statuses:

*   **Fact**: A claim backed directly by current code execution or explicit string matching (e.g., "The sandbox blocks `os.system` via `SAFETY_PREAMBLE`").
*   **Strong Inference**: A claim based on strong circumstantial evidence or architectural patterns (e.g., "The presence of two solver loops suggests divergent development environments").
*   **Weak Suspicion**: A claim based on naming conventions, incomplete analysis, or historical artifacts (e.g., "The `.jsonl` files in the root might be from an older iteration").
*   **Unresolved Unknown**: A question or risk that cannot be definitively answered without further dynamic analysis or external context (e.g., "Does the Kaggle evaluation environment enforce the same offline wheel dependencies?").

## Interpretation of Metadata

*   **Severity (High/Medium/Low)**: Indicates the potential impact of the blindspot on the system's correctness, reliability, or security.
*   **Confidence (High/Medium/Low)**: Indicates the certainty of our analysis based on the available evidence. A high-severity, low-confidence blindspot is a prime candidate for immediate investigation.
*   **Blocks future work? (Yes/No)**: Indicates whether this blindspot must be resolved before adding new features (like DSPy or specialized routers).
