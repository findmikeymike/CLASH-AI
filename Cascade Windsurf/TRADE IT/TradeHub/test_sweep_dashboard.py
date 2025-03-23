#!/usr/bin/env python
"""
Test script for generating sweep engulfing patterns with confirmations
and displaying them in the dashboard.
"""
import time
import random
import datetime
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("Starting sweep engulfing dashboard test...")

# Import our pattern detection modules
from candle_aggregator import CandleAggregator, Candle, PatternType
from sweep_engulfer_agent import SweepEngulferPattern
from trading_agents.setup_observers.sweep_engulfing_observer import SweepEngulfingSetupObserver

def create_tick_data(symbol: str, price: float, volume: float = 1.0) -> Dict[str, Any]:
    """Create a tick data dictionary with timestamp."""
    return {
        "symbol": symbol,
        "price": price,
        "volume": volume,
        "timestamp": datetime.datetime.now().isoformat()
    }

def insert_bullish_sweep_engulfing(
    candles: list, 
    index: int, 
    engulf_ratio: float = 1.5, 
    sweep_size: float = 1.0
) -> list:
    """
    Insert a bullish sweep engulfing pattern at the specified index.
    
    Args:
        candles: List of candles to modify
        index: Index where to insert the pattern
        engulf_ratio: How much the candle should engulf the previous candle (> 1.0)
        sweep_size: How much the candle should sweep beyond the previous low
        
    Returns:
        Modified list of candles
    """
    if index < 1 or index >= len(candles):
        return candles
        
    # Get the previous candle
    prev_candle = candles[index - 1]
    
    # Calculate the body size of the previous candle
    prev_body_size = abs(prev_candle.close - prev_candle.open)
    
    # Create a bullish engulfing candle (green candle)
    # That sweeps the low and then closes above the previous candle's body high
    new_low = prev_candle.low - sweep_size
    new_open = new_low + (0.1 * sweep_size)  # Open slightly above the low
    
    if prev_candle.open > prev_candle.close:  # If previous candle is red
        new_close = prev_candle.open + (engulf_ratio * prev_body_size * 0.5)
    else:  # If previous candle is green
        new_close = prev_candle.close + (engulf_ratio * prev_body_size * 0.5)
    
    # Create the new candle
    new_candle = candles[index]._replace(
        open=new_open,
        close=new_close,
        high=new_close,
        low=new_low
    )
    
    # Replace the candle at the index
    candles[index] = new_candle
    
    # Create a retracement candle after the sweep
    if index + 1 < len(candles):
        retrace_amount = (new_close - new_low) * 0.4  # Retrace 40% of the range
        retrace_candle = candles[index + 1]._replace(
            open=new_close,
            close=new_close - retrace_amount,
            high=new_close + (retrace_amount * 0.1),
            low=new_close - retrace_amount
        )
        candles[index + 1] = retrace_candle
    
    # Create confirmation candlestick patterns on 5m timeframe
    # Here we would need to also manipulate 5m candles, but for this test
    # we'll rely on the fake confirmation in process_with_fake_confirmation
        
    return candles

def insert_bearish_sweep_engulfing(
    candles: list, 
    index: int, 
    engulf_ratio: float = 1.5, 
    sweep_size: float = 1.0
) -> list:
    """
    Insert a bearish sweep engulfing pattern at the specified index.
    
    Args:
        candles: List of candles to modify
        index: Index where to insert the pattern
        engulf_ratio: How much the candle should engulf the previous candle (> 1.0)
        sweep_size: How much the candle should sweep beyond the previous high
        
    Returns:
        Modified list of candles
    """
    if index < 1 or index >= len(candles):
        return candles
        
    # Get the previous candle
    prev_candle = candles[index - 1]
    
    # Calculate the body size of the previous candle
    prev_body_size = abs(prev_candle.close - prev_candle.open)
    
    # Create a bearish engulfing candle (red candle)
    # That sweeps the high and then closes below the previous candle's body low
    new_high = prev_candle.high + sweep_size
    new_open = new_high - (0.1 * sweep_size)  # Open slightly below the high
    
    if prev_candle.open < prev_candle.close:  # If previous candle is green
        new_close = prev_candle.open - (engulf_ratio * prev_body_size * 0.5)
    else:  # If previous candle is red
        new_close = prev_candle.close - (engulf_ratio * prev_body_size * 0.5)
    
    # Create the new candle
    new_candle = candles[index]._replace(
        open=new_open,
        close=new_close,
        high=new_high,
        low=new_close
    )
    
    # Replace the candle at the index
    candles[index] = new_candle
    
    # Create a retracement candle after the sweep
    if index + 1 < len(candles):
        retrace_amount = (new_high - new_close) * 0.4  # Retrace 40% of the range
        retrace_candle = candles[index + 1]._replace(
            open=new_close,
            close=new_close + retrace_amount,
            high=new_close + retrace_amount,
            low=new_close - (retrace_amount * 0.1)
        )
        candles[index + 1] = retrace_candle
    
    return candles

