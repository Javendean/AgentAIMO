
import zipfile
import pandas as pd
import os
import sys

# Configuration
ZIP_PATH = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\ai-mathematical-olympiad-progress-prize-3-publicleaderboard-2026-02-13T14_27_49.zip'
OUTPUT_CSV = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\top_1_percent_leaderboard.csv'
TOP_PERCENT = 0.01

def extract_top_leaderboard():
    if not os.path.exists(ZIP_PATH):
        print(f"Error: Zip file not found at {ZIP_PATH}")
        return

    try:
        with zipfile.ZipFile(ZIP_PATH, 'r') as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            if not csv_files:
                print("Error: No CSV file found in the zip archive.")
                return
            
            filename = csv_files[0]
            print(f"Reading leaderboard data from: {filename}")
            
            with z.open(filename) as f:
                df = pd.read_csv(f)
                
            total_entries = len(df)
            print(f"Total entries: {total_entries}")
            
            if 'Score' not in df.columns:
                print("Error: 'Score' column not found in CSV.")
                print(f"Available columns: {df.columns.tolist()}")
                return

            # Determine Top 1% count
            top_n = int(total_entries * TOP_PERCENT)
            if top_n == 0:
                top_n = 1 # Ensure at least one entry if list is small
            
            print(f"Extracting top {top_n} entries (Top {TOP_PERCENT*100}%)")
            
            # Sort by Score descending
            df_sorted = df.sort_values(by='Score', ascending=False)
            
            # Select top N
            top_df = df_sorted.head(top_n)
            
            # Save to CSV
            top_df.to_csv(OUTPUT_CSV, index=False)
            print(f"Successfully saved top {top_n} entries to {OUTPUT_CSV}")
            
            # Verification output
            print("\nPreview of extracted entries:")
            print(top_df[['Rank', 'TeamName', 'Score']].to_string(index=False))

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    extract_top_leaderboard()
