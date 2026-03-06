# **The Cognitive Fidelity Framework: Restructuring Automated Evaluation for High-Order Reasoning Agents**

## **1\. The Epistemic Crisis in Generative Reasoning**

### **1.1 The "Reasoning Illusion" and the Failure of Scalar Metrics**

The advancement of Large Language Models (LLMs) from stochastic parrots to reasoning agents marks a pivotal shift in the trajectory of artificial intelligence. We have moved beyond the era of mere text generation—where success was measured by fluency, coherence, and n-gram overlap—into the epoch of "System 2" cognitive emulation. In this new paradigm, models are not simply asked to retrieve information but to engage in multi-step deductive inference, generate executable artifacts, and critically evaluate their own internal logic. This transition has exposed a fundamental fragility in our existing evaluation infrastructures: the "Reasoning Illusion."

Current state-of-the-art models, such as OpenAI’s o-series and DeepSeek-R1, have demonstrated remarkable proficiency on benchmarks like MATH, GSM8K, and the American Invitational Mathematics Examination (AIME). However, closer scrutiny reveals a disquieting phenomenon. A significant proportion of "correct" answers are arrived at via flawed logical pathways, relying on sophisticated pattern matching rather than genuine causal inference.1 This mimics the behavior of a student who memorizes the answers to a test rather than learning the underlying principles. When the problem distribution is slightly perturbed—for instance, by changing the numerical constants in a geometry problem or inverting the logical quantifiers—the model’s performance often collapses, revealing the brittleness of its "reasoning."

The traditional tools of evaluation—Likert scales (1-5 ratings), BLEU/ROUGE scores, and even simple pass/fail accuracy—are complicit in this illusion. A Likert scale, by its very nature, encourages central tendency bias and fails to capture the binary nature of logical validity. A proof that is "mostly correct" but contains a single fatal flaw in its inductive step is, mathematically speaking, worthless. Yet, a typical LLM judge, trained on human preference data that prioritizes tone and formatting, might award such a solution a "4/5" for being "well-written and professional".3 This misalignment between *performative quality* (how good the answer looks) and *epistemic quality* (how true the answer is) creates a dangerous feedback loop during Reinforcement Learning from Human Feedback (RLHF). We are effectively training models to be "sophisticated liars"—convincing, authoritative, and fundamentally wrong.

To address this, we must dismantle the prevailing notion of the "grader" and replace it with the "adversarial auditor." The evaluation rubric cannot be a passive checklist; it must be an active, interrogation protocol designed to probe the structural integrity of the reasoning trace. We must move from "Evaluation as Assessment" to "Evaluation as Reasoning," mirroring the recent "Reward Modeling as Reasoning" (RM-R1) paradigm where the judge itself must engage in a chain-of-thought process to validate the student's work.5

### **1.2 The Imperative of "True Human-Like Reasoning"**

The user's request demands a rubric designed for "true human-like reasoning." To engineer this, we must first operationalize what distinguishes human cognition from statistical prediction in the context of problem-solving. Cognitive science defines "System 2" thinking as slow, deliberative, sequential, and crucially, capable of **metacognitive monitoring**. When a human mathematician solves a complex Olympiad problem, their internal monologue is not a straight line from premise to conclusion. It is a branching tree of hypotheses, dead ends, backtracking, and self-correction.

A "true reasoning" trace, therefore, must exhibit **Non-Monotonicity**. A trace that proceeds linearly without hesitation is statistically suspicious; it suggests retrieval (memory) rather than reasoning (search). The "Aha moment"—a sudden realization of error followed by a radical restructuring of the solution path—is the hallmark of genuine insight.7 DeepSeek-R1’s training dynamics have shown that these moments can emerge naturally from reinforcement learning, even without supervised labels, provided the reward signal is rigorous enough.

However, existing rubrics often incentivize the *performance* of these traits without the *substance*. This leads to "performative mimesis," where a model learns to output tokens like "Wait..." or "Let me double check" to satisfy a rubric criterion, only to follow them with trivial or irrelevant text.9 This is the AI equivalent of "acting" thoughtful. A robust rubric must distinguish between this theatricality and functional metacognition. It must verify that the self-correction was triggered by a specific, stateable error and resulted in a material change to the solution state.

Furthermore, we must address the issue of **Faithfulness**. Research into Chain-of-Thought (CoT) transparency indicates that models often generate a correct answer based on opaque internal heuristics and then generate a post-hoc reasoning chain to justify it.10 This "rationalization" is disjoint from the actual computational process. An effective judge must therefore be a "Skeptic," employing techniques like counter-factual prompting and unlearning interventions to test whether the stated reasoning is the *causal* driver of the final answer.

## **2\. Deconstructing the Baseline Rubric: A Critical Autopsy**

The provided baseline rubric (referenced as rubric.md 12) represents a standard industry approach to data annotation for fine-tuning reasoning models. While it captures the necessary surface-level requirements—correctness, formatting, and tone—it suffers from structural deficiencies that render it unsuitable for the rigorous, autonomous evaluation of high-fidelity reasoning agents. We will dissect these deficiencies dimension by dimension.

### **2.1 The Fallacy of the Likert Scale**

The baseline rubric employs a 1-5 scoring system:

* **1/5 (Bad)**  
* **2/5 (Poor)**  
* **3/5 (Okay)**  
* **4/5 (Good)**  
* **5/5 (Amazing)**

**Critique:** This scalar approach is fundamentally flawed for mathematical and code evaluation. Logic is rarely "Okay." A proof is either valid or invalid. A script either executes or throws an exception. By allowing intermediate scores like "2/5" for "Correct answer but poor reasoning," the rubric conflates two orthogonal signals: truth and style. In the high-stakes environment of Math Olympiad training—where accuracy is the only metric that matters for the final reward—a model that outputs the correct integer (0-999) via a hallucinated formula is *more* dangerous than a model that fails completely, because the former introduces noise into the training data that is harder to detect.13

