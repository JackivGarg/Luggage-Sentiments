import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

# Initialize HuggingFace Client
load_dotenv()
try:
    hf_client = InferenceClient(api_key=os.environ.get("HF_TOKEN"))
    HF_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
except Exception as e:
    hf_client = None
    pass

# Page Configuration MUST be the first Streamlit command
st.set_page_config(page_title="Luggage Sentiment Dashboard", layout="wide")

@st.cache_data
def load_data():
    try:
        df_processed = pd.read_csv("data/processed_data.csv")
        df_summary = pd.read_csv("data/brand_summary.csv")
        return df_processed, df_summary
    except Exception as e:
        st.error(f"Error loading data. Make sure Phase 3 was run. Details: {e}")
        return pd.DataFrame(), pd.DataFrame()

def main():
    df_processed, df_summary = load_data()
    
    if df_processed.empty or df_summary.empty:
        st.warning("No data found. Please run Phase 3 first.")
        return

    st.sidebar.title("Navigation")
    pages = ["Overview", "Brand Comparison", "Product Drilldown", "Agent Insights", "AI Matchmaker"]
    selection = st.sidebar.radio("Go to", pages)

    if selection == "Overview":
        render_overview(df_processed, df_summary)
    elif selection == "Brand Comparison":
        render_comparison(df_processed, df_summary)
    elif selection == "Product Drilldown":
        render_drilldown(df_processed)
    elif selection == "Agent Insights":
        render_insights(df_processed, df_summary)
    elif selection == "AI Matchmaker":
        render_matchmaker(df_processed, df_summary)

