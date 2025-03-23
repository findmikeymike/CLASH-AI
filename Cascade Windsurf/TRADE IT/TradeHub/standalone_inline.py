from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from loguru import logger
import sys
import argparse
import os
import json
import random
from datetime import datetime, timedelta

# Create a Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tradehubsecret'

# Set up SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize logger
logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")

# Store active subscriptions
active_subscriptions = {}

# The HTML from simplified_chart.html, embedded directly
CHART_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trade Hub - Simplified Chart</title>
    <!-- TradingView Lightweight Charts -->
    <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
    <!-- Socket.IO Client -->
    <script src="https://cdn.socket.io/4.7.3/socket.io.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #1E222D;
            color: #d1d4dc;
        }
        .container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            padding: 20px;
            box-sizing: border-box;
        }
        .header {
            padding: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .title {
            font-size: 24px;
            font-weight: bold;
        }
        .controls {
            display: flex;
            gap: 10px;
        }
        select, button {
            padding: 6px 12px;
            border-radius: 4px;
            border: 1px solid #3f4454;
            background-color: #2a2e39;
            color: #d1d4dc;
        }
        .chart-container {
            flex: 1;
            position: relative;
            border-radius: 8px;
            overflow: hidden;
            background-color: #1E222D;
        }
        #chart {
            width: 100%;
            height: 100%;
        }
        .chart-tooltip {
            position: absolute;
            display: none;
            padding: 8px;
            background-color: rgba(42, 46, 57, 0.9);
            color: #d1d4dc;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            pointer-events: none;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .tooltip-date {
            margin-bottom: 4px;
            font-weight: bold;
        }
        .tooltip-price {
            display: grid;
            grid-template-columns: auto auto;
            gap: 4px;
        }
        .tooltip-value {
            font-weight: bold;
        }
        .footer {
            margin-top: 20px;
            text-align: center;
            font-size: 12px;
            color: #6c757d;
        }
        .status {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background-color: #2a2e39;
            border-radius: 4px;
            margin-top: 10px;
        }
        .connection-status {
            display: flex;
            align-items: center;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .connected {
            background-color: #26a69a;
        }
        .disconnected {
            background-color: #ef5350;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">Trade Hub - Simplified Chart</div>
            <div class="controls">
                <select id="symbolSelect">
                    <option value="AAPL">AAPL - Apple Inc.</option>
                    <option value="MSFT">MSFT - Microsoft Corp.</option>
                    <option value="GOOGL">GOOGL - Alphabet Inc.</option>
                    <option value="AMZN">AMZN - Amazon.com Inc.</option>
                    <option value="META">META - Meta Platforms Inc.</option>
                    <option value="NVDA">NVDA - NVIDIA Corp.</option>
                    <option value="TSLA">TSLA - Tesla Inc.</option>
                </select>
                <select id="timeframeSelect">
                    <option value="1m">1 Minute</option>
                    <option value="5m">5 Minutes</option>
                    <option value="15m">15 Minutes</option>
                    <option value="30m">30 Minutes</option>
                    <option value="1h">1 Hour</option>
                    <option value="4h">4 Hours</option>
                    <option value="1d" selected>1 Day</option>
                    <option value="1w">1 Week</option>
                </select>
                <button id="refreshButton">Refresh</button>
            </div>
        </div>
        
        <div class="chart-container">
            <div id="chart"></div>
            <div class="chart-tooltip"></div>
        </div>
        
        <div class="status">
            <div class="connection-status">
                <div id="statusDot" class="status-dot disconnected"></div>
                <span id="statusText">Disconnected</span>
            </div>
            <div class="price-info">
                Last Price: <span id="lastPrice">--</span>
            </div>
        </div>
        
        <div class="footer">
            Trade Hub - Powered by Alpaca Markets - &copy; 2025
        </div>
    </div>

    <script>
        // Global variables
        let chart = null;
        let candleSeries = null;
        let volumeSeries = null;
        let socket = null;
        let currentSymbol = 'AAPL';
        let currentTimeframe = '1d';
        let isConnected = false;
        
        // Initialize chart on load
        document.addEventListener('DOMContentLoaded', function() {
            initChart();
            setupEventListeners();
            connectWebSocket();
            loadSymbolData(currentSymbol, currentTimeframe);
        });
        
        // Initialize TradingView chart
        function initChart() {
            const chartContainer = document.getElementById('chart');
            
            // Create chart
            chart = LightweightCharts.createChart(chartContainer, {
                layout: {
                    background: { color: '#1E222D' },
                    textColor: '#d1d4dc',
                },
                grid: {
                    vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
                    horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
                },
                rightPriceScale: {
                    borderColor: 'rgba(197, 203, 206, 0.8)',
                    scaleMargins: {
                        top: 0.1,
                        bottom: 0.2
                    }
                },
                timeScale: {
                    borderColor: 'rgba(197, 203, 206, 0.8)',
                    timeVisible: true,
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                }
            });
            
            // Resize chart with window
            window.addEventListener('resize', () => {
                chart.applyOptions({
                    width: chartContainer.clientWidth,
                    height: chartContainer.clientHeight
                });
            });
            
            // Add candlestick series
            candleSeries = chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });
            
            // Add volume series
            volumeSeries = chart.addHistogramSeries({
                color: '#26a69a',
                priceFormat: {
                    type: 'volume',
                },
                priceScaleId: 'volume',
                scaleMargins: {
                    top: 0.8,
                    bottom: 0
                },
            });
            
            // Set volume scale options
            chart.priceScale('volume').applyOptions({
                scaleMargins: {
                    top: 0.8,
                    bottom: 0
                },
                visible: false
            });
            
            // Set up tooltip
            const toolTip = document.querySelector('.chart-tooltip');
            
            chart.subscribeCrosshairMove(param => {
                if (!param || !param.time || param.point === undefined) {
                    toolTip.style.display = 'none';
                    return;
                }
                
                const data = param.seriesData.get(candleSeries);
                if (!data) {
                    toolTip.style.display = 'none';
                    return;
                }
                
                toolTip.style.display = 'block';
                
                const dateStr = new Date(param.time * 1000).toLocaleDateString();
                toolTip.innerHTML = `
                    <div class="tooltip-date">${dateStr}</div>
                    <div class="tooltip-price">
                        <div>O: <span class="tooltip-value">${data.open.toFixed(2)}</span></div>
                        <div>H: <span class="tooltip-value">${data.high.toFixed(2)}</span></div>
                        <div>L: <span class="tooltip-value">${data.low.toFixed(2)}</span></div>
                        <div>C: <span class="tooltip-value">${data.close.toFixed(2)}</span></div>
                    </div>
                `;
                
                const y = param.point.y;
                const x = param.point.x;
                
                let left = x + 15;
                let top = y + 15;
                
                if (left > chartContainer.clientWidth - 150) {
                    left = x - 15 - 150;
                }
                
                if (top > chartContainer.clientHeight - 100) {
                    top = y - 15 - 100;
                }
                
                toolTip.style.left = left + 'px';
                toolTip.style.top = top + 'px';
            });
        }
        
        // Set up event listeners
        function setupEventListeners() {
            // Symbol dropdown
            document.getElementById('symbolSelect').addEventListener('change', function() {
                currentSymbol = this.value;
                loadSymbolData(currentSymbol, currentTimeframe);
            });
            
            // Timeframe dropdown
            document.getElementById('timeframeSelect').addEventListener('change', function() {
                currentTimeframe = this.value;
                loadSymbolData(currentSymbol, currentTimeframe);
            });
            
            // Refresh button
            document.getElementById('refreshButton').addEventListener('click', function() {
                loadSymbolData(currentSymbol, currentTimeframe);
            });
        }
        
        // Connect to WebSocket for real-time updates
        function connectWebSocket() {
            try {
                console.log('Connecting to WebSocket...');
                
                // Check if Socket.io is available
                if (typeof io === 'undefined') {
                    console.error('Socket.io is not loaded');
                    updateConnectionStatus(false);
                    return;
                }
                
                // Create WebSocket connection
                socket = io();
                
                // Connection events
                socket.on('connect', () => {
                    console.log('WebSocket connected');
                    updateConnectionStatus(true);
                    subscribeToSymbol(currentSymbol);
                });
                
                socket.on('disconnect', () => {
                    console.log('WebSocket disconnected');
                    updateConnectionStatus(false);
                });
                
                // Data event
                socket.on('price_update', (data) => {
                    console.log('Received price update:', data);
                    updateChartData(data);
                });
                
                socket.on('connect_error', (error) => {
                    console.error('WebSocket connection error:', error);
                    updateConnectionStatus(false);
                });
            } catch (error) {
                console.error('Error connecting to WebSocket:', error);
                updateConnectionStatus(false);
            }
        }
        
        // Update connection status indicators
        function updateConnectionStatus(connected) {
            isConnected = connected;
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            
            if (connected) {
                statusDot.classList.remove('disconnected');
                statusDot.classList.add('connected');
                statusText.textContent = 'Connected';
            } else {
                statusDot.classList.remove('connected');
                statusDot.classList.add('disconnected');
                statusText.textContent = 'Disconnected';
            }
        }
        
        // Subscribe to real-time updates for a symbol
        function subscribeToSymbol(symbol) {
            if (!isConnected || !socket) {
                console.warn('WebSocket not connected');
                return;
            }
            
            console.log(`Subscribing to ${symbol}...`);
            socket.emit('subscribe', { symbol: symbol }, (response) => {
                if (response && response.status === 'success') {
                    console.log(`Successfully subscribed to ${symbol}`);
                } else {
                    console.error(`Failed to subscribe to ${symbol}`);
                }
            });
        }
        
        // Update chart with real-time data
        function updateChartData(data) {
            if (!data || data.symbol !== currentSymbol) return;
            
            const candleData = {
                time: new Date(data.date).getTime() / 1000,
                open: data.open,
                high: data.high,
                low: data.low,
                close: data.close
            };
            
            candleSeries.update(candleData);
            
            const volumeData = {
                time: candleData.time,
                value: data.volume,
                color: data.close >= data.open ? '#26a69a' : '#ef5350'
            };
            
            volumeSeries.update(volumeData);
            
            // Update last price
            document.getElementById('lastPrice').textContent = data.close.toFixed(2);
        }
        
        // Load historical data for a symbol
        function loadSymbolData(symbol, timeframe) {
            console.log(`Loading data for ${symbol} (${timeframe})...`);
            
            // Subscribe to real-time updates if connected
            if (isConnected && socket) {
                subscribeToSymbol(symbol);
            }
            
            // Fetch historical data
            fetch(`/api/price-data/${symbol}?timeframe=${timeframe}`)
                .then(response => response.json())
                .then(data => {
                    console.log(`Received ${data.length} data points for ${symbol}`);
                    
                    // Process candlestick data
                    const candleData = data.map(item => ({
                        time: new Date(item.date).getTime() / 1000,
                        open: item.open,
                        high: item.high,
                        low: item.low,
                        close: item.close
                    }));
                    
                    // Process volume data
                    const volumeData = data.map(item => ({
                        time: new Date(item.date).getTime() / 1000,
                        value: item.volume,
                        color: item.close >= item.open ? '#26a69a' : '#ef5350'
                    }));
                    
                    // Set data to chart
                    candleSeries.setData(candleData);
                    volumeSeries.setData(volumeData);
                    
                    // Fit content
                    chart.timeScale().fitContent();
                    
                    // Update last price
                    if (data.length > 0) {
                        const lastCandle = data[data.length - 1];
                        document.getElementById('lastPrice').textContent = lastCandle.close.toFixed(2);
                    }
                })
                .catch(error => {
                    console.error(`Error loading data for ${symbol}:`, error);
                });
        }
    </script>
