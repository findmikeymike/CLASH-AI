#!/usr/bin/env python3
"""
IBKR Continuous Setup Scanner

This script implements a continuous scanner that uses Interactive Brokers (IBKR)
for data fetching and runs at regular intervals to detect trading setups.
"""
import os
import sys
import time
import argparse
import schedule
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Any, Optional
import pandas as pd
from loguru import logger

# Import the scanner functionality
from non_prefect_setup_scanner import (
    SimpleScanner,
    store_setups,
    setup_scanner_workflow
)

# Import IBKR connector
from trading_agents.utils.ibkr_connector import (
    fetch_historical_data as ibkr_fetch_data,
    is_market_open as ibkr_is_market_open,
    get_ib_connection,
    disconnect_ib,
    IBKR_AVAILABLE
)

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/ibkr_scanner_{time}.log", rotation="500 MB", level="DEBUG")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# US Market hours (Eastern Time)
MARKET_OPEN_HOUR = 9  # 9:30 AM ET
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16  # 4:00 PM ET
MARKET_CLOSE_MINUTE = 0
EASTERN_TZ = pytz.timezone('US/Eastern')

def is_market_open() -> bool:
    """
    Check if the US stock market is currently open.
    
    Returns:
        bool: True if the market is open, False otherwise
    """
    # Try to use IBKR to check if market is open
    if IBKR_AVAILABLE:
        return ibkr_is_market_open()
    
    # Fallback to time-based check
    now = datetime.now(EASTERN_TZ)
    
    # Check if it's a weekday (0 = Monday, 4 = Friday)
    if now.weekday() > 4:  # Saturday or Sunday
        return False
    
    # Check if it's within market hours
    market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
    market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
    
    return market_open <= now <= market_close

def fetch_market_data(symbol: str, timeframe: str, period: str = "1y") -> pd.DataFrame:
    """
    Fetch market data for a symbol and timeframe using IBKR.
    
    Args:
        symbol: The ticker symbol to fetch data for
        timeframe: The timeframe to fetch data for (e.g., 1D, 1H, 4H)
        period: The period to fetch data for (e.g., 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
    Returns:
        A pandas DataFrame with the market data
    """
    logger.info(f"Fetching data for {symbol} on {timeframe} timeframe using IBKR")
    
    # Convert period to IBKR duration format
    duration_map = {
        "1d": "1 D",
        "5d": "5 D",
        "1mo": "1 M",
        "3mo": "3 M",
        "6mo": "6 M",
        "1y": "1 Y",
        "2y": "2 Y",
        "5y": "5 Y",
        "10y": "10 Y",
        "ytd": "YTD",
        "max": "10 Y"  # Max in IBKR is limited, using 10Y as a reasonable maximum
    }
    
    duration = duration_map.get(period, "1 Y")  # Default to 1 year if not found
    
    # Try to fetch data from IBKR
    if IBKR_AVAILABLE:
        data = ibkr_fetch_data(symbol, timeframe, duration)
        
        if not data.empty:
            logger.info(f"Fetched {len(data)} data points for {symbol} from IBKR")
            return data
        else:
            logger.warning(f"No data returned from IBKR for {symbol}, falling back to Yahoo Finance")
    else:
        logger.warning("IBKR not available. Falling back to Yahoo Finance")
    
    # Fall back to Yahoo Finance if IBKR fails or isn't available
    from non_prefect_setup_scanner import fetch_market_data as yf_fetch_data
    return yf_fetch_data(symbol, timeframe, period)

def run_scanner(
    symbols: List[str],
    timeframes: List[str],
    lookback_periods: int = 50,
    min_volume_threshold: int = 10000,
    price_rejection_threshold: float = 0.005,
    fvg_threshold: float = 0.003,
    min_touches: int = 2,
    retest_threshold: float = 0.005,
    retracement_threshold: float = 0.33,
    period: str = "1y",
    force_run: bool = False
) -> Dict[str, Any]:
    """
    Run the scanner if the market is open or if force_run is True.
    
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
        force_run: Whether to run the scanner even if the market is closed
        
    Returns:
        Dictionary with summary of setups found
    """
    # Check if market is open or if we're forcing a run
    if not is_market_open() and not force_run:
        logger.info("Market is closed. Skipping scan.")
        return {"total_setups": 0, "market_open": False}
    
    logger.info(f"Running scanner at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
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
            
            # Fetch market data using IBKR
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
        "timestamp": datetime.now().isoformat(),
        "market_open": is_market_open()
    }

