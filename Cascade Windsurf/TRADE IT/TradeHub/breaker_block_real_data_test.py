#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Breaker Block Detection - Real Historical Data Test
---------------------------------------------------

This script tests the breaker block detection logic using real historical data
from Yahoo Finance. It downloads data for specified symbols, processes it with
the breaker block detection algorithm, and visualizes the results.
"""

import os
import sys
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from scipy.signal import argrelextrema
from loguru import logger
import matplotlib.dates as mdates

# Configure logger with "nuclear" logging for detailed debugging
log_path = os.path.join("logs", f"breaker_block_real_test_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')}.log")
os.makedirs("logs", exist_ok=True)

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(log_path, level="DEBUG", rotation="500 MB", retention="10 days")
logger.info(f"Logging to {log_path}")

# Symbols to test - using a few with known volatility that might show breaker patterns
# Feel free to modify this list
TEST_SYMBOLS = [
    "AAPL",  # Apple
    "TSLA",  # Tesla
    "SPY",   # S&P 500 ETF
    "BTC-USD" # Bitcoin
]

def fetch_historical_data(symbol, period="3mo", interval="1d"):
    """
    Fetch historical price data from Yahoo Finance
    
    Args:
        symbol (str): Stock symbol
        period (str): Time period to fetch (default: 3 months)
        interval (str): Candle interval (default: daily)
        
    Returns:
        pandas.DataFrame: Price data with OHLCV columns
    """
    logger.info(f"Fetching historical data for {symbol} ({period}, {interval})")
    
    try:
        # Download data from Yahoo Finance
        data = yf.download(symbol, period=period, interval=interval, progress=False)
        
        # Format the data to match our expected structure
        df = pd.DataFrame({
            'timestamp': data.index,
            'open': data['Open'].values,
            'high': data['High'].values,
            'low': data['Low'].values,
            'close': data['Close'].values,
            'volume': data['Volume'].values.astype(float)  # Convert to 1D float array
        })
        
        logger.info(f"Successfully downloaded {len(df)} candles for {symbol}")
        return df
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None

def detect_breaker_blocks(df, direction="both", window=10, threshold=0.6, retest_window=10):
    """
    Implementation of breaker block detection algorithm for real market data.
    
    Args:
        df (pandas.DataFrame): Price data with OHLCV columns
        direction (str): 'bullish', 'bearish', or 'both'
        window (int): Window size for extrema detection
        threshold (float): Confidence threshold
        retest_window (int): Window to look for retests
        
    Returns:
        list: Detected breaker blocks
    """
    logger.info(f"Detecting {direction} breaker blocks with window={window}")
    
    # Copy the dataframe to avoid modifying the original
    df = df.copy()
    
    # Make sure timestamp is a datetime index
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
    
    # Find local extrema using argrelextrema
    # For local maxima (resistance levels)
    max_idx = argrelextrema(df['high'].values, np.greater_equal, order=window)[0]
    df['is_max'] = False
    df.iloc[max_idx, df.columns.get_indexer(['is_max'])] = True
    
    # For local minima (support levels)
    min_idx = argrelextrema(df['low'].values, np.less_equal, order=window)[0]
    df['is_min'] = False
    df.iloc[min_idx, df.columns.get_indexer(['is_min'])] = True
    
    # Identify support and resistance levels
    support_levels = df[df['is_min']]['low'].tolist()
    resistance_levels = df[df['is_max']]['high'].tolist()
    
    support_indices = df[df['is_min']].index.tolist()
    resistance_indices = df[df['is_max']].index.tolist()
    
    logger.info(f"Found {len(support_levels)} support levels and {len(resistance_levels)} resistance levels")
    
    # Find price levels that were broken
    broken_supports = []
    broken_support_indices = []
    broken_resistances = []
    broken_resistance_indices = []
    
    # Threshold for considering a level as broken (as percentage of the level)
    break_threshold = 0.002  # 0.2%
    retest_threshold = 0.01  # 1%
    
    # Break the data into chunks to find breaks and retests
    for i, level_idx in enumerate(support_indices):
        level = support_levels[i]
        level_date = support_indices[i]
        
        # Only look at levels from the first 2/3 of the data (to give time for break and retest)
        if level_date > df.index[int(len(df) * 2/3)]:
            continue
            
        # Get data after this level was established
        after_level = df.loc[level_date:].copy()
        
        if len(after_level) < 5:  # Skip if not enough data after this level
            continue
            
        # Check if price broke below this support
        breaks = after_level[after_level['close'] < level * (1 - break_threshold)]
        
        if len(breaks) > 0:
            # Find first instance of break
            first_break = breaks.iloc[0]
            break_date = breaks.index[0]
            
            # Get data after the break to look for retests
            after_break = df.loc[break_date:].copy()
            
            # Look for a retest (price came back to the level from below)
            # We look for cases where price approaches the level but doesn't necessarily exceed it
            retests = after_break[
                (after_break['high'] > level * (1 - retest_threshold)) & 
                (after_break['high'] < level * (1 + retest_threshold))
            ]
            
            if len(retests) > 0:
                # We found a broken support that was retested = bullish breaker block
                broken_supports.append(level)
                broken_support_indices.append(level_date)
                logger.debug(f"Found bullish breaker at {level:.2f} on {level_date}")
    
    # Do the same for resistance levels
    for i, level_idx in enumerate(resistance_indices):
        level = resistance_levels[i]
        level_date = resistance_indices[i]
        
        # Only look at levels from the first 2/3 of the data
        if level_date > df.index[int(len(df) * 2/3)]:
            continue
            
        # Get data after this level was established
        after_level = df.loc[level_date:].copy()
        
        if len(after_level) < 5:  # Skip if not enough data after this level
            continue
            
        # Check if price broke above this resistance
        breaks = after_level[after_level['close'] > level * (1 + break_threshold)]
        
        if len(breaks) > 0:
            # Find first instance of break
            first_break = breaks.iloc[0]
            break_date = breaks.index[0]
            
            # Get data after the break to look for retests
            after_break = df.loc[break_date:].copy()
            
            # Look for a retest (price came back to the level from above)
            retests = after_break[
                (after_break['low'] < level * (1 + retest_threshold)) & 
                (after_break['low'] > level * (1 - retest_threshold))
            ]
            
            if len(retests) > 0:
                # We found a broken resistance that was retested = bearish breaker block
                broken_resistances.append(level)
                broken_resistance_indices.append(level_date)
                logger.debug(f"Found bearish breaker at {level:.2f} on {level_date}")
    
    # Combine results based on requested direction
    breaker_blocks = []
    
    if direction in ["bullish", "both"]:
        for i, level in enumerate(broken_supports):
            level_date = broken_support_indices[i]
            breaker_blocks.append({
                "price": level,
                "date": level_date,
                "confidence": min(1.0, 0.6 + i * 0.1),  # Simple confidence calculation
                "direction": "bullish"
            })
    
    if direction in ["bearish", "both"]:
        for i, level in enumerate(broken_resistances):
            level_date = broken_resistance_indices[i]
            breaker_blocks.append({
                "price": level,
                "date": level_date,
                "confidence": min(1.0, 0.6 + i * 0.1),
                "direction": "bearish"
            })
    
    logger.info(f"Detected {len(breaker_blocks)} breaker blocks " +
                f"({len([b for b in breaker_blocks if b['direction'] == 'bullish'])} bullish, " +
                f"{len([b for b in breaker_blocks if b['direction'] == 'bearish'])} bearish)")
    return breaker_blocks

def plot_results(df, breaker_blocks, symbol, filename=None):
    """
    Plot price data with detected breaker blocks
    
    Args:
        df (pandas.DataFrame): Price data
        breaker_blocks (list): Detected breaker blocks
        symbol (str): Symbol being plotted
        filename (str, optional): File to save the plot to
    """
    # Create a figure with 1 row, 1 column
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Plot candlestick chart
    width = 0.6
    width2 = 0.05
    
    up = df[df.close >= df.open]
    down = df[df.close < df.open]
    
    # Plot bullish and bearish candles
    ax.bar(up.index, up.close-up.open, width, bottom=up.open, color='green', alpha=0.5)
    ax.bar(up.index, up.high-up.close, width2, bottom=up.close, color='green', alpha=0.8)
    ax.bar(up.index, up.low-up.open, width2, bottom=up.open, color='green', alpha=0.8)
    
    ax.bar(down.index, down.close-down.open, width, bottom=down.open, color='red', alpha=0.5)
    ax.bar(down.index, down.high-down.open, width2, bottom=down.open, color='red', alpha=0.8)
    ax.bar(down.index, down.low-down.close, width2, bottom=down.close, color='red', alpha=0.8)
    
    # Highlight breaker blocks
    for block in breaker_blocks:
        color = 'green' if block['direction'] == 'bullish' else 'red'
        linestyle = '--' if block['direction'] == 'bullish' else '-.'
        price = block['price']
        date = block['date']
        
        # Draw a horizontal line at the price level
        ax.axhline(y=price, color=color, linestyle=linestyle, alpha=0.7, 
                  label=f"{block['direction'].capitalize()} Breaker ({price:.2f})")
        
        # Mark the point where the level was established
        ax.plot(date, price, 'o', color=color, markersize=8)
    
    # Set title and labels
    ax.set_title(f"Breaker Block Detection for {symbol}", fontsize=16)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Price", fontsize=12)
    
    # Format x-axis to show readable dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    # Add a legend (only show one entry per direction)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='best')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the figure if filename is provided
    if filename:
        plt.savefig(filename)
        logger.info(f"Saved plot to {filename}")
    
    # Show the plot
    plt.close()

def run_real_data_test():
    """Run the breaker block detection test on real market data"""
    logger.info("=== REAL DATA BREAKER BLOCK DETECTION TEST ===")
    
    # Test for each symbol
    for symbol in TEST_SYMBOLS:
        # Fetch historical data
        df = fetch_historical_data(symbol, period="1y", interval="1d")
        
        if df is None or len(df) < 50:
            logger.warning(f"Insufficient data for {symbol}, skipping")
            continue
        
        # Detect breaker blocks (both bullish and bearish)
        breaker_blocks = detect_breaker_blocks(df, direction="both", window=10)
        
        # Check results
        if len(breaker_blocks) > 0:
            logger.info(f" {symbol} TEST PASSED: Found {len(breaker_blocks)} breaker blocks")
            # Plot the results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"breaker_block_{symbol}_test_{timestamp}.png"
            plot_results(df, breaker_blocks, symbol, filename)
        else:
            logger.warning(f" {symbol} TEST: No breaker blocks detected")
    
    logger.info("=== TEST COMPLETED ===")
    logger.info(f"Full test logs available in: {log_path}")

if __name__ == "__main__":
    run_real_data_test()
