"""
DeepResearcher v2: H100-Optimized Math Research Agent

Major upgrades over v1:
    - Model: DS-R1-Distill-Qwen-32B-AWQ (2.2x faster, higher pass@1 than 70B)
    - Majority voting: Generate N solutions, take consensus answer
    - Tool-Integrated Reasoning (TIR): Execute code mid-generation
    - Natural Language Verifier: Catch logic errors code can't detect
    - Balanced prompting: Anti-confirmation bias (from Gemini Deep Think)
    - Dynamic time allocation: Spend more time on harder problems
    - Auto-detect chat template (Qwen vs Llama)
    - Higher token limits (8192+ for long reasoning chains)

Usage (Kaggle Notebook):
    researcher = DeepResearcher(
        model_path="/kaggle/input/aimo-model-32b-awq/",
        time_limit_hours=4.5,
        num_samples=16,
    )
    researcher.run(problems, "/kaggle/working/research_data.jsonl")
"""

import json
import logging
import re
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path

from agent.sandbox import run_verification, extract_code_blocks
from agent.prompts import (
    build_system_prompt,
    build_generate_prompt,
    build_verify_prompt,
    build_nl_verify_prompt,
    build_correct_prompt,
    extract_answer,
    extract_nl_verdict,
    detect_model_family,
    detect_model_family,
    format_tir_continuation,
    classify_topic,
    TOPIC_PATCHES,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================

class TimeLimitExceeded(Exception):
    """Raised when the hard timer triggers a graceful exit."""
    pass


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Attempt:
    """A single generate/correct attempt within a research cycle."""
    attempt_number: int
    solution_text: str
    extracted_answer: str | None
    code_blocks_found: int
    verification_passed: bool
    verification_output: str
    nl_verification: str = ""
    duration_seconds: float = 0.0


@dataclass
class ResearchTrace:
    """Full research trace for one problem -- the output artifact."""
    problem_id: str
    problem_text: str
    source: str
    difficulty: str
    attempts: list[Attempt] = field(default_factory=list)
    majority_vote_answers: dict = field(default_factory=dict)
    final_answer: str | None = None
    solved: bool = False
    total_duration_seconds: float = 0.0
    total_attempts: int = 0
    strategy: str = ""  # "majority_vote" | "self_correct" | "exhausted"

    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# DeepResearcher v2
# =============================================================================

class DeepResearcher:
    """
    H100-optimized research agent for generating math reasoning traces.

    v2 implements:
    - Majority voting with N parallel samples
    - Tool-Integrated Reasoning (TIR)
    - Natural Language Verification
    - Dynamic time allocation
    - Auto model family detection
    """

    def __init__(
        self,
        model_path: str,
        time_limit_hours: float = 4.5,
        num_samples: int = 16,
        max_retries: int = 3,
        generate_temperature: float = 0.7,
        correct_temperature: float = 0.3,
        max_generate_tokens: int = 8192,
        max_correct_tokens: int = 4096,
        code_timeout: int = 30,
        gpu_memory_utilization: float = 0.92,
        max_model_len: int = 16384,
        patch_text: str | None = None,
        enable_tir: bool = True,
        enable_nl_verify: bool = True,
        tir_max_rounds: int = 3,
        dry_run: bool = False,
    ):
        """
        Initialize the DeepResearcher v2.

        Args:
            model_path: Path to the AWQ-quantized model weights.
            time_limit_hours: Hard time limit (default 4.5hr = 5hr - 30min buffer).
            num_samples: Number of parallel samples for majority voting.
            max_retries: Self-correction attempts for unresolved problems.
            generate_temperature: Temperature for generation (creative).
            correct_temperature: Temperature for corrections (precise).
            max_generate_tokens: Max tokens per generation (8192 for long CoT).
            max_correct_tokens: Max tokens per correction.
            code_timeout: Timeout for sandboxed code execution (seconds).
            gpu_memory_utilization: Fraction of GPU memory to use.
            max_model_len: Maximum sequence length for the model.
            patch_text: Optional System Prompt Patch from analysis.
            enable_tir: Enable Tool-Integrated Reasoning.
            enable_nl_verify: Enable Natural Language Verification.
            tir_max_rounds: Max code execution rounds per TIR generation.
            dry_run: If True, skip vLLM init (for testing locally).
        """
        self.model_path = model_path
        self.time_limit_hours = time_limit_hours
        self.time_limit_seconds = time_limit_hours * 3600
        self.num_samples = num_samples
        self.max_retries = max_retries
        self.generate_temperature = generate_temperature
        self.correct_temperature = correct_temperature
        self.max_generate_tokens = max_generate_tokens
        self.max_correct_tokens = max_correct_tokens
        self.code_timeout = code_timeout
        self.enable_tir = enable_tir
        self.enable_nl_verify = enable_nl_verify
        self.tir_max_rounds = tir_max_rounds
        self.dry_run = dry_run
        self.start_time = None

        # Auto-detect model family for chat template
        self.model_family = detect_model_family(model_path)
        logger.info(f"Detected model family: {self.model_family}")

        # Build system prompt (with optional patches)
        self.system_prompt = build_system_prompt(patch_text)

        # Initialize vLLM engine
        if not dry_run:
            self._init_vllm(model_path, gpu_memory_utilization, max_model_len)
        else:
            self.llm = None
            logger.info("DRY RUN mode -- vLLM not initialized")

    def _init_vllm(self, model_path: str, gpu_mem: float, max_len: int):
        """Initialize the vLLM inference engine."""
        from vllm import LLM

        logger.info(f"Loading model from {model_path}")
        logger.info(f"  Model family:         {self.model_family}")
        logger.info(f"  GPU memory util:      {gpu_mem:.0%}")
        logger.info(f"  Max model length:     {max_len}")
        logger.info(f"  Majority vote N:      {self.num_samples}")
        logger.info(f"  TIR enabled:          {self.enable_tir}")
        logger.info(f"  NL Verify enabled:    {self.enable_nl_verify}")

        self.llm = LLM(
            model=model_path,
            # NOTE: No quantization= or dtype= specified.
            # GPT-OSS 20B uses native MXFP4 (E2M1 + E8M0 scale) for MoE
            # weights, which vLLM auto-detects from the model config.
            # Specifying quantization="awq" here would be WRONG and cause
            # loading failures or silent quality degradation.
            gpu_memory_utilization=gpu_mem,
            max_model_len=max_len,
            trust_remote_code=True,
            enforce_eager=True,
        )
        self.tokenizer = self.llm.get_tokenizer()

        logger.info("Model loaded successfully")

    # =========================================================================
    # Timer Management
    # =========================================================================

    def _check_timer(self):
        """Check if we have exceeded the time limit."""
        if self.start_time is None:
            return
        elapsed = time.time() - self.start_time
        remaining = self.time_limit_seconds - elapsed
        if remaining <= 0:
            raise TimeLimitExceeded(
                f"Time limit of {self.time_limit_hours:.1f}hr exceeded "
                f"(elapsed: {elapsed / 3600:.2f}hr)"
            )

    def _remaining_seconds(self) -> float:
        """Get remaining seconds."""
        if self.start_time is None:
            return self.time_limit_seconds
        return max(0, self.time_limit_seconds - (time.time() - self.start_time))

    def _elapsed_str(self) -> str:
        """Human-readable elapsed time."""
        if self.start_time is None:
            return "0:00:00"
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}"

    def _remaining_str(self) -> str:
        """Human-readable remaining time."""
        remaining = self._remaining_seconds()
        if remaining <= 0:
            return "0:00:00"
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        return f"{hours}:{minutes:02d}"

    # =========================================================================
    # LLM Inference
    # =========================================================================

    def _generate_text(
        self,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate a single text response using the vLLM engine."""
        if self.dry_run:
            return (
                "[DRY RUN] This is a placeholder response.\n\n"
                "```python\nresult = 6 * 7\nprint(f'Result: {result}')\n```\n\n"
                "Let me verify by trying to disprove: 6*7 = 42 is well-known.\n"
                "**ANSWER: 42**"
            )

        from vllm import SamplingParams

        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=0.95,
            max_tokens=max_tokens,
        )

        conversation = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        full_prompt = self.tokenizer.apply_chat_template(
            conversation,
            tokenize=False,
            add_generation_prompt=True,
        )

        outputs = self.llm.generate([full_prompt], sampling_params)
        return outputs[0].outputs[0].text

    def _generate_batch(
        self,
        user_prompt: str,
        n: int,
        temperature: float,
        max_tokens: int,
    ) -> list[str]:
        """Generate N solutions in a single batch (majority voting)."""
        if self.dry_run:
            return [self._generate_text(user_prompt, temperature, max_tokens)
                    for _ in range(min(n, 3))]  # Only 3 in dry run

        from vllm import SamplingParams

        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=0.95,
            max_tokens=max_tokens,
            n=n,  # vLLM natively supports generating N completions
        )

        conversation = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        full_prompt = self.tokenizer.apply_chat_template(
            conversation,
            tokenize=False,
            add_generation_prompt=True,
        )

        outputs = self.llm.generate([full_prompt], sampling_params)
        return [output.text for output in outputs[0].outputs]

    # =========================================================================
    # Tool-Integrated Reasoning (TIR)
    # =========================================================================

    def _generate_with_tir(
        self,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Generate with Tool-Integrated Reasoning.

        The model generates text. When it produces a ```python block,
        we execute it, inject the output, and let the model continue.
        """
        if not self.enable_tir:
            return self._generate_text(user_prompt, temperature, max_tokens)

        if self.dry_run:
            return self._generate_text(user_prompt, temperature, max_tokens)

        from vllm import SamplingParams

        full_response = ""
        remaining_tokens = max_tokens
        conversation = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        current_prompt = self.tokenizer.apply_chat_template(
            conversation,
            tokenize=False,
            add_generation_prompt=True,
        )

        for tir_round in range(self.tir_max_rounds + 1):
            sampling_params = SamplingParams(
                temperature=temperature,
                top_p=0.95,
                max_tokens=remaining_tokens,
                stop=["```\n\n"],  # Stop after code block ends
            )

            outputs = self.llm.generate([current_prompt], sampling_params)
            chunk = outputs[0].outputs[0].text

            full_response += chunk
            remaining_tokens -= len(outputs[0].outputs[0].token_ids)

            if remaining_tokens <= 100:
                break  # No budget left

            # Check if the model produced a code block that we should execute
            code_blocks = extract_code_blocks(full_response)
            if not code_blocks or tir_round >= self.tir_max_rounds:
                break  # No code to execute or max rounds reached

            # Execute the LAST code block
            last_code = code_blocks[-1]
            passed, exec_output = run_verification(
                f"```python\n{last_code}\n```",
                timeout=self.code_timeout,
            )

            # Inject execution result and continue generation
            tir_output = format_tir_continuation(
                model_family=self.model_family,
                execution_result=exec_output[:2000],  # Cap output length
            )
            full_response += tir_output

            # --- State Compression (P1: anti-context-rot) ---
            # Instead of appending to an ever-growing prompt, rebuild from
            # scratch with a compact state summary. This keeps each TIR round
            # under ~6K tokens regardless of how many rounds have occurred.
            state_summary = (
                f"## State After Round {tir_round + 1}\n"
                f"Code execution result: {exec_output[:1000]}\n\n"
                f"Continue solving the problem. Build on the code results above. "
                f"Do NOT re-derive what you have already computed."
            )
            state_conversation = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": f"[Previous reasoning omitted for brevity]\n{state_summary}"},
                {"role": "user", "content": "Continue from where you left off. Use the code results above."},
            ]
            current_prompt = self.tokenizer.apply_chat_template(
                state_conversation,
                tokenize=False,
                add_generation_prompt=True,
            )

            logger.info(
                f"    TIR round {tir_round + 1}: "
                f"{'PASS' if passed else 'FAIL'} | "
                f"Output: {exec_output[:80]}... "
                f"(prompt compressed to ~{len(current_prompt)//4} tokens)"
            )

        return full_response

    # =========================================================================
    # Natural Language Verification
    # =========================================================================

    def _nl_verify(self, problem_text: str, solution: str) -> tuple[bool, str]:
        """Run natural language verification on a solution."""
        if not self.enable_nl_verify:
            return True, "NL Verify disabled"

        nl_prompt = build_nl_verify_prompt(problem_text, solution)
        nl_response = self._generate_text(
            nl_prompt,
            temperature=0.2,  # Low temperature for careful review
            max_tokens=1024,
        )
        return extract_nl_verdict(nl_response)

    # =========================================================================
    # Majority Voting (with Early Stopping)
    # =========================================================================

    def _check_early_consensus(
        self,
        answer_counts: Counter,
        total_generated: int,
    ) -> str | None:
        """
        Check if we have early consensus to stop generating more samples.

        Thresholds (from NemoSkills 1st place):
          - With 4 samples: need 3/4 (75%) agreement
          - With 8 samples: need 5/8 (63%) agreement
          - With 12+ samples: need 7/12 (58%) agreement
        """
        if not answer_counts:
            return None

        top_answer, top_count = answer_counts.most_common(1)[0]
        total_votes = sum(answer_counts.values())

        # Scale threshold: stricter with fewer samples
        if total_generated <= 4:
            threshold = 0.75  # 3/4 must agree
        elif total_generated <= 8:
            threshold = 0.63  # 5/8 must agree
        else:
            threshold = 0.58  # 7/12 must agree

        consensus_ratio = top_count / total_votes
        if consensus_ratio >= threshold:
            logger.info(
                f"    ⚡ Early consensus after {total_generated} samples: "
                f"'{top_answer}' at {consensus_ratio:.0%} (threshold: {threshold:.0%})"
            )
            return top_answer

        return None

    def _majority_vote(
        self,
        problem: dict,
    ) -> tuple[list[Attempt], dict, str | None]:
        """
        Generate N solutions in waves with early stopping on consensus.

        Wave strategy (inspired by NemoSkills 1st place):
          - Wave 1: Generate 4 → check consensus (saves 75% compute if strong)
          - Wave 2: Generate 4 more (total 8) → check consensus (saves 50%)
          - Wave 3: Generate 4 more (total 12) → check consensus (saves 25%)
          - Wave 4: Generate remaining to reach num_samples → final vote

        Returns:
            (attempts, vote_counts, consensus_answer)
        """
        problem_text = problem["problem_text"]
        generate_prompt = build_generate_prompt(problem_text)
        effective_n = min(self.num_samples, 8) if self.enable_tir else self.num_samples
        wave_size = 4

        logger.info(
            f"    Generating up to {effective_n} samples "
            f"(wave_size={wave_size}, early_stop=on)..."
        )

        batch_start = time.time()
        all_solutions = []
        attempts = []
        answer_counts = Counter()
        early_stopped = False
        consensus = None

        # Generate in waves
        generated = 0
        while generated < effective_n:
            self._check_timer()
            wave_n = min(wave_size, effective_n - generated)

            if self.enable_tir:
                # TIR: generate one at a time within the wave
                wave_solutions = []
                for _ in range(wave_n):
                    self._check_timer()
                    sol = self._generate_with_tir(
                        generate_prompt,
                        temperature=self.generate_temperature,
                        max_tokens=self.max_generate_tokens,
                    )
                    wave_solutions.append(sol)
            else:
                # Batch: generate wave_n at once
                wave_solutions = self._generate_batch(
                    generate_prompt,
                    n=wave_n,
                    temperature=self.generate_temperature,
                    max_tokens=self.max_generate_tokens,
                )

            # Process wave results
            wave_duration = (time.time() - batch_start) / max(generated + len(wave_solutions), 1)
            for i, solution in enumerate(wave_solutions):
                code_blocks = extract_code_blocks(solution)
                passed, verify_output = run_verification(solution, timeout=self.code_timeout)
                answer = extract_answer(solution)

                attempt = Attempt(
                    attempt_number=generated + i + 1,
                    solution_text=solution,
                    extracted_answer=answer,
                    code_blocks_found=len(code_blocks),
                    verification_passed=passed,
                    verification_output=verify_output,
                    duration_seconds=wave_duration,
                )
                attempts.append(attempt)

                if answer is not None:
                    weight = 2 if passed else 1
                    answer_counts[answer] += weight

            generated += len(wave_solutions)
            all_solutions.extend(wave_solutions)

            # Check for early consensus (don't check on last wave)
            if generated < effective_n:
                early_answer = self._check_early_consensus(answer_counts, generated)
                if early_answer is not None:
                    consensus = early_answer
                    early_stopped = True
                    break

        batch_duration = time.time() - batch_start
        saved_pct = max(0, (effective_n - generated) / effective_n * 100)
        logger.info(
            f"    Generation: {generated}/{effective_n} solutions in {batch_duration:.1f}s"
            f"{f' (saved {saved_pct:.0f}% via early stop)' if early_stopped else ''}"
        )

        # Final consensus if not already found via early stopping
        if consensus is None:
            vote_dict = dict(answer_counts)
            if answer_counts:
                top_answer, top_count = answer_counts.most_common(1)[0]
                total_votes = sum(answer_counts.values())
                consensus_ratio = top_count / total_votes
                logger.info(
                    f"    Majority vote: '{top_answer}' with {top_count}/{total_votes} "
                    f"votes ({consensus_ratio:.0%})"
                )
                if consensus_ratio >= 0.3:  # Accept if ≥30% agreement (weighted)
                    consensus = top_answer
        else:
            vote_dict = dict(answer_counts)

        return attempts, vote_dict, consensus

    # =========================================================================
    # GenSelect (Generative Solution Selection)
    # =========================================================================

    def _genselect(
        self,
        problem: dict,
        attempts: list,
    ) -> str | None:
        """
        Use the model to select the best solution via comparative evaluation.

        Inspired by NemoSkills (AIMO2 1st place): when majority vote has
        weak consensus, feeding all solution summaries back into the model
        and asking it to pick the best one can recover +3-5% accuracy.

        Returns:
            The selected answer string, or None if selection fails.
        """
        # Only consider attempts that have an extracted answer
        valid = [a for a in attempts if a.extracted_answer is not None]
        if len(valid) < 2:
            return None

        # Build solution summaries (truncated to fit context)
        summaries = []
        max_per_summary = 2000  # ~500 tokens each
        for i, att in enumerate(valid):
            verified = "✓ code verified" if att.verification_passed else "✗ unverified"
            summary = att.solution_text[:max_per_summary]
            summaries.append(
                f"## Solution {i + 1} (Answer: {att.extracted_answer}, {verified})\n"
                f"{summary}"
            )

        genselect_prompt = (
            f"You are evaluating {len(valid)} candidate solutions to this problem:\n\n"
            f"{problem['problem_text']}\n\n"
            f"{'\n---\n'.join(summaries)}\n\n"
            f"## Task\n"
            f"Analyze each solution's reasoning quality. Identify which has:\n"
            f"1. The most rigorous mathematical reasoning\n"
            f"2. Correct intermediate steps verified by code\n"
            f"3. No logical gaps or unproven assumptions\n\n"
            f"Output ONLY the number of the best solution: BEST: [number]"
        )

        logger.info(f"    GenSelect: evaluating {len(valid)} candidates...")

        response = self._generate_text(
            genselect_prompt,
            temperature=0.1,  # Low temp for careful evaluation
            max_tokens=2048,
        )

        # Extract selection
        match = re.search(r"BEST:\s*(\d+)", response)
        if match:
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(valid):
                selected = valid[idx].extracted_answer
                logger.info(f"    GenSelect chose Solution {idx + 1}: '{selected}'")
                return selected

        logger.info("    GenSelect failed to extract a valid selection")
        return None

    # =========================================================================
    # Research Loop (v2)
    # =========================================================================

    def research_problem(self, problem: dict) -> ResearchTrace:
        """
        Full research loop for one problem:
        1. Majority vote (N parallel samples)
        2. If consensus found → optional NL verify → done
        3. If no consensus → self-correct top candidate

        Args:
            problem: Dict with keys: id, problem_text, source, difficulty

        Returns:
            ResearchTrace with all attempts and the final result.
        """
        problem_start = time.time()
        problem_id = problem.get("id", "unknown")
        problem_text = problem["problem_text"]
        source = problem.get("source", "unknown")
        difficulty = problem.get("difficulty", "unknown")

        trace = ResearchTrace(
            problem_id=problem_id,
            problem_text=problem_text,
            source=source,
            difficulty=difficulty,
        )

        logger.info(
            f"[{self._elapsed_str()}] Researching problem {problem_id} "
            f"({source}, {difficulty}) | Remaining: {self._remaining_str()}"
        )

        # --- Topic Classification: inject domain-specific strategy hints ---
        original_system_prompt = self.system_prompt
        topic = classify_topic(problem_text)
        if topic and topic in TOPIC_PATCHES:
            self.system_prompt = build_system_prompt(TOPIC_PATCHES[topic])
            logger.info(f"    Topic classified: {topic} (injecting strategy patch)")
        else:
            logger.info(f"    Topic: unclassified (using baseline prompt)")

        try:
            return self._research_problem_inner(problem, trace, problem_start, problem_text)
        finally:
            # Always restore original system prompt to avoid topic leak
            self.system_prompt = original_system_prompt

    def _research_problem_inner(
        self,
        problem: dict,
        trace: ResearchTrace,
        problem_start: float,
        problem_text: str,
    ) -> ResearchTrace:
        """Inner research loop, separated to allow system prompt restore via try/finally."""
        self._check_timer()
        attempts, vote_dict, consensus = self._majority_vote(problem)
        trace.attempts.extend(attempts)
        trace.majority_vote_answers = vote_dict

        # --- Phase 1B: GenSelect (if weak consensus) ---
        if consensus is not None:
            # Check if consensus is weak (< 40% of weighted votes)
            total_votes = sum(vote_dict.values()) if vote_dict else 0
            top_votes = vote_dict.get(consensus, 0) if vote_dict else 0
            consensus_strength = top_votes / total_votes if total_votes > 0 else 0

            if consensus_strength < 0.4 and len(attempts) >= 4:
                # Weak consensus — try GenSelect for a better pick
                logger.info(
                    f"    Weak consensus ({consensus_strength:.0%}), "
                    f"trying GenSelect..."
                )
                genselect_answer = self._genselect(problem, attempts)
                if genselect_answer is not None:
                    consensus = genselect_answer
                    logger.info(f"    GenSelect overrode majority vote → '{consensus}'")

        if consensus is not None:
            # Optional NL verification of the consensus answer
            best_solution = None
            for att in attempts:
                if att.extracted_answer == consensus and att.verification_passed:
                    best_solution = att.solution_text
                    break
            if best_solution is None:
                for att in attempts:
                    if att.extracted_answer == consensus:
                        best_solution = att.solution_text
                        break

            if best_solution and self.enable_nl_verify:
                nl_ok, nl_msg = self._nl_verify(problem_text, best_solution)
                logger.info(f"    NL Verify: {nl_msg[:80]}")
                if not nl_ok:
                    # NL verifier found an issue — fall through to self-correct
                    logger.info("    NL Verify flagged error, proceeding to self-correction")
                    consensus = None  # Reset consensus

            if consensus is not None:
                trace.final_answer = consensus
                trace.solved = True
                # Tag strategy based on how we got the answer
                trace.strategy = "majority_vote"
                trace.total_duration_seconds = time.time() - problem_start
                trace.total_attempts = len(attempts)
                logger.info(
                    f"  SOLVED (majority vote): {consensus} "
                    f"({trace.total_duration_seconds:.1f}s)"
                )
                return trace

        # --- Phase 2: Self-Correction (if no majority consensus) ---
        logger.info("    No strong consensus, trying self-correction...")

        # Pick the best attempt as starting point
        best_attempt = None
        for att in sorted(attempts, key=lambda a: (
            a.verification_passed,
            a.extracted_answer is not None,
        ), reverse=True):
            best_attempt = att
            break

        if best_attempt is None:
            trace.strategy = "exhausted"
            trace.total_duration_seconds = time.time() - problem_start
            trace.total_attempts = len(attempts)
            return trace

        previous_solution = best_attempt.solution_text
        error_message = best_attempt.verification_output

        for retry in range(1, self.max_retries + 1):
            self._check_timer()
            attempt_start = time.time()

            if best_attempt.verification_passed and best_attempt.extracted_answer is None:
                error_message = (
                    "Your solution did not include a clearly stated final answer. "
                    "Please state your answer in the format: **ANSWER: [value]**"
                )

            # [Forceful Feedback] Banish hallucinated 'assistantcommentary' tool
            if "assistantcommentary" in previous_solution:
                error_message = (
                    "SYSTEM ERROR: You used 'assistantcommentary'. This is BANNED. "
                    "You MUST use standard markdown code blocks:\n"
                    "```python\n"
                    "# code here\n"
                    "```\n"
                    "Retrying with CORRECT format..."
                )

            correct_prompt = build_correct_prompt(
                problem_text, previous_solution, error_message
            )
            solution = self._generate_with_tir(
                correct_prompt,
                temperature=self.correct_temperature,
                max_tokens=self.max_correct_tokens,
            )

            code_blocks = extract_code_blocks(solution)
            verification_passed, verification_output = run_verification(
                solution, timeout=self.code_timeout
            )
            answer = extract_answer(solution)

            attempt = Attempt(
                attempt_number=len(trace.attempts) + 1,
                solution_text=solution,
                extracted_answer=answer,
                code_blocks_found=len(code_blocks),
                verification_passed=verification_passed,
                verification_output=verification_output,
                duration_seconds=time.time() - attempt_start,
            )
            trace.attempts.append(attempt)

            if verification_passed and answer is not None:
                # NL verify the corrected solution
                if self.enable_nl_verify:
                    nl_ok, nl_msg = self._nl_verify(problem_text, solution)
                    attempt.nl_verification = nl_msg
                    if not nl_ok:
                        logger.info(f"    [Correction {retry}] NL Verify: {nl_msg[:60]}")
                        previous_solution = solution
                        error_message = nl_msg
                        continue

                trace.final_answer = answer
                trace.solved = True
                trace.strategy = "self_correct"
                trace.total_duration_seconds = time.time() - problem_start
                trace.total_attempts = len(trace.attempts)
                logger.info(
                    f"  SOLVED (self-correct, attempt {retry}): {answer} "
                    f"({trace.total_duration_seconds:.1f}s)"
                )
                return trace

            logger.info(
                f"    [Correction {retry}] FAILED ({attempt.duration_seconds:.1f}s)"
            )

            previous_solution = solution
            error_message = verification_output

        # --- Exhausted: pick best available answer ---
        trace.strategy = "exhausted"
        for att in reversed(trace.attempts):
            if att.extracted_answer is not None:
                trace.final_answer = att.extracted_answer
                break

        trace.total_duration_seconds = time.time() - problem_start
        trace.total_attempts = len(trace.attempts)
        logger.warning(
            f"  [EXHAUSTED] {trace.total_attempts} attempts, "
            f"best answer: {trace.final_answer}"
        )
        return trace

    # =========================================================================
    # Dynamic Time Allocation
    # =========================================================================

    def _compute_time_budget(
        self, problems_remaining: int, difficulty: str
    ) -> float:
        """
        Compute per-problem time budget based on remaining time and difficulty.

        Returns max seconds to spend on this problem.
        """
        remaining = self._remaining_seconds()
        if problems_remaining <= 0:
            return remaining

        base_budget = remaining / problems_remaining

        # Difficulty multipliers
        multipliers = {
            "easy": 0.6,
            "medium": 1.0,
            "hard": 1.5,
            "extreme": 2.0,
        }
        mult = multipliers.get(difficulty, 1.0)

        # Cap at 80% of remaining time (leave buffer for other problems)
        budget = min(base_budget * mult, remaining * 0.8)

        return max(budget, 60)  # Minimum 60 seconds per problem

    # =========================================================================
    # Main Execution
    # =========================================================================

    def run(self, problems: list[dict], output_path: str) -> dict:
        """
        Main execution loop. Processes problems with hard timer.

        Args:
            problems: List of problem dicts.
            output_path: Path to write JSONL output.

        Returns:
            Summary statistics dict.
        """
        self.start_time = time.time()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        total = len(problems)
        solved = 0
        attempted = 0
        traces = []

        logger.info("=" * 60)
        logger.info("DEEP RESEARCHER v2 — H100 Research Sprint")
        logger.info("=" * 60)
        logger.info(f"  Model:       {self.model_path}")
        logger.info(f"  Family:      {self.model_family}")
        logger.info(f"  Problems:    {total}")
        logger.info(f"  Time limit:  {self.time_limit_hours:.1f} hours")
        logger.info(f"  Samples/Q:   {self.num_samples}")
        logger.info(f"  Max retries: {self.max_retries}")
        logger.info(f"  TIR:         {'ON' if self.enable_tir else 'OFF'}")
        logger.info(f"  NL Verify:   {'ON' if self.enable_nl_verify else 'OFF'}")
        logger.info(f"  Max tokens:  {self.max_generate_tokens}")
        logger.info(f"  Output:      {output_path}")
        logger.info(f"  Dry run:     {self.dry_run}")
        logger.info("=" * 60)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for i, problem in enumerate(problems):
                    self._check_timer()

                    problems_remaining = total - i
                    difficulty = problem.get("difficulty", "medium")
                    budget = self._compute_time_budget(problems_remaining, difficulty)

                    logger.info(
                        f"\n--- Problem {i + 1}/{total} "
                        f"(budget: {budget / 60:.1f}min) ---"
                    )

                    trace = self.research_problem(problem)
                    traces.append(trace)
                    attempted += 1

                    if trace.solved:
                        solved += 1

                    # Crash-safe write: flush after every problem
                    f.write(json.dumps(trace.to_dict(), ensure_ascii=False) + "\n")
                    f.flush()

                    # Progress report
                    rate = solved / attempted if attempted > 0 else 0
                    logger.info(
                        f"  Progress: {attempted}/{total} attempted, "
                        f"{solved} solved ({rate:.0%}) | "
                        f"Elapsed: {self._elapsed_str()} | "
                        f"Remaining: {self._remaining_str()}"
                    )

        except TimeLimitExceeded as e:
            logger.warning(f"\n{'=' * 60}")
            logger.warning(f"GRACEFUL EXIT: {e}")
            logger.warning(f"{'=' * 60}")

        except Exception as e:
            logger.error(f"\nUNEXPECTED ERROR: {type(e).__name__}: {e}")
            raise

        # Final summary
        elapsed = time.time() - self.start_time
        strategy_counts = Counter(t.strategy for t in traces)

        summary = {
            "total_problems": total,
            "attempted": attempted,
            "solved": solved,
            "solve_rate": solved / attempted if attempted > 0 else 0,
            "elapsed_seconds": elapsed,
            "elapsed_hours": elapsed / 3600,
            "output_file": output_path,
            "avg_time_per_problem": elapsed / attempted if attempted > 0 else 0,
            "strategies": dict(strategy_counts),
            "model": self.model_path,
            "model_family": self.model_family,
            "num_samples": self.num_samples,
            "tir_enabled": self.enable_tir,
            "nl_verify_enabled": self.enable_nl_verify,
        }

        logger.info(f"\n{'=' * 60}")
        logger.info("RESEARCH SPRINT COMPLETE")
        logger.info(f"{'=' * 60}")
        logger.info(f"  Attempted:  {attempted}/{total}")
        logger.info(f"  Solved:     {solved}/{attempted} ({summary['solve_rate']:.0%})")
        logger.info(f"  Strategies: {dict(strategy_counts)}")
        logger.info(f"  Elapsed:    {self._elapsed_str()}")
        logger.info(f"  Avg/prob:   {summary['avg_time_per_problem']:.1f}s")
        logger.info(f"  Output:     {output_path}")
        logger.info(f"{'=' * 60}")

        # Write summary to separate file
        summary_path = str(output_file.with_suffix(".summary.json"))
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"  Summary:    {summary_path}")

        return summary
