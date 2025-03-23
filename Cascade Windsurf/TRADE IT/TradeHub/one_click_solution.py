#!/usr/bin/env python
"""
One-Click Trading System

A completely self-contained script to run a simple trading dashboard.
No dependencies on any other project files.
"""
import os
import sys
import json
import logging
from datetime import datetime, timedelta

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('one-click-trading')

# Check and install required packages if needed
try:
    import flask
    import alpaca_trade_api
    from alpaca.trading.client import TradingClient
    
    logger.info("All required packages are installed")
except ImportError:
    logger.warning("Missing required packages. Installing now...")
    
    import subprocess
    import sys
    
    # Install required packages
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "flask==2.3.3",
        "alpaca-trade-api==3.2.0",
        "alpaca-py==0.10.0"
    ])
    
    # Now import the required packages
    import flask
    from alpaca.trading.client import TradingClient
    
    logger.info("Packages installed successfully")

# Now that we know the packages are installed, import the rest
from flask import Flask, render_template_string, jsonify, request
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Create Flask app
app = Flask(__name__)

# Alpaca API credentials
# Default to paper trading keys if not provided
API_KEY = os.environ.get('ALPACA_API_KEY', 'PKXFD5Z3GYF03HNVGDVR')
API_SECRET = os.environ.get('ALPACA_API_SECRET', 'i5GYQXgmfZS4sdQlkCzixA9jU5EgTXZEyWAQ0CMl')

# Market symbols to display
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

