"""
Custom TradingView-based dashboard for the trading agents system.
Provides a modern, responsive UI with advanced charting capabilities.
"""
import os
from flask import Flask
from flask_cors import CORS


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    
    # Enable CORS for API endpoints
    CORS(app)
    
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        DATABASE=os.path.join(app.instance_path, "custom_dashboard.sqlite"),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register blueprints with the app
    from . import views
    app = views.init_app(app)  # Use the new init_app function that handles SocketIO
    
    # Register API routes
    from . import api
    app.register_blueprint(api.bp)
    
    return app 