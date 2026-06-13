"""
Market metrics calculator for Indian indices
Uses Indian Stock Market API (community API)
For: NIFTY50, Nifty Next50, Nifty Midcap 150
"""

import requests
import json
import os
from datetime import datetime

# Indian Stock Market API base URL
API_BASE = "http://65.0.104.9"

# Index symbols for the API
INDICES = {
    "NIFTY50": "NIFTY 50",
    "NIFTY_NEXT50": "NIFTY NEXT 50",
    "NIFTY_MIDCAP150": "NIFTY MIDCAP 150"
}


def fetch_index_data(index_symbol):
    """
    Fetch index data using Indian Stock Market API
    
    Args:
        index_symbol (str): Index symbol (e.g., "NIFTY 50")
        
    Returns:
        dict: Index data or error message
    """
    try:
        print(f"Fetching data for {index_symbol}...")
        
        # Construct API URL
        url = f"{API_BASE}/stock"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        params = {
            'symbol': index_symbol
        }
        
        # Make request with timeout
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if data is valid
        if data and isinstance(data, dict):
            print(f"✓ Successfully fetched {index_symbol}")
            return data
        else:
            print(f"⚠ No valid data returned for {index_symbol}")
            return {"error": f"No data found for {index_symbol}"}
    
    except requests.exceptions.Timeout:
        print(f"✗ Timeout fetching {index_symbol}")
        return {"error": f"Request timeout for {index_symbol}"}
    except requests.exceptions.ConnectionError:
        print(f"✗ Connection error for {index_symbol}")
        return {"error": f"Connection error for {index_symbol}"}
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON response for {index_symbol}")
        return {"error": f"Invalid response for {index_symbol}"}
    except Exception as e:
        print(f"✗ Error for {index_symbol}: {str(e)}")
        return {"error": str(e)}


def calculate_metrics(index_symbol, index_display_name):
    """
    Calculate metrics for index using API data
    
    Args:
        index_symbol (str): Index symbol for API
        index_display_name (str): Display name
        
    Returns:
        dict: Calculated metrics
    """
    try:
        # Fetch current data
        index_data = fetch_index_data(index_symbol)
        
        if "error" in index_data:
            return {"error": index_data["error"], "ticker": index_display_name}
        
        # Extract metrics from API response
        metrics = {
            "ticker": index_display_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            "raw_data": index_data
        }
        
        # Current price
        if 'currentPrice' in index_data:
            metrics["current_price"] = float(index_data['currentPrice'])
        elif 'price' in index_data:
            metrics["current_price"] = float(index_data['price'])
        else:
            return {"error": "Could not extract price", "ticker": index_display_name}
        
        # 52-week high
        if 'high52Week' in index_data:
            metrics["week_52_high"] = float(index_data['high52Week'])
        elif '52WeekHigh' in index_data:
            metrics["week_52_high"] = float(index_data['52WeekHigh'])
        
        # 52-week low
        if 'low52Week' in index_data:
            metrics["week_52_low"] = float(index_data['low52Week'])
        elif '52WeekLow' in index_data:
            metrics["week_52_low"] = float(index_data['52WeekLow'])
        
        # Today's high
        if 'dayHigh' in index_data:
            metrics["today_high"] = float(index_data['dayHigh'])
        elif 'high' in index_data:
            metrics["today_high"] = float(index_data['high'])
        
        # Today's low
        if 'dayLow' in index_data:
            metrics["today_low"] = float(index_data['dayLow'])
        elif 'low' in index_data:
            metrics["today_low"] = float(index_data['low'])
        
        # Percentage change
        if 'priceChangePercent' in index_data:
            metrics["pct_change"] = float(index_data['priceChangePercent'])
        elif 'percentChange' in index_data:
            metrics["pct_change"] = float(index_data['percentChange'])
        
        # Open price
        if 'open' in index_data:
            metrics["open_price"] = float(index_data['open'])
        
        # Close price
        if 'close' in index_data:
            metrics["close_price"] = float(index_data['close'])
        
        # Calculate percentage from 52-week high
        if 'current_price' in metrics and 'week_52_high' in metrics:
            if metrics['week_52_high'] > 0:
                pct_diff = ((metrics['current_price'] - metrics['week_52_high']) / metrics['week_52_high']) * 100
                metrics['pct_from_52w_high'] = round(pct_diff, 2)
        
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
    lines = [
        f"📊 {metrics['ticker']}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━"
    ]
    
    if 'current_price' in metrics:
        lines.append(f"💰 Current: {metrics['current_price']:.2f}")
    
    if 'open_price' in metrics:
        lines.append(f"📍 Open: {metrics['open_price']:.2f}")
    
    if 'today_high' in metrics and 'today_low' in metrics:
        lines.append(f"📈 High/Low: {metrics['today_high']:.2f} / {metrics['today_low']:.2f}")
    
    if 'pct_change' in metrics:
        change = metrics['pct_change']
        emoji = "🟢" if change >= 0 else "🔴"
        lines.append(f"{emoji} Change: {change:+.2f}%")
    
    if 'week_52_high' in metrics:
        lines.append(f"🎯 52W High: {metrics['week_52_high']:.2f}")
    
    if 'week_52_low' in metrics:
        lines.append(f"📉 52W Low: {metrics['week_52_low']:.2f}")
    
    if 'pct_from_52w_high' in metrics:
        lines.append(f"📊 vs 52W High: {metrics['pct_from_52w_high']:+.2f}%")
    
    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"⏰ {metrics['timestamp']}"
    ])
    
    return "\n".join(lines)


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
        "🚀 Indian Market Alerts Report",
        f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}",
        ""
    ]
    
    # Process each Indian index
    for index_key, index_symbol in INDICES.items():
        print(f"\nProcessing {index_key}...")
        metrics = calculate_metrics(index_symbol, index_key.replace('_', ' '))
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
