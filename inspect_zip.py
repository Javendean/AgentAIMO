
import zipfile
import pandas as pd
import sys

zip_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ai-mathematical-olympiad-progress-prize-3-publicleaderboard-2026-02-13T14_27_49.zip'

try:
    with zipfile.ZipFile(zip_path, 'r') as z:
        filename = z.namelist()[0]
        print(f"Reading {filename}...")
        df = pd.read_csv(z.open(filename))
        print("Columns:")
        print(df.columns.tolist())
        print("\nFirst 5 rows:")
        print(df.head())
        
        # Calculate top 1%
        if 'Score' in df.columns:
            n = len(df)
            top_1_percent_count = int(n * 0.01)
            print(f"Total entries: {n}")
            print(f"Top 1% count: {top_1_percent_count}")
            # Assumption: Score is higher is better or lower is better? 
            # Usually strict score (like accuracy) is higher better.
            # But let's check the values.
            print(df['Score'].describe())
except Exception as e:
    print(f"Error: {e}")
