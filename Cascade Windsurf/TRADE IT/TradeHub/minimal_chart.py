from flask import Flask
import argparse

app = Flask(__name__)

# Minimal HTML for a chart
CHART_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Minimal Trading Chart</title>
    <style>
        body { 
            font-family: Arial, sans-serif;
            background-color: #1E222D;
            color: white;
            margin: 0;
            padding: 20px;
        }
        .chart-container {
            background-color: #2a2e39;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            height: 500px;
        }
        h1 { color: #26a69a; }
        .mock-chart {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            border: 1px dashed #666;
            color: #ccc;
        }
    </style>
</head>
<body>
    <h1>Minimal Trading Chart Test</h1>
    <p>This is a minimal test page to verify that basic Flask routing works.</p>
    
    <div class="chart-container">
        <div class="mock-chart">
            <h2>Mock Chart Area</h2>
            <p>If you can see this text, basic Flask routing is working correctly!</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main test page."""
    print("Home page requested")
    return CHART_HTML

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run minimal chart test")
    parser.add_argument("--port", type=int, default=7777, help="Port to run the server on")
    args = parser.parse_args()
    
    port = args.port
    print(f"Starting minimal test server on port {port}")
    print(f"Try accessing: http://localhost:{port}/")
    
    # Run with default Flask server (no SocketIO)
    app.run(host='0.0.0.0', port=port, debug=True) 