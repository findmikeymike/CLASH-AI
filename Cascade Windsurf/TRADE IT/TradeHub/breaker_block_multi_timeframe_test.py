#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Multi-Timeframe Breaker Block Detection Test
-------------------------------------------

Tests breaker block detection across multiple timeframes to estimate the
total number of setups that would be found over a year period.
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
log_path = os.path.join(log_dir, f"multi_tf_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(log_path, level="DEBUG")
logger.info(f"Logging to {log_path}")

# Test parameters
SYMBOL = "AAPL"  # We'll use Apple for this test
TIMEFRAMES = {
    "1h": "1h",    # 1 hour
    "4h": "4h",    # 4 hours (close to)
    "1d": "1d"     # 1 day
}

# Note: Yahoo Finance doesn't offer 15min and 30min data for periods longer than 60 days
# so we're using 1h, 4h and 1d for this test

WINDOW_SIZES = {
    "1h": 20,     # For hourly, use a larger window
    "4h": 15,     # For 4-hour
    "1d": 10      # For daily
}

def get_stock_data(symbol, timeframe, period="1y"):
    """Get stock data from Yahoo Finance for the given timeframe"""
    logger.info(f"Downloading {period} {timeframe} data for {symbol}")
    
    # For intraday data, we might need to adjust the period
    if timeframe == "1h":
        # Yahoo only provides 60 days of hourly data
        period = "60d"
    
    try:
        data = yf.download(symbol, period=period, interval=timeframe, progress=False)
        if len(data) > 30:  # Ensure we have enough data
            logger.info(f"Downloaded {len(data)} {timeframe} data points for {symbol}")
            return data
        else:
            logger.warning(f"Insufficient {timeframe} data points ({len(data)}) for {symbol}")
            return None
    except Exception as e:
        logger.error(f"Error downloading {symbol} {timeframe} data: {e}")
        return None

def detect_breaker_blocks(df, timeframe, window=10):
    """Detect breaker blocks in the data"""
    # Use window size appropriate for the timeframe
    window = WINDOW_SIZES.get(timeframe, window)
    
    logger.info(f"Detecting breaker blocks with {timeframe} data using window={window}")
    
    # Copy dataframe
    df = df.copy()
    
    # Find extrema
    max_idx = argrelextrema(df['High'].values, np.greater_equal, order=window)[0]
    min_idx = argrelextrema(df['Low'].values, np.less_equal, order=window)[0]
    
    # Adjust thresholds based on timeframe - shorter timeframes need tighter thresholds
    break_threshold_map = {"1h": 0.001, "4h": 0.0015, "1d": 0.002}
    retest_threshold_map = {"1h": 0.005, "4h": 0.008, "1d": 0.01}
    
    break_threshold = break_threshold_map.get(timeframe, 0.002)  # Default to daily
    retest_threshold = retest_threshold_map.get(timeframe, 0.01)  # Default to daily
    
    breakers = []
    
    # Process identified extrema - bullish breakers
    for idx in min_idx:
        if idx < len(df) - window:
            support_level = float(df['Low'].iloc[idx])
            
            # Check if level was broken
            future_data = df.iloc[idx:idx+window]
            if any(future_data['Close'] < support_level * (1 - break_threshold)):
                
                # Check if price returned to test the level
                test_data = df.iloc[idx+window:]
                if len(test_data) > 0 and any(abs(test_data['Close'] - support_level) / support_level < retest_threshold):
                    breakers.append({
                        'type': 'bullish',
                        'price': support_level,
                        'date': df.index[idx],
                        'confidence': 0.8
                    })
                    logger.debug(f"Found bullish breaker at {float(support_level):.2f} on {df.index[idx]}")
    
    # Process identified extrema - bearish breakers
    for idx in max_idx:
        if idx < len(df) - window:
            resistance_level = float(df['High'].iloc[idx])
            
            # Check if level was broken
            future_data = df.iloc[idx:idx+window]
            if any(future_data['Close'] > resistance_level * (1 + break_threshold)):
                
                # Check if price returned to test the level
                test_data = df.iloc[idx+window:]
                if len(test_data) > 0 and any(abs(test_data['Close'] - resistance_level) / resistance_level < retest_threshold):
                    breakers.append({
                        'type': 'bearish',
                        'price': resistance_level,
                        'date': df.index[idx],
                        'confidence': 0.8
                    })
                    logger.debug(f"Found bearish breaker at {float(resistance_level):.2f} on {df.index[idx]}")
    
    return breakers

def run_multi_timeframe_test():
    """Run breaker block detection across multiple timeframes"""
    logger.info(f"=== MULTI-TIMEFRAME BREAKER BLOCK TEST FOR {SYMBOL} ===")
    
    results = {}
    total_setups = 0
    
    # Test each timeframe
    for tf_name, tf_value in TIMEFRAMES.items():
        data = get_stock_data(SYMBOL, tf_value)
        
        if data is None:
            continue
            
        # Detect breaker blocks
        breakers = detect_breaker_blocks(data, tf_name)
        
        # Calculate expected annual count
        # For timeframes less than daily, we need to extrapolate to full year
        multiplier = 1
        if tf_name == "1h":
            # Downloaded 60 days of hourly data, extrapolate to 252 trading days
            multiplier = 252 / 60
        
        estimated_annual = int(len(breakers) * multiplier)
        
        # Store results
        results[tf_name] = {
            'data_points': len(data),
            'breaker_count': len(breakers),
            'bullish_count': len([b for b in breakers if b['type'] == 'bullish']),
            'bearish_count': len([b for b in breakers if b['type'] == 'bearish']),
            'estimated_annual': estimated_annual
        }
        
        total_setups += estimated_annual
        
        # Log results
        logger.info(f"{tf_name}: Found {len(breakers)} breaker blocks in {len(data)} candles")
        logger.info(f"{tf_name}: Estimated {estimated_annual} breaker blocks annually")
    
    # Print summary
    logger.info("=== TEST RESULTS SUMMARY ===")
    for tf_name, result in results.items():
        logger.info(f"{tf_name}: {result['breaker_count']} breakers ({result['bullish_count']} bullish, {result['bearish_count']} bearish) - Est. Annual: {result['estimated_annual']}")
    
    logger.info(f"Total estimated annual breaker blocks across all timeframes: {total_setups}")
    logger.info("=== TEST COMPLETED ===")
    
    return results

if __name__ == "__main__":
    run_multi_timeframe_test()
