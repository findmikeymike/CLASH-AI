#!/usr/bin/env python
"""
Alpaca Data Viewer

A minimal web interface for viewing Alpaca market data.
Built on Python's standard library HTTP server for maximum reliability.
"""
import http.server
import socketserver
import json
import os
import sys
import time
from datetime import datetime, timedelta
import urllib.request
import urllib.error
import threading
import subprocess

# Configuration
PORT = 7777
ALPACA_API_KEY = os.environ.get('ALPACA_API_KEY', 'PKXFD5Z3GYF03HNVGDVR')
ALPACA_API_SECRET = os.environ.get('ALPACA_API_SECRET', 'i5GYQXgmfZS4sdQlkCzixA9jU5EgTXZEyWAQ0CMl')
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
ALPACA_DATA_URL = "https://data.alpaca.markets"

# Check if we have required packages
required_packages = ["alpaca-trade-api", "alpaca-py"]
missing_packages = []

for package in required_packages:
    try:
        __import__(package.replace("-", "_"))
    except ImportError:
        missing_packages.append(package)

# Install missing packages if needed
if missing_packages:
    print(f"Installing missing packages: {', '.join(missing_packages)}")
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
    print("Packages installed successfully")

# Now we can safely import Alpaca
try:
    import alpaca_trade_api as tradeapi
    from alpaca.trading.client import TradingClient
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    print("Alpaca modules imported successfully")
except ImportError as e:
    print(f"Error importing Alpaca modules: {e}")
    print("Continuing with basic API-only access")

# Default symbols to display
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

# In-memory cache for API responses
cache = {}
cache_expiry = {}
CACHE_DURATION = 60  # seconds

