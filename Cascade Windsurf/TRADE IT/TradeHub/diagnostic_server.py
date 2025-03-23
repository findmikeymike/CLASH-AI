#!/usr/bin/env python
"""
Trading System Diagnostic Server

A simplified version of the Flask server that includes basic routes
for diagnosing potential issues with the trading system.
"""
from flask import Flask, jsonify, render_template_string
import sys
import os
import json
from datetime import datetime, timedelta
from loguru import logger
import argparse

# Set up logging
logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

# Create Flask app
app = Flask(__name__)

# Try importing SocketIO 
try:
    from flask_socketio import SocketIO
    socketio = SocketIO(cors_allowed_origins="*")
    SOCKETIO_AVAILABLE = True
    logger.success("SocketIO imported successfully")
except ImportError:
    socketio = None
    SOCKETIO_AVAILABLE = False
    logger.warning("SocketIO not available. Install with: pip install flask-socketio==5.3.6 python-socketio==5.11.1 eventlet==0.33.3")

# HTML template for the diagnostic page
DIAGNOSTIC_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Trading System Diagnostics</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
        }
        .card {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .card h2 {
            margin-top: 0;
            color: #3498db;
        }
        .success {
            color: #27ae60;
        }
        .error {
            color: #e74c3c;
        }
        .warning {
            color: #f39c12;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-green {
            background-color: #27ae60;
        }
        .status-yellow {
            background-color: #f39c12;
        }
        .status-red {
            background-color: #e74c3c;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #2980b9;
        }
        pre {
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        .socket-status {
            margin-top: 10px;
            font-weight: bold;
        }
    </style>
    {% if socketio_available %}
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.0/socket.io.js"></script>
    <script>
        let socket;
        
        function connectWebSocket() {
            try {
                console.log('Connecting to WebSocket...');
                socket = io();
                
                socket.on('connect', () => {
                    console.log('WebSocket connected');
                    document.getElementById('socket-status').innerHTML = 
                        '<span class="status-indicator status-green"></span> WebSocket Connected';
                    document.getElementById('socket-status').className = 'socket-status success';
                });
                
                socket.on('disconnect', () => {
                    console.log('WebSocket disconnected');
                    document.getElementById('socket-status').innerHTML = 
                        '<span class="status-indicator status-red"></span> WebSocket Disconnected';
                    document.getElementById('socket-status').className = 'socket-status error';
                });
                
                socket.on('connect_error', (error) => {
                    console.error('WebSocket connection error:', error);
                    document.getElementById('socket-status').innerHTML = 
                        '<span class="status-indicator status-red"></span> WebSocket Error: ' + error;
                    document.getElementById('socket-status').className = 'socket-status error';
                });
                
                socket.on('diagnostic_message', (data) => {
                    console.log('Received diagnostic message:', data);
                    
                    const messagesContainer = document.getElementById('socket-messages');
                    const messageElement = document.createElement('div');
                    messageElement.className = 'card';
                    messageElement.innerHTML = `
                        <h3>${data.type || 'Message'}</h3>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                        <small>${new Date().toLocaleTimeString()}</small>
                    `;
                    messagesContainer.prepend(messageElement);
                });
            } catch (error) {
                console.error('Error setting up WebSocket:', error);
                document.getElementById('socket-status').innerHTML = 
                    '<span class="status-indicator status-red"></span> WebSocket Setup Error: ' + error;
                document.getElementById('socket-status').className = 'socket-status error';
            }
        }
        
        function sendTestMessage() {
            if (socket && socket.connected) {
                socket.emit('test_message', { message: 'Test message from client', timestamp: new Date().toISOString() });
            } else {
                alert('Socket is not connected');
            }
        }
        
        window.addEventListener('load', () => {
            if (typeof io !== 'undefined') {
                connectWebSocket();
            } else {
                document.getElementById('socket-status').innerHTML = 
                    '<span class="status-indicator status-red"></span> Socket.IO not loaded';
                document.getElementById('socket-status').className = 'socket-status error';
            }
        });
    </script>
    {% endif %}
</head>
<body>
    <div class="container">
        <h1>Trading System Diagnostics</h1>
        
        <div class="card">
            <h2>System Status</h2>
            <p><strong>Flask Server:</strong> <span class="success">Running</span></p>
            <p><strong>SocketIO Status:</strong> {% if socketio_available %}<span class="success">Available</span>{% else %}<span class="error">Not Available</span>{% endif %}</p>
            <p><strong>Server Time:</strong> {{ server_time }}</p>
            {% if socketio_available %}
            <p id="socket-status" class="socket-status warning">
                <span class="status-indicator status-yellow"></span> WebSocket Connecting...
            </p>
            {% endif %}
        </div>
        
        <div class="card">
            <h2>API Diagnostics</h2>
            <p>Test the basic API endpoints to verify they are working correctly.</p>
            <a href="/api/health" target="_blank"><button>Test Health Endpoint</button></a>
            <a href="/api/time" target="_blank"><button>Test Time Endpoint</button></a>
            <a href="/api/symbols" target="_blank"><button>Test Symbols Endpoint</button></a>
        </div>
        
        {% if socketio_available %}
        <div class="card">
            <h2>WebSocket Testing</h2>
            <p>Test WebSocket communication with the server.</p>
            <button onclick="sendTestMessage()">Send Test Message</button>
            
            <div id="socket-messages">
                <!-- WebSocket messages will appear here -->
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

# Routes
@app.route('/')
def index():
    """Main diagnostic page."""
    server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template_string(
        DIAGNOSTIC_HTML, 
        socketio_available=SOCKETIO_AVAILABLE, 
        server_time=server_time
    )

@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "Diagnostic Server"
    })

@app.route('/api/time')
def current_time():
    """Current server time endpoint."""
    return jsonify({
        "server_time": datetime.now().isoformat(),
        "utc_time": datetime.utcnow().isoformat()
    })

@app.route('/api/symbols')
def symbols():
    """Test endpoint to return available symbols."""
    sample_symbols = [
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ"},
        {"symbol": "TSLA", "name": "Tesla, Inc.", "exchange": "NASDAQ"}
    ]
    return jsonify(sample_symbols)

# Set up SocketIO if available
if SOCKETIO_AVAILABLE and socketio:
    socketio.init_app(app)
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        logger.info(f"Client connected: {request.sid}")
        socketio.emit('diagnostic_message', {
            "type": "connection_status",
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('test_message')
    def handle_test_message(data):
        """Handle test messages from clients."""
        logger.info(f"Received test message: {data}")
        
        # Echo the message back to the client
        socketio.emit('diagnostic_message', {
            "type": "echo_response",
            "original_message": data,
            "server_received": datetime.now().isoformat()
        })

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the Trading System Diagnostic Server")
    parser.add_argument("--port", type=int, default=5555, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    args = parser.parse_args()
    
    port = args.port
    host = args.host
    debug = args.debug
    
    logger.info(f"Starting diagnostic server on {host}:{port}")
    logger.info(f"Open in your browser: http://localhost:{port}/")
    
    if SOCKETIO_AVAILABLE and socketio:
        logger.info("Running with SocketIO support")
        socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
    else:
        logger.info("Running without SocketIO support")
        app.run(host=host, port=port, debug=debug) 