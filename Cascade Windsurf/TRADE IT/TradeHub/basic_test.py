"""
Basic Flask server test without complex dependencies.
"""
from flask import Flask, send_file
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a simple Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Serve the test template directly."""
    logger.info("Home page requested")
    return send_file('test_template.html')

if __name__ == '__main__':
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run basic test server")
    parser.add_argument("--port", type=int, default=9090, help="Port to run the server on")
    args = parser.parse_args()
    
    logger.info(f"Starting test server on port {args.port}")
    app.run(host='0.0.0.0', port=args.port, debug=True, threaded=False) 