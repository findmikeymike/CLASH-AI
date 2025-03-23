#!/usr/bin/env python3
"""
Start Scanner

This script starts the market scanner with a predefined list of symbols and timeframes.
It's a convenience wrapper around run_market_scanner.py.
"""
import os
import sys
import argparse
import subprocess
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/start_scanner_{time}.log", rotation="500 MB", level="DEBUG")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Default symbols to scan
DEFAULT_SYMBOLS = [
    # Tech stocks
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "AMD", "INTC", "CSCO", "ORCL",
    # Financial stocks
    "JPM", "BAC", "C", "GS", "MS", "V", "MA", "AXP", "BLK", "WFC",
    # Consumer stocks
    "PG", "KO", "PEP", "WMT", "COST", "MCD", "NKE", "SBUX", "DIS", "HD",
    # Healthcare stocks
    "JNJ", "PFE", "MRK", "UNH", "ABT", "TMO", "LLY", "ABBV", "BMY", "AMGN",
    # Energy stocks
    "XOM", "CVX", "COP", "EOG", "SLB"
]

# Default timeframes to scan
DEFAULT_TIMEFRAMES = ["1D", "4H", "1H", "30m", "15m", "5m"]

def start_scanner(
    symbols=None,
    timeframes=None,
    interval_minutes=5,
    duration="1 Y",
    scan_outside_market_hours=False,
    max_scans=None
):
    """
    Start the market scanner with the specified parameters.
    
    Args:
        symbols: List of symbols to scan (defaults to DEFAULT_SYMBOLS)
        timeframes: List of timeframes to scan (defaults to DEFAULT_TIMEFRAMES)
        interval_minutes: How often to run the scanner (in minutes)
        duration: How far back to fetch data (e.g., "1 D", "1 W", "1 M", "1 Y")
        scan_outside_market_hours: Whether to run scans even when the market is closed
        max_scans: Maximum number of scans to run (for testing purposes)
    """
    if symbols is None:
        symbols = DEFAULT_SYMBOLS
    
    if timeframes is None:
        timeframes = DEFAULT_TIMEFRAMES
    
    # Build the command
    cmd = ["python", "run_market_scanner.py"]
    cmd.extend(["--symbols"] + symbols)
    cmd.extend(["--timeframes"] + timeframes)
    cmd.extend(["--interval", str(interval_minutes)])
    cmd.extend(["--duration", duration])
    
    if scan_outside_market_hours:
        cmd.append("--scan-outside-market-hours")
    
    if max_scans is not None:
        cmd.extend(["--max-scans", str(max_scans)])
    
    # Log the command
    logger.info(f"Starting scanner with command: {' '.join(cmd)}")
    
    # Run the command
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Scanner failed with exit code {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        logger.info("Scanner stopped by user")
        return 0
    
    return 0

def main():
    """Main function to parse command line arguments and start the scanner."""
    parser = argparse.ArgumentParser(description="Start the market scanner with predefined symbols and timeframes")
    parser.add_argument("--symbols", type=str, nargs="+", default=None,
                        help=f"List of symbols to scan (defaults to {len(DEFAULT_SYMBOLS)} predefined symbols)")
    parser.add_argument("--timeframes", type=str, nargs="+", default=None,
                        help=f"List of timeframes to scan (defaults to {', '.join(DEFAULT_TIMEFRAMES)})")
    parser.add_argument("--interval", type=int, default=5,
                        help="How often to run the scanner (in minutes)")
    parser.add_argument("--duration", type=str, default="1 Y",
                        help="How far back to fetch data (e.g., '1 D', '1 W', '1 M', '1 Y')")
    parser.add_argument("--scan-outside-market-hours", action="store_true",
                        help="Run scans even when the market is closed")
    parser.add_argument("--max-scans", type=int, default=None,
                        help="Maximum number of scans to run (for testing purposes)")
    parser.add_argument("--list-symbols", action="store_true",
                        help="List the default symbols and exit")
    
    args = parser.parse_args()
    
    # If --list-symbols is specified, print the default symbols and exit
    if args.list_symbols:
        print("Default symbols:")
        for i, symbol in enumerate(DEFAULT_SYMBOLS):
            print(f"{i+1:2d}. {symbol}")
        return 0
    
    # Start the scanner
    return start_scanner(
        symbols=args.symbols,
        timeframes=args.timeframes,
        interval_minutes=args.interval,
        duration=args.duration,
        scan_outside_market_hours=args.scan_outside_market_hours,
        max_scans=args.max_scans
    )

if __name__ == "__main__":
    sys.exit(main()) 