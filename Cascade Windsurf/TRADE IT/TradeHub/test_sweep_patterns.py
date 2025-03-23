#!/usr/bin/env python
# Test script for sweep engulfing pattern detection and confirmation

import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from candle_aggregator import CandleAggregator, Candle, TimeFrame, SweepEngulfingMultiTFObserver
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_sweep_patterns')

def generate_mock_data() -> Dict[str, pd.DataFrame]:
    """Generate mock data with known patterns."""
    # Create timestamp index
    now = datetime.now()
    daily_dates = pd.date_range(end=now, periods=30, freq='D')
    h4_dates = pd.date_range(end=now, periods=180, freq='4H')
    m5_dates = pd.date_range(end=now, periods=1000, freq='5min')
    
    # Create sample data frames
    daily_data = pd.DataFrame({
        'timestamp': daily_dates,
        'open': np.random.normal(100, 2, len(daily_dates)),
        'high': np.random.normal(102, 2, len(daily_dates)),
        'low': np.random.normal(98, 2, len(daily_dates)),
        'close': np.random.normal(101, 2, len(daily_dates)),
        'volume': np.random.normal(1000, 200, len(daily_dates))
    })
    
    h4_data = pd.DataFrame({
        'timestamp': h4_dates,
        'open': np.random.normal(100, 1, len(h4_dates)),
        'high': np.random.normal(101, 1, len(h4_dates)),
        'low': np.random.normal(99, 1, len(h4_dates)),
        'close': np.random.normal(100.5, 1, len(h4_dates)),
        'volume': np.random.normal(500, 100, len(h4_dates))
    })
    
    m5_data = pd.DataFrame({
        'timestamp': m5_dates,
        'open': np.random.normal(100, 0.5, len(m5_dates)),
        'high': np.random.normal(100.2, 0.5, len(m5_dates)),
        'low': np.random.normal(99.8, 0.5, len(m5_dates)),
        'close': np.random.normal(100.1, 0.5, len(m5_dates)),
        'volume': np.random.normal(100, 20, len(m5_dates))
    })
    
    # Insert a bullish sweep engulfing pattern in 4h data
    insert_bullish_sweep_engulfing(h4_data, 100)
    
    # Insert a bearish sweep engulfing pattern in daily data
    insert_bearish_sweep_engulfing(daily_data, 15)
    
    # Insert confirmation patterns in 5m data
    insert_change_of_character(m5_data, 500, direction='bullish')
    insert_inverse_fvg(m5_data, 600, direction='bearish')
    
    return {
        'daily': daily_data,
        '4h': h4_data,
        '5m': m5_data
    }

def insert_bullish_sweep_engulfing(df: pd.DataFrame, index: int) -> None:
    """Insert a bullish sweep engulfing pattern at the specified index."""
    # Ensure we have room
    if index >= len(df) - 3:
        index = len(df) - 4
    
    # Previous candle (to be engulfed)
    df.loc[df.index[index], 'open'] = 100.5
    df.loc[df.index[index], 'high'] = 101.2
    df.loc[df.index[index], 'low'] = 99.8
    df.loc[df.index[index], 'close'] = 100.0  # Slightly bearish
    
    # Sweep engulfing candle
    df.loc[df.index[index+1], 'open'] = 99.9  # Opens slightly bearish
    df.loc[df.index[index+1], 'high'] = 101.8  # High exceeds previous high
    df.loc[df.index[index+1], 'low'] = 99.5  # Sweeps below previous low
    df.loc[df.index[index+1], 'close'] = 101.5  # Closes above previous high (bullish engulfing)
    
    # First retracement candle
    df.loc[df.index[index+2], 'open'] = 101.3
    df.loc[df.index[index+2], 'high'] = 101.6
    df.loc[df.index[index+2], 'low'] = 100.8  # Retraces ~35% of the sweep engulfing candle
    df.loc[df.index[index+2], 'close'] = 101.0
    
    logger.info(f"Inserted bullish sweep engulfing pattern at index {index+1}")

