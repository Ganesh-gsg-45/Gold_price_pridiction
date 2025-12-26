"""
Main Flask Application
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from config import config
from routes.api import api_bp
from supabase_client import authenticate_user, register_user

class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    # Use secure secret key from config
    app.secret_key = app.config.get('SECRET_KEY') or os.urandom(24)
    
    # Enable CORS
    CORS(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        # For simplicity, we'll store user info in session
        # In production, you might want to query the database
        return User(user_id, session.get('email'))
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Main route - requires login
    @app.route('/')
    @login_required
    def index():
        return render_template('index.html')
    
    # Calculator route - requires login
    @app.route('/calculator')
    @login_required
    def calculator():
        return render_template('calculator.html')
    
    # Login route
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            
            success, result = authenticate_user(email, password)
            if success:
                user = User(result['id'], email)
                login_user(user)
                session['email'] = email
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash(result, 'error')
        
        return render_template('login.html')
    
    # Register route
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            
            success, message = register_user(email, password)
            if success:
                flash(message, 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'error')
        
        return render_template('register.html')
    
    # Logout route
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        session.clear()
        flash('Logged out successfully!', 'success')
        return redirect(url_for('login'))

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500

    return app

if __name__ == '__main__':
    app = create_app('development')
    print("\n🚀 Gold Price Predictor Server")
    print("📍 http://localhost:5000")
    print("="*50 + "\n")
    app.run(host='127.0.0.1', port=5000, debug=True)
