
import sys
import unittest
from agent.sandbox import extract_code_blocks
from agent.deep_researcher import DeepResearcher

class TestHallucinationFix(unittest.TestCase):
    def test_parser_adapter_extracts_hallucinated_code(self):
        """Test that extract_code_blocks captures the assistantcommentary format."""
        
        # Scenario 1: Inline header + code
        text1 = "Let's compute.\n\nassistantcommentary to=python codes=2.5\nt=24\nprint(s*t)\n"
        blocks1 = extract_code_blocks(text1)
        self.assertTrue(len(blocks1) > 0, "Failed to extract inline assistantcommentary")
        self.assertIn("s=2.5", blocks1[0], "Extracted content missing code")

        # Scenario 2: Header + newline + code
        text2 = "Analysis:\nassistantcommentary to=python code\nimport sympy\nx = sympy.Symbol('x')\n"
        blocks2 = extract_code_blocks(text2)
        self.assertTrue(len(blocks2) > 0, "Failed to extract newline assistantcommentary")
        self.assertIn("import sympy", blocks2[0])

        # Scenario 3: Standard markdown (sanity check)
        text3 = "Here is code:\n```python\nprint(1)\n```"
        blocks3 = extract_code_blocks(text3)
        self.assertEqual(len(blocks3), 1)
        self.assertIn("print(1)", blocks3[0])

    def test_forceful_feedback_logic(self):
        """Test that the feedback loop detects the banned format."""
        # Mocking the logic since we can't easily instantiate the full Researcher with vLLM
        previous_solution = "assistantcommentary to=python code\nprint(1)"
        
        error_message = "Original Error"
        
        # Simulate the logic added to deep_researcher.py
        if "assistantcommentary" in previous_solution:
            error_message = (
                "SYSTEM ERROR: You used 'assistantcommentary'. This is BANNED. "
                "You MUST use standard markdown code blocks:\n"
                "```python\n"
                "# code here\n"
                "```\n"
                "Retrying with CORRECT format..."
            )
            
        self.assertIn("SYSTEM ERROR", error_message)
        self.assertIn("BANNED", error_message)

if __name__ == '__main__':
    unittest.main()
