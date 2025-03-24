"""
API endpoints for the custom dashboard application.
"""
import json
import random
import math
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from flask import (
    Blueprint, jsonify, request
)
from loguru import logger

# Try to import real data functions, fall back to mock data if unavailable
try:
    from trading_agents.utils.data_fetcher import fetch_historical_data as yf_fetch_historical_data
    from trading_agents.utils.setup_storage import get_setups as db_get_setups, get_setup_by_id, cleanup_old_setups
    # Set MOCK_DATA to False to use real data from IBKR for pending setups
    MOCK_DATA = False
except ImportError:
    MOCK_DATA = True

# Try to import Alpaca connector
try:
    from trading_agents.utils.alpaca_connector import (
        fetch_historical_data as alpaca_fetch_historical_data,
        initialize_real_time_data,
        subscribe_to_symbol,
        start_data_stream,
        ALPACA_AVAILABLE
    )
    USE_ALPACA = True
    # Initialize real-time data stream
    if initialize_real_time_data():
        logger.info("Alpaca real-time data initialized successfully")
        start_data_stream()
    else:
        logger.warning("Could not initialize Alpaca real-time data")
        USE_ALPACA = False
except ImportError:
    logger.warning("Alpaca connector not available. Using Yahoo Finance for data.")
    USE_ALPACA = False
    ALPACA_AVAILABLE = False

# Import pending setups module
try:
    from trading_agents.custom_dashboard.pending_setups import get_pending_sweep_engulfing_setups
    PENDING_SETUPS_AVAILABLE = True
except ImportError:
    logger.warning("Pending setups module not available. Pending setups will not be shown.")
    PENDING_SETUPS_AVAILABLE = False

# Try to get a reference to the CandleAggregator instance
try:
    from trading_agents.candle_aggregator import CandleAggregator
    HAS_CANDLE_AGGREGATOR = True
except ImportError:
    logger.warning("CandleAggregator not available")
    HAS_CANDLE_AGGREGATOR = False

# Try to get a reference to the CandleAggregator instance
try:
    from trading_agents.utils.aggregator_singleton import get_aggregator_instance
    AGGREGATOR_AVAILABLE = True
except ImportError:
    logger.warning("CandleAggregator singleton not available. Pending setups will use mock data.")
    AGGREGATOR_AVAILABLE = False

