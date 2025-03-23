"""
Simple test server to verify Flask functionality.
"""
from flask import Flask
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a simple Flask app
app = Flask(__name__)

@app.route('/')
def index():
    logger.info("Home page requested")
    return """
    <html>
    <head>
        <title>Test Server</title>
    </head>
    <body>
        <h1>Test Server is Working!</h1>
        <p>This confirms that the Flask server is running and accessible.</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    logger.info("Starting test server on port 5000")
    # Use threaded=False and specify the host explicitly
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=False) 