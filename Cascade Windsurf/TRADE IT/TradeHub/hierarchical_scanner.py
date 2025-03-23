#!/usr/bin/env python3
"""
Hierarchical Multi-Timeframe Scanner

This module provides functionality for detecting trading setups that span multiple timeframes,
using a hierarchical approach that starts with higher timeframes and cascades down to lower
timeframes for confirmation.
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/hierarchical_scanner_{time}.log", rotation="500 MB", level="DEBUG")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def hierarchical_scan(symbol, timeframe_hierarchy, scanner, data_cache=None):
    """
    Perform a hierarchical scan starting from higher timeframes and cascading down.
    
    Args:
        symbol: The ticker symbol to scan
        timeframe_hierarchy: Ordered list of timeframes from highest to lowest
                            (e.g., ["1D", "4H", "1H", "15m"])
        scanner: Scanner instance
        data_cache: Optional cache of already fetched market data
    
    Returns:
        List of confirmed setups that meet criteria across multiple timeframes
    """
    logger.info(f"Running hierarchical scan for {symbol} across {timeframe_hierarchy}")
    
    # Initialize data cache if not provided
    if data_cache is None:
        data_cache = {}
    
    # Start with highest timeframe
    highest_tf = timeframe_hierarchy[0]
    
    # Fetch data for highest timeframe if not in cache
    if (symbol, highest_tf) not in data_cache:
        data_highest = scanner.fetch_market_data(symbol, highest_tf)
        data_cache[(symbol, highest_tf)] = data_highest
    else:
        data_highest = data_cache[(symbol, highest_tf)]
    
    # Find potential setup conditions in highest timeframe
    potential_setups = []
    
    # Look for FVGs, breaker blocks, key levels, etc.
    logger.debug(f"Finding potential setup conditions in {highest_tf} timeframe")
    
    # Find Fair Value Gaps
    fvgs = scanner.find_fair_value_gaps(data_highest, symbol, highest_tf)
    for fvg in fvgs:
        if fvg.get('status') == 'unfilled':  # Only consider unfilled FVGs
            potential_setups.append({
                'type': 'FVG',
                'timeframe': highest_tf,
                'zone': (fvg['low'], fvg['high']),
                'direction': fvg['direction'],
                'created_at': fvg['date'],
                'details': fvg
            })
            logger.debug(f"Found unfilled {fvg['direction']} FVG in {highest_tf} at {fvg['date']}")
    
    # Find Breaker Blocks
    breaker_blocks = scanner.find_breaker_blocks(data_highest, symbol, highest_tf)
    for block in breaker_blocks:
        if block.get('status') == 'active':  # Only consider active breaker blocks
            potential_setups.append({
                'type': 'BreakerBlock',
                'timeframe': highest_tf,
                'zone': (block['low'], block['high']),
                'direction': block['direction'],
                'created_at': block['date'],
                'details': block
            })
            logger.debug(f"Found active {block['direction']} Breaker Block in {highest_tf} at {block['date']}")
    
    # If no potential setups found in highest timeframe, no need to continue
    if not potential_setups:
        logger.info(f"No potential setup conditions found in {highest_tf} timeframe for {symbol}")
        return []
    
    logger.info(f"Found {len(potential_setups)} potential setup conditions in {highest_tf} timeframe")
    
    # Now cascade down to lower timeframes for confirmation
    confirmed_setups = []
    
    for i in range(1, len(timeframe_hierarchy)):
        current_tf = timeframe_hierarchy[i]
        logger.debug(f"Cascading to {current_tf} timeframe for confirmation")
        
        # Fetch data for current timeframe if not in cache
        if (symbol, current_tf) not in data_cache:
            data_current = scanner.fetch_market_data(symbol, current_tf)
            data_cache[(symbol, current_tf)] = data_current
        else:
            data_current = data_cache[(symbol, current_tf)]
        
        # For each potential setup from higher timeframe
        new_potential_setups = []
        
        for setup in potential_setups:
            # Check for confirmation in current timeframe
            confirmations = find_confirmations(data_current, setup, current_tf, scanner)
            
            if confirmations:
                logger.debug(f"Found {len(confirmations)} confirmations in {current_tf} for {setup['type']} from {setup['timeframe']}")
                
                # If this is the lowest timeframe, add as confirmed setup
                if i == len(timeframe_hierarchy) - 1:
                    for conf in confirmations:
                        confirmed_setup = {
                            'symbol': symbol,
                            'type': f"{setup['type']}_{conf['type']}",  # e.g., "FVG_SweepEngulfer"
                            'primary_tf': current_tf,
                            'reference_tf': setup['timeframe'],
                            'date': conf['date'],
                            'price': conf['price'],
                            'direction': conf['direction'],
                            'strength': conf.get('strength', 0.7),  # Default strength
                            'notes': f"{conf['direction']} {conf['type']} at {setup['timeframe']} {setup['type']}",
                            'higher_tf_setup': setup,
                            'confirmation': conf
                        }
                        confirmed_setups.append(confirmed_setup)
                        logger.info(f"Confirmed setup: {confirmed_setup['type']} in {symbol} at {conf['date']}")
                else:
                    # If not lowest timeframe, add to potential setups for next level
                    for conf in confirmations:
                        new_potential_setup = {
                            'type': f"{setup['type']}_{conf['type']}",
                            'timeframe': current_tf,
                            'reference_tf': setup['timeframe'],
                            'zone': conf.get('zone', setup['zone']),
                            'direction': conf['direction'],
                            'created_at': conf['date'],
                            'parent_setup': setup,
                            'confirmation': conf
                        }
                        new_potential_setups.append(new_potential_setup)
                        logger.debug(f"Intermediate confirmation: {new_potential_setup['type']} in {current_tf}")
            
        # Update potential setups for next iteration
        potential_setups = new_potential_setups
        
        # If no potential setups left, break the loop
        if not potential_setups:
            logger.info(f"No confirmations found in {current_tf} timeframe, stopping cascade")
            break
    
    logger.info(f"Hierarchical scan complete. Found {len(confirmed_setups)} confirmed setups for {symbol}")
    return confirmed_setups

def find_confirmations(data, higher_tf_setup, current_tf, scanner):
    """
    Find confirmation patterns in current timeframe for a higher timeframe setup.
    
    Args:
        data: Market data for current timeframe
        higher_tf_setup: Setup condition from higher timeframe
        current_tf: Current timeframe being analyzed
        scanner: Scanner instance
        
    Returns:
        List of confirmation patterns found
    """
    confirmations = []
    
    # Get the zone from higher timeframe setup
    zone_low, zone_high = higher_tf_setup['zone']
    
    # Find where price interacts with the zone
    interactions = []
    for i in range(len(data)):
        high, low = data['high'].iloc[i], data['low'].iloc[i]
        # Check if candle interacts with the zone
        if (low <= zone_high and high >= zone_low):
            interactions.append(i)
    
    # If no interactions, return empty list
    if not interactions:
        return []
    
    logger.debug(f"Found {len(interactions)} price interactions with {higher_tf_setup['type']} zone")
    
    # Check for specific patterns at interaction points
    for idx in interactions:
        # Skip if not enough data before this index
        if idx < 10:
            continue
            
        # Check for Sweep Engulfer pattern
        if higher_tf_setup['type'] == 'FVG' and current_tf in ['1H', '30m', '15m', '5m']:
            sweep_engulfers = find_sweep_engulfers_at_index(data, idx, scanner)
            for se in sweep_engulfers:
                confirmations.append({
                    'type': 'SweepEngulfer',
                    'date': data.index[idx],
                    'price': data['close'].iloc[idx],
                    'direction': se['direction'],
                    'strength': 0.8,  # Higher strength for this specific combo
                    'details': se
                })
                logger.debug(f"Found {se['direction']} Sweep Engulfer at {data.index[idx]}")
        
        # Check for MSS (Market Structure Shift)
        if higher_tf_setup['type'] in ['FVG', 'BreakerBlock'] and current_tf in ['30m', '15m', '5m']:
            mss = is_market_structure_shift(data, idx)
            if mss:
                confirmations.append({
                    'type': 'MSS',
                    'date': data.index[idx],
                    'price': data['close'].iloc[idx],
                    'direction': mss['direction'],
                    'strength': 0.75,
                    'details': mss
                })
                logger.debug(f"Found {mss['direction']} Market Structure Shift at {data.index[idx]}")
        
        # Check for Sweeping Engulfer pattern
        sweeping_engulfers = find_sweeping_engulfers_at_index(data, idx, scanner)
        for se in sweeping_engulfers:
            confirmations.append({
                'type': 'SweepingEngulfer',
                'date': data.index[idx],
                'price': data['close'].iloc[idx],
                'direction': se['direction'],
                'strength': 0.7,
                'details': se
            })
            logger.debug(f"Found {se['direction']} Sweeping Engulfer at {data.index[idx]}")
    
    return confirmations

def find_sweep_engulfers_at_index(data, idx, scanner, window=5):
    """
    Check if there's a Sweep Engulfer pattern at the specified index.
    
    Args:
        data: Market data
        idx: Index to check
        scanner: Scanner instance
        window: Number of candles to look back
        
    Returns:
        List of Sweep Engulfer patterns found
    """
    # Extract the relevant window of data
    start_idx = max(0, idx - window)
    window_data = data.iloc[start_idx:idx+1]
    
    # Use the scanner's sweep engulfer detection
    try:
        # This assumes the scanner has a method to detect sweep engulfers in a window
        sweep_engulfers = scanner.detect_sweep_engulfer_in_window(window_data)
        
        # If the method doesn't exist, we'll implement a simplified version here
        if not sweep_engulfers and hasattr(scanner, 'sweep_engulfer_agent'):
            # Use the sweep engulfer agent directly
            sweep_engulfers = scanner.sweep_engulfer_agent.detect_sweep_engulfer(window_data)
        
        return sweep_engulfers if sweep_engulfers else []
    except Exception as e:
        logger.error(f"Error detecting Sweep Engulfer: {e}")
        return []

def find_sweeping_engulfers_at_index(data, idx, scanner, window=5):
    """
    Check if there's a Sweeping Engulfer pattern at the specified index.
    
    Args:
        data: Market data
        idx: Index to check
        scanner: Scanner instance
        window: Number of candles to look back
        
    Returns:
        List of Sweeping Engulfer patterns found
    """
    # Extract the relevant window of data
    start_idx = max(0, idx - window)
    window_data = data.iloc[start_idx:idx+1]
    
    # Use the scanner's sweeping engulfer detection
    try:
        # This assumes the scanner has a method to detect sweeping engulfers in a window
        sweeping_engulfers = scanner.find_sweeping_engulfers_in_window(window_data)
        
        return sweeping_engulfers if sweeping_engulfers else []
    except Exception as e:
        logger.error(f"Error detecting Sweeping Engulfer: {e}")
        return []

def is_market_structure_shift(data, idx, window=10):
    """
    Check if there's a market structure shift at the specified index.
    
    Args:
        data: Market data
        idx: Index to check
        window: Number of candles to look back
        
    Returns:
        Dictionary with MSS details if found, None otherwise
    """
    if idx < window:
        return None
    
    # Extract the relevant window of data
    window_data = data.iloc[idx-window:idx+1]
    
    # Check for higher highs and higher lows (uptrend)
    highs = window_data['high'].values
    lows = window_data['low'].values
    
    # Simple MSS detection - check for sequence of higher highs/lows or lower highs/lows
    # This is a simplified version - a real implementation would be more sophisticated
    
    # Check for bullish MSS (shift from downtrend to uptrend)
    if (highs[-1] > max(highs[-6:-1]) and 
        lows[-1] > max(lows[-6:-1]) and
        all(highs[i] < highs[i+1] for i in range(-6, -1))):
        return {
            'direction': 'Bullish',
            'type': 'MSS',
            'strength': 0.75
        }
    
    # Check for bearish MSS (shift from uptrend to downtrend)
    if (highs[-1] < min(highs[-6:-1]) and 
        lows[-1] < min(lows[-6:-1]) and
        all(lows[i] > lows[i+1] for i in range(-6, -1))):
        return {
            'direction': 'Bearish',
            'type': 'MSS',
            'strength': 0.75
        }
    
    return None

# Specific multi-timeframe setup combinations

def scan_fvg_sweep_engulfer_setup(symbol, scanner, data_cache=None):
    """
    Scan for Sweep Engulfer confirmations at Fair Value Gaps.
    
    Args:
        symbol: The ticker symbol to scan
        scanner: Scanner instance
        data_cache: Optional cache of already fetched market data
        
    Returns:
        List of confirmed setups
    """
    logger.info(f"Scanning for FVG → Sweep Engulfer setups in {symbol}")
    
    # Define timeframe hierarchy for this specific setup
    timeframe_hierarchy = ["4H", "15m"]
    
    # Initialize data cache if not provided
    if data_cache is None:
        data_cache = {}
    
    # Fetch data for both timeframes if not in cache
    if (symbol, "4H") not in data_cache:
        data_4h = scanner.fetch_market_data(symbol, "4H")
        data_cache[(symbol, "4H")] = data_4h
    else:
        data_4h = data_cache[(symbol, "4H")]
    
    if (symbol, "15m") not in data_cache:
        data_15m = scanner.fetch_market_data(symbol, "15m")
        data_cache[(symbol, "15m")] = data_15m
    else:
        data_15m = data_cache[(symbol, "15m")]
    
    # Find unfilled FVGs in 4H timeframe
    fvgs_4h = scanner.find_fair_value_gaps(data_4h, symbol, "4H")
    unfilled_fvgs = [fvg for fvg in fvgs_4h if fvg.get('status') == 'unfilled']
    
    if not unfilled_fvgs:
        logger.info(f"No unfilled FVGs found in {symbol} on 4H timeframe")
        return []  # No unfilled FVGs, so no setups to find
    
    logger.info(f"Found {len(unfilled_fvgs)} unfilled FVGs in {symbol} on 4H timeframe")
    
    # For each unfilled FVG, look for Sweep Engulfer confirmations in 15m
    confirmed_setups = []
    
    for fvg in unfilled_fvgs:
        # Find where 15m price interacts with the FVG zone
        fvg_low, fvg_high = fvg['low'], fvg['high']
        
        # Find all candles that interact with the FVG
        interaction_indices = []
        for i in range(len(data_15m)):
            high, low = data_15m['high'].iloc[i], data_15m['low'].iloc[i]
            # Check if candle interacts with FVG zone
            if (low <= fvg_high and high >= fvg_low):
                interaction_indices.append(i)
        
        if not interaction_indices:
            logger.debug(f"No price interactions with FVG at {fvg['date']} in 15m timeframe")
            continue
            
        logger.debug(f"Found {len(interaction_indices)} price interactions with FVG at {fvg['date']}")
        
        # For each interaction point, check for Sweep Engulfer pattern
        for idx in interaction_indices:
            # Need to look back a few candles to detect the pattern
            if idx >= 5:  # Need at least 5 candles to detect pattern
                # Check for Sweep Engulfer pattern
                sweep_engulfers = find_sweep_engulfers_at_index(data_15m, idx, scanner)
                
                for sweep_engulfer in sweep_engulfers:
                    # We found a confirmation!
                    confirmed_setup = {
                        'symbol': symbol,
                        'type': 'FVG_SweepEngulfer',
                        'primary_tf': '15m',
                        'reference_tf': '4H',
                        'date': data_15m.index[idx],
                        'price': data_15m['close'].iloc[idx],
                        'direction': sweep_engulfer['direction'],
                        'strength': 0.85,  # High strength for this specific combo
                        'fvg': {
                            'low': fvg_low,
                            'high': fvg_high,
                            'date': fvg['date']
                        },
                        'notes': f"{sweep_engulfer['direction']} Sweep Engulfer at 4H Fair Value Gap"
                    }
                    confirmed_setups.append(confirmed_setup)
                    logger.info(f"Found {sweep_engulfer['direction']} Sweep Engulfer at 4H FVG in {symbol} at {data_15m.index[idx]}")
    
    logger.info(f"Found {len(confirmed_setups)} FVG → Sweep Engulfer setups in {symbol}")
    return confirmed_setups

def scan_breaker_block_mss_setup(symbol, scanner, data_cache=None):
    """
    Scan for Market Structure Shift confirmations at Breaker Blocks.
    
    Args:
        symbol: The ticker symbol to scan
        scanner: Scanner instance
        data_cache: Optional cache of already fetched market data
        
    Returns:
        List of confirmed setups
    """
    logger.info(f"Scanning for Breaker Block → MSS setups in {symbol}")
    
    # Define timeframe hierarchy for this specific setup
    timeframe_hierarchy = ["1D", "1H"]
    
    # Initialize data cache if not provided
    if data_cache is None:
        data_cache = {}
    
    # Fetch data for both timeframes if not in cache
    if (symbol, "1D") not in data_cache:
        data_1d = scanner.fetch_market_data(symbol, "1D")
        data_cache[(symbol, "1D")] = data_1d
    else:
        data_1d = data_cache[(symbol, "1D")]
    
    if (symbol, "1H") not in data_cache:
        data_1h = scanner.fetch_market_data(symbol, "1H")
        data_cache[(symbol, "1H")] = data_1h
    else:
        data_1h = data_cache[(symbol, "1H")]
    
    # Find active breaker blocks in 1D timeframe
    breaker_blocks = scanner.find_breaker_blocks(data_1d, symbol, "1D")
    active_blocks = [block for block in breaker_blocks if block.get('status') == 'active']
    
    if not active_blocks:
        logger.info(f"No active breaker blocks found in {symbol} on 1D timeframe")
        return []  # No active breaker blocks, so no setups to find
    
    logger.info(f"Found {len(active_blocks)} active breaker blocks in {symbol} on 1D timeframe")
    
    # For each active breaker block, look for MSS confirmations in 1H
    confirmed_setups = []
    
    for block in active_blocks:
        # Find where 1H price interacts with the breaker block zone
        block_low, block_high = block['low'], block['high']
        
        # Find all candles that interact with the breaker block
        interaction_indices = []
        for i in range(len(data_1h)):
            high, low = data_1h['high'].iloc[i], data_1h['low'].iloc[i]
            # Check if candle interacts with breaker block zone
            if (low <= block_high and high >= block_low):
                interaction_indices.append(i)
        
        if not interaction_indices:
            logger.debug(f"No price interactions with breaker block at {block['date']} in 1H timeframe")
            continue
            
        logger.debug(f"Found {len(interaction_indices)} price interactions with breaker block at {block['date']}")
        
        # For each interaction point, check for MSS
        for idx in interaction_indices:
            # Need to look back a few candles to detect the pattern
            if idx >= 10:  # Need at least 10 candles to detect MSS
                # Check for Market Structure Shift
                mss = is_market_structure_shift(data_1h, idx)
                
                if mss:
                    # We found a confirmation!
                    confirmed_setup = {
                        'symbol': symbol,
                        'type': 'BreakerBlock_MSS',
                        'primary_tf': '1H',
                        'reference_tf': '1D',
                        'date': data_1h.index[idx],
                        'price': data_1h['close'].iloc[idx],
                        'direction': mss['direction'],
                        'strength': 0.8,  # High strength for this specific combo
                        'breaker_block': {
                            'low': block_low,
                            'high': block_high,
                            'date': block['date'],
                            'direction': block['direction']
                        },
                        'notes': f"{mss['direction']} Market Structure Shift at 1D Breaker Block"
                    }
                    confirmed_setups.append(confirmed_setup)
                    logger.info(f"Found {mss['direction']} MSS at 1D Breaker Block in {symbol} at {data_1h.index[idx]}")
    
    logger.info(f"Found {len(confirmed_setups)} Breaker Block → MSS setups in {symbol}")
    return confirmed_setups 