def insert_bearish_sweep_engulfing(df: pd.DataFrame, index: int) -> None:
    """Insert a bearish sweep engulfing pattern at the specified index."""
    # Ensure we have room
    if index >= len(df) - 3:
        index = len(df) - 4
    
    # Previous candle (to be engulfed)
    df.loc[df.index[index], 'open'] = 99.5
    df.loc[df.index[index], 'high'] = 100.2
    df.loc[df.index[index], 'low'] = 98.8
    df.loc[df.index[index], 'close'] = 100.0  # Slightly bullish
    
    # Sweep engulfing candle
    df.loc[df.index[index+1], 'open'] = 100.1  # Opens slightly bullish
    df.loc[df.index[index+1], 'high'] = 100.5  # Sweeps above previous high
    df.loc[df.index[index+1], 'low'] = 98.2  # Low exceeds previous low
    df.loc[df.index[index+1], 'close'] = 98.5  # Closes below previous low (bearish engulfing)
    
    # First retracement candle
    df.loc[df.index[index+2], 'open'] = 98.7
    df.loc[df.index[index+2], 'high'] = 99.2  # Retraces ~35% of the sweep engulfing candle
    df.loc[df.index[index+2], 'low'] = 98.4
    df.loc[df.index[index+2], 'close'] = 99.0
    
    logger.info(f"Inserted bearish sweep engulfing pattern at index {index+1}")

def insert_change_of_character(df: pd.DataFrame, index: int, direction: str) -> None:
    """Insert a change of character pattern at the specified index."""
    # Ensure we have room
    if index >= len(df) - 10:
        index = len(df) - 11
    
    if direction == 'bullish':
        # Create a downtrend
        for i in range(index-5, index):
            df.loc[df.index[i], 'high'] = 100.0 - 0.1 * (index - i)
            df.loc[df.index[i], 'low'] = 99.0 - 0.1 * (index - i)
            df.loc[df.index[i], 'close'] = 99.5 - 0.1 * (index - i)
        
        # Change of character - bullish reversal
        df.loc[df.index[index], 'open'] = 98.8
        df.loc[df.index[index], 'high'] = 99.5
        df.loc[df.index[index], 'low'] = 98.7  # Higher low
        df.loc[df.index[index], 'close'] = 99.3  # Strong bullish candle
    else:
        # Create an uptrend
        for i in range(index-5, index):
            df.loc[df.index[i], 'high'] = 101.0 + 0.1 * (index - i)
            df.loc[df.index[i], 'low'] = 100.0 + 0.1 * (index - i)
            df.loc[df.index[i], 'close'] = 100.5 + 0.1 * (index - i)
        
        # Change of character - bearish reversal
        df.loc[df.index[index], 'open'] = 101.2
        df.loc[df.index[index], 'high'] = 101.3  # Lower high
        df.loc[df.index[index], 'low'] = 100.5
        df.loc[df.index[index], 'close'] = 100.7  # Strong bearish candle
    
    logger.info(f"Inserted {direction} change of character at index {index}")

