"""
Market Analysis Workflow that analyzes market conditions and evaluates setups.
This workflow integrates with the setup scanner to provide market context for trading decisions.
Updated for compatibility with Prefect 3.x
"""
from prefect import task, flow
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import json
from loguru import logger

# Conditional imports with fallbacks for simplified testing
try:
    from ..agents.market_analyzer import MarketAnalyzer
    from ..utils.setup_storage import get_setups, update_setup_status
    from ..utils.data_fetcher import fetch_historical_data
except ImportError:
    logger.warning("Could not import agents - using simplified versions")
    
    class MarketAnalyzer:
        def __init__(self, config=None):
            self.config = config or {}
            
        async def process(self, data):
            # Simplified market analyzer that returns some basic metrics
            class AnalysisResult:
                def __init__(self):
                    self.indicators = {
                        "SMA": {"trend": "up" if datetime.now().day % 2 == 0 else "down"},
                        "RSI": {"value": 50},
                        "ATR": {"value": 1.0}
                    }
            return AnalysisResult()
    
    def get_setups():
        return []
        
    def update_setup_status(setup_id, status, analysis=None):
        logger.info(f"Would update setup {setup_id} to status {status}")
        return True
        
    def fetch_historical_data(symbol, timeframe, period):
        import yfinance as yf
        return yf.download(symbol, period=period, interval=timeframe)


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
        The updated setup with confluence analysis
    """
    logger.info(f"Evaluating confluence for setup {setup.get('id', 'unknown')}")
    
    # Get basic setup and market information
    setup_type = setup.get("type", "unknown")
    setup_direction = setup.get("direction", 0)  # 1 for long, -1 for short
    market_trend = market_analysis.get("trend", "unknown")
    
    # Check if the setup is aligned with the market trend
    trend_aligned = (
        (setup_direction > 0 and market_trend == "bullish") or
        (setup_direction < 0 and market_trend == "bearish")
    )
    
    # Calculate confluence score (0.0 to 1.0)
    confluence_score = 0.0
    
    if trend_aligned:
        # Higher confluence if aligned with market trend
        confluence_score += 0.5
        
        # Add more confluence based on market strength
        market_strength = market_analysis.get("strength", 50)
        if setup_direction > 0:  # Long setup
            strength_factor = (market_strength - 50) / 50  # 0.0 to 0.5
        else:  # Short setup
            strength_factor = (50 - market_strength) / 50  # 0.0 to 0.5
            
        confluence_score += max(0, strength_factor)
    
    logger.info(f"Confluence score: {confluence_score:.2f} (trend aligned: {trend_aligned})")
    
    # Update the setup with confluence information
    updated_setup = setup.copy()
    updated_setup["confluence_score"] = confluence_score
    updated_setup["trend_aligned"] = trend_aligned
    updated_setup["market_analysis"] = {
        "trend": market_trend,
        "strength": market_analysis.get("strength", 0),
        "volatility": market_analysis.get("volatility", 0)
    }
    
    return updated_setup


@task(name="Fetch Market Data")
def fetch_market_data(symbol: str, timeframe: str, period: str = "1y") -> pd.DataFrame:
    """
    Fetch market data for the given symbol and timeframe.
    
    Args:
        symbol: The ticker symbol
        timeframe: The timeframe to fetch
        period: The period to fetch data for
        
    Returns:
        A pandas DataFrame with the market data
    """
    logger.info(f"Fetching market data for {symbol} on {timeframe} timeframe")
    
    try:
        try:
            # Try to use custom data fetcher
            data = fetch_historical_data(symbol, timeframe, period)
        except:
            # Fall back to yfinance
            import yfinance as yf
            data = yf.download(symbol, period=period, interval=timeframe, progress=False)
        
        # Rename columns to lowercase for consistency
        data.columns = [col.lower() for col in data.columns]
        
        logger.info(f"Fetched {len(data)} data points for {symbol}")
        return data
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return pd.DataFrame()


@flow(name="Market Analysis Workflow")
def market_analysis_workflow(
    symbols: List[str] = ["AAPL", "MSFT", "AMZN", "GOOGL"],
    timeframes: List[str] = ["1D"],
    analyze_existing_setups: bool = True
) -> Dict[str, Any]:
    """
    Workflow that analyzes market conditions and evaluates existing setups.
    
    Args:
        symbols: List of ticker symbols to analyze
        timeframes: List of timeframes to analyze
        analyze_existing_setups: Whether to analyze existing setups
        
    Returns:
        A dictionary with the analysis results
    """
    logger.info(f"Starting market analysis workflow at {datetime.now().isoformat()}")
    logger.info(f"Analyzing {len(symbols)} symbols on {len(timeframes)} timeframes")
    
    market_analyses = {}
    updated_setups = []
    activated_setups = []
    
    # Process each symbol and timeframe combination
    for symbol in symbols:
        market_analyses[symbol] = {}
        
        for timeframe in timeframes:
            # Fetch market data
            data = fetch_market_data(symbol, timeframe, "1y")
            
            # Skip if no data was fetched
            if data.empty:
                logger.warning(f"No data fetched for {symbol} on {timeframe} timeframe")
                continue
            
            # Analyze market conditions
            market_analysis = analyze_market_conditions(symbol, timeframe, data)
            
            # Store analysis results
            market_analyses[symbol][timeframe] = market_analysis
    
    # Analyze existing setups if requested
    if analyze_existing_setups:
        logger.info("Analyzing existing setups for confluence")
        
        try:
            # Get existing setups
            existing_setups = get_setups()
            logger.info(f"Found {len(existing_setups)} existing setups to analyze")
            
            # Evaluate each setup for confluence with market conditions
            for setup in existing_setups:
                symbol = setup.get("symbol")
                timeframe = setup.get("timeframe")
                
                if symbol in market_analyses and timeframe in market_analyses[symbol]:
                    # Evaluate confluence
                    updated_setup = evaluate_setup_confluence(
                        setup=setup,
                        market_analysis=market_analyses[symbol][timeframe]
                    )
                    
                    # Update setup status based on confluence
                    confluence_score = updated_setup.get("confluence_score", 0)
                    if confluence_score >= 0.7:
                        # High confluence - activate the setup
                        update_setup_status(
                            setup_id=setup.get("id"),
                            status="active",
                            analysis={"confluence_score": confluence_score}
                        )
                        activated_setups.append(updated_setup)
                    elif confluence_score >= 0.4:
                        # Medium confluence - mark as potential
                        update_setup_status(
                            setup_id=setup.get("id"),
                            status="potential",
                            analysis={"confluence_score": confluence_score}
                        )
                    else:
                        # Low confluence - ignore
                        update_setup_status(
                            setup_id=setup.get("id"),
                            status="ignored",
                            analysis={"confluence_score": confluence_score}
                        )
                    
                    # Add to updated setups
                    updated_setups.append(updated_setup)
        except Exception as e:
            logger.error(f"Error analyzing existing setups: {str(e)}")
    
    # Return the results
    result = {
        "market_analyses": market_analyses,
        "updated_setups": updated_setups,
        "activated_setups": activated_setups,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Market analysis workflow completed at {datetime.now().isoformat()}")
    logger.info(f"Analyzed {len(market_analyses)} symbols, activated {len(activated_setups)} setups")
    
    return result 