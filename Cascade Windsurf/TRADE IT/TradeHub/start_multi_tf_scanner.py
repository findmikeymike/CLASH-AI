#!/usr/bin/env python3
"""
Start Multi-Timeframe Scanner

This script provides a convenient way to start the multi-timeframe scanner with predefined
symbols and timeframes.
"""
import os
import sys
import argparse
import subprocess
from datetime import datetime
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/start_multi_tf_scanner_{time}.log", rotation="500 MB", level="DEBUG")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Default symbols to scan
DEFAULT_SYMBOLS = {
    "tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "AMD", "INTC", "CSCO", "ORCL"],
    "financial": ["JPM", "BAC", "C", "GS", "MS", "V", "MA", "AXP", "BLK", "WFC"],
    "consumer": ["PG", "KO", "PEP", "WMT", "COST", "MCD", "NKE", "SBUX", "DIS", "HD"],
    "healthcare": ["JNJ", "PFE", "MRK", "UNH", "ABT", "TMO", "LLY", "ABBV", "BMY", "AMGN"],
    "energy": ["XOM", "CVX", "COP", "EOG", "SLB"]
}

# Default timeframe combinations for multi-timeframe setups
DEFAULT_TF_COMBINATIONS = {
    "fvg_sweep_engulfer": ["4H", "15m"],
    "breaker_block_mss": ["1D", "1H"],
    "fvg_sweeping_engulfer": ["1H", "15m"],
    "all": ["1D", "4H", "1H", "30m", "15m", "5m"]
}

def start_scanner(
    symbols=None,
    tf_combination="all",
    interval=5,
    duration="1 M",
    scan_outside_market_hours=False,
    max_scans=None
):
    """
    Start the multi-timeframe scanner with the specified parameters.
    
    Args:
        symbols: List of symbols to scan (None for all default symbols)
        tf_combination: Timeframe combination to use (key from DEFAULT_TF_COMBINATIONS)
        interval: Interval between scans in minutes
        duration: How far back to fetch data (e.g., "1 D", "1 W", "1 M", "1 Y")
        scan_outside_market_hours: Whether to scan outside market hours
        max_scans: Maximum number of scans to run (None for unlimited)
    """
    # Use all default symbols if none specified
    if symbols is None:
        symbols = []
        for category in DEFAULT_SYMBOLS.values():
            symbols.extend(category)
    
    # Get timeframes for the specified combination
    if tf_combination in DEFAULT_TF_COMBINATIONS:
        timeframes = DEFAULT_TF_COMBINATIONS[tf_combination]
    else:
        logger.error(f"Unknown timeframe combination: {tf_combination}")
        logger.info(f"Available combinations: {', '.join(DEFAULT_TF_COMBINATIONS.keys())}")
        return
    
    # Build command to run the scanner
    cmd = ["python", "multi_timeframe_scanner.py"]
    cmd.extend(["--symbols"] + symbols)
    cmd.extend(["--timeframes"] + timeframes)
    cmd.extend(["--interval", str(interval)])
    cmd.extend(["--duration", duration])
    
    if scan_outside_market_hours:
        cmd.append("--scan-outside-market-hours")
    
    if max_scans:
        cmd.extend(["--max-scans", str(max_scans)])
    
    # Log the command
    logger.info(f"Starting scanner with command: {' '.join(cmd)}")
    
    # Run the command
    subprocess.run(cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start Multi-Timeframe Market Scanner")
    parser.add_argument("--symbols", nargs="+", help="Symbols to scan (default: all default symbols)")
    parser.add_argument("--tf-combination", default="all", choices=DEFAULT_TF_COMBINATIONS.keys(),
                        help="Timeframe combination to use")
    parser.add_argument("--interval", type=int, default=5, help="Interval between scans in minutes")
    parser.add_argument("--duration", default="1 M", help="How far back to fetch data")
    parser.add_argument("--scan-outside-market-hours", action="store_true", help="Scan outside market hours")
    parser.add_argument("--max-scans", type=int, help="Maximum number of scans to run")
    parser.add_argument("--list-symbols", action="store_true", help="List default symbols and exit")
    parser.add_argument("--list-tf-combinations", action="store_true", help="List timeframe combinations and exit")
    
    args = parser.parse_args()
    
    # List default symbols if requested
    if args.list_symbols:
        print("Default symbols:")
        i = 1
        for category, symbols in DEFAULT_SYMBOLS.items():
            print(f"\n{category.capitalize()}:")
            for symbol in symbols:
                print(f"{i:2d}. {symbol}")
                i += 1
        sys.exit(0)
    
    # List timeframe combinations if requested
    if args.list_tf_combinations:
        print("Timeframe combinations:")
        for name, timeframes in DEFAULT_TF_COMBINATIONS.items():
            print(f"{name}: {', '.join(timeframes)}")
        sys.exit(0)
    
    # Start the scanner
    start_scanner(
        symbols=args.symbols,
        tf_combination=args.tf_combination,
        interval=args.interval,
        duration=args.duration,
        scan_outside_market_hours=args.scan_outside_market_hours,
        max_scans=args.max_scans
    ) 