</body>
</html>
"""

# API endpoints
@app.route('/')
def index():
    """Serve the main chart page."""
    logger.info("Home page requested")
    return CHART_HTML

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
        logger.info("Attempting to fetch data from Alpaca")
        try:
            from trading_agents.utils.alpaca_connector import fetch_historical_data
            data = fetch_historical_data(symbol, timeframe)
            if data and len(data) > 0:
                logger.info(f"Fetched {len(data)} data points for {symbol} from Alpaca")
                return jsonify(data)
            else:
                logger.warning(f"No data returned from Alpaca for {symbol}, falling back to mock data")
                mock_data = generate_mock_data(symbol)
                return jsonify(mock_data)
        except ImportError:
            logger.warning("Alpaca connector not available, using mock data")
            mock_data = generate_mock_data(symbol)
            return jsonify(mock_data)
    except Exception as e:
        logger.error(f"Error fetching price data for {symbol}: {e}")
        mock_data = generate_mock_data(symbol)
        return jsonify(mock_data)

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
        
        # Just acknowledge the subscription for now
        # Real-time data would come from Alpaca when markets are open
        return {'status': 'success', 'message': f'Subscribed to {symbol}'}
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
    logger.info(f"Generating mock data for {symbol}")
    
    # Generate random price data
    now = datetime.now()
    data = []
    
    # Use different base prices for different symbols to make it look more realistic
    symbol_base_prices = {
        "AAPL": 190.0,
        "MSFT": 410.0,
        "GOOGL": 175.0,
        "AMZN": 185.0,
        "META": 485.0,
        "TSLA": 175.0, 
        "NVDA": 950.0
    }
    
    base_price = symbol_base_prices.get(symbol, 100.0)
    
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

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run standalone Trade Hub server with inline HTML")
    parser.add_argument("--port", type=int, default=9393, help="Port to run the server on")
    args = parser.parse_args()
    
    # Log startup
    logger.info(f"Starting standalone Trade Hub server (inline version) on port {args.port}")
    logger.info("No external files needed - everything is embedded")
    
    # Run the SocketIO server
    socketio.run(app, host='0.0.0.0', port=args.port, debug=True, allow_unsafe_werkzeug=True) 