#!/usr/bin/env python3
"""
Sweep Engulfer Pattern Detection

This module implements the Sweep Engulfer pattern detection logic, which identifies
potential reversal setups where price sweeps a significant level and then engulfs
the previous candle, indicating a potential reversal.
"""
import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/sweep_engulfer_{time}.log", rotation="500 MB", level="DEBUG")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

class SweepEngulferPattern:
    """
    Detects Sweep Engulfer patterns in price data.
    
    A Sweep Engulfer pattern occurs when:
    1. Price sweeps (breaks) a significant high/low level of previous candle
    2. The candle then engulfs and closes beyond the BODY of the previous candle (not the wick)
    3. For bullish pattern: sweeps below previous low, then closes above previous body high
    4. For bearish pattern: sweeps above previous high, then closes below previous body low
    5. This often indicates a potential reversal in the market
    """
    
    def __init__(
        self,
        lookback_periods: int = 20,
        engulfing_threshold: float = 1.0,  # Minimum engulf ratio (body comparison)
        sweep_threshold_pips: float = 1,  # How far price needs to sweep beyond the level
        min_retracement: float = 0.33,  # Minimum retracement required (1/3 of candle)
    ):
        """Initialize the Sweep Engulfer pattern detector with configuration parameters."""
        self.lookback_periods = lookback_periods
        self.engulfing_threshold = engulfing_threshold
        self.sweep_threshold_pips = sweep_threshold_pips
        self.min_retracement = min_retracement
        logger.info(f"Initialized SweepEngulferPattern with lookback={lookback_periods}, "
                   f"engulfing_threshold={engulfing_threshold}, "
                   f"sweep_threshold_pips={sweep_threshold_pips}, "
                   f"min_retracement={min_retracement}")
    
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range (ATR) for the given data."""
        high = data['high'] if 'high' in data.columns else data['High']
        low = data['low'] if 'low' in data.columns else data['Low']
        close = data['close'] if 'close' in data.columns else data['Close']
        
        # Handle previous close for first calculation
        prev_close = close.shift(1)
        
        # Calculate true range
        tr1 = high - low  # Current high - current low
        tr2 = (high - prev_close).abs()  # Current high - previous close
        tr3 = (low - prev_close).abs()  # Current low - previous close
        
        # True Range is the maximum of the three
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def detect_patterns(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Detect sweep engulfer patterns in OHLCV data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with original data and additional columns indicating patterns
        """
        # Ensure we have enough data
        if len(data) < 3:
            return data
            
        # Create output DataFrame
        result = data.copy()
        result['bullish_sweep_engulfing'] = False
        result['bearish_sweep_engulfing'] = False
        result['engulf_ratio'] = np.nan
        result['sweep_size'] = np.nan
        
        # Calculate ATR for reference
        atr = self.calculate_atr(data)
        
        # Loop through candles starting from 3rd candle
        for i in range(2, len(data)):
            current_candle = data.iloc[i]
            prev_candle = data.iloc[i-1]
            
            # Calculate previous candle's body high and low
            prev_body_high = max(prev_candle['open'], prev_candle['close'])
            prev_body_low = min(prev_candle['open'], prev_candle['close'])
            
            # Bullish sweep engulfing check
            if (
                # Sweep below previous low
                current_candle['low'] < prev_candle['low'] and
                # Close above previous body high
                current_candle['close'] > prev_body_high and
                # Bullish candle
                current_candle['close'] > current_candle['open']
            ):
                # Calculate engulf ratio and sweep size
                candle_size = abs(current_candle['close'] - current_candle['low'])
                engulf_size = abs(current_candle['close'] - prev_body_low)
                engulf_ratio = engulf_size / abs(prev_body_high - prev_body_low) if abs(prev_body_high - prev_body_low) > 0 else 0
                sweep_size = abs(prev_candle['low'] - current_candle['low'])
                
                # Check if engulf ratio meets threshold
                if engulf_ratio >= self.engulfing_threshold and sweep_size > 0:
                    result.loc[result.index[i], 'bullish_sweep_engulfing'] = True
                    result.loc[result.index[i], 'engulf_ratio'] = engulf_ratio
                    result.loc[result.index[i], 'sweep_size'] = sweep_size
                    
            # Bearish sweep engulfing check
            elif (
                # Sweep above previous high
                current_candle['high'] > prev_candle['high'] and
                # Close below previous body low
                current_candle['close'] < prev_body_low and
                # Bearish candle
                current_candle['close'] < current_candle['open']
            ):
                # Calculate engulf ratio and sweep size
                candle_size = abs(current_candle['high'] - current_candle['close'])
                engulf_size = abs(prev_body_high - current_candle['close'])
                engulf_ratio = engulf_size / abs(prev_body_high - prev_body_low) if abs(prev_body_high - prev_body_low) > 0 else 0
                sweep_size = abs(current_candle['high'] - prev_candle['high'])
                
                # Check if engulf ratio meets threshold
                if engulf_ratio >= self.engulfing_threshold and sweep_size > 0:
                    result.loc[result.index[i], 'bearish_sweep_engulfing'] = True
                    result.loc[result.index[i], 'engulf_ratio'] = engulf_ratio
                    result.loc[result.index[i], 'sweep_size'] = sweep_size
        
        return result
    
    def check_retracement(self, data: pd.DataFrame, pattern_idx: int, direction: str) -> bool:
        """
        Check if price has retraced at least 1/3 of the sweep engulfing candle's range.
        
        Args:
            data: DataFrame with OHLCV data
            pattern_idx: Index of the pattern candle
            direction: 'bullish' or 'bearish'
            
        Returns:
            True if price has retraced sufficiently, False otherwise
        """
        # Ensure we have data after the pattern
        if pattern_idx >= len(data) - 1:
            return False
            
        pattern_candle = data.iloc[pattern_idx]
        
        # Calculate min retracement level
        if direction == 'bullish':
            candle_size = abs(pattern_candle['close'] - pattern_candle['low'])
            retracement_target = pattern_candle['close'] - (candle_size * self.min_retracement)
            
            # Check if price retraced to target
            for i in range(pattern_idx + 1, len(data)):
                if data.iloc[i]['low'] <= retracement_target:
                    return True
                    
        elif direction == 'bearish':
            candle_size = abs(pattern_candle['high'] - pattern_candle['close'])
            retracement_target = pattern_candle['close'] + (candle_size * self.min_retracement)
            
            # Check if price retraced to target
            for i in range(pattern_idx + 1, len(data)):
                if data.iloc[i]['high'] >= retracement_target:
                    return True
        
        return False

