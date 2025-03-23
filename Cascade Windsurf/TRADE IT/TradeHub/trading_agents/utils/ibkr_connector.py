"""
Interactive Brokers (IBKR) Market Data Integration

This module provides functionality to connect to Interactive Brokers API for real-time and historical market data.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger
from typing import Dict, List, Any, Optional, Callable, Union, Tuple

# Import ib_insync
try:
    from ib_insync import IB, Contract, Stock, Option, BarData, util
    import ib_insync
    IBKR_AVAILABLE = True
except ImportError:
    logger.warning("IB Insync not installed. Run 'pip install ib_insync' to enable IBKR market data.")
    IBKR_AVAILABLE = False

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/ibkr_connector_{time}.log", rotation="500 MB", level="DEBUG")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# IBKR connection parameters
IBKR_HOST = "127.0.0.1"  # TWS or IB Gateway address
IBKR_PORT = 7496         # Using live trading port (7496) instead of paper trading port (7497)
IBKR_CLIENT_ID = 1       # Unique client ID

# Map our timeframes to IBKR timeframes
TIMEFRAME_MAP = {
    "1m": "1 min",
    "5m": "5 mins",
    "15m": "15 mins",
    "15min": "15 mins",
    "30m": "30 mins",
    "30min": "30 mins",
    "1H": "1 hour",
    "4H": "4 hours",
    "1D": "1 day",
    "1W": "1 week",
    "1M": "1 month"
}

# Singleton IB connection
_ib_connection = None

def get_ib_connection() -> Optional[IB]:
    """
    Get or create the IB connection.
    
    Returns:
        IB connection object or None if connection fails
    """
    global _ib_connection
    
    if not IBKR_AVAILABLE:
        logger.error("IB Insync not installed. Cannot connect to IBKR.")
        return None
    
    if _ib_connection is None or not _ib_connection.isConnected():
        try:
            _ib_connection = IB()
            _ib_connection.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)
            logger.info(f"Connected to IBKR at {IBKR_HOST}:{IBKR_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            _ib_connection = None
    
    return _ib_connection

def disconnect_ib():
    """Disconnect from Interactive Brokers."""
    global _ib_connection
    
    if _ib_connection is not None and _ib_connection.isConnected():
        _ib_connection.disconnect()
        logger.info("Disconnected from IBKR")
        _ib_connection = None

def create_stock_contract(symbol: str) -> Optional[Contract]:
    """
    Create a stock contract for the given symbol.
    
    Args:
        symbol: The stock symbol
        
    Returns:
        Stock contract or None if creation fails
    """
    if not IBKR_AVAILABLE:
        logger.error("IB Insync not installed. Cannot create stock contract.")
        return None
    
    try:
        contract = Stock(symbol, 'SMART', 'USD')
        return contract
    except Exception as e:
        logger.error(f"Failed to create stock contract for {symbol}: {e}")
        return None

def create_option_contract(symbol: str, expiry: str, strike: float, option_type: str) -> Optional[Contract]:
    """
    Create an option contract for the given parameters.
    
    Args:
        symbol: The underlying stock symbol
        expiry: Option expiry date in format 'YYYYMMDD'
        strike: Option strike price
        option_type: 'C' for call, 'P' for put
        
    Returns:
        Option contract or None if creation fails
    """
    if not IBKR_AVAILABLE:
        logger.error("IB Insync not installed. Cannot create option contract.")
        return None
    
    try:
        contract = Option(symbol, expiry, strike, option_type, 'SMART', multiplier=100)
        return contract
    except Exception as e:
        logger.error(f"Failed to create option contract for {symbol} {expiry} {strike} {option_type}: {e}")
        return None

def fetch_historical_data(
    symbol: str, 
    timeframe: str = "1D", 
    duration: str = "1 Y",
    what_to_show: str = "TRADES",
    use_rth: bool = True
) -> pd.DataFrame:
    """
    Fetch historical price data for a given symbol using IBKR API.
    
    Args:
        symbol: The ticker symbol to fetch data for
        timeframe: The timeframe for the data (e.g., 1D, 1H, 15m)
        duration: How far back to fetch data (e.g., "1 D", "1 W", "1 M", "1 Y")
        what_to_show: Type of data to fetch (TRADES, BID, ASK, MIDPOINT, etc.)
        use_rth: Whether to use regular trading hours only
        
    Returns:
        A pandas DataFrame with OHLCV data
    """
    if not IBKR_AVAILABLE:
        logger.error("IB Insync not installed. Cannot fetch historical data.")
        return pd.DataFrame()
    
    # Get the mapped timeframe
    bar_size = TIMEFRAME_MAP.get(timeframe)
    if not bar_size:
        logger.error(f"Unsupported timeframe: {timeframe}")
        return pd.DataFrame()
    
    # Get IB connection
    ib = get_ib_connection()
    if ib is None:
        return pd.DataFrame()
    
    try:
        # Create contract
        contract = create_stock_contract(symbol)
        if contract is None:
            return pd.DataFrame()
        
        # Fetch historical data
        bars = ib.reqHistoricalData(
            contract,
            endDateTime='',  # '' for latest data
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=use_rth,
            formatDate=1  # 1 for dates as 'YYYYMMDD'
        )
        
        if not bars:
            logger.warning(f"No historical data returned for {symbol}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = util.df(bars)
        
        # Rename columns to match our standard format
        column_mapping = {
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'average': 'vwap',
            'barCount': 'bar_count'
        }
        
        # Rename columns that exist in the DataFrame
        rename_cols = {col: column_mapping[col] for col in df.columns if col in column_mapping}
        df = df.rename(columns=rename_cols)
        
        # Set date as index
        if 'date' in df.columns:
            df.set_index('date', inplace=True)
        
        logger.info(f"Fetched {len(df)} {timeframe} data points for {symbol} from IBKR")
        return df
    
    except Exception as e:
        logger.error(f"Error fetching {symbol} data from IBKR: {e}")
        return pd.DataFrame()

def fetch_real_time_data(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch real-time market data for a symbol.
    
    Args:
        symbol: The ticker symbol
        
    Returns:
        Dictionary with real-time market data or None if fetch fails
    """
    if not IBKR_AVAILABLE:
        logger.error("IB Insync not installed. Cannot fetch real-time data.")
        return None
    
    # Get IB connection
    ib = get_ib_connection()
    if ib is None:
        return None
    
    try:
        # Create contract
        contract = create_stock_contract(symbol)
        if contract is None:
            return None
        
        # Request market data
        ib.reqMktData(contract)
        
        # Wait for data to arrive
        ib.sleep(1)
        
        # Get the ticker
        tickers = ib.reqTickers(contract)
        if not tickers:
            logger.warning(f"No real-time data returned for {symbol}")
            return None
        
        ticker = tickers[0]
        
        # Format the data
        data = {
            'symbol': symbol,
            'last_price': ticker.last,
            'bid': ticker.bid,
            'ask': ticker.ask,
            'volume': ticker.volume,
            'high': ticker.high,
            'low': ticker.low,
            'close': ticker.close,
            'timestamp': datetime.now().isoformat()
        }
        
        return data
    
    except Exception as e:
        logger.error(f"Error fetching real-time data for {symbol}: {e}")
        return None

