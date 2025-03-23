"""
Test script for the BreakerBlockAgent.

This script creates mock price data with clear support/resistance patterns,
breaker blocks, and retests to verify the BreakerBlockAgent's functionality.
"""

import asyncio
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from loguru import logger

from trading_agents.agents.breaker_block_agent import BreakerBlockAgent

def create_test_data_with_support_break_retest():
    """
    Create test data with a clear support level that breaks and then retests.
    """
    # Create sample OHLC data with support/resistance levels
    start_date = datetime.now() - timedelta(days=30)
    dates = pd.date_range(start=start_date, periods=100, freq='1h')
    
    # Create a clear pattern with support
    close_prices = [100] * 100  # Initial flat pattern
    
    # Create support level around 98
    support_level = 98
    
    # First touch of support
    for i in range(10, 15):
        close_prices[i] = support_level + 0.1
        
    # Second touch of support
    for i in range(25, 30):
        close_prices[i] = support_level + 0.1
        
    # Third touch of support (to ensure min_touches is met)
    for i in range(40, 45):
        close_prices[i] = support_level + 0.1
    
    # Break support level clearly
    for i in range(60, 70):
        close_prices[i] = support_level - 3  # Clear break
    
    # Continue lower to establish the break
    for i in range(70, 80):
        close_prices[i] = support_level - 5
        
    # Retest the broken support from below
    for i in range(85, 95):
        close_prices[i] = support_level - 0.2  # Just below the support level
    
    # Create DataFrame with clear pattern
    # Make sure highs and lows reflect the pattern too
    highs = []
    lows = []
    for p in close_prices:
        if p <= support_level + 0.5 and p >= support_level - 0.5:
            # Near support level - make lows touch the support
            highs.append(p + 1.5)
            lows.append(support_level)
        else:
            # Normal candle
            highs.append(p + 1)
            lows.append(p - 1)
    
    data = {
        'open': close_prices.copy(),
        'high': highs,
        'low': lows,
        'close': close_prices,
        'volume': np.random.normal(1000000, 200000, 100)
    }
    
    return pd.DataFrame(data, index=dates)

def create_test_data_with_resistance_break_retest():
    """
    Create test data with a clear resistance level that breaks and then retests.
    """
    # Create sample OHLC data with support/resistance levels
    start_date = datetime.now() - timedelta(days=30)
    dates = pd.date_range(start=start_date, periods=100, freq='1h')
    
    # Create a clear pattern with resistance
    close_prices = [100] * 100  # Initial flat pattern
    
    # Create resistance level around 102
    resistance_level = 102
    
    # First touch of resistance
    for i in range(10, 15):
        close_prices[i] = resistance_level - 0.1
    
    # Second touch of resistance
    for i in range(25, 30):
        close_prices[i] = resistance_level - 0.1
        
    # Third touch of resistance (to ensure min_touches is met)
    for i in range(40, 45):
        close_prices[i] = resistance_level - 0.1
    
    # Break resistance level clearly
    for i in range(60, 70):
        close_prices[i] = resistance_level + 3  # Clear break
    
    # Continue higher to establish the break
    for i in range(70, 80):
        close_prices[i] = resistance_level + 5
        
    # Retest the broken resistance from above
    for i in range(85, 95):
        close_prices[i] = resistance_level + 0.2  # Just above the resistance level
    
    # Create DataFrame with clear pattern
    # Make sure highs and lows reflect the pattern too
    highs = []
    lows = []
    for p in close_prices:
        if p >= resistance_level - 0.5 and p <= resistance_level + 0.5:
            # Near resistance level - make highs touch the resistance
            highs.append(resistance_level)
            lows.append(p - 1.5)
        else:
            # Normal candle
            highs.append(p + 1)
            lows.append(p - 1)
    
    data = {
        'open': close_prices.copy(),
        'high': highs,
        'low': lows,
        'close': close_prices,
        'volume': np.random.normal(1000000, 200000, 100)
    }
    
    return pd.DataFrame(data, index=dates)

def plot_test_data(df, ticker, breaker_blocks=None, active_retests=None):
    """Plot the test data with breaker blocks and retests."""
    plt.figure(figsize=(12, 8))
    
    # Plot OHLC data
    plt.plot(df.index, df['close'], label='Close Price')
    plt.plot(df.index, df['high'], 'g-', alpha=0.3)
    plt.plot(df.index, df['low'], 'r-', alpha=0.3)
    
    # Mark breaker blocks on the chart
    if breaker_blocks:
        for block in breaker_blocks:
            block_mid = (block.high + block.low) / 2
            color = 'g' if block.direction == 'bullish' else 'r'
            plt.axhspan(block.low, block.high, alpha=0.2, color=color)
            plt.text(df.index[60], block_mid, f"{block.direction} breaker", 
                    color=color, fontweight='bold')
    
    # Mark active retests on the chart
    if active_retests:
        for retest in active_retests:
            retest_mid = (retest.high + retest.low) / 2
            color = 'g' if retest.direction == 'bullish' else 'r'
            plt.scatter(df.index[-1], retest_mid, marker='*', s=200, color=color)
            plt.text(df.index[-5], retest_mid, f"Retest ({retest.direction})", 
                    color=color, fontweight='bold')
    
    plt.title(f"{ticker} Price Chart with Breaker Blocks and Retests")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{ticker}_breaker_analysis.png")
    logger.info(f"Saved chart as {ticker}_breaker_analysis.png")

