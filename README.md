Luggage Sentiment Intelligence
A end-to-end data pipeline that scrapes Amazon India luggage reviews, runs sentiment analysis, extracts AI-powered themes, and serves everything through an interactive Streamlit dashboard — so you can actually understand what customers feel about luggage brands, not just what they rate them.


How It Works
The project runs in 3 phases, each building on the last.
Phase 1 — Scraping (scraper.py)
Playwright automates a real Chromium browser, logs into Amazon India using your saved cookies, and crawls through each brand's search results. For every brand it grabs up to 10 products, and for every product it scrapes up to 60 reviews — saving each row to CSV instantly so nothing is lost if it crashes midway.
Phase 2 — Processing (analyze.py)
Takes the raw CSV and runs two things. First, VADER sentiment analysis scores every single review from -1 to +1. Then it samples those reviews and sends them to Llama 3.3 70B via HuggingFace, which reads them and returns exactly 3 pros and 3 cons per brand in structured JSON. Finally everything gets rolled up into a clean brand summary CSV.
Phase 3 — Dashboard (app.py)
A Streamlit app with 5 pages, a brand comparison tool, a product drilldown with color-coded reviews, auto-generated insights (like which brand has inflated ratings or ineffective discounts), and an AI Matchmaker chatbot where you describe what you need and Llama recommends a specific product from the actual catalog.


Structure -> 

munshot
├── data/
│   ├── raw_data.csv
│   ├── processed_data.csv
│   └── brand_summary.csv
├── .env
├── .gitignore
├── analyze.py
├── app.py
├── cookies.json
├── link.txt
├── README.md
├── requirements.txt
└── scraper.py