def insert_inverse_fvg(df: pd.DataFrame, index: int, direction: str) -> None:
    """Insert an inverse fair value gap at the specified index."""
    # Ensure we have room
    if index >= len(df) - 10:
        index = len(df) - 11
    
    if direction == 'bullish':
        # Create a bearish FVG
        df.loc[df.index[index-3], 'open'] = 100.5
        df.loc[df.index[index-3], 'high'] = 101.0
        df.loc[df.index[index-3], 'low'] = 100.2
        df.loc[df.index[index-3], 'close'] = 100.3  # Bearish candle
        
        df.loc[df.index[index-2], 'open'] = 100.2
        df.loc[df.index[index-2], 'high'] = 100.3
        df.loc[df.index[index-2], 'low'] = 99.5
        df.loc[df.index[index-2], 'close'] = 99.7  # Bearish continuation
        
        # Create gap between candles (no overlap between this and previous)
        df.loc[df.index[index-1], 'open'] = 99.2
        df.loc[df.index[index-1], 'high'] = 99.3  # Gap between 99.3 and 99.5
        df.loc[df.index[index-1], 'low'] = 98.8
        df.loc[df.index[index-1], 'close'] = 99.0
        
        # Inverse FVG - bullish candle that closes the gap
        df.loc[df.index[index], 'open'] = 99.1
        df.loc[df.index[index], 'high'] = 99.8
        df.loc[df.index[index], 'low'] = 99.0
        df.loc[df.index[index], 'close'] = 99.6  # Bullish candle closing the gap
    else:
        # Create a bullish FVG
        df.loc[df.index[index-3], 'open'] = 99.5
        df.loc[df.index[index-3], 'high'] = 99.8
        df.loc[df.index[index-3], 'low'] = 99.0
        df.loc[df.index[index-3], 'close'] = 99.7  # Bullish candle
        
        df.loc[df.index[index-2], 'open'] = 99.8
        df.loc[df.index[index-2], 'high'] = 100.5
        df.loc[df.index[index-2], 'low'] = 99.7
        df.loc[df.index[index-2], 'close'] = 100.3  # Bullish continuation
        
        # Create gap between candles (no overlap between this and previous)
        df.loc[df.index[index-1], 'open'] = 100.7
        df.loc[df.index[index-1], 'high'] = 101.2
        df.loc[df.index[index-1], 'low'] = 100.7  # Gap between 100.5 and 100.7
        df.loc[df.index[index-1], 'close'] = 101.0
        
        # Inverse FVG - bearish candle that closes the gap
        df.loc[df.index[index], 'open'] = 100.9
        df.loc[df.index[index], 'high'] = 101.0
        df.loc[df.index[index], 'low'] = 100.2
        df.loc[df.index[index], 'close'] = 100.4  # Bearish candle closing the gap
    
    logger.info(f"Inserted {direction} inverse FVG at index {index}")

def test_sweep_engulfing_detection():
    """Test the sweep engulfing pattern detection in the CandleAggregator."""
    # Generate mock data
    mock_data = generate_mock_data()
    
    # Create candle aggregator with our test symbol
    symbol = "TEST"
    aggregator = CandleAggregator(
        symbols=[symbol],
        timeframes=[TimeFrame.M5.value, TimeFrame.H4.value, TimeFrame.D1.value]
    )
    
    # Initialize the observer
    observer = SweepEngulfingMultiTFObserver(aggregator)
    observer.register()
    
    # Feed data into the aggregator
    logger.info("Feeding daily data into aggregator...")
    aggregator.process_candles(mock_data['daily'], TimeFrame.D1.value, symbol)
    
    logger.info("Feeding 4h data into aggregator...")
    aggregator.process_candles(mock_data['4h'], TimeFrame.H4.value, symbol)
    
    logger.info("Feeding 5m data into aggregator...")
    aggregator.process_candles(mock_data['5m'], TimeFrame.M5.value, symbol)
    
    # Check for detected patterns
    logger.info("Checking for detected sweep engulfing patterns...")
    h4_patterns = aggregator.get_patterns_by_timeframe(
        TimeFrame.H4.value, symbol, include_completed=True)
    
    daily_patterns = aggregator.get_patterns_by_timeframe(
        TimeFrame.D1.value, symbol, include_completed=True)
    
    # Check for patterns that have been confirmed
    logger.info("Checking for confirmed setups...")
    confirmed_setups = observer.get_confirmed_setups(symbol)
    
    # Print results
    logger.info(f"Found {len(h4_patterns)} patterns on 4h timeframe")
    logger.info(f"Found {len(daily_patterns)} patterns on daily timeframe")
    logger.info(f"Found {len(confirmed_setups)} confirmed setups")
    
    # Print details of the sweep engulfing patterns
    for pattern in h4_patterns + daily_patterns:
        if hasattr(pattern, 'pattern_type') and pattern.pattern_type.value == 'sweep_engulfing':
            logger.info(f"Sweep Engulfing Pattern:")
            logger.info(f"  Timeframe: {pattern.timeframe}")
            logger.info(f"  Direction: {pattern.data.get('direction', 'unknown')}")
            logger.info(f"  Engulf Ratio: {pattern.data.get('engulf_ratio', 0):.2f}")
            logger.info(f"  Sweep Size: {pattern.data.get('sweep_size', 0):.2f}")
            logger.info(f"  Retracement Tracked: {pattern.data.get('retracement_tracked', False)}")
            
            if pattern.data.get('retracement_tracked', False):
                logger.info(f"  Retracement Time: {pattern.data.get('retracement_time')}")
    
    # Print details of confirmed setups
    for setup in confirmed_setups:
        logger.info(f"Confirmed Trade Setup:")
        logger.info(f"  Symbol: {setup['symbol']}")
        logger.info(f"  Timeframe: {setup['timeframe']}")
        logger.info(f"  Direction: {setup['direction']}")
        logger.info(f"  Confirmation Type: {setup['confirmation_type']}")
        
    return aggregator, observer, mock_data

