#!/usr/bin/env python3
"""
IBKR Single Scan

This script runs a single scan using IBKR data to detect trading setups.
It's a simplified version of the continuous scanner for testing purposes.
"""
import os
import sys
import argparse
from datetime import datetime
import pandas as pd
from loguru import logger

# Import the scanner functionality
from non_prefect_setup_scanner import (
    SimpleScanner,
    store_setups
)

# Import IBKR connector
from trading_agents.utils.ibkr_connector import (
    fetch_historical_data as ibkr_fetch_data,
    get_ib_connection,
    disconnect_ib,
    IBKR_AVAILABLE
)

# Import hierarchical scanner
from hierarchical_scanner import (
    hierarchical_scan,
    scan_fvg_sweep_engulfer_setup,
    scan_breaker_block_mss_setup
)

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/ibkr_single_scan_{time}.log", rotation="500 MB", level="DEBUG")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def fetch_market_data(symbol: str, timeframe: str, duration: str = "1 Y") -> pd.DataFrame:
    """
    Fetch market data for a symbol and timeframe using IBKR.
    
    Args:
        symbol: The ticker symbol to fetch data for
        timeframe: The timeframe to fetch data for (e.g., 1D, 1H, 4H)
        duration: How far back to fetch data (e.g., "1 D", "1 W", "1 M", "1 Y")
        
    Returns:
        A pandas DataFrame with the market data
    """
    logger.info(f"Fetching data for {symbol} on {timeframe} timeframe using IBKR")
    
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
    return yf_fetch_data(symbol, timeframe, "1y")

