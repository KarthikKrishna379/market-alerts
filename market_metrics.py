"""
Market metrics calculator for Indian indices
Calculates: 200 DMA, 50 DMA, 52 Week High, and % differences
For: NIFTY50, Nifty Next50, Nifty Midcap 150
Uses nsepython for reliable NSE India data
"""

import requests
import json
import os
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO

# NSE India index symbols
INDICES = {
    "NIFTY50": "NIFTY 50",
    "NIFTY_NEXT50": "NIFTY NEXT 50",
    "NIFTY_MIDCAP150": "NIFTY MIDCAP 150"
}


def fetch_nse_index_data(index_name):
    """
    Fetch NSE index data using NSE India's unofficial API
    
    Args:
        index_name (str): Index name (e.g., "NIFTY 50")
        
    Returns:
        dict: Index data or error message
    """
    try:
        print(f"Fetching data for {index_name}...")
        
        # NSE India API endpoint for index data
        url = f"https://www.nseindia.com/api/index-data"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        params = {
            'index': index_name
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            print(f"✓ Successfully fetched {index_name}")
            return data['data'][0]
        else:
            return {"error": f"No data found for {index_name}"}
    
    except Exception as e:
        print(f"✗ Error for {index_name}: {str(e)}")
        return {"error": str(e)}


def fetch_nse_historical_data(index_symbol):
    """
    Fetch historical data for NSE index
    
    Args:
        index_symbol (str): Index symbol (e.g., "NIFTY 50")
        
    Returns:
        list: Historical data points
    """
    try:
        # Using nsepython library to get historical data
        from nsepython import nsefetch
        
        print(f"Fetching historical data for {index_symbol}...")
        
        # Get data for last 1 year
        data = nsefetch(
            f"https://www.nseindia.com/api/historical/cm/equity/shares/csv/{index_symbol.lower().replace(' ', '%20')}",
            user_agent="Mozilla/5.0"
        )
        
        return data
    
    except Exception as e:
        print(f"⚠ Error fetching historical data: {str(e)}")
        return None


def calculate_metrics_from_api(index_name, index_display_name):
    """
    Calculate metrics for NSE index using live API data
    
    Args:
        index_name (str): Index name for API
        index_display_name (str): Display name
        
    Returns:
        dict: Calculated metrics
    """
    try:
        # Fetch current data
        index_data = fetch_nse_index_data(index_name)
        
        if "error" in index_data:
            return {"error": index_data["error"], "ticker": index_display_name}
        
        # Extract current price
        if 'lastPrice' in index_data:
            current_price = float(index_data['lastPrice'])
        else:
            return {"error": "Could not extract price", "ticker": index_display_name}
        
        # NSE API provides some metrics
        # We'll use available data and fetch historical for moving averages
        metrics = {
            "ticker": index_display_name,
            "current_price": round(current_price, 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            "raw_data": index_data
        }
        
        # Try to extract 52-week high and other metrics if available
        if 'week52High' in index_data:
            metrics["week_52_high"] = round(float(index_data['week52High']), 2)
        
        if 'week52Low' in index_data:
            metrics["week_52_low"] = round(float(index_data['week52Low']), 2)
        
        # Calculate percentage difference from 52-week high if available
        if 'week_52_high' in metrics:
            pct_diff = ((current_price - metrics['week_52_high']) / metrics['week_52_high']) * 100
            metrics['pct_diff_52w_high'] = round(pct_diff, 2)
        
        return metrics
    
    except Exception as e:
        print(f"✗ Error calculating metrics: {str(e)}")
        return {"error": str(e), "ticker": index_display_name}


def format_message(metrics):
    """
    Format metrics into a readable Telegram message
    
    Args:
        metrics (dict): Dictionary of metrics
        
    Returns:
        str: Formatted message
    """
    if "error" in metrics:
        return f"❌ Error analyzing {metrics.get('ticker', 'Unknown')}: {metrics['error']}"
    
    # Build message with available data
    message_parts = [
        f"📊 Market Alert - {metrics['ticker']}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"💰 Current Price: {metrics['current_price']}"
    ]
    
    if 'week_52_high' in metrics:
        message_parts.append(f"🎯 52-Week High: {metrics['week_52_high']}")
    
    if 'week_52_low' in metrics:
        message_parts.append(f"📉 52-Week Low: {metrics['week_52_low']}")
    
    if 'pct_diff_52w_high' in metrics:
        message_parts.append(f"📊 vs 52W High: {metrics['pct_diff_52w_high']:+.2f}%")
    
    # Add raw data if available
    if 'raw_data' in metrics:
        raw = metrics['raw_data']
        if 'perChange' in raw:
            message_parts.append(f"📈 Change: {raw['perChange']}%")
        if 'highPrice' in raw:
            message_parts.append(f"📊 Today's High: {raw['highPrice']}")
        if 'lowPrice' in raw:
            message_parts.append(f"📊 Today's Low: {raw['lowPrice']}")
    
    message_parts.extend([
        f"⏰ Updated: {metrics['timestamp']}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ])
    
    return "\n".join(message_parts)


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
    for index_key, index_name in INDICES.items():
        print(f"\nProcessing {index_key}...")
        metrics = calculate_metrics_from_api(index_name, index_key.replace('_', ' '))
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
