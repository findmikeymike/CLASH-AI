#!/usr/bin/env python3
"""
Run script for the complete trading system (scanner + dashboard)
"""
import os
import sys
import argparse
import subprocess
import time
from datetime import datetime
from loguru import logger

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_setup_scanner(symbols, timeframes):
    """Run the setup scanner workflow."""
    logger.info(f"Starting setup scanner workflow at {datetime.now().isoformat()}")
    
    # Build command
    cmd = [sys.executable, "run_setup_scanner.py"]
    
    # Add symbols
    if symbols:
        cmd.append("--symbols")
        cmd.extend(symbols)
    
    # Add timeframes
    if timeframes:
        cmd.append("--timeframes")
        cmd.extend(timeframes)
    
    # Run the command
    logger.info(f"Running command: {' '.join(cmd)}")
    process = subprocess.run(cmd, capture_output=True, text=True)
    
    if process.returncode == 0:
        logger.info("Setup scanner completed successfully")
        logger.info(process.stdout)
    else:
        logger.error(f"Setup scanner failed with code {process.returncode}")
        logger.error(process.stderr)
    
    return process.returncode == 0

def run_dashboard(port):
    """Run the TradingView dashboard."""
    logger.info(f"Starting TradingView dashboard on port {port}")
    
    # Build command
    cmd = [sys.executable, "run_tradingview_dashboard.py", "--port", str(port)]
    
    # Run the command in a new process
    logger.info(f"Running command: {' '.join(cmd)}")
    process = subprocess.Popen(cmd)
    
    # Wait a bit to ensure the dashboard starts
    time.sleep(2)
    
    return process

def main():
    """Run the complete trading system."""
    parser = argparse.ArgumentParser(description='Run trading system')
    parser.add_argument('--symbols', type=str, nargs='+', 
                        default=["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA"],
                        help='List of symbols to scan')
    parser.add_argument('--timeframes', type=str, nargs='+', 
                        default=["1D", "4H", "1H"],
                        help='List of timeframes to scan')
    parser.add_argument('--port', type=int, default=8082,
                        help='Port for the dashboard')
    parser.add_argument('--scan-interval', type=int, default=3600,
                        help='Interval between scans in seconds (default: 1 hour)')
    parser.add_argument('--skip-initial-scan', action='store_true',
                        help='Skip the initial scan and just start the dashboard')
    args = parser.parse_args()
    
    logger.info("Starting trading system")
    
    # Start the dashboard
    dashboard_process = run_dashboard(args.port)
    
    try:
        # Run initial scan if not skipped
        if not args.skip_initial_scan:
            run_setup_scanner(args.symbols, args.timeframes)
        
        # Main loop - run scanner at regular intervals
        while True:
            logger.info(f"Waiting {args.scan_interval} seconds until next scan")
            time.sleep(args.scan_interval)
            run_setup_scanner(args.symbols, args.timeframes)
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    finally:
        # Terminate the dashboard process
        if dashboard_process:
            logger.info("Terminating dashboard process")
            dashboard_process.terminate()
    
    logger.info("Trading system shutdown complete")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 