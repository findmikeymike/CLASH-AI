#!/usr/bin/env python
"""
Script to run the trading workflow.
"""
import argparse
from loguru import logger

from trading_agents.workflows.trading_dag import trading_workflow
from trading_agents.utils.logging_config import setup_logging
from trading_agents.config.settings import DEFAULT_TICKERS, TIMEFRAMES, SCANNER_SETTINGS, Settings

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the trading agent workflow")
    
    parser.add_argument(
        "--ticker", 
        type=str, 
        help="Ticker symbol to scan",
        default="AAPL"
    )
    
    parser.add_argument(
        "--timeframe", 
        type=str, 
        choices=list(TIMEFRAMES.keys()),
        default=SCANNER_SETTINGS["default_timeframe"],
        help="Timeframe to use for scanning"
    )
    
    parser.add_argument(
        "--period", 
        type=str, 
        default="1y",
        help="Period to fetch data for (e.g., 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"
    )
    
    parser.add_argument(
        "--lookback", 
        type=int, 
        default=50,
        help="Number of periods to look back"
    )
    
    parser.add_argument(
        "--min-volume", 
        type=int, 
        default=10000,
        help="Minimum volume threshold"
    )
    
    parser.add_argument(
        "--price-rejection", 
        type=float, 
        default=0.5,
        help="Price rejection threshold (percentage)"
    )
    
    parser.add_argument(
        "--fvg-threshold", 
        type=float, 
        default=0.3,
        help="Fair value gap threshold (percentage)"
    )
    
    return parser.parse_args()

def main():
    """Run the trading workflow."""
    # Parse command line arguments
    args = parse_args()
    
    # Set up logging
    setup_logging()
    
    # Create settings from arguments
    settings = Settings(
        ticker=args.ticker,
        timeframe=args.timeframe,
        period=args.period,
        lookback_periods=args.lookback,
        min_volume_threshold=args.min_volume,
        price_rejection_threshold=args.price_rejection / 100,  # Convert from percentage to decimal
        fvg_threshold=args.fvg_threshold / 100  # Convert from percentage to decimal
    )
    
    logger.info(f"Running trading workflow with the following parameters:")
    logger.info(f"Ticker: {settings.ticker}")
    logger.info(f"Timeframe: {settings.timeframe}")
    logger.info(f"Period: {settings.period}")
    logger.info(f"Lookback periods: {settings.lookback_periods}")
    logger.info(f"Min volume threshold: {settings.min_volume_threshold}")
    logger.info(f"Price rejection threshold: {settings.price_rejection_threshold:.4f}")
    logger.info(f"FVG threshold: {settings.fvg_threshold:.4f}")
    
    # Run the workflow
    results = trading_workflow(settings=settings)
    
    # Print summary
    if results:
        breaker_blocks = results.get("breaker_blocks", [])
        fair_value_gaps = results.get("fair_value_gaps", [])
        
        logger.info(f"Workflow completed. Found {len(breaker_blocks)} breaker blocks and {len(fair_value_gaps)} fair value gaps.")
        
        if breaker_blocks:
            logger.info("Breaker blocks found:")
            for i, block in enumerate(breaker_blocks, 1):
                logger.info(f"{i}. Breaker block at index {block.get('start_idx')}-{block.get('end_idx')}")
        
        if fair_value_gaps:
            logger.info("Fair value gaps found:")
            for i, fvg in enumerate(fair_value_gaps, 1):
                logger.info(f"{i}. FVG at index {fvg.get('idx')} (Gap: {fvg.get('gap_size'):.4f})")
    else:
        logger.warning("No results returned from workflow.")

if __name__ == "__main__":
    main() 