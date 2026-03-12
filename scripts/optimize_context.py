import re
import os

input_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ExternalChatContext.txt'
output_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ExternalChatContext_Optimized.txt'

def optimize_text(text):
    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in text.splitlines()]
    
    # Rejoin to handle multiple newlines
    text = '\n'.join(lines)
    
    # Replace 3 or more newlines with 2 (preserve paragraph breaks, remove excessive gaps)
    # Actually, for "minimizing whitespace", maybe 2 is enough? 
    # Let's stick to max 2 consecutive newlines.
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Ensure file ends with a single newline
    text = text.strip() + '\n'
    
    return text

try:
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    optimized = optimize_text(content)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(optimized)
        
    print(f"Successfully optimized file. Original size: {len(content)}, New size: {len(optimized)}")
    print(f"Output saved to: {output_path}")

except Exception as e:
    print(f"Error: {e}")
