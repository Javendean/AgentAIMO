
import pandas as pd
import time
import os
from playwright.sync_api import sync_playwright

# Configuration
INPUT_CSV = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\top_1_percent_leaderboard.csv'
OUTPUT_CSV = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\public_notebooks_found.csv'
BASE_URL = "https://www.kaggle.com"

def scrape_kaggle_notebooks():
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Input file {INPUT_CSV} not found.")
        return

    # Read the leaderboard data
    df = pd.read_csv(INPUT_CSV)
    
    # Extract users (TeamMemberUserNames might be a list string, we need strict usernames)
    # The column 'TeamMemberUserNames' usually contains the usernames. 
    # If there are multiple members, they might be comma separated.
    # We will try to split them and scrape for all unique users.
    
    users_to_scrape = set()
    for _, row in df.iterrows():
        users_str = str(row.get('TeamMemberUserNames', ''))
        # Simple split by comma if multiple users
        parts = [u.strip() for u in users_str.split(',') if u.strip()]
        for p in parts:
            users_to_scrape.add(p)
            
    print(f"Found {len(users_to_scrape)} unique users to scrape from top leaderboard entries.")
    
    results = []

    with sync_playwright() as p:
        # Launch browser (headless=True for speed, False for debugging)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for user in list(users_to_scrape):
            user_code_url = f"{BASE_URL}/{user}/code"
            print(f"Checking user: {user} at {user_code_url}")
            
            try:
                page.goto(user_code_url, timeout=30000)
                # Wait for some content to load. 
                # If user has no code or private, this might timeout or show "No code found".
                # We'll wait for the main list container or a known element.
                # Kaggle lists often have a specific class or structure. 
                # We'll look for notebook item links.
                
                # Wait for initial load
                try:
                    page.wait_for_selector('a', timeout=10000)
                except:
                    print(f"  - Timeout waiting for initial content {user}")

                # SCROLLING LOGIC: Kaggle uses lazy loading. We need to scroll down to reveal more items.
                # We will scroll a few times to ensure we catch everything.
                for _ in range(5):
                    page.evaluate("window.scrollBy(0, 1000)")
                    time.sleep(1) # wait for load

                # Extract potential notebook links
                # We look for anchor tags that contain the user's name and 'code' or just standard notebook patterns
                # The previous query was too specific for some Kaggle layouts
                links = page.query_selector_all('a')
                
                found_for_user = 0
                for link in links:
                    href = link.get_attribute('href')
                    text = link.inner_text().strip()
                    
                    if not href:
                        continue
                        
                    # Debug: print all code-like links
                    # Valid pattern: /username/code/notebook-slug OR /code/username/notebook-slug
                    if '/code/' in href:
                         # normalize
                        full_link = f"{BASE_URL}{href}" if href.startswith('/') else href
                        
                        # Filter to ensure it's likely a notebook
                        # We accept ANY notebook from the user's profile page as a candidate
                        if user.lower() in href.lower() or 'code' in href.lower():
                            if not any(r['Link'] == full_link for r in results):
                                results.append({
                                    'User': user,
                                    'Title': text if text else "Untitled",
                                    'Link': full_link
                                })
                                found_for_user += 1
                                print(f"  + Found: {text} -> {full_link}")

                if found_for_user == 0:
                    print(f"  - No public code found for {user}")

            except Exception as e:
                print(f"  ! Error scraping {user}: {e}")
                
            # Be nice to the server
            time.sleep(1)

        browser.close()

    # Save results
    if results:
        results_df = pd.DataFrame(results)
        results_df.to_csv(OUTPUT_CSV, index=False)
        print(f"\nScraping complete. Found {len(results)} public notebooks.")
        print(f"Saved to: {OUTPUT_CSV}")
    else:
        print("\nScraping complete. No public notebooks found for these users.")

if __name__ == "__main__":
    scrape_kaggle_notebooks()
