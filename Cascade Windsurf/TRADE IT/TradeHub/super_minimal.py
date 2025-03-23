from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Hello from Super Minimal Flask!</h1><p>If you can see this, everything is working correctly.</p>'

if __name__ == '__main__':
    print("Starting super minimal server on port 5555")
    print("Try accessing: http://localhost:5555/")
    app.run(host='0.0.0.0', port=5555) 