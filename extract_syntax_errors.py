import json
import re

input_file = 'research_data2.jsonl.bak'
output_file = 'syntax_errors.txt'

def extract_syntax_errors():
    with open(input_file, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f if line.strip()]

    with open(output_file, 'w', encoding='utf-8') as out:
        for d in data:
            if d.get('solved'):
                 continue
            
            pid = d.get('problem_id')
            out.write(f"Problem: {pid}\n" + "="*40 + "\n")
            
            for i, attempt in enumerate(d.get('attempts', [])):
                ver_output = attempt.get('verification_output', '')
                if 'SyntaxError' in ver_output:
                    out.write(f"Attempt {i+1} SyntaxError:\n")
                    
                    # Extract error message
                    error_match = re.search(r"SyntaxError:.*", ver_output)
                    if error_match:
                        out.write(f"  Error: {error_match.group(0)}\n")
                    
                    # Extract the code block that failed (simplistic approach)
                    # Often the error shows the line. Let's look for "File" lines
                    file_match = re.search(r"File \".*?\", line (\d+)", ver_output)
                    if file_match:
                        line_num = file_match.group(1)
                        out.write(f"  Line: {line_num}\n")
                    
                    # Try to get the snippet from the error output if present
                    # The error output usually echoes the line.
                    lines = ver_output.split('\n')
                    for j, line in enumerate(lines):
                         if "SyntaxError" in line:
                              # Print a few lines before it for context
                              start = max(0, j-4)
                              snippet = '\n'.join(lines[start:j+1])
                              out.write(f"  Context:\n{snippet}\n")
                              break
                    out.write("-" * 20 + "\n")

if __name__ == "__main__":
    extract_syntax_errors()
    print(f"Syntax errors extracted to {output_file}")
