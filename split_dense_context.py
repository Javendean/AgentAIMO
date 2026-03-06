
import os
import math

input_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ExternalChatContext_UltraDense.txt'
chunk_size = 60000

try:
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    total_length = len(content)
    num_chunks = math.ceil(total_length / chunk_size)
    
    print(f"Total length: {total_length} characters")
    print(f"Splitting into {num_chunks} chunks of ~{chunk_size} characters.")

    base_name, ext = os.path.splitext(input_path)
    
    for i in range(num_chunks):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, total_length)
        chunk = content[start:end]
        
        output_filename = f"{base_name}_Part{i+1}{ext}"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(chunk)
            
        print(f"Created {output_filename} ({len(chunk)} chars)")

    print("Splitting complete.")

except Exception as e:
    print(f"Error: {e}")
