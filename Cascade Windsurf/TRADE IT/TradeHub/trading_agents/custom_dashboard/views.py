"""
Views for the custom dashboard application.
"""
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
)
import os
import json
from loguru import logger

try:
    from flask_socketio import SocketIO
    SOCKETIO_AVAILABLE = True
except ImportError:
    logger.warning("flask-socketio not installed. Real-time updates will not be available.")
    SOCKETIO_AVAILABLE = False

# Create a blueprint for the views
bp = Blueprint("views", __name__)

# Initialize SocketIO if available
socketio = SocketIO(cors_allowed_origins="*") if SOCKETIO_AVAILABLE else None

# Dict to store active subscriptions
active_subscriptions = {}

@bp.route("/")
def index():
    """Render the main dashboard with feed layout."""
    return render_template("index.html")


@bp.route("/market-analysis")
def market_analysis():
    """Render the market analysis page."""
    return render_template("market_analysis.html")


@bp.route("/trade-setups")
def trade_setups():
    """Render the trade setups page."""
    return render_template("trade_setups.html")


@bp.route("/watchlist")
def watchlist():
    """Render the watchlist page."""
    return render_template("watchlist.html")


@bp.route("/backtest")
def backtest():
    """Render the backtest page."""
    return render_template("backtest.html")


@bp.route("/settings")
def settings():
    """Render the settings page."""
    return render_template("settings.html")


@bp.route('/tradingview')
def tradingview():
    """Render the TradingView chart dashboard."""
    return render_template('tradingview.html')


@bp.route("/test-api")
def test_api():
    """Test page for the setup API."""
    return render_template("test_setup_api.html")


@bp.route("/setup/<int:setup_id>")
def setup_detail(setup_id):
    """Render the setup detail page."""
    return render_template("setup_detail.html", setup_id=setup_id)


@bp.route("/favicon.ico")
def favicon():
    """Serve the favicon."""
    return send_from_directory(
        os.path.join(current_app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


def init_app(app):
    """Initialize the application with the views blueprint."""
    app.register_blueprint(bp)
    
    # Initialize SocketIO with the Flask app if available
    if SOCKETIO_AVAILABLE and socketio:
        socketio.init_app(app)
        
        # Set up SocketIO event handlers
        @socketio.on('connect')
        def handle_connect():
            logger.info("Client connected to WebSocket")
        
        @socketio.on('disconnect')
        def handle_disconnect():
            logger.info("Client disconnected from WebSocket")
            
        @socketio.on('subscribe')
        def handle_subscribe(data):
            """Handle subscription to real-time data for a symbol."""
            try:
                symbol = data.get('symbol')
                if not symbol:
                    return {'status': 'error', 'message': 'No symbol provided'}
                
                logger.info(f"Client subscribed to real-time data for {symbol}")
                
                # Store subscription in active_subscriptions
                client_id = request.sid if hasattr(request, 'sid') else None
                
                # Get SID from the SocketIO context if not in request
                if client_id is None:
                    from flask_socketio import request as socketio_request
                    client_id = socketio_request.sid
                
                if client_id not in active_subscriptions:
                    active_subscriptions[client_id] = set()
                active_subscriptions[client_id].add(symbol)
                
                # Try to use Alpaca for real-time data if available
                try:
                    from trading_agents.utils.alpaca_connector import subscribe_to_symbol
                    
                    # Create a callback function to send data to this specific client
                    def send_update(data):
                        socketio.emit('price_update', data, room=client_id)
                    
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
                
                logger.info(f"Client unsubscribed from real-time data for {symbol}")
                
                # Remove subscription from active_subscriptions
                client_id = request.sid if hasattr(request, 'sid') else None
                
                # Get SID from the SocketIO context if not in request
                if client_id is None:
                    from flask_socketio import request as socketio_request
                    client_id = socketio_request.sid
                
                if client_id in active_subscriptions:
                    active_subscriptions[client_id].discard(symbol)
                
                return {'status': 'success', 'message': f'Unsubscribed from {symbol}'}
            except Exception as e:
                logger.error(f"Error in unsubscribe handler: {e}")
                return {'status': 'error', 'message': str(e)}
    
    return app


def run_socketio(app, host='0.0.0.0', port=8080, debug=True):
    """Run the application with SocketIO support."""
    if SOCKETIO_AVAILABLE and socketio:
        # Ensure we bind to 0.0.0.0 for wider accessibility
        logger.info(f"Starting SocketIO server on {host}:{port}")
        socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
    else:
        # Fallback to regular Flask server
        logger.info(f"Starting Flask server on {host}:{port}")
        app.run(host=host, port=port, debug=debug) 