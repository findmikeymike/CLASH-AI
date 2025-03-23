#!/usr/bin/env python
"""
Run the TradingView Lightweight Charts dashboard.
"""
import argparse
import sys
import os

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from loguru import logger

logger.info("Starting TradingView Lightweight Charts dashboard...")

from trading_agents.custom_dashboard import create_app
from trading_agents.custom_dashboard.views import run_socketio

# Parse command line arguments
parser = argparse.ArgumentParser(description="Run the TradingView Lightweight Charts dashboard")
parser.add_argument("--port", type=int, default=8080, help="Port to run the dashboard on")
args = parser.parse_args()

# Set up the application
app = create_app()

# Add a simple before_request handler to log all requests
@app.before_request
def log_request():
    import flask
    logger.info(f"REQUEST: {flask.request.method} {flask.request.path} from {flask.request.remote_addr}")

# Initialize the database
from trading_agents.utils.setup_storage import init_db
init_db()

# Set up API key for Alpaca from environment if available
import os
try:
    from trading_agents.utils.alpaca_connector import ALPACA_API_KEY, ALPACA_API_SECRET
    # Check for environment variables and update if available
    if os.environ.get("ALPACA_API_KEY"):
        ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY")
    if os.environ.get("ALPACA_API_SECRET"):
        ALPACA_API_SECRET = os.environ.get("ALPACA_API_SECRET")
    logger.info("Alpaca API credentials configured")
except ImportError:
    logger.warning("Alpaca connector not available")

logger.info(f"Starting dashboard on port {args.port}")

# Run the application with SocketIO support
run_socketio(app, port=args.port, debug=True) 