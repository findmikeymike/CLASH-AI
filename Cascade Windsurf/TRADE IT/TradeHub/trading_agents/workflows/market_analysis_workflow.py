"""
Market Analysis Workflow that analyzes market conditions and evaluates setups.
This workflow integrates with the setup scanner to provide market context for trading decisions.
"""
from prefect import flow, task
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import json
from loguru import logger

from ..agents.market_analyzer import MarketAnalyzer
from ..utils.setup_storage import get_setups, update_setup_status
from ..utils.data_fetcher import fetch_historical_data

@task(name="Analyze Market Conditions")
def analyze_market_conditions(
    symbol: str,
    timeframe: str,
    data: pd.DataFrame
) -> Dict[str, Any]:
    """
    Analyze market conditions using the MarketAnalyzer agent.
    
    Args:
        symbol: The ticker symbol
        timeframe: The timeframe of the data
        data: The market data as a pandas DataFrame
        
    Returns:
        A dictionary with market analysis results
    """
    logger.info(f"Analyzing market conditions for {symbol} on {timeframe} timeframe")
    
    # Initialize the market analyzer
    analyzer = MarketAnalyzer(config={
        "default_timeframe": timeframe,
        "indicators": ["SMA", "RSI", "MACD", "ATR", "Bollinger"]
    })
    
    # Process the data synchronously (since we're in a Prefect task)
    analysis_input = {
        "symbol": symbol,
        "timeframe": timeframe,
        "data": data
    }
    
    # Since the agent's process method is async, we need to run it synchronously
    import asyncio
    analysis_result = asyncio.run(analyzer.process(analysis_input))
    
    # Extract key metrics from the analysis
    market_trend = "bullish" if analysis_result.indicators.get("SMA", {}).get("trend") == "up" else "bearish"
    market_strength = analysis_result.indicators.get("RSI", {}).get("value", 50)
    volatility = analysis_result.indicators.get("ATR", {}).get("value", 0)
    
    logger.info(f"Market analysis complete: {market_trend} trend with strength {market_strength}")
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "trend": market_trend,
        "strength": market_strength,
        "volatility": volatility,
        "indicators": analysis_result.indicators,
        "timestamp": datetime.now().isoformat()
    }

@task(name="Evaluate Setup Confluence")
def evaluate_setup_confluence(
    setup: Dict[str, Any],
    market_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate if a setup is confluent with overall market conditions.
    
    Args:
        setup: The trading setup to evaluate
        market_analysis: The market analysis results
        
    Returns:
        The updated setup with confluence score
    """
    logger.info(f"Evaluating confluence for {setup['setup_type']} setup on {setup['symbol']}")
    
    # Extract setup direction and market trend
    setup_direction = setup["direction"]
    market_trend = market_analysis["trend"]
    market_strength = market_analysis["strength"]
    
    # Calculate confluence score (0-100)
    confluence_score = 0
    
    # Check if setup direction aligns with market trend
    if setup_direction == market_trend:
        confluence_score += 40  # Major factor: alignment with trend
        logger.info(f"Setup direction {setup_direction} aligns with market trend {market_trend}")
    else:
        logger.info(f"Setup direction {setup_direction} against market trend {market_trend}")
    
    # Add points based on market strength
    if setup_direction == "bullish" and market_strength > 50:
        # For bullish setups, higher RSI is better
        confluence_score += min(30, (market_strength - 50) * 0.6)
    elif setup_direction == "bearish" and market_strength < 50:
        # For bearish setups, lower RSI is better
        confluence_score += min(30, (50 - market_strength) * 0.6)
    
    # Add points for risk/reward ratio
    risk_reward = setup.get("risk_reward", 0)
    if risk_reward >= 3:
        confluence_score += 20
    elif risk_reward >= 2:
        confluence_score += 15
    elif risk_reward >= 1.5:
        confluence_score += 10
    
    # Round the score
    confluence_score = round(confluence_score)
    
    # Update the setup with confluence information
    updated_setup = setup.copy()
    updated_setup["confluence_score"] = confluence_score
    updated_setup["market_aligned"] = setup_direction == market_trend
    updated_setup["market_analysis"] = {
        "trend": market_trend,
        "strength": market_strength,
        "volatility": market_analysis["volatility"]
    }
    
    # Determine if the setup should be activated based on confluence
    if confluence_score >= 70:
        updated_setup["status"] = "activated"
        logger.info(f"Setup activated with high confluence score: {confluence_score}")
    elif confluence_score >= 50:
        updated_setup["status"] = "watching"
        logger.info(f"Setup set to watching with moderate confluence score: {confluence_score}")
    else:
        updated_setup["status"] = "low_confluence"
        logger.info(f"Setup marked as low confluence with score: {confluence_score}")
    
    return updated_setup

@flow(name="Market Analysis Workflow")
def market_analysis_workflow(
    symbols: List[str] = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA"],
    timeframes: List[str] = ["1D", "4H", "1H"],
    analyze_existing_setups: bool = True
) -> Dict[str, Any]:
    """
    Main workflow for analyzing market conditions and evaluating setups.
    
    Args:
        symbols: List of symbols to analyze
        timeframes: List of timeframes to analyze
        analyze_existing_setups: Whether to analyze existing setups in the database
        
    Returns:
        A dictionary with the results of the analysis
    """
    logger.info(f"Starting market analysis workflow for {len(symbols)} symbols on {len(timeframes)} timeframes")
    
    market_analyses = {}
    updated_setups = []
    
    # Analyze market conditions for each symbol and timeframe
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                # Fetch historical data
                raw_data = fetch_historical_data(symbol, timeframe, limit=200)
                
                # Convert to pandas DataFrame
                df = pd.DataFrame(raw_data)
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
                
                # Analyze market conditions
                market_analysis = analyze_market_conditions(symbol, timeframe, df)
                
                # Store the analysis for later use
                key = f"{symbol}_{timeframe}"
                market_analyses[key] = market_analysis
                
                logger.info(f"Completed market analysis for {symbol} on {timeframe}")
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol} on {timeframe}: {str(e)}")
    
    # If requested, analyze existing setups
    if analyze_existing_setups:
        logger.info("Analyzing existing setups from database")
        
        # Get active setups from the database
        active_setups = get_setups(status="active")
        logger.info(f"Found {len(active_setups)} active setups to evaluate")
        
        # Evaluate each setup for confluence with market conditions
        for setup in active_setups:
            try:
                # Get the corresponding market analysis
                key = f"{setup['symbol']}_{setup['timeframe']}"
                if key in market_analyses:
                    # Evaluate setup confluence
                    updated_setup = evaluate_setup_confluence(setup, market_analyses[key])
                    
                    # Update the setup status in the database
                    if updated_setup["status"] != setup["status"]:
                        update_setup_status(setup["id"], updated_setup["status"])
                    
                    updated_setups.append(updated_setup)
                else:
                    logger.warning(f"No market analysis available for {key}, skipping setup evaluation")
            
            except Exception as e:
                logger.error(f"Error evaluating setup {setup['id']}: {str(e)}")
    
    logger.info(f"Market analysis workflow completed. Evaluated {len(updated_setups)} setups.")
    
    return {
        "market_analyses": market_analyses,
        "updated_setups": updated_setups,
        "activated_setups": [s for s in updated_setups if s["status"] == "activated"],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Run the workflow with default settings
    market_analysis_workflow() 