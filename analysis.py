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
        You are an investment manager. Analyze the following article/text and identify which companies (Positive/Bullish or Negative/Bearish).
        
        1. Provide a general summary of the market sentiment found in the text (Markdown format).
        2. identify companies that would be affected positively or negatively by this news, provide the basic details (Symbol, Name, Sentiment, Reason, Analyst Sources).
        
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
        
        # --- Second Pass: Find Positively Affected Companies ---
        if "stocks" in result and result["stocks"]:
            original_stocks = result["stocks"]
            stock_summaries = [f"{s.get('Name')} ({s.get('Symbol')}): {s.get('Sentiment')}" for s in original_stocks]
            context_str = ", ".join(stock_summaries)
            
            second_prompt = f"""
            Based on the analysis that the following companies are affected: {context_str}
            And the news summary: {result.get('summary', '')}
            
            Identify OTHER companies that would be POSITIVELY affected by this situation (e.g. suppliers, partners, competitors if the news is bad for the first group).
            
            Return the result STRICTLY as a single JSON object with a key "stocks".
            
            Format:
            {{
                "stocks": [
                    {{
                        "Symbol": "TSM",
                        "Name": "Taiwan Semiconductor",
                        "Sentiment": "Bullish",
                        "Reason": "Supplier to Nvidia...",
                        "Analyst_Sources": ["MarketWatch"]
                    }}
                ]
            }}
            """
            try:
                second_response = model.generate_content(second_prompt)
                second_clean = second_response.text.strip()
                if second_clean.startswith("```json"): second_clean = second_clean[7:]
                if second_clean.startswith("```"): second_clean = second_clean[3:]
                if second_clean.endswith("```"): second_clean = second_clean[:-3]
                
                second_result = json.loads(second_clean)
                
                if "stocks" in second_result:
                    # Filter out duplicates
                    existing_symbols = {s.get("Symbol") for s in original_stocks if s.get("Symbol")}
                    for new_stock in second_result["stocks"]:
                        if new_stock.get("Symbol") and new_stock.get("Symbol") not in existing_symbols:
                            original_stocks.append(new_stock) # Append to main list
                            
            except Exception as e:
                print(f"Secondary analysis failed: {e}") # Non-blocking error

        # Enrich with yfinance data (for ALL stocks now)
        if "stocks" in result:
            for stock in result["stocks"]:
                symbol = stock.get("Symbol")
                if symbol:
                    metrics = get_stock_metrics(symbol)
                    stock.update(metrics) # Merge yfinance data into the stock dict
        
        return result
        
    except Exception as e:
        return {"summary": f"Error analyzing text: {str(e)}", "stocks": []}
