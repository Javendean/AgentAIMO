# Verification Semantics Audit

This document audits the current mechanisms for verifying and checking mathematical reasoning within the DeepResearcher repository. It highlights the critical architectural flaw of collapsing multiple verification signals into a single boolean state, violating AGENTS.md Rule #2 and Rule #3.

---

## 1. Typed Evidence Schema (Proposed)

The most significant gap in the current architecture is the lack of a typed evidence schema. To decouple "code execution success" from "mathematical correctness," the system must adopt an explicit, strongly typed structure.

**Proposed Implementation:**

```python
from enum import Enum, auto
from dataclasses import dataclass

class EvidenceType(Enum):
    EXECUTION_SUCCESS = auto()       # Code ran without throwing exceptions (weakest)
    ANSWER_MATCH = auto()            # Output matches known ground truth (strong, but silent on reasoning)
    SPOT_CHECK = auto()              # Evaluated specific test/edge cases successfully
    SYMBOLIC_CAS = auto()            # SymPy/CAS confirmed an algebraic identity or equation
    EXHAUSTIVE_ENUMERATION = auto()  # Brute-forced all cases in a bounded range
    LLM_JUDGMENT = auto()            # An LLM reviewed and approved the logic (weakest for truth)
    FORMAL_PROOF = auto()            # Proof kernel (e.g., Lean) accepted the proof (strongest, not implemented)
    UNVERIFIED = auto()              # No check performed, timed out, or inapplicable

@dataclass
class VerificationSignal:
    evidence_type: EvidenceType
    passed: bool
    output_message: str
    metadata: dict | None = None
```

---

## 2. Code Verification (Sandbox)

### The `BEFORE` Flow (Current State)

Currently, the `run_verification` function collapses the entire execution trace of all generated code blocks into a single boolean (`all_passed`). It produces the `EXECUTION_SUCCESS` evidence type but treats it as absolute correctness.

**Location:** `agent/sandbox.py`, lines 189-231

```python
def run_verification(solution_text: str, timeout: int = 30) -> tuple[bool, str]:
    """Extract and execute all code blocks from a solution."""
    blocks = extract_code_blocks(solution_text)

    if not blocks:
        return False, "NO_CODE: No executable Python code blocks found in solution"

    all_outputs = []
    all_passed = True

    for i, code in enumerate(blocks):
        success, stdout, stderr = execute_code(code, timeout=timeout)

        block_label = f"[Block {i + 1}/{len(blocks)}]"

        if success:
            output = f"{block_label} PASSED"
            if stdout.strip():
                output += f"\n  Output: {stdout.strip()}"
        else:
            all_passed = False
            output = f"{block_label} FAILED"
            if stderr.strip():
                output += f"\n  Error: {stderr.strip()}"

        all_outputs.append(output)

    combined = "\n".join(all_outputs)
    return all_passed, combined
```

**How it is used (The Conflation):**
In `agent/deep_researcher.py`, the result of this function is directly mapped to the `verification_passed` boolean field on the `Attempt` dataclass and used to double the weight of the answer in the majority vote, severely polluting the consensus mechanism.

```python
passed, verify_output = run_verification(solution, timeout=self.code_timeout)
# ...
if answer is not None:
    weight = 2 if passed else 1
    answer_counts[answer] += weight
```

### The `AFTER` Flow (Proposed Architecture)

```python
def run_verification(solution_text: str, timeout: int = 30) -> list[VerificationSignal]:
    blocks = extract_code_blocks(solution_text)
    signals = []

    if not blocks:
        signals.append(VerificationSignal(EvidenceType.UNVERIFIED, False, "NO_CODE"))
        return signals

    for i, code in enumerate(blocks):
        success, stdout, stderr = execute_code(code, timeout=timeout)

        # Analyze stdout/code to determine *why* it succeeded
        if success:
            if "assert " in code:
                sig_type = EvidenceType.SPOT_CHECK
            elif "sympy" in code and "==" in code: # Crude heuristic for proposed flow
                sig_type = EvidenceType.SYMBOLIC_CAS
            else:
                sig_type = EvidenceType.EXECUTION_SUCCESS

            signals.append(VerificationSignal(sig_type, True, stdout))
        else:
            signals.append(VerificationSignal(EvidenceType.EXECUTION_SUCCESS, False, stderr))

    return signals
```

