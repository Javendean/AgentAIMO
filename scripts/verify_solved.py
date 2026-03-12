import json

data = []
with open('research_data2.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            data.append(json.loads(line))

solved_probs = [d for d in data if d.get('solved')]
print("--- SOLVED PROBLEMS ---")
for p in solved_probs:
    pid = p.get('problem_id')
    ans = p.get('final_answer')
    print(f"[{pid}] Answer: {ans}")
print("-" * 30)
