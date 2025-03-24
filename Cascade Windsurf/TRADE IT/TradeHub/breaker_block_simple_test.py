#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Breaker Block Detection Test with Real Data
-------------------------------------------------

A simplified script to test breaker block detection on real historical data.
"""

import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.signal import argrelextrema
from loguru import logger

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, f"breaker_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(log_path, level="DEBUG")
logger.info(f"Logging to {log_path}")

# Test parameters
SYMBOLS = ["AAPL", "TSLA", "SPY", "BTC-USD"]
PERIOD = "1y"
INTERVAL = "1d"
WINDOW = 10  # Window for detecting extrema
CONFIDENCE_THRESHOLD = 0.6

def get_stock_data(symbol):
    """Get stock data from Yahoo Finance"""
    logger.info(f"Downloading {PERIOD} {INTERVAL} data for {symbol}")
    try:
        data = yf.download(symbol, period=PERIOD, interval=INTERVAL, progress=False)
        if len(data) > 30:  # Ensure we have enough data
            logger.info(f"Downloaded {len(data)} data points for {symbol}")
            return data
        else:
            logger.warning(f"Insufficient data points ({len(data)}) for {symbol}")
            return None
    except Exception as e:
        logger.error(f"Error downloading {symbol}: {e}")
        return None

def detect_breaker_blocks(data, window=10):
    """Detect breaker blocks in the data"""
    df = data.copy()
    
    # Find extrema
    max_idx = argrelextrema(df['High'].values, np.greater_equal, order=window)[0]
    min_idx = argrelextrema(df['Low'].values, np.less_equal, order=window)[0]
    
    breakers = []
    
    # Process identified extrema
    for idx in min_idx:  # Check support levels (bullish breakers)
        if idx < len(df) - window:  # Ensure we have room for future data
            support_level = float(df['Low'].iloc[idx])  # Convert to float explicitly
            
            # Check if level was broken (price went below support)
            future_data = df.iloc[idx:idx+window]
            if any(future_data['Close'] < support_level * 0.99):  # 1% break
                
                # Check if price returned to test the level
                test_data = df.iloc[idx+window:]
                if any(abs(test_data['Close'] - support_level) / support_level < 0.02):  # 2% test
                    breakers.append({
                        'type': 'bullish',
                        'price': support_level,
                        'date': df.index[idx],
                        'confidence': 0.8
                    })
                    logger.debug(f"Found bullish breaker at {float(support_level):.2f} on {df.index[idx]}")
    
    for idx in max_idx:  # Check resistance levels (bearish breakers)
        if idx < len(df) - window:
            resistance_level = float(df['High'].iloc[idx])  # Convert to float explicitly
            
            # Check if level was broken (price went above resistance)
            future_data = df.iloc[idx:idx+window]
            if any(future_data['Close'] > resistance_level * 1.01):  # 1% break
                
                # Check if price returned to test the level
                test_data = df.iloc[idx+window:]
                if any(abs(test_data['Close'] - resistance_level) / resistance_level < 0.02):  # 2% test
                    breakers.append({
                        'type': 'bearish',
                        'price': resistance_level,
                        'date': df.index[idx],
                        'confidence': 0.8
                    })
                    logger.debug(f"Found bearish breaker at {float(resistance_level):.2f} on {df.index[idx]}")
    
    return breakers

def plot_data_with_breakers(data, breakers, symbol):
    """Plot the data with identified breaker blocks"""
    plt.figure(figsize=(12, 6))
    
    # Plot price data
    plt.plot(data.index, data['Close'], label='Price', color='blue', alpha=0.5)
    
    # Plot breaker levels
    bullish_levels = [b for b in breakers if b['type'] == 'bullish']
    bearish_levels = [b for b in breakers if b['type'] == 'bearish']
    
    for b in bullish_levels:
        plt.axhline(y=b['price'], color='green', linestyle='--', alpha=0.7)
        plt.plot(b['date'], b['price'], 'go', markersize=8)
    
    for b in bearish_levels:
        plt.axhline(y=b['price'], color='red', linestyle='--', alpha=0.7)
        plt.plot(b['date'], b['price'], 'ro', markersize=8)
    
    # Add titles and labels
    plt.title(f"Breaker Block Detection - {symbol} ({PERIOD})")
    plt.xlabel("Date")
    plt.ylabel("Price")
    
    # Add legend
    if bullish_levels:
        plt.plot([], [], 'go-', label='Bullish Breaker')
    if bearish_levels:
        plt.plot([], [], 'ro-', label='Bearish Breaker')
    
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save plot
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"breaker_blocks_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    plt.savefig(filename)
    plt.close()
    
    logger.info(f"Saved plot to {filename}")
    return filename

def run_test():
    """Run the breaker block detection test"""
    logger.info("=== BREAKER BLOCK DETECTION TEST ===")
    
    results = {}
    
    for symbol in SYMBOLS:
        # Get data
        data = get_stock_data(symbol)
        if data is None:
            continue
        
        # Detect breaker blocks
        breakers = detect_breaker_blocks(data, window=WINDOW)
        
        # Store results
        results[symbol] = {
            'data_length': len(data),
            'breaker_count': len(breakers),
            'bullish_count': len([b for b in breakers if b['type'] == 'bullish']),
            'bearish_count': len([b for b in breakers if b['type'] == 'bearish'])
        }
        
        # Plot if we found any breakers
        if breakers:
            logger.info(f"{symbol}: Found {len(breakers)} breaker blocks")
            plot_file = plot_data_with_breakers(data, breakers, symbol)
            results[symbol]['plot'] = plot_file
        else:
            logger.warning(f"{symbol}: No breaker blocks detected")
    
    # Print summary
    logger.info("=== TEST RESULTS SUMMARY ===")
    for symbol, result in results.items():
        logger.info(f"{symbol}: {result['breaker_count']} breakers ({result['bullish_count']} bullish, {result['bearish_count']} bearish)")
    
    logger.info("=== TEST COMPLETED ===")
    return results

if __name__ == "__main__":
    run_test()