# Create a blueprint for the API
bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/symbols", methods=["GET"])
def get_symbols():
    """Get a list of available symbols."""
    # In a real implementation, this would query your database or another source
    symbols = [
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"},
        {"symbol": "AMZN", "name": "Amazon.com, Inc.", "exchange": "NASDAQ"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ"},
        {"symbol": "META", "name": "Meta Platforms, Inc.", "exchange": "NASDAQ"},
        {"symbol": "TSLA", "name": "Tesla, Inc.", "exchange": "NASDAQ"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ"},
        {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "exchange": "NYSE"},
        {"symbol": "V", "name": "Visa Inc.", "exchange": "NYSE"},
        {"symbol": "JNJ", "name": "Johnson & Johnson", "exchange": "NYSE"},
    ]
    return jsonify(symbols)


@bp.route("/price-data/<symbol>", methods=["GET"])
def get_price_data(symbol):
    """Get price data for a symbol."""
    timeframe = request.args.get("timeframe", "1d")
    logger.info(f"API request for price data: {symbol} on {timeframe}")
    
    try:
        # Try to use Alpaca first if available
        if USE_ALPACA and ALPACA_AVAILABLE:
            logger.info(f"Using Alpaca for {symbol} data")
            data = alpaca_fetch_historical_data(symbol, timeframe)
            if data:
                logger.info(f"Fetched {len(data)} data points for {symbol} ({timeframe}) from Alpaca")
                return jsonify(data)
            else:
                logger.warning(f"No data returned from Alpaca for {symbol}, falling back to Yahoo Finance")
        
        # Fall back to Yahoo Finance if Alpaca fails or isn't available
        if not MOCK_DATA:
            data = yf_fetch_historical_data(symbol, timeframe)
            if data:
                logger.info(f"Fetched {len(data)} data points for {symbol} ({timeframe})")
                return jsonify(data)
            else:
                logger.warning(f"No real data available for {symbol}, using mock data")
        
        # Generate mock data if all real data sources fail
        logger.warning(f"Using mock data for {symbol}")
        
        # Generate random price data
        now = datetime.now()
        data = []
        base_price = random.uniform(50, 500)
        for i in range(200):
            date = now - timedelta(days=200 - i)
            # Add some randomness to the price
            if i > 0:
                price_change = random.uniform(-2, 2)
                base_price += price_change
            
            # Ensure the price doesn't go negative
            base_price = max(base_price, 1)
            
            # Generate OHLCV data
            open_price = base_price * random.uniform(0.99, 1.01)
            close_price = base_price * random.uniform(0.99, 1.01)
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.03)
            low_price = min(open_price, close_price) * random.uniform(0.97, 1.0)
            volume = int(random.uniform(100000, 10000000))
            
            data.append({
                "date": date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume
            })
        
        logger.info(f"Generated {len(data)} mock data points for {symbol}")
        return jsonify(data)
    
    except Exception as e:
        logger.error(f"Error fetching price data for {symbol}: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/setups", methods=["GET"])
def get_setups():
    """Get trade setups."""
    # Always force sweep_engulfing_confirmed as the setup type, regardless of input
    direction = request.args.get("direction", "all")
    symbol = request.args.get("symbol")
    timeframe = request.args.get("timeframe")
    status = request.args.get("status", "active")
    limit = int(request.args.get("limit", 50))
    
    logger.info(f"Setups API called: direction={direction}, symbol={symbol}, timeframe={timeframe}")
    logger.info(f"MOCK_DATA setting is: {MOCK_DATA}")
    
    # Automatically clean up old setups before fetching (keeping only the last 2 days)
    try:
        days_to_keep = 2  # Keep setups from the last 2 days
        expired_count = cleanup_old_setups(days_to_keep)
        logger.info(f"Auto-cleanup: Marked {expired_count} setups older than {days_to_keep} days as expired")
    except Exception as e:
        logger.error(f"Error during auto-cleanup of old setups: {str(e)}")
    
    if not MOCK_DATA:
        try:
            # Use real setups from database
            setups = db_get_setups(
                setup_type="sweep_engulfing_confirmed",  # Force this type
                direction=direction,
                symbol=symbol,
                timeframe=timeframe,
                status=status,
                limit=limit
            )
            
            # Convert to JSON-serializable format
            for setup in setups:
                # Convert any non-serializable values
                for key, value in setup.items():
                    if isinstance(value, (np.int64, np.float64)):
                        setup[key] = float(value)
                
                # Remove stop loss and target prices from the data sent to the frontend
                if 'stop_loss' in setup:
                    del setup['stop_loss']
                if 'target' in setup:
                    del setup['target']
                    
                # If there's entry_price, rename it to entry_zone for clarity
                if 'entry_price' in setup:
                    setup['entry_zone'] = setup['entry_price']
                
            logger.info(f"Returning {len(setups)} real setups")
            return jsonify(setups)
        except Exception as e:
            # Fall back to mock data if database access fails
            logger.error(f"Error fetching real setups: {e}")
            mock_setups = generate_mock_setups(direction=direction)
            logger.info(f"Falling back to {len(mock_setups)} mock setups")
            return jsonify(mock_setups)
    else:
        # Use mock setups - always with sweep_engulfing_confirmed
        mock_setups = generate_mock_setups(direction=direction)
        logger.info(f"Returning {len(mock_setups)} mock setups")
        return jsonify(mock_setups)


@bp.route("/analysis/<symbol>", methods=["GET"])
def get_analysis(symbol):
    """Get analysis for a symbol."""
    # Try to load real analysis data
    try:
        with open(f"{symbol}_options_analysis.json", "r") as f:
            analysis = json.load(f)
    except FileNotFoundError:
        # Generate mock analysis
        analysis = generate_mock_analysis(symbol)
    
    return jsonify(analysis)


def ensure_serializable(obj):
    """
    Recursively convert an object to be JSON serializable.
    Handles numpy types, booleans, and other non-serializable types.
    """
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, (datetime, )):
        return obj.isoformat()
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: ensure_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [ensure_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(ensure_serializable(item) for item in obj)
    elif obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        return str(obj)


@bp.route("/setup/<int:setup_id>", methods=["GET"])
def get_setup_detail(setup_id):
    """Get detailed information for a specific setup."""
    logger.info(f"API request for setup detail: ID {setup_id}")
    try:
        # Fetch the setup data from the database using the get_setup_by_id function
        from trading_agents.utils.setup_storage import get_setup_by_id
        setup = get_setup_by_id(setup_id)
        logger.info(f"Successfully retrieved setup details for ID {setup_id}")
        
        # Ensure all values are JSON serializable
        setup_copy = ensure_serializable(setup)
        logger.debug(f"Returning setup data: {setup_copy}")
        return jsonify(setup_copy)
    except Exception as e:
        logger.error(f"Error fetching setup details for ID {setup_id}: {str(e)}", exc_info=True)
        # Fallback to mock data if needed
        try:
            mock_setup = get_mock_setup_detail(setup_id)
            # Ensure mock data is serializable
            mock_setup_copy = ensure_serializable(mock_setup)
            logger.info(f"Using mock data for setup ID {setup_id}")
            return jsonify(mock_setup_copy)
        except Exception as mock_error:
            logger.error(f"Error generating mock data: {str(mock_error)}", exc_info=True)
            return jsonify({"error": str(e), "mock_error": str(mock_error)}), 500


def generate_mock_price_data(symbol, timeframe="1d", limit=200):
    """Generate mock price data for testing."""
    data = []
    
    # Determine time interval based on timeframe
    if timeframe in ["1m", "5m", "15m", "30m"]:
        # For minute timeframes, use minutes
        interval = int(timeframe.replace("m", "")) * 60  # seconds
    elif timeframe in ["1h", "4h"]:
        # For hour timeframes, use hours
        interval = int(timeframe.replace("h", "")) * 3600  # seconds
    elif timeframe == "1d":
        # For daily timeframe, use days
        interval = 86400  # seconds
    elif timeframe == "1w":
        # For weekly timeframe, use weeks
        interval = 604800  # seconds
    else:
        # Default to daily
        interval = 86400
    
    # Start time (N intervals ago)
    end_time = datetime.now()
    
    # Generate data for each interval
    for i in range(limit):
        # Calculate timestamp for this candle
        current_time = end_time - timedelta(seconds=interval * (limit - i))
        
        # Base price (use ticker first letter as seed for variety)
        base = 100 + (ord(symbol[0]) % 26) * 10
        
        # Add some randomness but maintain a trend
        price_multiplier = 1 + ((i - limit/2) / limit) * 0.2  # Creates a trend
        random_factor = 0.02  # Random noise
        
        price_base = base * price_multiplier
        
        # Calculate OHLC with some randomness
        open_price = price_base * (1 + random.uniform(-random_factor, random_factor))
        close_price = price_base * (1 + random.uniform(-random_factor, random_factor))
        
        # High and low should respect open and close
        high_price = max(open_price, close_price) * (1 + random.uniform(0, random_factor * 2))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, random_factor * 2))
        
        # Volume varies but follows a pattern
        volume = int(1000 + abs(math.sin(i / 10)) * 10000)
        
        # For sudden events
        if random.random() < 0.05:  # 5% chance
            # Big move
            direction = random.choice([-1, 1])
            spike = random.uniform(0.05, 0.15)  # 5-15% spike
            high_price = max(high_price, close_price * (1 + spike * max(0, direction)))
            low_price = min(low_price, close_price * (1 - spike * max(0, -direction)))
            volume *= random.uniform(3, 5)  # Increased volume
        
        # Add the data point
        data.append({
            "time": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": int(volume)
        })
    
    return data


