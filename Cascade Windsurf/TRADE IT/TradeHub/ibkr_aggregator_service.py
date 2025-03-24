#!/usr/bin/env python3
"""
IBKR Aggregator Service

This script provides automated integration between Interactive Brokers (IBKR) 
and the CandleAggregator system. It handles:

1. Auto-connection to IBKR TWS/Gateway
2. Historical data seeding
3. Live data streaming to the candle aggregator
4. State persistence between sessions
5. Automatic recovery from disconnections
6. Signal generation for trading setups

Usage:
    python ibkr_aggregator_service.py [--symbols SYMBOL1,SYMBOL2,...]
"""

import os
import sys
import time
import pickle
import argparse
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from loguru import logger
import ib_insync

# Local imports
from trading_agents.utils.ibkr_connector import (
    get_ib_connection, disconnect_ib, 
    fetch_historical_data, subscribe_to_market_data,
    IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID
)
from candle_aggregator import CandleAggregator, TimeFrame, PatternType
from start_scanner import DEFAULT_SYMBOLS

# Configure logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(f"{LOG_DIR}/ibkr_aggregator_{datetime.now().strftime('%Y%m%d')}.log", 
           rotation="500 MB", level="DEBUG")

# Configuration
SAVE_STATE_INTERVAL = 15  # Minutes between state saves
RECONNECT_INTERVAL = 60   # Seconds between reconnection attempts
STATE_FILE = "data/aggregator_state.pkl"
MAX_RECONNECT_ATTEMPTS = 5

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

