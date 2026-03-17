"""
Kaggle Notebook Script: AIMO3 DeepResearcher H100 Sprint

Copy this into a Kaggle notebook to run a 3-hour research sprint on the H100.

PREREQUISITES (Kaggle Datasets to attach):
    1. 'aimo-vllm-wheels'    — vLLM wheel files from supply_chain/download_vllm_wheels.py
    2. 'aimo-model-70b-awq'  — DeepSeek-R1-Distill-Llama-70B-AWQ model weights
    3. 'aimo-problems'       — Problem corpus (problems_v1.jsonl)
    4. 'aimo-agent-code'     — This agent/ directory uploaded as a dataset

SETTINGS:
    Accelerator: GPU H100
    Internet:    OFF
    Run mode:    Save & Run All (Commit) — prevents idle quota drain
"""

# ===========================================================================
# Cell 1: Offline Install
# ===========================================================================
import subprocess
import sys

# Install vLLM from offline wheels
# 1. Uninstall conflicting bleeding-edge packages from Kaggle/Google environment
subprocess.check_call([
    sys.executable, "-m", "pip", "uninstall", "-y",
    "fsspec", 
    "google-ai-generativelanguage", 
    "google-cloud-translate", 
    "google-cloud-bigquery-storage", 
    "tensorflow", 
    "protobuf", 
    "cuda-python", 
    "rich",
    "--quiet",
])

# 2. Install vLLM (and its deps like correct protobuf/cuda-python) from offline wheels
subprocess.check_call([
    sys.executable, "-m", "pip", "install",
    "--no-index",
    "--find-links=/kaggle/input/aimo-vllm-wheels/",
    "vllm==0.10.2",
    "--quiet",
])

# 3. Verify vLLM Version (Golden Config Check)
import vllm
print(f"[CHECK] Installed vLLM version: {vllm.__version__}")
assert vllm.__version__ == "0.10.2", "CRITICAL: Failed to install vLLM 0.10.2"

print("[OK] vLLM installed from offline wheels")


# ===========================================================================
# Cell 2: Setup & Imports
# ===========================================================================
import json
import logging
import os

# Add agent code to path
sys.path.insert(0, "/kaggle/input/aimo-agent-code/")

from agent.deep_researcher import DeepResearcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ===========================================================================
# Cell 3: Load Problems
# ===========================================================================
PROBLEMS_PATH = "/kaggle/input/aimo-problems/problems_v1.jsonl"

with open(PROBLEMS_PATH, "r", encoding="utf-8") as f:
    problems = [json.loads(line) for line in f if line.strip()]

logger.info(f"Loaded {len(problems)} problems")


# ===========================================================================
# Cell 4: Load System Prompt Patches (if any)
# ===========================================================================
PATCH_PATH = "/kaggle/input/aimo-problems/prompt_patch.txt"
patch_text = None

if os.path.exists(PATCH_PATH):
    with open(PATCH_PATH, "r", encoding="utf-8") as f:
        patch_text = f.read()
    logger.info(f"Loaded prompt patch ({len(patch_text)} chars)")
else:
    logger.info("No prompt patch found — using baseline prompts")


# ===========================================================================
# Cell 5: Initialize DeepResearcher
# ===========================================================================
# CHANGED: Using 120B MXFP4 Model (Golden Config)
# PRIMARY: GPT-OSS-120B (MXFP4)
# BACKUP: Qwen-2.5-Math-72B (if Canary fails)
MODEL_PATH = "/kaggle/input/gpt-oss-120b-mxfp4/"

researcher = DeepResearcher(
    model_path=MODEL_PATH,
    time_limit_hours=2.8,       # 3hr target - 12min buffer
    max_retries=5,              # Up to 5 self-correction attempts
    generate_temperature=0.7,   # Creative for initial generation
    correct_temperature=0.3,    # Precise for corrections
    max_generate_tokens=4096,   # Long CoT for deep reasoning
    max_correct_tokens=2048,    # Shorter for targeted fixes
    code_timeout=30,            # 30s sandbox limit
    gpu_memory_utilization=0.90,
    max_model_len=8192,
    patch_text=patch_text,
)

# ===========================================================================
# Cell 5b: The "Canary Test" (Hostility Detection)
# ===========================================================================
# Synthetic canary problem (non-memorizable, verifiable by enumeration)
# "How many integers from 1 to 500 are divisible by 3 or 7 but not by 21?"
# Answer: len({n for n in range(1,501) if (n%3==0 or n%7==0) and n%21!=0}) == 190
CANARY_PROBLEM = {
    "problem": (
        "Count the number of integers from 1 to 500 (inclusive) that are divisible "
        "by 3 or by 7, but NOT divisible by 21. Give your answer as a single integer."
    ),
    "answer": "190",
    "verification": "len({n for n in range(1, 501) if (n % 3 == 0 or n % 7 == 0) and n % 21 != 0})",
}

