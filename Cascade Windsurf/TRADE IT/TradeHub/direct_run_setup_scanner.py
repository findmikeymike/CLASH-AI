#!/usr/bin/env python3
"""
Direct run script for the setup scanner workflow (Prefect 3.x compatible version)
This script imports directly from the file to avoid package import issues.
"""
import os
import sys
import argparse
from datetime import datetime
import importlib.util
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/direct_setup_scanner_{time}.log", rotation="500 MB", level="DEBUG")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def import_from_file(file_path, module_name):
    """Import a module directly from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

try:
    # Import the setup scanner workflow directly from file
    scanner_v3_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "trading_agents/workflows/setup_scanner_v3.py"
    )
    
    scanner_module = import_from_file(scanner_v3_path, "setup_scanner_v3")
    setup_scanner_workflow = scanner_module.setup_scanner_workflow
    
    def main():
        """Run the setup scanner workflow."""
        parser = argparse.ArgumentParser(description='Direct run of setup scanner workflow (Prefect 3.x compatible)')
        parser.add_argument('--symbols', type=str, nargs='+', 
                            default=["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA"],
                            help='List of symbols to scan')
        parser.add_argument('--timeframes', type=str, nargs='+', 
                            default=["1D", "4H", "1H"],
                            help='List of timeframes to scan')
        args = parser.parse_args()
        
        logger.info(f"Starting direct setup scanner workflow at {datetime.now().isoformat()}")
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