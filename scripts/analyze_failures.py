import json
import collections
import re

input_file = 'research_data2.jsonl.bak'

def analyze_failures():
    data = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return

    print(f"Analyzing {len(data)} problems from {input_file}...\n")

    failure_patterns = collections.defaultdict(int)
    error_types = collections.defaultdict(int)
    
    unsolved_problems = [d for d in data if not d.get('solved', False)]

    print("--- UNSOLVED PROBLEMS ANALYSIS ---")
    for d in unsolved_problems:
        pid = d.get('problem_id')
        print(f"\nProblem: {pid}")
        
        attempts = d.get('attempts', [])
        print(f"Total Attempts: {len(attempts)}")
        
        # Analyze extracted answers (distractors)
        answers = [a.get('extracted_answer') for a in attempts if a.get('extracted_answer')]
        if answers:
            print(f"Common Wrong Answers: {collections.Counter(answers).most_common(3)}")
        else:
            print("No extracted answers found in attempts.")

        # Analyze verification errors
        for i, attempt in enumerate(attempts):
            ver_output = attempt.get('verification_output', '')
            if ver_output and 'FAILED' in ver_output:
                # Simple extraction of python error types
                errors = re.findall(r"(\w+Error):", ver_output)
                if errors:
                    for err in errors:
                        error_types[err] += 1
                        failure_patterns[f"{pid}_{err}"] += 1
                elif "Timeout" in ver_output:
                     error_types["Timeout"] += 1
                else:
                    error_types["Unknown/Logic Fail"] += 1

            # Check for empty solution text or specific failure indicators
            sol_text = attempt.get('solution_text', '')
            if not sol_text.strip():
                print(f"  Attempt {i+1}: Empty solution text!")
            
            # Check for repetition loops
            if "I made a mistake" in sol_text and sol_text.count("I made a mistake") > 3:
                 print(f"  Attempt {i+1}: Detected repetition loop ('I made a mistake').")

    print("\n--- GLOBAL FAILURE STATISTICS ---")
    print("Top Error Types:")
    for err, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {err}: {count}")

if __name__ == "__main__":
    analyze_failures()
