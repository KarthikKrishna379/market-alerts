"""
Market metrics calculator for stock analysis
Calculates: 200 DMA, 50 DMA, 52 Week High, and % differences
"""

import yfinance as yf
from datetime import datetime, timedelta
import requests
import json


def calculate_metrics(ticker, days_lookback=252):
    """
    Calculate market metrics for a given ticker
    
    Args:
        ticker (str): Stock ticker symbol
        days_lookback (int): Number of days to look back for calculations
        
    Returns:
        dict: Dictionary containing all metrics
    """
    try:
        # Fetch historical data
        stock = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_lookback)
        
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            return {"error": f"No data found for ticker {ticker}"}
        
        current_price = hist['Close'].iloc[-1]
        
        # Calculate 200-day moving average (200 DMA)
        dma_200 = hist['Close'].tail(200).mean() if len(hist) >= 200 else hist['Close'].mean()
        
        # Calculate 50-day moving average (50 DMA)
        dma_50 = hist['Close'].tail(50).mean() if len(hist) >= 50 else hist['Close'].mean()
        
        # Calculate 52-week high
        week_52_high = hist['Close'].max()
        
        # Calculate percentage differences
        pct_diff_200dma = ((current_price - dma_200) / dma_200) * 100
        pct_diff_52w_high = ((current_price - week_52_high) / week_52_high) * 100
        
        metrics = {
            "ticker": ticker.upper(),
            "current_price": round(current_price, 2),
            "dma_200": round(dma_200, 2),
            "dma_50": round(dma_50, 2),
            "week_52_high": round(week_52_high, 2),
            "pct_diff_200dma": round(pct_diff_200dma, 2),
            "pct_diff_52w_high": round(pct_diff_52w_high, 2),
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
    
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def format_message(metrics):
    """
    Format metrics into a readable Telegram message
    
    Args:
        metrics (dict): Dictionary of metrics from calculate_metrics()
        
    Returns:
        str: Formatted message
    """
    if "error" in metrics:
        return f"❌ Error analyzing {metrics.get('ticker', 'Unknown')}: {metrics['error']}"
    
    message = f"""
📊 Market Alert - {metrics['ticker']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Current Price: ${metrics['current_price']}

📈 Moving Averages:
   • 50 DMA: ${metrics['dma_50']}
   • 200 DMA: ${metrics['dma_200']}

🎯 52-Week High: ${metrics['week_52_high']}

📊 Percentage Differences:
   • vs 200 DMA: {metrics['pct_diff_200dma']:+.2f}%
   • vs 52W High: {metrics['pct_diff_52w_high']:+.2f}%

⏰ Updated: {metrics['timestamp']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return message.strip()


def send_telegram_message(message, bot_token, chat_id):
    """
    Send message to Telegram
    
    Args:
        message (str): Message text
        bot_token (str): Telegram bot token
        chat_id (str): Telegram chat ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False


def main():
    """Main function to run market alerts"""
    import os
    
    # Get environment variables
    tickers = os.getenv("STOCK_TICKERS", "AAPL,GOOGL,MSFT").split(",")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return
    
    all_messages = ["🚀 Market Alerts Report\n"]
    
    for ticker in tickers:
        ticker = ticker.strip()
        print(f"Processing {ticker}...")
        metrics = calculate_metrics(ticker)
        message = format_message(metrics)
        all_messages.append(message)
    
    # Combine all messages
    final_message = "\n\n".join(all_messages)
    
    # Send to Telegram
    if send_telegram_message(final_message, bot_token, chat_id):
        print("✅ Message sent successfully!")
    else:
        print("❌ Failed to send message")


if __name__ == "__main__":
    main()