def generate_mock_setups(setup_type="all", direction="all"):
    """Generate mock trade setups."""
    # Only use sweep_engulfing_confirmed as the setup type
    directions = ["bullish", "bearish"]
    symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "JPM", "V", "JNJ"]
    timeframes = ["1min", "5min", "15min", "1H", "4H", "1D"]
    statuses = ["active", "triggered", "expired", "completed"]
    
    setups = []
    
    for _ in range(15):  # Generate more setups for better testing
        # Randomly choose a direction if not specified
        current_direction = random.choice(directions) if direction == "all" else direction
        
        # Generate a realistic entry price
        entry_price = round(random.uniform(100, 500), 2)
        
        # For bullish patterns, stop loss is below entry, target is above
        # For bearish patterns, stop loss is above entry, target is below
        if current_direction == "bullish":
            stop_loss = round(entry_price * random.uniform(0.94, 0.98), 2)  # 2-6% below entry
            target = round(entry_price * random.uniform(1.05, 1.15), 2)    # 5-15% above entry
        else:  # bearish
            stop_loss = round(entry_price * random.uniform(1.02, 1.06), 2)  # 2-6% above entry
            target = round(entry_price * random.uniform(0.85, 0.95), 2)    # 5-15% below entry
        
        # Calculate risk reward based on direction
        risk = abs(stop_loss - entry_price)
        reward = abs(target - entry_price)
        risk_reward = round(reward / risk, 2) if risk > 0 else random.uniform(1.5, 3.5)
        
        # Create the setup with proper prices
        setup = {
            "id": random.randint(1000, 9999),
            "symbol": random.choice(symbols),
            "setup_type": "sweep_engulfing_confirmed",  # Always use this setup type
            "direction": current_direction,
            "timeframe": random.choice(timeframes),
            "confidence": round(random.uniform(0.6, 0.98), 2),
            "entry_zone": entry_price,  # Use entry_zone instead of entry_price
            # Stop loss and target are calculated but not included in the response
            # as per user request (they're still calculated to maintain the logic)
            "risk_reward": risk_reward,
            "date_identified": (datetime.now() - timedelta(hours=random.randint(0, 48))).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": random.choice(statuses)
        }
        setups.append(setup)
    
    # Filter by direction if specified
    filtered_setups = setups
    if direction != "all":
        filtered_setups = [s for s in filtered_setups if s["direction"] == direction]
    
    return filtered_setups


