
import re
import os

original_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ExternalChatContext_Optimized.txt'
new_content_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\new_context_content.txt'
final_output_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ExternalChatContext_Final.txt'

def latexify(text):
    # Specific replacements based on observed patterns
    replacements = [
        (r'V\(s\)', r'$V(s)$'),
        (r'V_ver\(s\)', r'$V_{ver}(s)$'),
        (r'V_prm\(s\)', r'$V_{prm}(s)$'),
        (r'Delta\(', r'$\Delta('),
        (r'!=', r'$\neq$'),
        (r'approx 0', r'\approx 0$'),
        (r'\[0,\s*1\]', r'$[0, 1]$'),
        (r'Exit Code', r'\text{Exit Code}'),
        (r'Ground Truth', r'\text{Ground Truth}'),
        # Fix potential double dollars from previous regexes if any overlap
        (r'\$\$', r'$'), 
    ]
    
    for old, new in replacements:
        text = re.sub(old, new, text)
        
    return text

def minimize_whitespace(text):
    # Remove leading/trailing
    text = text.strip()
    # Replace multiple newlines with single newline (aggressive minimization as requested)
    # The user said "minimizing whitespace while maintaining readability"
    # "Output for direct copy and paste." 
    # Usually single newline separates lines, double separates paragraphs.
    # Let's reduce 3+ newlines to 2. 
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove spaces at end of lines
    text = re.sub(r'[ \t]+\n', '\n', text)
    return text

try:
    with open(original_path, 'r', encoding='utf-8') as f:
        original_text = f.read()

    with open(new_content_path, 'r', encoding='utf-8') as f:
        new_content = f.read()

    # Process original text
    processed_original = latexify(original_text)
    
    # Combine
    combined_text = processed_original + "\n\n" + "="*50 + "\n\n" + new_content
    
    # Final whitespace minimization
    final_text = minimize_whitespace(combined_text)

    with open(final_output_path, 'w', encoding='utf-8') as f:
        f.write(final_text)

    print(f"Successfully created {final_output_path}")
    print(f"Original length: {len(original_text)}")
    print(f"Final length: {len(final_text)}")

except Exception as e:
    print(f"Error: {e}")
