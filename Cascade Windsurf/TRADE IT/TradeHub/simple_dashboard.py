"""
Simplified version of the TradingView Dashboard without SocketIO or Alpaca integration.
"""
import os
import sys
from flask import Flask, render_template, jsonify, Blueprint, request
from loguru import logger

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create a simple Flask app
app = Flask(__name__, 
            static_folder='trading_agents/custom_dashboard/static',
            template_folder='trading_agents/custom_dashboard/templates')

# Create a views blueprint to match what the templates expect
views_bp = Blueprint("views", __name__)

@views_bp.route("/")
def index():
    """Render the main dashboard."""
    logger.info("Home page requested")
    return render_template("index.html")

# Create an API blueprint for consistency
api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/symbols", methods=["GET"])
def get_symbols():
    """Get a list of available symbols."""
    symbols = [
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"},
        {"symbol": "AMZN", "name": "Amazon.com, Inc.", "exchange": "NASDAQ"}
    ]
    return jsonify(symbols)

@api_bp.route("/price-data/<symbol>", methods=["GET"])
def get_price_data(symbol):
    """Get mock price data for a symbol."""
    import random
    from datetime import datetime, timedelta
    
    # Generate random price data
    now = datetime.now()
    data = []
    base_price = random.uniform(50, 500)
    
    for i in range(100):
        date = now - timedelta(days=100 - i)
        
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
    
    logger.info(f"Generated {len(data)} mock data points for {symbol}")
    return jsonify(data)

@api_bp.route("/run-market-analysis", methods=["POST"])
def run_market_analysis_api():
    """Run the non-Prefect market analysis workflow and return the results."""
    try:
        # Import the market analysis module
        import importlib.util
        
        # Get parameters from the request
        data = request.get_json() or {}
        symbols = data.get("symbols", ["AAPL", "MSFT", "AMZN", "GOOGL"])
        timeframes = data.get("timeframes", ["1D"])
        
        logger.info(f"Running market analysis for symbols: {symbols} on timeframes: {timeframes}")
        
        # Try to import the module
        try:
            # First try to import directly
            from non_prefect_market_analysis import market_analysis_workflow
            logger.info("Successfully imported non_prefect_market_analysis")
        except ImportError:
            # Try to import from file
            file_path = "non_prefect_market_analysis.py"
            if os.path.exists(file_path):
                spec = importlib.util.spec_from_file_location("non_prefect_market_analysis", file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules["non_prefect_market_analysis"] = module
                spec.loader.exec_module(module)
                market_analysis_workflow = module.market_analysis_workflow
                logger.info("Successfully imported non_prefect_market_analysis from file")
            else:
                logger.error("Could not find non_prefect_market_analysis.py")
                return jsonify({"error": "Market analysis module not found"}), 500
        
        # Run the workflow
        result = market_analysis_workflow(
            symbols=symbols,
            timeframes=timeframes,
            analyze_existing_setups=True
        )
        
        # Format the result for the API
        formatted_result = {
            "timestamp": result.get("timestamp", ""),
            "symbols_analyzed": len(result.get("market_analyses", {})),
            "market_analyses": {}
        }
        
        # Format the market analyses
        for symbol, timeframe_data in result.get("market_analyses", {}).items():
            formatted_result["market_analyses"][symbol] = {}
            for timeframe, analysis in timeframe_data.items():
                # Extract the key metrics
                formatted_result["market_analyses"][symbol][timeframe] = {
                    "trend": analysis.get("trend", "unknown"),
                    "strength": analysis.get("strength", 0),
                    "volatility": analysis.get("volatility", 0),
                    "indicators": {
                        "SMA": {
                            "value": analysis.get("indicators", {}).get("SMA", {}).get("value", 0),
                            "trend": analysis.get("indicators", {}).get("SMA", {}).get("trend", "unknown")
                        },
                        "RSI": {
                            "value": analysis.get("indicators", {}).get("RSI", {}).get("value", 0)
                        },
                        "ATR": {
                            "value": analysis.get("indicators", {}).get("ATR", {}).get("value", 0)
                        }
                    }
                }
        
        logger.info(f"Market analysis completed for {len(formatted_result['market_analyses'])} symbols")
        return jsonify(formatted_result)
    except Exception as e:
        logger.error(f"Error running market analysis: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add some other routes the template might need
@views_bp.route("/market-analysis")
def market_analysis():
    """Render the market analysis page."""
    return render_template("market_analysis.html")

@views_bp.route("/trade-setups")
def trade_setups():
    """Render the trade setups page."""
    return render_template("trade_setups.html")

@views_bp.route("/watchlist")
def watchlist():
    """Render the watchlist page."""
    return render_template("watchlist.html")

@views_bp.route("/backtest")
def backtest():
    """Render the backtest page."""
    return render_template("backtest.html")

@views_bp.route("/settings")
def settings():
    """Render the settings page."""
    return render_template("settings.html")

@app.before_request
def log_request():
    from flask import request
    logger.info(f"REQUEST: {request.method} {request.path} from {request.remote_addr}")

if __name__ == '__main__':
    import argparse
    
    # Register the blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run simplified TradingView dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the dashboard on")
    args = parser.parse_args()
    
    logger.info(f"Starting simplified dashboard on port {args.port}")
    # Use threaded=False for simplicity
    app.run(host='0.0.0.0', port=args.port, debug=True, threaded=False) 