import json
import google.generativeai as genai

from finance_utils import get_stock_metrics

def analyze_market_sentiment(text, api_key):
    """
    Analyzes the text using Gemini to identify relevant companies and fetch financial metrics.
    Returns a list of dictionaries (JSON).
    """
    try:
        genai.configure(api_key=api_key)
        # Using available model from check_models (2026 available models)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are an investment manager. Analyze the following article/text and identify relevant companies (Positive/Bullish sentiment).
        
        1. Provide a general summary of the market sentiment found in the text (Markdown format).
        2. For each identified company, provide the basic details (Symbol, Name, Sentiment, Reason, Analyst Sources).
        
        Note: DO NOT estimate financial metrics (Revenue, Market Cap, etc.). These will be fetched fro an external API.
        
        Return the result STRICTLY as a single JSON object with two keys: "summary" and "stocks".
        
        Format:
        {{
            "summary": "Markdown text summary...",
            "stocks": [
                {{
                    "Symbol": "AAPL",
                    "Name": "Apple Inc.",
                    "Sentiment": "Bullish",
                    "Reason": "Strong iPhone sales...",
                    "Analyst_Sources": ["Goldman Sachs", "Bloomberg"]
                }},
                ...
            ]
        }}

        Article Content:
        {text[:20000]} 
        """
        
        response = model.generate_content(prompt)
        
        # Clean up response if it contains markdown code blocks
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        result = json.loads(clean_text)
        
        # Enrich with yfinance data
        if "stocks" in result:
            for stock in result["stocks"]:
                symbol = stock.get("Symbol")
                if symbol:
                    metrics = get_stock_metrics(symbol)
                    stock.update(metrics) # Merge yfinance data into the stock dict
        
        return result
        
    except Exception as e:
        return {"summary": f"Error analyzing text: {str(e)}", "stocks": []}
