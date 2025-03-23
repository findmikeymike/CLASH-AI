#!/usr/bin/env python3
"""
Run Market Scanner

This script runs the IBKR single scan at regular intervals during market hours.
It's designed to be run as a background process or service.
"""
import os
import sys
import time
import argparse
import schedule
from datetime import datetime, timedelta
import pytz
from loguru import logger

# Import the single scan functionality
from ibkr_single_scan import run_single_scan

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/market_scanner_{time}.log", rotation="500 MB", level="DEBUG")

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
    now = datetime.now(EASTERN_TZ)
    
    # Check if it's a weekday (0 = Monday, 4 = Friday)
    if now.weekday() > 4:  # Saturday or Sunday
        return False
    
    # Check if it's within market hours
    market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
    market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
    
    return market_open <= now <= market_close

def run_scanner_job(
    symbols,
    timeframes,
    lookback_periods=50,
    min_volume_threshold=10000,
    price_rejection_threshold=0.005,
    fvg_threshold=0.003,
    min_touches=2,
    retest_threshold=0.005,
    retracement_threshold=0.33,
    duration="1 Y",
    force_run=False
):
    """
    Run the scanner job if the market is open or if force_run is True.
    
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
        duration: How far back to fetch data (e.g., "1 D", "1 W", "1 M", "1 Y")
        force_run: Whether to run the scanner even if the market is closed
    """
    # Check if market is open or if we're forcing a run
    if not is_market_open() and not force_run:
        logger.info("Market is closed. Skipping scan.")
        return
    
    logger.info(f"Running scanner at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the single scan
    result = run_single_scan(
        symbols=symbols,
        timeframes=timeframes,
        lookback_periods=lookback_periods,
        min_volume_threshold=min_volume_threshold,
        price_rejection_threshold=price_rejection_threshold,
        fvg_threshold=fvg_threshold,
        min_touches=min_touches,
        retest_threshold=retest_threshold,
        retracement_threshold=retracement_threshold,
        duration=duration
    )
    
    logger.info(f"Scan completed. Found {result['total_setups']} setups.")

def start_market_scanner(
    symbols,
    timeframes,
    interval_minutes=5,
    lookback_periods=50,
    min_volume_threshold=10000,
    price_rejection_threshold=0.005,
    fvg_threshold=0.003,
    min_touches=2,
    retest_threshold=0.005,
    retracement_threshold=0.33,
    duration="1 Y",
    scan_outside_market_hours=False,
    max_scans=None
):
    """
    Start the market scanner to run at regular intervals.
    
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
        duration: How far back to fetch data (e.g., "1 D", "1 W", "1 M", "1 Y")
        scan_outside_market_hours: Whether to run scans even when the market is closed
        max_scans: Maximum number of scans to run (for testing purposes)
    """
    logger.info(f"Starting market scanner with {len(symbols)} symbols on {len(timeframes)} timeframes")
    logger.info(f"Symbols: {', '.join(symbols)}")
    logger.info(f"Timeframes: {', '.join(timeframes)}")
    logger.info(f"Scan interval: {interval_minutes} minutes")
    if max_scans:
        logger.info(f"Maximum scans: {max_scans}")
    
    # Define the job to run
    def job():
        run_scanner_job(
            symbols=symbols,
            timeframes=timeframes,
            lookback_periods=lookback_periods,
            min_volume_threshold=min_volume_threshold,
            price_rejection_threshold=price_rejection_threshold,
            fvg_threshold=fvg_threshold,
            min_touches=min_touches,
            retest_threshold=retest_threshold,
            retracement_threshold=retracement_threshold,
            duration=duration,
            force_run=scan_outside_market_hours
        )
    
    # Schedule the job to run at the specified interval
    schedule.every(interval_minutes).minutes.do(job)
    
    # Run the job immediately once
    job()
    
    # Keep the script running
    logger.info(f"Market scanner running. Press Ctrl+C to stop.")
    
    # For testing purposes, limit the number of scans
    scan_count = 1  # Already ran once above
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
            
            # Check if we've reached the maximum number of scans
            if max_scans and schedule.jobs:
                pending_jobs = len(schedule.jobs)
                if schedule.jobs[0].next_run <= datetime.now() and scan_count < max_scans:
                    scan_count += 1
                    logger.info(f"Scan {scan_count} of {max_scans}")
                elif scan_count >= max_scans:
                    logger.info(f"Reached maximum number of scans ({max_scans}). Exiting.")
                    break
    except KeyboardInterrupt:
        logger.info("Scanner stopped by user.")

def main():
    """Main function to run the market scanner."""
    parser = argparse.ArgumentParser(description="Run the market scanner at regular intervals")
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
    parser.add_argument("--duration", type=str, default="1 Y",
                        help="How far back to fetch data (e.g., '1 D', '1 W', '1 M', '1 Y')")
    parser.add_argument("--scan-outside-market-hours", action="store_true",
                        help="Run scans even when the market is closed")
    parser.add_argument("--max-scans", type=int, default=None,
                        help="Maximum number of scans to run (for testing purposes)")
    
    args = parser.parse_args()
    
    # Start the market scanner
    start_market_scanner(
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
        duration=args.duration,
        scan_outside_market_hours=args.scan_outside_market_hours,
        max_scans=args.max_scans
    )
    
    return 0

if __name__ == "__main__":
    main() 