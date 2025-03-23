#!/usr/bin/env python
"""
Ultra-Simple Scanner - A very basic scanner that just shows simple indicators
"""
import sys
import argparse
import pandas as pd
import yfinance as yf
from datetime import datetime

def fetch_data(symbol, timeframe="1d", period="1y"):
    """Fetch market data for the given symbol."""
    print(f"Fetching data for {symbol} on {timeframe} timeframe...")
    try:
        data = yf.download(symbol, period=period, interval=timeframe, progress=False)
        print(f"Fetched {len(data)} data points for {symbol}")
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return pd.DataFrame()

def calculate_indicators(data):
    """Calculate basic technical indicators."""
    if data.empty:
        return data
        
    # Calculate moving averages
    data['SMA20'] = data['Close'].rolling(window=20).mean()
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['SMA200'] = data['Close'].rolling(window=200).mean()
    
    # Calculate daily change
    data['Change'] = data['Close'].pct_change() * 100
    
    # Calculate ATR (Average True Range) - simplified approach
    data['HL'] = data['High'] - data['Low']
    data['HC'] = abs(data['High'] - data['Close'].shift(1))
    data['LC'] = abs(data['Low'] - data['Close'].shift(1))
    
    # Use maximum of the three TR components
    data['TR'] = data[['HL', 'HC', 'LC']].max(axis=1)
    data['ATR14'] = data['TR'].rolling(window=14).mean()
    
    return data
    
def analyze_simple_trend(data):
    """Perform a simple trend analysis."""
    if data.empty or len(data) < 50:
        return "Insufficient data for analysis"
    
    # Get current values
    current = data.iloc[-1]
    price = current['Close']
    sma20 = data['Close'].rolling(window=20).mean().iloc[-1]
    sma50 = data['Close'].rolling(window=50).mean().iloc[-1]
    sma200 = data['Close'].rolling(window=200).mean().iloc[-1]
    
    # Convert to scalar values to avoid Series comparison issues
    price_val = float(price.iloc[0]) if hasattr(price, 'iloc') else float(price)
    sma20_val = float(sma20.iloc[0]) if hasattr(sma20, 'iloc') else float(sma20)
    sma50_val = float(sma50.iloc[0]) if hasattr(sma50, 'iloc') else float(sma50)
    sma200_val = float(sma200.iloc[0]) if hasattr(sma200, 'iloc') else float(sma200)
    
    # Determine trend based on price vs SMAs
    trend = "Neutral"
    signals = []
    
    # Calculate trend based on SMAs
    if price_val > sma20_val and price_val > sma50_val and price_val > sma200_val:
        trend = "Strong Bullish"
        signals.append("BUY: Strong uptrend")
    elif price_val < sma20_val and price_val < sma50_val and price_val < sma200_val:
        trend = "Strong Bearish"
        signals.append("SELL: Strong downtrend")
    elif price_val > sma20_val and price_val > sma50_val:
        trend = "Bullish"
        signals.append("BUY: Uptrend")
    elif price_val < sma20_val and price_val < sma50_val:
        trend = "Bearish"
        signals.append("SELL: Downtrend")
    
    # Create result dictionary with basic analysis
    result = {
        'trend': trend,
        'signals': signals,
        'daily_change': float(current['Change'].iloc[0]) if hasattr(current['Change'], 'iloc') and 'Change' in current else 0.0,
        'volume': int(current['Volume'].iloc[0]) if hasattr(current['Volume'], 'iloc') else int(current['Volume']),
        'atr': float(current['ATR14'].iloc[0]) if hasattr(current['ATR14'], 'iloc') and 'ATR14' in current else 0.0,
        'price': price_val,
        'sma20': sma20_val,
        'sma50': sma50_val,
        'sma200': sma200_val
    }
    
    # Calculate 52-week high and low
    try:
        year_high = float(data['High'].rolling(window=252).max().iloc[-1].iloc[0]) if hasattr(data['High'].rolling(window=252).max().iloc[-1], 'iloc') else float(data['High'].rolling(window=252).max().iloc[-1])
        year_low = float(data['Low'].rolling(window=252).min().iloc[-1].iloc[0]) if hasattr(data['Low'].rolling(window=252).min().iloc[-1], 'iloc') else float(data['Low'].rolling(window=252).min().iloc[-1])
        
        # Calculate distance from 52-week high and low as percentages
        high_distance = ((year_high - price_val) / price_val) * 100
        low_distance = ((price_val - year_low) / year_low) * 100
        
        result['year_high'] = year_high
        result['year_high_distance'] = high_distance
        result['year_low'] = year_low
        result['year_low_distance'] = low_distance
        
        # Add signals based on 52-week high/low proximity
        if high_distance < 5:
            signals.append("CAUTION: Near 52-week high")
        if low_distance < 5:
            signals.append("OPPORTUNITY: Near 52-week low")
            
    except Exception as e:
        print(f"Warning: Could not calculate 52-week high/low: {e}")
        result['year_high'] = None
        result['year_high_distance'] = None
        result['year_low'] = None
        result['year_low_distance'] = None
    
    return result

