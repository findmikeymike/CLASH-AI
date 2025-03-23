#!/usr/bin/env python3
"""
Run script for the Custom TradingView Dashboard
"""
from trading_agents.custom_dashboard import create_app
from trading_agents.custom_dashboard.views import run_socketio

if __name__ == "__main__":
    # Create the application instance
    app = create_app()
    
    # Run the application with SocketIO support if available
    run_socketio(app, host='0.0.0.0', port=8081, debug=True)