def run_single_scan(
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
    enable_hierarchical_scan=True  # New parameter to enable/disable hierarchical scanning
):
    """
    Run a single scan for the specified symbols and timeframes.
    
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
        enable_hierarchical_scan: Whether to enable hierarchical multi-timeframe scanning
        
    Returns:
        Dictionary with summary of setups found
    """
    logger.info(f"Running single scan for {len(symbols)} symbols on {len(timeframes)} timeframes")
    
    # Connect to IBKR if available
    if IBKR_AVAILABLE:
        ib = get_ib_connection()
        if ib:
            logger.info("Successfully connected to IBKR")
        else:
            logger.warning("Failed to connect to IBKR")
    
    # Initialize scanner
    scanner = SimpleScanner(
        lookback=lookback_periods,
        min_volume=min_volume_threshold,
        price_rejection=price_rejection_threshold,
        fvg_threshold=fvg_threshold,
        min_touches=min_touches
    )
    
    # Data cache to avoid fetching the same data multiple times
    data_cache = {}
    
    # Track all setups found
    all_setups = []
    
    # Process each symbol
    for symbol in symbols:
        symbol_setups = []
        
        # Single-timeframe scanning
        for timeframe in timeframes:
            logger.info(f"Processing {symbol} on {timeframe} timeframe")
            
            # Fetch market data
            data = fetch_market_data(symbol, timeframe, duration)
            
            # Cache the data for hierarchical scanning
            data_cache[(symbol, timeframe)] = data
            
            if data.empty:
                logger.warning(f"No data returned for {symbol} on {timeframe} timeframe")
                continue
            
            # Find breaker blocks
            breaker_blocks = scanner.find_breaker_blocks(data, symbol, timeframe)
            if breaker_blocks:
                logger.info(f"Found {len(breaker_blocks)} breaker blocks for {symbol} on {timeframe} timeframe")
                symbol_setups.extend(breaker_blocks)
            
            # Find fair value gaps
            fvgs = scanner.find_fair_value_gaps(data, symbol, timeframe)
            if fvgs:
                logger.info(f"Found {len(fvgs)} fair value gaps for {symbol} on {timeframe} timeframe")
                symbol_setups.extend(fvgs)
            
            # Find sweep engulfer patterns
            sweep_engulfers = scanner.find_sweep_engulfers(data, symbol, timeframe)
            if sweep_engulfers:
                logger.info(f"Found {len(sweep_engulfers)} sweep engulfer patterns for {symbol} on {timeframe} timeframe")
                for se in sweep_engulfers:
                    logger.info(f"  {se['direction']} Sweep Engulfer at {se['date']} - Price: {se['price']}")
                symbol_setups.extend(sweep_engulfers)
            
            # Find sweeping engulfer patterns
            sweeping_engulfers = scanner.find_sweeping_engulfers(data, symbol, timeframe)
            if sweeping_engulfers:
                logger.info(f"Found {len(sweeping_engulfers)} sweeping engulfer patterns for {symbol} on {timeframe} timeframe")
                symbol_setups.extend(sweeping_engulfers)
        
        # Hierarchical multi-timeframe scanning
        if enable_hierarchical_scan:
            multi_tf_setups = []
            
            # Check if we have the necessary timeframes for specific setup combinations
            available_timeframes = set(timeframes)
            
            # FVG → Sweep Engulfer setup (4H → 15m)
            if "4H" in available_timeframes and "15m" in available_timeframes:
                logger.info(f"Running FVG → Sweep Engulfer scan for {symbol}")
                fvg_se_setups = scan_fvg_sweep_engulfer_setup(symbol, scanner, data_cache)
                multi_tf_setups.extend(fvg_se_setups)
            
            # Breaker Block → MSS setup (1D → 1H)
            if "1D" in available_timeframes and "1H" in available_timeframes:
                logger.info(f"Running Breaker Block → MSS scan for {symbol}")
                bb_mss_setups = scan_breaker_block_mss_setup(symbol, scanner, data_cache)
                multi_tf_setups.extend(bb_mss_setups)
            
            # General hierarchical scan with 3 levels if available
            if len(available_timeframes) >= 3:
                # Sort timeframes from highest to lowest
                tf_hierarchy = sorted(
                    list(available_timeframes),
                    key=lambda tf: {
                        "1M": 0, "1W": 1, "1D": 2, "4H": 3, "1H": 4, "30m": 5, "15m": 6, "5m": 7, "1m": 8
                    }.get(tf, 999)
                )[:3]  # Take top 3
                
                logger.info(f"Running general hierarchical scan for {symbol} with {tf_hierarchy}")
                hierarchical_setups = hierarchical_scan(
                    symbol,
                    tf_hierarchy,
                    scanner,
                    data_cache
                )
                multi_tf_setups.extend(hierarchical_setups)
            
            # Update all setups with multi-timeframe setups
            all_setups.extend(multi_tf_setups)
    
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
        "timestamp": datetime.now().isoformat()
    }

def main():
    """Main function to run the single scan."""
    parser = argparse.ArgumentParser(description="Run a single scan with IBKR data")
    parser.add_argument("--symbols", type=str, nargs="+", default=["AAPL", "MSFT"],
                        help="List of symbols to scan")
    parser.add_argument("--timeframes", type=str, nargs="+", default=["1D"],
                        help="List of timeframes to scan")
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
    parser.add_argument("--enable-hierarchical-scan", action="store_true",
                        help="Enable hierarchical multi-timeframe scanning")
    
    args = parser.parse_args()
    
    # Run the single scan
    result = run_single_scan(
        symbols=args.symbols,
        timeframes=args.timeframes,
        lookback_periods=args.lookback,
        min_volume_threshold=args.min_volume,
        price_rejection_threshold=args.price_rejection,
        fvg_threshold=args.fvg_threshold,
        min_touches=args.min_touches,
        retest_threshold=args.retest_threshold,
        retracement_threshold=args.retracement_threshold,
        duration=args.duration,
        enable_hierarchical_scan=args.enable_hierarchical_scan
    )
    
    logger.info(f"Single scan completed. Found {result['total_setups']} setups.")
    return 0

if __name__ == "__main__":
    main() 