def render_overview(df_processed, df_summary):
    # ── Hero Header ──────────────────────────────────────────────────────────
    total_brands = df_summary['brand'].nunique()
    total_products = df_processed['product_title'].nunique()
    total_reviews = len(df_processed)
    overall_sentiment = df_processed['sentiment_score'].mean()

    st.markdown(f"""
    <style>
    .hero {{
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        border-radius: 16px;
        padding: 40px 48px;
        margin-bottom: 28px;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }}
    .hero h1 {{
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 8px 0;
        line-height: 1.2;
    }}
    .hero p {{
        color: rgba(255,255,255,0.65);
        font-size: 1.05rem;
        margin: 0 0 20px 0;
    }}
    .hero-badge {{
        display: inline-block;
        background: rgba(96,165,250,0.15);
        border: 1px solid rgba(96,165,250,0.4);
        color: #93c5fd;
        border-radius: 999px;
        padding: 4px 16px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
    }}
    .kpi-row {{
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
    }}
    .kpi-card {{
        flex: 1;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
    }}
    .kpi-card .kpi-icon {{ font-size: 1.6rem; }}
    .kpi-card .kpi-value {{
        font-size: 2rem;
        font-weight: 800;
        color: #f1f5f9;
        line-height: 1.1;
        margin: 4px 0;
    }}
    .kpi-card .kpi-label {{
        font-size: 0.78rem;
        color: rgba(255,255,255,0.5);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}
    </style>

    <div class="hero">
        <h1>🧳 Luggage Sentiment Intelligence</h1>
        <p>Real-time analysis of Amazon India customer reviews — surfacing what buyers truly feel about top luggage brands.</p>
        <span class="hero-badge">🏷️ {total_brands} Brands</span>
        <span class="hero-badge">📦 {total_products} Products</span>
        <span class="hero-badge">💬 {total_reviews} Reviews Analysed</span>
    </div>

    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-icon">🏷️</div>
            <div class="kpi-value">{total_brands}</div>
            <div class="kpi-label">Brands Tracked</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">📦</div>
            <div class="kpi-value">{total_products}</div>
            <div class="kpi-label">Unique Products</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">💬</div>
            <div class="kpi-value">{total_reviews}</div>
            <div class="kpi-label">Reviews Processed</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">{'🟢' if overall_sentiment > 0 else '🔴'}</div>
            <div class="kpi-value">{overall_sentiment:.3f}</div>
            <div class="kpi-label">Overall Avg Sentiment</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Sort summary by sentiment
    df_sentiment = df_summary.sort_values('avg_sentiment', ascending=False)

    # Colors: Green for > 0, Red for < 0
    colors = ['green' if x > 0 else 'red' for x in df_sentiment['avg_sentiment']]

    fig1 = go.Figure(data=[
        go.Bar(x=df_sentiment['brand'], y=df_sentiment['avg_sentiment'], marker_color=colors)
    ])
    fig1.update_layout(title="Avg Sentiment Score per Brand", xaxis_title="Brand", yaxis_title="Sentiment")

    st.plotly_chart(fig1, width='stretch')

    col_chart1, col_chart2 = st.columns(2)

    fig2 = px.bar(df_summary, x='brand', y='avg_price', title='Avg Price per Brand',
                  color='brand', text='avg_price')
    fig2.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    col_chart1.plotly_chart(fig2, width='stretch')

    fig3 = px.bar(df_summary, x='brand', y='avg_discount_pct', title='Avg Discount % per Brand',
                  color='brand', text='avg_discount_pct')
    fig3.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    col_chart2.plotly_chart(fig3, width='stretch')

def render_comparison(df_processed, df_summary):
    st.title("⚖️ Brand Comparison")
    
    brands = df_summary['brand'].tolist()
    selected_brands = st.multiselect("Choose brands to compare", brands, default=brands[:2])
    
    if not selected_brands:
        st.warning("Please select at least one brand.")
        return
        
    filtered_summary = df_summary[df_summary['brand'].isin(selected_brands)].copy()
    
    # Format the dataframe
    display_df = filtered_summary[['brand', 'avg_price', 'avg_discount_pct', 'avg_rating', 'avg_sentiment', 'total_reviews']].copy()
    st.dataframe(display_df, width='stretch', hide_index=True)
    
    st.markdown("### Top Pros & Cons")
    cols = st.columns(len(selected_brands))
    
    for i, brand in enumerate(selected_brands):
        with cols[i]:
            st.subheader(brand)
            brand_data = df_summary[df_summary['brand'] == brand].iloc[0]
            
            # Extract pros/cons
            pros = str(brand_data['top_5_positive_themes']).split(', ')
            cons = str(brand_data['top_5_negative_themes']).split(', ')
            
            pros = [p for p in pros if p != 'None'][:3]
            cons = [c for c in cons if c != 'None'][:3]
            
            st.markdown("**Top 3 Pros**")
            for pro in pros:
                st.success(f"✓ {pro}")
            if not pros:
                st.info("No significant pros found.")
                
            st.markdown("**Top 3 Cons**")
            for con in cons:
                st.error(f"✗ {con}")
            if not cons:
                st.info("No significant cons found.")

def render_drilldown(df_processed):
    st.title("🔍 Product Drilldown")
    
    # Dropdowns
    col1, col2 = st.columns(2)
    brands = df_processed['brand'].unique().tolist()
    
    with col1:
        selected_brand = st.selectbox("Pick a brand", brands)
        
    brand_products = df_processed[df_processed['brand'] == selected_brand]
    product_titles = brand_products['product_title'].unique().tolist()
    
    with col2:
        selected_product = st.selectbox("Pick a product", product_titles)
        
    product_data = brand_products[brand_products['product_title'] == selected_product]
    
    st.subheader("Product Details")
    # There could be multiple rows for one product (each row is a review)
    # So we take the first row for static product info
    info = product_data.iloc[0]
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Price", f"₹{info['price']}")
    c2.metric("MRP", f"₹{info['mrp']}")
    c3.metric("Discount", f"{info['discount_pct']}%")
    c4.metric("Rating", info['rating'])
    c5.metric("Total Reviews", info['review_count'])
    
    avg_prod_sentiment = product_data['sentiment_score'].mean()
    st.metric("Avg Sentiment Score", f"{avg_prod_sentiment:.3f}")
    
    st.divider()
    st.subheader("Sample Reviews")
    
    sample_reviews = product_data.sample(min(5, len(product_data)))
    
    for _, row in sample_reviews.iterrows():
        sentiment = row['sentiment_score']
        text = str(row['review_text'])
        
        # Determine background color based on sentiment
        if sentiment >= 0.05:
            bgColor = "#d4edda" # green
            textColor = "#155724"
        elif sentiment <= -0.05:
            bgColor = "#f8d7da" # red
            textColor = "#721c24"
        else:
            bgColor = "#e2e3e5" # neutral
            textColor = "#383d41"
            
        html = f"""
        <div style="background-color: {bgColor}; color: {textColor}; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
            <strong>Reviewer Rating: {row.get('reviewer_rating', 'N/A')}</strong> | Sentiment: {sentiment:.2f} <br><br>
            {text}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

def render_insights(df_processed, df_summary):
    st.title("💡 Agent Insights")
    st.markdown("Auto-generated insights mining the review data.")
    
    # 1. Brand with highest rating but lowest sentiment
    # We rank by rating desc and sentiment asc
    df_inflated = df_summary.sort_values(by=['avg_rating', 'avg_sentiment'], ascending=[False, True])
    b1_name = df_inflated.iloc[0]['brand']
    b1_rating = df_inflated.iloc[0]['avg_rating']
    b1_sent = df_inflated.iloc[0]['avg_sentiment']
    
    st.info(f"**Potential Inflated Ratings: {b1_name}**\n\n"
            f"Shows the highest ratings ({b1_rating}) but lowest comparative sentiment score ({b1_sent:.3f}). Users may be leaving a forced 5-star rating despite negative textual complaints.")
    
    # 2. Best value brand (sentiment / price)
    # Shift sentiment slightly to avoid negatives
    shifted_sentiment = df_summary['avg_sentiment'] + abs(df_summary['avg_sentiment'].min()) + 0.1
    df_summary['value_score'] = shifted_sentiment / df_summary['avg_price']
    df_val = df_summary.sort_values('value_score', ascending=False)
    b2_name = df_val.iloc[0]['brand']
    b2_sent = df_val.iloc[0]['avg_sentiment']
    b2_price = df_val.iloc[0]['avg_price']
    
    st.success(f"**Best Value Brand: {b2_name}**\n\n"
               f"Offers the highest sentiment ({b2_sent:.3f}) relative to its lower average price (₹{b2_price:.2f}). Highly recommended for budget buyers.")
    
    # 3. Brand with most complaints about zipper or handle
    # Filter negative reviews with keyword
    neg_reviews = df_processed[df_processed['sentiment_score'] < -0.05]
    mask = neg_reviews['review_text'].str.contains('zipper|handle', case=False, na=False)
    complaints = neg_reviews[mask].groupby('brand').size().reset_index(name='count')
    if not complaints.empty:
        complaints = complaints.sort_values('count', ascending=False)
        b3_name = complaints.iloc[0]['brand']
        b3_count = complaints.iloc[0]['count']
        total_brand_reviews = df_summary[df_summary['brand'] == b3_name].iloc[0]['total_reviews']
        pct = (b3_count / total_brand_reviews) * 100
    else:
        b3_name, b3_count, pct = "None", 0, 0
        
    st.warning(f"**Hardware Complaints: {b3_name}**\n\n"
               f"Received {b3_count} negative complaints specifically mentioning zippers or handles, making up {pct:.1f}% of their total reviews.")
    
    # 4. Brand with highest discount % but still low sentiment
    df_disc = df_summary.sort_values(by=['avg_discount_pct', 'avg_sentiment'], ascending=[False, True])
    b4_name = df_disc.iloc[0]['brand']
    b4_disc = df_disc.iloc[0]['avg_discount_pct']
    b4_sent = df_disc.iloc[0]['avg_sentiment']
    
    st.error(f"**Ineffective Deep Discounts: {b4_name}**\n\n"
             f"Offers the highest average discount at {b4_disc:.1f}%, but retains a desperately poor sentiment score of {b4_sent:.3f}. The heavy discounting is not overcoming quality concerns.")
             
    # 5. Most consistent brand (lowest std dev in reviewer_rating)
    if 'reviewer_rating' in df_processed.columns:
        std_df = df_processed.groupby('brand')['reviewer_rating'].std().reset_index(name='std_dev')
        std_df = std_df.sort_values('std_dev', ascending=True)
        b5_name = std_df.iloc[0]['brand']
        b5_std = std_df.iloc[0]['std_dev']
        b5_mean = df_summary[df_summary['brand'] == b5_name].iloc[0]['avg_rating']
        
        st.info(f"**Most Consistent Quality: {b5_name}**\n\n"
                f"Has the lowest standard deviation ({b5_std:.2f}) across user ratings with a mean of {b5_mean:.2f}. Buyers generally have the exact same predictable experience.")
    else:
        st.info("**Most Consistent Quality: N/A**\n\nReviewer ratings column not found in data.")

def render_matchmaker(df_processed, df_summary):
    st.title("🤖 AI Luggage Matchmaker")
    st.markdown("Chat with our Llama-powered assistant to find the perfect bag!")

    # Check if API Key exists
    if not os.environ.get("HF_TOKEN"):
        st.error("Missing HF_TOKEN in the environment. Please add it to your .env file to use this feature.")
        return

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Prepare catalog context
    catalog_context = df_summary.to_string(index=False)

    # Prepare specific product context
    product_stats = df_processed.groupby(['brand', 'product_title']).agg(
        avg_price=('price', 'mean'),
        avg_rating=('rating', 'mean'),
        avg_sentiment=('sentiment_score', 'mean'),
        total_reviews=('review_count', 'first')
    ).reset_index()
    product_stats['avg_price'] = product_stats['avg_price'].round(2)
    product_stats['avg_rating'] = product_stats['avg_rating'].round(2)
    product_stats['avg_sentiment'] = product_stats['avg_sentiment'].round(3)
    product_context = product_stats.to_string(index=False)

    # React to user input
    if prompt := st.chat_input("E.g., I want a cheap but high-quality cabin bag with reliable zippers"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Build prompt payload
        system_prompt = f"""
        You are an expert luggage shopping assistant. 
        Here is the catalog of available luggage BRANDS and their average stats (including top pros/cons):
        {catalog_context}
        
        Here are the specific bag MODELS available for each brand, with their individual price, rating, and sentiment:
        {product_context}
        
        The user asks: {prompt}
        
        Recommend the absolute best specific bag model(s) for them. Use formatting (bullet points, bold text) to be highly readable.
        Mention the EXACT product name, exact price, and why the brand's pros matches the user's request. Keep it short, confident, and helpful.
        """

        # Get response from HuggingFace
        with st.chat_message("assistant"):
            try:
                if hf_client:
                    response = hf_client.chat.completions.create(
                        model=HF_MODEL,
                        messages=[{"role": "user", "content": system_prompt}],
                        max_tokens=500,
                        temperature=0.5
                    )
                    full_raw_response = response.choices[0].message.content
                    st.markdown(full_raw_response)
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": full_raw_response})
                else:
                    st.error("HuggingFace client is not initialized.")
            except Exception as e:
                st.error(f"Error querying HuggingFace API: {e}")

if __name__ == "__main__":
    main()
