#!/usr/bin/env python
"""
Ultra-Minimal Trading System

A stripped-down version focusing only on core functionality.
"""
from flask import Flask, render_template_string
import os
import json
from datetime import datetime, timedelta
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('minimal-trading')

# Create Flask app
app = Flask(__name__)

# Minimal HTML with no external dependencies
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Minimal Trading System</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 5px; }
        h1 { color: #333; }
        .card { border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; }
        pre { background: #f8f8f8; padding: 10px; border-radius: 3px; overflow-x: auto; }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Minimal Trading System</h1>
        
        <div class="card">
            <h2>System Status</h2>
            <p><strong>Server Time:</strong> {{ server_time }}</p>
        </div>
        
        <div class="card">
            <h2>Alpaca Connection Status</h2>
            {% if alpaca_status.success %}
            <p class="success">✅ Connected to Alpaca API</p>
            {% else %}
            <p class="error">❌ Alpaca Connection Failed: {{ alpaca_status.error }}</p>
            {% endif %}
        </div>
        
        {% if market_data %}
        <div class="card">
            <h2>Latest Market Data</h2>
            <pre>{{ market_data }}</pre>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

def check_alpaca_connection():
    """Test connection to Alpaca API and return status."""
    try:
        # Try to import Alpaca
        import alpaca_trade_api as tradeapi
        from alpaca.trading.client import TradingClient
        from alpaca.data.historical import StockHistoricalDataClient
        
        # Try both new and old API patterns to ensure compatibility
        # New API pattern (alpaca-py)
        API_KEY = os.environ.get('ALPACA_API_KEY', 'PKXFD5Z3GYF03HNVGDVR')
        API_SECRET = os.environ.get('ALPACA_API_SECRET', 'i5GYQXgmfZS4sdQlkCzixA9jU5EgTXZEyWAQ0CMl')
        
        # Check if we can connect to Alpaca
        trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
        account = trading_client.get_account()
        
        return {
            'success': True,
            'account_id': account.id,
            'equity': account.equity
        }
    except Exception as e:
        logger.error(f"Alpaca connection failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_market_data():
    """Get some basic market data for display."""
    try:
        import alpaca_trade_api as tradeapi
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        
        # Try to get market data
        API_KEY = os.environ.get('ALPACA_API_KEY', 'PKXFD5Z3GYF03HNVGDVR')
        API_SECRET = os.environ.get('ALPACA_API_SECRET', 'i5GYQXgmfZS4sdQlkCzixA9jU5EgTXZEyWAQ0CMl')
        
        # Get data for AAPL
        stock_client = StockHistoricalDataClient(API_KEY, API_SECRET)
        
        # Get bars for the last 5 days
        end = datetime.now()
        start = end - timedelta(days=5)
        
        request_params = StockBarsRequest(
            symbol_or_symbols=["AAPL", "MSFT"],
            timeframe=TimeFrame.Day,
            start=start.strftime("%Y-%m-%d")
        )
        
        bars = stock_client.get_stock_bars(request_params)
        
        # Format and return the data
        result = {}
        for symbol, data in bars.data.items():
            result[symbol] = [
                {
                    'timestamp': bar.timestamp.isoformat(),
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume
                }
                for bar in data
            ]
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Failed to get market data: {str(e)}")
        return json.dumps({"error": str(e)})

@app.route('/')
def index():
    """Main page with minimal UI and API test results."""
    alpaca_status = check_alpaca_connection()
    market_data = get_market_data() if alpaca_status['success'] else None
    
    return render_template_string(
        HTML,
        server_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        alpaca_status=alpaca_status,
        market_data=market_data
    )

if __name__ == '__main__':
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run minimal trading system")
    parser.add_argument("--port", type=int, default=7000, help="Port to run on")
    args = parser.parse_args()
    
    port = args.port
    
    logger.info(f"Starting minimal trading system on port {port}")
    logger.info(f"Access at http://localhost:{port}/")
    
    # Run with default Flask server - no extras
    app.run(host='0.0.0.0', port=port) 