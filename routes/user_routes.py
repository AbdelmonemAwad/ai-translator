#!/usr/bin/env python3
"""
مسارات API للمستخدم
"""

import logging
from flask import Blueprint, jsonify, request, session, redirect, url_for, render_template, flash
from utils.auth import is_authenticated, get_user_language, get_user_theme
from utils.settings import get_setting
from models import UserSession, db

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Handle language switching
    if 'lang' in request.args:
        session['language'] = request.args.get('lang')
        return redirect(url_for('user.login'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin_username = get_setting('admin_username', 'admin')
        admin_password = get_setting('admin_password', 'your_strong_password')
        
        if username == admin_username and password == admin_password:
            session['authenticated'] = True
            session['username'] = username
            logger.info(f"User logged in: {username}")
            return redirect(url_for('dashboard'))
        else:
            # Display error message in user's language
            if session.get('language', 'ar') == 'ar':
                flash('اسم المستخدم أو كلمة المرور غير صحيحة')
            else:
                flash('Invalid username or password')
            logger.warning(f"Failed login attempt: {username}")
    
    return render_template('login.html')

@user_bp.route('/logout')
def logout():
    username = session.get('username')
    session.clear()
    logger.info(f"User logged out: {username}")
    return redirect(url_for('user.login'))

@user_bp.route('/api/user/theme', methods=['POST'])
def api_user_theme():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    data = request.get_json() or {}
    theme = data.get('theme', 'system')
    
    # Update user session theme preference
    session_id = session.get('session_id')
    if session_id:
        user_session = UserSession.query.filter_by(session_id=session_id).first()
        if user_session:
            user_session.theme = theme
            db.session.commit()
    
    return jsonify({'success': True})

@user_bp.route('/api/user/language', methods=['POST'])
def api_user_language():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    data = request.get_json() or {}
    language = data.get('language', 'en')
    
    # Update session
    session['user_language'] = language
    
    # Update user session language preference in database
    session_id = session.get('session_id')
    if session_id:
        user_session = UserSession.query.filter_by(session_id=session_id).first()
        if user_session:
            user_session.language = language
            db.session.commit()
    
    return jsonify({'success': True})

@user_bp.route('/api/session-token')
def api_session_token():
    """Get session token for API authentication"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Generate or get session token
    session_id = session.get('session_id', 'authenticated')
    username = session.get('username', 'admin')
    
    return jsonify({
        'token': f"{session_id}:{username}",
        'authenticated': True,
        'username': username
    })

# Alternative authentication check using session token
@user_bp.route('/api/check-auth')
def api_check_auth():
    """Check if user is authenticated"""
    # Check regular session first
    if is_authenticated():
        return jsonify({'authenticated': True})
    
    # Check session token from headers
    token = request.headers.get('X-Session-Token')
    if token and ':' in token:
        # Validate token logic here
        return jsonify({'authenticated': True})
    
    return jsonify({'authenticated': False}), 401