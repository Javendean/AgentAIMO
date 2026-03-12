
import os

file_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ExternalChatContext_Final.txt'

new_content_block = r"""In MCTS, the Value Function $V(s)$ estimates the probability that state $s$ leads to a correct solution. The Rubric defines $V(s)$ with high granularity.
Standard MCTS: $V(s) \in [0, 1]$ based on final answer correctness.
Cognitive Fidelity MCTS:
$V_{ver}(s)$ (Hard Value): Based on Dimension 1 (Verification). If Exit Code $\neq 0$ OR Ground Truth $\neq$ Answer $\to V(s) = -1$ (Immediate Pruning).
$V_{prm}(s)$ (Soft Value): Based on Dimension 2 (Reasoning). The Metacognition criteria (MET_01, MET_02) serve as dense rewards for intermediate steps.
Implementation: A "Process Reward Model" is trained to predict the "Self-Correction Entropy" score of the next token. High entropy (radical shift) = High Value node to explore.
B. The "Rollout Policy" (Simulation)
When the tree reaches a leaf, MCTS simulates the future (Rollouts).
Rubric Impact: The rubric explicitly banning "linear reasoning" (MET_01) dictates we must use a Temperature-Scaled Rollout that favors branching.
Negative Constraint: The policy must be penalized if it generates "Performative Mimesis" (fake "Wait" tokens). The Semantic Delta Check (Section 6.3) should be a runtime filter during rollout. If $\Delta(\text{Pre-Wait}, \text{Post-Wait}) \approx 0$, kill the rollout.
C. The "Selection Policy" (PUCT)
How do we choose which child node to explore?"""

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Lines 16-91 correspond to indices 15-91 (exclusive of 91? No, inclusive in 1-based, so 15:91 in 0-based slice is 16..91)
    # Let's verify the content of the start and end lines to be sure.
    start_index = 15
    end_index = 91 
    
    # Check context
    print(f"Line {start_index+1} starts with: {lines[start_index][:20]}")
    print(f"Line {end_index} starts with: {lines[end_index-1][:20]}")
    
    # We want to replace lines[15:91] with the new block. 
    # Note: lines[15] is the 16th line. lines[90] is the 91st line.
    # So we replace slice [15:91]
    
    # Split new content into lines and add newlines
    new_lines = [line + '\n' for line in new_content_block.splitlines()]
    
    # Careful not to double newline if original had it, but here we are replacing the whole block.
    
    final_lines = lines[:start_index] + new_lines + lines[end_index:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)
        
    print("Successfully replaced lines 16-91.")

except Exception as e:
    print(f"Error: {e}")