def scan_symbol(symbol, timeframe="1d", period="1y"):
    """Scan a single symbol and output basic analysis."""
    # Fetch the data
    data = fetch_data(symbol, timeframe, period)
    if data.empty:
        return {
            'symbol': symbol,
            'error': 'No data available',
            'timestamp': datetime.now().isoformat()
        }
    
    # Calculate indicators
    data = calculate_indicators(data)
    
    # Analyze the trend
    trend_analysis = analyze_simple_trend(data)
    
    # Create result
    result = {
        'symbol': symbol,
        'timestamp': datetime.now().isoformat(),
        'last_price': float(data['Close'].iloc[-1].iloc[0]) if hasattr(data['Close'].iloc[-1], 'iloc') else float(data['Close'].iloc[-1]),
        'analysis': trend_analysis
    }
    
    return result

def main():
    """Main function to run the scanner."""
    parser = argparse.ArgumentParser(description="Run the ultra-simple scanner")
    parser.add_argument("--symbols", type=str, nargs="+", default=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
                        help="List of symbols to scan")
    parser.add_argument("--timeframe", type=str, default="1d",
                        help="Timeframe to use (e.g., 1d, 1h, 15m)")
    parser.add_argument("--period", type=str, default="1y",
                        help="Period to fetch data for (e.g., 1d, 5d, 1mo, 1y, 2y)")
    args = parser.parse_args()
    
    print("\n=== ULTRA SIMPLE MARKET SCANNER ===\n")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scanning {len(args.symbols)} symbols on {args.timeframe} timeframe\n")
    
    # Scan each symbol
    for symbol in args.symbols:
        result = scan_symbol(symbol, args.timeframe, args.period)
        
        print(f"\n----- {symbol} -----")
        
        if 'error' in result:
            print(f"Error: {result['error']}")
            continue
        
        # Display the results
        analysis = result.get('analysis', {})
        if isinstance(analysis, str):
            print(analysis)
            continue
            
        print(f"Current Price: ${result['last_price']:.2f}")
        print(f"Trend: {analysis.get('trend', 'Unknown')}")
        print(f"Daily Change: {analysis.get('daily_change', 0):.2f}%")
        print(f"SMA20: ${analysis.get('sma20', 0):.2f}")
        print(f"SMA50: ${analysis.get('sma50', 0):.2f}")
        print(f"SMA200: ${analysis.get('sma200', 0):.2f}")
        print(f"ATR (14): ${analysis.get('atr', 0):.2f}")
        print(f"Volume: {analysis.get('volume', 0):,}")
        
        if analysis.get('year_high') is not None:
            print(f"52-Week High: ${analysis.get('year_high'):.2f} ({analysis.get('year_high_distance'):.2f}%)")
            print(f"52-Week Low: ${analysis.get('year_low'):.2f} ({analysis.get('year_low_distance'):.2f}%)")
        else:
            print(f"52-Week High: $nan (nan%)")
            print(f"52-Week Low: $nan (nan%)")
        
        # Simple Buy/Sell signals
        signals = analysis.get('signals', [])
        if signals:
            print("\nSignals:")
            for signal in signals:
                print(f"- {signal}")
        else:
            print("\nNo clear signals at this time")
    
    print("\n=== Scan Complete ===\n")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 