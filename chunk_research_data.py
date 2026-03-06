import json
import os
import re
import math

input_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\research_data2.jsonl'
output_base = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ResearchData_Part'
chunk_size = 60000

def normalize(text):
    # Remove all excessive whitespace, similar to maximize_density.py logic
    # maximize_density.py used: ' '.join(content.split())
    if not text:
        return ""
    return ' '.join(str(text).split())

def format_attempt(attempt):
    # dense format: Attempt N: [Solution] extracted: [Ans] verified: [Ver]
    return f"Attempt {attempt.get('attempt_number','')}: {normalize(attempt.get('solution_text',''))} extracted: {normalize(attempt.get('extracted_answer',''))} verified: {normalize(attempt.get('nl_verification',''))}"

def process_file():
    print(f"Reading {input_path}...")
    
    all_text = []
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f):
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # Extract fields
                    pid = data.get('problem_id', 'Unknown')
                    p_text = normalize(data.get('problem_text', ''))
                    final_ans = normalize(data.get('final_answer', ''))
                    
                    attempts = data.get('meaningful_attempts', [])
                    if not isinstance(attempts, list):
                        attempts = []
                        
                    formatted_attempts = " ".join([format_attempt(a) for a in attempts])
                    
                    # Combine into a single block
                    # Format: ID: [pid] Problem: [text] Answer: [ans] [Attempts...]
                    block = f"ID: {pid} Problem: {p_text} Answer: {final_ans} {formatted_attempts}"
                    
                    all_text.append(block)
                    
                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON at line {line_num+1}")
                    
    except FileNotFoundError:
        print(f"Error: File not found at {input_path}")
        return

    # Join all blocks with a space
    full_content = " ".join(all_text)
    
    # Final density check (though individual parts are already densified)
    final_dense_content = ' '.join(full_content.split())
    
    total_length = len(final_dense_content)
    num_chunks = math.ceil(total_length / chunk_size)
    
    print(f"Total densified length: {total_length}")
    print(f"Splitting into {num_chunks} chunks of ~{chunk_size} chars")
    
    for i in range(num_chunks):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, total_length)
        chunk = final_dense_content[start:end]
        
        output_filename = f"{output_base}{i+1}.txt"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(chunk)
            
        print(f"Created {output_filename} ({len(chunk)} chars)")

if __name__ == "__main__":
    process_file()
