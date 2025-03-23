#!/usr/bin/env python3
"""
Run script for the setup scanner workflow (Prefect 3.x compatible version)
"""
import os
import sys
import argparse
from datetime import datetime
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/setup_scanner_{time}.log", rotation="500 MB", level="DEBUG")

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from trading_agents.workflows.setup_scanner_v3 import setup_scanner_workflow
    
    def main():
        """Run the setup scanner workflow."""
        parser = argparse.ArgumentParser(description='Run setup scanner workflow (Prefect 3.x compatible)')
        parser.add_argument('--symbols', type=str, nargs='+', 
                            default=["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA"],
                            help='List of symbols to scan')
        parser.add_argument('--timeframes', type=str, nargs='+', 
                            default=["1D", "4H", "1H"],
                            help='List of timeframes to scan')
        args = parser.parse_args()
        
        logger.info(f"Starting setup scanner workflow at {datetime.now().isoformat()}")
        logger.info(f"Scanning symbols: {args.symbols}")
        logger.info(f"Scanning timeframes: {args.timeframes}")
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Run the workflow
        result = setup_scanner_workflow(
            symbols=args.symbols,
            timeframes=args.timeframes
        )
        
        logger.info(f"Setup scanner workflow completed. Found {result['total_setups']} setups.")
        
        return 0
    
    if __name__ == "__main__":
        sys.exit(main())
        
except Exception as e:
    logger.error(f"Error running setup scanner workflow: {e}")
    raise 