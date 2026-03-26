# 🧳 Luggage Brand Competitive Intelligence Dashboard

This project is a competitive intelligence tool designed to monitor and analyze sentiment for major luggage brands on Amazon India. By scraping customer reviews and running them through a sentiment analysis pipeline, we can gain insights into what customers love (and hate) about specific brands.

---

## 🔍 Project Vision

The goal is to provide a real-time (or near real-time) dashboard that helps business analysts compare brands side-by-side. 

- **Scraping**: Using Playwright to navigate Amazon's search results and extract product details and customer reviews.
- **Sentiment**: Using VADER (`vaderSentiment`) which is specifically tuned for social media and product-like text (handling emojis, punctuation, and intensifiers).
- **Visualization**: A clean Streamlit interface with Plotly charts for competitive benchmarking.

---

## 🛠️ Project Structure

```text
munshot/
├── link.txt              # Our source list: Brand Name | Search URL
├── scraper.py            # The data fetcher (Playwright) -> saves to raw_data.csv
├── analyze.py            # The "brain" (VADER Sentiment) -> saves to processed_data.csv
├── app.py                # The interactive dashboard (Streamlit + Plotly)
├── requirements.txt      # Python dependencies
├── README.md             # This guide
└── data/                 # Local data storage
    ├── raw_data.csv      # Unfiltered, scraped data
    └── processed_data.csv # Enriched data with sentiment scores
```

---

## 🚀 Getting Started

### 1. Environment Setup
First, make sure you have the dependencies installed. I've pinned these to stable versions that I know play well together.

```bash
pip install -r requirements.txt
```

Since we're using Playwright, you'll also need to install the browser binaries:
```bash
playwright install chromium
```

### 2. Running the Pipeline
The project follows a linear data pipeline:

1.  **Scrape**: `python scraper.py` — This marks the start. It reads `link.txt` and goes out to fetch the data.
2.  **Analyze**: `python analyze.py` — Once we have the raw data, this script cleans it and runs the sentiment scoring.
3.  **Visualize**: `streamlit run app.py` — Finally, launch the dashboard to see the results.

---

## 📈 Developer Roadmap
- [x] **Scaffold**: Folder structure, dependencies, and empty data stores.
- [x] **Scraper**: Async Playwright — products + reviews, pricing, user-agent rotation.
- [ ] **Analysis**: Fine-tune VADER thresholds and add data cleaning steps.
- [ ] **Dashboard**: Build out the multi-brand comparison views.