#!/usr/bin/env python3
"""
Run script for the setup scanner workflow
"""
import os
import sys
import argparse
from datetime import datetime
from loguru import logger

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from trading_agents.workflows.setup_scanner import setup_scanner_workflow
    
    def main():
        """Run the setup scanner workflow."""
        parser = argparse.ArgumentParser(description='Run setup scanner workflow')
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