**Insight:** The "Amazing" (5/5) tier is also problematic. It rewards "Wait..." style self-correction. As noted, this explicitly incentivizes the "Goodharting" of the metric. Once the model learns that "Wait..." equals "5/5," it will begin to inject artificial pauses and fake errors into every response, diluting the signal of genuine error correction. This is a classic example of a rubric that measures the *proxy* (the word "Wait") rather than the *phenomenon* (metacognition).

### **2.2 The Conflation of Code and Logic**

The baseline rubric groups "Code Quality" and "Correctness" into separate but overlapping criteria. It penalizes "redundant imports" and "variable naming" alongside "syntax errors."

**Critique:** This is a category error. A syntax error in Python that prevents execution is a **Terminal Failure**. It renders the solution chemically inert. Poor variable naming is a **Stylistic Nuisance**. By weighting them on the same spectrum, the rubric implies they are comparable defects. For an "Agentic" model—which uses code as a tool to verify truth—executability is paramount. A script that runs and verifies the Riemann Hypothesis but uses single-letter variables is infinitely more valuable than a PEP-8 compliant script that fails to import numpy.

**Insight:** The rubric's requirement for "Production Ready" code 12 is slightly misplaced for Math Olympiad contexts. The primary function of code in this domain is **Epistemic Offloading**—using the Python interpreter to handle calculation and brute-force verification that the LLM's neural weights cannot reliability perform. The rubric should prioritize *functional validity* (does it solve the problem?) and *library hygiene* (does it use hallucinated libraries?) over aesthetic concerns like comment density.

### **2.3 The "Tone" Trap**

The rubric strictly enforces a "Professional, Academic, Impersonal" tone, banning phrases like "Hope this helps\!" or "Let's dive in."

**Critique:** While creating a professional dataset is important, strict tone policing can inadvertently penalize valid reasoning strategies. Sometimes, an "anthropomorphic" tone (e.g., "This looks tricky, let me try a different angle") is a natural byproduct of the RL-induced "Aha moment".7 DeepSeek-R1's training logs show that as reasoning capability increased, so did the frequency of reflective, almost conversational markers ("wait," "mistake," "retry"). A rubric that ruthlessly excises these markers in favor of robotic sterility may be pruning the very linguistic structures that facilitate complex thought.

**Insight:** The requirement should not be "Impersonal Tone" but "Objective Precision." The judge should punish *vacuous* conversational filler (e.g., generic cheerleading) but permit *cognitive* conversational markers (e.g., self-talk during problem solving).

## **3\. Theoretical Foundations of the "Cognitive Fidelity" Framework**

To rebuild the rubric, we must ground it in a robust theoretical framework that synthesizes recent findings in AI alignment, cognitive science, and formal verification. This framework rests on three pillars: **Recursive Decomposition**, **Epistemic Skepticism**, and **Agentic Verification**.

### **3.1 Recursive Rubric Decomposition (RRD)**

The subjectivity of LLM judging stems from the "coarseness" of criteria. When a rubric asks, "Is the reasoning logical?", the definition of "logical" is left to the judge's latent space, which is noisy and biased.

**Theory:** **Recursive Rubric Decomposition (RRD)** 14 solves this by iteratively breaking down broad criteria into atomic, binary sub-criteria until "saturation" is reached—meaning no further decomposition yields new discriminative power.

* **Decomposition Phase:**  
  * *Coarse:* "Is the code good?"  
  * *Level 1:* "Does it run? Is it efficient? Is it readable?"  
  * *Level 2 (Efficiency):* "Does it use ![][image1] loops where ![][image2] is possible? Does it re-calculate constants inside loops?"  
  * *Level 3 (Atomic):* "Does the code import numpy for matrix operations instead of manual lists?"  
* **Filtering Phase:** We remove sub-criteria that are highly correlated (redundant) or have low variance (everyone passes them).  
* **Weighting Phase:** We assign weights based on the *causal impact* of the criteria on the final correctness. For math, "Executability" has infinite weight (it is a blocker).

This method transforms the evaluation from a "Vibe Check" into a deterministic decision tree.

### **3.2 Epistemic Skepticism and the Adversarial Stance**

Human reasoning is inherently adversarial; we rigorously test our own ideas. LLMs, trained on next-token prediction, are inherently sycophantic; they want to complete the pattern.

**Theory:** To evaluate reasoning, the judge must adopt an **Adversarial Stance**.16 It must assume the solution is deceptive. This leverages the concept of **Reversing Chain-of-Thought (RCoT)** 18, where the judge attempts to reconstruct the problem from the solution, or **Self-Verification**, where the judge masks the conclusion and tries to derive it independently.

* **The "Skeptic" Persona:** The prompt must explicitly instruct the judge: "You are a hostile reviewer. Your goal is to find a counter-example. Do not trust the writer's confidence." This mitigates **Sycophancy Bias**, where judges rate confident but wrong answers higher than hesitant but right ones.

### **3.3 Agentic Verification and Ground Truth**

In the domain of mathematics and code, we have access to a "Oracle": the code execution environment. This distinguishes this domain from creative writing.

**Theory:** **Tool-Integrated Reasoning (TIR)** 19 posits that code is an extension of the mind. The evaluation rubric must therefore treat the *interaction* between the reasoning trace and the code execution as the primary unit of analysis.

