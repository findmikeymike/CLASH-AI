#!/usr/bin/env python3
"""
Run script for the market analysis workflow (Prefect 3.x compatible version)
"""
import os
import sys
import argparse
from datetime import datetime
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/market_analysis_{time}.log", rotation="500 MB", level="DEBUG")

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from trading_agents.workflows.market_analysis_v3 import market_analysis_workflow
    
    def main():
        """Run the market analysis workflow."""
        parser = argparse.ArgumentParser(description='Run market analysis workflow (Prefect 3.x compatible)')
        parser.add_argument('--symbols', type=str, nargs='+', 
                            default=["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA"],
                            help='List of symbols to analyze')
        parser.add_argument('--timeframes', type=str, nargs='+', 
                            default=["1D", "4H", "1H"],
                            help='List of timeframes to analyze')
        parser.add_argument('--analyze-setups', action='store_true', default=True,
                            help='Analyze existing setups for confluence')
        args = parser.parse_args()
        
        logger.info(f"Starting market analysis workflow at {datetime.now().isoformat()}")
        logger.info(f"Analyzing symbols: {args.symbols}")
        logger.info(f"Analyzing timeframes: {args.timeframes}")
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Run the workflow
        result = market_analysis_workflow(
            symbols=args.symbols,
            timeframes=args.timeframes,
            analyze_existing_setups=args.analyze_setups
        )
        
        logger.info(f"Market analysis workflow completed.")
        logger.info(f"Analyzed {len(result['market_analyses'])} symbols")
        logger.info(f"Updated {len(result['updated_setups'])} setups")
        logger.info(f"Activated {len(result['activated_setups'])} setups")
        
        return 0
    
    if __name__ == "__main__":
        sys.exit(main())
        
except Exception as e:
    logger.error(f"Error running market analysis workflow: {e}")
    raise 