#!/usr/bin/env python
# Simple test script for sweep engulfing pattern detection

import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sweep_engulfer_agent import SweepEngulferPattern

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_sweep_simple')

def generate_mock_data() -> pd.DataFrame:
    """Generate mock data with known patterns."""
    # Create timestamp index
    now = datetime.now()
    dates = pd.date_range(end=now, periods=50, freq='D')
    
    # Create sample data frames
    data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.normal(100, 2, len(dates)),
        'high': np.random.normal(102, 2, len(dates)),
        'low': np.random.normal(98, 2, len(dates)),
        'close': np.random.normal(101, 2, len(dates)),
        'volume': np.random.normal(1000, 200, len(dates))
    })
    
    data.set_index('timestamp', inplace=True)
    
    # Insert a bullish sweep engulfing pattern
    insert_bullish_sweep_engulfing(data, 20)
    
    # Insert a bearish sweep engulfing pattern
    insert_bearish_sweep_engulfing(data, 35)
    
    return data

def insert_bullish_sweep_engulfing(df: pd.DataFrame, index: int) -> None:
    """Insert a bullish sweep engulfing pattern at the specified index."""
    # Previous candle (to be engulfed)
    df.iloc[index-1, df.columns.get_loc('open')] = 100.5
    df.iloc[index-1, df.columns.get_loc('high')] = 101.2
    df.iloc[index-1, df.columns.get_loc('low')] = 99.8
    df.iloc[index-1, df.columns.get_loc('close')] = 100.0  # Slightly bearish
    
    # Sweep engulfing candle
    df.iloc[index, df.columns.get_loc('open')] = 99.9  # Opens slightly bearish
    df.iloc[index, df.columns.get_loc('high')] = 101.8  # High exceeds previous high
    df.iloc[index, df.columns.get_loc('low')] = 99.5  # Sweeps below previous low
    df.iloc[index, df.columns.get_loc('close')] = 101.5  # Closes above previous high (bullish engulfing)
    
    # First retracement candle
    df.iloc[index+1, df.columns.get_loc('open')] = 101.3
    df.iloc[index+1, df.columns.get_loc('high')] = 101.6
    df.iloc[index+1, df.columns.get_loc('low')] = 100.8  # Retraces ~35% of the sweep engulfing candle
    df.iloc[index+1, df.columns.get_loc('close')] = 101.0
    
    logger.info(f"Inserted bullish sweep engulfing pattern at index {index}")

def insert_bearish_sweep_engulfing(df: pd.DataFrame, index: int) -> None:
    """Insert a bearish sweep engulfing pattern at the specified index."""
    # Previous candle (to be engulfed)
    df.iloc[index-1, df.columns.get_loc('open')] = 99.5
    df.iloc[index-1, df.columns.get_loc('high')] = 100.2
    df.iloc[index-1, df.columns.get_loc('low')] = 98.8
    df.iloc[index-1, df.columns.get_loc('close')] = 100.0  # Slightly bullish
    
    # Sweep engulfing candle
    df.iloc[index, df.columns.get_loc('open')] = 100.1  # Opens slightly bullish
    df.iloc[index, df.columns.get_loc('high')] = 100.5  # Sweeps above previous high
    df.iloc[index, df.columns.get_loc('low')] = 98.2  # Low exceeds previous low
    df.iloc[index, df.columns.get_loc('close')] = 98.5  # Closes below previous low (bearish engulfing)
    
    # First retracement candle
    df.iloc[index+1, df.columns.get_loc('open')] = 98.7
    df.iloc[index+1, df.columns.get_loc('high')] = 99.2  # Retraces ~35% of the sweep engulfing candle
    df.iloc[index+1, df.columns.get_loc('low')] = 98.4
    df.iloc[index+1, df.columns.get_loc('close')] = 99.0
    
    logger.info(f"Inserted bearish sweep engulfing pattern at index {index}")

def test_sweep_engulfing_detection():
    """Test the sweep engulfing pattern detection."""
    # Generate mock data
    data = generate_mock_data()
    
    # Create pattern detector
    detector = SweepEngulferPattern(
        engulfing_threshold=1.0,  # Full engulfing
        sweep_threshold_pips=0.1,  # Small threshold for testing
        min_retracement=0.33       # 1/3 retracement
    )
    
    # Detect patterns
    results = detector.detect_patterns(data)
    
    # Check for detected patterns
    bullish_patterns = results[results['bullish_sweep_engulfing'] == True]
    bearish_patterns = results[results['bearish_sweep_engulfing'] == True]
    
    logger.info(f"Found {len(bullish_patterns)} bullish sweep engulfing patterns")
    logger.info(f"Found {len(bearish_patterns)} bearish sweep engulfing patterns")
    
    # Print pattern details
    for idx, row in bullish_patterns.iterrows():
        logger.info(f"Bullish Sweep Engulfing at {idx}:")
        logger.info(f"  Engulf Ratio: {row['engulf_ratio']:.2f}")
        logger.info(f"  Sweep Size: {row['sweep_size']:.2f}")
        
        # Test retracement detection
        retraced = detector.check_retracement(data, data.index.get_loc(idx), 'bullish')
        logger.info(f"  Retracement detected: {retraced}")
    
    for idx, row in bearish_patterns.iterrows():
        logger.info(f"Bearish Sweep Engulfing at {idx}:")
        logger.info(f"  Engulf Ratio: {row['engulf_ratio']:.2f}")
        logger.info(f"  Sweep Size: {row['sweep_size']:.2f}")
        
        # Test retracement detection
        retraced = detector.check_retracement(data, data.index.get_loc(idx), 'bearish')
        logger.info(f"  Retracement detected: {retraced}")
    
    return data, results

def plot_patterns(data, results):
    """Plot the patterns for visual inspection."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot close prices
    ax.plot(data.index, data['close'], label='Close')
    
    # Highlight bullish patterns
    bullish_indices = results[results['bullish_sweep_engulfing'] == True].index
    bearish_indices = results[results['bearish_sweep_engulfing'] == True].index
    
    # Plot high and low
    ax.scatter(data.index, data['high'], marker='^', color='green', s=30, label='High')
    ax.scatter(data.index, data['low'], marker='v', color='red', s=30, label='Low')
    
    # Highlight pattern areas
    for idx in bullish_indices:
        idx_loc = data.index.get_loc(idx)
        # Ensure we don't go out of bounds
        prev_idx = max(0, idx_loc-1)
        next_idx = min(len(data.index)-1, idx_loc+1)
        # Highlight the pattern and the candle before it
        ax.axvspan(data.index[prev_idx], data.index[next_idx], alpha=0.2, color='green', 
                  label='Bullish Pattern' if idx == bullish_indices[0] else "")
    
    for idx in bearish_indices:
        idx_loc = data.index.get_loc(idx)
        # Ensure we don't go out of bounds
        prev_idx = max(0, idx_loc-1)
        next_idx = min(len(data.index)-1, idx_loc+1)
        # Highlight the pattern and the candle before it
        ax.axvspan(data.index[prev_idx], data.index[next_idx], alpha=0.2, color='red',
                  label='Bearish Pattern' if idx == bearish_indices[0] else "")
    
    ax.set_title('Sweep Engulfing Patterns Detection')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('sweep_patterns_simple_test.png')
    logger.info("Saved pattern visualization to 'sweep_patterns_simple_test.png'")
    plt.close()

if __name__ == "__main__":
    logger.info("Starting sweep engulfing pattern simple test...")
    
    # Test detection
    data, results = test_sweep_engulfing_detection()
    
    # Plot patterns
    plot_patterns(data, results)
    
    logger.info("Test completed.")