# Handler for HTTP requests
class AlpacaHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Add timestamp to log messages
        sys.stderr.write("%s - %s - %s\n" % (
            self.log_date_time_string(),
            self.address_string(),
            format % args))
    
    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
        self.end_headers()
    
    def _handle_error(self, status=500, message="Internal Server Error"):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"error": message}
        self.wfile.write(json.dumps(response).encode("utf-8"))
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Home page
            if self.path == "/":
                self._serve_home_page()
            
            # API endpoint for time
            elif self.path == "/api/time":
                self._serve_time()
            
            # API endpoint for symbols
            elif self.path == "/api/symbols":
                self._serve_symbols()
            
            # API endpoint for account info
            elif self.path == "/api/account":
                self._serve_account_info()
            
            # API endpoint for market data
            elif self.path.startswith("/api/market-data/"):
                symbol = self.path.split("/")[-1]
                self._serve_market_data(symbol)
            
            # 404 for anything else
            else:
                self._handle_error(404, "Not found")
        
        except Exception as e:
            print(f"Error handling request: {e}")
            self._handle_error(500, str(e))
    
    def _serve_home_page(self):
        """Serve the home page HTML"""
        self._set_headers("text/html")
        with open(os.path.join(os.path.dirname(__file__), "alpaca_viewer.html"), "r") as f:
            html = f.read()
        self.wfile.write(html.encode("utf-8"))
    
    def _serve_time(self):
        """Serve the current time"""
        self._set_headers()
        response = {
            "server_time": datetime.now().isoformat(),
            "timestamp": datetime.now().timestamp()
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))
    
    def _serve_symbols(self):
        """Serve the list of default symbols"""
        self._set_headers()
        symbols = [{"symbol": s} for s in DEFAULT_SYMBOLS]
        self.wfile.write(json.dumps(symbols).encode("utf-8"))
    
    def _serve_account_info(self):
        """Serve Alpaca account information"""
        # Check cache first
        if "account" in cache and time.time() < cache_expiry.get("account", 0):
            self._set_headers()
            self.wfile.write(json.dumps(cache["account"]).encode("utf-8"))
            return
        
        try:
            # Try the newer API first
            try:
                trading_client = TradingClient(ALPACA_API_KEY, ALPACA_API_SECRET, paper=True)
                account = trading_client.get_account()
                response = {
                    "id": account.id,
                    "status": account.status,
                    "equity": account.equity,
                    "cash": account.cash,
                    "buying_power": account.buying_power,
                    "api_version": "v2"
                }
            except (NameError, ImportError):
                # Fall back to direct API call
                url = f"{ALPACA_BASE_URL}/v2/account"
                headers = {
                    "APCA-API-KEY-ID": ALPACA_API_KEY,
                    "APCA-API-SECRET-KEY": ALPACA_API_SECRET
                }
                req = urllib.request.Request(url, headers=headers)
                response = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
                response["api_version"] = "direct"
            
            # Cache the response
            cache["account"] = response
            cache_expiry["account"] = time.time() + CACHE_DURATION
            
            self._set_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
        
        except Exception as e:
            print(f"Error fetching account info: {e}")
            self._handle_error(500, f"Error fetching account info: {str(e)}")
    
    def _serve_market_data(self, symbol):
        """Serve market data for a specific symbol"""
        # Validate symbol
        if not symbol or not symbol.isalpha():
            self._handle_error(400, "Invalid symbol")
            return
        
        symbol = symbol.upper()
        cache_key = f"market_data_{symbol}"
        
        # Check cache first
        if cache_key in cache and time.time() < cache_expiry.get(cache_key, 0):
            self._set_headers()
            self.wfile.write(json.dumps(cache[cache_key]).encode("utf-8"))
            return
        
        try:
            # Try the newer API first
            try:
                # Create a stock historical data client
                stock_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_API_SECRET)
                
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
                bar_list = bars.data.get(symbol, [])
                for bar in reversed(bar_list):  # Most recent first
                    change = 0
                    if prev_close:
                        change = ((bar.close - prev_close) / prev_close) * 100
                    
                    result.append({
                        "timestamp": bar.timestamp.isoformat(),
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume,
                        "change": change
                    })
                    
                    prev_close = bar.close
                
                response = {"symbol": symbol, "bars": result}
            
            except (NameError, ImportError):
                # Fall back to direct API call
                url = f"{ALPACA_DATA_URL}/v2/stocks/{symbol}/bars"
                params = {
                    "timeframe": "1Day",
                    "start": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
                    "end": datetime.now().strftime("%Y-%m-%d"),
                    "limit": 10
                }
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                url = f"{url}?{query_string}"
                
                headers = {
                    "APCA-API-KEY-ID": ALPACA_API_KEY,
                    "APCA-API-SECRET-KEY": ALPACA_API_SECRET
                }
                
                req = urllib.request.Request(url, headers=headers)
                raw_response = urllib.request.urlopen(req).read().decode("utf-8")
                api_response = json.loads(raw_response)
                
                # Process the bars
                result = []
                prev_close = None
                
                for bar in reversed(api_response.get("bars", [])):
                    change = 0
                    if prev_close:
                        change = ((bar["c"] - prev_close) / prev_close) * 100
                    
                    result.append({
                        "timestamp": bar["t"],
                        "open": bar["o"],
                        "high": bar["h"],
                        "low": bar["l"],
                        "close": bar["c"],
                        "volume": bar["v"],
                        "change": change
                    })
                    
                    prev_close = bar["c"]
                
                response = {"symbol": symbol, "bars": result}
            
            # Cache the response
            cache[cache_key] = response
            cache_expiry[cache_key] = time.time() + CACHE_DURATION
            
            self._set_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
        
        except Exception as e:
            print(f"Error fetching market data for {symbol}: {e}")
            self._handle_error(500, f"Error fetching market data: {str(e)}")

