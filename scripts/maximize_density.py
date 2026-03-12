
import os

input_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ExternalChatContext_Final.txt'
output_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ExternalChatContext_UltraDense.txt'

try:
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove all extra whitespace using split() which splits by any whitespace (newlines, spaces, tabs)
    # and rejoin with a single space.
    dense_content = ' '.join(content.split())
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(dense_content)
        
    print(f"Successfully created {output_path}")
    print(f"Original length: {len(content)}")
    print(f"Final length: {len(dense_content)}")
    print(f"Reduction: {len(content) - len(dense_content)} characters")

except Exception as e:
    print(f"Error: {e}")