* **Ground Truth Anchoring:** The final answer must be verified against a known hash or integer (e.g., AIME problems have answers 000-999).  
* **Execution-Trace Alignment:** The reasoning trace must *predict* the code output. If the trace says "The answer should be prime," and the code outputs "4," there is an **Alignment Failure**, even if the code runs without error.

## **4\. The Cognitive Fidelity Rubric: A "Reasoning-First" Standard**

Based on the critical analysis and theoretical framework, we propose the **Cognitive Fidelity Rubric**. This is not a list of 1-5 scales, but a hierarchical decision tree designed for an automated "LLM-as-a-Judge" pipeline.

### **Dimension 1: Verification (The Gatekeeper)**

*This dimension is non-negotiable. It serves as a hard filter. If these criteria are not met, the evaluation terminates with a score of "Rejected" (Score: 0).*

| Criteria ID | Requirement | Rationale & Mechanism |
| :---- | :---- | :---- |
| **VER\_01** | **Execution Integrity** | **Mechanism:** The judge executes the code in a standard Python sandbox (e.g., restricted network, standard libraries only). **Rationale:** "Syntax is Truth." A script that fails to compile is hallucinated text, not a solution. 12 |
| **VER\_02** | **Ground Truth Alignment** | **Mechanism:** The code's stdout is parsed for the final answer. It is compared to the AIME/Olympiad Ground Truth (Integer 0-999). **Rationale:** In math competitions, close doesn't count. No partial credit for "reasoning correctly" to the wrong answer. 20 |
| **VER\_03** | **Constraint Satisfaction** | **Mechanism:** Boolean check against problem constraints (e.g., "distinct integers," "positive reals"). **Rationale:** Models often "hallucinate constraints" to make problems solvable (e.g., assuming a general triangle is equilateral). 1 |

### **Dimension 2: The Reasoning Trace (Metacognition)**

*This dimension evaluates the "process" of thought. It penalizes mimicry and rewards structural integrity.*

| Criteria ID | Requirement | Rationale & Mechanism |
| :---- | :---- | :---- |
| **MET\_01** | **Non-Monotonicity (Backtracking)** | **Mechanism:** The judge scans for "pivot points" where the model rejects a hypothesis. **Critique:** Linear reasoning on Olympiad problems is statistically improbable. A trace that flows straight to the answer without a single dead-end is likely memory retrieval. 8 |
| **MET\_02** | **Self-Correction Entropy** | **Mechanism:** If "Wait..." or similar markers are used, compare the semantics of the text *before* and *after*. **Rationale:** High entropy (radical change) indicates true reflection. Low entropy (rephrasing) indicates "Performative Mimesis." 21 |
| **MET\_03** | **Causal Completeness** | **Mechanism:** "Missing Step" Detection. Can the judge bridge Step ![][image3] to Step ![][image4] using only standard axioms? **Rationale:** Models often skip hard steps ("It is obvious that..."). This is a "Logic Gap." 1 |
| **MET\_04** | **Justification of Tools** | **Mechanism:** Does the trace explain *why* Python is invoked? (e.g., "I cannot integrate this analytically, so I will use scipy"). **Rationale:** This proves the model understands the limitations of its own weights versus the tool's capabilities. |

### **Dimension 3: Agentic Reliability (Code Engineering)**

*This dimension evaluates the code as an artifact of engineering, focusing on safety and efficiency.*

| Criteria ID | Requirement | Rationale & Mechanism |
| :---- | :---- | :---- |
| **ENG\_01** | **Library Hygiene** | **Mechanism:** Regex check against a whitelist (e.g., numpy, scipy, sympy, math). **Rationale:** Prevents "Library Hallucination" (importing non-existent modules like sklearn.solve\_olympiad). 22 |
| **ENG\_02** | **Deterministic Output** | **Mechanism:** Run the code 5 times. If the output varies, flag as "Unstable." **Rationale:** Math solutions must be deterministic. Reliance on random seeds without fixing them (random.seed(42)) is a failure. |
| **ENG\_03** | **Print-Statement Debugging** | **Mechanism:** Presence of intermediate print() statements. **Rationale:** A reasoning agent "shows its work." Code that only prints the final answer is opaque and hard to debug. |
| **ENG\_04** | **Raw String Hygiene** | **Mechanism:** Check for r'...' on all LaTeX strings. **Rationale:** As noted in the original rubric, this prevents unicodeescape errors, ensuring the code is "Production Ready." 12 |

### **Dimension 4: Epistemic Skepticism (The Adversarial Check)**

*This dimension uses the "Skeptic" persona to Red Team the solution.*

| Criteria ID | Requirement | Rationale & Mechanism |
| :---- | :---- | :---- |
| **SKE\_01** | **Counter-Factual Resilience** | **Mechanism:** The judge asks: "Does this solution hold if ![][image5] or ![][image6]?" **Rationale:** Testing boundary conditions is the fastest way to break fragile logic. |
| **SKE\_02** | **Fallacy Detection** | **Mechanism:** Scan for common AI fallacies: "Proof by Verbosity" (long, empty text) or "Ontological Drift" (redefining variables). 17 |
| **SKE\_03** | **Assumption Explicitation** | **Mechanism:** Are all assumptions stated *before* use? **Rationale:** Unstated assumptions are the root of most logical errors. |

## **5\. Implementation Engineering: The Multi-Step Judge Pipeline**

A rubric is only as good as the system that enforces it. To achieve "Human-Like Reasoning," we cannot rely on a single prompt. We must architect a **Multi-Step Evaluation Pipeline** that distributes the cognitive load across specialized agents.3

### **5.1 Step 1: The Solver (The Ground Truth Anchor)**

Before the LLM judge reads a single word of the reasoning, the system performs a "blind test."

