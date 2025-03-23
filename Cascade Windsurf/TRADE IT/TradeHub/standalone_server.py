"""
Standalone server for Trade Hub with Alpaca integration.
This simplified version avoids complex template dependencies.
"""
import os
import sys
import argparse
from flask import Flask, send_file, jsonify, request
from flask_socketio import SocketIO
from loguru import logger

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create a Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tradehubsecret'

# Set up SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize logger
logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")

# Store active subscriptions
active_subscriptions = {}

# API endpoints
@app.route('/')
def index():
    """Serve the main chart page."""
    logger.info("Home page requested")
    return send_file('simplified_chart.html')

@app.route('/api/symbols', methods=["GET"])
def get_symbols():
    """Get a list of available symbols."""
    logger.info("Symbols requested")
    symbols = [
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"},
        {"symbol": "AMZN", "name": "Amazon.com, Inc.", "exchange": "NASDAQ"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ"},
        {"symbol": "META", "name": "Meta Platforms, Inc.", "exchange": "NASDAQ"},
        {"symbol": "TSLA", "name": "Tesla, Inc.", "exchange": "NASDAQ"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ"}
    ]
    return jsonify(symbols)

@app.route('/api/price-data/<symbol>', methods=["GET"])
def get_price_data(symbol):
    """Get price data for a symbol."""
    timeframe = request.args.get("timeframe", "1d")
    logger.info(f"Price data requested for {symbol} ({timeframe})")
    
    try:
        # Try to use Alpaca
        from trading_agents.utils.alpaca_connector import fetch_historical_data
        data = fetch_historical_data(symbol, timeframe)
        
        if data and len(data) > 0:
            logger.info(f"Fetched {len(data)} data points for {symbol} from Alpaca")
            return jsonify(data)
        else:
            logger.warning(f"No data returned from Alpaca for {symbol}, falling back to mock data")
            return jsonify(generate_mock_data(symbol))
    except ImportError:
        logger.warning("Alpaca connector not available, using mock data")
        return jsonify(generate_mock_data(symbol))
    except Exception as e:
        logger.error(f"Error fetching price data for {symbol}: {e}")
        return jsonify(generate_mock_data(symbol))

# SocketIO events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")
    
    # Remove all subscriptions for this client
    if request.sid in active_subscriptions:
        del active_subscriptions[request.sid]

@socketio.on('subscribe')
def handle_subscribe(data):
    """Handle subscription to real-time data for a symbol."""
    try:
        symbol = data.get('symbol')
        if not symbol:
            return {'status': 'error', 'message': 'No symbol provided'}
        
        logger.info(f"Client {request.sid} subscribed to {symbol}")
        
        # Store subscription
        if request.sid not in active_subscriptions:
            active_subscriptions[request.sid] = set()
        active_subscriptions[request.sid].add(symbol)
        
        # Try to use Alpaca for real-time data
        try:
            from trading_agents.utils.alpaca_connector import subscribe_to_symbol
            
            # Create a callback function to send data to this specific client
            def send_update(data):
                socketio.emit('price_update', data, room=request.sid)
            
            # Subscribe to the symbol
            success = subscribe_to_symbol(symbol, send_update)
            
            if success:
                return {'status': 'success', 'message': f'Subscribed to {symbol}'}
            else:
                return {'status': 'error', 'message': f'Failed to subscribe to {symbol}'}
        except ImportError:
            logger.warning("Alpaca connector not available for real-time data")
            return {'status': 'error', 'message': 'Real-time data not available'}
    except Exception as e:
        logger.error(f"Error in subscribe handler: {e}")
        return {'status': 'error', 'message': str(e)}

@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """Handle unsubscription from real-time data."""
    try:
        symbol = data.get('symbol')
        if not symbol:
            return {'status': 'error', 'message': 'No symbol provided'}
        
        logger.info(f"Client {request.sid} unsubscribed from {symbol}")
        
        # Remove subscription
        if request.sid in active_subscriptions:
            active_subscriptions[request.sid].discard(symbol)
        
        return {'status': 'success', 'message': f'Unsubscribed from {symbol}'}
    except Exception as e:
        logger.error(f"Error in unsubscribe handler: {e}")
        return {'status': 'error', 'message': str(e)}

# Utility functions
def generate_mock_data(symbol, points=200):
    """Generate mock price data for a symbol."""
    import random
    from datetime import datetime, timedelta
    
    logger.info(f"Generating mock data for {symbol}")
    
    # Generate random price data
    now = datetime.now()
    data = []
    base_price = random.uniform(50, 500)
    
    for i in range(points):
        date = now - timedelta(days=points - i)
        
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
    
    return data

# Initialize Alpaca
def initialize_alpaca():
    """Initialize Alpaca connector."""
    try:
        from trading_agents.utils.alpaca_connector import (
            initialize_real_time_data,
            start_data_stream,
            ALPACA_API_KEY,
            ALPACA_API_SECRET
        )
        
        # Initialize real-time data
        if initialize_real_time_data():
            logger.info("Alpaca real-time data initialized successfully")
            start_data_stream()
            return True
        else:
            logger.warning("Could not initialize Alpaca real-time data")
            return False
    except ImportError:
        logger.warning("Alpaca connector not available")
        return False
    except Exception as e:
        logger.error(f"Error initializing Alpaca: {e}")
        return False

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run standalone Trade Hub server")
    parser.add_argument("--port", type=int, default=9090, help="Port to run the server on")
    args = parser.parse_args()
    
    # Initialize Alpaca if available
    initialize_alpaca()
    
    # Log startup
    logger.info(f"Starting standalone Trade Hub server on port {args.port}")
    
    # Run the SocketIO server
    socketio.run(app, host='0.0.0.0', port=args.port, debug=True, allow_unsafe_werkzeug=True) 