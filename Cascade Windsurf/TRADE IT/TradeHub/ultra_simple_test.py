from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    # Simple HTML directly in the response
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ultra Simple Test</title>
        <style>
            body { 
                font-family: Arial, sans-serif;
                background-color: #1E222D;
                color: white;
                text-align: center;
                padding-top: 100px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #2a2e39;
                border-radius: 8px;
            }
            h1 { color: #26a69a; }
            .status { margin-top: 20px; }
            .button {
                display: inline-block;
                padding: 10px 20px;
                background-color: #26a69a;
                color: white;
                border-radius: 4px;
                text-decoration: none;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Ultra Simple Test Page</h1>
            <p>If you can see this page, Flask is working correctly!</p>
            
            <div class="status">
                <h2>Server Status</h2>
                <p>Flask server is running and responding to requests.</p>
            </div>
            
            <a href="/hello" class="button">Test Another Route</a>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/hello')
def hello():
    return "<h1>Hello from the test server!</h1><p>This is a second route.</p><a href='/'>Back to home</a>"

if __name__ == '__main__':
    import sys
    
    # Default port
    port = 9292
    
    # Check if port is provided as command line argument
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    
    print(f"Starting ultra simple test server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 