"""
Alpaca Market Data Integration

This module provides functionality to connect to Alpaca's API for real-time and historical market data.
"""
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from typing import Dict, List, Any, Optional, Callable

# We'll use the alpaca-py library for simplicity
try:
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    from alpaca.data.live import StockDataStream
    from alpaca.common.exceptions import APIError
    ALPACA_AVAILABLE = True
except ImportError:
    logger.warning("Alpaca SDK not installed. Run 'pip install alpaca-py' to enable live market data.")
    ALPACA_AVAILABLE = False

# Alpaca credentials - in production these would be stored securely
ALPACA_API_KEY = "AK7ONMIZZ3CQW5GOB4"
ALPACA_API_SECRET = "q5E8eJL5POu5GNWAnRoOMHkHwTCJcbpfCc6YCbUM"
ALPACA_BASE_URL = "https://api.alpaca.markets"

# Map our timeframes to Alpaca timeframes
TIMEFRAME_MAP = {}
if ALPACA_AVAILABLE:
    # The TimeFrame class has predefined constants for common timeframes
    TIMEFRAME_MAP = {
        "1m": TimeFrame.Minute,  # 1Min
        "5m": TimeFrame.Minute,  # We'll adjust to 5Min in the request
        "15m": TimeFrame.Minute, # We'll adjust to 15Min in the request
        "30m": TimeFrame.Minute, # We'll adjust to 30Min in the request
        "1h": TimeFrame.Hour,    # 1Hour
        "4h": TimeFrame.Hour,    # We'll adjust to 4Hour in the request
        "1d": TimeFrame.Day,     # 1Day
        "1w": TimeFrame.Week     # 1Week
    }

# Singleton historical data client
_historical_client = None

def get_historical_client():
    """Get or create the historical data client."""
    global _historical_client
    if _historical_client is None and ALPACA_AVAILABLE:
        _historical_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_API_SECRET)
    return _historical_client

def fetch_historical_data(symbol: str, timeframe: str = "1d", limit: int = 200) -> List[Dict[str, Any]]:
    """
    Fetch historical price data for a given symbol using Alpaca API.
    
    Args:
        symbol: The ticker symbol to fetch data for
        timeframe: The timeframe for the data (e.g., 1d, 1h, 15m)
        limit: The number of data points to return
        
    Returns:
        A list of dictionaries containing OHLCV data
    """
    if not ALPACA_AVAILABLE:
        logger.error("Alpaca SDK not installed. Cannot fetch historical data.")
        return []
    
    # Get the mapped timeframe - we'll handle non-standard periods below
    base_timeframe = TIMEFRAME_MAP.get(timeframe)
    if not base_timeframe:
        logger.error(f"Unsupported timeframe: {timeframe}")
        return []
    
    try:
        # Calculate start and end times
        end = datetime.now()
        
        # For different timeframes, we need different lookback periods to ensure we get enough data
        if timeframe in ["1m", "5m", "15m", "30m"]:
            # Maximum lookback for minute data is 7 days
            start = end - timedelta(days=7)
        elif timeframe in ["1h", "4h"]:
            # For hourly data, look back 60 days
            start = end - timedelta(days=60)
        else:
            # For daily data and above, look back 1500 days
            start = end - timedelta(days=1500)
        
        # Extract multiplier from timeframe if needed (e.g., 5m → 5)
        multiplier = 1
        if timeframe not in ["1m", "1h", "1d", "1w"]:
            multiplier = int(timeframe.replace("m", "").replace("h", "").replace("d", "").replace("w", ""))
        
        # Create the request
        request_params = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=base_timeframe,
            start=start,
            end=end,
            limit=limit,
            adjustment='all',  # Split and dividend adjusted
            multiplier=multiplier  # Apply multiplier for non-standard periods (e.g., 5m, 15m, 4h)
        )
        
        # Get the client and fetch data
        client = get_historical_client()
        bars = client.get_stock_bars(request_params)
        
        # Convert to our standard format
        result = []
        
        # Process the bars data
        if symbol in bars:
            symbol_bars = bars[symbol]
            
            for bar in symbol_bars:
                result.append({
                    "date": bar.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": int(bar.volume)
                })
        
        logger.info(f"Fetched {len(result)} {timeframe} data points for {symbol} from Alpaca")
        return result
    
    except APIError as e:
        logger.error(f"Alpaca API error fetching {symbol}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching {symbol} data from Alpaca: {e}")
        return []

# Real-time data stream
class AlpacaDataStream:
    """Class to manage real-time data streaming from Alpaca."""
    
    def __init__(self):
        self.stream = None
        self.connected = False
        self.subscribed_symbols = set()
        self.callbacks = {}
    
    def connect(self):
        """Connect to the Alpaca data stream."""
        if not ALPACA_AVAILABLE:
            logger.error("Alpaca SDK not installed. Cannot connect to data stream.")
            return False
        
        try:
            self.stream = StockDataStream(ALPACA_API_KEY, ALPACA_API_SECRET)
            self.connected = True
            logger.info("Connected to Alpaca data stream")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Alpaca data stream: {e}")
            self.connected = False
            return False
    
    def subscribe(self, symbol: str, callback: Callable):
        """Subscribe to updates for a symbol."""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            # Store the callback
            if symbol not in self.callbacks:
                self.callbacks[symbol] = []
            self.callbacks[symbol].append(callback)
            
            # If not already subscribed, subscribe now
            if symbol not in self.subscribed_symbols:
                async def handle_bar(bar):
                    # Format the bar data
                    data = {
                        "symbol": bar.symbol,
                        "date": bar.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": int(bar.volume)
                    }
                    
                    # Call all callbacks registered for this symbol
                    for cb in self.callbacks.get(bar.symbol, []):
                        cb(data)
                
                # Subscribe to minute bars
                self.stream.subscribe_bars(handle_bar, symbol)
                self.subscribed_symbols.add(symbol)
                logger.info(f"Subscribed to {symbol} real-time data")
            
            return True
        except Exception as e:
            logger.error(f"Error subscribing to {symbol}: {e}")
            return False
    
    def start(self):
        """Start the data stream processing."""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            # Start the stream asynchronously
            import threading
            thread = threading.Thread(target=self._run_stream)
            thread.daemon = True
            thread.start()
            return True
        except Exception as e:
            logger.error(f"Error starting data stream: {e}")
            return False
    
    def _run_stream(self):
        """Run the stream in a separate thread."""
        try:
            self.stream.run()
        except Exception as e:
            logger.error(f"Error in data stream: {e}")
            self.connected = False

# Create a singleton instance
data_stream = AlpacaDataStream()

def initialize_real_time_data():
    """Initialize the real-time data stream."""
    return data_stream.connect()

def subscribe_to_symbol(symbol: str, callback: Callable):
    """Subscribe to real-time updates for a symbol."""
    return data_stream.subscribe(symbol, callback)

def start_data_stream():
    """Start the real-time data stream."""
    return data_stream.start() 