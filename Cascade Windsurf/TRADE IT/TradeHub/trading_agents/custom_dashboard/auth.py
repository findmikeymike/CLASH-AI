import os
import json
import logging
from flask import Flask, redirect, url_for, session, request, jsonify, Blueprint
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# User class
class User(UserMixin):
    def __init__(self, id, name, email, profile_pic):
        self.id = id
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'profile_pic': self.profile_pic
        }

    @staticmethod
    def from_json(json_data):
        return User(
            id=json_data['id'],
            name=json_data['name'],
            email=json_data['email'],
            profile_pic=json_data['profile_pic']
        )

# User database (in-memory for now, can be replaced with a real DB)
users_db = {}

# Initialize auth components
auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()
oauth = OAuth()

def init_auth(app):
    """Initialize authentication for the application"""
    logger.info("Initializing authentication...")
    
    # Configure login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Configure OAuth
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )
    
    # Register the auth blueprint
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    logger.info("Authentication initialized successfully")
    return login_manager

@login_manager.user_loader
def load_user(user_id):
    """Load user from the database"""
    logger.info(f"Loading user: {user_id}")
    if user_id in users_db:
        return User.from_json(users_db[user_id])
    return None

# Routes for authentication
@auth_bp.route('/login')
def login():
    """Route for login page"""
    redirect_uri = url_for('auth.authorize', _external=True)
    logger.info(f"Login initiated, redirect URI: {redirect_uri}")
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/authorize')
def authorize():
    """Callback for OAuth authorization"""
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        
        logger.info(f"User authorized: {user_info.get('email')}")
        
        # Create or update user in our database
        user = User(
            id=user_info['sub'],
            name=user_info['name'],
            email=user_info['email'],
            profile_pic=user_info.get('picture', '')
        )
        
        users_db[user.id] = user.to_json()
        
        # Log the user in
        login_user(user)
        
        # Redirect to dashboard
        return redirect('/')
    except Exception as e:
        logger.error(f"Authorization error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/logout')
def logout():
    """Log out the current user"""
    logger.info(f"User logged out: {current_user.id if not current_user.is_anonymous else 'anonymous'}")
    logout_user()
    session.clear()
    return redirect('/')

@auth_bp.route('/user')
def get_user():
    """Get current user information"""
    if current_user.is_authenticated:
        logger.info(f"User info requested: {current_user.id}")
        return jsonify(current_user.to_json())
    logger.info("User info requested but no user is authenticated")
    return jsonify({"authenticated": False}), 401