# Function to test the pattern detector
def test_sweep_engulfer_detector(symbol: str = "AAPL", timeframe: str = "1d", period: str = "1y"):
    """Test the Sweep Engulfer pattern detector with a single symbol."""
    import yfinance as yf
    
    # Fetch data
    logger.info(f"Fetching data for {symbol} on {timeframe} timeframe...")
    data = yf.download(symbol, period=period, interval=timeframe, progress=False)
    
    if data.empty:
        logger.error(f"No data available for {symbol}")
        return
    
    logger.info(f"Fetched {len(data)} data points for {symbol}")
    
    # Initialize detector
    detector = SweepEngulferPattern()
    
    # Detect patterns
    patterns = detector.detect_patterns(data)
    
    # Print results
    if patterns['bullish_sweep_engulfing'].any() or patterns['bearish_sweep_engulfing'].any():
        logger.info(f"Found Sweep Engulfer patterns in {symbol}:")
        for i, row in patterns.iterrows():
            if row['bullish_sweep_engulfing']:
                logger.info(f"Bullish Sweep Engulfer at {i}:")
                logger.info(f"  Engulf Ratio: {row['engulf_ratio']:.2f}")
                logger.info(f"  Sweep Size: {row['sweep_size']:.2f}")
            elif row['bearish_sweep_engulfing']:
                logger.info(f"Bearish Sweep Engulfer at {i}:")
                logger.info(f"  Engulf Ratio: {row['engulf_ratio']:.2f}")
                logger.info(f"  Sweep Size: {row['sweep_size']:.2f}")
    else:
        logger.info(f"No Sweep Engulfer patterns found in {symbol}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Sweep Engulfer pattern detector")
    parser.add_argument("--symbol", type=str, default="AAPL", help="Symbol to analyze")
    parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe to use")
    parser.add_argument("--period", type=str, default="1y", help="Period to fetch data for")
    
    args = parser.parse_args()
    
    test_sweep_engulfer_detector(args.symbol, args.timeframe, args.period) 