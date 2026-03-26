import pandas as pd
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from google import genai
from dotenv import load_dotenv

# Load API Key from .env
load_dotenv()
try:
    gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
except Exception as e:
    print("Warning: Could not configure Gemini API Key.")
    gemini_client = None

KEYWORDS = ['wheels', 'zipper', 'handle', 'lock', 'material', 'size', 'weight', 'quality', 'price', 'durability']

def load_data(filepath):
    """Loads raw data. Assumes standard CSV structure."""
    return pd.read_csv(filepath)

def add_sentiment_scores(df):
    """Uses VADER to score every review_text row -> add column sentiment_score (-1 to +1)"""
    analyzer = SentimentIntensityAnalyzer()
    
    # Ensure review_text is string
    df['review_text'] = df['review_text'].astype(str).fillna('')
    
    # Calculate compound score directly into a new column
    df['sentiment_score'] = df['review_text'].apply(lambda x: analyzer.polarity_scores(x)['compound'])
    return df

def get_gemini_themes(reviews, sentiment_type):
    """Hits Gemini API to extract top 3 themes from a list of reviews."""
    if not reviews:
        return "None"
    
    reviews_str = " | ".join(reviews[:30]) # Limit to 30 to save context/time
    prompt = (
        f"You are an expert product analyst. Review these {sentiment_type} luggage reviews.\n"
        f"Extract the top 3 most common distinct {sentiment_type} themes/complaints/praises.\n"
        "Be extremely concise. Return ONLY a comma-separated list of exactly 3 short phrases. (e.g. 'Sturdy handle, Good wheels, Nice color').\n"
        f"Reviews:\n{reviews_str}"
    )

    try:
        if not gemini_client:
            return "API Error: No Client"
            
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        # Clean up any newlines or extra spaces
        return response.text.strip().replace('\n', '')
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Error extracting themes"

def extract_themes(df):
    """
    Extracts top 3 positive and negative themes per brand using Gemini 1.5 Flash.
    Returns two dictionaries mapping brand -> comma separated top 3 themes.
    """
    pos_themes_dict = {}
    neg_themes_dict = {}

    brands = df['brand'].unique()
    for brand in brands:
        print(f"  -> Asking Gemini for {brand} themes...")
        brand_df = df[df['brand'] == brand]
        
        # Consider reviews with >0.05 score as positive, <-0.05 as negative
        pos_reviews = brand_df[brand_df['sentiment_score'] > 0.05]['review_text'].tolist()
        neg_reviews = brand_df[brand_df['sentiment_score'] < -0.05]['review_text'].tolist()

        pos_themes_dict[brand] = get_gemini_themes(pos_reviews, "positive") if pos_reviews else "None"
        neg_themes_dict[brand] = get_gemini_themes(neg_reviews, "negative") if neg_reviews else "None"

    return pos_themes_dict, neg_themes_dict

def aggregate_data(df, pos_themes, neg_themes):
    """Aggregates per brand, adding stats and top themes"""
    agg_df = df.groupby('brand').agg(
        avg_price=('price', 'mean'),
        avg_mrp=('mrp', 'mean'),
        avg_discount_pct=('discount_pct', 'mean'),
        avg_rating=('rating', 'mean'),
        avg_sentiment=('sentiment_score', 'mean'),
        total_reviews=('review_text', 'count')
    ).reset_index()

    # Map the top themes strings
    agg_df['top_5_positive_themes'] = agg_df['brand'].map(pos_themes)
    agg_df['top_5_negative_themes'] = agg_df['brand'].map(neg_themes)

    # Clean up floats
    agg_df['avg_price'] = agg_df['avg_price'].round(2)
    agg_df['avg_mrp'] = agg_df['avg_mrp'].round(2)
    agg_df['avg_discount_pct'] = agg_df['avg_discount_pct'].round(2)
    agg_df['avg_rating'] = agg_df['avg_rating'].round(2)
    agg_df['avg_sentiment'] = agg_df['avg_sentiment'].round(3)

    return agg_df

def main():
    raw_path = 'data/raw_data.csv'
    processed_path = 'data/processed_data.csv'
    summary_path = 'data/brand_summary.csv'

    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} not found. Please ensure data exists.")
        return

    print("Loading raw data...")
    df = load_data(raw_path)
    
    print("Running VADER Sentiment Analysis...")
    df = add_sentiment_scores(df)

    print("Extracting keyword themes using Gemini...")
    pos_themes, neg_themes = extract_themes(df)

    print("Aggregating brand summary...")
    brand_summary = aggregate_data(df, pos_themes, neg_themes)

    print("Saving outputs...")
    os.makedirs('data', exist_ok=True)
    df.to_csv(processed_path, index=False)
    brand_summary.to_csv(summary_path, index=False)

    print(f"\nPhase 3 Complete! Saved {len(df)} rows to {processed_path}")
    print(f"Saved {len(brand_summary)} brand summaries to {summary_path}")
    print("\n--- brand_summary.csv contents ---")
    print(brand_summary.to_string(index=False))

if __name__ == '__main__':
    main()