class IBKRAggregatorService:
    def __init__(self, symbols: List[str] = None):
        """
        Initialize the IBKR Aggregator Service.
        
        Args:
            symbols: List of symbols to track (default: use DEFAULT_SYMBOLS from start_scanner)
        """
        self.symbols = symbols or DEFAULT_SYMBOLS
        self._ib_connection = None
        self.aggregator = None
        self.is_running = False
        self.reconnect_attempts = 0
        
        # Initialize or load aggregator
        self._initialize_aggregator()
        
        # Store active market data subscriptions
        self.active_subscriptions = {}
        
        logger.info(f"IBKR Aggregator Service initialized with {len(self.symbols)} symbols")
    
    def _initialize_aggregator(self):
        """Initialize the candle aggregator, loading from saved state if available."""
        # Try to load existing state
        self.aggregator = self._load_aggregator_state()
        
        # If no state found, create a new aggregator
        if self.aggregator is None:
            logger.info("No saved state found. Creating new CandleAggregator.")
            self.aggregator = CandleAggregator(
                symbols=self.symbols,
                timeframes=[tf.value for tf in TimeFrame],
                pattern_detection_enabled=True
            )
        else:
            # Update symbols if needed
            for symbol in self.symbols:
                if symbol not in self.aggregator.symbols:
                    logger.info(f"Adding new symbol to aggregator: {symbol}")
                    self.aggregator.add_symbol(symbol)
        
        # Register observers for pattern detection
        self.aggregator.register_observer('pattern_detected', self._on_pattern_detected)
        self.aggregator.register_observer('pattern_completed', self._on_pattern_completed)
    
    def _save_aggregator_state(self):
        """Save the current state of the candle aggregator to disk."""
        try:
            with open(STATE_FILE, 'wb') as f:
                pickle.dump(self.aggregator, f)
            logger.info(f"Saved aggregator state to {STATE_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save aggregator state: {e}")
            return False
    
    def _load_aggregator_state(self) -> Optional[CandleAggregator]:
        """Load a previously saved candle aggregator state from disk."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'rb') as f:
                    aggregator = pickle.load(f)
                logger.info(f"Loaded aggregator state from {STATE_FILE}")
                return aggregator
            except Exception as e:
                logger.error(f"Failed to load aggregator state: {e}")
        return None
    
    def _seed_historical_data(self):
        """Seed the aggregator with historical data from IBKR."""
        if not self._ib_connection:
            logger.error("Cannot seed historical data: Not connected to IBKR")
            return False
        
        logger.info("Seeding historical data...")
        
        for symbol in self.symbols:
            for timeframe in self.aggregator.timeframes:
                # Skip if we already have enough data for this symbol and timeframe
                candles = self.aggregator.get_candles(timeframe, symbol)
                if candles and len(candles) > 50:  # Arbitrary threshold
                    logger.debug(f"Skipping historical data for {symbol} {timeframe} - already have {len(candles)} candles")
                    continue
                
                # Set appropriate duration based on timeframe
                if timeframe == TimeFrame.D1.value:
                    duration = "60 D"  # 60 days for daily timeframe
                elif timeframe in [TimeFrame.H4.value, TimeFrame.H1.value]:
                    duration = "20 D"  # 20 days for hourly timeframes
                else:
                    duration = "5 D"   # 5 days for minute timeframes
                
                logger.debug(f"Fetching {duration} of historical data for {symbol} on {timeframe}")
                
                # Fetch historical data from IBKR
                df = fetch_historical_data(symbol, timeframe, duration)
                
                if df is not None and not df.empty:
                    # Process historical candles to seed the aggregator
                    logger.debug(f"Processing {len(df)} historical candles for {symbol} on {timeframe}")
                    
                    # Log the actual DataFrame columns we received
                    logger.debug(f"DataFrame columns from IBKR: {df.columns.tolist()}")
                    logger.debug(f"DataFrame index: {type(df.index).__name__}")
                    
                    # Convert IBKR format to our expected format
                    # IBKR typically has 'date' as the index and columns like 'open', 'high', etc.
                    processed_df = df.reset_index().copy()
                    
                    # Rename the date/time column to our expected 'timestamp' column
                    column_mapping = {}
                    if 'date' in processed_df.columns:
                        column_mapping['date'] = 'timestamp'
                    
                    # Make sure all required columns are lowercase for case-insensitive matching
                    for col in processed_df.columns:
                        if col.lower() in ['open', 'high', 'low', 'close', 'volume'] and col != col.lower():
                            column_mapping[col] = col.lower()
                    
                    # Apply column renaming if needed
                    if column_mapping:
                        processed_df = processed_df.rename(columns=column_mapping)
                    
                    # Validate that we have all required columns now
                    required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    missing_cols = [col for col in required_cols if col not in processed_df.columns]
                    
                    if missing_cols:
                        logger.error(f"Missing required columns after processing: {missing_cols}")
                        logger.error(f"Available columns: {processed_df.columns.tolist()}")
                        continue  # Skip this timeframe/symbol if we can't process it
                    
                    logger.info(f"Successfully processed data for {symbol} on {timeframe}")
                    self.aggregator.process_candles(processed_df, timeframe, symbol)
                else:
                    logger.warning(f"No historical data available for {symbol} on {timeframe}")
        
        logger.info("Historical data seeding completed")
        return True
    
    def _process_ibkr_tick(self, tick_data):
        """Process real-time tick data from IBKR."""
        try:
            # Convert IBKR tick format to what the aggregator expects
            aggregator_tick = {
                "symbol": tick_data["symbol"],
                "timestamp": tick_data["time"],
                "price": tick_data["price"],
                "volume": tick_data.get("size", 0)
            }
            self.aggregator.process_tick(aggregator_tick)
        except Exception as e:
            logger.error(f"Error processing tick data: {e}")
    
    def _on_pattern_detected(self, timeframe, symbol, pattern):
        """Handler for pattern detection events."""
        pattern_type = pattern.pattern_type
        logger.info(f"⭐ Pattern detected: {pattern_type} on {symbol} {timeframe}")
        
        # For sweep engulfing patterns, log more details
        if pattern_type in [PatternType.SWEEP_ENGULFING.value, PatternType.SWEEP_ENGULFING_CONFIRMED.value]:
            direction = pattern.data.get('direction', 'unknown')
            engulfing_size = pattern.data.get('engulfing_size', 0)
            logger.info(f"Sweep Engulfing details: Direction={direction}, Size={engulfing_size:.2f}%")
    
    def _on_pattern_completed(self, timeframe, symbol, pattern):
        """Handler for pattern completion events."""
        logger.info(f"Pattern completed: {pattern.pattern_type} on {symbol} {timeframe}")
    
    def _schedule_state_saving(self):
        """Schedule periodic state saving."""
        schedule.every(SAVE_STATE_INTERVAL).minutes.do(self._save_aggregator_state)
        
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
        logger.info(f"Scheduled state saving every {SAVE_STATE_INTERVAL} minutes")
    
    def _connect_to_ibkr(self):
        """Establish connection to IBKR."""
        logger.info(f"Connecting to IBKR at {IBKR_HOST}:{IBKR_PORT}...")
        self._ib_connection = get_ib_connection()
        
        if self._ib_connection:
            logger.info("Successfully connected to IBKR")
            self.reconnect_attempts = 0
            return True
        else:
            self.reconnect_attempts += 1
            logger.error(f"Failed to connect to IBKR (attempt {self.reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS})")
            return False
    
    def _setup_market_data_subscriptions(self):
        """Subscribe to market data for all symbols."""
        if not self._ib_connection:
            logger.error("Cannot subscribe to market data: Not connected to IBKR")
            return False
        
        logger.info("Setting up market data subscriptions...")
        for symbol in self.symbols:
            logger.debug(f"Subscribing to market data for {symbol}")
            sub_id = subscribe_to_market_data(symbol, self._process_ibkr_tick)
            if sub_id:
                self.active_subscriptions[symbol] = sub_id
        
        logger.info(f"Subscribed to market data for {len(self.active_subscriptions)} symbols")
        return len(self.active_subscriptions) > 0
    
    def _setup_connection_monitoring(self):
        """Set up a thread to monitor the IBKR connection and reconnect if needed."""
        def monitor_connection():
            while self.is_running:
                if self._ib_connection is None or not self._ib_connection.isConnected():
                    logger.warning("IBKR connection lost. Attempting to reconnect...")
                    if self.reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
                        success = self._connect_to_ibkr()
                        if success:
                            self._setup_market_data_subscriptions()
                    else:
                        logger.error(f"Maximum reconnection attempts ({MAX_RECONNECT_ATTEMPTS}) reached. Giving up.")
                        self.is_running = False
                        break
                time.sleep(RECONNECT_INTERVAL)
        
        thread = threading.Thread(target=monitor_connection, daemon=True)
        thread.start()
        logger.info("Connection monitoring started")
    
    def start(self):
        """Start the IBKR Aggregator Service."""
        logger.info("Starting IBKR Aggregator Service...")
        self.is_running = True
        
        # Connect to IBKR
        if not self._connect_to_ibkr():
            logger.error("Failed to connect to IBKR. Make sure TWS/IB Gateway is running.")
            return False
        
        # Seed historical data
        self._seed_historical_data()
        
        # Set up market data subscriptions
        self._setup_market_data_subscriptions()
        
        # Schedule state saving
        self._schedule_state_saving()
        
        # Set up connection monitoring
        self._setup_connection_monitoring()
        
        logger.info("IBKR Aggregator Service started successfully")
        return True
    
    def stop(self):
        """Stop the IBKR Aggregator Service."""
        logger.info("Stopping IBKR Aggregator Service...")
        self.is_running = False
        
        # Save state before stopping
        self._save_aggregator_state()
        
        # Disconnect from IBKR
        if self._ib_connection:
            disconnect_ib()
            self._ib_connection = None
        
        logger.info("IBKR Aggregator Service stopped")
    
    def run_forever(self):
        """
        Run the service indefinitely, handling reconnections automatically.
        """
        logger.info("Starting service in continuous mode...")
        self.is_running = True
        reconnect_counter = 0
        
        # Constants for reconnection strategy
        MAX_RECONNECT_ATTEMPTS = 5
        RECONNECT_INTERVAL = 60  # seconds
        
        while self.is_running:
            try:
                if not self.start():
                    logger.error("Failed to start service")
                    self.is_running = False
                    return
                
                while self.is_running:
                    time.sleep(1)  # Check connection status periodically
                    
                    # Verify connection is still active
                    if not self._ib_connection.isConnected():
                        logger.warning("IBKR connection lost. Attempting to reconnect...")
                        break
                    
                    schedule.run_pending()  # Run any scheduled tasks
            
            except Exception as e:
                logger.exception(f"Error in service: {str(e)}")
            
            finally:
                self.stop()
            
            # Attempt to reconnect
            if self.is_running:
                reconnect_counter += 1
                logger.info(f"Reconnection attempt {reconnect_counter} of {MAX_RECONNECT_ATTEMPTS}...")
                
                if reconnect_counter < MAX_RECONNECT_ATTEMPTS:
                    time.sleep(RECONNECT_INTERVAL)
                    if self._connect_to_ibkr():
                        reconnect_counter = 0  # Reset counter on successful reconnection
                        logger.info("Reconnected successfully")
                        
                        # Reinitialize data seeding
                        logger.info("Reseeding historical data after reconnection")
                        success = self._seed_historical_data()
                        if success:
                            self._setup_market_data_subscriptions()
                    else:
                        logger.error(f"Maximum reconnection attempts ({MAX_RECONNECT_ATTEMPTS}) reached. Giving up.")
                        self.is_running = False
                        break
                time.sleep(RECONNECT_INTERVAL)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="IBKR Aggregator Service")
    parser.add_argument("--symbols", type=str, help="Comma-separated list of symbols to track")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    # Parse symbols if provided
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    
    # Create and run the service
    service = IBKRAggregatorService(symbols=symbols)
    service.run_forever()
