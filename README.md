# Luggage Sentiments: Amazon Review Analysis Dashboard

A comprehensive dashboard for analyzing customer sentiment on luggage brands sold on Amazon India. This tool scrapes review data, performs NLP sentiment analysis, and presents actionable insights via an interactive Streamlit UI.

## Methodology

- **Sentiment Scoring**: Uses **VADER** (Valence Aware Dictionary and sEntiment Reasoner) to assign a quantitative sentiment score (-1 to +1) to every review. VADER is particularly effective for social media and review text as it handles emojis, intensifiers, and nuanced phrasing without requiring heavy machine learning models.
- **Theme Extraction**: Utilizes **HuggingFace** and the `Llama-3.3-70B-Instruct` model to intelligently read through reviews and extract specific, non-contradictory top Pros & Cons for each luggage brand.
- **AI Matchmaker**: Features an intelligent Chatbot (powered by Llama 70B) in the dashboard that takes user preferences (e.g., "I need a cheap cabin bag with good wheels") and recommends specific luggage models, factoring in real-world prices and sentiment data.

## Dataset Description

The analysis covers 6 major luggage brands:
* Safari
* Skybags
* American Tourister
* VIP
* Aristocrat
* Nasher Miles

**Core Columns Context:**
- `brand`: The brand of the luggage.
- `product_title`: Full product listing name.
- `price` / `mrp` / `discount_pct`: Pricing metrics for value analysis.
- `rating` / `review_count`: Overall product consensus metrics.
- `reviewer_name` / `reviewer_rating`: Individual user consensus metrics.
- `review_text`: The textual review analyzed by VADER.
- `sentiment_score`: The VADER compound sentiment score mapping text to a -1 to +1 polarity.

## Known Limitations

- **Scraping Constraints**: Reviews are scraped exclusively from the primary product page. Pagination into the dedicated "All Reviews" section is restricted due to Amazon's aggressive anti-bot protections and CAPTCHA walls.

## Getting Started

### Installation

Install the required Python dependencies listed in the requirements file:
```bash
pip install -r requirements.txt
```

*(Note: Ensure you have run Phase 1 (scraper) and Phase 3 (`analyze.py`) before launching the dashboard so that the `data/processed_data.csv` is populated).*

### Running the Dashboard

To launch the interactive Streamlit dashboard:
```bash
streamlit run app.py
```