#!/usr/bin/env python3
"""
Configurable Authentication Manager for AI Translator
مدير المصادقة القابل للتخصيص للمترجم الآلي
"""

import os
import time
import hashlib
import secrets
import json
from typing import Optional, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, request, redirect, url_for, flash
import logging

class AuthManager:
    """Configurable authentication system"""
    
    def __init__(self, app=None):
        self.app = app
        self.settings_cache = {}
        self.is_setup_complete = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize authentication with Flask app"""
        self.app = app
        
        # Check if setup is required
        self.check_setup_status()
    
    def check_setup_status(self) -> bool:
        """Check if initial setup is complete"""
        try:
            from models import Settings
            
            # Check if admin credentials exist
            admin_username = Settings.query.filter_by(key='admin_username').first()
            admin_password = Settings.query.filter_by(key='admin_password_hash').first()
            
            self.is_setup_complete = bool(admin_username and admin_password and admin_password.value)
            return self.is_setup_complete
            
        except Exception as e:
            logging.error(f"Error checking setup status: {e}")
            self.is_setup_complete = False
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get authentication setting with caching"""
        if key in self.settings_cache:
            return self.settings_cache[key]
        
        try:
            from models import Settings
            setting = Settings.query.filter_by(key=key).first()
            value = setting.value if setting else default
            self.settings_cache[key] = value
            return value
        except:
            return default
    
    def update_setting(self, key: str, value: str) -> bool:
        """Update authentication setting"""
        try:
            from models import Settings, db
            
            setting = Settings.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = Settings()
                setting.key = key
                setting.value = value
                setting.section = 'AUTH'
                setting.type = 'string'
                setting.description = '{"en": "Authentication Setting", "ar": "إعداد المصادقة"}'
                db.session.add(setting)
            
            db.session.commit()
            
            # Update cache
            self.settings_cache[key] = value
            
            return True
            
        except Exception as e:
            logging.error(f"Error updating setting {key}: {e}")
            return False
    
    def create_initial_admin(self, username: str, password: str) -> bool:
        """Create initial admin user"""
        try:
            # Generate password hash
            password_hash = generate_password_hash(password)
            
            # Save credentials
            success = (
                self.update_setting('admin_username', username) and
                self.update_setting('admin_password_hash', password_hash)
            )
            
            if success:
                self.is_setup_complete = True
                logging.info(f"Initial admin user created: {username}")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error creating initial admin: {e}")
            return False
    
    def validate_credentials(self, username: str, password: str) -> bool:
        """Validate user credentials"""
        try:
            stored_username = self.get_setting('admin_username')
            stored_password_hash = self.get_setting('admin_password_hash')
            
            if not stored_username or not stored_password_hash:
                return False
            
            # Check username
            if username != stored_username:
                return False
            
            # Check password
            return check_password_hash(stored_password_hash, password)
            
        except Exception as e:
            logging.error(f"Error validating credentials: {e}")
            return False
    
    def change_password(self, current_password: str, new_password: str) -> bool:
        """Change admin password"""
        try:
            username = self.get_setting('admin_username')
            
            # Validate current password
            if not self.validate_credentials(username, current_password):
                return False
            
            # Generate new password hash
            new_password_hash = generate_password_hash(new_password)
            
            # Update password
            return self.update_setting('admin_password_hash', new_password_hash)
            
        except Exception as e:
            logging.error(f"Error changing password: {e}")
            return False
    
    def change_username(self, new_username: str, password: str) -> bool:
        """Change admin username"""
        try:
            current_username = self.get_setting('admin_username')
            
            # Validate current password
            if not self.validate_credentials(current_username, password):
                return False
            
            # Update username
            return self.update_setting('admin_username', new_username)
            
        except Exception as e:
            logging.error(f"Error changing username: {e}")
            return False
    
    def login_user(self, username: str, password: str) -> bool:
        """Login user and create session"""
        if self.validate_credentials(username, password):
            session['authenticated'] = True
            session['username'] = username
            session['login_time'] = int(os.urandom(4).hex(), 16)  # Simple session token
            
            # Update last login
            self.update_setting('last_login', str(int(time.time())))
            
            return True
        
        return False
    
    def logout_user(self):
        """Logout user and clear session"""
        session.clear()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return session.get('authenticated', False)
    
    def get_current_user(self) -> Optional[str]:
        """Get current authenticated username"""
        if self.is_authenticated():
            return session.get('username')
        return None
    
    def require_auth(self, f):
        """Decorator for routes that require authentication"""
        def decorated_function(*args, **kwargs):
            if not self.is_setup_complete:
                return redirect(url_for('setup_page'))
            
            if not self.is_authenticated():
                flash('Please login to continue', 'error')
                return redirect(url_for('login'))
            
            return f(*args, **kwargs)
        
        decorated_function.__name__ = f.__name__
        return decorated_function
    
    def require_setup(self, f):
        """Decorator for setup route"""
        def decorated_function(*args, **kwargs):
            if self.is_setup_complete:
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        
        decorated_function.__name__ = f.__name__
        return decorated_function
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        return {
            'authenticated': self.is_authenticated(),
            'username': self.get_current_user(),
            'setup_complete': self.is_setup_complete,
            'session_timeout': self.get_setting('session_timeout', 3600),
            'login_time': session.get('login_time'),
            'last_activity': session.get('last_activity', 0)
        }
    
    def generate_secure_password(self, length: int = 12) -> str:
        """Generate secure password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def setup_default_settings(self):
        """Setup default authentication settings"""
        defaults = {
            'session_timeout': '3600',
            'enable_2fa': 'false',
            'max_login_attempts': '5',
            'lockout_duration': '300',
            'password_min_length': '8',
            'require_strong_password': 'true'
        }
        
        for key, value in defaults.items():
            if not self.get_setting(key):
                self.update_setting(key, value)

# Global auth manager instance
auth_manager = AuthManager()

def init_auth_manager(app):
    """Initialize authentication manager with app"""
    auth_manager.init_app(app)
    return auth_manager