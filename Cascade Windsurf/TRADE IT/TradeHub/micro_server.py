#!/usr/bin/env python
"""
Micro Server

The absolutely simplest possible web server with no external dependencies.
Just uses the built-in HTTP server from Python's standard library.
"""
import http.server
import socketserver
import json
from datetime import datetime

# Port to run on - using a high port to avoid conflicts
PORT = 7070

# Handler for HTTP requests
class SimpleHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        # Home page
        if self.path == "/":
            self._set_headers("text/html")
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Micro Server</title>
                <style>
                    body { font-family: Arial; margin: 40px; }
                    h1 { color: #333; }
                    .card { border: 1px solid #ddd; padding: 20px; border-radius: 5px; }
                    pre { background: #f5f5f5; padding: 10px; }
                </style>
            </head>
            <body>
                <h1>Micro Server is running!</h1>
                <p>This is a minimal web server with zero external dependencies.</p>
                <div class="card">
                    <h2>Server Time</h2>
                    <p>%s</p>
                </div>
                <div class="card">
                    <h2>Available Endpoints</h2>
                    <ul>
                        <li><a href="/api/time">/api/time</a> - Current server time</li>
                        <li><a href="/api/symbols">/api/symbols</a> - List of stock symbols</li>
                    </ul>
                </div>
            </body>
            </html>
            """ % datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.wfile.write(html.encode("utf-8"))
        
        # API endpoint for time
        elif self.path == "/api/time":
            self._set_headers()
            response = {
                "server_time": datetime.now().isoformat(),
                "timestamp": datetime.now().timestamp()
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
        
        # API endpoint for symbols
        elif self.path == "/api/symbols":
            self._set_headers()
            symbols = [
                {"symbol": "AAPL", "name": "Apple Inc."},
                {"symbol": "MSFT", "name": "Microsoft Corporation"},
                {"symbol": "GOOGL", "name": "Alphabet Inc."},
                {"symbol": "AMZN", "name": "Amazon.com Inc."},
                {"symbol": "TSLA", "name": "Tesla, Inc."}
            ]
            self.wfile.write(json.dumps(symbols).encode("utf-8"))
        
        # 404 for anything else
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"error": "Not found", "path": self.path}
            self.wfile.write(json.dumps(response).encode("utf-8"))

# Print nice welcome message
print("\n" + "=" * 50)
print("  MICRO SERVER")
print("=" * 50)
print(f"  Starting server on port {PORT}")
print(f"  Open your browser to: http://localhost:{PORT}/")
print("=" * 50 + "\n")

# Start the server
with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
    print(f"Server running at http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server...")
        httpd.server_close()
        print("Server stopped.") 