"""
Market metrics calculator for Indian indices
Calculates: 200 DMA, 50 DMA, 52 Week High, and % differences
For: NIFTY50, Nifty Next50, Nifty Midcap 150
"""

import yfinance as yf
from datetime import datetime, timedelta
import requests
import json
import os

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})
# Indian index tickers on Yahoo Finance
INDICES = {
    "NIFTY50": "^NSEI",
    "NIFTY_NEXT50": "^NSMIDCP",
    "NIFTY_MIDCAP150": "NIFTYMIDCAP150.NS"
}


def calculate_metrics(ticker_symbol, ticker_name, days_lookback=252):
    """
    Calculate market metrics for a given ticker
    
    Args:
        ticker_symbol (str): Yahoo Finance ticker symbol
        ticker_name (str): Human readable name
        days_lookback (int): Number of days to look back for calculations
        
    Returns:
        dict: Dictionary containing all metrics
    """
    try:
        print(f"Fetching data for {ticker_name} ({ticker_symbol})...")
        
        # Fetch historical data
        stock = yf.Ticker(ticker_symbol,session=session)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_lookback)
        
        # Download with retries (removed progress parameter)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty or len(hist) == 0:
            return {"error": f"No data found for {ticker_name}", "ticker": ticker_name}
        
        current_price = hist['Close'].iloc[-1]
        
        # Calculate 200-day moving average (200 DMA)
        if len(hist) >= 200:
            dma_200 = hist['Close'].tail(200).mean()
        else:
            dma_200 = hist['Close'].mean()
        
        # Calculate 50-day moving average (50 DMA)
        if len(hist) >= 50:
            dma_50 = hist['Close'].tail(50).mean()
        else:
            dma_50 = hist['Close'].mean()
        
        # Calculate 52-week high (approximately 252 trading days)
        week_52_high = hist['Close'].max()
        
        # Calculate percentage differences
        pct_diff_200dma = ((current_price - dma_200) / dma_200) * 100
        pct_diff_52w_high = ((current_price - week_52_high) / week_52_high) * 100
        
        metrics = {
            "ticker": ticker_name,
            "current_price": round(current_price, 2),
            "dma_200": round(dma_200, 2),
            "dma_50": round(dma_50, 2),
            "week_52_high": round(week_52_high, 2),
            "pct_diff_200dma": round(pct_diff_200dma, 2),
            "pct_diff_52w_high": round(pct_diff_52w_high, 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            "data_points": len(hist)
        }
        
        print(f"✓ Successfully fetched {ticker_name}")
        return metrics
    
    except Exception as e:
        print(f"✗ Error for {ticker_name}: {str(e)}")
        return {"error": str(e), "ticker": ticker_name}


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

💰 Current Price: {metrics['current_price']}

📈 Moving Averages:
   • 50 DMA: {metrics['dma_50']}
   • 200 DMA: {metrics['dma_200']}

🎯 52-Week High: {metrics['week_52_high']}

📊 Percentage Differences:
   • vs 200 DMA: {metrics['pct_diff_200dma']:+.2f}%
   • vs 52W High: {metrics['pct_diff_52w_high']:+.2f}%

⏰ Updated: {metrics['timestamp']}
📍 Data Points: {metrics['data_points']} days
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
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"✓ Message sent to Telegram")
        return True
    except Exception as e:
        print(f"✗ Error sending Telegram message: {e}")
        return False


def main():
    """Main function to run market alerts"""
    
    # Get environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("❌ Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return
    
    print("Starting Indian Market Alerts...")
    print("=" * 50)
    
    all_messages = [
        "🚀 Indian Market Alerts Report\n",
        f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n"
    ]
    
    # Process each Indian index
    for ticker_name, ticker_symbol in INDICES.items():
        print(f"\nProcessing {ticker_name}...")
        metrics = calculate_metrics(ticker_symbol, ticker_name)
        message = format_message(metrics)
        all_messages.append(message)
    
    # Combine all messages
    final_message = "\n\n".join(all_messages)
    
    print("\n" + "=" * 50)
    print("Final Message:")
    print(final_message)
    print("=" * 50)
    
    # Send to Telegram
    if send_telegram_message(final_message, bot_token, chat_id):
        print("\n✅ All alerts sent successfully!")
    else:
        print("\n❌ Failed to send alerts")


if __name__ == "__main__":
    main()
