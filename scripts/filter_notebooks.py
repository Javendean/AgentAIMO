
import pandas as pd
import os

INPUT_CSV = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\public_notebooks_found.csv'
OUTPUT_CSV = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\relevant_notebooks_filtered.csv'

# Keywords that suggest relevance to AI Math Olympiad
POSITIVE_KEYWORDS = [
    'aimo', 'math', 'olympiad', 
    'qwen', 'gemma', 'deepseek', 'gpt', 'llm',
    'tir', 'reasoning', 'inference', 'chain of thought', 'cot',
    'solver', 'theorem', 'proving',
    'skill', 'luck', # specifically for "Skills Optional, Luck Necessary"
    'reflexion', 'awq', 'vllm'
]

# Keywords that suggest irrelevance (strong filtering)
NEGATIVE_KEYWORDS = [
    'titanic', 'house price', 'football', 'nfl', 'soccer', 
    'bird', 'audio', 'image', 'vision', 'detect', 'segmentation',
    'cancer', 'diabetes', 'medical', 'ct scan', 'x-ray',
    'store sales', 'forecasting', 'stock', 'trading', 'crypto',
    'spotify', 'tweets', 'sentiment', 'movie',
    'playground' # general kaggle playground series usually unrelated
]

def filter_notebooks():
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} not found.")
        return

    df = pd.read_csv(INPUT_CSV)
    print(f"Total notebooks found: {len(df)}")

# Strict Recency Filter: Competition started ~Nov 20, 2025 (approx 3 months ago from Feb 2026)
# We will accept notebooks updated within the last 4 months to be safe.
def is_recent(title_str):
    title_str = title_str.lower()
    if 'updated a few seconds ago' in title_str or 'updated minutes ago' in title_str:
        return True
    if 'updated a day ago' in title_str or 'days ago' in title_str:
        return True
    
    # Check for "months ago"
    # "updated a month ago" -> 1 month
    # "updated 2 months ago" -> 2 months
    if 'month ago' in title_str or 'months ago' in title_str:
        # Try to extract the number
        import re
        match = re.search(r'updated (\d+) months? ago', title_str)
        if match:
            months = int(match.group(1))
            return months <= 4
        # "updated a month ago" handles 1 month
        return True
        
    # "year ago" -> definitely old
    if 'year ago' in title_str or 'years ago' in title_str:
        return False
        
    return False


def get_priority(row):
    title = str(row['Title']).lower()
    link = str(row['Link']).lower()
    slug = link.split('/')[-1]
    
    # 1. Critical Whitelist (High)
    if 'nihilisticneuralnet' in link and ('aimo' in link or 'aimo' in title):
        return 'High'
    if 'aimo' in slug or 'aimo' in title:
        return 'High'

    # 2. Strong Positive Keywords (High if recent, Medium if old)
    has_positive = any(pos in title for pos in POSITIVE_KEYWORDS) or any(pos in slug for pos in POSITIVE_KEYWORDS)
    recent = is_recent(title)
    
    if has_positive:
        if recent:
            return 'High'
        else:
            return 'Medium' # Old but relevant topic (e.g. "Math", "TIR")
            
    # 3. Known Top User (Medium)
    # If a top 1% user writes something, it might be valuable even if unrelated
    # We'll give it Medium unless it's explicitly negative
    
    # 4. Negative Keywords (Low)
    extended_negatives = NEGATIVE_KEYWORDS + ['essay', 'writing', 'speech', 'audio', 'vision', 'detect']
    if any(neg in title for neg in extended_negatives) or any(neg in slug for neg in extended_negatives):
        return 'Low'

    # 5. Default
    if recent:
         return 'Medium' # Recent generic notebook might be a new attempt
    return 'Low'

def filter_notebooks():
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} not found.")
        return

    df = pd.read_csv(INPUT_CSV)
    print(f"Total notebooks found: {len(df)}")

    # Apply priority
    df['Priority'] = df.apply(get_priority, axis=1)

    # Sort: High -> Medium -> Low
    # We use a custom sort key
    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    df['PriorityRank'] = df['Priority'].map(priority_order)
    
    df_sorted = df.sort_values(by=['PriorityRank', 'User'], ascending=[True, True])
    df_sorted = df_sorted.drop(columns=['PriorityRank'])

    # Save
    df_sorted.to_csv(OUTPUT_CSV, index=False)
    
    print(f"Processed {len(df_sorted)} notebooks.")
    print("\nTop 15 High/Medium Priority Notebooks:")
    print(df_sorted[df_sorted['Priority'].isin(['High', 'Medium'])][['Priority', 'User', 'Title']].head(15).to_string(index=False))
    print(f"\nSaved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    filter_notebooks()
