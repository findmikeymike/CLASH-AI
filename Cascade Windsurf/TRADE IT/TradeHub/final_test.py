#!/usr/bin/env python
"""
Ultra simple Flask test app with no dependencies
"""
from flask import Flask
import sys
import datetime

# Create a Flask application with no dependencies
app = Flask(__name__)

# Very simple HTML page
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Final Test Page</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 50px;
            background-color: #f0f0f0;
        }
        .container {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            max-width: 600px;
            margin: 0 auto;
        }
        h1 {
            color: #4CAF50;
        }
        p {
            color: #333;
        }
        .success {
            color: #4CAF50;
            font-weight: bold;
            font-size: 24px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Final Test Page</h1>
        <p>This is an ultra-simple test page with no dependencies.</p>
        <div class="success">SUCCESS! The Flask server is working correctly.</div>
        <p>If you can see this page, your browser can connect to the Flask server on port 3333.</p>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Home page requested at {timestamp}")
    return HTML

if __name__ == '__main__':
    print("Starting final test server on port 3333")
    print("Try accessing: http://localhost:3333/")
    app.run(host='0.0.0.0', port=3333, debug=True) 