def generate_random_candles(num_candles: int = 50, base_price: float = 100.0, volatility: float = 1.0) -> list:
    """
    Generate a list of random candles for testing.
    
    Args:
        num_candles: Number of candles to generate
        base_price: Starting price for the first candle
        volatility: How volatile the price movements should be
        
    Returns:
        List of random candles
    """
    candles = []
    current_price = base_price
    timestamp = datetime.datetime.now() - datetime.timedelta(days=num_candles)
    
    for i in range(num_candles):
        # Generate a random price change
        price_change = random.normalvariate(0, volatility)
        
        # Determine if this will be an up or down candle
        if price_change > 0:
            open_price = current_price
            close_price = current_price + price_change
            high_price = close_price + random.uniform(0, price_change * 0.5)
            low_price = open_price - random.uniform(0, price_change * 0.3)
        else:
            open_price = current_price
            close_price = current_price + price_change
            high_price = open_price + random.uniform(0, -price_change * 0.3)
            low_price = close_price - random.uniform(0, -price_change * 0.5)
        
        # Ensure high is the highest and low is the lowest
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)
        
        # Create the candle
        candle = Candle(
            timestamp=timestamp + datetime.timedelta(days=i),
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=random.uniform(100, 1000)
        )
        
        candles.append(candle)
        current_price = close_price
    
    return candles

def process_with_fake_confirmation(aggregator: CandleAggregator, candles: list, symbol: str, timeframe: str):
    """
    Process the given candles through the aggregator and add fake confirmations.
    
    For real implementation, this would detect patterns properly using multiple timeframes,
    but for this test we'll just feed the candles and simulate confirmations.
    """
    for i, candle in enumerate(candles):
        # Process the candle as a completed candle
        aggregator.on_candle_completed(timeframe, symbol, candle)
        
        # Check if this is a pattern candle (just testing every 10th candle)
        if i > 0 and i % 10 == 0:
            # Alternate between bullish and bearish patterns
            direction = "bullish" if i % 20 == 0 else "bearish"
            
            # Fake metadata for the pattern
            metadata = {
                "direction": direction,
                "engulf_ratio": random.uniform(1.2, 3.0),
                "sweep_size": random.uniform(0.5, 2.0),
                "entry_price": candle.close,
                "stop_loss": candle.low - 1.0 if direction == "bullish" else candle.high + 1.0,
                "target": candle.close + 3.0 if direction == "bullish" else candle.close - 3.0,
                "retracement": True,
                "confidence": random.uniform(0.6, 0.95),
                "confirmation_details": {
                    "type": random.choice(["inverse_fair_value_gap", "change_of_character"])
                }
            }
            
            # Directly notify about a confirmed pattern
            for observer in aggregator.observers:
                observer.on_pattern_detected(
                    PatternType.SWEEP_ENGULFING_CONFIRMED,
                    symbol,
                    timeframe,
                    candle,
                    metadata
                )
            
            logger.info(f"Created fake confirmed {direction} sweep engulfing pattern for {symbol}")
            
            # Slow down to see patterns appear gradually
            time.sleep(0.5)

def run_test():
    """
    Run the test to generate and store sweep engulfing patterns.
    """
    # Create an aggregator
    aggregator = CandleAggregator()
    
    # Create and register the sweep engulfing setup observer
    observer = SweepEngulfingSetupObserver()
    aggregator.register_observer(observer)
    
    # Define symbols and timeframes
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    timeframes = ["15m", "1h", "4h"]
    
    # Process candles for each symbol and timeframe
    for symbol in symbols:
        for timeframe in timeframes:
            logger.info(f"Processing {symbol} on {timeframe} timeframe")
            
            # Generate random candles
            candles = generate_random_candles(
                num_candles=30, 
                base_price=random.uniform(50, 150),
                volatility=random.uniform(0.5, 2.0)
            )
            
            # Insert some bullish and bearish patterns
            if random.random() > 0.5:
                insert_bullish_sweep_engulfing(
                    candles, 
                    index=random.randint(5, 10),
                    engulf_ratio=random.uniform(1.5, 3.0),
                    sweep_size=random.uniform(0.5, 2.0)
                )
            
            if random.random() > 0.5:
                insert_bearish_sweep_engulfing(
                    candles, 
                    index=random.randint(15, 20),
                    engulf_ratio=random.uniform(1.5, 3.0),
                    sweep_size=random.uniform(0.5, 2.0)
                )
            
            # Process the candles with fake confirmations
            process_with_fake_confirmation(aggregator, candles, symbol, timeframe)
    
    logger.info("Test completed! Check the dashboard for confirmed sweep engulfing patterns.")

if __name__ == "__main__":
    run_test()
