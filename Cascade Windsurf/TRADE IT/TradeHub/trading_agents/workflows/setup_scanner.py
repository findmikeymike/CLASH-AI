"""
Setup scanner workflow that identifies and stores trading setups.
"""
from prefect import flow, task
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import yfinance as yf
from loguru import logger

from ..agents.scanner_agent import BreakerBlockScanner, BreakoutSetup
from ..utils.setup_storage import store_setup
from ..utils.data_fetcher import fetch_historical_data

@task(name="Identify Breakout Setups")
def identify_breakout_setups(
    symbol: str,
    timeframe: str,
    data: pd.DataFrame
) -> List[Dict[str, Any]]:
    """
    Identify breakout setups from market data.
    
    Args:
        symbol: The ticker symbol
        timeframe: The timeframe of the data
        data: The market data as a pandas DataFrame
        
    Returns:
        A list of setup dictionaries
    """
    logger.info(f"Scanning for breakout setups in {symbol} on {timeframe} timeframe")
    
    # Initialize the scanner
    scanner = BreakerBlockScanner(
        lookback_periods=50,
        min_volume_threshold=10000,
        price_rejection_threshold=0.005,
        fvg_threshold=0.003
    )
    
    # Find breaker blocks and fair value gaps
    breaker_blocks = scanner.find_breaker_blocks(data)
    fair_value_gaps = scanner.find_fair_value_gaps(data)
    
    logger.info(f"Found {len(breaker_blocks)} breaker blocks and {len(fair_value_gaps)} fair value gaps")
    
    # Identify potential setups
    setups = []
    
    # Process breaker blocks for potential setups
    for block in breaker_blocks:
        # Check if price is approaching the breaker block
        current_price = data.iloc[-1]['close']
        block_price = block['price']
        
        # Determine direction (bullish or bearish)
        direction = "bullish" if block['direction'] > 0 else "bearish"
        
        # Calculate distance to breaker block as percentage
        distance_pct = abs(current_price - block_price) / current_price
        
        # If price is within 2% of the breaker block, consider it a potential setup
        if distance_pct < 0.02:
            # Calculate risk/reward based on ATR or a fixed percentage
            atr = data['high'].rolling(14).max() - data['low'].rolling(14).min()
            avg_atr = atr.mean()
            
            # Set stop loss and target based on direction and ATR
            if direction == "bullish":
                entry_price = block_price
                stop_loss = entry_price - avg_atr
                target = entry_price + (2 * avg_atr)  # 2:1 risk/reward
            else:
                entry_price = block_price
                stop_loss = entry_price + avg_atr
                target = entry_price - (2 * avg_atr)  # 2:1 risk/reward
            
            # Calculate risk/reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(target - entry_price)
            risk_reward = reward / risk if risk > 0 else 0
            
            # Create setup dictionary
            setup = {
                "symbol": symbol,
                "setup_type": "Breaker Block Retest",
                "direction": direction,
                "timeframe": timeframe,
                "confidence": 0.8,  # High confidence for breaker block retests
                "entry_price": float(entry_price),
                "stop_loss": float(stop_loss),
                "target": float(target),
                "risk_reward": float(risk_reward),
                "date_identified": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "active",
                "metadata": {
                    "breaker_block": block,
                    "current_price": float(current_price),
                    "distance_pct": float(distance_pct),
                    "atr": float(avg_atr)
                }
            }
            
            setups.append(setup)
    
    # Process fair value gaps for potential setups
    for gap in fair_value_gaps:
        # Check if price is approaching the fair value gap
        current_price = data.iloc[-1]['close']
        gap_high = gap['high']
        gap_low = gap['low']
        
        # Determine if price is above or below the gap
        if current_price < gap_low:
            direction = "bullish"  # Price might move up to fill the gap
            distance_pct = (gap_low - current_price) / current_price
        elif current_price > gap_high:
            direction = "bearish"  # Price might move down to fill the gap
            distance_pct = (current_price - gap_high) / current_price
        else:
            # Price is already within the gap, not a setup
            continue
        
        # If price is within 2% of the gap, consider it a potential setup
        if distance_pct < 0.02:
            # Calculate risk/reward based on ATR or a fixed percentage
            atr = data['high'].rolling(14).max() - data['low'].rolling(14).min()
            avg_atr = atr.mean()
            
            # Set entry, stop loss and target based on direction and gap
            if direction == "bullish":
                entry_price = gap_low
                stop_loss = entry_price - avg_atr
                target = gap_high  # Target is the top of the gap
            else:
                entry_price = gap_high
                stop_loss = entry_price + avg_atr
                target = gap_low  # Target is the bottom of the gap
            
            # Calculate risk/reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(target - entry_price)
            risk_reward = reward / risk if risk > 0 else 0
            
            # Create setup dictionary
            setup = {
                "symbol": symbol,
                "setup_type": "Fair Value Gap Fill",
                "direction": direction,
                "timeframe": timeframe,
                "confidence": 0.7,  # Moderate confidence for FVG fills
                "entry_price": float(entry_price),
                "stop_loss": float(stop_loss),
                "target": float(target),
                "risk_reward": float(risk_reward),
                "date_identified": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "active",
                "metadata": {
                    "fair_value_gap": gap,
                    "current_price": float(current_price),
                    "distance_pct": float(distance_pct),
                    "atr": float(avg_atr)
                }
            }
            
            setups.append(setup)
    
    logger.info(f"Identified {len(setups)} potential setups for {symbol}")
    return setups

@task(name="Store Setups")
def store_setups(setups: List[Dict[str, Any]]) -> List[int]:
    """
    Store identified setups in the database.
    
    Args:
        setups: A list of setup dictionaries
        
    Returns:
        A list of setup IDs
    """
    setup_ids = []
    
    for setup in setups:
        try:
            setup_id = store_setup(setup)
            setup_ids.append(setup_id)
        except Exception as e:
            logger.error(f"Error storing setup: {str(e)}")
    
    logger.info(f"Stored {len(setup_ids)} setups in the database")
    return setup_ids

@flow(name="Setup Scanner Workflow")
def setup_scanner_workflow(
    symbols: List[str] = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA"],
    timeframes: List[str] = ["1D", "4H", "1H"]
) -> Dict[str, Any]:
    """
    Main workflow for scanning and identifying trading setups.
    
    Args:
        symbols: List of symbols to scan
        timeframes: List of timeframes to scan
        
    Returns:
        A dictionary with the results of the scan
    """
    logger.info(f"Starting setup scanner workflow for {len(symbols)} symbols on {len(timeframes)} timeframes")
    
    all_setups = []
    
    # Scan each symbol and timeframe
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                # Convert data to pandas DataFrame
                raw_data = fetch_historical_data(symbol, timeframe, limit=200)
                
                # Convert to pandas DataFrame
                df = pd.DataFrame(raw_data)
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
                
                # Identify setups
                setups = identify_breakout_setups(symbol, timeframe, df)
                
                # Store setups
                if setups:
                    setup_ids = store_setups(setups)
                    all_setups.extend(setups)
            
            except Exception as e:
                logger.error(f"Error scanning {symbol} on {timeframe}: {str(e)}")
    
    logger.info(f"Setup scanner workflow completed. Identified {len(all_setups)} setups.")
    
    return {
        "total_setups": len(all_setups),
        "setups": all_setups,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Run the workflow with default settings
    setup_scanner_workflow() 