def subscribe_to_market_data(symbol: str, callback: Callable[[Dict[str, Any]], None]) -> bool:
    """
    Subscribe to real-time market data updates for a symbol.
    
    Args:
        symbol: The ticker symbol
        callback: Function to call when new data arrives
        
    Returns:
        True if subscription successful, False otherwise
    """
    if not IBKR_AVAILABLE:
        logger.error("IB Insync not installed. Cannot subscribe to market data.")
        return False
    
    # Get IB connection
    ib = get_ib_connection()
    if ib is None:
        return False
    
    try:
        # Create contract
        contract = create_stock_contract(symbol)
        if contract is None:
            return False
        
        # Define update handler
        def handle_ticker_update(ticker):
            # Format the data
            data = {
                'symbol': symbol,
                'last_price': ticker.last,
                'bid': ticker.bid,
                'ask': ticker.ask,
                'volume': ticker.volume,
                'high': ticker.high,
                'low': ticker.low,
                'close': ticker.close,
                'timestamp': datetime.now().isoformat()
            }
            
            # Call the callback
            callback(data)
        
        # Request market data
        ib.reqMktData(contract)
        
        # Set up the ticker update callback
        ib.pendingTickersEvent += handle_ticker_update
        
        logger.info(f"Subscribed to real-time market data for {symbol}")
        return True
    
    except Exception as e:
        logger.error(f"Error subscribing to market data for {symbol}: {e}")
        return False

