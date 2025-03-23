#!/usr/bin/env python3
"""
Candle Aggregator Module

This module provides a centralized system for:
1. Converting tick data to candles of multiple timeframes
2. Storing and tracking candle data across timeframes
3. Identifying and storing patterns (like fair value gaps) 
4. Notifying observers when patterns form across timeframes
"""

import os
import sys
from typing import Dict, List, Tuple, Callable, Optional, Set, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import threading
import time
import json
from collections import defaultdict

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/candle_aggregator_{time}.log", rotation="500 MB", level="DEBUG")

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Define supported timeframes and their minute values
class TimeFrame(Enum):
    M1 = "1m"   # 1 minute
    M5 = "5m"   # 5 minutes
    M15 = "15m" # 15 minutes
    M30 = "30m" # 30 minutes
    H1 = "1h"   # 1 hour
    H4 = "4h"   # 4 hours
    D1 = "1d"   # 1 day

# Timeframe conversion factors (in minutes)
TIMEFRAME_MINUTES = {
    TimeFrame.M1.value: 1,
    TimeFrame.M5.value: 5,
    TimeFrame.M15.value: 15,
    TimeFrame.M30.value: 30,
    TimeFrame.H1.value: 60,
    TimeFrame.H4.value: 240,
    TimeFrame.D1.value: 1440
}

# Pattern types that can be detected
class PatternType(Enum):
    FAIR_VALUE_GAP = "fair_value_gap"
    INVERSE_FAIR_VALUE_GAP = "inverse_fair_value_gap"
    BREAKER_BLOCK = "breaker_block"
    ORDER_BLOCK = "order_block"
    MITIGATION_BLOCK = "mitigation_block"
    LIQUIDITY_VOID = "liquidity_void"
    EQUAL_HIGH = "equal_high"
    EQUAL_LOW = "equal_low"
    LOW_SWEPT = "low_swept"
    HIGH_SWEPT = "high_swept"
    BOS = "break_of_structure"
    CHoCH = "change_of_character"
    FVG = "fair_value_gap"
    INVERSE_FVG = "inverse_fair_value_gap" 
    SWEEP_ENGULFING = "sweep_engulfing"
    SWEEP_ENGULFING_CONFIRMED = "sweep_engulfing_confirmed"
    SUPPORT_RESISTANCE = "support_resistance"
    CHANGE_OF_CHARACTER = "change_of_character"