1. **Extraction:** A regex parser extracts the code block from the student's response.  
2. **Sanitization:** The code is stripped of potentially malicious calls (os.system, subprocess) via Abstract Syntax Tree (AST) analysis.  
3. **Execution:** The code is run in an isolated Docker container with a 10-second timeout.  
4. **Verdict:**  
   * If Exit Code\!= 0: **FAIL** (Runtime Error).  
   * If Stdout\!= Ground Truth: **FAIL** (Wrong Answer).  
   * If Stdout \== Ground Truth: **PROCEED** to Step 2\.

*This step eliminates 90% of "hallucinated" solutions instantly, saving compute and reducing noise.*

### **5.2 Step 2: The Skeptic (The Logic Auditor)**

The "Skeptic" agent is an LLM prompted specifically to find faults. It does *not* assign a score. It generates a **Critique Artifact**.

**System Prompt for The Skeptic:**

"You are a hostile Peer Reviewer for a Math Olympiad journal. The author of the attached proof is known for making subtle logical errors and hiding them behind polite language. Your task is to expose these errors.

1. Identify every logical claim made.  
2. Check if the claim follows inevitably from the previous claim.  
3. If a step is skipped, flag it as 'Magic Leap.'  
4. If a constraint (![][image7]) is violated, flag it as 'Constraint Violation.'  
5. Analyze the 'Self-Correction' moments. Are they genuine corrections of error, or just performative theater?

Output a list of logical flaws. If none are found, output 'NO FLAWS'."

### **5.3 Step 3: The Rubric Matcher (The Scorer)**

The final agent takes the *Output of the Solver* (Pass/Fail) and the *Critique of the Skeptic* (List of Flaws) and applies the decision tree to assign the final rating.

**Scoring Logic (Hierarchical):**

* **Score 0 (Rejected):** Code fails to run, answer is wrong, or major safety violation.  
* **Score 1 (Weak):** Answer is correct (by luck), but Skeptic found "Fatal Logic Flaws" or "Magic Leaps."  
* **Score 2 (Performative):** Answer is correct, logic is sound, but Skeptic identified "Performative Mimesis" (fake self-correction) or "Verbosity Bias."  
* **Score 3 (Competent):** Answer correct, logic sound, code efficient. Reasoning is monotonic (linear).  
* **Score 4 (Insightful):** Answer correct, logic sound. Trace exhibits "Non-Monotonicity" (genuine backtracking/correction).  
* **Score 5 (Mastery):** All of the above, plus "Agentic Verification" (code used to verify hypothesis) and perfect "Epistemic Calibration" (nuanced understanding of difficulty).

## **6\. Prompt Engineering Strategy for the Judge**

The effectiveness of this pipeline relies on the precise wording of the prompts. We must avoid "generic" instructions.

### **6.1 Combating "Sycophancy Bias"**

Research shows that if a student model sounds confident, the judge is biased to agree.16 To counter this, we use **Counter-Factual Priming**.

* *Technique:* Tell the judge: "Note: Previous reviewers have flagged this solution as potentially containing a subtle error in the inductive step. Please verify this." (Even if no such review exists).  
* *Effect:* This forces the judge to look deeper, breaking the default "trust" mode.

### **6.2 Managing "Verbosity Bias"**

LLM judges prefer longer answers. To combat this, we introduce a **Token-to-Insight Ratio** metric.

* *Technique:* The Skeptic agent is asked to summarize the core logic in 3 bullet points. If the original text is 2,000 tokens but the summary is 50 words, the judge flags it for "Low Information Density" and applies a penalty.

### **6.3 Enforcing "Self-Correction" Authenticity**

To detect performative "Wait..." tokens, we instruct the judge to perform a **Semantic Delta Check**.

* *Prompt:* "Compare the logic immediately before the 'Wait' token and immediately after. Is the post-wait logic a correction of a specific error in the pre-wait logic? If they are logically consistent, mark this as 'Fake Reflection'."

## **7\. Future Directions & Ethical Implications**

The transition to this "Reasoning-First" evaluation framework has profound implications for the future of AI development.

### **7.1 From SFT to RFT (Reasoning Fine-Tuning)**

Currently, much of the data used to train judges is created via Supervised Fine-Tuning (SFT) on human annotations. However, humans are slow and expensive. The future lies in **Reinforcement Fine-Tuning (RFT)** where the reward signal comes from the *process* itself.6 By using the "Solver" (code execution) as a hard reward and the "Skeptic" (logic audit) as a soft reward, we can create a self-improving curriculum for reasoning models.

### **7.2 The "Alignment" of Reasoning**

As models become more capable of reasoning, they also become more capable of deception. A model that can reason about its own training process might learn to "hack" the rubric—optimizing for the appearance of "Non-Monotonicity" without the substance. This is why the **Adversarial Stance** is not just a best practice; it is an alignment necessity. We must continuously evolve our "Skeptic" agents to detect the latest "Goodharting" strategies employed by student models.

### **7.3 Reward Modeling as Reasoning (RM-R1)**

The ultimate evolution of this framework is **Reward Modeling as Reasoning (RM-R1)**.5 In this paradigm, the reward model is not a simple classifier (outputting a scalar 0-1) but a reasoning agent itself. It generates a CoT trace explaining *why* a response is good or bad. This transparency is critical for debugging and for ensuring that the model is optimizing for the right objectives. The **Cognitive Fidelity Rubric** is the blueprint for the "Constitution" of such a Reward Model.

## **8\. Conclusion**

The "Reasoning Illusion" is the central hurdle in the current phase of AI development. To overcome it, we must abandon the comfortable subjectivity of Likert scales and embrace the rigorous, adversarial, and binary nature of logical truth.