# HTML template for the main page - completely self-contained
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>One-Click Trading System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f6f9;
            color: #333;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 15px 20px;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .card {
            background-color: white;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .card h2 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .info-box {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 15px;
        }
        .info-item {
            flex: 1;
            min-width: 200px;
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
        }
        .info-item h3 {
            margin-top: 0;
            font-size: 16px;
            color: #7f8c8d;
        }
        .info-item p {
            margin-bottom: 0;
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
        }
        .success { color: #27ae60; }
        .error { color: #e74c3c; }
        .warning { color: #f39c12; }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        table th, table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        table th {
            background-color: #f8f9fa;
        }
        
        .symbol-selector {
            margin-bottom: 15px;
        }
        .symbol-selector select {
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        .symbol-selector button {
            padding: 8px 12px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .symbol-selector button:hover {
            background-color: #2980b9;
        }
        
        .price-change-positive { color: #27ae60; }
        .price-change-negative { color: #e74c3c; }
        
        @media (max-width: 768px) {
            .info-item {
                min-width: 100%;
            }
        }
    </style>
    <script>
        // Function to fetch data periodically
        function fetchMarketData() {
            const symbolSelect = document.getElementById('symbol-select');
            const symbol = symbolSelect ? symbolSelect.value : 'AAPL';
            
            fetch(`/api/market-data/${symbol}`)
                .then(response => response.json())
                .then(data => {
                    updateMarketTable(data);
                    updateLatestPrice(data);
                })
                .catch(error => {
                    console.error('Error fetching market data:', error);
                });
        }
        
        // Update the market data table
        function updateMarketTable(data) {
            const tableBody = document.getElementById('market-data-body');
            if (!tableBody || !data || !data.bars || data.bars.length === 0) return;
            
            // Clear existing rows
            tableBody.innerHTML = '';
            
            // Add rows for each bar
            data.bars.forEach(bar => {
                const row = document.createElement('tr');
                
                // Format the date nicely
                const date = new Date(bar.timestamp);
                const formattedDate = date.toLocaleDateString() + ' ' + 
                                    date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                
                // Create the price change class
                const priceChangeClass = bar.change >= 0 ? 'price-change-positive' : 'price-change-negative';
                const priceChangeSymbol = bar.change >= 0 ? '▲' : '▼';
                
                // Set the row content
                row.innerHTML = `
                    <td>${formattedDate}</td>
                    <td>$${bar.open.toFixed(2)}</td>
                    <td>$${bar.high.toFixed(2)}</td>
                    <td>$${bar.low.toFixed(2)}</td>
                    <td>$${bar.close.toFixed(2)}</td>
                    <td class="${priceChangeClass}">${priceChangeSymbol} ${Math.abs(bar.change).toFixed(2)}%</td>
                    <td>${bar.volume.toLocaleString()}</td>
                `;
                
                tableBody.appendChild(row);
            });
        }
        
        // Update the latest price display
        function updateLatestPrice(data) {
            const priceElement = document.getElementById('latest-price');
            const changeElement = document.getElementById('price-change');
            const volumeElement = document.getElementById('latest-volume');
            
            if (!priceElement || !changeElement || !volumeElement || !data || !data.bars || data.bars.length === 0) return;
            
            const latestBar = data.bars[0];
            
            priceElement.textContent = `$${latestBar.close.toFixed(2)}`;
            
            // Update price change
            const changeClass = latestBar.change >= 0 ? 'price-change-positive' : 'price-change-negative';
            const changeSymbol = latestBar.change >= 0 ? '▲' : '▼';
            changeElement.className = changeClass;
            changeElement.textContent = `${changeSymbol} ${Math.abs(latestBar.change).toFixed(2)}%`;
            
            // Update volume
            volumeElement.textContent = latestBar.volume.toLocaleString();
        }
        
        // Function to reload data when symbol changes
        function changeSymbol() {
            fetchMarketData();
        }
        
        // Load initial data
        document.addEventListener('DOMContentLoaded', () => {
            fetchMarketData();
            
            // Refresh data every 30 seconds
            setInterval(fetchMarketData, 30000);
        });
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>One-Click Trading System</h1>
        </div>
        
        <div class="card">
            <h2>System Status</h2>
            <div class="info-box">
                <div class="info-item">
                    <h3>Server Time</h3>
                    <p>{{ server_time }}</p>
                </div>
                <div class="info-item">
                    <h3>Alpaca API</h3>
                    {% if alpaca_status.success %}
                    <p class="success">Connected ✓</p>
                    {% else %}
                    <p class="error">Disconnected ✗</p>
                    {% endif %}
                </div>
                {% if alpaca_status.success %}
                <div class="info-item">
                    <h3>Account ID</h3>
                    <p>{{ alpaca_status.account_id }}</p>
                </div>
                <div class="info-item">
                    <h3>Account Equity</h3>
                    <p>${{ alpaca_status.equity }}</p>
                </div>
                {% endif %}
            </div>
            
            {% if not alpaca_status.success %}
            <div class="card error">
                <p>Error connecting to Alpaca: {{ alpaca_status.error }}</p>
            </div>
            {% endif %}
        </div>
        
        {% if alpaca_status.success %}
        <div class="card">
            <h2>Market Data</h2>
            
            <div class="symbol-selector">
                <select id="symbol-select">
                    {% for symbol in symbols %}
                    <option value="{{ symbol }}">{{ symbol }}</option>
                    {% endfor %}
                </select>
                <button onclick="changeSymbol()">Update</button>
            </div>
            
            <div class="info-box">
                <div class="info-item">
                    <h3>Latest Price</h3>
                    <p id="latest-price">Loading...</p>
                </div>
                <div class="info-item">
                    <h3>Change</h3>
                    <p id="price-change" class="price-change-positive">Loading...</p>
                </div>
                <div class="info-item">
                    <h3>Volume</h3>
                    <p id="latest-volume">Loading...</p>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Open</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Close</th>
                        <th>Change</th>
                        <th>Volume</th>
                    </tr>
                </thead>
                <tbody id="market-data-body">
                    <tr>
                        <td colspan="7" style="text-align: center;">Loading data...</td>
                    </tr>
                </tbody>
            </table>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

def check_alpaca_connection():
    """Test connection to Alpaca API and return status."""
    try:
        # Try to connect to Alpaca
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

def get_market_data(symbol):
    """Get market data for a specific symbol."""
    try:
        # Create a client
        stock_client = StockHistoricalDataClient(API_KEY, API_SECRET)
        
        # Get data for the last 10 days
        end = datetime.now()
        start = end - timedelta(days=10)
        
        request_params = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Day,
            start=start.strftime("%Y-%m-%d")
        )
        
        bars = stock_client.get_stock_bars(request_params)
        
        # Process the bars
        result = []
        prev_close = None
        
        # Convert bars to a list and calculate price changes
        data = bars.data.get(symbol, [])
        for bar in reversed(data):  # Most recent first
            change = 0
            if prev_close:
                change = ((bar.close - prev_close) / prev_close) * 100
            
            result.append({
                'timestamp': bar.timestamp.isoformat(),
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'change': change
            })
            
            prev_close = bar.close
        
        return {'symbol': symbol, 'bars': result}
    except Exception as e:
        logger.error(f"Failed to get market data for {symbol}: {str(e)}")
        return {'symbol': symbol, 'error': str(e), 'bars': []}

# Define routes
@app.route('/')
def index():
    """Main page with dashboard."""
    alpaca_status = check_alpaca_connection()
    
    return render_template_string(
        HTML_TEMPLATE,
        server_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        alpaca_status=alpaca_status,
        symbols=DEFAULT_SYMBOLS
    )

@app.route('/api/market-data/<symbol>')
def api_market_data(symbol):
    """API endpoint to get market data for a symbol."""
    data = get_market_data(symbol)
    return jsonify(data)

if __name__ == '__main__':
    # Parse command line arguments for port
    import argparse
    parser = argparse.ArgumentParser(description="Run one-click trading system")
    parser.add_argument("--port", type=int, default=9999, help="Port to run on")
    args = parser.parse_args()
    
    port = args.port
    
    # Print nice welcome message
    print("\n" + "=" * 70)
    print(f"  ONE-CLICK TRADING SYSTEM")
    print("=" * 70)
    print(f"  Starting server on port {port}")
    print(f"  Open your browser and go to: http://localhost:{port}/")
    print("=" * 70 + "\n")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port) 