@dataclass
class Candle:
    """Represents a single OHLCV candle."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    completed: bool = False  # True if candle is complete, False if still forming

@dataclass
class PatternState:
    """Stores information about a detected pattern."""
    pattern_type: PatternType
    timeframe: str
    symbol: str
    start_time: datetime
    end_time: Optional[datetime] = None  # None if pattern is still active
    data: Dict[str, Any] = field(default_factory=dict)  # Pattern-specific data
    id: str = ""  # Unique identifier for the pattern
    
    def __post_init__(self):
        """Generate a unique ID for the pattern."""
        if not self.id:
            self.id = f"{self.pattern_type.value}_{self.timeframe}_{self.symbol}_{int(self.start_time.timestamp())}"

class CandleAggregator:
    """
    Core class for aggregating tick data into multiple timeframe candles and 
    tracking patterns across timeframes.
    """
    
    def __init__(self, 
                 symbols: List[str] = None, 
                 timeframes: List[str] = None,
                 pattern_detection_enabled: bool = True):
        """
        Initialize the candle aggregator.
        
        Args:
            symbols: List of symbols to track
            timeframes: List of timeframes to build (from TimeFrame enum values)
            pattern_detection_enabled: Whether to automatically detect patterns
        """
        self.symbols = symbols or []
        self.timeframes = timeframes or [tf.value for tf in TimeFrame]
        self.pattern_detection_enabled = pattern_detection_enabled
        
        # Initialize candle storage: {timeframe: {symbol: List[Candle]}}
        self.candles: Dict[str, Dict[str, List[Candle]]] = {
            tf: {symbol: [] for symbol in self.symbols} for tf in self.timeframes
        }
        
        # Initialize pattern storage: {pattern_type: {timeframe: {symbol: List[PatternState]}}}
        self.patterns: Dict[str, Dict[str, Dict[str, List[PatternState]]]] = {
            pattern.value: {
                tf: {symbol: [] for symbol in self.symbols} 
                for tf in self.timeframes
            } 
            for pattern in PatternType
        }
        
        # Observer callbacks: {timeframe: {event_type: List[Callable]}}
        self.observers = {
            tf: {
                'candle_complete': [],
                'pattern_detected': [],
                'pattern_updated': [],
                'pattern_completed': []
            } for tf in self.timeframes
        }
        
        # Add global observers that receive events from all timeframes
        self.global_observers = {
            'candle_complete': [],
            'pattern_detected': [],
            'pattern_updated': [],
            'pattern_completed': []
        }
        
        # Track active patterns by ID for quick lookup
        self.active_patterns: Dict[str, PatternState] = {}
        
        # Track last update time for each timeframe and symbol
        self.last_update_time: Dict[str, Dict[str, datetime]] = {
            tf: {symbol: None for symbol in self.symbols} 
            for tf in self.timeframes
        }
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        logger.info(f"CandleAggregator initialized with symbols: {self.symbols}, timeframes: {self.timeframes}")
        
    def add_symbol(self, symbol: str) -> None:
        """Add a new symbol to track."""
        with self.lock:
            if symbol not in self.symbols:
                self.symbols.append(symbol)
                
                # Initialize candle storage for the new symbol
                for tf in self.timeframes:
                    self.candles[tf][symbol] = []
                    self.last_update_time[tf][symbol] = None
                    
                # Initialize pattern storage for the new symbol
                for pattern_type in PatternType:
                    for tf in self.timeframes:
                        self.patterns[pattern_type.value][tf][symbol] = []
                        
                logger.info(f"Added symbol: {symbol}")
    
    def process_tick(self, tick_data: Dict[str, Any]) -> None:
        """
        Process a tick of market data and update candles.
        
        Args:
            tick_data: Dictionary containing tick data with keys:
                - symbol: The ticker symbol
                - timestamp: Timestamp of the tick
                - price: Current price
                - volume: Volume at this tick (if available)
        """
        with self.lock:
            symbol = tick_data['symbol']
            timestamp = tick_data['timestamp']
            price = tick_data['price']
            volume = tick_data.get('volume', 0)
            
            # Ensure symbol is being tracked
            if symbol not in self.symbols:
                self.add_symbol(symbol)
            
            # Update 1-minute candle first (lowest timeframe)
            self._update_candle(TimeFrame.M1.value, symbol, timestamp, price, volume)
    
    def _update_candle(self, timeframe: str, symbol: str, timestamp: datetime, 
                     price: float, volume: float = 0) -> Optional[Candle]:
        """
        Update a candle for the given timeframe and symbol.
        
        Args:
            timeframe: Timeframe to update
            symbol: Symbol to update
            timestamp: Timestamp of the update
            price: Current price
            volume: Volume for this update
            
        Returns:
            The completed candle if a candle was completed, otherwise None
        """
        # Get candle list for this timeframe and symbol
        candle_list = self.candles[timeframe][symbol]
        
        # Calculate candle start time based on timeframe
        minutes = TIMEFRAME_MINUTES[timeframe]
        candle_start = self._normalize_timestamp(timestamp, minutes)
        
        # Check if we need to create a new candle
        if not candle_list or candle_list[-1].timestamp < candle_start:
            # Previous candle is completed if it exists
            if candle_list:
                candle_list[-1].completed = True
                completed_candle = candle_list[-1]
                
                # Notify observers that previous candle is complete
                self._notify_candle_complete(timeframe, symbol, completed_candle)
                
                # Check if we should roll up to the next timeframe
                self._roll_up_if_needed(timeframe, symbol, completed_candle)
                
                # Detect patterns if enabled
                if self.pattern_detection_enabled:
                    self._detect_patterns(timeframe, symbol)
            else:
                completed_candle = None
                
            # Create new candle
            new_candle = Candle(
                timestamp=candle_start,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=volume,
                completed=False
            )
            candle_list.append(new_candle)
            logger.debug(f"Created new {timeframe} candle for {symbol} at {candle_start}")
            
            # Update last update time
            self.last_update_time[timeframe][symbol] = timestamp
            
            return completed_candle
        else:
            # Update existing candle
            current_candle = candle_list[-1]
            current_candle.high = max(current_candle.high, price)
            current_candle.low = min(current_candle.low, price)
            current_candle.close = price
            current_candle.volume += volume
            
            # Update last update time
            self.last_update_time[timeframe][symbol] = timestamp
            
            return None
    
    def _normalize_timestamp(self, timestamp: datetime, minutes: int) -> datetime:
        """
        Normalize a timestamp to the start of a candle period.
        
        Args:
            timestamp: The timestamp to normalize
            minutes: The number of minutes in the timeframe
            
        Returns:
            Normalized timestamp for the start of the candle period
        """
        if minutes < 60:
            # For timeframes less than an hour
            minute_offset = timestamp.minute % minutes
            second_offset = timestamp.second
            microsecond_offset = timestamp.microsecond
            
            return timestamp - timedelta(
                minutes=minute_offset,
                seconds=second_offset,
                microseconds=microsecond_offset
            )
        elif minutes < 1440:
            # For hourly timeframes
            hours = minutes // 60
            hour_offset = timestamp.hour % hours
            minute_offset = timestamp.minute
            second_offset = timestamp.second
            microsecond_offset = timestamp.microsecond
            
            return timestamp - timedelta(
                hours=hour_offset,
                minutes=minute_offset,
                seconds=second_offset,
                microseconds=microsecond_offset
            )
        else:
            # For daily timeframes
            return datetime(
                timestamp.year, 
                timestamp.month, 
                timestamp.day, 
                0, 0, 0
            )
    
    def _roll_up_if_needed(self, timeframe: str, symbol: str, completed_candle: Candle) -> None:
        """
        Roll up a completed candle to the next higher timeframe if needed.
        
        Args:
            timeframe: The timeframe of the completed candle
            symbol: The symbol of the completed candle
            completed_candle: The completed candle
        """
        # Get the next higher timeframe
        timeframe_order = list(TIMEFRAME_MINUTES.keys())
        try:
            current_index = timeframe_order.index(timeframe)
            if current_index < len(timeframe_order) - 1:
                next_timeframe = timeframe_order[current_index + 1]
                
                # Check if this candle completes a higher timeframe candle
                next_tf_minutes = TIMEFRAME_MINUTES[next_timeframe]
                current_tf_minutes = TIMEFRAME_MINUTES[timeframe]
                
                if (completed_candle.timestamp.minute + current_tf_minutes) % next_tf_minutes == 0:
                    # This is a boundary candle that completes a higher timeframe
                    self._update_higher_timeframe(next_timeframe, symbol, completed_candle)
        except ValueError:
            # If timeframe is not in the list, just ignore
            pass
    
    def _update_higher_timeframe(self, higher_timeframe: str, symbol: str, 
                               last_completed_candle: Candle) -> None:
        """
        Update a higher timeframe candle with data from a lower timeframe candle.
        
        Args:
            higher_timeframe: The higher timeframe to update
            symbol: The symbol to update
            last_completed_candle: The last completed candle from the lower timeframe
        """
        higher_tf_list = self.candles[higher_timeframe][symbol]
        higher_tf_minutes = TIMEFRAME_MINUTES[higher_timeframe]
        higher_tf_start = self._normalize_timestamp(last_completed_candle.timestamp, higher_tf_minutes)
        
        # Check if we need to create a new higher timeframe candle
        if not higher_tf_list or higher_tf_list[-1].timestamp < higher_tf_start:
            # Complete previous higher timeframe candle if it exists
            if higher_tf_list:
                higher_tf_list[-1].completed = True
                completed_higher_candle = higher_tf_list[-1]
                
                # Notify observers
                self._notify_candle_complete(higher_timeframe, symbol, completed_higher_candle)
                
                # Roll up to next timeframe if needed
                self._roll_up_if_needed(higher_timeframe, symbol, completed_higher_candle)
                
                # Detect patterns
                if self.pattern_detection_enabled:
                    self._detect_patterns(higher_timeframe, symbol)
            
            # Create new higher timeframe candle
            new_candle = Candle(
                timestamp=higher_tf_start,
                open=last_completed_candle.open,
                high=last_completed_candle.high,
                low=last_completed_candle.low,
                close=last_completed_candle.close,
                volume=last_completed_candle.volume,
                completed=False
            )
            higher_tf_list.append(new_candle)
        else:
            # Update existing higher timeframe candle
            current_candle = higher_tf_list[-1]
            current_candle.high = max(current_candle.high, last_completed_candle.high)
            current_candle.low = min(current_candle.low, last_completed_candle.low)
            current_candle.close = last_completed_candle.close
            current_candle.volume += last_completed_candle.volume
        
        # Update last update time
        self.last_update_time[higher_timeframe][symbol] = datetime.now()
        
    def _notify_candle_complete(self, timeframe: str, symbol: str, candle: Candle) -> None:
        """
        Notify observers that a candle has been completed.
        
        Args:
            timeframe: Timeframe of the completed candle
            symbol: Symbol of the completed candle
            candle: The completed candle
        """
        # Update patterns if needed
        if timeframe in [TimeFrame.H4.value, TimeFrame.D1.value]:
            self._update_sweep_engulfing_retracements(timeframe, symbol, candle)
        
        # Call timeframe-specific observers
        for observer in self.observers[timeframe]['candle_complete']:
            observer(timeframe, symbol, candle)
        
        # Call global observers
        for observer in self.global_observers['candle_complete']:
            observer(timeframe, symbol, candle)
            
    def _detect_patterns(self, timeframe: str, symbol: str) -> None:
        """
        Detect patterns in the candle data for a specific timeframe and symbol.
        
        Args:
            timeframe: Timeframe to detect patterns in
            symbol: Symbol to detect patterns for
        """
        # Get candles for this timeframe and symbol
        candle_list = self.candles[timeframe][symbol]
        
        # Need at least 3 candles to detect most patterns
        if len(candle_list) < 3:
            return
        
        # Convert to pandas DataFrame for easier pattern detection
        df = self._candles_to_dataframe(candle_list)
        
        # Detect fair value gaps
        self._detect_fair_value_gaps(timeframe, symbol, df)
        
        # Detect inverse fair value gaps
        self._detect_inverse_fair_value_gaps(timeframe, symbol, df)
        
        # Detect breaker blocks
        self._detect_breaker_blocks(timeframe, symbol, df)
        
        # Detect sweep engulfer patterns
        self._detect_sweep_engulfers(timeframe, symbol, df)
        
        # Detect change of character
        self._detect_change_of_character(timeframe, symbol, df)
        
        # Detect support and resistance levels
        self._detect_support_resistance(timeframe, symbol, df)
    
    def _candles_to_dataframe(self, candles: List[Candle]) -> pd.DataFrame:
        """
        Convert a list of Candle objects to a pandas DataFrame.
        
        Args:
            candles: List of Candle objects
            
        Returns:
            pandas DataFrame with OHLCV data
        """
        data = {
            'timestamp': [c.timestamp for c in candles],
            'open': [c.open for c in candles],
            'high': [c.high for c in candles],
            'low': [c.low for c in candles],
            'close': [c.close for c in candles],
            'volume': [c.volume for c in candles]
        }
        return pd.DataFrame(data)
    
    def _detect_fair_value_gaps(self, timeframe: str, symbol: str, df: pd.DataFrame) -> None:
        """
        Detect fair value gaps in the candle data.
        A fair value gap occurs when a candle's low is higher than the previous candle's high.
        
        Args:
            timeframe: Timeframe to detect in
            symbol: Symbol to detect for
            df: DataFrame containing candle data
        """
        # Need at least 3 candles
        if len(df) < 3:
            return
            
        # Look at the most recent 3 candles
        last_candles = df.iloc[-3:].copy()
        
        # Check if there's a bullish fair value gap
        if last_candles.iloc[1]['low'] > last_candles.iloc[0]['high']:
            # Found a bullish fair value gap
            gap_size = last_candles.iloc[1]['low'] - last_candles.iloc[0]['high']
            gap_percentage = gap_size / last_candles.iloc[0]['high'] * 100
            
            # Only record significant gaps (adjust threshold as needed)
            if gap_percentage > 0.1:  # 0.1% threshold
                self._record_pattern(
                    pattern_type=PatternType.FAIR_VALUE_GAP,
                    timeframe=timeframe,
                    symbol=symbol,
                    start_time=last_candles.iloc[0]['timestamp'],
                    data={
                        'direction': 'bullish',
                        'gap_size': gap_size,
                        'gap_percentage': gap_percentage,
                        'bottom': last_candles.iloc[0]['high'],
                        'top': last_candles.iloc[1]['low'],
                        'filled': False
                    }
                )
                
        # Check if there's a bearish fair value gap
        if last_candles.iloc[1]['high'] < last_candles.iloc[0]['low']:
            # Found a bearish fair value gap
            gap_size = last_candles.iloc[0]['low'] - last_candles.iloc[1]['high']
            gap_percentage = gap_size / last_candles.iloc[0]['low'] * 100
            
            # Only record significant gaps
            if gap_percentage > 0.1:  # 0.1% threshold
                self._record_pattern(
                    pattern_type=PatternType.FAIR_VALUE_GAP,
                    timeframe=timeframe,
                    symbol=symbol,
                    start_time=last_candles.iloc[0]['timestamp'],
                    data={
                        'direction': 'bearish',
                        'gap_size': gap_size,
                        'gap_percentage': gap_percentage,
                        'top': last_candles.iloc[0]['low'],
                        'bottom': last_candles.iloc[1]['high'],
                        'filled': False
                    }
                )
                
        # Update existing fair value gaps to check if they've been filled
        self._update_fair_value_gaps(timeframe, symbol, df.iloc[-1])
        
    def _update_fair_value_gaps(self, timeframe: str, symbol: str, latest_candle: pd.Series) -> None:
        """
        Update existing fair value gaps to check if they've been filled.
        
        Args:
            timeframe: Timeframe to update
            symbol: Symbol to update
            latest_candle: Latest candle data
        """
        # Get active fair value gaps for this timeframe and symbol
        pattern_list = self.patterns[PatternType.FAIR_VALUE_GAP.value][timeframe][symbol]
        
        for pattern in pattern_list:
            # Skip patterns that are already filled or completed
            if pattern.end_time is not None or pattern.data.get('filled', False):
                continue
                
            # Check if gap has been filled
            if pattern.data['direction'] == 'bullish':
                if latest_candle['low'] <= pattern.data['top']:
                    pattern.data['filled'] = True
                    pattern.end_time = latest_candle['timestamp']
                    self._notify_pattern_completed(timeframe, symbol, pattern)
            else:  # bearish
                if latest_candle['high'] >= pattern.data['bottom']:
                    pattern.data['filled'] = True
                    pattern.end_time = latest_candle['timestamp']
                    self._notify_pattern_completed(timeframe, symbol, pattern)
                    
    def _detect_inverse_fair_value_gaps(self, timeframe: str, symbol: str, df: pd.DataFrame) -> None:
        """
        Detect inverse fair value gaps (IFVG) in the candle data.
        
        An IFVG occurs when a previously formed fair value gap is closed by a later candle's body.
        
        Args:
            timeframe: Timeframe to detect in
            symbol: Symbol to detect for
            df: DataFrame containing candle data
        """
        # Need at least 4 candles for IFVG detection (3 for FVG + 1 for closing it)
        if len(df) < 10:  # Need more history to find potential FVGs
            return
            
        # Get all previously detected FVGs for this symbol and timeframe
        fvgs = self.get_patterns_by_timeframe(
            timeframe=timeframe, 
            symbol=symbol,
            pattern_type=PatternType.FAIR_VALUE_GAP,
            include_completed=True  # Include completed ones as they may be closed later
        )
        
        # Current candle
        current_candle = df.iloc[-1]
        current_body_high = max(current_candle['open'], current_candle['close'])
        current_body_low = min(current_candle['open'], current_candle['close'])
        
        for fvg in fvgs:
            # Skip if this FVG has already been marked as having an IFVG
            if fvg.data.get('has_inverse_fvg', False):
                continue
                
            # Get gap boundaries
            gap_high = fvg.data.get('gap_high')
            gap_low = fvg.data.get('gap_low')
            fvg_direction = fvg.data.get('direction')
            
            if gap_high is None or gap_low is None or fvg_direction is None:
                continue
                
            # Check if current candle body closes the gap in the opposite direction
            if fvg_direction == 'bullish':
                # For bullish FVG, need bearish candle closing the gap
                if (current_candle['close'] < current_candle['open'] and  # Bearish candle
                    current_body_high >= gap_high and current_body_low <= gap_low):  # Body closes gap
                    
                    # Record the inverse FVG
                    self._record_pattern(
                        pattern_type=PatternType.INVERSE_FAIR_VALUE_GAP,
                        timeframe=timeframe,
                        symbol=symbol,
                        start_time=current_candle['timestamp'],
                        data={
                            'direction': 'bearish',  # Opposite of original FVG
                            'original_fvg_id': fvg.id,
                            'original_fvg_start_time': fvg.start_time,
                            'gap_high': gap_high,
                            'gap_low': gap_low,
                            'closing_candle_timestamp': current_candle['timestamp']
                        }
                    )
                    
                    # Mark the original FVG as having an inverse
                    fvg.data['has_inverse_fvg'] = True
                    self._notify_pattern_updated(timeframe, symbol, fvg)
                    logger.debug(f"Detected bearish IFVG on {timeframe} for {symbol}")
                    
            elif fvg_direction == 'bearish':
                # For bearish FVG, need bullish candle closing the gap
                if (current_candle['close'] > current_candle['open'] and  # Bullish candle
                    current_body_high >= gap_high and current_body_low <= gap_low):  # Body closes gap
                    
                    # Record the inverse FVG
                    self._record_pattern(
                        pattern_type=PatternType.INVERSE_FAIR_VALUE_GAP,
                        timeframe=timeframe,
                        symbol=symbol,
                        start_time=current_candle['timestamp'],
                        data={
                            'direction': 'bullish',  # Opposite of original FVG
                            'original_fvg_id': fvg.id,
                            'original_fvg_start_time': fvg.start_time,
                            'gap_high': gap_high,
                            'gap_low': gap_low,
                            'closing_candle_timestamp': current_candle['timestamp']
                        }
                    )
                    
                    # Mark the original FVG as having an inverse
                    fvg.data['has_inverse_fvg'] = True
                    self._notify_pattern_updated(timeframe, symbol, fvg)
                    logger.debug(f"Detected bullish IFVG on {timeframe} for {symbol}")
    
    def _detect_breaker_blocks(self, timeframe: str, symbol: str, df: pd.DataFrame) -> None:
        """
        Detect breaker blocks in the candle data.
        
        A breaker block forms when price breaks through a significant support/resistance level
        and then returns to retest that level from the opposite side.
        
        Args:
            timeframe: Timeframe to detect in
            symbol: Symbol to detect for
            df: DataFrame containing candle data
        """
        # Need at least 5 candles for breaker block detection
        if len(df) < 5:
            return
            
        # Implementation for breaker block detection would go here
        # This is a simplified placeholder
        pass
        
    def _detect_sweep_engulfers(self, timeframe: str, symbol: str, df: pd.DataFrame) -> None:
        """
        Detect sweep engulfer patterns in the candle data.
        
        A sweep engulfer occurs when price sweeps beyond a local high/low and then
        quickly reverses, engulfing the previous candle's body (not just the wick).
        
        Args:
            timeframe: Timeframe to detect in
            symbol: Symbol to detect for
            df: DataFrame containing candle data
        """
        # Need at least a few candles for proper detection
        if len(df) < 5:
            return
            
        # Only detect on certain timeframes (typically higher timeframes)
        if timeframe not in [TimeFrame.H4.value, TimeFrame.D1.value]:
            return
            
        # Get candles for analysis
        df = df.copy().reset_index(drop=True)
        
        for i in range(2, len(df)):
            current_candle = df.iloc[i]
            prev_candle = df.iloc[i-1]
            pre_prev_candle = df.iloc[i-2]
            
            # Calculate previous candle's body high and low (not considering wicks)
            prev_body_high = max(prev_candle['open'], prev_candle['close'])
            prev_body_low = min(prev_candle['open'], prev_candle['close'])
            
            # Bullish sweep engulfing (sweeps below recent low then engulfs previous candle's body)
            if (current_candle['low'] < prev_candle['low'] and  # Sweeps below previous low
                current_candle['close'] > prev_body_high and    # Closes above previous body high
                current_candle['close'] > current_candle['open']):  # Bullish candle
                
                # Calculate candle size and properties
                candle_size = abs(current_candle['close'] - current_candle['low'])
                engulf_size = abs(current_candle['close'] - prev_body_low)
                engulf_ratio = engulf_size / abs(prev_body_high - prev_body_low)
                sweep_size = abs(prev_candle['low'] - current_candle['low'])
                
                # Significant sweep engulfing
                if engulf_ratio > 1.0 and sweep_size > 0:
                    self._record_pattern(
                        pattern_type=PatternType.SWEEP_ENGULFING,
                        timeframe=timeframe,
                        symbol=symbol,
                        start_time=current_candle['timestamp'],
                        data={
                            'direction': 'bullish',
                            'engulf_ratio': engulf_ratio,
                            'sweep_size': sweep_size,
                            'candle_size': candle_size,
                            'retracement_tracked': False,
                            'retracement_levels': {
                                '33_percent': current_candle['close'] - (candle_size * 0.33),
                                '50_percent': current_candle['close'] - (candle_size * 0.5),
                                '66_percent': current_candle['close'] - (candle_size * 0.66)
                            },
                            'candle_idx': i,
                            'prev_body_high': prev_body_high,
                            'prev_body_low': prev_body_low
                        }
                    )
                    logger.debug(f"Detected bullish sweep engulfing on {timeframe} for {symbol}")
            
            # Bearish sweep engulfing (sweeps above recent high then engulfs previous candle's body)
            elif (current_candle['high'] > prev_candle['high'] and  # Sweeps above previous high
                  current_candle['close'] < prev_body_low and      # Closes below previous body low
                  current_candle['close'] < current_candle['open']):  # Bearish candle
                
                # Calculate candle size and properties
                candle_size = abs(current_candle['high'] - current_candle['close'])
                engulf_size = abs(prev_body_high - current_candle['close'])
                engulf_ratio = engulf_size / abs(prev_body_high - prev_body_low)
                sweep_size = abs(current_candle['high'] - prev_candle['high'])
                
                # Significant sweep engulfing
                if engulf_ratio > 1.0 and sweep_size > 0:
                    self._record_pattern(
                        pattern_type=PatternType.SWEEP_ENGULFING,
                        timeframe=timeframe,
                        symbol=symbol,
                        start_time=current_candle['timestamp'],
                        data={
                            'direction': 'bearish',
                            'engulf_ratio': engulf_ratio,
                            'sweep_size': sweep_size,
                            'candle_size': candle_size,
                            'retracement_tracked': False,
                            'retracement_levels': {
                                '33_percent': current_candle['close'] + (candle_size * 0.33),
                                '50_percent': current_candle['close'] + (candle_size * 0.5),
                                '66_percent': current_candle['close'] + (candle_size * 0.66)
                            },
                            'candle_idx': i,
                            'prev_body_high': prev_body_high,
                            'prev_body_low': prev_body_low
                        }
                    )
                    logger.debug(f"Detected bearish sweep engulfing on {timeframe} for {symbol}")
    
    def _update_sweep_engulfing_retracements(self, timeframe: str, symbol: str, 
                                          candle: Candle) -> None:
        """
        Update sweep engulfing patterns to track retracement levels.
        
        Args:
            timeframe: Timeframe of the candle
            symbol: Symbol of the candle
            candle: The newest candle
        """
        # Only check retracements on the timeframe where the pattern was detected
        active_patterns = self.get_active_patterns(
            pattern_type=PatternType.SWEEP_ENGULFING,
            timeframe=timeframe,
            symbol=symbol
        )
        
        for pattern in active_patterns:
            # Skip if retracement already tracked
            if pattern.data.get('retracement_tracked', False):
                continue
                
            # Get retracement levels
            retracement_levels = pattern.data.get('retracement_levels', {})
            if not retracement_levels:
                continue
                
            # Check if price has retraced to required level (33%)
            if pattern.data['direction'] == 'bullish':
                # For bullish patterns, price should retrace downward
                if candle.low <= retracement_levels['33_percent']:
                    # Mark retracement as tracked
                    pattern.data['retracement_tracked'] = True
                    pattern.data['retracement_time'] = candle.timestamp
                    pattern.data['retracement_price'] = candle.low
                    
                    # Notify observers about the update
                    self._notify_pattern_updated(timeframe, symbol, pattern)
                    logger.debug(f"Bullish sweep engulfing retraced 33% on {timeframe} for {symbol}")
                    
            else:  # Bearish pattern
                # For bearish patterns, price should retrace upward
                if candle.high >= retracement_levels['33_percent']:
                    # Mark retracement as tracked
                    pattern.data['retracement_tracked'] = True
                    pattern.data['retracement_time'] = candle.timestamp
                    pattern.data['retracement_price'] = candle.high
                    
                    # Notify observers about the update
                    self._notify_pattern_updated(timeframe, symbol, pattern)
                    logger.debug(f"Bearish sweep engulfing retraced 33% on {timeframe} for {symbol}")
    
    def _detect_change_of_character(self, timeframe: str, symbol: str, df: pd.DataFrame) -> None:
        """
        Detect change of character (COC) in the candle data.
        
        A change of character occurs when market structure breaks in the opposite direction of the trend.
        For bullish COC: In a downtrend (lower highs, lower lows), price breaks structure by making a higher low.
        For bearish COC: In an uptrend (higher highs, higher lows), price breaks structure by making a lower low.
        
        Args:
            timeframe: Timeframe to detect in
            symbol: Symbol to detect for
            df: DataFrame containing candle data
        """
        # Need sufficient candles to detect trend and COC
        if len(df) < 10:
            return
            
        # Get last 10 candles for analysis
        recent_df = df.tail(10).reset_index(drop=True)
        
        # Determine trend direction using recent highs and lows
        highs = recent_df['high'].tolist()
        lows = recent_df['low'].tolist()
        
        # Simple trend detection - compare first half to second half
        first_half_high_max = max(highs[:5])
        first_half_low_min = min(lows[:5])
        second_half_high_max = max(highs[5:])
        second_half_low_min = min(lows[5:])
        
        # Current and previous candles
        current_candle = recent_df.iloc[-1]
        prev_candle = recent_df.iloc[-2]
        
        # Check for bullish COC (break of downtrend)
        is_downtrend = second_half_high_max < first_half_high_max and second_half_low_min < first_half_low_min
        has_higher_low = current_candle['low'] > prev_candle['low'] and min(current_candle['open'], current_candle['close']) > min(prev_candle['open'], prev_candle['close'])
        
        if is_downtrend and has_higher_low and current_candle['close'] > current_candle['open']:
            # Bullish change of character
            self._record_pattern(
                pattern_type=PatternType.CHANGE_OF_CHARACTER,
                timeframe=timeframe,
                symbol=symbol,
                start_time=current_candle['timestamp'],
                data={
                    'direction': 'bullish',
                    'previous_trend': 'downtrend',
                    'structure_break': 'higher_low',
                    'previous_low': prev_candle['low'],
                    'current_low': current_candle['low']
                }
            )
            logger.debug(f"Detected bullish COC on {timeframe} for {symbol}")
        
        # Check for bearish COC (break of uptrend)
        is_uptrend = second_half_high_max > first_half_high_max and second_half_low_min > first_half_low_min
        has_lower_high = current_candle['high'] < prev_candle['high'] and max(current_candle['open'], current_candle['close']) < max(prev_candle['open'], prev_candle['close'])
        
        if is_uptrend and has_lower_high and current_candle['close'] < current_candle['open']:
            # Bearish change of character
            self._record_pattern(
                pattern_type=PatternType.CHANGE_OF_CHARACTER,
                timeframe=timeframe,
                symbol=symbol,
                start_time=current_candle['timestamp'],
                data={
                    'direction': 'bearish',
                    'previous_trend': 'uptrend',
                    'structure_break': 'lower_high',
                    'previous_high': prev_candle['high'],
                    'current_high': current_candle['high']
                }
            )
            logger.debug(f"Detected bearish COC on {timeframe} for {symbol}")
    
    def _notify_candle_complete(self, timeframe: str, symbol: str, candle: Candle) -> None:
        """
        Notify observers that a candle has been completed.
        
        Args:
            timeframe: Timeframe of the completed candle
            symbol: Symbol of the completed candle
            candle: The completed candle
        """
        # Update patterns if needed
        if timeframe in [TimeFrame.H4.value, TimeFrame.D1.value]:
            self._update_sweep_engulfing_retracements(timeframe, symbol, candle)
        
        # Call timeframe-specific observers
        for observer in self.observers[timeframe]['candle_complete']:
            observer(timeframe, symbol, candle)
        
        # Call global observers
        for observer in self.global_observers['candle_complete']:
            observer(timeframe, symbol, candle)
            
    def _detect_patterns(self, timeframe: str, symbol: str) -> None:
        """
        Detect all patterns for a specific timeframe and symbol.
        
        Args:
            timeframe: Timeframe to detect in
            symbol: Symbol to detect for
        """
        # Get candles
        candles = self.get_candles(timeframe, symbol)
        if not candles:
            return
            
        # Convert to DataFrame
        df = self._candles_to_dataframe(candles)
        
        # Detect fair value gaps
        self._detect_fair_value_gaps(timeframe, symbol, df)
        
        # Detect inverse fair value gaps
        self._detect_inverse_fair_value_gaps(timeframe, symbol, df)
        
        # Detect breaker blocks
        self._detect_breaker_blocks(timeframe, symbol, df)
        
        # Detect sweep engulfer patterns
        self._detect_sweep_engulfers(timeframe, symbol, df)
        
        # Detect change of character
        self._detect_change_of_character(timeframe, symbol, df)
        
        # Detect support and resistance levels
        self._detect_support_resistance(timeframe, symbol, df)
    
    def _record_pattern(self, pattern_type: PatternType, timeframe: str, symbol: str, 
                      start_time: datetime, data: Dict[str, Any] = None, 
                      end_time: Optional[datetime] = None) -> PatternState:
        """
        Record a detected pattern.
        
        Args:
            pattern_type: Type of pattern detected
            timeframe: Timeframe the pattern was detected in
            symbol: Symbol the pattern was detected for
            start_time: Start time of the pattern
            data: Additional data about the pattern
            end_time: End time of the pattern (None if still active)
            
        Returns:
            The created PatternState object
        """
        pattern = PatternState(
            pattern_type=pattern_type,
            timeframe=timeframe,
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            data=data or {}
        )
        
        # Add to pattern list
        self.patterns[pattern_type.value][timeframe][symbol].append(pattern)
        
        # Add to active patterns if not completed
        if end_time is None:
            self.active_patterns[pattern.id] = pattern
            
        # Notify observers
        self._notify_pattern_detected(timeframe, symbol, pattern)
        
        logger.debug(f"Recorded {pattern_type.value} pattern for {symbol} on {timeframe}")
        
        return pattern
    
    def _notify_pattern_detected(self, timeframe: str, symbol: str, pattern: PatternState) -> None:
        """
        Notify observers that a pattern has been detected.
        
        Args:
            timeframe: Timeframe of the pattern
            symbol: Symbol of the pattern
            pattern: The detected pattern
        """
        # Call timeframe-specific observers
        for observer in self.observers[timeframe]['pattern_detected']:
            observer(timeframe, symbol, pattern)
        
        # Call global observers
        for observer in self.global_observers['pattern_detected']:
            observer(timeframe, symbol, pattern)
    
    def _notify_pattern_updated(self, timeframe: str, symbol: str, pattern: PatternState) -> None:
        """
        Notify observers that a pattern has been updated.
        
        Args:
            timeframe: Timeframe of the pattern
            symbol: Symbol of the pattern
            pattern: The updated pattern
        """
        # Call timeframe-specific observers
        for observer in self.observers[timeframe]['pattern_updated']:
            observer(timeframe, symbol, pattern)
        
        # Call global observers
        for observer in self.global_observers['pattern_updated']:
            observer(timeframe, symbol, pattern)
    
    def _notify_pattern_completed(self, timeframe: str, symbol: str, pattern: PatternState) -> None:
        """
        Notify observers that a pattern has been completed.
        
        Args:
            timeframe: Timeframe of the pattern
            symbol: Symbol of the pattern
            pattern: The completed pattern
        """
        # Remove from active patterns
        if pattern.id in self.active_patterns:
            del self.active_patterns[pattern.id]
            
        # Call timeframe-specific observers
        for observer in self.observers[timeframe]['pattern_completed']:
            observer(timeframe, symbol, pattern)
        
        # Call global observers
        for observer in self.global_observers['pattern_completed']:
            observer(timeframe, symbol, pattern)
    
    def register_observer(self, event_type: str, callback: Callable, 
                        timeframe: Optional[str] = None) -> None:
        """
        Register an observer for a specific event type and optionally a specific timeframe.
        
        Args:
            event_type: Type of event to observe 
                ('candle_complete', 'pattern_detected', 'pattern_updated', 'pattern_completed')
            callback: Callback function to call when the event occurs
            timeframe: Specific timeframe to observe, or None for all timeframes
        """
        with self.lock:
            if timeframe is None:
                # Register as global observer for all timeframes
                if event_type in self.global_observers:
                    self.global_observers[event_type].append(callback)
            else:
                # Register for specific timeframe
                if timeframe in self.observers and event_type in self.observers[timeframe]:
                    self.observers[timeframe][event_type].append(callback)
    
    def unregister_observer(self, event_type: str, callback: Callable, 
                          timeframe: Optional[str] = None) -> bool:
        """
        Unregister an observer.
        
        Args:
            event_type: Type of event the observer was registered for
            callback: The callback function to unregister
            timeframe: Specific timeframe, or None for global observers
            
        Returns:
            True if observer was successfully unregistered, False otherwise
        """
        with self.lock:
            if timeframe is None:
                # Unregister global observer
                if event_type in self.global_observers and callback in self.global_observers[event_type]:
                    self.global_observers[event_type].remove(callback)
                    return True
            else:
                # Unregister timeframe-specific observer
                if (timeframe in self.observers and 
                    event_type in self.observers[timeframe] and 
                    callback in self.observers[timeframe][event_type]):
                    self.observers[timeframe][event_type].remove(callback)
                    return True
                    
            return False
    
    def get_candles(self, timeframe: str, symbol: str, limit: int = None) -> List[Candle]:
        """
        Get candles for a specific timeframe and symbol.
        
        Args:
            timeframe: Timeframe to get candles for
            symbol: Symbol to get candles for
            limit: Maximum number of candles to return (most recent ones)
            
        Returns:
            List of Candle objects
        """
        with self.lock:
            candle_list = self.candles[timeframe][symbol]
            if limit:
                return candle_list[-limit:]
            return candle_list.copy()
    
    def get_active_patterns(self, pattern_type: Optional[PatternType] = None, 
                          timeframe: Optional[str] = None, 
                          symbol: Optional[str] = None) -> List[PatternState]:
        """
        Get active patterns, optionally filtered by type, timeframe, and/or symbol.
        
        Args:
            pattern_type: Pattern type to filter by, or None for all pattern types
            timeframe: Timeframe to filter by, or None for all timeframes
            symbol: Symbol to filter by, or None for all symbols
            
        Returns:
            List of active PatternState objects
        """
        with self.lock:
            result = []
            
            for pattern in self.active_patterns.values():
                # Apply filters
                if pattern_type and pattern.pattern_type != pattern_type:
                    continue
                if timeframe and pattern.timeframe != timeframe:
                    continue
                if symbol and pattern.symbol != symbol:
                    continue
                    
                result.append(pattern)
                
            return result
    
    def get_patterns_by_timeframe(self, timeframe: str, symbol: str, 
                               pattern_type: Optional[PatternType] = None,
                               include_completed: bool = False) -> List[PatternState]:
        """
        Get patterns for a specific timeframe and symbol.
        
        Args:
            timeframe: Timeframe to get patterns for
            symbol: Symbol to get patterns for
            pattern_type: Specific pattern type to get, or None for all types
            include_completed: Whether to include completed patterns
            
        Returns:
            List of PatternState objects
        """
        with self.lock:
            result = []
            
            if pattern_type:
                # Get patterns for specific type
                pattern_list = self.patterns[pattern_type.value][timeframe][symbol]
                for pattern in pattern_list:
                    if include_completed or pattern.end_time is None:
                        result.append(pattern)
            else:
                # Get patterns for all types
                for pattern_type_value in self.patterns:
                    pattern_list = self.patterns[pattern_type_value][timeframe][symbol]
                    for pattern in pattern_list:
                        if include_completed or pattern.end_time is None:
                            result.append(pattern)
                            
            return result
    
    def get_timeframe_interactions(self, symbol: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get information about how patterns on different timeframes interact for a symbol.
        
        This is useful for finding setups like "we're in a 4h fair value gap, now we want to see X on the 5m".
        
        Args:
            symbol: Symbol to analyze
            
        Returns:
            Dictionary mapping parent timeframe patterns to child timeframe patterns
        """
        with self.lock:
            result = {}
            
            # Get all active patterns for the symbol
            all_patterns = [p for p in self.active_patterns.values() if p.symbol == symbol]
            
            # Sort timeframes from higher to lower (e.g., 4h -> 1h -> 15m -> 5m -> 1m)
            timeframe_order = sorted(self.timeframes, 
                                    key=lambda tf: TIMEFRAME_MINUTES[tf], 
                                    reverse=True)
            
            # For each higher timeframe pattern
            for parent_tf in timeframe_order[:-1]:  # Skip the lowest timeframe
                parent_patterns = [p for p in all_patterns if p.timeframe == parent_tf]
                
                for parent_pattern in parent_patterns:
                    # Find child patterns in lower timeframes that occurred after the parent pattern
                    child_patterns = []
                    
                    for child_tf in timeframe_order[timeframe_order.index(parent_tf)+1:]:
                        # Get child patterns that started after the parent pattern
                        child_candidates = [
                            p for p in all_patterns 
                            if p.timeframe == child_tf and p.start_time >= parent_pattern.start_time
                        ]
                        
                        for child in child_candidates:
                            child_patterns.append({
                                'parent_pattern': parent_pattern,
                                'child_pattern': child,
                                'parent_timeframe': parent_tf,
                                'child_timeframe': child_tf,
                                'time_difference': (child.start_time - parent_pattern.start_time).total_seconds() / 60  # minutes
                            })
                    
                    if child_patterns:
                        pattern_key = f"{parent_pattern.pattern_type.value}_{parent_tf}_{parent_pattern.id}"
                        result[pattern_key] = child_patterns
                        
            return result

    def to_dataframe(self, timeframe: str, symbol: str) -> pd.DataFrame:
        """
        Convert candles for a specific timeframe and symbol to a pandas DataFrame.
        
        Args:
            timeframe: Timeframe to convert
            symbol: Symbol to convert
            
        Returns:
            pandas DataFrame with OHLCV data
        """
        candles = self.get_candles(timeframe, symbol)
        return self._candles_to_dataframe(candles)
        
    def process_candles(self, candles: pd.DataFrame, timeframe: str, symbol: str) -> None:
        """
        Process a batch of candles for a specific timeframe and symbol.
        
        This is useful for initializing historical data or when receiving batch updates.
        
        Args:
            candles: DataFrame containing OHLCV data
            timeframe: Timeframe of the candles
            symbol: Symbol of the candles
        """
        with self.lock:
            # Ensure required columns exist
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in candles.columns for col in required_cols):
                raise ValueError(f"Candles DataFrame must contain columns: {required_cols}")
                
            # Ensure symbol is being tracked
            if symbol not in self.symbols:
                self.add_symbol(symbol)
                
            # Convert to Candle objects
            candle_list = []
            for _, row in candles.iterrows():
                candle = Candle(
                    timestamp=row['timestamp'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume'],
                    completed=True  # Historical candles are always completed
                )
                candle_list.append(candle)
                
            # Replace existing candles for this timeframe and symbol
            self.candles[timeframe][symbol] = candle_list
            
            # Update last update time
            self.last_update_time[timeframe][symbol] = datetime.now()
            
            # Detect patterns if enabled
            if self.pattern_detection_enabled:
                self._detect_patterns(timeframe, symbol)
                
            logger.info(f"Processed {len(candle_list)} {timeframe} candles for {symbol}")


class SweepEngulfingMultiTFObserver(MultiTimeframeObserver):
    """
    Observer for tracking sweep engulfing patterns with confirmations on lower timeframes.
    
    This observer looks for:
    1. Sweep engulfing patterns on 4h or daily timeframes
    2. Retracement of at least 33% of the engulfing candle
    3. Specific price action on 5m timeframe:
       - Either a Change of Character (COC)
       - Or an Inverse Fair Value Gap (IFVG)
    """
    
    def __init__(self, aggregator: CandleAggregator):
        """
        Initialize the sweep engulfing observer.
        
        Args:
            aggregator: The CandleAggregator instance to observe
        """
        super().__init__(aggregator)
        self.pending_setups = {}  # Tracks setups waiting for lower timeframe confirmation
        
    def get_observed_timeframes(self) -> List[str]:
        """
        Get the timeframes this observer is interested in.
        
        Returns:
            List of timeframe strings
        """
        return [TimeFrame.M5.value, TimeFrame.H4.value, TimeFrame.D1.value]
    
    def on_pattern_detected(self, timeframe: str, symbol: str, pattern: PatternState) -> None:
        """
        Called when any pattern is detected. We need to check for both high TF patterns
        and also potential confirmation patterns on the 5m timeframe.
        
        Args:
            timeframe: Timeframe of the pattern
            symbol: Symbol of the pattern
            pattern: The detected pattern
        """
        # Track the high TF sweep engulfing patterns
        if (pattern.pattern_type == PatternType.SWEEP_ENGULFING and 
            timeframe in [TimeFrame.H4.value, TimeFrame.D1.value]):
            logger.info(f"High TF Sweep Engulfing detected on {timeframe} for {symbol}: {pattern.data['direction']}")
            return
            
        # Check for confirmation patterns on 5m
        if timeframe != TimeFrame.M5.value:
            return
            
        # We're looking for either IFVG or COC on 5m as confirmation
        if pattern.pattern_type not in [PatternType.INVERSE_FAIR_VALUE_GAP, PatternType.CHANGE_OF_CHARACTER]:
            return
            
        # Check all pending setups for this symbol
        symbol_setups = [s for s_id, s in self.pending_setups.items() 
                          if s['symbol'] == symbol and not s['confirmed']]
        
        for setup in symbol_setups:
            higher_tf_pattern = setup['pattern']
            
            # Only confirm if the pattern directions align
            if self._is_valid_confirmation(higher_tf_pattern, pattern):
                setup_id = f"{symbol}_{setup['timeframe']}_{higher_tf_pattern.id}"
                self.pending_setups[setup_id]['confirmed'] = True
                self.pending_setups[setup_id]['confirmation_type'] = pattern.pattern_type.value
                self.pending_setups[setup_id]['confirmation_pattern_id'] = pattern.id
                
                logger.info(f"TRADE SETUP COMPLETE: {higher_tf_pattern.data['direction']} sweep engulfing on "
                         f"{setup['timeframe']} confirmed by {pattern.pattern_type.value} on 5m for {symbol}")
    
    def _is_valid_confirmation(self, higher_tf_pattern: PatternState, 
                                    confirmation_pattern: PatternState) -> bool:
        """
        Check if a 5m confirmation pattern is valid for a higher timeframe sweep engulfing pattern.
        
        Args:
            higher_tf_pattern: The higher timeframe sweep engulfing pattern
            confirmation_pattern: The potential 5m confirmation pattern
            
        Returns:
            True if the confirmation is valid, False otherwise
        """
        # Directions must match (both bullish or both bearish)
        higher_tf_direction = higher_tf_pattern.data.get('direction')
        confirmation_direction = confirmation_pattern.data.get('direction')
        
        if higher_tf_direction != confirmation_direction:
            return False
            
        # Pattern must have occurred after the retracement
        retracement_time = higher_tf_pattern.data.get('retracement_time')
        confirmation_time = confirmation_pattern.start_time
        
        if retracement_time is None or confirmation_time < retracement_time:
            return False
            
        return True
    
    def get_confirmed_setups(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get confirmed trade setups, optionally filtered by symbol.
        
        Args:
            symbol: Symbol to filter by, or None for all symbols
            
        Returns:
            List of confirmed setup dictionaries
        """
        result = []
        
        for setup_id, setup in self.pending_setups.items():
            if setup['confirmed']:
                if symbol is None or setup['symbol'] == symbol:
                    result.append({
                        'symbol': setup['symbol'],
                        'timeframe': setup['timeframe'],
                        'direction': setup['pattern'].data['direction'],
                        'entry_time': datetime.now(),
                        'pattern_id': setup['pattern'].id,
                        'pattern_start_time': setup['pattern'].start_time,
                        'retracement_time': setup['pattern'].data.get('retracement_time'),
                        'confirmation_type': setup['confirmation_type'],
                        'confirmation_pattern_id': setup['confirmation_pattern_id']
                    })
                    
        return result
    
    def get_pending_setups(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get pending trade setups (retraced but not yet confirmed), optionally filtered by symbol.
        
        Args:
            symbol: Symbol to filter by, or None for all symbols
            
        Returns:
            List of pending setup dictionaries
        """
        result = []
        
        for setup_id, setup in self.pending_setups.items():
            if not setup['confirmed']:
                if symbol is None or setup['symbol'] == symbol:
                    result.append({
                        'symbol': setup['symbol'],
                        'timeframe': setup['timeframe'],
                        'direction': setup['pattern'].data['direction'],
                        'ready_since': setup['ready_since'],
                        'pattern_id': setup['pattern'].id,
                        'pattern_start_time': setup['pattern'].start_time
                    })
                    
        return result
    
    def _record_pattern(self, pattern_type: PatternType, timeframe: str, symbol: str, 
                      start_time: datetime, data: Dict[str, Any] = None, 
                      end_time: Optional[datetime] = None) -> PatternState:
        """
        Record a detected pattern.
        
        Args:
            pattern_type: Type of pattern detected
            timeframe: Timeframe the pattern was detected in
            symbol: Symbol the pattern was detected for
            start_time: Start time of the pattern
            data: Additional data about the pattern
            end_time: End time of the pattern (None if still active)
            
        Returns:
            The created PatternState object
        """
        pattern = PatternState(
            pattern_type=pattern_type,
            timeframe=timeframe,
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            data=data or {}
        )
        
        # Add to pattern list
        self.patterns[pattern_type.value][timeframe][symbol].append(pattern)
        
        # Add to active patterns if not completed
        if end_time is None:
            self.active_patterns[pattern.id] = pattern
            
        # Notify observers
        self._notify_pattern_detected(timeframe, symbol, pattern)
        
        logger.debug(f"Recorded {pattern_type.value} pattern for {symbol} on {timeframe}")
        
        return pattern
    
    def _notify_pattern_detected(self, timeframe: str, symbol: str, pattern: PatternState) -> None:
        """
        Notify observers that a pattern has been detected.
        
        Args:
            timeframe: Timeframe of the pattern
            symbol: Symbol of the pattern
            pattern: The detected pattern
        """
        # Call timeframe-specific observers
        for observer in self.observers[timeframe]['pattern_detected']:
            observer(timeframe, symbol, pattern)
        
        # Call global observers
        for observer in self.global_observers['pattern_detected']:
            observer(timeframe, symbol, pattern)
    
    def _notify_pattern_updated(self, timeframe: str, symbol: str, pattern: PatternState) -> None:
        """
        Notify observers that a pattern has been updated.
        
        Args:
            timeframe: Timeframe of the pattern
            symbol: Symbol of the pattern
            pattern: The updated pattern
        """
        # Call timeframe-specific observers
        for observer in self.observers[timeframe]['pattern_updated']:
            observer(timeframe, symbol, pattern)
        
        # Call global observers
        for observer in self.global_observers['pattern_updated']:
            observer(timeframe, symbol, pattern)
    
    def _notify_pattern_completed(self, timeframe: str, symbol: str, pattern: PatternState) -> None:
        """
        Notify observers that a pattern has been completed.
        
        Args:
            timeframe: Timeframe of the pattern
            symbol: Symbol of the pattern
            pattern: The completed pattern
        """
        # Remove from active patterns
        if pattern.id in self.active_patterns:
            del self.active_patterns[pattern.id]
            
        # Call timeframe-specific observers
        for observer in self.observers[timeframe]['pattern_completed']:
            observer(timeframe, symbol, pattern)
        
        # Call global observers
        for observer in self.global_observers['pattern_completed']:
            observer(timeframe, symbol, pattern)
    
    def register_observer(self, event_type: str, callback: Callable, 
                        timeframe: Optional[str] = None) -> None:
        """
        Register an observer for a specific event type and optionally a specific timeframe.
        
        Args:
            event_type: Type of event to observe 
                ('candle_complete', 'pattern_detected', 'pattern_updated', 'pattern_completed')
            callback: Callback function to call when the event occurs
            timeframe: Specific timeframe to observe, or None for all timeframes
        """
        with self.lock:
            if timeframe is None:
                # Register as global observer for all timeframes
                if event_type in self.global_observers:
                    self.global_observers[event_type].append(callback)
            else:
                # Register for specific timeframe
                if timeframe in self.observers and event_type in self.observers[timeframe]:
                    self.observers[timeframe][event_type].append(callback)
    
    def unregister_observer(self, event_type: str, callback: Callable, 
                          timeframe: Optional[str] = None) -> bool:
        """
        Unregister an observer.
        
        Args:
            event_type: Type of event the observer was registered for
            callback: The callback function to unregister
            timeframe: Specific timeframe, or None for global observers
            
        Returns:
            True if observer was successfully unregistered, False otherwise
        """
        with self.lock:
            if timeframe is None:
                # Unregister global observer
                if event_type in self.global_observers and callback in self.global_observers[event_type]:
                    self.global_observers[event_type].remove(callback)
                    return True
            else:
                # Unregister timeframe-specific observer
                if (timeframe in self.observers and 
                    event_type in self.observers[timeframe] and 
                    callback in self.observers[timeframe][event_type]):
                    self.observers[timeframe][event_type].remove(callback)
                    return True
                    
            return False
    
    def get_candles(self, timeframe: str, symbol: str, limit: int = None) -> List[Candle]:
        """
        Get candles for a specific timeframe and symbol.
        
        Args:
            timeframe: Timeframe to get candles for
            symbol: Symbol to get candles for
            limit: Maximum number of candles to return (most recent ones)
            
        Returns:
            List of Candle objects
        """
        with self.lock:
            candle_list = self.candles[timeframe][symbol]
            if limit:
                return candle_list[-limit:]
            return candle_list.copy()
    
    def get_active_patterns(self, pattern_type: Optional[PatternType] = None, 
                          timeframe: Optional[str] = None, 
                          symbol: Optional[str] = None) -> List[PatternState]:
        """
        Get active patterns, optionally filtered by type, timeframe, and/or symbol.
        
        Args:
            pattern_type: Pattern type to filter by, or None for all pattern types
            timeframe: Timeframe to filter by, or None for all timeframes
            symbol: Symbol to filter by, or None for all symbols
            
        Returns:
            List of active PatternState objects
        """
        with self.lock:
            result = []
            
            for pattern in self.active_patterns.values():
                # Apply filters
                if pattern_type and pattern.pattern_type != pattern_type:
                    continue
                if timeframe and pattern.timeframe != timeframe:
                    continue
                if symbol and pattern.symbol != symbol:
                    continue
                    
                result.append(pattern)
                
            return result
    
    def get_patterns_by_timeframe(self, timeframe: str, symbol: str, 
                               pattern_type: Optional[PatternType] = None,
                               include_completed: bool = False) -> List[PatternState]:
        """
        Get patterns for a specific timeframe and symbol.
        
        Args:
            timeframe: Timeframe to get patterns for
            symbol: Symbol to get patterns for
            pattern_type: Specific pattern type to get, or None for all types
            include_completed: Whether to include completed patterns
            
        Returns:
            List of PatternState objects
        """
        with self.lock:
            result = []
            
            if pattern_type:
                # Get patterns for specific type
                pattern_list = self.patterns[pattern_type.value][timeframe][symbol]
                for pattern in pattern_list:
                    if include_completed or pattern.end_time is None:
                        result.append(pattern)
            else:
                # Get patterns for all types
                for pattern_type_value in self.patterns:
                    pattern_list = self.patterns[pattern_type_value][timeframe][symbol]
                    for pattern in pattern_list:
                        if include_completed or pattern.end_time is None:
                            result.append(pattern)
                            
            return result
    
    def get_timeframe_interactions(self, symbol: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get information about how patterns on different timeframes interact for a symbol.
        
        This is useful for finding setups like "we're in a 4h fair value gap, now we want to see X on the 5m".
        
        Args:
            symbol: Symbol to analyze
            
        Returns:
            Dictionary mapping parent timeframe patterns to child timeframe patterns
        """
        with self.lock:
            result = {}
            
            # Get all active patterns for the symbol
            all_patterns = [p for p in self.active_patterns.values() if p.symbol == symbol]
            
            # Sort timeframes from higher to lower (e.g., 4h -> 1h -> 15m -> 5m -> 1m)
            timeframe_order = sorted(self.timeframes, 
                                    key=lambda tf: TIMEFRAME_MINUTES[tf], 
                                    reverse=True)
            
            # For each higher timeframe pattern
            for parent_tf in timeframe_order[:-1]:  # Skip the lowest timeframe
                parent_patterns = [p for p in all_patterns if p.timeframe == parent_tf]
                
                for parent_pattern in parent_patterns:
                    # Find child patterns in lower timeframes that occurred after the parent pattern
                    child_patterns = []
                    
                    for child_tf in timeframe_order[timeframe_order.index(parent_tf)+1:]:
                        # Get child patterns that started after the parent pattern
                        child_candidates = [
                            p for p in all_patterns 
                            if p.timeframe == child_tf and p.start_time >= parent_pattern.start_time
                        ]
                        
                        for child in child_candidates:
                            child_patterns.append({
                                'parent_pattern': parent_pattern,
                                'child_pattern': child,
                                'parent_timeframe': parent_tf,
                                'child_timeframe': child_tf,
                                'time_difference': (child.start_time - parent_pattern.start_time).total_seconds() / 60  # minutes
                            })
                    
                    if child_patterns:
                        pattern_key = f"{parent_pattern.pattern_type.value}_{parent_tf}_{parent_pattern.id}"
                        result[pattern_key] = child_patterns
                        
            return result

    def to_dataframe(self, timeframe: str, symbol: str) -> pd.DataFrame:
        """
        Convert candles for a specific timeframe and symbol to a pandas DataFrame.
        
        Args:
            timeframe: Timeframe to convert
            symbol: Symbol to convert
            
        Returns:
            pandas DataFrame with OHLCV data
        """
        candles = self.get_candles(timeframe, symbol)
        return self._candles_to_dataframe(candles)
        
    def process_candles(self, candles: pd.DataFrame, timeframe: str, symbol: str) -> None:
        """
        Process a batch of candles for a specific timeframe and symbol.
        
        This is useful for initializing historical data or when receiving batch updates.
        
        Args:
            candles: DataFrame containing OHLCV data
            timeframe: Timeframe of the candles
            symbol: Symbol of the candles
        """
        with self.lock:
            # Ensure required columns exist
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in candles.columns for col in required_cols):
                raise ValueError(f"Candles DataFrame must contain columns: {required_cols}")
                
            # Ensure symbol is being tracked
            if symbol not in self.symbols:
                self.add_symbol(symbol)
                
            # Convert to Candle objects
            candle_list = []
            for _, row in candles.iterrows():
                candle = Candle(
                    timestamp=row['timestamp'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume'],
                    completed=True  # Historical candles are always completed
                )
                candle_list.append(candle)
                
            # Replace existing candles for this timeframe and symbol
            self.candles[timeframe][symbol] = candle_list
            
            # Update last update time
            self.last_update_time[timeframe][symbol] = datetime.now()
            
            # Detect patterns if enabled
            if self.pattern_detection_enabled:
                self._detect_patterns(timeframe, symbol)
                
            logger.info(f"Processed {len(candle_list)} {timeframe} candles for {symbol}")


class MultiTimeframeObserver:
    """
    A base class for observers that need to react to events across multiple timeframes.
    
    This class provides utility methods for tracking and correlating patterns across
    different timeframes, which is useful for implementing strategies like
    "we're in a 4h fair value gap, now we want to see X on the 5m".
    """
    
    def __init__(self, candle_aggregator: CandleAggregator):
        """
        Initialize the multi-timeframe observer.
        
        Args:
            candle_aggregator: The CandleAggregator instance to observe
        """
        self.aggregator = candle_aggregator
        self.correlated_patterns = {}
        
    def register(self):
        """
        Register this observer with the candle aggregator for all relevant events.
        """
        # Register for pattern events across all timeframes
        self.aggregator.register_observer('pattern_detected', self.on_pattern_detected)
        self.aggregator.register_observer('pattern_completed', self.on_pattern_completed)
        
        # Register for candle events on specific timeframes if needed
        for timeframe in self.get_observed_timeframes():
            self.aggregator.register_observer('candle_complete', self.on_candle_complete, timeframe)
            
    def unregister(self):
        """
        Unregister this observer from the candle aggregator.
        """
        # Unregister pattern events
        self.aggregator.unregister_observer('pattern_detected', self.on_pattern_detected)
        self.aggregator.unregister_observer('pattern_completed', self.on_pattern_completed)
        
        # Unregister candle events
        for timeframe in self.get_observed_timeframes():
            self.aggregator.unregister_observer('candle_complete', self.on_candle_complete, timeframe)
    
    def get_observed_timeframes(self) -> List[str]:
        """
        Get the timeframes this observer is interested in.
        
        Override in subclasses to specify which timeframes to observe.
        
        Returns:
            List of timeframe strings
        """
        # Default implementation observes all timeframes
        return self.aggregator.timeframes
    
    def on_pattern_detected(self, timeframe: str, symbol: str, pattern: PatternState) -> None:
        """
        Called when a pattern is detected.
        
        Override in subclasses to implement custom behavior.
        
        Args:
            timeframe: Timeframe of the pattern
            symbol: Symbol of the pattern
            pattern: The detected pattern
        """
        pass
    
    def on_pattern_completed(self, timeframe: str, symbol: str, pattern: PatternState) -> None:
        """
        Called when a pattern is completed.
        
        Override in subclasses to implement custom behavior.
        
        Args:
            timeframe: Timeframe of the pattern
            symbol: Symbol of the pattern
            pattern: The completed pattern
        """
        pass
    
    def on_candle_complete(self, timeframe: str, symbol: str, candle: Candle) -> None:
        """
        Called when a candle is completed.
        
        Override in subclasses to implement custom behavior.
        
        Args:
            timeframe: Timeframe of the candle
            symbol: Symbol of the candle
            candle: The completed candle
        """
        pass
    
    def check_hierarchical_patterns(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Check for hierarchical patterns across timeframes.
        
        For example, finding a bullish pattern on the 5m inside a larger bearish pattern on the 4h.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            List of hierarchical pattern descriptions
        """
        results = []
        
        # Get interactions between patterns on different timeframes
        interactions = self.aggregator.get_timeframe_interactions(symbol)
        
        for parent_key, children in interactions.items():
            for child_info in children:
                parent_pattern = child_info['parent_pattern']
                child_pattern = child_info['child_pattern']
                
                # Check if the patterns have the relationship we're looking for
                if self.is_relevant_pattern_interaction(parent_pattern, child_pattern):
                    results.append({
                        'symbol': symbol,
                        'parent_pattern': {
                            'type': parent_pattern.pattern_type.value,
                            'timeframe': parent_pattern.timeframe,
                            'start_time': parent_pattern.start_time,
                            'data': parent_pattern.data
                        },
                        'child_pattern': {
                            'type': child_pattern.pattern_type.value,
                            'timeframe': child_pattern.timeframe,
                            'start_time': child_pattern.start_time,
                            'data': child_pattern.data
                        },
                        'description': self.describe_pattern_interaction(parent_pattern, child_pattern)
                    })
                    
        return results
    
    def is_relevant_pattern_interaction(self, parent_pattern: PatternState, 
                                    child_pattern: PatternState) -> bool:
        """
        Determine if an interaction between parent and child patterns is relevant.
        
        Override in subclasses to implement strategy-specific logic.
        
        Args:
            parent_pattern: The parent (higher timeframe) pattern
            child_pattern: The child (lower timeframe) pattern
            
        Returns:
            True if the interaction is relevant, False otherwise
        """
        # Default implementation considers all interactions relevant
        return True
    
    def describe_pattern_interaction(self, parent_pattern: PatternState, 
                                  child_pattern: PatternState) -> str:
        """
        Generate a human-readable description of a pattern interaction.
        
        Override in subclasses for strategy-specific descriptions.
        
        Args:
            parent_pattern: The parent (higher timeframe) pattern
            child_pattern: The child (lower timeframe) pattern
            
        Returns:
            Human-readable description of the interaction
        """
        return (f"{parent_pattern.pattern_type.value} on {parent_pattern.timeframe} "
                f"contains {child_pattern.pattern_type.value} on {child_pattern.timeframe}")


# Example usage:
if __name__ == "__main__":
    # Create a candle aggregator
    aggregator = CandleAggregator(
        symbols=["AAPL", "MSFT"],
        timeframes=[TimeFrame.M1.value, TimeFrame.M5.value, TimeFrame.M15.value, TimeFrame.H1.value, TimeFrame.H4.value, TimeFrame.D1.value]
    )
    
    # Example observer implementation
    class FairValueGapObserver(MultiTimeframeObserver):
        def __init__(self, aggregator):
            super().__init__(aggregator)
            
        def get_observed_timeframes(self):
            # Observing specific timeframes
            return [TimeFrame.M5.value, TimeFrame.H1.value, TimeFrame.H4.value]
            
        def on_pattern_detected(self, timeframe, symbol, pattern):
            if pattern.pattern_type == PatternType.FAIR_VALUE_GAP:
                print(f"Detected {pattern.data['direction']} FVG on {timeframe} for {symbol}")
                
                # Check if this is a lower timeframe pattern within a higher timeframe pattern
                if timeframe == TimeFrame.M5.value:
                    # Check for 4h patterns
                    h4_patterns = self.aggregator.get_patterns_by_timeframe(
                        TimeFrame.H4.value, symbol, PatternType.FAIR_VALUE_GAP)
                    
                    for h4_pattern in h4_patterns:
                        if h4_pattern.end_time is None:  # Active pattern
                            print(f"SETUP ALERT: 5m FVG within active 4h FVG for {symbol}")
    
    # Create and register observers
    fvg_observer = FairValueGapObserver(aggregator)
    fvg_observer.register()
    
    sweep_observer = SweepEngulfingMultiTFObserver(aggregator)
    sweep_observer.register()
    
    # Example of processing tick data
    tick_data = {
        'symbol': 'AAPL',
        'timestamp': datetime.now(),
        'price': 150.25,
        'volume': 100
    }
    
    # Process the tick
    aggregator.process_tick(tick_data)

    def _confirm_pattern_on_lower_timeframe(self, symbol: str, tf_parent: str, pattern_type: PatternType, 
                                        candle: Candle, metadata: Dict[str, Any]) -> None:
        """
        Confirm a pattern on a lower timeframe as a way to reduce false positives.
        
        Args:
            symbol: The symbol being analyzed
            tf_parent: The parent timeframe on which the pattern was initially detected
            pattern_type: The type of pattern that was detected
            candle: The candle associated with the pattern
            metadata: Additional metadata about the pattern
        """
        # Only handle sweep engulfing patterns for now
        if pattern_type.name != "SWEEP_ENGULFING":
            return
        
        # Only confirm patterns if we have the required timeframes
        if tf_parent not in self.timeframes or "5m" not in self.timeframes:
            return
        
        # Get direction from metadata
        direction = metadata.get("direction")
        if not direction:
            return
        
        # Check if we have a retracement already
        retracement = metadata.get("retracement", False)
        if not retracement:
            return
        
        # Perform 5-minute timeframe confirmation logic
        if self._check_5min_confirmation(symbol, candle, direction, metadata):
            # Create a copy of metadata with confirmation details
            confirmed_metadata = metadata.copy()
            confirmed_metadata["confirmation_type"] = metadata.get("confirmation_details", {}).get("type", "unknown")
            
            # Notify observers of the confirmed pattern
            for observer in self.observers:
                observer.on_pattern_detected(
                    PatternType.SWEEP_ENGULFING_CONFIRMED,
                    symbol,
                    tf_parent,
                    candle,
                    confirmed_metadata
                )
            
            logger.info(f"Confirmed {direction} sweep engulfing pattern for {symbol} on {tf_parent}")