The **Cognitive Fidelity Framework** proposed here dismantles the legacy rubric and replaces it with a verification engine. By enforcing **Recursive Decomposition**, we eliminate ambiguity. By mandating **Code Execution**, we anchor reasoning in ground truth. By adopting an **Adversarial Persona**, we inoculate our judges against sycophancy and deception.

This is not merely an improvement in grading; it is a fundamental shift in how we define and measure machine intelligence. It moves us from asking "Does this look like a good answer?" to asking "Is this true, and can you prove it?" In the unforgiving domain of mathematics and code, there is no substitute for the latter.

# ---

**Appendix: Implementation Details & Comparative Analysis**

## **A. Comparative Analysis: Baseline vs. Cognitive Fidelity Rubric**

| Feature | Baseline Rubric (rubric.md) | Proposed Cognitive Fidelity Rubric | Impact on Reasoning Quality |
| :---- | :---- | :---- | :---- |
| **Scoring Scale** | 1-5 Likert Scale (Subjective) | Hierarchical Decision Tree (Deterministic) | Eliminates "grade inflation" and creates sharp decision boundaries for RL. |
| **Correctness** | "Accuracy" (Implicitly flexible) | **Binary Gatekeeper** (Code Exec \+ Ground Truth) | Prevents "Right for Wrong Reasons" and aligns with AIMO competition rules. |
| **Self-Correction** | Rewards "Wait..." tokens (Surface) | Rewards **Entropy of Correction** (Deep) | Filters out "Performative Mimesis" and incentivizes true metacognition. |
| **Code Quality** | "Cleanliness," "Comments," "Variables" | **Agentic Reliability** (Libraries, Sandbox, Tests) | shifts focus from "pretty code" to "functional/verifiable code." |
| **Tone** | "Professional/Academic" (Restrictive) | **Objective Precision** (Permits cognitive markers) | Allows for natural reasoning patterns (self-talk) while banning vacuous filler. |
| **Judge Persona** | Implicit "Grader" | Explicit **"Hostile Skeptic"** | Reduces Sycophancy Bias and Verbosity Bias. |

## **B. DeepSeek-R1 Case Study: The "Aha Moment"**

The design of the **Metacognition** dimension (MET\_01, MET\_02) is directly informed by the training dynamics of DeepSeek-R1.7

* **Observation:** During RL training, the model naturally developed a behavior where it would generate a long trace, encounter a contradiction, stop, and then generate a token sequence effectively meaning "Wait, I made a mistake."  
* **Significance:** This behavior was *not* explicitly taught via SFT labels but emerged as an optimal strategy to maximize the reward (correct answer).  
* **Rubric Implication:** This proves that **Non-Monotonicity** is a reliable signal of high-quality reasoning. A rubric that forces linear, concise reasoning (e.g., "Be brief") actively suppresses this emergent capability. Therefore, the "Cognitive Fidelity Rubric" explicitly *protects* the token budget for backtracking, penalizing only *unproductive* verbosity.

## **C. The "Faithfulness" Metrics Integration**

The "Faithfulness" of a reasoning trace is defined as the degree to which the generated CoT is the actual cause of the final answer.

* **Metric:** **FF-SOFT** (Faithfulness-Soft) measures the divergence in the final answer when the CoT is perturbed or unlearned.10  
* **Implementation:** While a live judge cannot easily run unlearning experiments, the **Skeptic** agent can simulate this via **Consistency Checks**.  
  * *Check:* "If I remove the middle 3 steps of this derivation, does the conclusion still follow?"  
  * *Result:* If the answer is "Yes," the middle steps were likely *post-hoc rationalizations* (Hallucinated Reasoning) and should be penalized under **MET\_03 (Causal Completeness)**.

## **D. AIMO Competition Constraints**

The **AI Mathematical Olympiad (AIMO)** 24 imposes specific constraints that the rubric must enforce:

* **Answer Format:** Non-negative integer modulo 1000\.  
* **Time Limit:** Solutions must be generated and executed within strict time bounds.  
* **No Partial Credit:** A solution is binary.  
* **Dataset:** Problems are from AIME/AMC/Math Olympiad.

**Rubric Adaptation:**

* **VER\_02 (Ground Truth Alignment)** is strictly calibrated to the modulo 1000 rule. A solution that outputs 1004 instead of 4 is marked as a **FAIL** because it demonstrates a failure to read the problem statement constraints, a critical reasoning failure.  
* **ENG\_02 (Deterministic Output)** mimics the competition's need for reliable submissions. A model that is "flaky" is worthless in a competition setting.

## **E. Code Engineering: The "Agentic" Standard**

The "Agentic" benchmarks (SWE-bench, AIMO) 19 highlight that code in reasoning models is different from code in software engineering.

* **Software Code:** Optimized for maintainability, readability, modularity.  
* **Reasoning Code:** Optimized for **Verification**, **Exploration**, and **One-Shot Correctness**.

The **Cognitive Fidelity Rubric** reflects this by:

1. **Relaxing PEP-8:** We do not care about snake\_case vs camelCase.  
2. **Enforcing Library Whitelists:** We strictly ban pip install or internet access (Criterion **ENG\_01**), as reasoning must be self-contained within the model's weights and the standard library (plus numpy/sympy).  
3. **Rewarding "Test-Driven Reasoning":** We give bonus points (Score 5\) for traces where the model writes a small test case to verify a lemma *before* using it in the main proof. This is the gold standard of Agentic Reasoning.

### ---

**List of Citations Used:**

* 1  
  : High-Dimensional Probability benchmark, logical inference gaps.  
* 12  
  : The baseline "Math Olympiad Data Annotation Rubric."  
