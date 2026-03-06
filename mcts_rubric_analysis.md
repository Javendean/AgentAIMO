# Operationalizing "Cognitive Fidelity" for MCTS-RL (Gemini DeepThink Style)

## 1. Executive Summary & Critical Review
The document `Refining LLM Rubric for Human Reasoning.md` is a **landmark architectural blueprint** rather than a simple grading guide. It correctly identifies that standard RLHF (Outcome Supervision) encourages "Pattern Matching" and "Goodharting" (e.g., fake "Wait..." tokens).

To implement this in a **Monte Carlo Tree Search (MCTS)** system like AlphaProof or Gemini DeepThink, we must convert this static rubric into dynamic **Reward Models** and **Search Policies**.

> [!IMPORTANT]
> **Critical Insight**: The rubric's "Hierarchical Decision Tree" matches the structure of MCTS perfectly.
> - **Dimension 1 (Verification)** = **Terminal Leaf Evaluation** (Win/Loss).
> - **Dimension 2 (Reasoning)** = **Process Reward Model (PRM)** for Node Selection.
> - **Dimension 4 (Skepticism)** = **Tree Expansion / Backtracking Policy**.

---

## 2. Mapping Rubric to MCTS Components

### A. The "Value Function" (V-Function)
In MCTS, the Value Function $V(s)$ estimates the probability that state $s$ leads to a correct solution. The Rubric defines $V(s)$ with high granularity.

*   **Standard MCTS**: $V(s) \in [0, 1]$ based on final answer correctness.
*   **Cognitive Fidelity MCTS**:
    *   **$V_{ver}(s)$ (Hard Value)**: Based on **Dimension 1 (Verification)**.
        *   If `Exit Code != 0` OR `Gt != Answer` -> $V(s) = -1$ (Immediate Pruning).
    *   **$V_{prm}(s)$ (Soft Value)**: Based on **Dimension 2 (Reasoning)**.
        *   The **Metacognition** criteria (`MET_01`, `MET_02`) serve as dense rewards for intermediate steps.
        *   *Implementation*: A "Process Reward Model" is trained to predict the "Self-Correction Entropy" score of the *next* token. High entropy (radical shift) = High Value node to explore.

### B. The "Rollout Policy" (Simulation)
When the tree reaches a leaf, MCTS simulates the future (Rollouts).
*   **Rubric Impact**: The rubric explicitly banning "linear reasoning" (`MET_01`) dictates we must use a **Temperature-Scaled Rollout** that favors *branching*.
*   **Negative Constraint**: The policy must be penalized if it generates "Performative Mimesis" (fake "Wait" tokens). The **Semantic Delta Check** (Section 6.3) should be a runtime filter during rollout. If $\Delta(\text{Pre-Wait}, \text{Post-Wait}) \approx 0$, kill the rollout.

### C. The "Selection Policy" (PUCT)
How do we choose which child node to explore?
*   **Rubric Impact**: Use **Dimension 4 (Epistemic Skepticism)** as an "Uncertainty Bonus".
*   **Strategy**: Nodes that have *not* yet faced **SKE_01 (Counter-Factual Resilience)** should have higher exploration uncertainty. The system should prioritize exploring branches where the "Skeptic" agent has found potential "Magic Leaps" (`MET_03`), treating them as high-risk, high-reward pivots.

---

## 3. Implementation: "System 2" Training Loop

To achieve "Gemini DeepThink" capabilities, we do not just filter data. We run an **Iterative Self-Improvement Loop**:

### Phase 1: The "Skeptic" as a Data Generator
Use the **Multi-Step Judge Pipeline** (Section 5) to generate a massive dataset of (Solution, Critique) pairs.
*   **Input**: A raw math problem.
*   **Agent**: Generates a solution.
*   **Skeptic**: Applies `SKE_01`, `SKE_02` to find flaws.
*   **Output**: If Flaws > 0, the solution is labeled "Rejected". If Flaws = 0 (and Code Exec passes), it is "Chosen".

### Phase 2: Training the Process Reward Model (PRM)
Train a PRM to predict the **Cognitive Fidelity Score** (0-5) of any given *partial* reasoning trace.
*   **Training Signal**: Use the `MET_xx` criteria.
    *   Did it backtrack? (+1)
    *   Did use a verified tool? (+1)
    *   Did it Justify? (+1)
*   **Usage**: During inference, MCTS uses this PRM to prune "linear/hallucinated" branches early, before wasting compute on code execution.

### Phase 3: MCTS Inference (The "DeepThink" Step)
At runtime:
1.  **Expand**: Generate 50 possible reasoning steps.
2.  **Evaluate**:
    *   **Fast Check**: Run `ENG_01` (Library Hygiene). Prune illegal imports.
    *   **PRM Check**: Score `MET_02` (Entropy). Prefer steps that show "Aha moments".
3.  **Simulate**: Run code for the top 5 branches.
4.  **Backpropagate**: Update values based on `VER_02` (Ground Truth).

---

## 4. Critical Gaps & "Painstaking Scrutiny"
While the rubric is excellent, here are the flaws a Deep Research Agent must address:

1.  **The "Entropy" Trap**: `MET_02` (Self-Correction Entropy) is theoretically sound but computationally expensive to measure at runtime (requires embedding comparison).
    *   *Fix*: Train a lightweight "Drift Detector" head on the main model to estimate semantic shift efficiently.
2.  **Infinite Loops in Skepticism**: The "Skeptic" (`SKE_01`) might nitpick indefinitely ("But what if x is a complex number?").
    *   *Fix*: Implement a **Depth Limit** on skepticism. After 3 rounds of defense, if code executes and matches GT, accept the solution.
3.  **Ground Truth Reliance**: `VER_02` relies on *knowing* the answer (0-999). In "Discovery Mode" (new science), we don't know the answer.
    *   *Fix*: Replace `VER_02` with **Consensus Verification** (do 5 different derivations lead to the same result?).

## 5. Conclusion
This rubric is **System 2 Ready**. It moves the definition of "Quality" from *Linguistic plausibility* (Outcome) to *Epistemic soundness* (Process).
By treating the **Skeptic** and **Solver** as distinct agents in the MCTS loop, you effectively build a **Generative Adversarial Network (GAN) for Reasoning**:
*   **Generator**: The Solver (trying to pass the rubric).
*   **Discriminator**: The Skeptic (trying to find `SKE_xx` violations).
This is the exact recipe for AlphaZero-style superhuman logic.
