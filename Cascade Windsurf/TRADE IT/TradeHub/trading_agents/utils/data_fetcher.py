"""
Data fetching utilities for retrieving market data.
"""
import os
import pandas as pd
import yfinance as yf
from loguru import logger
from typing import List, Dict, Any, Optional

def fetch_historical_data(symbol: str, timeframe: str = "1d", period: str = "1y") -> List[Dict[str, Any]]:
    """
    Fetch historical price data for a given symbol.
    
    Args:
        symbol: The ticker symbol to fetch data for
        timeframe: The timeframe for the data (e.g., 1d, 1h, 15m)
        period: The period to fetch data for (e.g., 1d, 5d, 1mo, 3mo, 1y, 2y, 5y, 10y, ytd, max)
        
    Returns:
        A list of dictionaries containing OHLCV data
    """
    # Map timeframes to Yahoo Finance intervals
    timeframe_map = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",  # Note: Yahoo Finance doesn't directly support 4h
        "1d": "1d",
        "1w": "1wk"
    }
    
    # Use the mapped interval or default to daily
    interval = timeframe_map.get(timeframe, "1d")
    
    try:
        # For 4h timeframe, we fetch hourly data and resample
        if timeframe == "4h":
            # Fetch hourly data and resample to 4h
            data = yf.download(symbol, period=period, interval="1h")
            data = data.resample('4H').agg({
                'Open': 'first', 
                'High': 'max', 
                'Low': 'min', 
                'Close': 'last',
                'Volume': 'sum'
            })
        else:
            # Fetch data directly
            data = yf.download(symbol, period=period, interval=interval)
        
        # Convert to list of dictionaries
        result = []
        for index, row in data.iterrows():
            # Convert pandas Series to dict with proper handling of potentially nested Series objects
            ohlcv = {
                "date": index.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": float(row['Open'] if hasattr(row, 'iloc') else row['Open']),
                "high": float(row['High'] if hasattr(row, 'iloc') else row['High']),
                "low": float(row['Low'] if hasattr(row, 'iloc') else row['Low']),
                "close": float(row['Close'] if hasattr(row, 'iloc') else row['Close']),
                "volume": int(row['Volume'] if hasattr(row, 'iloc') else row['Volume'])
            }
            result.append(ohlcv)
        
        logger.info(f"Fetched {len(result)} {interval} data points for {symbol}")
        return result
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        # Return empty list in case of error
        return [] 