def fetch_option_chain(symbol: str) -> pd.DataFrame:
    """
    Fetch the option chain for a symbol.
    
    Args:
        symbol: The underlying stock symbol
        
    Returns:
        DataFrame with option chain data
    """
    if not IBKR_AVAILABLE:
        logger.error("IB Insync not installed. Cannot fetch option chain.")
        return pd.DataFrame()
    
    # Get IB connection
    ib = get_ib_connection()
    if ib is None:
        return pd.DataFrame()
    
    try:
        # Create contract for the underlying
        contract = create_stock_contract(symbol)
        if contract is None:
            return pd.DataFrame()
        
        # Request contract details to get the contract ID
        details = ib.reqContractDetails(contract)
        if not details:
            logger.warning(f"No contract details found for {symbol}")
            return pd.DataFrame()
        
        # Get the contract ID
        conId = details[0].contract.conId
        
        # Request option chain
        chains = ib.reqSecDefOptParams(symbol, '', 'STK', conId)
        if not chains:
            logger.warning(f"No option chain data found for {symbol}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = util.df(chains)
        
        logger.info(f"Fetched option chain for {symbol} with {len(df)} rows")
        return df
    
    except Exception as e:
        logger.error(f"Error fetching option chain for {symbol}: {e}")
        return pd.DataFrame()

def fetch_option_data(
    symbol: str, 
    expiry: str, 
    strike: float, 
    option_type: str,
    timeframe: str = "1D",
    duration: str = "1 M"
) -> pd.DataFrame:
    """
    Fetch historical data for a specific option.
    
    Args:
        symbol: The underlying stock symbol
        expiry: Option expiry date in format 'YYYYMMDD'
        strike: Option strike price
        option_type: 'C' for call, 'P' for put
        timeframe: The timeframe for the data (e.g., 1D, 1H, 15m)
        duration: How far back to fetch data (e.g., "1 D", "1 W", "1 M", "1 Y")
        
    Returns:
        DataFrame with option price data
    """
    if not IBKR_AVAILABLE:
        logger.error("IB Insync not installed. Cannot fetch option data.")
        return pd.DataFrame()
    
    # Get the mapped timeframe
    bar_size = TIMEFRAME_MAP.get(timeframe)
    if not bar_size:
        logger.error(f"Unsupported timeframe: {timeframe}")
        return pd.DataFrame()
    
    # Get IB connection
    ib = get_ib_connection()
    if ib is None:
        return pd.DataFrame()
    
    try:
        # Create option contract
        contract = create_option_contract(symbol, expiry, strike, option_type)
        if contract is None:
            return pd.DataFrame()
        
        # Fetch historical data
        bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow='TRADES',
            useRTH=True,
            formatDate=1
        )
        
        if not bars:
            logger.warning(f"No historical data returned for {symbol} option")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = util.df(bars)
        
        # Rename columns to match our standard format
        column_mapping = {
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'average': 'vwap',
            'barCount': 'bar_count'
        }
        
        # Rename columns that exist in the DataFrame
        rename_cols = {col: column_mapping[col] for col in df.columns if col in column_mapping}
        df = df.rename(columns=rename_cols)
        
        # Set date as index
        if 'date' in df.columns:
            df.set_index('date', inplace=True)
        
        logger.info(f"Fetched {len(df)} {timeframe} data points for {symbol} option")
        return df
    
    except Exception as e:
        logger.error(f"Error fetching option data: {e}")
        return pd.DataFrame()

def is_market_open() -> bool:
    """
    Check if the US stock market is currently open via IBKR.
    
    Returns:
        True if market is open, False otherwise
    """
    if not IBKR_AVAILABLE:
        logger.error("IB Insync not installed. Cannot check market status.")
        return False
    
    # Get IB connection
    ib = get_ib_connection()
    if ib is None:
        return False
    
    try:
        # Create a contract for SPY (as a proxy for US market)
        contract = create_stock_contract('SPY')
        if contract is None:
            return False
        
        # Request market data
        ib.reqMktData(contract)
        
        # Wait for data to arrive
        ib.sleep(1)
        
        # Get the ticker
        tickers = ib.reqTickers(contract)
        if not tickers:
            logger.warning("No market data returned for SPY")
            return False
        
        ticker = tickers[0]
        
        # If we have a last price and it's during trading hours, market is open
        return ticker.last is not None and ticker.last > 0
    
    except Exception as e:
        logger.error(f"Error checking market status: {e}")
        return False

# Test function to verify IBKR connection and data fetching
def test_ibkr_connection():
    """Test the IBKR connection and data fetching."""
    if not IBKR_AVAILABLE:
        logger.error("IB Insync not installed. Cannot test connection.")
        return
    
    try:
        # Connect to IBKR
        ib = get_ib_connection()
        if ib is None:
            logger.error("Failed to connect to IBKR")
            return
        
        # Check if connected
        if ib.isConnected():
            logger.info("Successfully connected to IBKR")
            
            # Test fetching historical data for AAPL
            df = fetch_historical_data('AAPL', '1D', '1 M')
            if not df.empty:
                logger.info(f"Successfully fetched {len(df)} data points for AAPL")
                logger.info(f"Sample data:\n{df.head()}")
            else:
                logger.error("Failed to fetch historical data for AAPL")
            
            # Disconnect
            disconnect_ib()
        else:
            logger.error("Not connected to IBKR")
    
    except Exception as e:
        logger.error(f"Error testing IBKR connection: {e}")

if __name__ == "__main__":
    # Test the IBKR connection
    test_ibkr_connection() 