#!/usr/bin/env python
"""
Script to add test setup data to the database for development purposes.
"""
import random
import os
import sys
from datetime import datetime, timedelta
from trading_agents.utils.setup_storage import store_setup, get_setups

def create_test_setup(symbol, setup_type, direction, timeframe):
    """Create a test setup with realistic values based on inputs."""
    # Set a base price appropriate for the symbol
    base_prices = {
        "AAPL": 180.0,
        "MSFT": 390.0,
        "AMZN": 180.0,
        "GOOGL": 175.0,
        "META": 480.0,
        "NVDA": 870.0,
        "SPY": 510.0,
        "QQQ": 440.0
    }
    
    base_price = base_prices.get(symbol, 100.0)
    # Add some randomness to the price
    entry_price = round(base_price * (1 + random.uniform(-0.05, 0.05)), 2)
    
    # Set stop loss and target based on direction
    if direction == "bullish":
        stop_loss = round(entry_price * (1 - random.uniform(0.02, 0.05)), 2)
        target = round(entry_price * (1 + random.uniform(0.05, 0.15)), 2)
    else:
        stop_loss = round(entry_price * (1 + random.uniform(0.02, 0.05)), 2)
        target = round(entry_price * (1 - random.uniform(0.05, 0.15)), 2)
    
    # Calculate risk/reward
    risk = abs(entry_price - stop_loss)
    reward = abs(target - entry_price)
    risk_reward = round(reward / risk, 2) if risk > 0 else 0
    
    # Generate a date in the recent past
    days_ago = random.randint(0, 14)
    date_identified = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Create a complete setup dictionary
    setup = {
        "symbol": symbol,
        "setup_type": setup_type,
        "direction": direction,
        "timeframe": timeframe,
        "confidence": round(random.uniform(50, 95), 1),
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "target": target,
        "risk_reward": risk_reward,
        "date_identified": date_identified,
        "status": random.choice(["active", "triggered", "expired", "completed"]),
        "metadata": {
            "notes": f"Test setup for {symbol} {direction} {setup_type}",
            "tags": ["test", setup_type, direction, timeframe],
        }
    }
    
    return setup

def add_test_setups(count=10):
    """Add a specified number of test setups to the database."""
    symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "SPY", "QQQ"]
    setup_types = ["breakout", "reversal", "continuation", "pullback", "support", "resistance"]
    directions = ["bullish", "bearish"]
    timeframes = ["1h", "4h", "1d", "1w"]
    
    for _ in range(count):
        symbol = random.choice(symbols)
        setup_type = random.choice(setup_types)
        direction = random.choice(directions)
        timeframe = random.choice(timeframes)
        
        setup = create_test_setup(symbol, setup_type, direction, timeframe)
        setup_id = store_setup(setup)
        print(f"Added setup {setup_id}: {symbol} {direction} {setup_type} on {timeframe} timeframe")
    
    # List the setups we just added
    setups = get_setups(limit=count)
    print(f"\nRetrieved {len(setups)} newest setups from database:")
    for s in setups:
        print(f"ID {s['id']}: {s['symbol']} {s['direction']} {s['setup_type']} ({s['status']})")

if __name__ == "__main__":
    # Get the number of setups to add from command line argument, default to 10
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    add_test_setups(count) 