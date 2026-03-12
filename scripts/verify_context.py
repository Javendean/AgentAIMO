import os
import re

original_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ExternalChatContext.txt'
ultra_dense_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ExternalChatContext_UltraDense.txt'

def normalize(text):
    # Remove all whitespace to compare raw alphanumeric content
    # This ignores formatting differences (newlines vs spaces)
    return re.sub(r'\s+', '', text)

try:
    print("Reading original file...")
    with open(original_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    print("Reading ultra dense file...")
    # We can check optimal_ultra_dense.txt directly as it represents the sum of the parts
    # (Checking valid concatenation was done in split step, but we can verify parts if needed. 
    # For now, let's check the source of the split first.)
    with open(ultra_dense_path, 'r', encoding='utf-8') as f:
        dense_content = f.read()

    print("Normalizing contents...")
    norm_original = normalize(original_content)
    norm_dense = normalize(dense_content)
    
    print(f"Original normalized length: {len(norm_original)}")
    print(f"Dense normalized length: {len(norm_dense)}")
    
    # Check if original is in dense
    # Note: We added content to dense, so dense should contain original + more.
    # However, we also replaced a block in `ExternalChatContext_Final.txt` (lines 16-91)
    # The replacement was manually crafted to fix formatting. 
    # This means EXACT substring match might fail for that specific block.
    # We should check the *rest* of the file.
    
    # Let's try to match the beginning and end of original in dense.
    
    head_len = 1000
    tail_len = 1000
    
    head_match = norm_original[:head_len] in norm_dense
    tail_match = norm_original[-tail_len:] in norm_dense
    
    print(f"Head match ({head_len} chars): {head_match}")
    print(f"Tail match ({tail_len} chars): {tail_match}")
    
    if not head_match:
        print("HEAD MISMATCH DETAILS:")
        print("Original Head:", norm_original[:100])
        print("Dense Head:", norm_dense[:100])
        
    if not tail_match:
        print("TAIL MISMATCH DETAILS:")
        # The tail of original should be somewhere in the middle of dense (before the appended new context)
        # Wait, norm_original[-tail_len:] might not be at the *end* of norm_dense, but inside it.
        # Let's check simply if norm_original is a substring, allowing for the edited block.
        pass

    # Because we edited lines 16-91, let's exclude that region from the check.
    # Lines 16-91 in original (approxchars) -> need to find where they are.
    # Instead, let's check if the *vast majority* matches.
    # We can split original into chunks and check if they exist in dense.
    
    step = 5000
    mismatches = []
    
    print(f"Checking in chunks of {step} chars...")
    for i in range(0, len(norm_original), step):
        chunk = norm_original[i:i+step]
        if chunk not in norm_dense:
             # If chunk is not found, maybe it overlaps with the edited region?
             # Let's print the location.
             mismatches.append(i)
             print(f"Mismatch at original index {i}")
             print(f"Sample: {chunk[:50]}...")

    if not mismatches:
        print("VERIFICATION SUCCESSFUL: All chunks of original content found in dense file.")
    else:
        print(f"VERIFICATION FAILED: {len(mismatches)} chunks missing.")
        # Note: The edited block is at the beginning (lines 16-91). 
        # So mismatch at index 0 or near 0 is expected.
        # But extensive mismatches imply data loss.

except Exception as e:
    print(f"Error: {e}")
