#!/usr/bin/env python3
"""
Unified Runner for Trading Workflows

This script provides a command-line interface to run the trading workflows
without any dependency on Prefect. It can run either the setup scanner,
the market analysis, or both in sequence.
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
logger.add("logs/trading_workflows_{time}.log", rotation="500 MB", level="DEBUG")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def import_workflow(module_name):
    """Import a workflow module by name."""
    try:
        # First try to import directly
        module = importlib.import_module(module_name)
        logger.info(f"Successfully imported {module_name}")
        return module
    except ImportError:
        logger.warning(f"Could not import {module_name} directly, trying file import")
        
        # Try to import from file
        file_path = f"{module_name}.py"
        if os.path.exists(file_path):
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            logger.info(f"Successfully imported {module_name} from file")
            return module
        else:
            logger.error(f"Could not find module file {file_path}")
            raise ImportError(f"Could not import {module_name}")

def run_setup_scanner(symbols, timeframes):
    """Run the setup scanner workflow."""
    logger.info(f"Running setup scanner workflow at {datetime.now().isoformat()}")
    logger.info(f"Scanning symbols: {symbols}")
    logger.info(f"Scanning timeframes: {timeframes}")
    
    try:
        # Import the setup scanner module
        scanner_module = import_workflow("non_prefect_setup_scanner")
        
        # Run the workflow
        result = scanner_module.setup_scanner_workflow(
            symbols=symbols,
            timeframes=timeframes
        )
        
        logger.info(f"Setup scanner workflow completed. Found {result['total_setups']} setups.")
        return result
    except Exception as e:
        logger.error(f"Error running setup scanner workflow: {str(e)}")
        return {"error": str(e), "total_setups": 0, "stored_setups": 0}

def run_market_analysis(symbols, timeframes, analyze_setups=True):
    """Run the market analysis workflow."""
    logger.info(f"Running market analysis workflow at {datetime.now().isoformat()}")
    logger.info(f"Analyzing symbols: {symbols}")
    logger.info(f"Analyzing timeframes: {timeframes}")
    
    try:
        # Import the market analysis module
        analysis_module = import_workflow("non_prefect_market_analysis")
        
        # Run the workflow
        result = analysis_module.market_analysis_workflow(
            symbols=symbols,
            timeframes=timeframes,
            analyze_existing_setups=analyze_setups
        )
        
        logger.info(f"Market analysis workflow completed.")
        logger.info(f"Analyzed {len(result['market_analyses'])} symbols")
        logger.info(f"Updated {len(result['updated_setups'])} setups")
        logger.info(f"Activated {len(result['activated_setups'])} setups")
        return result
    except Exception as e:
        logger.error(f"Error running market analysis workflow: {str(e)}")
        return {"error": str(e), "market_analyses": {}, "updated_setups": [], "activated_setups": []}

def main():
    """Main function to run the trading workflows."""
    parser = argparse.ArgumentParser(description="Run trading workflows")
    parser.add_argument("--workflow", type=str, choices=["scanner", "analysis", "both"], default="both",
                        help="Which workflow to run (scanner, analysis, or both)")
    parser.add_argument("--symbols", type=str, nargs="+", 
                        default=["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA"],
                        help="List of symbols to analyze")
    parser.add_argument("--timeframes", type=str, nargs="+", 
                        default=["1D"],
                        help="List of timeframes to analyze")
    parser.add_argument("--analyze-setups", action="store_true", default=True,
                        help="Analyze existing setups for confluence")
    args = parser.parse_args()
    
    logger.info(f"Starting trading workflows at {datetime.now().isoformat()}")
    logger.info(f"Selected workflow: {args.workflow}")
    
    results = {}
    
    # Run the selected workflow(s)
    if args.workflow in ["scanner", "both"]:
        scanner_result = run_setup_scanner(args.symbols, args.timeframes)
        results["scanner"] = scanner_result
    
    if args.workflow in ["analysis", "both"]:
        analysis_result = run_market_analysis(args.symbols, args.timeframes, args.analyze_setups)
        results["analysis"] = analysis_result
    
    logger.info(f"Trading workflows completed at {datetime.now().isoformat()}")
    
    # Print a summary of the results
    if "scanner" in results:
        scanner_result = results["scanner"]
        print("\n=== SETUP SCANNER RESULTS ===")
        print(f"Total setups found: {scanner_result.get('total_setups', 0)}")
        print(f"Setups stored: {scanner_result.get('stored_setups', 0)}")
    
    if "analysis" in results:
        analysis_result = results["analysis"]
        print("\n=== MARKET ANALYSIS RESULTS ===")
        print(f"Symbols analyzed: {len(analysis_result.get('market_analyses', {}))}")
        print(f"Setups updated: {len(analysis_result.get('updated_setups', []))}")
        print(f"Setups activated: {len(analysis_result.get('activated_setups', []))}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 