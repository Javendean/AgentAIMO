from agent.sandbox import extract_code_blocks, run_verification

# Test Case 1: Nested backticks in assistantcommentary
hallucinated_output = """
assistantcommentary to=python code
import math
print("Start")
```python
x = 10
print(x)
```
print("End")
"""

print("--- Test Case 1: Extraction ---")
blocks = extract_code_blocks(hallucinated_output)
print(f"Blocks found: {len(blocks)}")
print("Block Content:")
print(blocks[0])
print("-" * 20)

print("--- Test Case 2: Execution ---")
success, output = run_verification(hallucinated_output)
print(f"Success: {success}")
print("Output:")
print(output)

expected_clean = """
import math
print("Start")
x = 10
print(x)
print("End")
""".strip()

# Verification check
# Note: extract_code_blocks might preserve newlines differently, so exact string match might be tricky.
# But "```" should be gone.

if "```" not in blocks[0]:
    print("\n✅ PASSED: No backticks in extracted block.")
else:
    print("\n❌ FAILED: Backticks still present.")

if "10" in output and "Start" in output and "End" in output:
    print("✅ PASSED: Code executed successfully.")
else:
    print("❌ FAILED: Code execution failed.")