def start_continuous_scanner(
    symbols: List[str],
    timeframes: List[str],
    interval_minutes: int = 5,
    lookback_periods: int = 50,
    min_volume_threshold: int = 10000,
    price_rejection_threshold: float = 0.005,
    fvg_threshold: float = 0.003,
    min_touches: int = 2,
    retest_threshold: float = 0.005,
    retracement_threshold: float = 0.33,
    period: str = "1y",
    scan_outside_market_hours: bool = False
):
    """
    Start a continuous scanner that runs at regular intervals.
    
    Args:
        symbols: List of symbols to scan
        timeframes: List of timeframes to scan
        interval_minutes: How often to run the scanner (in minutes)
        lookback_periods: Number of periods to look back for pattern recognition
        min_volume_threshold: Minimum volume to consider a candle significant
        price_rejection_threshold: Threshold for price rejection
        fvg_threshold: Threshold for fair value gaps
        min_touches: Minimum touches to consider a level significant
        retest_threshold: Threshold for retest
        retracement_threshold: Threshold for retracement in sweeping engulfer patterns
        period: Period to fetch data for (e.g., 1d, 5d, 1mo, 1y, 2y)
        scan_outside_market_hours: Whether to run scans even when the market is closed
    """
    logger.info(f"Starting continuous scanner with {len(symbols)} symbols on {len(timeframes)} timeframes")
    logger.info(f"Symbols: {', '.join(symbols)}")
    logger.info(f"Timeframes: {', '.join(timeframes)}")
    logger.info(f"Scan interval: {interval_minutes} minutes")
    
    # Connect to IBKR if available
    if IBKR_AVAILABLE:
        ib = get_ib_connection()
        if ib is not None:
            logger.info("Successfully connected to IBKR")
        else:
            logger.warning("Failed to connect to IBKR, will use Yahoo Finance for data")
    
    # Define the job to run
    def job():
        run_scanner(
            symbols=symbols,
            timeframes=timeframes,
            lookback_periods=lookback_periods,
            min_volume_threshold=min_volume_threshold,
            price_rejection_threshold=price_rejection_threshold,
            fvg_threshold=fvg_threshold,
            min_touches=min_touches,
            retest_threshold=retest_threshold,
            retracement_threshold=retracement_threshold,
            period=period,
            force_run=scan_outside_market_hours
        )
    
    # Schedule the job to run at the specified interval
    schedule.every(interval_minutes).minutes.do(job)
    
    # Run the job immediately once
    job()
    
    # Keep the script running
    logger.info(f"Continuous scanner running. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scanner stopped by user.")
        # Disconnect from IBKR
        if IBKR_AVAILABLE:
            disconnect_ib()

def main():
    """Main function to run the continuous scanner."""
    parser = argparse.ArgumentParser(description="Run the continuous setup scanner with IBKR data")
    parser.add_argument("--symbols", type=str, nargs="+", default=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META"],
                        help="List of symbols to scan")
    parser.add_argument("--timeframes", type=str, nargs="+", default=["1D"],
                        help="List of timeframes to scan")
    parser.add_argument("--interval", type=int, default=5,
                        help="How often to run the scanner (in minutes)")
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
    parser.add_argument("--scan-outside-market-hours", action="store_true",
                        help="Run scans even when the market is closed")
    
    args = parser.parse_args()
    
    # Start the continuous scanner
    start_continuous_scanner(
        symbols=args.symbols,
        timeframes=args.timeframes,
        interval_minutes=args.interval,
        lookback_periods=args.lookback,
        min_volume_threshold=args.min_volume,
        price_rejection_threshold=args.price_rejection,
        fvg_threshold=args.fvg_threshold,
        min_touches=args.min_touches,
        retest_threshold=args.retest_threshold,
        retracement_threshold=args.retracement_threshold,
        period=args.period,
        scan_outside_market_hours=args.scan_outside_market_hours
    )
    
    return 0

if __name__ == "__main__":
    main() 