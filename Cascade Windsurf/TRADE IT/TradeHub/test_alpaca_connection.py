#!/usr/bin/env python
"""
Alpaca Connection Diagnostic Tool

This script tests the connectivity to Alpaca API and verifies that data can be
successfully retrieved. It's designed to be a simple diagnostic tool.
"""
from loguru import logger
import sys
import os
import json
from datetime import datetime, timedelta

# Configure logger to output to console
logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

logger.info("Starting Alpaca Connection Diagnostic Tool")

try:
    # Import Alpaca modules
    logger.info("Importing Alpaca modules")
    
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    from alpaca.data.live import StockDataStream
    from alpaca.common.exceptions import APIError
    
    logger.success("Successfully imported Alpaca modules")
except ImportError as e:
    logger.error(f"Failed to import Alpaca modules: {e}")
    logger.error("Please install Alpaca SDK with: pip install alpaca-py")
    sys.exit(1)

# Get Alpaca credentials (try from environment or use defaults)
ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "AK7ONMIZZ3CQW5GOB4")
ALPACA_API_SECRET = os.environ.get("ALPACA_API_SECRET", "q5E8eJL5POu5GNWAnRoOMHkHwTCJcbpfCc6YCbUM")

logger.info(f"Using Alpaca API Key: {ALPACA_API_KEY[:4]}...{ALPACA_API_KEY[-4:]}")

# Test 1: Create a historical data client
try:
    logger.info("Creating historical data client")
    client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_API_SECRET)
    logger.success("Successfully created historical data client")
except Exception as e:
    logger.error(f"Failed to create historical data client: {e}")
    sys.exit(1)

# Test 2: Fetch historical data
try:
    logger.info("Fetching historical data for AAPL")
    
    # Get data for the last week
    end = datetime.now()
    start = end - timedelta(days=7)
    
    request_params = StockBarsRequest(
        symbol_or_symbols=["AAPL"],
        timeframe=TimeFrame.Day,
        start=start,
        end=end
    )
    
    bars = client.get_stock_bars(request_params)
    
    # Check if we got data
    aapl_bars = bars.get("AAPL", None)
    if aapl_bars is None or len(aapl_bars) == 0:
        logger.warning("No data returned for AAPL")
    else:
        logger.success(f"Successfully fetched {len(aapl_bars)} bars for AAPL")
        logger.info(f"Latest price: ${aapl_bars[-1].close}")
except APIError as e:
    logger.error(f"Alpaca API Error: {e}")
    # Check if this is an authentication error
    if "authentication" in str(e).lower():
        logger.error("Authentication failed. Please check your API key and secret.")
except Exception as e:
    logger.error(f"Failed to fetch historical data: {e}")

# Test 3: Test WebSocket connection
try:
    logger.info("Testing WebSocket connection")
    
    # Create a WebSocket connection
    stream = StockDataStream(ALPACA_API_KEY, ALPACA_API_SECRET)
    
    # Define callback for connection success
    async def on_connect():
        logger.success("WebSocket connected successfully")
        # Close the connection after successfully connecting
        stream.close()
    
    # Set up the connection handler
    stream.add_on_connect_callback(on_connect)
    
    # Run the connection test (with timeout)
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    import threading
    
    connected_event = threading.Event()
    
    async def wait_for_connection():
        try:
            # Try to connect and wait for a bit
            await stream._connect()
            connected_event.set()
        except Exception as e:
            logger.error(f"Error in WebSocket connection: {e}")
    
    # Run the connection test with a timeout
    logger.info("Attempting to connect to WebSocket (timeout: 5 seconds)")
    
    # We'll use a thread to run this async code
    def run_async_test():
        asyncio.run(wait_for_connection())
    
    # Start the thread
    thread = threading.Thread(target=run_async_test)
    thread.daemon = True
    thread.start()
    
    # Wait for up to 5 seconds
    if connected_event.wait(5):
        logger.success("WebSocket connected successfully")
    else:
        logger.warning("WebSocket connection test timed out after 5 seconds")
    
except Exception as e:
    logger.error(f"Failed to test WebSocket connection: {e}")

logger.info("Alpaca Connection Diagnostic completed") 