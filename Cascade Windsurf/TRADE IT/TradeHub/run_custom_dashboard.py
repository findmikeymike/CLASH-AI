#!/usr/bin/env python3
"""
Run script for the custom TradingView-based dashboard
"""
import os
import sys
from loguru import logger

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from trading_agents.custom_dashboard import create_app
    
    logger.info("Starting custom TradingView dashboard...")
    app = create_app()
    
    if __name__ == "__main__":
        # Use different port to avoid conflicts with other dashboards
        port = int(os.environ.get("PORT", 8070))
        app.run(host="0.0.0.0", port=port, debug=True)
        
except Exception as e:
    logger.error(f"Error starting custom dashboard: {e}")
    raise 