def plot_patterns(mock_data, pattern_indices=None):
    """Plot the patterns for visual inspection."""
    # Create subplots
    fig, axs = plt.subplots(3, 1, figsize=(12, 15))
    
    # Plot daily data
    daily_df = mock_data['daily']
    axs[0].plot(daily_df.index, daily_df['close'], label='Daily Close')
    axs[0].scatter(daily_df.index, daily_df['high'], marker='^', color='green', s=50, label='High')
    axs[0].scatter(daily_df.index, daily_df['low'], marker='v', color='red', s=50, label='Low')
    axs[0].set_title('Daily Timeframe')
    axs[0].legend()
    
    # Plot 4h data
    h4_df = mock_data['4h']
    axs[1].plot(h4_df.index, h4_df['close'], label='4h Close')
    axs[1].scatter(h4_df.index, h4_df['high'], marker='^', color='green', s=30, label='High')
    axs[1].scatter(h4_df.index, h4_df['low'], marker='v', color='red', s=30, label='Low')
    axs[1].set_title('4h Timeframe')
    axs[1].legend()
    
    # Plot 5m data
    m5_df = mock_data['5m']
    # We'll just plot a subset to keep it readable
    subset = m5_df.iloc[400:700]
    axs[2].plot(subset.index, subset['close'], label='5m Close')
    axs[2].scatter(subset.index, subset['high'], marker='^', color='green', s=10, label='High')
    axs[2].scatter(subset.index, subset['low'], marker='v', color='red', s=10, label='Low')
    axs[2].set_title('5m Timeframe (Subset)')
    axs[2].legend()
    
    # Highlight pattern areas if provided
    if pattern_indices:
        if 'daily' in pattern_indices and pattern_indices['daily']:
            for idx in pattern_indices['daily']:
                axs[0].axvspan(idx-0.5, idx+2.5, alpha=0.2, color='yellow')
        
        if '4h' in pattern_indices and pattern_indices['4h']:
            for idx in pattern_indices['4h']:
                axs[1].axvspan(idx-0.5, idx+2.5, alpha=0.2, color='yellow')
        
        if '5m' in pattern_indices and pattern_indices['5m']:
            for idx in pattern_indices['5m']:
                if 400 <= idx <= 700:  # Only highlight in our plotted range
                    axs[2].axvspan(idx-0.5, idx+2.5, alpha=0.2, color='yellow')
    
    plt.tight_layout()
    plt.savefig('sweep_patterns_test.png')
    logger.info("Saved pattern visualization to 'sweep_patterns_test.png'")
    plt.close()

if __name__ == "__main__":
    logger.info("Starting sweep engulfing pattern test...")
    
    # Test detection
    aggregator, observer, mock_data = test_sweep_engulfing_detection()
    
    # Plot patterns
    pattern_indices = {
        'daily': [15],  # Where we inserted the bearish pattern
        '4h': [100],    # Where we inserted the bullish pattern
        '5m': [500, 600]  # Where we inserted confirmations
    }
    plot_patterns(mock_data, pattern_indices)
    
    logger.info("Test completed.")
