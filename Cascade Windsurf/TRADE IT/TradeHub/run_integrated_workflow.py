#!/usr/bin/env python3
"""
Integrated Trading Workflow Runner

This script runs the complete trading workflow:
1. Setup Scanner: Identifies potential trading setups
2. Market Analysis: Analyzes market conditions and evaluates setups for confluence
3. Activates high-confluence setups for display in the dashboard

Usage:
    python run_integrated_workflow.py [--symbols SYMBOLS] [--timeframes TIMEFRAMES] [--port PORT]
"""
import os
import sys
import argparse
import subprocess
import time
from datetime import datetime
from loguru import logger

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from trading_agents.workflows.setup_scanner import setup_scanner_workflow
    from trading_agents.workflows.market_analysis_workflow import market_analysis_workflow
    from trading_agents.utils.setup_storage import init_db
except ImportError as e:
    logger.error(f"Error importing required modules: {str(e)}")
    sys.exit(1)

def run_setup_scanner(symbols, timeframes):
    """Run the setup scanner workflow."""
    logger.info(f"Starting setup scanner workflow at {datetime.now().isoformat()}")
    
    try:
        # Run the setup scanner workflow
        result = setup_scanner_workflow(symbols=symbols, timeframes=timeframes)
        
        logger.info(f"Setup scanner completed. Found {result['total_setups']} potential setups.")
        return result
    except Exception as e:
        logger.error(f"Error running setup scanner workflow: {str(e)}")
        return {"total_setups": 0, "setups": [], "timestamp": datetime.now().isoformat()}

def run_market_analysis(symbols, timeframes):
    """Run the market analysis workflow."""
    logger.info(f"Starting market analysis workflow at {datetime.now().isoformat()}")
    
    try:
        # Run the market analysis workflow
        result = market_analysis_workflow(
            symbols=symbols, 
            timeframes=timeframes,
            analyze_existing_setups=True
        )
        
        activated_setups = result.get("activated_setups", [])
        logger.info(f"Market analysis completed. Activated {len(activated_setups)} setups.")
        return result
    except Exception as e:
        logger.error(f"Error running market analysis workflow: {str(e)}")
        return {"market_analyses": {}, "updated_setups": [], "activated_setups": [], "timestamp": datetime.now().isoformat()}

def run_dashboard(port):
    """Start the TradingView dashboard."""
    logger.info(f"Starting TradingView dashboard on port {port}")
    
    try:
        # Build the command to run the dashboard
        cmd = [sys.executable, "run_tradingview_dashboard.py", "--port", str(port)]
        
        # Start the dashboard process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit to ensure the dashboard starts
        time.sleep(2)
        
        # Check if the process is still running
        if process.poll() is None:
            logger.info(f"Dashboard started successfully on port {port}")
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Dashboard failed to start: {stderr}")
            return False
    except Exception as e:
        logger.error(f"Error starting dashboard: {str(e)}")
        return False

def main():
    """Main function to run the integrated workflow."""
    parser = argparse.ArgumentParser(description="Run the integrated trading workflow")
    parser.add_argument("--symbols", nargs="+", default=["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META"],
                        help="List of symbols to analyze")
    parser.add_argument("--timeframes", nargs="+", default=["1D", "4H", "1H"],
                        help="List of timeframes to analyze")
    parser.add_argument("--port", type=int, default=8085,
                        help="Port to run the dashboard on")
    parser.add_argument("--scan-interval", type=int, default=3600,
                        help="Interval between scans in seconds (default: 1 hour)")
    parser.add_argument("--skip-initial-scan", action="store_true",
                        help="Skip the initial scan and just start the dashboard")
    
    args = parser.parse_args()
    
    logger.info(f"Starting integrated trading workflow with symbols: {args.symbols}")
    logger.info(f"Timeframes: {args.timeframes}")
    
    # Initialize the database
    init_db()
    
    # Start the dashboard
    dashboard_running = run_dashboard(args.port)
    
    if not dashboard_running:
        logger.warning("Dashboard failed to start. Continuing with workflow...")
    
    # Main workflow loop
    try:
        while True:
            if not args.skip_initial_scan:
                # Run the setup scanner
                scanner_result = run_setup_scanner(args.symbols, args.timeframes)
                
                # Run the market analysis
                analysis_result = run_market_analysis(args.symbols, args.timeframes)
                
                # Log the results
                logger.info(f"Workflow cycle completed at {datetime.now().isoformat()}")
                logger.info(f"Found {scanner_result['total_setups']} potential setups")
                logger.info(f"Activated {len(analysis_result['activated_setups'])} setups")
                
                # Wait for the next scan interval
                logger.info(f"Waiting {args.scan_interval} seconds until next scan")
                time.sleep(args.scan_interval)
            else:
                # If skipping initial scan, just run once to set up the dashboard
                args.skip_initial_scan = False
                logger.info("Skipped initial scan. Dashboard is running.")
                time.sleep(args.scan_interval)
    
    except KeyboardInterrupt:
        logger.info("Workflow interrupted by user. Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in workflow: {str(e)}")
    finally:
        logger.info("Workflow stopped")

if __name__ == "__main__":
    main() 