def run_canary_test(researcher_instance):
    """Runs a 'Canary' logic test to detect broken 4-bit quantization or vLLM kernel issues.

    Uses a synthetic, non-memorizable counting problem (answer: 190) that the model
    must compute, not recall. Accepts the model's actual output format (**ANSWER: N**).

    Args:
        researcher_instance (DeepResearcher): An instantiated DeepResearcher object to test.

    Returns:
        bool: True if passed, False if environment is 'Hostile' (throttled or logic failure).
    """
    import re
    import time

    logger.info("🦜 RUNNING CANARY TEST (synthetic, answer=190)...")

    original_prompt = researcher_instance.system_prompt
    researcher_instance.system_prompt += "\nReasoning Effort: High.\nThinking Process: Mandatory."

    try:
        messages = [
            {"role": "system", "content": researcher_instance.system_prompt},
            {"role": "user", "content": CANARY_PROBLEM["problem"]}
        ]

        t0 = time.time()
        outputs = researcher_instance.llm.generate(
            [researcher_instance.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )],
            vllm.SamplingParams(temperature=0.0, max_tokens=2048)
        )
        dt = time.time() - t0

        output_text = outputs[0].outputs[0].text
        generated_tokens = len(outputs[0].outputs[0].token_ids)
        tps = generated_tokens / dt

        logger.info(f"🦜 Speed: {tps:.2f} tokens/sec (Threshold: 5.0)")
        logger.info(f"🦜 Output: {output_text[:300]}...")

        # Check 1: Speed
        if tps < 5.0:
            logger.error(f"🦜 FAIL: Speed too slow ({tps:.2f} t/s). Environment is throttling.")
            return False

        # Check 2: Logic — accept any clean format containing the correct integer 190.
        # Patterns: "**ANSWER: 190**", "ANSWER: 190", "\boxed{190}", bare "190"
        gold = CANARY_PROBLEM["answer"]
        answer_patterns = [
            re.compile(r"\*\*ANSWER:\s*" + gold + r"\*\*", re.IGNORECASE),
            re.compile(r"ANSWER:\s*" + gold, re.IGNORECASE),
            re.compile(r"\\boxed\{" + gold + r"\}"),
            re.compile(r"\b" + gold + r"\b"),
        ]
        matched = any(p.search(output_text) for p in answer_patterns)
        if matched:
            logger.info(f"🦜 PASS: Model produced correct answer ({gold}). Logic Verified.")
            return True
        else:
            logger.error(
                f"🦜 FAIL: Logic Collapse. Model did not produce answer={gold}. "
                f"Last 200 chars: {output_text[-200:]!r}"
            )
            return False

    except Exception as e:
        logger.error(f"🦜 CRASH: Canary died with error: {e}")
        return False
    finally:
        researcher_instance.system_prompt = original_prompt

# Run the Canary
if not run_canary_test(researcher):
    logger.warning("🚨 CANARY FAILED! TRIGGERING FAIL-FAST SWAP 🚨")
    
    # KILL SWITCH: Delete 120B model to free VRAM
    del researcher
    import gc
    import torch
    gc.collect()
    torch.cuda.empty_cache()
    
    # SWAP TO QWEN-72B (The "Safety Net")
    logger.info("🔄 Swapping to Backup Model: Qwen-2.5-Math-72B...")
    BACKUP_MODEL_PATH = "/kaggle/input/qwen-2.5-math-72b/"
    
    researcher = DeepResearcher(
        model_path=BACKUP_MODEL_PATH,
        time_limit_hours=2.8,
        max_retries=5,
        generate_temperature=0.6,
        max_generate_tokens=4096,
        patch_text=patch_text
    )
    logger.info("✅ FAIl-FAST COMPLETE. Running with Qwen-72B.")
else:
    logger.info("✅ CANARY PASSED. Proceeding with GPT-OSS-120B (Best Case).")


# ===========================================================================
# Cell 6: Run Research Sprint
# ===========================================================================
OUTPUT_PATH = "/kaggle/working/research_data.jsonl"

summary = researcher.run(problems, OUTPUT_PATH)

# Print final stats
print("\n" + "=" * 60)
print("SPRINT COMPLETE")
print("=" * 60)
for k, v in summary.items():
    if isinstance(v, float):
        print(f"  {k}: {v:.4f}")
    else:
        print(f"  {k}: {v}")
print("=" * 60)
print(f"\nOutput saved to: {OUTPUT_PATH}")
print("Download this file from the notebook's Output tab.")