def print_breaker_blocks(blocks):
    """Print detailed information about breaker blocks."""
    for i, block in enumerate(blocks):
        logger.info(f"Breaker Block {i+1}:")
        logger.info(f"  Direction: {block.direction}")
        logger.info(f"  Price Range: {block.low:.2f} - {block.high:.2f}")
        logger.info(f"  Strength: {block.strength:.2f}")
        logger.info(f"  Created At: {block.created_at}")
        logger.info(f"  Retested: {block.retested}")
        logger.info(f"  Retest Time: {block.retest_time}")
        logger.info(f"  Retest Price: {block.retest_price}")
        logger.info(f"  Notes: {block.notes}")

async def test_breaker_block_agent():
    """Test the BreakerBlockAgent with mock data."""
    logger.info("Starting BreakerBlockAgent test")
    
    # Initialize agent with more lenient settings for testing
    agent = BreakerBlockAgent(config={
        'min_touches': 2,  # Require at least 2 touches to consider a level significant
        'retest_threshold': 0.02  # 2% threshold for retest detection
    })
    
    # Test with support break and retest
    logger.info("\n=== Testing Support Break and Retest ===")
    support_df = create_test_data_with_support_break_retest()
    ticker = "SUPPORT_TEST"
    timeframe = "1h"
    
    logger.info(f"Processing {ticker} data...")
    
    # First run to establish breaker blocks
    logger.info("First run - Establishing breaker blocks...")
    first_result = await agent.process({
        "ticker": ticker,
        "timeframe": timeframe,
        "ohlc_data": support_df.iloc[:70]  # Only use data up to the break
    })
    
    logger.info(f"First run found {len(first_result.breaker_blocks)} breaker blocks")
    print_breaker_blocks(first_result.breaker_blocks)
    
    # Second run to detect retests
    logger.info("\nSecond run - Detecting retests...")
    second_result = await agent.process({
        "ticker": ticker,
        "timeframe": timeframe,
        "ohlc_data": support_df  # Use all data including retest
    })
    
    logger.info(f"Second run found {len(second_result.breaker_blocks)} breaker blocks")
    logger.info(f"Found {len(second_result.active_retests)} active retests")
    
    print_breaker_blocks(second_result.breaker_blocks)
    
    if second_result.active_retests:
        logger.info("\nActive Retests:")
        for retest in second_result.active_retests:
            logger.info(f"  Direction: {retest.direction}")
            logger.info(f"  Strength: {retest.strength:.2f}")
            logger.info(f"  Price Range: {retest.low:.2f} - {retest.high:.2f}")
            logger.info(f"  Notes: {retest.notes}")
    
    logger.info("\nAnalysis:")
    for key, value in second_result.analysis.items():
        logger.info(f"  {key}: {value}")
    
    # Plot the results
    plot_test_data(support_df, ticker, 
                  second_result.breaker_blocks, 
                  second_result.active_retests)
    
    # Test with resistance break and retest
    logger.info("\n=== Testing Resistance Break and Retest ===")
    resistance_df = create_test_data_with_resistance_break_retest()
    ticker = "RESISTANCE_TEST"
    
    logger.info(f"Processing {ticker} data...")
    
    # First run to establish breaker blocks
    logger.info("First run - Establishing breaker blocks...")
    first_result = await agent.process({
        "ticker": ticker,
        "timeframe": timeframe,
        "ohlc_data": resistance_df.iloc[:70]  # Only use data up to the break
    })
    
    logger.info(f"First run found {len(first_result.breaker_blocks)} breaker blocks")
    print_breaker_blocks(first_result.breaker_blocks)
    
    # Second run to detect retests
    logger.info("\nSecond run - Detecting retests...")
    second_result = await agent.process({
        "ticker": ticker,
        "timeframe": timeframe,
        "ohlc_data": resistance_df  # Use all data including retest
    })
    
    logger.info(f"Second run found {len(second_result.breaker_blocks)} breaker blocks")
    logger.info(f"Found {len(second_result.active_retests)} active retests")
    
    print_breaker_blocks(second_result.breaker_blocks)
    
    if second_result.active_retests:
        logger.info("\nActive Retests:")
        for retest in second_result.active_retests:
            logger.info(f"  Direction: {retest.direction}")
            logger.info(f"  Strength: {retest.strength:.2f}")
            logger.info(f"  Price Range: {retest.low:.2f} - {retest.high:.2f}")
            logger.info(f"  Notes: {retest.notes}")
    
    logger.info("\nAnalysis:")
    for key, value in second_result.analysis.items():
        logger.info(f"  {key}: {value}")
    
    # Plot the results
    plot_test_data(resistance_df, ticker, 
                  second_result.breaker_blocks, 
                  second_result.active_retests)
    
    logger.info("BreakerBlockAgent test completed")

if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(lambda msg: print(msg, flush=True), level="INFO")
    
    # Run the test
    asyncio.run(test_breaker_block_agent()) 