def generate_mock_analysis(symbol):
    """Generate mock analysis data for a symbol."""
    return {
        "symbol": symbol,
        "last_price": round(random.uniform(100, 1000), 2),
        "change_percent": round(random.uniform(-5, 5), 2),
        "volume": int(random.uniform(1000000, 10000000)),
        "market_cap": round(random.uniform(10, 2000), 2),
        "pe_ratio": round(random.uniform(10, 40), 2),
        "dividend_yield": round(random.uniform(0, 3), 2),
        "analyst_rating": random.choice(["Buy", "Hold", "Sell"]),
        "price_target": round(random.uniform(100, 1200), 2),
        "support_levels": [
            round(random.uniform(80, 95), 2),
            round(random.uniform(70, 85), 2)
        ],
        "resistance_levels": [
            round(random.uniform(105, 120), 2),
            round(random.uniform(125, 140), 2)
        ],
        "technical_indicators": {
            "rsi": round(random.uniform(30, 70), 2),
            "macd": round(random.uniform(-5, 5), 2),
            "ema_20": round(random.uniform(90, 110), 2),
            "ema_50": round(random.uniform(85, 115), 2),
            "ema_200": round(random.uniform(80, 120), 2)
        }
    }


def generate_mock_setup_detail(setup_id):
    """Generate detailed mock data for a specific setup."""
    # Use the setup_id as a seed for random generation to ensure consistency
    random.seed(setup_id)
    
    symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "JPM", "V", "JNJ"]
    setup_types = ["Support Test", "Resistance Test", "Trend Continuation", "Reversal", "Breakout"]
    directions = ["bullish", "bearish"]
    timeframes = ["1min", "5min", "15min", "1H", "4H", "1D"]
    
    # Basic setup info
    symbol = random.choice(symbols)
    setup_type = random.choice(setup_types)
    direction = random.choice(directions)
    timeframe = random.choice(timeframes)
    entry_price = round(random.uniform(100, 500), 2)
    
    # For bullish patterns, stop loss is below entry, target is above
    # For bearish patterns, stop loss is above entry, target is below
    if direction == "bullish":
        stop_loss = round(entry_price * 0.95, 2)
        target = round(entry_price * 1.15, 2)
    else:
        stop_loss = round(entry_price * 1.05, 2)
        target = round(entry_price * 0.85, 2)
    
    # Calculate risk reward based on direction
    risk = abs(stop_loss - entry_price)
    reward = abs(target - entry_price)
    risk_reward = round(reward / risk, 2) if risk > 0 else random.uniform(1.5, 3.5)
    
    # Generate price data for the chart
    price_data = generate_mock_price_data(symbol, timeframe, 100)
    
    # Market analysis
    market_analysis = {
        "trend": random.choice(["Uptrend", "Downtrend", "Sideways"]),
        "strength": round(random.uniform(0, 100), 1),
        "volatility": round(random.uniform(0, 100), 1),
        "volume_profile": random.choice(["Increasing", "Decreasing", "Stable"]),
        "key_levels": [
            {"price": round(random.uniform(80, 95), 2), "type": "Support"},
            {"price": round(random.uniform(70, 85), 2), "type": "Support"}
        ],
        "indicators": {
            "rsi": round(random.uniform(30, 70), 2),
            "macd": round(random.uniform(-5, 5), 2),
            "ema_20": round(random.uniform(90, 110), 2),
            "ema_50": round(random.uniform(85, 115), 2),
            "ema_200": round(random.uniform(80, 120), 2)
        }
    }
    
    # Order flow analysis
    order_flow_analysis = {
        "buying_pressure": round(random.uniform(0, 100), 1),
        "selling_pressure": round(random.uniform(0, 100), 1),
        "large_orders": [
            {
                "time": (datetime.now() - timedelta(hours=random.randint(1, 24))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "price": round(random.uniform(90, 110), 2),
                "size": random.randint(10000, 100000),
                "side": random.choice(["buy", "sell"])
            }
            for _ in range(3)
        ],
        "imbalance": round(random.uniform(-100, 100), 1),
        "liquidity": {
            "above": round(random.uniform(100000, 1000000), 0),
            "below": round(random.uniform(100000, 1000000), 0)
        }
    }
    
    # Options analysis
    options_analysis = {
        "implied_volatility": round(random.uniform(20, 60), 1),
        "put_call_ratio": round(random.uniform(0.5, 2.0), 2),
        "open_interest": {
            "calls": random.randint(1000, 10000),
            "puts": random.randint(1000, 10000)
        },
        "significant_strikes": [
            {
                "strike": round(random.uniform(90, 110), 2),
                "type": random.choice(["call", "put"]),
                "expiry": (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
                "open_interest": random.randint(100, 1000),
                "volume": random.randint(50, 500)
            }
            for _ in range(3)
        ],
        "gamma_exposure": round(random.uniform(-1000000, 1000000), 0)
    }
    
    # Reset the random seed
    random.seed()
    
    logger.info(f"Generated mock setup detail for ID {setup_id}")
    logger.debug(f"Mock setup detail: {setup_id}")
    
    return {
        "id": setup_id,
        "symbol": symbol,
        "setup_type": setup_type,
        "direction": direction,
        "timeframe": timeframe,
        "confidence": round(random.uniform(0.6, 0.98), 2),
        "entry_price": float(entry_price),  # Ensure float
        "stop_loss": float(stop_loss),  # Ensure float
        "target": float(target),  # Ensure float
        "risk_reward": float(risk_reward),  # Ensure float
        "date_identified": (datetime.now() - timedelta(hours=random.randint(0, 48))).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": random.choice(["active", "triggered", "expired", "completed"]),
        "price_data": price_data,
        "market_analysis": market_analysis,
        "order_flow_analysis": order_flow_analysis,
        "options_analysis": options_analysis,
        "notes": "This is a sample trade setup with mock data."
    }


def get_mock_setup_detail(setup_id):
    """Generate mock data for a setup detail when real data is not available."""
    setup_types = ["breakout", "reversal", "continuation", "pullback"]
    directions = ["bullish", "bearish"]
    timeframes = ["1h", "4h", "1d", "1w"]
    symbols = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA", "META", "NVDA"]
    
    # Deterministic but varied mock data
    mock_seed = setup_id * 100
    np.random.seed(mock_seed)
    
    price_base = 100.0 + (mock_seed % 900)
    entry_price = round(price_base, 2)
    
    direction = directions[mock_seed % len(directions)]
    
    if direction == "bullish":
        stop_loss = round(entry_price * 0.95, 2)
        target = round(entry_price * 1.15, 2)
    else:
        stop_loss = round(entry_price * 1.05, 2)
        target = round(entry_price * 0.85, 2)
    
    risk_reward = round(abs(target - entry_price) / abs(stop_loss - entry_price), 2)
    
    days_ago = mock_seed % 30
    date_identified = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Mock options and order flow data
    options_data = {
        "iv_percentile": round(np.random.uniform(1, 100), 2),
        "put_call_ratio": round(np.random.uniform(0.5, 2.5), 2),
        "unusual_activity": bool(np.random.choice([1, 0]))  # Convert to standard Python bool
    }
    
    order_flow_data = {
        "buying_pressure": round(np.random.uniform(1, 100), 2),
        "selling_pressure": round(np.random.uniform(1, 100), 2),
        "smart_money_direction": np.random.choice(["bullish", "bearish", "neutral"])
    }
    
    setup = {
        "id": int(setup_id),  # Ensure integer
        "symbol": symbols[mock_seed % len(symbols)],
        "setup_type": setup_types[mock_seed % len(setup_types)],
        "direction": direction,
        "timeframe": timeframes[mock_seed % len(timeframes)],
        "confidence": float(round(np.random.uniform(50, 95), 2)),  # Ensure float
        "entry_price": float(entry_price),  # Ensure float
        "stop_loss": float(stop_loss),  # Ensure float
        "target": float(target),  # Ensure float
        "risk_reward": float(risk_reward),  # Ensure float
        "date_identified": date_identified,
        "status": np.random.choice(["active", "triggered", "expired", "completed"]),
        "market_aligned": bool(np.random.choice([1, 0])),  # Convert to standard Python bool
        "analysis": {
            "options": options_data,
            "order_flow": order_flow_data
        }
    }
    
    # Reset numpy's random seed
    np.random.seed(None)
    
    logger.info(f"Generated mock setup detail for ID {setup_id}")
    logger.debug(f"Mock setup detail: {setup_id}")
    
    return setup 


@bp.route("/pending-setups", methods=["GET"])
def get_pending_setups():
    """
    Get pending setup patterns that have started forming but aren't yet complete.
    This is useful for planning ahead for the next trading day.
    
    Parameters:
    - type: Optional query param to filter by pattern type (e.g., "sweep_engulfing")
    - timeframe: Optional query param to filter by timeframe (e.g., "D1")
    
    Returns:
        JSON object with:
        - status: "success" or "error"
        - count: Number of pending setups
        - pending_setups: List of pending setup objects
    """
    try:
        pattern_type = request.args.get("type", "sweep_engulfing")
        timeframe = request.args.get("timeframe", None)
        
        # Default empty response
        result = {
            "status": "success", 
            "count": 0, 
            "pending_setups": []
        }
        
        # Use real data if available
        if not MOCK_DATA and AGGREGATOR_AVAILABLE and PENDING_SETUPS_AVAILABLE:
            logger.info("Getting real pending setups from aggregator")
            aggregator = get_aggregator_instance()
            
            if pattern_type == "sweep_engulfing":
                pending_setups = get_pending_sweep_engulfing_setups(aggregator)
                
                # Apply timeframe filter if specified
                if timeframe:
                    pending_setups = [s for s in pending_setups if s["timeframe"] == timeframe]
                
                result["pending_setups"] = pending_setups
                result["count"] = len(pending_setups)
                logger.info(f"Found {len(pending_setups)} real pending setups")
            else:
                logger.warning(f"Unsupported pattern type for pending setups: {pattern_type}")
        else:
            # Generate mock pending setups for demonstration
            logger.info("Generating mock pending setups")
            mock_setups = generate_mock_pending_setups(pattern_type, timeframe)
            result["pending_setups"] = mock_setups
            result["count"] = len(mock_setups)
            logger.info(f"Generated {len(mock_setups)} mock pending setups")
        
        return jsonify(result)
        
    except Exception as e:
        logger.exception(f"Error getting pending setups: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })


def generate_mock_pending_setups(pattern_type="sweep_engulfing", timeframe=None):
    """
    Generate mock pending setup data for testing.
    
    Args:
        pattern_type: Type of pattern to generate
        timeframe: Optional timeframe filter
        
    Returns:
        List of mock pending setup dictionaries
    """
    symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMD", "AMZN", "META", "TSLA", "JPM", "V"]
    timeframes = ["D1", "H4", "H1"] if not timeframe else [timeframe]
    directions = ["bullish", "bearish"]
    
    # Generate 3-10 random pending setups
    num_setups = random.randint(3, 10)
    pending_setups = []
    
    for _ in range(num_setups):
        symbol = random.choice(symbols)
        direction = random.choice(directions)
        setup_timeframe = random.choice(timeframes)
        
        # Generate random completion state
        has_sweep = random.random() > 0.1  # 90% chance to have sweep candle
        has_engulf = has_sweep and random.random() > 0.3  # 70% chance to have engulf if has sweep
        retrace_pct = 0
        
        if has_engulf:
            retrace_pct = random.uniform(0, 40)  # Random retracement percentage
        
        # Determine status text
        status_parts = []
        if has_sweep:
            status_parts.append("Sweep candle ")
        else:
            status_parts.append("Sweep candle ")
        
        if has_engulf:
            status_parts.append("Engulf candle ")
        else:
            status_parts.append("Engulf candle ")
        
        if retrace_pct > 0:
            status_parts.append(f"Retracement {retrace_pct:.1f}%")
        else:
            status_parts.append("Awaiting retracement")
        
        # Add confirmation status
        if retrace_pct >= 33:
            status_parts.append("Confirmation ")
        else:
            status_parts.append("Confirmation pending")
        
        # Calculate mock prices
        base_price = random.uniform(50, 500)
        if direction == "bullish":
            entry_price = base_price * (1 + random.uniform(0.01, 0.03))
            stop_price = base_price * (1 - random.uniform(0.01, 0.02))
            target_price = entry_price * (1 + random.uniform(0.02, 0.05))
        else:
            entry_price = base_price * (1 - random.uniform(0.01, 0.03))
            stop_price = base_price * (1 + random.uniform(0.01, 0.02))
            target_price = entry_price * (1 - random.uniform(0.02, 0.05))
        
        # Generate setup time between 1-5 days ago
        days_ago = random.randint(1, 5)
        detected_time = (datetime.now() - timedelta(days=days_ago)).isoformat()
        
        pending_setups.append({
            "symbol": symbol,
            "direction": direction,
            "timeframe": setup_timeframe,
            "sweep_candle_complete": has_sweep,
            "engulf_candle_complete": has_engulf,
            "retrace_percent": retrace_pct,
            "confirmation_status": " | ".join(status_parts),
            "entry_price": round(entry_price, 2),
            "stop_price": round(stop_price, 2),
            "target_price": round(target_price, 2),
            "detected_time": detected_time
        })
    
    # Sort by completeness (completed sweep, then engulf, then retrace percent)
    def get_completion_score(setup):
        score = 0
        if setup["sweep_candle_complete"]:
            score += 25
        if setup["engulf_candle_complete"]:
            score += 25
        score += min(setup["retrace_percent"], 33) / 33 * 25
        return score
    
    pending_setups.sort(key=get_completion_score, reverse=True)
    return pending_setups