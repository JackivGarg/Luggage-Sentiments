import pandas as pd
import os
import re
import json
import random
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

hf_client = InferenceClient(api_key=os.environ.get("HF_TOKEN"))
HF_MODEL = "meta-llama/Llama-3.3-70B-Instruct"

def load_data(filepath):
    return pd.read_csv(filepath)

def add_sentiment_scores(df):
    analyzer = SentimentIntensityAnalyzer()
    df['review_text'] = df['review_text'].astype(str).fillna('')
    df['sentiment_score'] = df['review_text'].apply(lambda x: analyzer.polarity_scores(x)['compound'])
    return df

def get_themes(pos_reviews, neg_reviews):
    if not pos_reviews and not neg_reviews:
        return "None", "None"

    pos_sample = random.sample(pos_reviews, min(20, len(pos_reviews)))
    neg_sample = random.sample(neg_reviews, min(20, len(neg_reviews)))

    prompt = (
        "You are a luggage product analyst. Given these reviews, return ONLY a JSON object with keys "
        "'pros' and 'cons', each a list of exactly 3 SHORT, SPECIFIC points (max 5 words each).\n"
        "RULES: Pros = specific strengths (e.g. 'Smooth spinner wheels'). "
        "Cons = specific failure modes (e.g. 'Zipper breaks quickly'). "
        "Pros and cons must cover DIFFERENT aspects — no contradictions.\n\n"
        f"Positive reviews: {' | '.join(pos_sample)}\n"
        f"Negative reviews: {' | '.join(neg_sample)}\n\n"
        'Return ONLY valid JSON like: {"pros": ["...", "...", "..."], "cons": ["...", "...", "..."]}'
    )

    try:
        response = hf_client.chat.completions.create(
            model=HF_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
        )
        text = response.choices[0].message.content
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            pros = ", ".join(data.get("pros", [])[:3] or ["None"])
            cons = ", ".join(data.get("cons", [])[:3] or ["None"])
            return pros, cons
    except Exception as e:
        print(f"  HF Error: {e}")

    return "Error", "Error"

def extract_themes(df):
    pos_themes_dict = {}
    neg_themes_dict = {}
    for brand in df['brand'].unique():
        print(f"  -> Extracting themes for {brand}...")
        brand_df = df[df['brand'] == brand]
        pos = brand_df[brand_df['sentiment_score'] > 0.05]['review_text'].tolist()
        neg = brand_df[brand_df['sentiment_score'] < -0.05]['review_text'].tolist()
        pros, cons = get_themes(pos, neg)
        pos_themes_dict[brand] = pros
        neg_themes_dict[brand] = cons
    return pos_themes_dict, neg_themes_dict

def aggregate_data(df, pos_themes, neg_themes):
    agg = df.groupby('brand').agg(
        avg_price=('price', 'mean'),
        avg_mrp=('mrp', 'mean'),
        avg_discount_pct=('discount_pct', 'mean'),
        avg_rating=('rating', 'mean'),
        avg_sentiment=('sentiment_score', 'mean'),
        total_reviews=('review_text', 'count')
    ).reset_index()
    agg['top_5_positive_themes'] = agg['brand'].map(pos_themes)
    agg['top_5_negative_themes'] = agg['brand'].map(neg_themes)
    for col in ['avg_price', 'avg_mrp', 'avg_discount_pct', 'avg_rating']:
        agg[col] = agg[col].round(2)
    agg['avg_sentiment'] = agg['avg_sentiment'].round(3)
    return agg

def main():
    raw_path = 'data/raw_data.csv'
    processed_path = 'data/processed_data.csv'
    summary_path = 'data/brand_summary.csv'

    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} not found.")
        return

    print("Loading raw data...")
    df = load_data(raw_path)

    print("Running VADER sentiment analysis...")
    df = add_sentiment_scores(df)

    print("Extracting themes using Llama (HuggingFace)...")
    pos_themes, neg_themes = extract_themes(df)

    print("Aggregating brand summary...")
    brand_summary = aggregate_data(df, pos_themes, neg_themes)

    os.makedirs('data', exist_ok=True)
    df.to_csv(processed_path, index=False)
    brand_summary.to_csv(summary_path, index=False)

    print(f"\nDone! {len(df)} rows -> {processed_path}")
    print(f"{len(brand_summary)} brands -> {summary_path}\n")
    print(brand_summary[['brand', 'top_5_positive_themes', 'top_5_negative_themes']].to_string(index=False))

if __name__ == '__main__':
    main()
