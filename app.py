"""
app.py
------
The final presentation layer. We're using Streamlit for an interactive 
web experience and Plotly for the data visualizations.
"""

import streamlit as st
import pandas as pd
import os

# --- Page Config ---
st.set_page_config(
    page_title="Luggage Sentiment Insights",
    page_icon="💼",
    layout="wide"
)

# --- Sidebar: Data Status ---
st.sidebar.title("📊 Pipeline Status")
data_file = "data/processed_data.csv"
if os.path.exists(data_file):
    st.sidebar.success("✅ Processed Data Loaded")
    # stats = os.path.getmtime(data_file)
else:
    st.sidebar.warning("⚠️ No data found. Run the pipeline first.")

# --- Main Branding ---
st.title("🧳 Luggage Brand Intelligence")
st.markdown("""
Welcome to the Competitive Intelligence Dashboard. This tool analyzes customer 
sentiment across major luggage brands on Amazon India.
""")

# --- Visual Sections (Placeholders) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Brand Rankings")
    st.info("Ranking charts will appear here once analysis is run.", icon="📊")

with col2:
    st.subheader("💡 Key Sentiment Drivers")
    st.info("Common positive/negative keywords will be extracted here.", icon="🔍")

st.divider()

st.subheader("📄 Raw Review Explorer")
st.caption("Drill down into individual customer feedback.")
st.write("---")

# TODO for Phase 4:
# - Connect to processed_data.csv
# - Add brand filter checkboxes in the sidebar
# - Implement Plotly Bar charts for sentiment comparison
# - Implement a searchable review table
