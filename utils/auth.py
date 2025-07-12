#!/usr/bin/env python3
"""
وحدة المصادقة للترجمان الآلي
"""

import logging
from flask import session
from models import UserSession

logger = logging.getLogger(__name__)

def is_authenticated():
    """التحقق من مصادقة المستخدم"""
    return session.get('authenticated', False)

def is_authenticated_with_token():
    """التحقق من المصادقة باستخدام رمز الجلسة"""
    from flask import request, session
    
    # التحقف من الجلسة العادية أولاً
    if is_authenticated():
        return True
    
    # التحقف من رمز الجلسة من الترويسات
    token = request.headers.get('X-Session-Token')
    if token and ':' in token:
        # منطق التحقف من صحة الرمز هنا
        # يمكن تحسين هذا بإضافة تحقق أكثر أماناً
        return True
    
    return False

def get_user_language():
    """الحصول على لغة المستخدم الحالي"""
    # أولاً التحقف من تخزين الجلسة
    lang = session.get('user_language')
    if lang:
        return lang
    
    # ثم التحقف من جلسة المستخدم في قاعدة البيانات
    session_id = session.get('session_id')
    if session_id:
        user_session = UserSession.query.filter_by(session_id=session_id).first()
        if user_session:
            return user_session.language
    
    # استخدام الإعداد الافتراضي
    from utils.settings import get_setting
    return get_setting('default_language', 'en')

def get_user_theme():
    """الحصول على سمة واجهة المستخدم الحالية"""
    # أولاً التحقف من تخزين الجلسة
    theme = session.get('user_theme')
    if theme:
        return theme
    
    # ثم التحقف من جلسة المستخدم في قاعدة البيانات
    session_id = session.get('session_id')
    if session_id:
        user_session = UserSession.query.filter_by(session_id=session_id).first()
        if user_session:
            return user_session.theme
    
    # استخدام الإعداد الافتراضي
    from utils.settings import get_setting
    return get_setting('user_theme', 'system')

# Authentication utility functions

def require_auth(f):
    """Decorator to require authentication for routes"""
    from functools import wraps
    from flask import session, redirect, url_for
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Add login_required as an alias for require_auth for compatibility
login_required = require_auth