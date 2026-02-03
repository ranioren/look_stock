import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from utils import extract_content
from analysis import analyze_market_sentiment
from finance_utils import get_stock_history, get_analyst_recommendation

# Load environment variables
load_dotenv()

def main():
    st.set_page_config(page_title="Lock Stock", page_icon="shotgun.png", layout="wide")

    c1, c2 = st.columns([0.5, 10])
    with c1:
        st.image("shotgun.png", width=80)
    with c2:
        st.title("Lock Stock")
    st.markdown("Analyze stocks from various data sources (Text, Webpage, Tweet) using Gemini.")

    api_key = os.getenv("GEMINI_API_KEY")
    # Check for API Key
    if not api_key:
        st.error("⚠️ GEMINI_API_KEY not found in .env file.")
        st.stop()

    # Single Input
    user_input = st.text_input("Enter text or URL (Webpage/Tweet):", placeholder="Paste text or URL here...")

    if st.button("Process Input"):
        if user_input:
            with st.spinner("Processing & Analyzing..."):
                extracted_text, source_type = extract_content(user_input)
                
                if extracted_text:
                    st.success(f"Source detected: {source_type}")
                    
                    # Run Analysis
                    analysis_result = analyze_market_sentiment(extracted_text, api_key)
                    
                    if isinstance(analysis_result, dict) and "summary" in analysis_result:
                        # 1. Display Summary (Previous Output)
                        st.subheader("Market Sentiment Summary")
                        st.markdown(analysis_result["summary"])
                        
                        # 2. Display Detailed Table/Expanders
                        st.subheader("Detailed Stock Analysis")
                        if "stocks" in analysis_result and analysis_result["stocks"]:
                            for stock in analysis_result["stocks"]:
                                with st.expander(f"{stock.get('Symbol')} - {stock.get('Name')} ({stock.get('Sentiment', 'N/A')})"):
                                    # Main Metrics
                                    c1, c2, c3 = st.columns(3)
                                    c1.metric("Market Cap", stock.get("Market_Cap", "N/A"))
                                    c2.metric("Revenue (LQ)", stock.get("Revenue_LQ", "N/A"))
                                    c3.metric("Net Income (LQ)", stock.get("Net_Income_LQ", "N/A"))
                                    
                                    st.markdown(f"**Reasoning:** {stock.get('Reason')}")
                                    
                                    
                                    # Financial Ratios & Analyst Recommendation (2 Columns)
                                    col_ratios, col_analyst = st.columns(2)
                                    
                                    with col_ratios:
                                        st.markdown("#### Financial Ratios")
                                        ratios = stock.get("Financial_Ratios", {})
                                        st.metric("P/E Ratio", ratios.get("P_E_Ratio", "N/A"))
                                        st.metric("EPS", ratios.get("EPS", "N/A"))
                                        st.metric("Debt/Equity", ratios.get("Debt_to_Equity", "N/A"))
                                        
                                    with col_analyst:
                                        st.markdown("#### Analyst Consensus")
                                        rec_df = get_analyst_recommendation(stock.get("Symbol"))
                                        if rec_df is not None:
                                            st.bar_chart(rec_df, x="Recommendation", y="Count", height=250)
                                        else:
                                            st.write("Analyst data unavailable.")
                                    
                                    # Stock Price Chart
                                    st.markdown("#### Price History (Last 3 Months)")
                                    history_df = get_stock_history(stock.get("Symbol"))
                                    if history_df is not None and not history_df.empty:
                                        st.line_chart(history_df, height=300)
                                    else:
                                        st.write("Price history unavailable.")

                                    # Sources
                                    st.markdown("#### Analyst Sources")
                                    sources = stock.get("Analyst_Sources", [])
                                    if sources:
                                        st.write(", ".join(sources))
                                    else:
                                        st.write("No specific analyst sources mentioned.")
                        else:
                            st.info("No relevant stocks found.")
                            
                    elif isinstance(analysis_result, list): # Fallback for old format if cached/weird
                         st.subheader("Gemini Analysis (Financial Metrics):")
                         df = pd.DataFrame(analysis_result)
                         st.dataframe(df, use_container_width=True)
                    else:
                        st.write(analysis_result)
                else:
                    st.error(f"Failed to process input: {source_type}")
        else:
            st.warning("Please provide some input.")

if __name__ == "__main__":
    main()
