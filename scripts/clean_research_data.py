import json
import collections

input_file = 'research_data2.jsonl'
output_file = 'cleaned_research_data.jsonl'
summary_file = 'research_summary.txt'

data = []
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            data.append(json.loads(line))

cleaned_data = []
summary_lines = []

for d in data:
    problem_id = d.get('problem_id', 'unknown')
    attempts = d.get('attempts', [])
    solved = d.get('solved', False)
    final_answer = d.get('final_answer')
    
    # Collect all extracted answers
    extracted_answers = [a.get('extracted_answer') for a in attempts if a.get('extracted_answer')]
    
    # Check for specific insights like "xy = 25"
    xy_25_found = False
    for attempt in attempts:
        if 'xy = 25' in attempt.get('solution_text', '') or 'xy=25' in attempt.get('solution_text', ''):
            xy_25_found = True
            break
            
    summary_lines.append(f"Problem: {problem_id}")
    summary_lines.append(f"  Solved: {solved}")
    summary_lines.append(f"  Final Answer: {final_answer}")
    summary_lines.append(f"  Attempts: {len(attempts)}")
    summary_lines.append(f"  Extracted Answers: {collections.Counter(extracted_answers)}")
    if xy_25_found:
        summary_lines.append(f"  Insight 'xy = 25' found in attempts.")
    summary_lines.append("-" * 20)

    # Create cleaned version
    # Keep problem info, answer, and ONLY the successful attempt or the one with the insight
    clean_d = {
        'problem_id': problem_id,
        'problem_text': d.get('problem_text'),
        'solved': solved,
        'final_answer': final_answer,
        'majority_vote_answers': d.get('majority_vote_answers'),
        'meaningful_attempts': []
    }
    
    for attempt in attempts:
        # Keep attempt if it's the final chosen one (matches final answer) OR contains the key insight
        # OR if it's the ONLY attempt (for context)
        is_meaningful = False
        if attempt.get('extracted_answer') == final_answer:
            is_meaningful = True
        if 'xy = 25' in attempt.get('solution_text', '') or 'xy=25' in attempt.get('solution_text', ''):
            is_meaningful = True
        
        if is_meaningful:
            # Strip strict "solution_text" if it's huge? No, keep it for the meaningful ones.
            # But maybe remove the raw "verification_output" if it's just syntax errors?
            # actually keep the text, it's the valuable part.
            clean_d['meaningful_attempts'].append(attempt)
    
    cleaned_data.append(clean_d)

with open(output_file, 'w', encoding='utf-8') as f:
    for d in cleaned_data:
        f.write(json.dumps(d) + '\n')

with open(summary_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(summary_lines))

print(f"Processed {len(data)} problems.")
print(f"Summary written to {summary_file}")
print(f"Cleaned data written to {output_file}")
