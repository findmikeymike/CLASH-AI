#!/usr/bin/env python
"""
Test script for the EnhancedOptionsExpertAgent.
This script tests the functionality of the enhanced options agent with simulated data.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from loguru import logger

from trading_agents.agents.enhanced_options_agent import EnhancedOptionsExpertAgent

def test_enhanced_options_agent():
    """Test the EnhancedOptionsExpertAgent with simulated data."""
    logger.info("Testing EnhancedOptionsExpertAgent...")
    
    # Initialize the agent with specific parameters
    agent = EnhancedOptionsExpertAgent(
        volume_threshold=3.0,
        open_interest_ratio=1.5,
        stop_hunt_sensitivity=0.7
    )
    
    # Test with different tickers
    for ticker in ['AAPL', 'MSFT', 'TSLA', 'AMZN', 'NVDA']:
        logger.info(f"\n==================================================")
        logger.info(f"Testing with ticker: {ticker}")
        logger.info(f"==================================================")
        
        # Create test data
        test_data = {
            'ticker': ticker,
            'price_data': pd.DataFrame({
                'Date': pd.date_range(end=pd.Timestamp.now(), periods=30),
                'Open': np.random.uniform(90, 110, 30),
                'High': np.random.uniform(95, 115, 30),
                'Low': np.random.uniform(85, 105, 30),
                'Close': np.random.uniform(90, 110, 30),
                'Volume': np.random.randint(1000000, 10000000, 30)
            })
        }
        
        # Process the data
        result = agent.process(test_data)
        
        # Log the results
        logger.info(f"Options Analysis for {ticker}:")
        logger.info(f"  Sentiment: {result['options_analysis']['sentiment']}")
        logger.info(f"  Confidence: {result['options_analysis']['confidence']}")
        
        logger.info(f"\nUnusual Activity:")
        logger.info(f"  Call/Put Ratio: {result['unusual_activity']['call_put_ratio']:.2f}")
        logger.info(f"  IV Percentile: {result['unusual_activity']['iv_percentile']:.2f}")
        
        logger.info(f"\nSweep Activity:")
        logger.info(f"  Call Sweep Volume: {result['sweep_activity']['call_sweep_volume']}")
        logger.info(f"  Put Sweep Volume: {result['sweep_activity']['put_sweep_volume']}")
        
        logger.info(f"\nGEX Analysis:")
        logger.info(f"  Current GEX: {result['gex_analysis']['current_gex']}")
        logger.info(f"  GEX Skew: {result['gex_analysis']['gex_skew']}")
        logger.info(f"  Largest GEX Level: {result['gex_analysis']['largest_gex_level']}")
        
        if result['risk_warnings']:
            logger.info(f"\nRisk Warnings:")
            for warning in result['risk_warnings']:
                logger.info(f"  {warning}")
        
        if result['stop_hunt_warnings']['has_stop_hunt']:
            logger.info(f"\nStop Hunt Warnings:")
            if result['stop_hunt_warnings']['upward_stop_hunt']['detected']:
                logger.info(f"  Upward Stop Hunt Detected")
            if result['stop_hunt_warnings']['downward_stop_hunt']['detected']:
                logger.info(f"  Downward Stop Hunt Detected")
            logger.info(f"  Risk Level: {result['stop_hunt_warnings']['risk_level']}")
        
        logger.info(f"\nRecommended Contracts:")
        for contract in result['recommended_contracts']:
            logger.info(f"  {contract['type']} {contract['strike']} {contract['expiration']} - IV: {contract['iv']:.2f}, Delta: {contract['delta']:.2f}")
        
        logger.info(f"Recommended Strategy: {result['recommended_strategy']}")
        
        # Save the results to a file
        with open(f"{ticker}_options_analysis.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"Saved detailed results to {ticker}_options_analysis.json")

if __name__ == "__main__":
    test_enhanced_options_agent() 