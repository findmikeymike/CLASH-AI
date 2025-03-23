#!/usr/bin/env python3
"""
Market Analysis Workflow Without Prefect

This script implements the same functionality as the market analysis workflow
but without any dependency on Prefect, making it more reliable when Prefect
versions change.
"""
import os
import sys
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import yfinance as yf
import json
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/market_analysis_{time}.log", rotation="500 MB", level="DEBUG")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

class SimpleMarketAnalyzer:
    """A simplified market analyzer that calculates basic indicators."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the analyzer with configuration parameters."""
        self.config = config or {}
        logger.info(f"Initialized SimpleMarketAnalyzer with config: {self.config}")
    
    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market data and calculate indicators."""
        logger.info(f"Analyzing market data with {len(data)} rows")
        
        # Check column names and print them for debugging
        logger.debug(f"Available columns: {data.columns.tolist()}")
        
        # Map expected column names to actual column names
        column_mapping = {
            'close': 'Close' if 'Close' in data.columns else 'close',
            'high': 'High' if 'High' in data.columns else 'high',
            'low': 'Low' if 'Low' in data.columns else 'low',
            'open': 'Open' if 'Open' in data.columns else 'open',
            'volume': 'Volume' if 'Volume' in data.columns else 'volume'
        }
        
        # Calculate SMA indicators
        try:
            sma20 = data[column_mapping['close']].rolling(window=20).mean().iloc[-1]
            sma50 = data[column_mapping['close']].rolling(window=50).mean().iloc[-1]
            sma200 = data[column_mapping['close']].rolling(window=200).mean().iloc[-1]
            
            # Determine trend based on SMAs - convert to scalar values to avoid Series comparison
            price = data[column_mapping['close']].iloc[-1]
            price_val = float(price.iloc[0]) if hasattr(price, 'iloc') else float(price)
            sma20_val = float(sma20.iloc[0]) if hasattr(sma20, 'iloc') else float(sma20)
            sma50_val = float(sma50.iloc[0]) if hasattr(sma50, 'iloc') else float(sma50)
            sma200_val = float(sma200.iloc[0]) if hasattr(sma200, 'iloc') else float(sma200)
            
            if price_val > sma20_val > sma50_val:
                trend = "up"
            elif price_val < sma20_val < sma50_val:
                trend = "down"
            else:
                trend = "sideways"
                
            sma_indicator = {
                "value": sma20_val,
                "sma50": sma50_val,
                "sma200": sma200_val,
                "trend": trend
            }
        except Exception as e:
            logger.error(f"Error calculating SMA: {str(e)}")
            sma_indicator = {"value": 0, "trend": "unknown"}
        
        # Calculate RSI
        try:
            delta = data[column_mapping['close']].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            rsi_indicator = {"value": float(rsi.iloc[0]) if hasattr(rsi, 'iloc') else float(rsi)}
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            rsi_indicator = {"value": 50}
        
        # Calculate ATR (Average True Range)
        try:
            high_low = data[column_mapping['high']] - data[column_mapping['low']]
            high_close = abs(data[column_mapping['high']] - data[column_mapping['close']].shift())
            low_close = abs(data[column_mapping['low']] - data[column_mapping['close']].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]
            atr_indicator = {"value": float(atr.iloc[0]) if hasattr(atr, 'iloc') else float(atr)}
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            atr_indicator = {"value": 0}
        
        # Return all indicators
        return {
            "SMA": sma_indicator,
            "RSI": rsi_indicator,
            "ATR": atr_indicator
        }


def fetch_market_data(symbol: str, timeframe: str, period: str = "1y") -> pd.DataFrame:
    """
    Fetch market data for the given symbol and timeframe.
    
    Args:
        symbol: The ticker symbol
        timeframe: The timeframe to fetch data for
        period: The period to fetch data for
    """
    logger.info(f"Fetching data for {symbol} on {timeframe} timeframe")
    
    try:
        # Fetch data using yfinance
        data = yf.download(symbol, period=period, interval=timeframe, progress=False)
        
        # Check if data is empty
        if data.empty:
            logger.warning(f"No data available for {symbol}")
            return pd.DataFrame()
        
        # Log column names for debugging
        logger.debug(f"Original columns: {data.columns.tolist()}")
        
        # We'll keep the original column names instead of lowercasing them
        # This ensures compatibility with the analyzer
        
        logger.info(f"Fetched {len(data)} data points for {symbol}")
        return data
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return pd.DataFrame()


def analyze_market_conditions(
    symbol: str,
    timeframe: str,
    data: pd.DataFrame
) -> Dict[str, Any]:
    """
    Analyze market conditions using the market analyzer.
    
    Args:
        symbol: The ticker symbol
        timeframe: The timeframe of the data
        data: The market data as a pandas DataFrame
        
    Returns:
        A dictionary with market analysis results
    """
    logger.info(f"Analyzing market conditions for {symbol} on {timeframe} timeframe")
    
    # Initialize the market analyzer
    analyzer = SimpleMarketAnalyzer(config={
        "default_timeframe": timeframe,
        "indicators": ["SMA", "RSI", "ATR"]
    })
    
    # Analyze the data
    indicators = analyzer.analyze(data)
    
    # Extract key metrics from the analysis
    market_trend = "bullish" if indicators.get("SMA", {}).get("trend") == "up" else "bearish"
    market_strength = indicators.get("RSI", {}).get("value", 50)
    volatility = indicators.get("ATR", {}).get("value", 0)
    
    logger.info(f"Market analysis complete: {market_trend} trend with strength {market_strength}")
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "trend": market_trend,
        "strength": market_strength,
        "volatility": volatility,
        "indicators": indicators,
        "timestamp": datetime.now().isoformat()
    }


def get_existing_setups() -> List[Dict[str, Any]]:
    """
    Get existing setups from the database.
    
    Returns:
        A list of setup dictionaries
    """
    # In a real implementation, this would query the database
    # For now, we just return an empty list
    logger.info("Getting existing setups (simplified version returns empty list)")
    return []


def update_setup_status(setup_id: str, status: str, analysis: Optional[Dict[str, Any]] = None) -> bool:
    """
    Update the status of a setup in the database.
    
    Args:
        setup_id: The ID of the setup to update
        status: The new status to set
        analysis: Additional analysis data to store
        
    Returns:
        True if the update was successful, False otherwise
    """
    # In a real implementation, this would update the database
    # For now, we just log it
    logger.info(f"Updating setup {setup_id} to status {status} with analysis {analysis}")
    return True


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
            
        confluence_score += max(0, min(0.5, strength_factor))
    
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
            existing_setups = get_existing_setups()
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


def main():
    """Main function to run the market analysis workflow."""
    parser = argparse.ArgumentParser(description="Run market analysis workflow")
    parser.add_argument("--symbols", type=str, nargs="+", 
                        default=["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA"],
                        help="List of symbols to analyze")
    parser.add_argument("--timeframes", type=str, nargs="+", 
                        default=["1D", "4H", "1H"],
                        help="List of timeframes to analyze")
    parser.add_argument("--analyze-setups", action="store_true", default=True,
                        help="Analyze existing setups for confluence")
    args = parser.parse_args()
    
    logger.info(f"Starting market analysis at {datetime.now().isoformat()}")
    logger.info(f"Analyzing symbols: {args.symbols}")
    logger.info(f"Analyzing timeframes: {args.timeframes}")
    
    # Run the workflow
    result = market_analysis_workflow(
        symbols=args.symbols,
        timeframes=args.timeframes,
        analyze_existing_setups=args.analyze_setups
    )
    
    logger.info(f"Market analysis workflow completed.")
    logger.info(f"Analyzed {len(result['market_analyses'])} symbols")
    logger.info(f"Updated {len(result['updated_setups'])} setups")
    logger.info(f"Activated {len(result['activated_setups'])} setups")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 