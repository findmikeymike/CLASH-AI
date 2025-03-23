#!/usr/bin/env python3
"""
Setup Scanner Workflow Without Prefect

This script implements the same functionality as the setup scanner workflow
but without any dependency on Prefect, making it more reliable when Prefect
versions change.
"""
import os
import sys
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
import pandas as pd
import yfinance as yf
from loguru import logger
import numpy as np
import json
from sweep_engulfer_agent import SweepEngulferPattern

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/scanner_{time}.log", rotation="500 MB", level="DEBUG")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

class SimpleScanner:
    """A simplified scanner that finds breaker blocks and fair value gaps."""
    
    def __init__(
        self, 
        lookback_periods: int = 50,
        min_volume_threshold: int = 10000,
        price_rejection_threshold: float = 0.005,
        fvg_threshold: float = 0.003,
        min_touches: int = 2,  # Minimum touches to consider a level significant
        retest_threshold: float = 0.005,  # 0.5% threshold for retest
        retracement_threshold: float = 0.33  # 33% retracement threshold for sweep engulfer
    ):
        """Initialize the scanner with configuration parameters."""
        self.lookback_periods = lookback_periods
        self.min_volume_threshold = min_volume_threshold
        self.price_rejection_threshold = price_rejection_threshold
        self.fvg_threshold = fvg_threshold
        self.min_touches = min_touches
        self.retest_threshold = retest_threshold
        self.retracement_threshold = retracement_threshold
        self.support_resistance = {}  # Dictionary to store support/resistance levels by symbol and timeframe
        self.breaker_blocks = {}  # Dictionary to store breaker blocks by symbol and timeframe
        # Initialize the Sweep Engulfer pattern detector
        self.sweep_engulfer = SweepEngulferPattern(
            lookback_periods=lookback_periods,
            engulfing_threshold=0.0,
            volume_increase_threshold=1.5,
            sweep_threshold_pips=5,
            min_candle_size_atr=0.5
        )
        logger.info(f"Initialized SimpleScanner with lookback={lookback_periods}, "
                   f"min_volume={min_volume_threshold}, price_rejection={price_rejection_threshold}, "
                   f"fvg_threshold={fvg_threshold}, min_touches={min_touches}")
    
    def find_breaker_blocks(self, data: pd.DataFrame, symbol: str = "UNKNOWN", timeframe: str = "1D") -> List[Dict[str, Any]]:
        """
        Find breaker blocks in the data using the exact BreakerBlockAgent logic.
        
        A breaker block is a price structure where:
        1. A support or resistance level is broken
        2. Price moves away from the level
        3. Price returns to test the level from the opposite side
        """
        logger.info(f"Scanning for breaker blocks in data with {len(data)} rows")
        
        if len(data) < self.lookback_periods + 10:
            logger.warning(f"Not enough data points to find breaker blocks (need at least {self.lookback_periods + 10})")
            return []
        
        # Make sure we have the required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        # Handle the case where columns are tuples (multi-index columns)
        column_list = []
        for col in data.columns:
            if isinstance(col, tuple):
                column_list.append(col[0].lower())
            else:
                column_list.append(str(col).lower())
        
        # Check if all required columns are present
        if not all(col in column_list for col in required_columns):
            available_cols = ', '.join([str(col) for col in data.columns])
            logger.error(f"Missing required columns for breaker block analysis. Available: {available_cols}")
            return []
        
        # Get the lookback data
        lookback_data = data.iloc[-self.lookback_periods:]
        
        # Ensure we have the right column names
        # If columns are tuples, extract the first element
        if isinstance(data.columns[0], tuple):
            # Create a mapping from lowercase column name to actual column
            col_mapping = {}
            for col in data.columns:
                col_mapping[col[0].lower()] = col
            
            # Use the mapping to access the right columns
            high_col = col_mapping.get('high')
            low_col = col_mapping.get('low')
            close_col = col_mapping.get('close')
            open_col = col_mapping.get('open')
            volume_col = col_mapping.get('volume')
        else:
            # Create a mapping from lowercase column name to actual column
            col_mapping = {}
            for col in data.columns:
                col_mapping[str(col).lower()] = col
            
            # Use the mapping to access the right columns
            high_col = col_mapping.get('high')
            low_col = col_mapping.get('low')
            close_col = col_mapping.get('close')
            open_col = col_mapping.get('open')
            volume_col = col_mapping.get('volume')
        
        # Create a new DataFrame with standardized column names
        std_data = pd.DataFrame()
        std_data['open'] = lookback_data[open_col]
        std_data['high'] = lookback_data[high_col]
        std_data['low'] = lookback_data[low_col]
        std_data['close'] = lookback_data[close_col]
        std_data['volume'] = lookback_data[volume_col]
        std_data.index = lookback_data.index
        
        # Step 1: Identify support and resistance levels
        support_resistance_levels = self._identify_support_resistance(std_data)
        
        # Step 2: Update stored support/resistance levels
        key = f"{symbol}_{timeframe}"
        if key not in self.support_resistance:
            self.support_resistance[key] = []
        
        # Merge new levels with existing levels
        for new_level in support_resistance_levels:
            merged = False
            for i, existing_level in enumerate(self.support_resistance[key]):
                if (existing_level["type"] == new_level["type"] and 
                    abs(existing_level["price"] - new_level["price"]) / new_level["price"] < 0.005):
                    # Merge levels
                    self.support_resistance[key][i]["touches"] = max(existing_level["touches"], new_level["touches"])
                    self.support_resistance[key][i]["strength"] = max(existing_level["strength"], new_level["strength"])
                    merged = True
                    break
            
            if not merged:
                self.support_resistance[key].append(new_level)
        
        # Step 3: Identify breaker blocks
        new_breaker_blocks = self._identify_breaker_blocks(std_data, symbol, timeframe)
        
        # Step 4: Update stored breaker blocks
        if key not in self.breaker_blocks:
            self.breaker_blocks[key] = []
        
        # Add new breaker blocks
        self.breaker_blocks[key].extend(new_breaker_blocks)
        
        # Step 5: Identify retests of breaker blocks
        active_retests = self._identify_retests(std_data, symbol, timeframe)
        
        logger.info(f"Found {len(new_breaker_blocks)} new breaker blocks and {len(active_retests)} active retests")
        
        # Return active retests as these are the actionable breaker blocks
        return active_retests
    
    def _identify_support_resistance(self, ohlc_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Identify support and resistance levels from price data.
        
        This method uses swing highs and lows to identify potential
        support and resistance levels.
        """
        support_resistance = []
        
        # Get high and low prices
        highs = ohlc_data["high"].values
        lows = ohlc_data["low"].values
        
        # Window size for detecting swing points
        window = 5
        
        # Detect swing highs (resistance)
        for i in range(window, len(highs) - window):
            # Check if this is a local maximum
            if highs[i] == max(highs[i-window:i+window+1]):
                # Calculate strength based on how much higher it is than surrounding bars
                height_diff = np.mean([highs[i] - highs[i-j] for j in range(1, window+1)] + 
                                     [highs[i] - highs[i+j] for j in range(1, window+1)])
                strength = min(1.0, height_diff / (highs[i] * 0.01))  # Normalize to 0-1
                
                # Create resistance level
                level = {
                    "price": float(highs[i]),
                    "type": "resistance",
                    "strength": float(strength),
                    "timeframe": "1D",  # Default timeframe
                    "created_at": ohlc_data.index[i].strftime('%Y-%m-%d %H:%M:%S') if hasattr(ohlc_data.index[i], 'strftime') else str(ohlc_data.index[i]),
                    "broken_at": None,
                    "touches": 1
                }
                
                # Check for similar levels and merge if found
                merged = False
                for j, existing_level in enumerate(support_resistance):
                    if (existing_level["type"] == "resistance" and 
                        abs(existing_level["price"] - level["price"]) / level["price"] < 0.005):
                        # Merge levels
                        support_resistance[j]["touches"] += 1
                        support_resistance[j]["strength"] = max(existing_level["strength"], strength)
                        merged = True
                        break
                
                if not merged:
                    support_resistance.append(level)
        
        # Detect swing lows (support)
        for i in range(window, len(lows) - window):
            # Check if this is a local minimum
            if lows[i] == min(lows[i-window:i+window+1]):
                # Calculate strength based on how much lower it is than surrounding bars
                depth_diff = np.mean([lows[i-j] - lows[i] for j in range(1, window+1)] + 
                                    [lows[i+j] - lows[i] for j in range(1, window+1)])
                strength = min(1.0, depth_diff / (lows[i] * 0.01))  # Normalize to 0-1
                
                # Create support level
                level = {
                    "price": float(lows[i]),
                    "type": "support",
                    "strength": float(strength),
                    "timeframe": "1D",  # Default timeframe
                    "created_at": ohlc_data.index[i].strftime('%Y-%m-%d %H:%M:%S') if hasattr(ohlc_data.index[i], 'strftime') else str(ohlc_data.index[i]),
                    "broken_at": None,
                    "touches": 1
                }
                
                # Check for similar levels and merge if found
                merged = False
                for j, existing_level in enumerate(support_resistance):
                    if (existing_level["type"] == "support" and 
                        abs(existing_level["price"] - level["price"]) / level["price"] < 0.005):
                        # Merge levels
                        support_resistance[j]["touches"] += 1
                        support_resistance[j]["strength"] = max(existing_level["strength"], strength)
                        merged = True
                        break
                
                if not merged:
                    support_resistance.append(level)
        
        # Filter out weak levels
        support_resistance = [level for level in support_resistance if level["touches"] >= self.min_touches]
        
        return support_resistance
    
    def _identify_breaker_blocks(self, data: pd.DataFrame, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """
        Identify breaker blocks from price data.
        
        This method detects when support/resistance levels are broken,
        creating potential breaker blocks.
        """
        breaker_blocks = []
        key = f"{symbol}_{timeframe}"
        
        if key not in self.support_resistance:
            return breaker_blocks
        
        # Get current price data
        current_price = data["close"].iloc[-1]
        current_time = data.index[-1]
        
        # Check for broken support/resistance levels
        for level in self.support_resistance[key]:
            if level.get("broken_at") is None:
                if level["type"] == "support" and current_price < level["price"] * 0.99:
                    # Support broken, create bearish breaker block
                    level["broken_at"] = current_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(current_time, 'strftime') else str(current_time)
                    
                    # Calculate breaker block boundaries
                    # For a broken support, the breaker block is from the support level to a bit above it
                    high = level["price"] * 1.005
                    low = level["price"] * 0.995
                    
                    breaker_block = {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "high": float(high),
                        "low": float(low),
                        "direction": "bearish",
                        "strength": float(level["strength"] * (level["touches"] / self.min_touches)),
                        "created_at": current_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(current_time, 'strftime') else str(current_time),
                        "broken_at": None,
                        "retested": False,
                        "retest_time": None,
                        "retest_price": None,
                        "confluence_count": 0,
                        "notes": f"Broken support at {level['price']:.2f}"
                    }
                    
                    breaker_blocks.append(breaker_block)
                
                elif level["type"] == "resistance" and current_price > level["price"] * 1.01:
                    # Resistance broken, create bullish breaker block
                    level["broken_at"] = current_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(current_time, 'strftime') else str(current_time)
                    
                    # Calculate breaker block boundaries
                    # For a broken resistance, the breaker block is from the resistance level to a bit below it
                    high = level["price"] * 1.005
                    low = level["price"] * 0.995
                    
                    breaker_block = {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "high": float(high),
                        "low": float(low),
                        "direction": "bullish",
                        "strength": float(level["strength"] * (level["touches"] / self.min_touches)),
                        "created_at": current_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(current_time, 'strftime') else str(current_time),
                        "broken_at": None,
                        "retested": False,
                        "retest_time": None,
                        "retest_price": None,
                        "confluence_count": 0,
                        "notes": f"Broken resistance at {level['price']:.2f}"
                    }
                    
                    breaker_blocks.append(breaker_block)
        
        return breaker_blocks
    
    def _identify_retests(self, data: pd.DataFrame, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """
        Identify retests of breaker blocks.
        
        This method detects when price returns to test a breaker block.
        """
        active_retests = []
        key = f"{symbol}_{timeframe}"
        
        if key not in self.breaker_blocks:
            return active_retests
        
        # Get current price data
        current_price = data["close"].iloc[-1]
        current_time = data.index[-1]
        
        # Check for retests of breaker blocks
        for i, block in enumerate(self.breaker_blocks[key]):
            if not block.get("retested", False):
                # Check if price is retesting the breaker block
                if block["low"] <= current_price <= block["high"]:
                    # Price is within the breaker block, this is a retest
                    self.breaker_blocks[key][i]["retested"] = True
                    self.breaker_blocks[key][i]["retest_time"] = current_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(current_time, 'strftime') else str(current_time)
                    self.breaker_blocks[key][i]["retest_price"] = float(current_price)
                    
                    active_retests.append(self.breaker_blocks[key][i])
                
                # Check if price is approaching the breaker block
                elif (block["direction"] == "bullish" and 
                      block["low"] - current_price < current_price * self.retest_threshold and
                      block["low"] > current_price):
                    # Price is approaching a bullish breaker block from below
                    active_retests.append(self.breaker_blocks[key][i])
                
                elif (block["direction"] == "bearish" and 
                      current_price - block["high"] < current_price * self.retest_threshold and
                      block["high"] < current_price):
                    # Price is approaching a bearish breaker block from above
                    active_retests.append(self.breaker_blocks[key][i])
        
        return active_retests
    
    def find_fair_value_gaps(self, data: pd.DataFrame, symbol: str = "UNKNOWN", timeframe: str = "1D") -> List[Dict[str, Any]]:
        """
        Find fair value gaps in the data.
        
        A fair value gap (FVG) is a gap in price where:
        1. There's a strong move in one direction
        2. The move leaves a gap in price that hasn't been filled
        3. This gap represents a potential area for price to return to
        """
        logger.info(f"Scanning for fair value gaps in data with {len(data)} rows")
        
        if len(data) < self.lookback_periods + 10:
            logger.warning(f"Not enough data points to find fair value gaps (need at least {self.lookback_periods + 10})")
            return []
        
        # Make sure we have the required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        # Handle the case where columns are tuples (multi-index columns)
        column_list = []
        for col in data.columns:
            if isinstance(col, tuple):
                column_list.append(col[0].lower())
            else:
                column_list.append(str(col).lower())
        
        # Check if all required columns are present
        if not all(col in column_list for col in required_columns):
            available_cols = ', '.join([str(col) for col in data.columns])
            logger.error(f"Missing required columns for fair value gap analysis. Available: {available_cols}")
            return []
        
        # Get the lookback data
        lookback_data = data.iloc[-self.lookback_periods:]
        
        # Ensure we have the right column names
        # If columns are tuples, extract the first element
        if isinstance(data.columns[0], tuple):
            # Create a mapping from lowercase column name to actual column
            col_mapping = {}
            for col in data.columns:
                col_mapping[col[0].lower()] = col
            
            # Use the mapping to access the right columns
            high_col = col_mapping.get('high')
            low_col = col_mapping.get('low')
            close_col = col_mapping.get('close')
            open_col = col_mapping.get('open')
            volume_col = col_mapping.get('volume')
        else:
            # Create a mapping from lowercase column name to actual column
            col_mapping = {}
            for col in data.columns:
                col_mapping[str(col).lower()] = col
            
            # Use the mapping to access the right columns
            high_col = col_mapping.get('high')
            low_col = col_mapping.get('low')
            close_col = col_mapping.get('close')
            open_col = col_mapping.get('open')
            volume_col = col_mapping.get('volume')
        
        # Create a new DataFrame with standardized column names
        std_data = pd.DataFrame()
        std_data['open'] = lookback_data[open_col]
        std_data['high'] = lookback_data[high_col]
        std_data['low'] = lookback_data[low_col]
        std_data['close'] = lookback_data[close_col]
        std_data['volume'] = lookback_data[volume_col]
        std_data.index = lookback_data.index
        
        fair_value_gaps = []
        
        # Calculate daily ranges and average range
        std_data['range'] = std_data['high'] - std_data['low']
        avg_range = std_data['range'].mean()
        
        # Calculate price changes
        std_data['price_change'] = std_data['close'].diff()
        std_data['pct_change'] = std_data['close'].pct_change()
        
        # Look for bullish FVGs (price moves up leaving a gap)
        for i in range(2, len(std_data)):
            # Check for a bullish move (current candle closes higher than previous)
            if std_data['close'].iloc[i] > std_data['close'].iloc[i-1]:
                # Check if there's a gap between the current candle's low and the previous candle's high
                if std_data['low'].iloc[i] > std_data['high'].iloc[i-1]:
                    # We found a bullish FVG
                    gap_size = std_data['low'].iloc[i] - std_data['high'].iloc[i-1]
                    
                    # Only consider significant gaps
                    if gap_size > avg_range * self.fvg_threshold:
                        # Check if the gap has been filled
                        filled = False
                        for j in range(i+1, len(std_data)):
                            if std_data['low'].iloc[j] <= std_data['high'].iloc[i-1]:
                                filled = True
                                break
                        
                        if not filled:
                            fvg = {
                                'type': 'fair_value_gap',
                                'direction': 'bullish',
                                'symbol': symbol,
                                'timeframe': timeframe,
                                'high': float(std_data['low'].iloc[i]),
                                'low': float(std_data['high'].iloc[i-1]),
                                'size': float(gap_size),
                                'created_at': std_data.index[i].strftime('%Y-%m-%d') if hasattr(std_data.index[i], 'strftime') else str(std_data.index[i]),
                                'filled': False,
                                'strength': float(gap_size / avg_range)
                            }
                            fair_value_gaps.append(fvg)
        
        # Look for bearish FVGs (price moves down leaving a gap)
        for i in range(2, len(std_data)):
            # Check for a bearish move (current candle closes lower than previous)
            if std_data['close'].iloc[i] < std_data['close'].iloc[i-1]:
                # Check if there's a gap between the current candle's high and the previous candle's low
                if std_data['high'].iloc[i] < std_data['low'].iloc[i-1]:
                    # We found a bearish FVG
                    gap_size = std_data['low'].iloc[i-1] - std_data['high'].iloc[i]
                    
                    # Only consider significant gaps
                    if gap_size > avg_range * self.fvg_threshold:
                        # Check if the gap has been filled
                        filled = False
                        for j in range(i+1, len(std_data)):
                            if std_data['high'].iloc[j] >= std_data['low'].iloc[i-1]:
                                filled = True
                                break
                        
                        if not filled:
                            fvg = {
                                'type': 'fair_value_gap',
                                'direction': 'bearish',
                                'symbol': symbol,
                                'timeframe': timeframe,
                                'high': float(std_data['low'].iloc[i-1]),
                                'low': float(std_data['high'].iloc[i]),
                                'size': float(gap_size),
                                'created_at': std_data.index[i].strftime('%Y-%m-%d') if hasattr(std_data.index[i], 'strftime') else str(std_data.index[i]),
                                'filled': False,
                                'strength': float(gap_size / avg_range)
                            }
                            fair_value_gaps.append(fvg)
        
        logger.info(f"Found {len(fair_value_gaps)} fair value gaps")
        return fair_value_gaps

    def find_sweep_engulfers(self, data: pd.DataFrame, symbol: str = "UNKNOWN", timeframe: str = "1D") -> List[Dict[str, Any]]:
        """
        Find Sweep Engulfer patterns in the data.
        
        A Sweep Engulfer is a pattern where price sweeps a significant level and then engulfs the previous candle,
        indicating a potential reversal.
        """
        logger.info(f"Scanning for Sweep Engulfer patterns in {symbol} ({timeframe}) data with {len(data)} rows")
        
        if len(data) < self.lookback_periods + 10:
            logger.warning(f"Not enough data points to find Sweep Engulfer patterns (need at least {self.lookback_periods + 10})")
            return []
        
        # Use the SweepEngulferPattern detector to find patterns
        patterns = self.sweep_engulfer.detect_sweep_engulfer(data, symbol, timeframe)
        
        if patterns:
            logger.info(f"Found {len(patterns)} Sweep Engulfer patterns in {symbol} ({timeframe})")
            for pattern in patterns:
                logger.info(f"  {pattern['direction'].capitalize()} Sweep Engulfer at {pattern['timestamp']} - Price: {pattern['price_level']:.2f}")
        else:
            logger.info(f"No Sweep Engulfer patterns found in {symbol} ({timeframe})")
        
        return patterns

    def find_sweeping_engulfers(self, data: pd.DataFrame, symbol: str = "UNKNOWN", timeframe: str = "1D") -> List[Dict[str, Any]]:
        """
        Find Sweeping Engulfer patterns in the data.
        
        A Sweeping Engulfer pattern occurs when:
        1. Price sweeps (breaks) below the previous candle's low (bullish) or above the previous candle's high (bearish)
        2. The candle then engulfs the previous candle's body
        3. The next candle shows a retracement of at least the specified threshold
        """
        logger.info(f"Scanning for Sweeping Engulfer patterns in {symbol} ({timeframe}) data with {len(data)} rows")
        
        if len(data) < 3:  # Need at least 3 candles (previous, current, and next)
            logger.warning(f"Not enough data points to find Sweeping Engulfer patterns (need at least 3)")
            return []
        
        # Make sure we have the required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        # Handle the case where columns are tuples (multi-index columns)
        column_list = []
        for col in data.columns:
            if isinstance(col, tuple):
                column_list.append(col[0].lower())
            else:
                column_list.append(str(col).lower())
        
        # Check if all required columns are present
        if not all(col in column_list for col in required_columns):
            available_cols = ', '.join([str(col) for col in data.columns])
            logger.error(f"Missing required columns for Sweeping Engulfer analysis. Available: {available_cols}")
            return []
        
        # Ensure we have the right column names
        # If columns are tuples, extract the first element
        if isinstance(data.columns[0], tuple):
            # Create a mapping from lowercase column name to actual column
            col_mapping = {}
            for col in data.columns:
                col_mapping[col[0].lower()] = col
            
            # Use the mapping to access the right columns
            high_col = col_mapping.get('high')
            low_col = col_mapping.get('low')
            close_col = col_mapping.get('close')
            open_col = col_mapping.get('open')
            volume_col = col_mapping.get('volume')
        else:
            # Create a mapping from lowercase column name to actual column
            col_mapping = {}
            for col in data.columns:
                col_mapping[str(col).lower()] = col
            
            # Use the mapping to access the right columns
            high_col = col_mapping.get('high')
            low_col = col_mapping.get('low')
            close_col = col_mapping.get('close')
            open_col = col_mapping.get('open')
            volume_col = col_mapping.get('volume')
        
        # Create a new DataFrame with standardized column names
        std_data = pd.DataFrame()
        std_data['open'] = data[open_col]
        std_data['high'] = data[high_col]
        std_data['low'] = data[low_col]
        std_data['close'] = data[close_col]
        std_data['volume'] = data[volume_col]
        std_data.index = data.index
        
        # Calculate body high and low for each candle
        std_data['body_high'] = std_data[['open', 'close']].max(axis=1)
        std_data['body_low'] = std_data[['open', 'close']].min(axis=1)
        
        # Calculate if candle is bullish or bearish
        std_data['bullish'] = std_data['close'] > std_data['open']
        
        # Calculate ATR for reference
        std_data['tr1'] = std_data['high'] - std_data['low']
        std_data['tr2'] = abs(std_data['high'] - std_data['close'].shift(1))
        std_data['tr3'] = abs(std_data['low'] - std_data['close'].shift(1))
        std_data['tr'] = std_data[['tr1', 'tr2', 'tr3']].max(axis=1)
        std_data['atr'] = std_data['tr'].rolling(window=14).mean()
        
        # Find Sweeping Engulfer patterns
        sweeping_engulfers = []
        
        for i in range(2, len(std_data)-1):  # Need at least 3 candles and leave room for the next candle
            current_candle = std_data.iloc[i]
            prev_candle = std_data.iloc[i-1]
            next_candle = std_data.iloc[i+1]
            
            # Check for bullish sweeping engulfing
            bullish_sweep = (
                current_candle['low'] < prev_candle['low'] and  # Sweeps below previous low
                current_candle['close'] > prev_candle['body_high'] and  # Closes above previous body high
                current_candle['bullish']  # Current candle is bullish
            )
            
            # Check for bearish sweeping engulfing
            bearish_sweep = (
                current_candle['high'] > prev_candle['high'] and  # Sweeps above previous high
                current_candle['close'] < prev_candle['body_low'] and  # Closes below previous body low
                not current_candle['bullish']  # Current candle is bearish
            )
            
            # Check if we have a sweeping engulfing pattern
            if bullish_sweep or bearish_sweep:
                pattern_type = "bullish" if bullish_sweep else "bearish"
                
                # Check for retracement in the next candle
                if bullish_sweep:
                    # For bullish pattern, retracement would be downward
                    retracement_distance = current_candle['close'] - current_candle['low']
                    retracement_target = current_candle['close'] - (retracement_distance * self.retracement_threshold)
                    retracement_confirmed = next_candle['low'] <= retracement_target
                else:
                    # For bearish pattern, retracement would be upward
                    retracement_distance = current_candle['high'] - current_candle['close']
                    retracement_target = current_candle['close'] + (retracement_distance * self.retracement_threshold)
                    retracement_confirmed = next_candle['high'] >= retracement_target
                
                if retracement_confirmed:
                    # Calculate strength based on volume and candle size
                    volume_ratio = current_candle['volume'] / prev_candle['volume']
                    candle_size = abs(current_candle['close'] - current_candle['open'])
                    avg_candle_size = std_data['tr'].iloc[i-5:i].mean()  # Average of last 5 candles
                    size_ratio = candle_size / avg_candle_size if avg_candle_size > 0 else 1.0
                    
                    # Combine factors for strength calculation
                    strength = min(1.0, (volume_ratio * size_ratio) / 4)  # Normalize to 0-1 range
                    
                    # Create the setup
                    setup = {
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'timestamp': std_data.index[i],
                        'type': 'sweeping_engulfer',
                        'direction': pattern_type,
                        'price_level': float(current_candle['close']),
                        'swept_level': float(prev_candle['low'] if bullish_sweep else prev_candle['high']),
                        'retracement_level': float(retracement_target),
                        'strength': float(strength),
                        'volume_ratio': float(volume_ratio),
                        'atr': float(current_candle['atr']) if not pd.isna(current_candle['atr']) else 0.0,
                        'notes': ""  # Will be set below
                    }
                    
                    # Set the notes based on the pattern type
                    if bullish_sweep:
                        setup['notes'] = f"Bullish Sweeping Engulfer: Swept low at {float(prev_candle['low']):.2f}, engulfed previous candle, and retraced to {retracement_target:.2f}"
                    else:
                        setup['notes'] = f"Bearish Sweeping Engulfer: Swept high at {float(prev_candle['high']):.2f}, engulfed previous candle, and retraced to {retracement_target:.2f}"
                    
                    sweeping_engulfers.append(setup)
                    logger.info(f"Found {pattern_type.capitalize()} Sweeping Engulfer in {symbol} at {std_data.index[i]}")
        
        return sweeping_engulfers


def fetch_market_data(symbol: str, timeframe: str, period: str = "1y") -> pd.DataFrame:
    """
    Fetch market data for a symbol and timeframe.
    
    Args:
        symbol: The ticker symbol to fetch data for
        timeframe: The timeframe to fetch data for (e.g., 1D, 1H, 4H)
        period: The period to fetch data for (e.g., 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
    Returns:
        A pandas DataFrame with the market data
    """
    logger.info(f"Fetching data for {symbol} on {timeframe} timeframe")
    
    try:
        # Convert timeframe to yfinance interval
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1H": "1h",
            "4H": "4h",
            "1D": "1d",
            "1W": "1wk",
            "1M": "1mo"
        }
        
        interval = interval_map.get(timeframe, "1d")  # Default to daily if not found
        
        # Fetch data from yfinance
        data = yf.download(symbol, period=period, interval=interval, auto_adjust=True)
        
        # Check if data is empty
        if data.empty:
            logger.warning(f"No data fetched for {symbol} on {timeframe} timeframe")
            return pd.DataFrame()
        
        # Print column information for debugging
        logger.info(f"Data columns: {data.columns}")
        logger.info(f"Data types: {data.dtypes}")
        
        # Standardize column names
        column_mapping = {
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Adj Close': 'adj_close',
            'Volume': 'volume'
        }
        
        # Rename columns
        data = data.rename(columns=lambda x: column_mapping.get(x, x.lower()))
        
        # If 'close' is missing but 'adj_close' is present, use adj_close as close
        if 'close' not in data.columns and 'adj_close' in data.columns:
            data['close'] = data['adj_close']
        
        # Ensure we have the standard column names
        expected_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in expected_columns if col not in data.columns]
        
        if missing_columns:
            logger.warning(f"Missing columns in data: {missing_columns}")
            
            # If still missing essential columns, return empty DataFrame
            if any(col not in data.columns for col in ['open', 'high', 'low', 'close']):
                logger.error(f"Essential price columns missing for {symbol}")
                return pd.DataFrame()
        
        logger.info(f"Fetched {len(data)} data points for {symbol}")
        return data
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return pd.DataFrame()


def identify_breakout_setups(data: pd.DataFrame, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
    """
    Identify potential breakout setups.
    
    A breakout setup is when price is approaching a significant resistance or support level
    with momentum, suggesting a potential breakout.
    
    Args:
        data: OHLCV data for the symbol
        symbol: The ticker symbol
        timeframe: The timeframe of the data
        
    Returns:
        A list of breakout setup dictionaries
    """
    logger.info(f"Identifying breakout setups for {symbol} on {timeframe}")
    
    if len(data) < 50:
        logger.warning(f"Not enough data points to identify breakout setups (need at least 50)")
        return []
    
    # Make sure we have the required columns
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    
    # Handle the case where columns are tuples (multi-index columns)
    column_list = []
    for col in data.columns:
        if isinstance(col, tuple):
            column_list.append(col[0].lower())
        else:
            column_list.append(str(col).lower())
    
    # Check if all required columns are present
    if not all(col in column_list for col in required_columns):
        available_cols = ', '.join([str(col) for col in data.columns])
        logger.error(f"Missing required columns for breakout setup analysis. Available: {available_cols}")
        return []
    
    # Get the lookback data
    lookback_data = data.iloc[-50:]
    
    # Ensure we have the right column names
    # If columns are tuples, extract the first element
    if isinstance(data.columns[0], tuple):
        # Create a mapping from lowercase column name to actual column
        col_mapping = {}
        for col in data.columns:
            col_mapping[col[0].lower()] = col
        
        # Use the mapping to access the right columns
        high_col = col_mapping.get('high')
        low_col = col_mapping.get('low')
        close_col = col_mapping.get('close')
        open_col = col_mapping.get('open')
        volume_col = col_mapping.get('volume')
    else:
        # Create a mapping from lowercase column name to actual column
        col_mapping = {}
        for col in data.columns:
            col_mapping[str(col).lower()] = col
        
        # Use the mapping to access the right columns
        high_col = col_mapping.get('high')
        low_col = col_mapping.get('low')
        close_col = col_mapping.get('close')
        open_col = col_mapping.get('open')
        volume_col = col_mapping.get('volume')
    
    # Create a new DataFrame with standardized column names
    std_data = pd.DataFrame()
    std_data['open'] = lookback_data[open_col]
    std_data['high'] = lookback_data[high_col]
    std_data['low'] = lookback_data[low_col]
    std_data['close'] = lookback_data[close_col]
    std_data['volume'] = lookback_data[volume_col]
    std_data.index = lookback_data.index
    
    breakout_setups = []
    
    # Calculate technical indicators
    # 1. Moving averages
    std_data['sma20'] = std_data['close'].rolling(window=20).mean()
    std_data['sma50'] = std_data['close'].rolling(window=50).mean()
    
    # 2. Bollinger Bands
    std_data['bb_middle'] = std_data['close'].rolling(window=20).mean()
    std_data['bb_std'] = std_data['close'].rolling(window=20).std()
    std_data['bb_upper'] = std_data['bb_middle'] + (std_data['bb_std'] * 2)
    std_data['bb_lower'] = std_data['bb_middle'] - (std_data['bb_std'] * 2)
    
    # 3. RSI
    delta = std_data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    std_data['rsi'] = 100 - (100 / (1 + rs))
    
    # 4. Volume indicators
    std_data['volume_sma20'] = std_data['volume'].rolling(window=20).mean()
    
    # Identify key levels (recent highs and lows)
    window_size = 10
    std_data['rolling_high'] = std_data['high'].rolling(window=window_size).max()
    std_data['rolling_low'] = std_data['low'].rolling(window=window_size).min()
    
    # Get the most recent data point
    current = std_data.iloc[-1]
    
    # Check for potential breakout setups
    
    # 1. Bullish breakout setup
    if (
        # Price is near the upper Bollinger Band
        current['close'] > current['bb_middle'] and
        current['close'] < current['bb_upper'] and
        # Price is above both moving averages
        current['close'] > current['sma20'] and
        current['close'] > current['sma50'] and
        # RSI shows momentum but not overbought
        current['rsi'] > 50 and current['rsi'] < 70 and
        # Volume is above average
        current['volume'] > current['volume_sma20'] and
        # Price is near recent high
        abs(current['close'] - current['rolling_high']) / current['close'] < 0.02
    ):
        # Calculate distance to breakout level
        breakout_level = current['rolling_high']
        distance_to_breakout = (breakout_level - current['close']) / current['close'] * 100
        
        # Calculate strength based on RSI and volume
        strength = (current['rsi'] / 100) * (current['volume'] / current['volume_sma20']) / 2
        
        setup = {
            "type": "breakout",
            "symbol": symbol,
            "timeframe": timeframe,
            "direction": "bullish",
            "price_level": float(breakout_level),
            "current_price": float(current['close']),
            "distance_to_breakout": float(distance_to_breakout),
            "strength": float(strength),
            "created_at": std_data.index[-1].strftime('%Y-%m-%d') if hasattr(std_data.index[-1], 'strftime') else str(std_data.index[-1]),
            "notes": f"Bullish breakout setup, {distance_to_breakout:.2f}% to breakout level"
        }
        
        breakout_setups.append(setup)
        logger.info(f"Found bullish breakout setup for {symbol} on {timeframe} at {breakout_level:.2f}")
    
    # 2. Bearish breakout setup
    if (
        # Price is near the lower Bollinger Band
        current['close'] < current['bb_middle'] and
        current['close'] > current['bb_lower'] and
        # Price is below both moving averages
        current['close'] < current['sma20'] and
        current['close'] < current['sma50'] and
        # RSI shows momentum but not oversold
        current['rsi'] < 50 and current['rsi'] > 30 and
        # Volume is above average
        current['volume'] > current['volume_sma20'] and
        # Price is near recent low
        abs(current['close'] - current['rolling_low']) / current['close'] < 0.02
    ):
        # Calculate distance to breakout level
        breakout_level = current['rolling_low']
        distance_to_breakout = (current['close'] - breakout_level) / current['close'] * 100
        
        # Calculate strength based on RSI and volume
        strength = ((100 - current['rsi']) / 100) * (current['volume'] / current['volume_sma20']) / 2
        
        setup = {
            "type": "breakout",
            "symbol": symbol,
            "timeframe": timeframe,
            "direction": "bearish",
            "price_level": float(breakout_level),
            "current_price": float(current['close']),
            "distance_to_breakout": float(distance_to_breakout),
            "strength": float(strength),
            "created_at": std_data.index[-1].strftime('%Y-%m-%d') if hasattr(std_data.index[-1], 'strftime') else str(std_data.index[-1]),
            "notes": f"Bearish breakout setup, {distance_to_breakout:.2f}% to breakout level"
        }
        
        breakout_setups.append(setup)
        logger.info(f"Found bearish breakout setup for {symbol} on {timeframe} at {breakout_level:.2f}")
    
    logger.info(f"Found {len(breakout_setups)} breakout setups for {symbol} on {timeframe}")
    return breakout_setups


def store_setup(setup: Dict[str, Any]) -> bool:
    """
    Store a setup in the database.
    
    Args:
        setup: The setup to store
        
    Returns:
        True if the setup was stored successfully, False otherwise
    """
    # In a real implementation, this would store the setup in a database
    # For now, we just log it
    logger.info(f"Storing setup: {setup}")
    return True


def store_setups(setups: List[Dict[str, Any]], symbol: str, timeframe: str) -> bool:
    """
    Store the identified setups to a file.
    
    Args:
        setups: List of setup dictionaries to store
        symbol: The symbol these setups are for
        timeframe: The timeframe these setups are for
        
    Returns:
        True if successful, False otherwise
    """
    if not setups:
        logger.warning(f"No setups to store for {symbol} on {timeframe}")
        return False
    
    try:
        # Create directory if it doesn't exist
        os.makedirs("data/setups", exist_ok=True)
        
        # Create a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/setups/{symbol}_{timeframe}_{timestamp}.json"
        
        # Add timestamp to each setup and convert any non-serializable objects
        for setup in setups:
            setup["identified_at"] = datetime.now().isoformat()
            
            # Convert Timestamp objects to strings
            if "timestamp" in setup and hasattr(setup["timestamp"], "isoformat"):
                setup["timestamp"] = setup["timestamp"].isoformat()
            
            # Convert date objects to strings
            for key, value in setup.items():
                if isinstance(value, (datetime, pd.Timestamp)):
                    setup[key] = value.isoformat()
                elif isinstance(value, (date)):
                    setup[key] = value.isoformat()
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(setups, f, indent=2)
        
        logger.info(f"Stored {len(setups)} setups for {symbol} on {timeframe} to {filename}")
        return True
    
    except Exception as e:
        logger.error(f"Error storing setups for {symbol} on {timeframe}: {str(e)}")
        return False


def setup_scanner_workflow(
    symbols: List[str] = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
    timeframes: List[str] = ["1D"],
    lookback_periods: int = 50,
    min_volume_threshold: int = 10000,
    price_rejection_threshold: float = 0.005,
    fvg_threshold: float = 0.003,
    min_touches: int = 2,
    retest_threshold: float = 0.005,
    retracement_threshold: float = 0.33,
    period: str = "1y"
) -> Dict[str, Any]:
    """
    Run the setup scanner workflow without using Prefect.
    
    This function orchestrates the process of:
    1. Fetching market data for the specified symbols and timeframes
    2. Scanning for breaker blocks and fair value gaps
    3. Storing the setups found
    
    Args:
        symbols: List of symbols to scan
        timeframes: List of timeframes to scan
        lookback_periods: Number of periods to look back for pattern recognition
        min_volume_threshold: Minimum volume to consider a candle significant
        price_rejection_threshold: Threshold for price rejection
        fvg_threshold: Threshold for fair value gaps
        min_touches: Minimum touches to consider a level significant
        retest_threshold: Threshold for retest
        retracement_threshold: Threshold for retracement in sweeping engulfer patterns
        period: Period to fetch data for (e.g., 1d, 5d, 1mo, 1y, 2y)
        
    Returns:
        Dictionary with summary of setups found
    """
    logger.info(f"Starting setup scanner workflow for {len(symbols)} symbols on {len(timeframes)} timeframes")
    logger.info(f"Symbols: {', '.join(symbols)}")
    logger.info(f"Timeframes: {', '.join(timeframes)}")
    
    # Initialize the scanner
    scanner = SimpleScanner(
        lookback_periods=lookback_periods,
        min_volume_threshold=min_volume_threshold,
        price_rejection_threshold=price_rejection_threshold,
        fvg_threshold=fvg_threshold,
        min_touches=min_touches,
        retest_threshold=retest_threshold,
        retracement_threshold=retracement_threshold
    )
    
    # Dictionary to store all setups
    all_setups = []
    
    # Scan each symbol and timeframe
    for symbol in symbols:
        for timeframe in timeframes:
            logger.info(f"Processing {symbol} on {timeframe} timeframe")
            
            # Fetch market data
            data = fetch_market_data(symbol, timeframe, period)
            
            if data.empty:
                logger.warning(f"No data available for {symbol} on {timeframe} timeframe")
                continue
            
            # Find breaker blocks
            breaker_blocks = scanner.find_breaker_blocks(data, symbol, timeframe)
            if breaker_blocks:
                all_setups.extend(breaker_blocks)
                logger.info(f"Found {len(breaker_blocks)} breaker blocks for {symbol} on {timeframe} timeframe")
            
            # Find fair value gaps
            fair_value_gaps = scanner.find_fair_value_gaps(data, symbol, timeframe)
            if fair_value_gaps:
                all_setups.extend(fair_value_gaps)
                logger.info(f"Found {len(fair_value_gaps)} fair value gaps for {symbol} on {timeframe} timeframe")
            
            # Find sweep engulfers
            sweep_engulfers = scanner.find_sweep_engulfers(data, symbol, timeframe)
            if sweep_engulfers:
                all_setups.extend(sweep_engulfers)
                logger.info(f"Found {len(sweep_engulfers)} sweep engulfer patterns for {symbol} on {timeframe} timeframe")
                
            # Find sweeping engulfers
            sweeping_engulfers = scanner.find_sweeping_engulfers(data, symbol, timeframe)
            if sweeping_engulfers:
                all_setups.extend(sweeping_engulfers)
                logger.info(f"Found {len(sweeping_engulfers)} sweeping engulfer patterns for {symbol} on {timeframe} timeframe")
    
    # Store the setups
    if all_setups:
        store_setups(all_setups, symbols[0], timeframes[0])
        logger.info(f"Stored {len(all_setups)} setups")
    else:
        logger.info("No setups found")
    
    # Return summary
    return {
        "total_setups": len(all_setups),
        "symbols_scanned": len(symbols),
        "timeframes_scanned": len(timeframes),
        "timestamp": datetime.now().isoformat()
    }


def main():
    """Main function to run the setup scanner workflow."""
    parser = argparse.ArgumentParser(description="Run the setup scanner workflow")
    parser.add_argument("--symbols", type=str, nargs="+", default=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META"],
                        help="List of symbols to scan")
    parser.add_argument("--timeframes", type=str, nargs="+", default=["1D"],
                        help="List of timeframes to scan")
    parser.add_argument("--lookback", type=int, default=50,
                        help="Number of periods to look back for pattern recognition")
    parser.add_argument("--min-volume", type=int, default=10000,
                        help="Minimum volume to consider a candle significant")
    parser.add_argument("--price-rejection", type=float, default=0.005,
                        help="Threshold for price rejection")
    parser.add_argument("--fvg-threshold", type=float, default=0.003,
                        help="Threshold for fair value gaps")
    parser.add_argument("--min-touches", type=int, default=2,
                        help="Minimum touches to consider a level significant")
    parser.add_argument("--retest-threshold", type=float, default=0.005,
                        help="Threshold for retest")
    parser.add_argument("--retracement-threshold", type=float, default=0.33,
                        help="Threshold for retracement in sweeping engulfer patterns")
    parser.add_argument("--period", type=str, default="1y",
                        help="Period to fetch data for (e.g., 1d, 5d, 1mo, 1y, 2y)")
    
    args = parser.parse_args()
    
    # Run the workflow
    result = setup_scanner_workflow(
        symbols=args.symbols,
        timeframes=args.timeframes,
        lookback_periods=args.lookback,
        min_volume_threshold=args.min_volume,
        price_rejection_threshold=args.price_rejection,
        fvg_threshold=args.fvg_threshold,
        min_touches=args.min_touches,
        retest_threshold=args.retest_threshold,
        retracement_threshold=args.retracement_threshold,
        period=args.period
    )
    
    logger.info(f"Setup scanner workflow completed. Found {result['total_setups']} setups.")
    return 0


if __name__ == "__main__":
    main() 