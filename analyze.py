"""
analyze.py
----------
The enrichment phase. Here we take the raw text from Amazon reviews and 
turn it into quantitative sentiment scores using VADER.

VADER (Valence Aware Dictionary and sEntiment Reasoner) is great here because:
1. It handles emojis (often found in reviews).
2. It's fast and doesn't require a heavy model download.
3. It understands intensifiers like "VERY good" or "not bad".
"""

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def load_raw_data(path="data/raw_data.csv"):
    """Loads the raw scraping output. Need to handle empty headers or missing files."""
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

def clean_data(df):
    """
    Initial cleaning:
    - Drop duplicates if the scraper hit the same product twice.
    - Handle missing review text (VADER needs strings).
    """
    print("Cleaning raw data...")
    # df.dropna(subset=['review_text'], inplace=True)
    return df

def run_sentiment(df):
    """
    Apply VADER scores to each review.
    We'll focus on the 'compound' score as our primary metric.
    """
    print("Running VADER sentiment analysis...")
    # analyzer = SentimentIntensityAnalyzer()
    # Logic to be implemented in Phase 3
    return df

def main():
    # Pipeline: Load -> Clean -> Analyze -> Save
    df_raw = load_raw_data()
    
    if df_raw.empty:
        print("No raw data found. Have you run scraper.py yet?")
        return

    df_clean = clean_data(df_raw)
    df_enriched = run_sentiment(df_clean)
    
    # Save results for the dashboard
    # df_enriched.to_csv("data/processed_data.csv", index=False)
    print("Analysis phase complete (boilerplate).")

if __name__ == "__main__":
    main()