---

## 3. Natural Language Verification (LLM Review)

The system employs an LLM to review the winning reasoning trace for logical errors.

**Location:** `agent/prompts.py`, lines 364-375

**Exact Judging Prompt:**
```text
You are a rigorous mathematical reviewer. Carefully review the following \
solution for logical errors, unstated assumptions, and mathematical mistakes.

## Problem
{problem_text}

## Solution Under Review
{solution}

## Your Task
1. Check each logical step for validity
2. Identify any unstated assumptions
3. Look for common mistakes (sign errors, off-by-one, incorrect formula usage)
4. Verify the final answer is consistent with ALL problem constraints

If the solution is correct, respond with: **VERDICT: CORRECT**
If you find errors, respond with: **VERDICT: ERROR** followed by a \
description of the specific flaw.
```

**Evidence Type:** `LLM_JUDGMENT`

**AGENTS.md Rule #3 Violation Analysis:**
AGENTS.md strictly states: *"Never use an LLM-style judgment as the primary truth signal."*
Currently, the codebase **does** violate the spirit of this rule in the fallback extraction logic.

**Location:** `agent/prompts.py` -> `extract_nl_verdict`
```python
def extract_nl_verdict(verifier_output: str) -> tuple[bool, str]:
    if "VERDICT: CORRECT" in verifier_output.upper():
        return True, "NL Verifier: Solution is correct"

    match = re.search(
        r"VERDICT:\s*ERROR\s*(.*)", verifier_output, re.IGNORECASE | re.DOTALL
    )
    if match:
        return False, f"NL Verifier found error: {match.group(1).strip()[:500]}"

    # If no clear verdict, treat as uncertain (pass through)
    return True, "NL Verifier: No clear verdict (treating as pass)"
```
If the verifier hallucinates its format and fails to output `VERDICT: ERROR`, the fallback logic returns `True`. This makes the LLM's structural obedience the ultimate arbiter of truth, bypassing actual mathematical rigor.

---

## 4. The False Positive Path

This is a concrete trace of how the current verification system can mark a mathematically WRONG solution as "verified" and boost it into the final consensus.

1.  **Problem Input:** "Find the area of a circle with radius 3."
2.  **LLM Generates (Hallucination):**
    ```text
    The formula for the area of a circle is 2*pi*r.
    ```python
    import math
    area = 2 * math.pi * 3
    print(area)
    ```
    Therefore, the area is 18.84.
    **ANSWER: 18.84**
    ```
3.  **Sandbox Execution:** `run_verification` extracts the block. The Python code is syntactically flawless. `execute_code` returns `success=True`.
4.  **Conflation:** `run_verification` returns `all_passed=True`.
5.  **Majority Vote Tally:** In `_majority_vote`, the variable `passed` is `True`. The hallucinated answer `"18.84"` is given a weight of `2` instead of `1`.
6.  **False Consensus:** Because the code didn't crash, the mathematically wrong answer out-competes correct answers that might have suffered a syntax error (e.g., forgetting a closing parenthesis in a complex SymPy block).
7.  **Result:** The system confidently selects `18.84` as the final answer.

---

## 5. Coverage Gaps

Because the current system relies strictly on `EXECUTION_SUCCESS` and `LLM_JUDGMENT`, its actual mathematical verification coverage is extremely limited.

*   **Can it verify arithmetic?** Yes (via Python evaluation, if the LLM chooses to write it).
*   **Can it verify algebraic identities?** Maybe (if the LLM explicitly imports SymPy, uses `expand()` or `simplify()`, and the sandbox doesn't crash).
*   **Can it verify inequalities?** Probably not. Python floats lack precision for tight bounds, and SymPy inequality solving is highly brittle in zero-shot code generation.
*   **Can it verify geometric claims?** No. There is no geometry engine (like GeoGebra or specific SymPy geometry setups) explicitly prompted or validated.
*   **Can it verify combinatorial arguments?** No. Python loops will time out (Sandbox limits to 30s) on large combinatorial state spaces, resulting in `all_passed=False` even if the logic is correct.
*   **Can it verify existence/uniqueness?** No. It cannot formally prove that no other solutions exist outside a brute-forced bound.