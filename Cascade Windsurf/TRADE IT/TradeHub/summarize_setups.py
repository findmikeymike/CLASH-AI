#!/usr/bin/env python3
"""
Summarize all the setups found by the scanner.

This script reads all the setup files in the data/setups directory
and creates a summary of the setups found.
"""

import os
import json
import glob
from datetime import datetime
from tabulate import tabulate
from loguru import logger

# Configure logging
logger.remove()
logger.add(
    "logs/summarize_setups.log",
    rotation="500 MB",
    level="INFO",
    format="{time} | {level} | {message}"
)
logger.add(
    lambda msg: print(msg),
    level="INFO",
    format="{message}"
)

def load_setup_files(directory="data/setups"):
    """
    Load all setup files from the specified directory.
    
    Args:
        directory: The directory containing the setup files
        
    Returns:
        A list of all setups found
    """
    logger.info(f"Loading setup files from {directory}")
    
    # Get all JSON files in the directory
    setup_files = glob.glob(f"{directory}/*.json")
    
    if not setup_files:
        logger.warning(f"No setup files found in {directory}")
        return []
    
    logger.info(f"Found {len(setup_files)} setup files")
    
    # Load all setups
    all_setups = []
    
    # Keep track of unique setups to avoid duplicates
    unique_setups = set()
    
    for file_path in setup_files:
        try:
            with open(file_path, 'r') as f:
                setups = json.load(f)
                
                # Add file info to each setup
                file_name = os.path.basename(file_path)
                
                for setup in setups:
                    # Create a unique identifier for this setup
                    setup_id = None
                    
                    if 'symbol' in setup and 'type' in setup and 'direction' in setup:
                        # For breaker blocks and fair value gaps
                        price_str = ""
                        if 'price_level' in setup:
                            price_str = f"{setup['price_level']:.2f}"
                        elif 'high' in setup and 'low' in setup:
                            price = (setup['high'] + setup['low']) / 2
                            price_str = f"{price:.2f}"
                        
                        setup_id = f"{setup['symbol']}_{setup['type']}_{setup['direction']}_{price_str}"
                    
                    # Only add if we haven't seen this setup before
                    if setup_id and setup_id not in unique_setups:
                        unique_setups.add(setup_id)
                        setup['file'] = file_name
                        all_setups.append(setup)
                    
        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)}")
    
    logger.info(f"Loaded {len(all_setups)} unique setups")
    return all_setups

def summarize_setups(setups):
    """
    Create a summary of the setups.
    
    Args:
        setups: A list of setup dictionaries
        
    Returns:
        A summary of the setups
    """
    if not setups:
        return "No setups found."
    
    # Group setups by symbol
    setups_by_symbol = {}
    for setup in setups:
        symbol = setup.get('symbol', 'UNKNOWN')
        if symbol not in setups_by_symbol:
            setups_by_symbol[symbol] = []
        setups_by_symbol[symbol].append(setup)
    
    # Create summary
    summary = []
    
    # Add header
    summary.append(f"=== Setup Summary ({len(setups)} setups) ===")
    summary.append("")
    
    # Add summary by symbol
    for symbol, symbol_setups in setups_by_symbol.items():
        summary.append(f"== {symbol} ({len(symbol_setups)} setups) ==")
        
        # Create a table for this symbol
        table_data = []
        for setup in symbol_setups:
            # Format the setup data
            setup_type = setup.get('type', 'unknown')
            direction = setup.get('direction', 'unknown')
            
            # Handle different price level formats
            price_level = None
            if 'price_level' in setup:
                price_level = setup['price_level']
            elif 'zone_high' in setup and 'zone_low' in setup:
                price_level = (setup['zone_high'] + setup['zone_low']) / 2
            elif 'high' in setup and 'low' in setup:
                price_level = (setup['high'] + setup['low']) / 2
            elif 'gap_high' in setup and 'gap_low' in setup:
                price_level = (setup['gap_high'] + setup['gap_low']) / 2
            else:
                price_level = 'N/A'
            
            strength = setup.get('strength', 'N/A')
            timeframe = setup.get('timeframe', 'unknown')
            notes = setup.get('notes', '')
            
            # Add to table
            table_data.append([
                setup_type,
                direction,
                f"{price_level:.2f}" if isinstance(price_level, (int, float)) else price_level,
                f"{strength:.2f}" if isinstance(strength, (int, float)) else strength,
                timeframe,
                notes
            ])
        
        # Create table
        headers = ["Type", "Direction", "Price", "Strength", "Timeframe", "Notes"]
        table = tabulate(table_data, headers=headers, tablefmt="grid")
        
        # Add table to summary
        summary.append(table)
        summary.append("")
    
    return "\n".join(summary)

def main():
    """
    Main function to summarize setups.
    """
    # Load all setups
    setups = load_setup_files()
    
    # Create summary
    summary = summarize_setups(setups)
    
    # Print summary
    print(summary)
    
    # Save summary to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = f"data/setup_summary_{timestamp}.txt"
    
    try:
        with open(summary_file, 'w') as f:
            f.write(summary)
        logger.info(f"Summary saved to {summary_file}")
    except Exception as e:
        logger.error(f"Error saving summary: {str(e)}")

if __name__ == "__main__":
    main() 