# Create the HTML file for the viewer
def create_html_file():
    """Create the HTML file for the viewer"""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Alpaca Data Viewer</title>
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
        // Global state
        let symbols = ["AAPL"];
        let accountInfo = null;
        let serverStartTime = null;
        
        // Function to fetch symbols
        function fetchSymbols() {
            fetch('/api/symbols')
                .then(response => response.json())
                .then(data => {
                    symbols = data.map(item => item.symbol);
                    const symbolSelect = document.getElementById('symbol-select');
                    
                    if (symbolSelect) {
                        // Clear existing options
                        symbolSelect.innerHTML = '';
                        
                        // Add options for each symbol
                        symbols.forEach(symbol => {
                            const option = document.createElement('option');
                            option.value = symbol;
                            option.textContent = symbol;
                            symbolSelect.appendChild(option);
                        });
                        
                        // Set default to first symbol
                        if (symbols.length > 0) {
                            symbolSelect.value = symbols[0];
                        }
                    }
                    
                    // Fetch initial market data
                    fetchMarketData();
                })
                .catch(error => {
                    console.error('Error fetching symbols:', error);
                });
        }
        
        // Function to fetch account info
        function fetchAccountInfo() {
            fetch('/api/account')
                .then(response => response.json())
                .then(data => {
                    accountInfo = data;
                    updateAccountInfo();
                })
                .catch(error => {
                    console.error('Error fetching account info:', error);
                    document.getElementById('connection-status').innerHTML = 
                        '<span class="error">Error connecting to Alpaca: ' + error.message + '</span>';
                });
        }
        
        // Function to update account info display
        function updateAccountInfo() {
            if (!accountInfo) return;
            
            document.getElementById('connection-status').innerHTML = 
                '<span class="success">Connected to Alpaca API ✓</span>';
            
            if (document.getElementById('account-id')) {
                document.getElementById('account-id').textContent = accountInfo.id || 'N/A';
            }
            
            if (document.getElementById('account-equity')) {
                document.getElementById('account-equity').textContent = 
                    '$' + (parseFloat(accountInfo.equity).toFixed(2) || '0.00');
            }
            
            if (document.getElementById('account-cash')) {
                document.getElementById('account-cash').textContent = 
                    '$' + (parseFloat(accountInfo.cash).toFixed(2) || '0.00');
            }
            
            if (document.getElementById('account-buying-power')) {
                document.getElementById('account-buying-power').textContent = 
                    '$' + (parseFloat(accountInfo.buying_power).toFixed(2) || '0.00');
            }
        }
        
        // Function to fetch server time
        function fetchServerTime() {
            fetch('/api/time')
                .then(response => response.json())
                .then(data => {
                    serverStartTime = data;
                    updateServerTime();
                })
                .catch(error => {
                    console.error('Error fetching server time:', error);
                });
        }
        
        // Function to update server time display
        function updateServerTime() {
            if (!serverStartTime) return;
            
            const serverTimeElement = document.getElementById('server-time');
            if (serverTimeElement) {
                const date = new Date(serverStartTime.server_time);
                serverTimeElement.textContent = date.toLocaleString();
            }
        }
        
        // Function to fetch market data
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
        
        // Check Alpaca connection status
        function checkAlpacaStatus() {
            const connectionStatus = document.getElementById('connection-status');
            if (!connectionStatus) return;
            
            if (accountInfo) {
                connectionStatus.innerHTML = '<span class="success">Connected to Alpaca API ✓</span>';
            } else {
                connectionStatus.innerHTML = '<span class="warning">Connecting to Alpaca...</span>';
                fetchAccountInfo();
            }
        }
        
        // Auto-refresh data
        function setupAutoRefresh() {
            // Refresh market data every 30 seconds
            setInterval(fetchMarketData, 30000);
            
            // Refresh account info every 60 seconds
            setInterval(fetchAccountInfo, 60000);
        }
        
        // Initialize everything when DOM is loaded
        document.addEventListener('DOMContentLoaded', () => {
            // Initial data load
            fetchSymbols();
            fetchAccountInfo();
            fetchServerTime();
            
            // Set up auto-refresh
            setupAutoRefresh();
        });
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Alpaca Data Viewer</h1>
        </div>
        
        <div class="card">
            <h2>System Status</h2>
            <div class="info-box">
                <div class="info-item">
                    <h3>Server Time</h3>
                    <p id="server-time">Loading...</p>
                </div>
                <div class="info-item">
                    <h3>Alpaca API</h3>
                    <p id="connection-status" class="warning">Connecting to Alpaca...</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Account Information</h2>
            <div class="info-box">
                <div class="info-item">
                    <h3>Account ID</h3>
                    <p id="account-id">Loading...</p>
                </div>
                <div class="info-item">
                    <h3>Equity</h3>
                    <p id="account-equity">$0.00</p>
                </div>
                <div class="info-item">
                    <h3>Cash</h3>
                    <p id="account-cash">$0.00</p>
                </div>
                <div class="info-item">
                    <h3>Buying Power</h3>
                    <p id="account-buying-power">$0.00</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Market Data</h2>
            
            <div class="symbol-selector">
                <select id="symbol-select">
                    <option value="AAPL">AAPL</option>
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
    </div>
</body>
</html>"""
    
    html_file = os.path.join(os.path.dirname(__file__), "alpaca_viewer.html")
    with open(html_file, "w") as f:
        f.write(html)
    print(f"Created HTML file: {html_file}")

# Main function
def main():
    create_html_file()
    
    # Print nice welcome message
    print("\n" + "=" * 50)
    print("  ALPACA DATA VIEWER")
    print("=" * 50)
    print(f"  Starting server on port {PORT}")
    print(f"  Open your browser to: http://localhost:{PORT}/")
    print("=" * 50 + "\n")
    
    # Start the server
    with socketserver.TCPServer(("", PORT), AlpacaHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down the server...")
            httpd.server_close()
            print("Server stopped.")

if __name__ == "__main__":
    main() 