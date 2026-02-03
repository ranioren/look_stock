import yfinance as yf
import finnhub
import os
import pandas as pd

def get_finnhub_client():
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return None
    return finnhub.Client(api_key=api_key)

def format_large_number(num):
    if not num:
        return "N/A"
    if num >= 1e12:
        return f"${num/1e12:.2f}T"
    if num >= 1e9:
        return f"${num/1e9:.2f}B"
    if num >= 1e6:
        return f"${num/1e6:.2f}M"
    return f"${num:,.2f}"

def get_stock_metrics(symbol):
    """
    Fetches real-time financial data using yfinance.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Safe extraction with defaults
        market_cap = info.get("marketCap")
        revenue = info.get("totalRevenue")
        net_income = info.get("netIncomeToCommon")
        
        # Ratios
        pe_ratio = info.get("trailingPE")
        eps = info.get("trailingEps")
        debt_to_equity = info.get("debtToEquity")
        
        metrics = {
            "Market_Cap": format_large_number(market_cap),
            "Revenue_LQ": format_large_number(revenue), # Note: yf often gives TTM, but for simplicity we label generally
            "Net_Income_LQ": format_large_number(net_income),
            "Financial_Ratios": {
                "P_E_Ratio": f"{pe_ratio:.2f}" if pe_ratio else "N/A",
                "EPS": f"${eps:.2f}" if eps else "N/A",
                "Debt_to_Equity": f"{debt_to_equity:.2f}" if debt_to_equity else "N/A"
            }
        }
        return metrics
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return {}

def get_stock_history(symbol, period="3mo"):
    """
    Fetches historical stock data (Close price) for the given period.
    Returns a DataFrame with Date index and Close column.
    """
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period)
        if history.empty:
            return None
        return history[['Close']]
    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
        return None

def get_analyst_recommendation(symbol):
    """
    Fetches latest analyst recommendation trends from Finnhub.
    Returns a DataFrame or dictionary for visualization.
    """
    try:
        client = get_finnhub_client()
        if not client:
            return None
            
        # Get recommendation trends (returns list of dicts)
        # Each dict usually has: {'buy': int, 'hold': int, 'period': '2023-11-01', 'sell': int, 'strongBuy': int, 'strongSell': int, 'symbol': 'AAPL'}
        trends = client.recommendation_trends(symbol)
        
        if not trends:
            return None
            
        # Finnhub returns newest first usually. Let's take the latest (index 0)
        latest = trends[0]
        
        # Prepare data for chart: Categories vs Count
        data = {
            "Recommendation": ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"],
            "Count": [
                latest.get("strongBuy", 0),
                latest.get("buy", 0),
                latest.get("hold", 0),
                latest.get("sell", 0),
                latest.get("strongSell", 0)
            ]
        }
        return pd.DataFrame(data)
        
    except Exception as e:
        print(f"Error fetching recommendations for {symbol}: {e}")
        return None