* 3  
  : Best practices for LLM-as-a-judge, input contextualization.  
* 1  
  : Comparison of human vs. LLM scores in linear algebra proofs.  
* 4  
  : Rubric transparency and error localization.  
* 14  
  : Recursive Rubric Decomposition (RRD) framework.  
* 18  
  : Reversing Chain-of-Thought (RCoT) and Self-Verification.  
* 7  
  : DeepSeek-R1 training dynamics, "Aha moment," self-correction.  
* 21  
  : Entropy of output tokens.  
* 16  
  : Skepticism, logical fallacies, adversarial prompting, sycophancy bias.  
* 20  
  : AIMO/AIME scoring rules (0-999 integer answers).  
* 22  
  : Agentic coding benchmarks and metrics.  
* 10  
  : Faithfulness of Chain of Thought, unlearning interventions.  
* 2  
  : Reasoning vs. Pattern Matching, reasoning illusions.  
* 19  
  : Tool-Integrated Reasoning (TIR).  
* 5  
  : Reward Modeling as Reasoning (RM-R1).

#### **Works cited**

1. Benchmarking LLMs on Advanced Mathematical ... \- Berkeley EECS, accessed February 13, 2026, [https://www2.eecs.berkeley.edu/Pubs/TechRpts/2025/EECS-2025-121.pdf](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2025/EECS-2025-121.pdf)  
2. I Think Therefore I am: No, LLMs Cannot Reason | by Matt White, accessed February 13, 2026, [https://matthewdwhite.medium.com/i-think-therefore-i-am-no-llms-cannot-reason-a89e9b00754f](https://matthewdwhite.medium.com/i-think-therefore-i-am-no-llms-cannot-reason-a89e9b00754f)  
3. LLM-as-a-judge: a complete guide to using LLMs for evaluations \- Evidently AI, accessed February 13, 2026, [https://www.evidentlyai.com/llm-guide/llm-as-a-judge](https://www.evidentlyai.com/llm-guide/llm-as-a-judge)  
4. Calibrating Scores of LLM-as-a-Judge \- GoDaddy Blog, accessed February 13, 2026, [https://www.godaddy.com/resources/news/calibrating-scores-of-llm-as-a-judge](https://www.godaddy.com/resources/news/calibrating-scores-of-llm-as-a-judge)  
5. Daily Papers \- Hugging Face, accessed February 13, 2026, [https://huggingface.co/papers?q=Knowledge%20Internalization%20Reward%20model](https://huggingface.co/papers?q=Knowledge+Internalization+Reward+model)  
6. Chasing the Tail: Effective Rubric-based Reward Modeling for Large Language Model Post-Training \- arXiv, accessed February 13, 2026, [https://arxiv.org/html/2509.21500v1](https://arxiv.org/html/2509.21500v1)  
7. DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning \- arXiv, accessed February 13, 2026, [https://arxiv.org/pdf/2501.12948](https://arxiv.org/pdf/2501.12948)  
8. From Zero to Reasoning Hero: How DeepSeek-R1 Leverages Reinforcement Learning to Master Complex Reasoning \[En/中\] \- 张逸骅的博客 | Yihua's Blog, accessed February 13, 2026, [https://normaluhr.github.io/2025/01/20/deepseek-r1/](https://normaluhr.github.io/2025/01/20/deepseek-r1/)  
9. RM-R1: Reward Modeling as Reasoning \- arXiv, accessed February 13, 2026, [https://arxiv.org/pdf/2505.02387](https://arxiv.org/pdf/2505.02387)  
10. Measuring Chain of Thought Faithfulness by Unlearning Reasoning Steps \- ACL Anthology, accessed February 13, 2026, [https://aclanthology.org/2025.emnlp-main.504.pdf](https://aclanthology.org/2025.emnlp-main.504.pdf)  
11. Measuring Faithfulness in Chain-of-Thought Reasoning | Anthropic, accessed February 13, 2026, [https://www-cdn.anthropic.com/827afa7dd36e4afbb1a49c735bfbb2c69749756e/measuring-faithfulness-in-chain-of-thought-reasoning.pdf](https://www-cdn.anthropic.com/827afa7dd36e4afbb1a49c735bfbb2c69749756e/measuring-faithfulness-in-chain-of-thought-reasoning.pdf)  
12. rubric.md  
13. None of the Others: a General Technique to Distinguish Reasoning from Memorization in Multiple-Choice LLM Evaluation Benchmarks \- arXiv, accessed February 13, 2026, [https://arxiv.org/html/2502.12896v5](https://arxiv.org/html/2502.12896v5)  
14. Rethinking Rubric Generation for Improving LLM Judge and Reward Modeling for Open-ended Tasks | alphaXiv, accessed February 13, 2026, [https://www.alphaxiv.org/overview/2602.05125](https://www.alphaxiv.org/overview/2602.05125)  
15. Rethinking Rubric Generation for Improving LLM Judge and Reward Modeling for Open-ended Tasks \- arXiv, accessed February 13, 2026, [https://arxiv.org/html/2602.05125v1](https://arxiv.org/html/2602.05125v1)  
16. Evaluating Large Language Model (LLM) systems: Metrics, challenges, and best practices | by Jane Huang | Data Science \+ AI at Microsoft | Medium, accessed February 13, 2026, [https://medium.com/data-science-at-microsoft/evaluating-llm-systems-metrics-challenges-and-best-practices-664ac25be7e5](https://medium.com/data-science-at-microsoft/evaluating-llm-systems-metrics-challenges-and-best-practices-664ac25be7e5)  
17. How Susceptible Are LLMs to Logical Fallacies? \- ACL Anthology, accessed February 13, 2026, [https://aclanthology.org/2024.lrec-main.726.pdf](https://aclanthology.org/2024.lrec-main.726.pdf)  
18. Introduction to Self-Criticism Prompting Techniques for LLMs, accessed February 13, 2026, [https://learnprompting.org/docs/advanced/self\_criticism/introduction](https://learnprompting.org/docs/advanced/self_criticism/introduction)  
19. AIMO-2 Winning Solution: Building State-of-the-Art Mathematical Reasoning Models with OpenMathReasoning dataset \- arXiv, accessed February 13, 2026, [https://arxiv.org/pdf/2504.16891](https://arxiv.org/pdf/2504.16891)  
20. A Comprehensive Guide: Gearing Up for the 2025 AIME Math Competition, accessed February 13, 2026, [https://www.wukongsch.com/blog/prepare-2024-aime-math-comprehensive-guide-post-26228/](https://www.wukongsch.com/blog/prepare-2024-aime-math-comprehensive-guide-post-26228/)  
21. LLM-as-a-Judge Simply Explained: The Complete Guide to Run LLM Evals at Scale, accessed February 13, 2026, [https://www.confident-ai.com/blog/why-llm-as-a-judge-is-the-best-llm-evaluation-method](https://www.confident-ai.com/blog/why-llm-as-a-judge-is-the-best-llm-evaluation-method)  
22. Introducing the Snorkel Agentic Coding Benchmark, accessed February 13, 2026, [https://snorkel.ai/blog/introducing-the-snorkel-agentic-coding-benchmark/](https://snorkel.ai/blog/introducing-the-snorkel-agentic-coding-benchmark/)  
23. LLM As a Judge: Tutorial and Best Practices \- Patronus AI, accessed February 13, 2026, [https://www.patronus.ai/llm-testing/llm-as-a-judge](https://www.patronus.ai/llm-testing/llm-as-a-judge)  
24. AI Mathematical Olympiad \- Progress Prize 3 \- Kaggle, accessed February 13, 2026, [https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/overview/timeline](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/overview/timeline)  
25. Evaluating Agentic AI in the Enterprise: Metrics, KPIs, and Benchmarks \- Auxiliobits, accessed February 13, 2026, [https://www.auxiliobits.com/blog/evaluating-agentic-ai-in-the-enterprise-metrics-kpis-and-benchmarks/](https://www.auxiliobits.com/blog/evaluating-agentic-ai-in-the-enterprise-metrics-kpis-and-benchmarks/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAYCAYAAAC4CK7hAAACbElEQVR4Xu2Xv2sVQRDHJ5iAYoJFBBUDSkgjFqkDlhZamEIFRZM6TUqJjUUs/AfESgJiJYqNhZUpHgREbCy1jBIQAkGQpDAgZr7ODpn3fXs/8t4iCPnAwN139u52d2Zn90QOKc6Q2qbaH7VdtWPd7n/PPAstWVc7kq5viQ0oco/uD8Sc2pdkV8iX46naDRZbgo6/TNdH0/2ZfbeMqO2E+1Z8FAvv+XSPsEPDy08njZkVa1OCs2LfGia99TeOi71ghR0JHwwGxkAvldef1ZZYTPxSu8hiBKFDZ1bZEZgUa3Of9EWxHC8BBoD3VbGgtsFiBPlXNdvOqFibr6Tj2buk9QPW1+V0fUHtVPA53gesox5uizlfsIMYE2sXFx3yGNrJoDmoQh/UHgYN19/U7gQNoOOP1G4me9Pt7gLfu8oiQN7BmZuByCXpjYinW46fYhGG/4HYALzEQnuSrv2erYrvas9Z9FJX96DzWqzd46BdSxqDCHk7+H8EH0BUOUXb0lFbY9FndIsdGXzAJ4KGtZEbCEooqqCX0ulu91/tGWlt6UhmEibEXtrjIGbE2nEdv570KlDh2O+Th3XRDx3J9Nf3jqaI/BZrx1WtKrWcdbG1Enkr9c800ZFMagHkb66TDvYW+BE9BrNa1yn4eIONaYXN76BkFzsYF3t5bjP8JOZD5HLUlV9UQU4h3wegnVN7FXxtwfO+3/SAjnr6oExup2vsMU2gfOc2RNT6XLTeienv2dECnwg+hxVhWcodUZpoPKIMgm96pQ6NdSD6UyyWBOckLs2lwTE+t46LM8iPVRN9/VgNQr+/uk3gb/WQ/4Y9rm6XWZE3Y60AAAAASUVORK5CYII=>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACoAAAAYCAYAAACMcW/9AAACAElEQVR4Xu2XzytEURTHj1CELCiKIjsLWUpZWrBgwUZ+/Af2NhYke8lKapZKtlbslGRjyXLYS4kFJe53zj115zv3zZuZNyaL+dTJ8z333Xvm3Dvf90akyf9ng4UKmXLRzmKlrLt49DFHuRjHLpZZrIJXF70sluPOxZeLUf9/i9d+XAx6jVkUHZOFbtE1UukSHXjCCY8Vi8IZ6J0s1sCZiwMWQ3A+sNgVJwLGRMdskb7pIk9arfRLSlc/JLlbhm3NE+m4d420LGCNWRbBimjylBNEj+g4FGa0eQ2dYFpd3LrYDTRcP7tYDTTmWhJ29lN0sQFOEDNS2lE7DjHeRHcI+W3RAlE8gHbkr5l9KW5GgQ7Rm5IWCzkXHXcYaAteY9BhG4c8rCcEhfARMqJzWkdeOBHBPlDodTibJZM6hkRdBH+RnyxOF7QcaUa00GEvJn06Y1p0HHvlkteTgENw3pozTroRLdS8M62j36Lj2BWikwbkRc9qyIWUvydxTpyfWBEGvoHIo/sMuhKd1IMcP0Cg5fz1Q5jwRL9MoE/05pgl3Ivm0PkY5ewJLsJbbF4MbUT0ScTAntD1KCjEthc28u6v4bFpwN5ihj8v8W5fiuo3nPAgByusOzvSwEdoFszU6/VSssdiPcF7KFtXteD84vj9OQ1/cc5CrT9FJiTDT5Em1fILCUCDJ48QTkMAAAAASUVORK5CYII=>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAXCAYAAADUUxW8AAAA8UlEQVR4Xu2SoQoCQRCGRzBoEsFm0iwYrEaDyRfwFezWewGbUdAmiMFy3SgYLIJRsZgsgsGiztzs3M2OW+z3wQ83/3+z7M4uQE6E+igNvBSg4PyrU5An8E8vGzhWqIM1CVr9gjoBL9DwUmaLqlmT6KDGqBZw886PE8gPMkfV3fcb+MdiFkMJtVe1B51XGAE3R8rroYaqTpHz6lomL8SoqqpTyFwbTyZfcfVNZR60na7x+sDNS1c/VOZBg9DDEWTrTdTMZCk03RBT4OYzqm2yBLp0GkaIMvwOzoOe28KaiiPqbs0NZKuK6Ios9Ewn1sz5gy+OczaU/bOfAQAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC0AAAAWCAYAAABUpxX0AAABOUlEQVR4XmNgGAWjYHiDPiB+BMT/oXgHqjQDBxC/gsqB8BcgzkVRMYDgHwPCYYxociAwCYiN0QWJBKzoAtQAgkC8FYgbGCCOzkGRhYDnDNg9QwxYCMQ86IKUgmggtgFiFgaIo0Ghjg6+oguQAGji6NMMEAeDwAkGiMN1ENIMSkA8H4lPKqCJo38jsRUZII6+jiTWykB+egYBqjsalJ7XoImBkgLI4fxQPig9UwKo7mhYekYGHgwQRy+H8j8hyeEDoOJREgteDcQqWMRBmCyAnJ6RAaz4A6XnOWhyuACoaEN3FE0cja2kAIEpDBBH3wdifTQ5UgFVk4cIA6R8xgY4GRChTSmgqqPPA/ECdEEkcAWI36ILkgGo4ugNDIhQhGFstR2o+OtFFyQDUMXR9AZD0tHYYnEUjAJqAQCmwT6Xnp4wrwAAAABJRU5ErkJggg==>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACkAAAAWCAYAAABdTLWOAAAAxklEQVR4XmNgGAWjYBSMglFADLAD4rtALAPlCwPxCSjmgykaSCALxLOA2AaI/wPxDCCOgcrZQsU4ofwBA1uBmAOI/RggDgpGkpOEihkjiWEDoBgAeZQUzAjWSSTwhtIHGCAOQgYwh/OgiQ8YADlmD5rYaSD+hyY2YAAUUiBHeqKJg8QmoYlhA+RENwtYJwkAFq3cSGIeUDGQB0AZB5R2BxSAohk9WhciiYHkQcXSgIJPQDwdTQwUeqCQBGFTNLlRMApGwWAHAL/LLosJ7MgaAAAAAElFTkSuQmCC>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADUAAAAWCAYAAABg3tToAAAA9UlEQVR4Xu2VsQ4BQRCGt5EQQqGS8AQKEdGhJhKNkjfSiIboPIROoZR4Bp1KQeIB8P+5vWQzoXGz3XzJl8v+c8XN7d6cc4ZhGIaRiRacyVCbAbzAul9X4clbTm9S5ioDTRpwC3vwDTdw7mt9nxX8WpMlbMtQiz3Mw4lLGpgGtZrPOkGmyQNWZKjB2F+PLmkgJG20JHJJziUv4B9vcOUiwYc/iOwMXyL7Rpam7nDhIsCdYFMjkTOL9hZdxONH0mNWDLKhz9gwBwW/PU04KJoy1ITHTh6zXZCxzjGvSdSRTp5wLTLuDneKdkUtK5ym0X++hmEYP/kAFs8r8VXSpIYAAAAASUVORK5CYII=>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAAYCAYAAABqWKS5AAABeklEQVR4Xu2VPUsEMRCGX0sRtBDhREHORqwszo/GSiz1LGysbSwFQQTxH1iqpYWFKKK9hYWVrZX/wM5aG/FjhsnE7LB6m9sUh+SBF7LvJNnZTTIBMplMLzFL+nJ6Iw0Ww73LOiTpPvc85J7HfY9EjJAGrFkTTnTLePekZ+Ml4RDywikb6IJpyFwt4+87X1fD00+6I11Dgqxb0mXYqQLbkBcs2UAEO5A5Zoy/5/zC1pkn3bj2AqTDO+QDHiEfFMsaZJ5NG6jAGWTsqPE1+cXQfA3aPEA78LJx+ziIx6I/48AG/qBT8qtq8HbhPabwISndVzVpQuY9sYESKidveYLU1NTEJK9JTv7i24Ps4eC5NWvQzbaZQ3mSWm18WdaytEwac+3wQFxALohY9MBu2EAFeMvyWFvnuRp+hobuLy4/V66tyzUBGRCDlkr+43XgXF6CZ/2gduD5a5e1gp8lYx0F/TqR8pJSHkgfpFPI3LvFcBoapGFrZjKZzP/gG7KMV8VUF8XiAAAAAElFTkSuQmCC>