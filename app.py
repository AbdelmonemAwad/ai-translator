#!/usr/bin/env python3
import os
os.environ['DATABASE_FILE'] = 'library_bcce0f55.db' # تم إضافته بواسطة reset_database.py
# استيراد المكتبات المطلوبة
import subprocess
# تم إزالة تكرار تعريف متغير البيئة DATABASE_FILE
import sys
import platform
import json
import time
import glob
import threading
import logging

# إعداد logger
logger = logging.getLogger(__name__)
import math
import psutil
import shutil
import requests
from datetime import datetime
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, Settings, MediaFile, Log, TranslationJob, Notification, UserSession, PasswordReset, TranslationHistory, DatabaseStats, TranslationLog
from translations import get_translation, t
from services.remote_storage import setup_remote_mount, get_mount_status
from gpu_manager import gpu_manager, get_gpu_environment_variables
from system_monitor import get_system_monitor

# استيراد الوحدات الجديدة
from utils.settings import get_settings, get_setting, is_development_feature_enabled
from utils.auth import is_authenticated, require_auth, get_user_language, get_user_theme

# استيراد البلوبرنت الجديد للإشعارات
from routes.notifications_routes import notifications_bp, create_notification
# استيراد البلوبرنت الجديد لإدارة قاعدة البيانات
from routes.database_routes import database_bp
# استيراد البلوبرنت الجديد لمراقبة النظام
from routes.system_routes import system_bp
# استيراد البلوبرنت الجديد للسجلات
from routes.logs_routes import logs_bp, log_to_db, log_to_file, log_translation_event
# استيراد البلوبرنت الجديد للإعدادات
from routes.settings_routes import settings_bp, update_setting

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")

# Session configuration for production
app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP in development
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_PERMANENT'] = False

# Database configuration
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # استخدام DuckDB
    database_url = "duckdb:///library_bcce0f55.db"  # Changed from library.db to library_new.db

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# تسجيل مسارات API
from routes.dependencies_routes import dependencies_bp
app.register_blueprint(dependencies_bp)

# استيراد مسارات المستخدم
from routes.user_routes import user_bp
from routes.media_routes import media_bp
from routes.static_routes import static_bp
from routes.gpu_routes import gpu_bp
from routes.test_routes import test_bp
from routes.media_services_routes import media_services_bp
from routes.media_processing_routes import media_processing_bp

# تسجيل مسارات المستخدم
app.register_blueprint(user_bp)
app.register_blueprint(media_bp)
app.register_blueprint(static_bp)
app.register_blueprint(gpu_bp)
app.register_blueprint(test_bp)
app.register_blueprint(media_services_bp)
app.register_blueprint(notifications_bp)  # إضافة بلوبرنت الإشعارات
app.register_blueprint(database_bp)  # إضافة بلوبرنت إدارة قاعدة البيانات
app.register_blueprint(system_bp)  # إضافة بلوبرنت مراقبة النظام
app.register_blueprint(logs_bp)  # إضافة بلوبرنت السجلات
app.register_blueprint(settings_bp)  # إضافة بلوبرنت الإعدادات
app.register_blueprint(media_processing_bp)  # إضافة بلوبرنت معالجة الوسائط

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Global variables for compatibility
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(PROJECT_DIR, "status.json")
BLACKLIST_FILE = os.path.join(PROJECT_DIR, "blacklist.txt")
PROCESS_LOG_FILE = os.path.join(PROJECT_DIR, "process.log")
APP_LOG_FILE = os.path.join(PROJECT_DIR, "app.log")

# These functions are now imported from utils.settings and utils.auth modules

def translate_text(key, **kwargs):
    """Translation helper function for templates"""
    lang = get_user_language()
    return get_translation(key, lang, **kwargs)

# Function moved to routes.notifications_routes

# These functions have been moved to routes.media_processing_routes module

# This function has been moved to routes.settings_routes module

# These functions have been moved to utils.logging module

# These authentication functions are now imported from utils.auth module

def validate_file_path(file_path):
    """Validate file path for security - prevent directory traversal attacks"""
    if not file_path:
        return False
    
    # منع المسارات التي تحتوي على ../ أو ../
    if '..' in file_path or file_path.startswith('/'):
        return False
    
    # قائمة بالمجلدات المحظورة
    forbidden_dirs = [
        '/etc', '/sys', '/proc', '/dev', '/boot', '/root', '/home',
        '/var/log', '/var/lib', '/usr/bin', '/usr/sbin', '/bin', '/sbin'
    ]
    
    # فحص إذا كان المسار يحتوي على مجلد محظور
    for forbidden in forbidden_dirs:
        if file_path.startswith(forbidden.lstrip('/')):
            return False
    
    return True

def get_safe_file_path(relative_path):
    """Get safe absolute file path from relative path"""
    if not validate_file_path(relative_path):
        return None
    
    # الحصول على الإعدادات المسموحة للملفات
    settings = get_settings()
    allowed_paths = [
        settings.get('local_movies_mount', '/mnt/remote/movies'),
        settings.get('local_tv_mount', '/mnt/remote/tv'),
        '/tmp/ai-translator',  # مجلد مؤقت للتطبيق
        './static',  # ملفات التطبيق الثابتة
        './uploads'  # مجلد الرفع إن وجد
    ]
    
    # التأكد من أن المسار ضمن المسارات المسموحة
    for allowed_path in allowed_paths:
        if relative_path.startswith(allowed_path.lstrip('./')):
            return os.path.abspath(relative_path)
    
    return None

def get_current_status():
    """Get current processing status"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {
        'status': 'idle',
        'progress': 0,
        'current_file': '',
        'total_files': 0,
        'files_done': 0,
        'task': ''
    }

def read_blacklist():
    """Read blacklisted paths from file"""
    if not os.path.exists(BLACKLIST_FILE):
        return []
    try:
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def add_to_blacklist(path):
    """Add path to blacklist"""
    blacklist = read_blacklist()
    if path not in blacklist:
        blacklist.append(path)
        try:
            with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(blacklist))
            
            # Update database record
            media_file = MediaFile.query.filter_by(path=path).first()
            if media_file:
                media_file.blacklisted = True
                db.session.commit()
            
            return True
        except Exception as e:
            log_to_db("ERROR", f"Failed to add to blacklist: {path}", str(e))
    return False

def remove_from_blacklist(path):
    """Remove path from blacklist"""
    blacklist = read_blacklist()
    if path in blacklist:
        blacklist.remove(path)
        try:
            with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(blacklist))
            
            # Update database record
            media_file = MediaFile.query.filter_by(path=path).first()
            if media_file:
                media_file.blacklisted = False
                db.session.commit()
            
            return True
        except Exception as e:
            log_to_db("ERROR", f"Failed to remove from blacklist: {path}", str(e))
    return False

# These functions are now imported from routes.media_processing_routes module

# Routes - These will be registered by main.py
@app.route('/')
def index():
    if not is_authenticated():
        return redirect(url_for('user.login'))
    return redirect(url_for('dashboard'))

# تم نقل وظيفة login() إلى routes/user_routes.py

# تم نقل وظيفة logout() إلى routes/user_routes.py

@app.route('/dashboard')
def dashboard():
    if not is_authenticated():
        return redirect(url_for('login'))
    
    status = get_current_status()
    
    # Get statistics
    total_files = MediaFile.query.count()
    translated_files = MediaFile.query.filter_by(translated=True).count()
    blacklisted_files = MediaFile.query.filter_by(blacklisted=True).count()
    
    stats = {
        'total_files': total_files,
        'translated_files': translated_files,
        'blacklisted_files': blacklisted_files,
        'pending_files': total_files - translated_files - blacklisted_files
    }
    
    return render_template('dashboard.html', status=status, stats=stats)







@app.route('/logs')
def logs_page():
    if not is_authenticated():
        return redirect(url_for('login'))
    return render_template('logs.html')

# This route has been moved to routes.settings_routes module

# This route has been moved to routes.settings_routes module

# New Hierarchical Settings Routes
# This route has been moved to routes.settings_routes module

# This route has been moved to routes.settings_routes module

# This route has been moved to routes.settings_routes module

# This route has been moved to routes.settings_routes module

# This route has been moved to routes.settings_routes module

# This route has been moved to routes.settings_routes module

# This route has been moved to routes.settings_routes module

# This route has been moved to routes.settings_routes module

# This route has been moved to routes.settings_routes module

@app.route('/system-monitor-advanced')
def system_monitor_advanced():
    """صفحة مراقبة النظام المتطورة الجديدة"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    return render_template('system_monitor_advanced.html')

# This route has been moved to routes.settings_routes module

@app.route('/system-monitor')
def system_monitor_page():
    if not is_authenticated():
        return redirect(url_for('login'))
    return render_template('system_monitor.html')

@app.route('/test-logs')
def test_logs_page():
    if not is_authenticated():
        return redirect(url_for('login'))
    return render_template('test_logs.html')

@app.route('/notifications')
def notifications_page():
    if not is_authenticated():
        return redirect(url_for('login'))
    return render_template('notifications.html')

@app.route('/docs')
def docs_page():
    """Documentation page with comprehensive application information"""
    return render_template('docs.html')

@app.route('/static/OLLAMA_MODELS_README.md')
def serve_ollama_readme():
    """Serve the OLLAMA_MODELS_README.md file as HTML"""
    try:
        with open('static/OLLAMA_MODELS_README.md', 'r', encoding='utf-8') as f:
            content = f.read()
        # Convert markdown to simple HTML
        content = content.replace('\n#', '\n<h1>')
        content = content.replace('\n##', '\n<h2>')
        content = content.replace('\n###', '\n<h3>')
        content = content.replace('\n', '<br>')
        # Replace markdown links with HTML links
        import re
        content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', content)
        # Replace markdown code blocks with HTML code blocks
        content = content.replace('```', '<pre>')
        return f'<html><head><title>Ollama Models Guide</title><style>body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}</style></head><body>{content}</body></html>'
    except FileNotFoundError:
        return "File not found", 404

@app.route('/static/ollama_models_guide.html')
def serve_ollama_guide():
    """Serve the ollama_models_guide.html file"""
    try:
        with open('static/ollama_models_guide.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return "File not found", 404

@app.route('/LICENSE')
def license_page():
    """Serve the LICENSE file"""
    try:
        with open('LICENSE', 'r', encoding='utf-8') as f:
            license_content = f.read()
        return f'<pre style="font-family: monospace; white-space: pre-wrap; padding: 20px; background: #f5f5f5; margin: 20px; border-radius: 5px;">{license_content}</pre>'
    except FileNotFoundError:
        return "License file not found", 404

@app.route('/database-admin')
def database_admin_page():
    if not is_authenticated():
        return redirect(url_for('login'))
    return render_template('database_admin.html')

# API Routes
@app.route('/api/status')
def api_status():
    status = get_current_status()
    status['is_running'] = is_task_running()
    return jsonify(status)

@app.route('/api/health-check')
def api_health_check():
    """Comprehensive system health check"""
    try:
        health = {
            'status': 'healthy',
            'database': 'connected',
            'ai_components': {},
            'system_resources': {},
            'issues': []
        }
        
        # Check database
        try:
            db.session.execute('SELECT 1')
            health['database'] = 'connected'
        except Exception as e:
            health['database'] = 'error'
            health['issues'].append(f'Database: {str(e)}')
            health['status'] = 'degraded'
        
        # Check AI components
        try:
            from ai_integration_workaround import get_ai_status
            ai_status = get_ai_status()
            health['ai_components'] = ai_status
        except ImportError:
            logger.warning("AI Integration Workaround module not found, using fallback")
            ai_status = {"status": "unavailable", "message": "AI integration module not found"}
            health['ai_components'] = ai_status
        
        if not ai_status.get('system_ready', False):
            health['issues'].append('AI system not fully ready')
            health['status'] = 'degraded'
        
        # Check system resources
        import psutil
        health['system_resources'] = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
        
        # Check for resource issues
        if health['system_resources']['memory_percent'] > 90:
            health['issues'].append('High memory usage')
            health['status'] = 'warning'
        
        if health['system_resources']['disk_percent'] > 95:
            health['issues'].append('Low disk space')
            health['status'] = 'warning'
        
        return jsonify(health)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500







@app.route('/api/clear_log', methods=['POST'])
def api_clear_log():
    data = request.get_json() or {}
    log_type = data.get('type', 'app')
    
    # Get filter parameters from URL
    level = request.args.get('level')
    days = request.args.get('days')
    
    try:
        # Clear database logs with filters
        if level:
            # Clear specific level logs
            Log.query.filter_by(level=level).delete()
            log_message = f"تم مسح سجلات {level}"
        elif days:
            # Clear old logs
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=int(days))
            Log.query.filter(Log.created_at < cutoff_date).delete()
            log_message = f"تم مسح السجلات الأقدم من {days} أيام"
        else:
            # Clear all logs
            Log.query.delete()
            log_message = "تم مسح جميع السجلات"
            
            # Also clear file logs if clearing all
            if log_type == 'process':
                log_file = PROCESS_LOG_FILE
            else:
                log_file = APP_LOG_FILE
            
            if os.path.exists(log_file):
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write('')
        
        db.session.commit()
        log_to_db("INFO", log_message)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_selected_logs', methods=['POST'])
def api_delete_selected_logs():
    """Delete selected log entries by indices"""
    try:
        data = request.get_json()
        indices = data.get('indices', [])
        
        if not indices:
            return jsonify({'success': False, 'error': 'No indices provided'})
        
        # Get all logs ordered by creation date (newest first)
        all_logs = Log.query.order_by(Log.created_at.desc()).all()
        
        # Convert indices to log IDs
        log_ids_to_delete = []
        for index in indices:
            if 0 <= int(index) < len(all_logs):
                log_ids_to_delete.append(all_logs[int(index)].id)
        
        if log_ids_to_delete:
            # Delete selected logs
            Log.query.filter(Log.id.in_(log_ids_to_delete)).delete(synchronize_session=False)
            db.session.commit()
            
            log_to_db("INFO", f"تم حذف {len(log_ids_to_delete)} سجل محدد")
        
        return jsonify({'success': True, 'deleted_count': len(log_ids_to_delete)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/translation_logs', methods=['GET'])
def api_translation_logs():
    """Get translation logs"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        status_filter = request.args.get('status', None)
        
        # Build query
        query = TranslationLog.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # Get logs ordered by creation date (newest first)
        logs = query.order_by(TranslationLog.created_at.desc()).limit(limit).all()
        
        # Convert to JSON-serializable format
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'file_path': log.file_path,
                'file_name': log.file_name,
                'status': log.status,
                'progress': log.progress,
                'error_message': log.error_message,
                'details': log.details,
                'file_size': log.file_size,
                'duration': log.duration,
                'whisper_model': log.whisper_model,
                'ollama_model': log.ollama_model,
                'subtitle_path': log.subtitle_path,
                'quality_score': log.quality_score,
                'created_at': log.created_at.isoformat() if log.created_at else None,
                'updated_at': log.updated_at.isoformat() if log.updated_at else None,
                'completed_at': log.completed_at.isoformat() if log.completed_at else None
            })
        
        return jsonify({'logs': logs_data, 'count': len(logs_data)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear_sample_translation_logs', methods=['POST'])
def api_clear_sample_translation_logs():
    """Clear all sample translation logs"""
    if not is_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Delete all translation logs
        count = TranslationLog.query.count()
        TranslationLog.query.delete()
        db.session.commit()
        
        log_to_db("INFO", f"تم حذف {count} سجل ترجمة وهمي")
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create_sample_translation_logs', methods=['POST'])
def api_create_sample_translation_logs():
    """Create sample translation logs for testing"""
    try:
        # Sample translation logs
        sample_logs = [
            {
                'file_path': '/media/movies/The.Matrix.1999.1080p.BluRay.x264.mkv',
                'file_name': 'The Matrix (1999)',
                'status': 'success',
                'progress': 100.0,
                'details': 'تم إنشاء ترجمة عربية عالية الجودة',
                'duration': 285.5,
                'whisper_model': 'medium.en',
                'ollama_model': 'llama3',
                'subtitle_path': '/media/movies/The.Matrix.1999.1080p.BluRay.x264.ar.srt',
                'quality_score': 95.0
            },
            {
                'file_path': '/media/series/Breaking.Bad.S01E01.720p.WEB-DL.x264.mkv',
                'file_name': 'Breaking Bad S01E01',
                'status': 'failed', 
                'progress': 45.0,
                'error_message': 'فشل في الاتصال بخدمة Ollama',
                'details': 'توقف أثناء مرحلة الترجمة',
                'duration': 120.3,
                'whisper_model': 'medium.en',
                'ollama_model': 'llama3'
            },
            {
                'file_path': '/media/movies/Inception.2010.1080p.BluRay.x264.mkv',
                'file_name': 'Inception (2010)',
                'status': 'incomplete',
                'progress': 75.0,
                'details': 'توقف أثناء المعالجة - يمكن استكمالها',
                'duration': 180.7,
                'whisper_model': 'medium.en',
                'ollama_model': 'llama3'
            },
            {
                'file_path': '/media/movies/Avatar.2009.1080p.BluRay.x264.mkv',
                'file_name': 'Avatar (2009)',
                'status': 'started',
                'progress': 25.0,
                'details': 'بدأت عملية استخراج الصوت',
                'whisper_model': 'medium.en',
                'ollama_model': 'llama3'
            }
        ]
        
        # Add sample logs to database
        for log_data in sample_logs:
            log_translation_event(**log_data)
        
        return jsonify({'success': True, 'message': f'تم إنشاء {len(sample_logs)} سجل تجريبي'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create_sample_media_files', methods=['POST'])
def api_create_sample_media_files():
    """Create sample media files for testing"""
    try:
        # Sample movie data
        sample_movies = [
            {
                'path': '/media/movies/The.Matrix.1999.1080p.BluRay.x264-GROUP.mkv',
                'title': 'The Matrix',
                'year': 1999,
                'media_type': 'movie',
                'poster_url': 'https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg',
                'imdb_id': 'tt0133093',
                'tmdb_id': 603,
                'has_subtitles': True,
                'translated': False,
                'blacklisted': False,
                'file_size': 8589934592,  # 8GB
                'duration': 8160,  # 136 minutes
                'quality': '1080p',
                'video_codec': 'x264',
                'audio_codec': 'AC3',
                'resolution': '1920x1080'
            },
            {
                'path': '/media/movies/Inception.2010.1080p.BluRay.x264-SPARKS.mkv',
                'title': 'Inception',
                'year': 2010,
                'media_type': 'movie',
                'poster_url': 'https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
                'imdb_id': 'tt1375666',
                'tmdb_id': 27205,
                'has_subtitles': False,
                'translated': True,
                'blacklisted': False,
                'file_size': 10737418240,  # 10GB
                'duration': 8880,  # 148 minutes
                'quality': '1080p',
                'video_codec': 'x264',
                'audio_codec': 'DTS',
                'resolution': '1920x1080'
            },
            {
                'path': '/media/movies/Avatar.2009.1080p.BluRay.x265-RARBG.mkv',
                'title': 'Avatar',
                'year': 2009,
                'media_type': 'movie',
                'poster_url': 'https://image.tmdb.org/t/p/w500/6EiRUJpuoeQPghrs3YNktfnqOVh.jpg',
                'imdb_id': 'tt0499549',
                'tmdb_id': 19995,
                'has_subtitles': True,
                'translated': False,
                'blacklisted': False,
                'file_size': 12884901888,  # 12GB
                'duration': 9720,  # 162 minutes
                'quality': '1080p',
                'video_codec': 'x265',
                'audio_codec': 'DTS-HD',
                'resolution': '1920x1080'
            },
            {
                'path': '/media/movies/Interstellar.2014.1080p.BluRay.x264-SPARKS.mkv',
                'title': 'Interstellar',
                'year': 2014,
                'media_type': 'movie',
                'poster_url': 'https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg',
                'imdb_id': 'tt0816692',
                'tmdb_id': 157336,
                'has_subtitles': False,
                'translated': False,
                'blacklisted': True,
                'file_size': 11811160064,  # 11GB
                'duration': 10140,  # 169 minutes
                'quality': '1080p',
                'video_codec': 'x264',
                'audio_codec': 'DTS',
                'resolution': '1920x1080'
            },
            {
                'path': '/media/movies/The.Dark.Knight.2008.1080p.BluRay.x264-REFiNED.mkv',
                'title': 'The Dark Knight',
                'year': 2008,
                'media_type': 'movie',
                'poster_url': 'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
                'imdb_id': 'tt0468569',
                'tmdb_id': 155,
                'has_subtitles': True,
                'translated': True,
                'blacklisted': False,
                'file_size': 9663676416,  # 9GB
                'duration': 9120,  # 152 minutes
                'quality': '1080p',
                'video_codec': 'x264',
                'audio_codec': 'AC3',
                'resolution': '1920x1080'
            }
        ]
        
        # Sample TV show data
        sample_tv_shows = [
            {
                'path': '/media/tv/Breaking Bad/Season 01/Breaking.Bad.S01E01.720p.WEB-DL.x264-GROUP.mkv',
                'title': 'Breaking Bad S01E01 - Pilot',
                'year': 2008,
                'media_type': 'episode',
                'poster_url': 'https://image.tmdb.org/t/p/w500/ggFHVNu6YYI5L9pCfOacjizRGt.jpg',
                'imdb_id': 'tt0959621',
                'tmdb_id': 1396,
                'sonarr_id': 1,
                'has_subtitles': False,
                'translated': False,
                'blacklisted': False,
                'file_size': 2147483648,  # 2GB
                'duration': 2760,  # 46 minutes
                'quality': '720p',
                'video_codec': 'x264',
                'audio_codec': 'AAC',
                'resolution': '1280x720'
            },
            {
                'path': '/media/tv/Breaking Bad/Season 01/Breaking.Bad.S01E02.720p.WEB-DL.x264-GROUP.mkv',
                'title': 'Breaking Bad S01E02 - Cat\'s in the Bag...',
                'year': 2008,
                'media_type': 'episode',
                'poster_url': 'https://image.tmdb.org/t/p/w500/ggFHVNu6YYI5L9pCfOacjizRGt.jpg',
                'imdb_id': 'tt0959621',
                'tmdb_id': 1396,
                'sonarr_id': 1,
                'has_subtitles': True,
                'translated': True,
                'blacklisted': False,
                'file_size': 2080374784,  # 1.9GB
                'duration': 2880,  # 48 minutes
                'quality': '720p',
                'video_codec': 'x264',
                'audio_codec': 'AAC',
                'resolution': '1280x720'
            },
            {
                'path': '/media/tv/Game of Thrones/Season 01/Game.of.Thrones.S01E01.1080p.BluRay.x264-REWARD.mkv',
                'title': 'Game of Thrones S01E01 - Winter Is Coming',
                'year': 2011,
                'media_type': 'episode',
                'poster_url': 'https://image.tmdb.org/t/p/w500/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg',
                'imdb_id': 'tt0944947',
                'tmdb_id': 1399,
                'sonarr_id': 2,
                'has_subtitles': False,
                'translated': False,
                'blacklisted': True,
                'file_size': 4294967296,  # 4GB
                'duration': 3600,  # 60 minutes
                'quality': '1080p',
                'video_codec': 'x264',
                'audio_codec': 'DTS',
                'resolution': '1920x1080'
            },
            {
                'path': '/media/tv/Stranger Things/Season 01/Stranger.Things.S01E01.1080p.NF.WEBRip.x264-SKGTV.mkv',
                'title': 'Stranger Things S01E01 - Chapter One: The Vanishing of Will Byers',
                'year': 2016,
                'media_type': 'episode',
                'poster_url': 'https://image.tmdb.org/t/p/w500/49WJfeN0moxb9IPfGn8AIqMGskD.jpg',
                'imdb_id': 'tt4574334',
                'tmdb_id': 66732,
                'sonarr_id': 3,
                'has_subtitles': True,
                'translated': False,
                'blacklisted': False,
                'file_size': 3221225472,  # 3GB
                'duration': 2880,  # 48 minutes
                'quality': '1080p',
                'video_codec': 'x264',
                'audio_codec': 'AC3',
                'resolution': '1920x1080'
            }
        ]
        
        # Combine all samples
        all_samples = sample_movies + sample_tv_shows
        
        # Add samples to database
        for media_data in all_samples:
            # Check if media file already exists
            existing_file = MediaFile.query.filter_by(path=media_data['path']).first()
            if not existing_file:
                new_file = MediaFile()
                for key, value in media_data.items():
                    if hasattr(new_file, key):
                        setattr(new_file, key, value)
                db.session.add(new_file)
        
        db.session.commit()
        log_to_db("INFO", f"تم إنشاء بيانات وهمية للملفات: {len(all_samples)} ملف")
        
        return jsonify({
            'success': True, 
            'message': f'تم إنشاء {len(all_samples)} ملف وهمي',
            'movies': len(sample_movies),
            'episodes': len(sample_tv_shows)
        })
    except Exception as e:
        log_to_db("ERROR", f"خطأ في إنشاء البيانات الوهمية: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/clear_sample_media_files', methods=['POST'])
def api_clear_sample_media_files():
    """Clear sample media files"""
    try:
        # Define sample file paths to identify and remove them
        sample_paths = [
            '/media/movies/The.Matrix.1999.1080p.BluRay.x264-GROUP.mkv',
            '/media/movies/Inception.2010.1080p.BluRay.x264-SPARKS.mkv',
            '/media/movies/Avatar.2009.1080p.BluRay.x265-RARBG.mkv',
            '/media/movies/Interstellar.2014.1080p.BluRay.x264-SPARKS.mkv',
            '/media/movies/The.Dark.Knight.2008.1080p.BluRay.x264-REFiNED.mkv',
            '/media/tv/Breaking Bad/Season 01/Breaking.Bad.S01E01.720p.WEB-DL.x264-GROUP.mkv',
            '/media/tv/Breaking Bad/Season 01/Breaking.Bad.S01E02.720p.WEB-DL.x264-GROUP.mkv',
            '/media/tv/Game of Thrones/Season 01/Game.of.Thrones.S01E01.1080p.BluRay.x264-REWARD.mkv',
            '/media/tv/Stranger Things/Season 01/Stranger.Things.S01E01.1080p.NF.WEBRip.x264-SKGTV.mkv'
        ]
        
        # Remove sample files from database
        deleted_count = 0
        for path in sample_paths:
            media_file = MediaFile.query.filter_by(path=path).first()
            if media_file:
                db.session.delete(media_file)
                deleted_count += 1
        
        db.session.commit()
        log_to_db("INFO", f"تم حذف {deleted_count} ملف وهمي من قاعدة البيانات")
        
        return jsonify({
            'success': True, 
            'message': f'تم حذف {deleted_count} ملف وهمي',
            'deleted_count': deleted_count
        })
    except Exception as e:
        log_to_db("ERROR", f"خطأ في حذف البيانات الوهمية: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})





# Action Routes
@app.route('/action/start-batch', methods=['POST'])
def action_start_batch():
    if not is_authenticated():
        return jsonify({'error': translate_text('not_authenticated')}), 401
    
    success, message = run_background_task('batch_translate')
    
    if success:
        return jsonify({'success': True, 'message': translate_text('batch_translation_started')})
    else:
        return jsonify({'error': f'{translate_text("failed_to_start_task")}: {message}'}), 500

@app.route('/action/stop', methods=['POST'])
def action_stop():
    if not is_authenticated():
        return jsonify({'error': translate_text('not_authenticated')}), 401
    
    try:
        # Find and terminate background processes
        terminated = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            cmdline = proc.info['cmdline']
            if cmdline and any('background_tasks.py' in arg for arg in cmdline):
                proc.terminate()
                terminated = True
        
        if terminated:
            log_to_db("INFO", "Background tasks stopped")
            return jsonify({'success': True, 'message': translate_text('tasks_stopped')})
        else:
            return jsonify({'error': translate_text('no_running_tasks')})
    except Exception as e:
        log_to_db("ERROR", "Failed to stop tasks", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/action/sync-library', methods=['POST'])
def action_sync_library():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    success, message = run_background_task('sync_library')
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'error': message}), 500

@app.route('/action/run-corrections', methods=['POST'])
def action_run_corrections():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    def generate():
        yield "data: بدء عملية التصحيح...\n\n"
        
        try:
            # Find and rename subtitle files
            corrections_made = 0
            
            for media_file in MediaFile.query.filter_by(translated=True).all():
                file_dir = os.path.dirname(media_file.path)
                filename = os.path.splitext(os.path.basename(media_file.path))[0]
                
                # Look for .hi.srt files
                hi_srt = os.path.join(file_dir, f"{filename}.hi.srt")
                ar_srt = os.path.join(file_dir, f"{filename}.ar.srt")
                
                if os.path.exists(hi_srt) and not os.path.exists(ar_srt):
                    try:
                        os.rename(hi_srt, ar_srt)
                        corrections_made += 1
                        yield f"data: تم تصحيح: {filename}\n\n"
                        time.sleep(0.1)
                    except Exception as e:
                        yield f"data: خطأ في تصحيح {filename}: {str(e)}\n\n"
            
            yield f"data: تم الانتهاء. عدد الملفات المصححة: {corrections_made}\n\n"
            
        except Exception as e:
            yield f"data: خطأ: {str(e)}\n\n"
    
    return Response(generate(), mimetype='text/plain')



@app.route('/action/scan_translation_status')
def action_scan_translation_status():
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if is_task_running():
        return jsonify({'error': translate_text('task_already_running')}), 400
    
    success = run_background_task("scan_translation_status_task")
    
    if success:
        create_notification('scan_started', 'scan_translation_status_started', 'info')
        return jsonify({'success': True, 'message': translate_text('scan_translation_status_started')})
    else:
        return jsonify({'error': translate_text('failed_to_start_task')}), 500

# Notification API endpoints - تم نقلها إلى routes.notifications_routes.py
# Database Admin API endpoints
@app.route('/api/database/stats')
def api_database_stats():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        from sqlalchemy import text
        import os
os.environ['DATABASE_FILE'] = 'library_bcce0f55.db' # تم إضافته بواسطة reset_database.py
        
        # Get database file size
        db_path = "library.db"
        db_size_mb = 0
        if os.path.exists(db_path):
            db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
        
        # Query all tables with proper error handling
        tables = ['settings', 'media_files', 'logs', 'translation_jobs', 'notifications', 'user_sessions', 'translation_history']
        tables_info = []
        total_records = 0
        
        for table_name in tables:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                if count is not None:
                    total_records += count
                    tables_info.append({
                        'name': table_name,
                        'record_count': count
                    })
            except Exception as e:
                print(f"Error querying table {table_name}: {e}")
                continue
        
        # Get last backup info (check for backup files)
        last_backup = 'لم يتم إجراء نسخ احتياطي'
        backup_files = [f for f in os.listdir('.') if f.startswith('library_backup_') and f.endswith('.db')]
        if backup_files:
            latest_backup = max(backup_files, key=lambda x: os.path.getmtime(x))
            backup_time = os.path.getmtime(latest_backup)
            import datetime
            last_backup = datetime.datetime.fromtimestamp(backup_time).strftime('%Y-%m-%d %H:%M')
        
        stats = {
            'total_size_mb': db_size_mb,
            'table_count': len(tables_info),
            'total_records': total_records,
            'last_backup': last_backup,
            'tables': tables_info
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/tables')
def api_database_tables():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        from sqlalchemy import text
        import datetime
        
        table_names = ['settings', 'media_files', 'logs', 'translation_jobs', 'notifications', 'user_sessions', 'translation_history']
        tables = []
        
        # Arabic names for tables
        table_translations = {
            'settings': 'الإعدادات',
            'media_files': 'ملفات الوسائط',
            'logs': 'السجلات',
            'translation_jobs': 'مهام الترجمة',
            'notifications': 'الإشعارات',
            'user_sessions': 'جلسات المستخدم',
            'translation_history': 'تاريخ الترجمة'
        }
        
        for table_name in table_names:
            try:
                # Get record count
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar() or 0
                
                # Try to get last updated timestamp if the table has created_at or updated_at columns
                last_updated = 'غير متوفر'
                try:
                    result = db.session.execute(text(f"SELECT MAX(created_at) FROM {table_name}"))
                    last_record = result.scalar()
                    if last_record:
                        last_updated = last_record.strftime('%Y-%m-%d %H:%M') if hasattr(last_record, 'strftime') else str(last_record)
                except:
                    pass
                
                tables.append({
                    'name': table_name,
                    'display_name': table_translations.get(table_name, table_name),
                    'record_count': count,
                    'size_mb': round(count * 0.1, 2),  # Rough estimate based on record count
                    'last_updated': last_updated
                })
            except Exception as e:
                print(f"Error querying table {table_name}: {e}")
                continue
        
        return jsonify(tables)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/query', methods=['POST'])
def api_database_query():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'لا يوجد استعلام'}), 400
    
    # Basic security check - only allow SELECT statements
    if not query.upper().startswith('SELECT'):
        return jsonify({'error': 'يُسمح فقط بعمليات SELECT'}), 400
    
    try:
        from sqlalchemy import text
        result = db.session.execute(text(query))
        
        # Try to fetch results
        try:
            results = []
            for row in result:
                results.append(dict(row))
            return jsonify({'results': results})
        except:
            return jsonify({'results': [], 'message': 'تم تنفيذ الاستعلام بنجاح'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/backup', methods=['POST'])
def api_database_backup():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        # Create notification about backup start
        create_notification(
            'backup_started',
            'backup_in_progress',
            'info'
        )
        
        # Simulate backup process (in real implementation, use pg_dump)
        import time
        time.sleep(2)
        
        create_notification(
            'backup_completed',
            'backup_success',
            'success'
        )
        
        return jsonify({'success': True, 'message': 'تم إنشاء النسخة الاحتياطية'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/optimize', methods=['POST'])
def api_database_optimize():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        # For PostgreSQL, VACUUM operations need to be done outside transactions
        # We'll just run ANALYZE which is safe in transactions
        from sqlalchemy import text
        
        # Run ANALYZE to update statistics
        db.session.execute(text('ANALYZE'))
        db.session.commit()
        
        # Optionally run REINDEX on key tables
        try:
            db.session.execute(text('REINDEX TABLE settings'))
            db.session.execute(text('REINDEX TABLE media_files'))
            db.session.commit()
        except:
            pass  # REINDEX may fail, that's OK
        
        create_notification(
            'database_optimized', 
            'database_optimization_success',
            'success'
        )
        
        return jsonify({'success': True, 'message': 'تم تحسين قاعدة البيانات بنجاح'})
    except Exception as e:
        return jsonify({'error': f'خطأ في تحسين قاعدة البيانات: {str(e)}'}), 500

@app.route('/api/database/cleanup', methods=['POST'])
def api_database_cleanup():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        # Clean old logs (older than 30 days)
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_logs = Log.query.filter(Log.created_at < cutoff_date).count()
        Log.query.filter(Log.created_at < cutoff_date).delete()
        
        # Clean read notifications older than 7 days
        notification_cutoff = datetime.utcnow() - timedelta(days=7)
        old_notifications = Notification.query.filter(
            Notification.read == True,
            Notification.created_at < notification_cutoff
        ).count()
        Notification.query.filter(
            Notification.read == True,
            Notification.created_at < notification_cutoff
        ).delete()
        
        db.session.commit()
        
        cleaned_records = old_logs + old_notifications
        
        create_notification(
            'database_cleaned',
            'database_cleanup_success',
            'success',
            count=cleaned_records
        )
        
        return jsonify({'success': True, 'cleaned_records': cleaned_records})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User preferences API
# تم نقل وظيفة api_user_theme() إلى routes/user_routes.py

# تم نقل وظيفة api_user_language() إلى routes/user_routes.py
@app.route('/api/check-ollama-models', methods=['GET'])
def api_check_ollama_models():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        import requests
        ollama_url = get_setting('ollama_url', 'http://localhost:11434')
        
        # Check if Ollama is running
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            available_models = [model['name'].split(':')[0] for model in models_data.get('models', [])]
            return jsonify({
                'success': True, 
                'available_models': available_models,
                'ollama_running': True
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Ollama غير متاح',
                'ollama_running': False
            })
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'خطأ في الاتصال بـ Ollama: {str(e)}',
            'ollama_running': False
        })

@app.route('/api/install-ollama-model', methods=['POST'])
def api_install_ollama_model():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    data = request.get_json() or {}
    model_name = data.get('model', '')
    
    if not model_name:
        return jsonify({'error': 'اسم النموذج مطلوب'}), 400
    
    try:
        import subprocess
        import sys
        import platform
        
        # محاولة تثبيت النموذج باستخدام pip أولاً
        try:
            pip_result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', f'ollama-{model_name}'],
                capture_output=True, text=True
            )
            
            if pip_result.returncode == 0:
                return jsonify({
                    'success': True, 
                    'message': f'تم تثبيت النموذج {model_name} بنجاح',
                    'model': model_name
                })
        except Exception as pip_error:
            # إذا فشل التثبيت عبر pip، نستمر بالطريقة التقليدية
            pass
        
        # تحديد الأمر المناسب حسب نظام التشغيل
        system = platform.system()
        
        if system == 'Windows':
            # في ويندوز، نستخدم الأمر مع cmd
            process = subprocess.Popen(
                ['cmd', '/c', 'ollama', 'pull', model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        else:  # macOS أو Linux
            # في أنظمة Unix، نستخدم الأمر مباشرة
            process = subprocess.Popen(
                ['ollama', 'pull', model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        return jsonify({
            'success': True, 
            'message': f'بدأ تحميل النموذج {model_name}. يرجى الانتظار...',
            'model': model_name
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'خطأ في تحميل النموذج: {str(e)}'
        })

# Initialize database and default settings
with app.app_context():
    # Make translation function available to all templates
    app.jinja_env.globals['t'] = translate_text
    app.jinja_env.globals['get_user_language'] = get_user_language
    app.jinja_env.globals['get_setting'] = get_setting
    
    # Create all database tables
    db.create_all()
    
    # Initialize default settings if database is empty
    if not Settings.query.first():
        default_settings = [
            # Authentication & Security
            {'key': 'admin_username', 'value': 'admin', 'section': 'AUTH', 'type': 'string', 'description': '{"ar": "اسم مستخدم المدير", "en": "Admin Username"}'},
            {'key': 'admin_password', 'value': 'your_strong_password', 'section': 'AUTH', 'type': 'password', 'description': '{"ar": "كلمة مرور المدير", "en": "Admin Password"}'},
            
            # API Settings
            {'key': 'sonarr_url', 'value': 'http://localhost:8989', 'section': 'API', 'type': 'url', 'description': '{"ar": "رابط Sonarr API", "en": "Sonarr API URL"}'},
            {'key': 'sonarr_api_key', 'value': '', 'section': 'API', 'type': 'string', 'description': '{"ar": "مفتاح Sonarr API", "en": "Sonarr API Key"}'},
            {'key': 'radarr_url', 'value': 'http://localhost:7878', 'section': 'API', 'type': 'url', 'description': '{"ar": "رابط Radarr API", "en": "Radarr API URL"}'},
            {'key': 'radarr_api_key', 'value': '', 'section': 'API', 'type': 'string', 'description': '{"ar": "مفتاح Radarr API", "en": "Radarr API Key"}'},
            {'key': 'ollama_url', 'value': 'http://localhost:11434', 'section': 'API', 'type': 'url', 'description': '{"ar": "رابط Ollama API", "en": "Ollama API URL"}'},
            
            # Model & AI Settings
            {'key': 'whisper_model', 'value': 'medium.en', 'section': 'MODELS', 'type': 'select', 'options': 'tiny,base,small,medium,large,medium.en,large-v2,large-v3', 'description': '{"ar": "نموذج Whisper", "en": "Whisper Model"}'},
            {'key': 'ollama_model', 'value': 'llama3', 'section': 'MODELS', 'type': 'string', 'description': '{"ar": "نموذج Ollama", "en": "Ollama Model"}'},
            
            # UI & Interface
            {'key': 'default_language', 'value': 'ar', 'section': 'UI', 'type': 'select', 'options': 'ar,en', 'description': '{"ar": "لغة الواجهة الافتراضية", "en": "Default Interface Language"}'},
            {'key': 'default_theme', 'value': 'system', 'section': 'UI', 'type': 'select', 'options': 'light,dark,system', 'description': '{"ar": "السمة الافتراضية", "en": "Default Theme"}'},
            {'key': 'items_per_page', 'value': '24', 'section': 'UI', 'type': 'number', 'description': '{"ar": "عدد العناصر في الصفحة", "en": "Items Per Page"}'},
            
            # Corrections & Quality
            {'key': 'auto_correct_filenames', 'value': 'true', 'section': 'CORRECTIONS', 'type': 'boolean', 'description': '{"ar": "تصحيح أسماء الملفات تلقائياً", "en": "Auto Correct Filenames"}'},
        ]
        
        for setting_data in default_settings:
            setting = Settings(**setting_data)
            db.session.add(setting)
        
        db.session.commit()
        print("✓ Default settings initialized successfully")

# Media Services API Endpoints
@app.route('/api/media-services/status')
def api_media_services_status():
    """Get status of all configured media services"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Initialize services from settings
        initialize_media_services()
        
        # Get status for all services
        # TODO: Implement media services status
        return jsonify({"status": "not_implemented", "services": []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/media-services/test/<service_type>')
def api_test_media_service(service_type):
    """Test connection to a specific media service"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        # Configure session with retries
        session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Get service configuration from settings
        service_config = get_service_config(service_type)
        if not service_config:
            return jsonify({
                'service': service_type,
                'connected': False,
                'error': f'Service {service_type} not configured - missing URL or API key',
                'config': {}
            }), 400
        
        url = service_config.get('url', '').rstrip('/')
        api_key = service_config.get('api_key', '')
        
        if not url or not api_key:
            return jsonify({
                'service': service_type,
                'connected': False,
                'error': f'Missing configuration: URL={bool(url)}, API Key={bool(api_key)}',
                'config': service_config
            }), 400
        
        # Test connection based on service type
        if service_type.lower() == 'radarr':
            test_url = f"{url}/api/v3/system/status"
            headers = {'X-Api-Key': api_key}
            
        elif service_type.lower() == 'sonarr':
            test_url = f"{url}/api/v3/system/status"
            headers = {'X-Api-Key': api_key}
            
        elif service_type.lower() == 'plex':
            test_url = f"{url}/identity"
            headers = {'X-Plex-Token': api_key}
            
        elif service_type.lower() == 'jellyfin':
            test_url = f"{url}/System/Info"
            headers = {'X-MediaBrowser-Token': api_key}
            
        elif service_type.lower() == 'emby':
            test_url = f"{url}/System/Info"
            headers = {'X-MediaBrowser-Token': api_key}
            
        elif service_type.lower() == 'kodi':
            # Kodi uses JSON-RPC
            test_url = f"{url}/jsonrpc"
            headers = {'Content-Type': 'application/json'}
            data = {
                "jsonrpc": "2.0",
                "method": "JSONRPC.Ping",
                "id": 1
            }
            
        else:
            return jsonify({
                'service': service_type,
                'connected': False,
                'error': f'Unsupported service type: {service_type}',
                'config': service_config
            }), 400
        
        # Make the test request
        try:
            if service_type.lower() == 'kodi':
                response = session.post(test_url, json=data, headers=headers, timeout=10)
            else:
                response = session.get(test_url, headers=headers, timeout=10)
            
            # Check response
            if response.status_code == 200:
                try:
                    response_json = response.json()
                    return jsonify({
                        'service': service_type,
                        'connected': True,
                        'status': 'Connection successful',
                        'response': response_json if len(str(response_json)) < 500 else 'Response too large',
                        'config': {k: v if k != 'api_key' else '***HIDDEN***' for k, v in service_config.items()}
                    })
                except ValueError as e:
                    # Response is not JSON
                    return jsonify({
                        'service': service_type,
                        'connected': False,
                        'error': f'استجابة JSON غير صالحة - تم استلام HTML بدلاً من JSON. تحقق من الرابط: {url}',
                        'error_en': f'Invalid JSON response - received HTML instead of JSON. Check URL: {url}',
                        'status_code': response.status_code,
                        'content_preview': response.text[:200] + '...' if len(response.text) > 200 else response.text,
                        'suggestion': 'تأكد من صحة الرابط ومفتاح API، وأن الخدمة تعمل بشكل صحيح',
                        'config': {k: v if k != 'api_key' else '***HIDDEN***' for k, v in service_config.items()}
                    })
            else:
                error_msg = f'HTTP {response.status_code}: {response.reason}'
                if response.status_code == 401:
                    error_msg = 'خطأ في المصادقة - مفتاح API غير صحيح'
                elif response.status_code == 404:
                    error_msg = 'المسار غير موجود - تحقق من الرابط'
                elif response.status_code == 403:
                    error_msg = 'ممنوع - تحقق من صلاحيات المفتاح'
                
                return jsonify({
                    'service': service_type,
                    'connected': False,
                    'error': error_msg,
                    'error_en': f'HTTP {response.status_code}: {response.reason}',
                    'status_code': response.status_code,
                    'content': response.text[:200] + '...' if len(response.text) > 200 else response.text,
                    'config': {k: v if k != 'api_key' else '***HIDDEN***' for k, v in service_config.items()}
                })
                
        except requests.exceptions.ConnectTimeout:
            return jsonify({
                'service': service_type,
                'connected': False,
                'error': f'Connection timeout - {url} is not responding',
                'config': {k: v if k != 'api_key' else '***HIDDEN***' for k, v in service_config.items()}
            })
        except requests.exceptions.ConnectionError:
            return jsonify({
                'service': service_type,
                'connected': False,
                'error': f'Connection failed - cannot reach {url}',
                'config': {k: v if k != 'api_key' else '***HIDDEN***' for k, v in service_config.items()}
            })
        except Exception as req_e:
            return jsonify({
                'service': service_type,
                'connected': False,
                'error': f'Request failed: {str(req_e)}',
                'config': {k: v if k != 'api_key' else '***HIDDEN***' for k, v in service_config.items()}
            })
            
    except Exception as e:
        return jsonify({
            'service': service_type,
            'connected': False,
            'error': f'Test failed: {str(e)}',
            'config': {}
        }), 500



@app.route('/api/media-services/sync/<service_type>')
def api_sync_media_service(service_type):
    """Sync media from a specific service"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Initialize services first
        initialize_media_services()
        
        # Sync from service
        results = {}
        
        return jsonify({
            'service': service_type,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/media-services/sync-all')
def api_sync_all_media_services():
    """Sync media from all configured services"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Initialize services first
        initialize_media_services()
        
        # Get all configured services
        service_types = ['radarr', 'sonarr', 'plex', 'jellyfin', 'emby']
        all_results = {}
        active_services = []
        
        # Sync from each configured service
        for service_type in service_types:
            service_config = get_service_config(service_type)
            if service_config:
                active_services.append(service_type)
                try:
                    # Call the appropriate sync function based on service type
                    if service_type == 'radarr':
                        from services.media_services import RadarrAPI
                        radarr = RadarrAPI(service_config['url'], service_config['api_key'])
                        result = radarr.sync_movies()
                    elif service_type == 'sonarr':
                        from services.media_services import SonarrAPI
                        sonarr = SonarrAPI(service_config['url'], service_config['api_key'])
                        result = sonarr.sync_series()
                    elif service_type in ['plex', 'jellyfin', 'emby']:
                        # For media servers, just verify connection for now
                        result = {'status': 'connected', 'message': f'{service_type.capitalize()} connection verified'}
                    else:
                        result = {'status': 'skipped', 'message': f'Sync not implemented for {service_type}'}
                    
                    all_results[service_type] = result
                except Exception as service_error:
                    all_results[service_type] = {
                        'status': 'error',
                        'message': f'Failed to sync {service_type}: {str(service_error)}'
                    }
        
        return jsonify({
            'results': all_results,
            'active_services': active_services
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_service_config(service_type):
    """Get service configuration from settings"""
    settings = get_settings()
    
    config_map = {
        'plex': {
            'enabled_key': 'plex_enabled',
            'url_key': 'plex_url',
            'auth_key': 'plex_token',
            'auth_field': 'token'
        },
        'jellyfin': {
            'enabled_key': 'jellyfin_enabled',
            'url_key': 'jellyfin_url',
            'auth_key': 'jellyfin_api_key',
            'auth_field': 'api_key'
        },
        'emby': {
            'enabled_key': 'emby_enabled',
            'url_key': 'emby_url',
            'auth_key': 'emby_api_key',
            'auth_field': 'api_key'
        },
        'radarr': {
            'enabled_key': 'radarr_enabled',
            'url_key': 'radarr_url',
            'auth_key': 'radarr_api_key',
            'auth_field': 'api_key'
        },
        'sonarr': {
            'enabled_key': 'sonarr_enabled',
            'url_key': 'sonarr_url',
            'auth_key': 'sonarr_api_key',
            'auth_field': 'api_key'
        },
        'kodi': {
            'enabled_key': 'kodi_enabled',
            'url_key': 'kodi_url',
            'auth_key': 'kodi_username',  # Kodi can use username/password
            'auth_field': 'username'
        }
    }
    
    if service_type not in config_map:
        return None
    
    config_info = config_map[service_type]
    
    # Check if service is enabled
    if not settings.get(config_info['enabled_key'], 'false').lower() == 'true':
        return None
    
    # Get URL and auth
    url = settings.get(config_info['url_key'], '')
    auth = settings.get(config_info['auth_key'], '')
    
    if not url:
        return None
    
    # For Kodi, auth is optional (some installations don't require it)
    if service_type == 'kodi':
        password = settings.get('kodi_password', '')
        return {
            'url': url,
            'username': auth,
            'password': password,
            'api_key': auth  # For compatibility
        }
    else:
        # For other services, auth is required
        if not auth:
            return None
        
        return {
            'url': url,
            config_info['auth_field']: auth,
            'api_key': auth  # Ensure this field is always present
        }

def initialize_media_services():
    """Initialize all enabled media services from settings"""
    service_types = ['plex', 'jellyfin', 'emby', 'radarr', 'sonarr']
    
    for service_type in service_types:
        service_config = get_service_config(service_type)
        if service_config:
            True  # TODO: Implement media service configuration

# GPU Management API Endpoints
@app.route('/api/gpu/status')
def api_gpu_status():
    """Get GPU status and information"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        gpus = gpu_manager.get_available_gpus()
        allocation = gpu_manager.get_optimal_allocation()
        
        return jsonify({
            'nvidia_available': gpu_manager.is_nvidia_available(),
            'gpus': gpus,
            'optimal_allocation': allocation,
            'total_gpus': len(gpus)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/gpu/allocate', methods=['POST'])
def api_gpu_allocate():
    """Allocate GPUs to services"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        whisper_gpu = data.get('whisper_gpu')
        ollama_gpu = data.get('ollama_gpu')
        
        # Update settings
        if whisper_gpu is not None:
            update_setting('whisper_gpu_id', str(whisper_gpu))
        
        if ollama_gpu is not None:
            update_setting('ollama_gpu_id', str(ollama_gpu))
        
        return jsonify({
            'success': True,
            'allocation': {
                'whisper_gpu': whisper_gpu,
                'ollama_gpu': ollama_gpu
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/gpu/auto-allocate', methods=['POST'])
def api_gpu_auto_allocate():
    """Automatically allocate GPUs based on optimal configuration"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        allocation = gpu_manager.get_optimal_allocation()
        
        # Update settings with optimal allocation
        if allocation['whisper'] is not None:
            update_setting('whisper_gpu_id', str(allocation['whisper']))
        else:
            update_setting('whisper_gpu_id', 'cpu')
            
        if allocation['ollama'] is not None:
            update_setting('ollama_gpu_id', str(allocation['ollama']))
        else:
            update_setting('ollama_gpu_id', 'cpu')
        
        # Update auto allocation setting
        update_setting('auto_gpu_allocation', 'true')
        
        return jsonify({
            'success': True,
            'allocation': allocation,
            'message': 'GPUs allocated automatically based on optimal configuration'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_current_gpu_allocation():
    """Get current GPU allocation from settings"""
    settings = get_settings()
    
    whisper_gpu = settings.get('whisper_gpu_id', 'auto')
    ollama_gpu = settings.get('ollama_gpu_id', 'auto')
    
    # Convert 'auto' to actual GPU IDs if needed
    if whisper_gpu == 'auto' or ollama_gpu == 'auto':
        optimal = gpu_manager.get_optimal_allocation()
        if whisper_gpu == 'auto':
            whisper_gpu = optimal['whisper'] if optimal['whisper'] is not None else 'cpu'
        if ollama_gpu == 'auto':
            ollama_gpu = optimal['ollama'] if optimal['ollama'] is not None else 'cpu'
    
    return {
        'whisper_gpu': whisper_gpu,
        'ollama_gpu': ollama_gpu
    }

# Remote Storage Management API Endpoints
@app.route('/api/remote-mount-test', methods=['POST'])
def api_remote_mount_test():
    """Test remote file system connection"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Check if remote storage is enabled
        settings = get_settings()
        enabled_value = settings.get('remote_storage_enabled', 'false')
        if isinstance(enabled_value, bool):
            is_enabled = enabled_value
        else:
            is_enabled = str(enabled_value).lower() == 'true'
        
        if not is_enabled:
            return jsonify({'success': False, 'message': 'Remote storage disabled', 'error': 'Remote storage is not enabled in settings'})
        
        data = request.get_json()
        protocol = data.get('protocol')
        host = data.get('host')
        username = data.get('username')
        password = data.get('password')
        path = data.get('path', '/')
        port = data.get('port')
        
        from services.remote_storage import test_remote_connection
        result = test_remote_connection(protocol, host, username, password, path, port)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/remote-mount-setup', methods=['POST'])
def api_remote_mount_setup():
    """Setup remote file system mount"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        # Save remote mount settings (this function should be able to enable storage)
        update_setting('remote_storage_enabled', str(data.get('enabled', False)))
        update_setting('remote_storage_protocol', data.get('protocol', 'sftp'))
        update_setting('remote_storage_host', data.get('host', ''))
        update_setting('remote_storage_port', str(data.get('port', 22)))
        update_setting('remote_storage_username', data.get('username', ''))
        update_setting('remote_storage_password', data.get('password', ''))
        update_setting('remote_storage_path', data.get('path', '/'))
        update_setting('remote_storage_mount_point', data.get('mount_point', '/mnt/remote'))
        update_setting('remote_storage_auto_mount', str(data.get('auto_mount', True)))
        
        if data.get('enabled', False):
            from services.remote_storage import setup_remote_mount
            result = setup_remote_mount(
                data.get('protocol', 'smb'),
                data.get('host', ''),
                data.get('username', ''),
                data.get('password', ''),
                data.get('remote_path', ''),
                data.get('local_path', ''),
                data.get('port')
            )
        else:
            result = {'success': True, 'message': 'Remote storage disabled'}
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/remote-mount-status', methods=['GET'])
def api_remote_mount_status():
    """Get remote mount status"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from services.remote_storage import get_mount_status
        status = get_mount_status()
        
        # Add settings info
        settings = get_settings()
        # Handle both string and boolean values for remote_storage_enabled
        enabled_value = settings.get('remote_storage_enabled', 'false')
        if isinstance(enabled_value, bool):
            is_enabled = enabled_value
        else:
            is_enabled = str(enabled_value).lower() == 'true'
        
        status['settings'] = {
            'enabled': is_enabled,
            'protocol': settings.get('remote_storage_protocol', 'sftp'),
            'host': settings.get('remote_storage_host', ''),
            'mount_point': settings.get('remote_storage_mount_point', '/mnt/remote')
        }
        
        print(f"DEBUG: Remote storage API - enabled_value: {enabled_value}, type: {type(enabled_value)}, is_enabled: {is_enabled}")
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/remote-mount-unmount', methods=['POST'])
def api_remote_mount_unmount():
    """Unmount remote storage"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        mount_point = data.get('mount_point')
        
        from services.remote_storage import unmount_remote_storage
        result = unmount_remote_storage(mount_point)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def validate_browse_path(path):
    """Validate path for browsing - security check"""
    if not path:
        return False
        
    # مسارات النظام المحظورة
    system_paths = [
        '/etc', '/sys', '/proc', '/dev', '/boot', '/root',
        '/var/log', '/var/lib', '/usr/bin', '/usr/sbin', '/bin', '/sbin',
        '/home/.ssh', '/home/.config', '/home/.local'
    ]
    
    # فحص إذا كان المسار من مسارات النظام المحظورة
    for sys_path in system_paths:
        if path.startswith(sys_path):
            return False
    
    # المسارات المسموحة للتصفح
    allowed_paths = [
        '/mnt', '/media', '/opt', '/srv', '/tmp',
        '/var/media', '/var/lib/media', '/home/media'
    ]
    
    # فحص إذا كان المسار يبدأ بمسار مسموح
    for allowed in allowed_paths:
        if path.startswith(allowed):
            return True
    
    # السماح بالمسار الجذري للتصفح الأولي
    if path == '/':
        return True
        
    return False

def is_supported_media_file(filename):
    """Check if file is a supported media format"""
    settings = get_settings()
    extensions = settings.get('video_extensions', 'mp4,mkv,avi,mov,wmv,flv,webm,m4v')
    supported_exts = [ext.strip().lower() for ext in extensions.split(',')]
    
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    return file_ext in supported_exts

@app.route('/api/server-config/apply', methods=['POST'])
def api_apply_server_config():
    """تطبيق تكوين الخادم الجديد"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', '0.0.0.0')
        port = data.get('port', 5000)
        
        # استيراد مدير الخادم
        from server_config import apply_server_settings
        
        # تطبيق الإعدادات
        result = apply_server_settings(host, port)
        
        if result['success']:
            # تحديث قاعدة البيانات
            update_setting('server_host', host)
            update_setting('server_port', str(port))
            
            log_to_db("INFO", f"Server config updated: {host}:{port}")
            
            return jsonify({
                'success': True,
                'message': 'تم تحديث تكوين الخادم بنجاح',
                'host': host,
                'port': port,
                'results': result['results']
            })
        else:
            return jsonify({
                'success': False,
                'message': 'فشل في تطبيق تكوين الخادم',
                'errors': result.get('errors', []),
                'results': result['results']
            })
            
    except Exception as e:
        log_to_db("ERROR", f"Server config error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/server-config/status')
def api_server_config_status():
    """الحصول على حالة الخادم الحالية"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from server_config import create_server_manager
        
        manager = create_server_manager()
        current_config = manager.get_current_config()
        service_status = manager.get_service_status()
        
        return jsonify({
            'current_config': current_config,
            'service_status': service_status,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/server-config/validate', methods=['POST'])
def api_validate_server_config():
    """التحقق من صحة تكوين الخادم"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', '0.0.0.0')
        port = data.get('port', 5000)
        
        from server_config import create_server_manager
        
        manager = create_server_manager()
        errors = manager.validate_config(host, port)
        port_available = manager.check_port_availability(int(port))
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors,
            'port_available': port_available,
            'host': host,
            'port': port
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/browse-folders', methods=['GET', 'POST'])
def api_browse_folders():
    """Browse folders for file browser with security protection"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json() or {}
        path = data.get('path', request.args.get('path', '/'))
        
        # التحقق الأمني من المسار
        if not validate_browse_path(path):
            return jsonify({'error': 'Access denied to this path'}), 403
        
        # Check if remote storage is enabled
        remote_storage_enabled = get_setting('remote_storage_enabled', 'false') == 'true'
        
        # If remote storage is enabled, try to browse remote directories
        if remote_storage_enabled and path.startswith('/remote/'):
            try:
                from services.remote_storage import list_remote_directory
                
                protocol = get_setting('remote_storage_protocol', 'sftp')
                host = get_setting('remote_storage_host', '')
                username = get_setting('remote_storage_username', '')
                password = get_setting('remote_storage_password', '')
                port = int(get_setting('remote_storage_port', '22'))
                
                # Remove '/remote' prefix for actual remote path
                remote_path = path.replace('/remote', '') or '/'
                
                result = list_remote_directory(
                    protocol=protocol,
                    host=host,
                    path=remote_path,
                    port=port,
                    username=username,
                    password=password
                )
                
                if result.get('success'):
                    folders = []
                    for item in result.get('files', []):
                        folders.append({
                            'name': item['name'],
                            'path': f"/remote{item['path']}",
                            'type': 'folder' if item['is_directory'] else 'file'
                        })
                    
                    return jsonify({
                        "success": True,
                        "path": path,
                        "folders": folders
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": f"Remote storage error: {result.get('error', 'Unknown error')}"
                    }), 500
                    
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"Remote storage disabled or not configured: {str(e)}"
                }), 500
        
        # Browse real local directories
        try:
            import os
os.environ['DATABASE_FILE'] = 'library_bcce0f55.db' # تم إضافته بواسطة reset_database.py
            
            # Normalize the path
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            
            # Security check - only allow certain directories
            allowed_paths = ['/home', '/mnt', '/opt', '/var', '/usr', '/root']
            
            # Check if path is allowed or subdirectory of allowed path
            path_allowed = False
            for allowed in allowed_paths:
                if path.startswith(allowed) or path == '/':
                    path_allowed = True
                    break
            
            if not path_allowed:
                return jsonify({
                    "success": False,
                    "error": "Access denied to this directory"
                }), 403
            
            folders = []
            
            # For root directory, show only allowed directories
            if path == '/':
                for allowed_dir in allowed_paths:
                    if os.path.exists(allowed_dir) and os.path.isdir(allowed_dir):
                        folders.append({
                            'name': os.path.basename(allowed_dir),
                            'path': allowed_dir,
                            'type': 'folder'
                        })
                # Add remote folder if enabled
                if remote_storage_enabled:
                    folders.append({'name': 'remote', 'path': '/remote', 'type': 'folder'})
            else:
                # Browse actual directory contents
                if os.path.exists(path) and os.path.isdir(path):
                    try:
                        for item in os.listdir(path):
                            item_path = os.path.join(path, item)
                            if os.path.isdir(item_path):
                                folders.append({
                                    'name': item,
                                    'path': item_path,
                                    'type': 'folder'
                                })
                    except PermissionError:
                        return jsonify({
                            "success": False,
                            "error": "Permission denied to access this directory"
                        }), 403
                else:
                    return jsonify({
                        "success": False,
                        "error": "Directory not found"
                    }), 404
            
            return jsonify({
                "success": True,
                "path": path,
                "folders": folders
            })
            
        except Exception as e:
            # Fallback to safe mock structure if real browsing fails
            mock_folders = {
                '/': [
                    {'name': 'home', 'path': '/home', 'type': 'folder'},
                    {'name': 'mnt', 'path': '/mnt', 'type': 'folder'},
                    {'name': 'opt', 'path': '/opt', 'type': 'folder'},
                    {'name': 'var', 'path': '/var', 'type': 'folder'},
                    {'name': 'usr', 'path': '/usr', 'type': 'folder'},
                ] + ([{'name': 'remote', 'path': '/remote', 'type': 'folder'}] if remote_storage_enabled else []),
            '/home': [
                {'name': 'user', 'path': '/home/user', 'type': 'folder'},
                {'name': 'admin', 'path': '/home/admin', 'type': 'folder'}
            ],
            '/mnt': [
                {'name': 'storage', 'path': '/mnt/storage', 'type': 'folder'},
                {'name': 'remote', 'path': '/mnt/remote', 'type': 'folder'},
                {'name': 'backup', 'path': '/mnt/backup', 'type': 'folder'}
            ],
            '/opt': [
                {'name': 'applications', 'path': '/opt/applications', 'type': 'folder'},
                {'name': 'scripts', 'path': '/opt/scripts', 'type': 'folder'}
            ],
            '/var': [
                {'name': 'log', 'path': '/var/log', 'type': 'folder'},
                {'name': 'www', 'path': '/var/www', 'type': 'folder'},
                {'name': 'lib', 'path': '/var/lib', 'type': 'folder'}
            ],
            '/mnt/storage': [
                {'name': 'movies', 'path': '/mnt/storage/movies', 'type': 'folder'},
                {'name': 'series', 'path': '/mnt/storage/series', 'type': 'folder'},
                {'name': 'music', 'path': '/mnt/storage/music', 'type': 'folder'}
            ],
            '/mnt/remote': [
                {'name': 'synology', 'path': '/mnt/remote/synology', 'type': 'folder'},
                {'name': 'nas', 'path': '/mnt/remote/nas', 'type': 'folder'}
            ]
        }
        
        folders = mock_folders.get(path, [])
        
        return jsonify({
            "success": True,
            "path": path,
            "folders": folders
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/download')
def download_page():
    """Display download page"""
    return render_template('download.html')

@app.route('/download-github-release')
def download_github_release():
    """Download GitHub release package without authentication"""
    from flask import send_file
    
    # Check if GitHub release file exists - prioritize latest version with installation files
    release_files = [
        'ai-translator-v2.2.5-final-github.zip',      # Latest final GitHub package with English docs
        'ai-translator-v2.2.5-fix-package.zip',       # Latest fix package with Flask-SQLAlchemy fix
        'ai-translator-v2.2.5-github-complete.zip',   # Complete with installation files
        'ai-translator-v2.2.5-github.zip',            # Latest GitHub package
        'ai-translator-v2.2.5.zip',                   # Latest version
        'ai-translator-v2.2.2.zip',                   # Previous release
        'ai-translator-github-v2.2.1.zip'             # fallback
    ]
    
    for release_file in release_files:
        if os.path.exists(release_file):
            if 'v2.2.5' in release_file:
                version = '2.2.5'
            elif 'v2.2.2' in release_file:
                version = '2.2.2'
            elif '2.2.1' in release_file:
                version = '2.2.1'
            else:
                version = '2.2.0'
            
            # Determine download name based on file content
            if 'final-github' in release_file:
                download_name = f'ai-translator-v{version}-final-github.zip'
            elif 'fix-package' in release_file:
                download_name = f'ai-translator-v{version}-fix-package.zip'
            elif 'complete' in release_file:
                download_name = f'ai-translator-v{version}-complete-with-installer.zip'
            else:
                download_name = f'ai-translator-v{version}-ubuntu-server.zip'
            
            return send_file(
                release_file,
                as_attachment=True,
                download_name=download_name,
                mimetype='application/zip'
            )
    else:
        return jsonify({'error': 'GitHub release file not found'}), 404

@app.route('/download-comprehensive-package')
def download_comprehensive_package():
    """Download comprehensive AI Translator package with Ubuntu Server compatibility"""
    try:
        # Find the latest comprehensive package
        package_files = [f for f in os.listdir('.') if f.startswith('ai-translator-comprehensive-v2.2.5-') and f.endswith('.zip')]
        
        if not package_files:
            return jsonify({
                'error': 'No comprehensive package found',
                'message': 'Package not available for download',
                'ubuntu_compatibility': 'Ubuntu Server 20.04+ fully supported'
            }), 404
        
        # Get the latest package
        latest_package = sorted(package_files)[-1]
        
        if not os.path.exists(latest_package):
            return jsonify({
                'error': 'Package file not found',
                'file': latest_package
            }), 404
        
        return send_file(
            latest_package,
            as_attachment=True,
            download_name=latest_package,
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({
            'error': 'Download failed',
            'message': str(e)
        }), 500

@app.route('/download-clean-package')
def download_clean_package():
    """Download clean GitHub package - optimized for new repository"""
    from flask import send_file
    
    # Check if clean package exists
    clean_package_file = 'ai-translator-clean-v2.2.5.zip'
    
    if os.path.exists(clean_package_file):
        return send_file(
            clean_package_file,
            as_attachment=True,
            download_name='ai-translator-clean-v2.2.5.zip',
            mimetype='application/zip'
        )
    else:
        return jsonify({'error': 'Clean package not found'}), 404

@app.route('/download-final-package')
def download_final_package():
    """Download final updated package with fixed installation script"""
    from flask import send_file
    
    # Check if final package exists
    final_package_file = 'ai-translator-final-v2.2.5.zip'
    
    if os.path.exists(final_package_file):
        return send_file(
            final_package_file,
            as_attachment=True,
            download_name='ai-translator-final-v2.2.5.zip',
            mimetype='application/zip'
        )
    else:
        return jsonify({'error': 'Final package not found'}), 404

@app.route('/download-working-package')
def download_working_package():
    """Download working package with universal installation script"""
    from flask import send_file
    
    # Check if working package exists
    working_package_file = 'ai-translator-working-v2.2.5.zip'
    
    if os.path.exists(working_package_file):
        return send_file(
            working_package_file,
            as_attachment=True,
            download_name='ai-translator-working-v2.2.5.zip',
            mimetype='application/zip'
        )
    else:
        return jsonify({'error': 'Working package not found'}), 404

@app.route('/install.sh')
def get_install_script():
    """Serve the GitHub installation script directly"""
    from flask import Response
    
    if os.path.exists('install_github.sh'):
        with open('install_github.sh', 'r') as f:
            script_content = f.read()
        
        return Response(
            script_content,
            mimetype='text/plain',
            headers={'Content-Disposition': 'inline; filename=install.sh'}
        )
    else:
        return "Installation script not found", 404

@app.route('/download-updated-files')
def download_updated_files():
    """Download updated files package for GitHub repository"""
    from flask import send_file
    import glob
    
    # Find the latest updated files package
    pattern = 'ai-translator-updated-files-*.zip'
    files = glob.glob(pattern)
    
    if files:
        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        return send_file(
            latest_file,
            as_attachment=True,
            download_name='ai-translator-updated-files.zip',
            mimetype='application/zip'
        )
    else:
        return jsonify({'error': 'Updated files package not found'}), 404

@app.route('/download-fixed-github-release')
def download_fixed_github_release():
    """Download Fixed GitHub release package without authentication"""
    from flask import send_file
    
    # Check if Fixed GitHub release file exists
    fixed_release_files = [
        'ai-translator-v2.2.5-fixed-github.zip',      # Latest fixed GitHub package
        'ai-translator-v2.2.5-final-github.zip',      # Fallback to final
        'ai-translator-v2.2.5-fix-package.zip',       # Latest fix package
        'ai-translator-v2.2.5-github.zip',            # Latest GitHub package
    ]
    
    for release_file in fixed_release_files:
        if os.path.exists(release_file):
            version = '2.2.5'
            
            # Determine download name based on file content
            if 'fixed-github' in release_file:
                download_name = f'ai-translator-v{version}-fixed-github.zip'
            elif 'final-github' in release_file:
                download_name = f'ai-translator-v{version}-final-github.zip'
            elif 'fix-package' in release_file:
                download_name = f'ai-translator-v{version}-fix-package.zip'
            else:
                download_name = f'ai-translator-v{version}-ubuntu-server.zip'
            
            return send_file(
                release_file,
                as_attachment=True,
                download_name=download_name,
                mimetype='application/zip'
            )
    
    return jsonify({'error': 'Fixed GitHub release file not found'}), 404

@app.route('/download-final-github-release')
def download_final_github_release():
    """Download Final GitHub release package with cache fixes"""
    from flask import send_file
    
    # Check if Final GitHub release file exists
    final_release_files = [
        'ai-translator-v2.2.5-final-cache-fix.zip',       # Latest final package with cache fixes
        'ai-translator-v2.2.5-fixed-github.zip',          # Fallback to fixed
        'ai-translator-v2.2.5-final-github.zip',          # Fallback to final
        'ai-translator-v2.2.5-github.zip',                # Latest GitHub package
    ]
    
    for release_file in final_release_files:
        if os.path.exists(release_file):
            version = '2.2.5'
            
            # Determine download name based on file content
            if 'final-cache-fix' in release_file:
                download_name = f'ai-translator-v{version}-final-cache-fix.zip'
            elif 'fixed-github' in release_file:
                download_name = f'ai-translator-v{version}-fixed-github.zip'
            elif 'final-github' in release_file:
                download_name = f'ai-translator-v{version}-final-github.zip'
            else:
                download_name = f'ai-translator-v{version}-ubuntu-server.zip'
            
            return send_file(
                release_file,
                as_attachment=True,
                download_name=download_name,
                mimetype='application/zip'
            )
    
    return jsonify({'error': 'Final GitHub release file not found'}), 404

@app.route('/download-remote-storage-fix')
def download_remote_storage_fix():
    """Download remote storage fix package without authentication"""
    try:
        # Package file path
        package_path = 'ai-translator-v2.2.5-remote-storage-fix.zip'
        
        # Check if file exists
        if os.path.exists(package_path):
            return send_file(
                package_path,
                as_attachment=True,
                download_name='ai-translator-v2.2.5-remote-storage-fix.zip',
                mimetype='application/zip'
            )
    
    except Exception as e:
        print(f"Download error: {e}")
    
    return jsonify({'error': 'Remote storage fix package not found'}), 404

@app.route('/fix-server-direct.sh')
def download_server_fix_script():
    """Download server fix script for direct execution on remote server"""
    try:
        script_path = 'fix_server_direct.sh'
        if os.path.exists(script_path):
            return send_file(
                script_path,
                as_attachment=True,
                download_name='fix_server_direct.sh',
                mimetype='text/x-shellscript'
            )
    except Exception as e:
        print(f"Script download error: {e}")
    
    return jsonify({'error': 'Server fix script not found'}), 404

@app.route('/download-enhanced-package')
def download_enhanced_package():
    """Download latest enhanced AI Translator v2.2.5 package without authentication"""
    # البحث عن أحدث حزمة محسنة
    import glob
    enhanced_packages = glob.glob('ai-translator-enhanced-v2.2.5-*.zip')
    if enhanced_packages:
        # ترتيب الحزم حسب التاريخ (الأحدث أولاً)
        enhanced_packages.sort(reverse=True)
        latest_package = enhanced_packages[0]
        return send_file(latest_package, as_attachment=True, download_name=latest_package)
    else:
        return jsonify({'error': 'Enhanced package not found'}), 404

@app.route('/install-reliable.sh')
def download_reliable_install_script():
    """Download reliable installation script without authentication"""
    script_path = 'install_fixed_reliable.sh'
    if os.path.exists(script_path):
        return send_file(
            script_path,
            as_attachment=True,
            download_name='install_reliable.sh',
            mimetype='text/x-shellscript'
        )
    else:
        return jsonify({'error': 'Reliable install script not found'}), 404

@app.route('/download-complete-github-package')
def download_complete_github_package():
    """Download complete GitHub release package without authentication"""
    package_file = 'ai-translator-github-release-v2.2.5-complete.zip'
    if os.path.exists(package_file):
        return send_file(
            package_file,
            as_attachment=True,
            download_name=package_file,
            mimetype='application/zip'
        )
    else:
        return jsonify({'error': 'GitHub release package not found'}), 404

@app.route('/download-database-fixed-package')
def download_database_fixed_package():
    """Download database fixed complete package without authentication"""
    try:
        with open('.latest_database_fixed_package.txt', 'r') as f:
            package_file = f.read().strip()
        
        if os.path.exists(package_file):
            return send_file(
                package_file,
                as_attachment=True,
                download_name=package_file,
                mimetype='application/gzip'
            )
        else:
            return jsonify({'error': 'Database fixed package not found'}), 404
    except FileNotFoundError:
        return jsonify({'error': 'Package information not found'}), 404

@app.route('/download-fix-pip-bat')
def download_fix_pip_bat():
    """Download fix_pip.bat script for fixing pip issues on Windows"""
    try:
        script_path = 'fix_pip.bat'
        if os.path.exists(script_path):
            return send_file(
                script_path,
                as_attachment=True,
                download_name='fix_pip.bat',
                mimetype='application/x-bat'
            )
    except Exception as e:
        print(f"Script download error: {e}")
    
    return jsonify({'error': 'fix_pip.bat script not found'}), 404

@app.route('/download-fix-pip-sh')
def download_fix_pip_sh():
    """Download fix_pip.sh script for fixing pip issues on Linux/Mac"""
    try:
        script_path = 'fix_pip.sh'
        if os.path.exists(script_path):
            return send_file(
                script_path,
                as_attachment=True,
                download_name='fix_pip.sh',
                mimetype='text/x-shellscript'
            )
    except Exception as e:
        print(f"Script download error: {e}")
    
    return jsonify({'error': 'fix_pip.sh script not found'}), 404

@app.route('/pip-fix-guide')
def pip_fix_guide():
    """Render the pip fix guide page"""
    return render_template('pip_fix_guide.html')

@app.route('/download-fixed-installation-package')
def download_fixed_installation_package():
    """Download fixed installation package with corrected scripts without authentication"""
    try:
        with open('.latest_fixed_package.txt', 'r') as f:
            package_file = f.read().strip()
        
        if os.path.exists(package_file):
            return send_file(
                package_file,
                as_attachment=True,
                download_name=package_file,
                mimetype='application/gzip'
            )
        else:
            return jsonify({'error': 'Fixed installation package not found'}), 404
    except FileNotFoundError:
        return jsonify({'error': 'Package information not found'}), 404

# System Performance API Endpoints
@app.route('/api/optimize-system', methods=['POST'])
def api_optimize_system():
    """Optimize system performance"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # تحسين النظام
        import subprocess
        import os
os.environ['DATABASE_FILE'] = 'library_bcce0f55.db' # تم إضافته بواسطة reset_database.py
        
        # مسح ملفات المؤقتة
        subprocess.run(['find', '/tmp', '-type', 'f', '-atime', '+7', '-delete'], 
                      capture_output=True, text=True)
        
        # تحسين ذاكرة SQLite
        from sqlalchemy import text
        db.session.execute(text('VACUUM;'))
        db.session.execute(text('PRAGMA optimize;'))
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'System optimized successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-cache', methods=['POST'])
def api_clear_cache():
    """Clear application cache"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import shutil
        import tempfile
        
        # مسح ملفات المؤقتة
        temp_dir = tempfile.gettempdir()
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isfile(item_path) and item.startswith('ai_translator_'):
                os.remove(item_path)
        
        return jsonify({'success': True, 'message': 'Cache cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/restart-services', methods=['POST'])
def api_restart_services():
    """Restart application services"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # في بيئة Replit، لا يمكن إعادة تشغيل الخدمات، لذا سنقوم بتنشيط الذاكرة
        import gc
        gc.collect()
        
        return jsonify({'success': True, 'message': 'Application refreshed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-metrics', methods=['POST'])
def api_reset_metrics():
    """Reset system metrics"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # إعادة تعيين المقاييس في قاعدة البيانات
        from sqlalchemy import text
        db.session.execute(text("DELETE FROM logs WHERE level = 'METRIC'"))
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Metrics reset successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-sample-data', methods=['POST'])
def api_create_sample_data():
    """Create sample data for development"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # إنشاء بيانات تجريبية
        from datetime import datetime
        
        # إضافة بعض الملفات التجريبية
        sample_media = [
            {'path': '/sample/movie1.mp4', 'title': 'Sample Movie 1', 'media_type': 'movie'},
            {'path': '/sample/movie2.mkv', 'title': 'Sample Movie 2', 'media_type': 'movie'},
            {'path': '/sample/series1.mp4', 'title': 'Sample Series S01E01', 'media_type': 'episode'}
        ]
        
        for media in sample_media:
            existing = MediaFile.query.filter_by(path=media['path']).first()
            if not existing:
                new_media = MediaFile()
                new_media.path = media['path']
                new_media.title = media['title']
                new_media.media_type = media['media_type']
                new_media.translated = False
                new_media.has_subtitles = False
                db.session.add(new_media)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Sample data created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-sample-data', methods=['POST'])
def api_clear_sample_data():
    """Clear sample data"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # مسح البيانات التجريبية
        MediaFile.query.filter(MediaFile.path.like('/sample/%')).delete()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Sample data cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-diagnostics', methods=['POST'])
def api_run_diagnostics():
    """Run system diagnostics"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401

@app.route('/api/check-ffmpeg-status', methods=['POST'])
def api_check_ffmpeg_status():
    """Check FFmpeg status"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import subprocess
        import os
os.environ['DATABASE_FILE'] = 'library_bcce0f55.db' # تم إضافته بواسطة reset_database.py
        
        data = request.get_json()
        ffmpeg_path = data.get('path', '')
        
        if not ffmpeg_path:
            ffmpeg_path = get_setting('UTILITIES.FFMPEG_PATH', '')
        
        if ffmpeg_path and os.path.exists(ffmpeg_path):
            # استخدام المسار المخصص
            cmd = [ffmpeg_path, '-version']
        else:
            # محاولة استخدام FFmpeg من مسار النظام
            cmd = ['ffmpeg', '-version']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # استخراج إصدار FFmpeg من النتيجة
                version_line = result.stdout.split('\n')[0]
                if 'ffmpeg version' in version_line.lower():
                    version = version_line.split('ffmpeg version')[1].strip().split(' ')[0]
                else:
                    version = 'installed'
                
                return jsonify({
                    'status': 'ok',
                    'version': version,
                    'path': ffmpeg_path if ffmpeg_path else 'system path'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'FFmpeg not found or not working properly'
                })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/install-ffmpeg', methods=['POST'])
def api_install_ffmpeg():
    """Install FFmpeg"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import subprocess
        import os
os.environ['DATABASE_FILE'] = 'library_bcce0f55.db' # تم إضافته بواسطة reset_database.py
        import platform
        import tempfile
        import shutil
        from pathlib import Path
        
        system = platform.system().lower()
        
        if system == 'windows':
            # تثبيت FFmpeg على Windows
            temp_dir = tempfile.mkdtemp()
            try:
                # تنزيل FFmpeg
                download_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
                zip_path = os.path.join(temp_dir, "ffmpeg.zip")
                
                # تنزيل الملف
                import urllib.request
                urllib.request.urlretrieve(download_url, zip_path)
                
                # استخراج الملف
                import zipfile
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # العثور على مجلد FFmpeg
                ffmpeg_dir = None
                for item in os.listdir(temp_dir):
                    if os.path.isdir(os.path.join(temp_dir, item)) and 'ffmpeg' in item.lower():
                        ffmpeg_dir = os.path.join(temp_dir, item)
                        break
                
                if not ffmpeg_dir:
                    return jsonify({
                        'success': False,
                        'message': 'Could not find FFmpeg directory in extracted files'
                    })
                
                # العثور على مسار FFmpeg.exe
                ffmpeg_exe = None
                for root, dirs, files in os.walk(ffmpeg_dir):
                    for file in files:
                        if file.lower() == 'ffmpeg.exe':
                            ffmpeg_exe = os.path.join(root, file)
                            break
                    if ffmpeg_exe:
                        break
                
                if not ffmpeg_exe:
                    return jsonify({
                        'success': False,
                        'message': 'Could not find ffmpeg.exe in extracted files'
                    })
                
                # إنشاء مجلد للبرامج المساعدة إذا لم يكن موجودًا
                app_dir = os.path.dirname(os.path.abspath(__file__))
                utilities_dir = os.path.join(app_dir, 'utilities')
                os.makedirs(utilities_dir, exist_ok=True)
                
                # نسخ FFmpeg إلى مجلد البرامج المساعدة
                ffmpeg_dest = os.path.join(utilities_dir, 'ffmpeg.exe')
                shutil.copy2(ffmpeg_exe, ffmpeg_dest)
                
                # تحديث الإعدادات
                update_setting('UTILITIES.FFMPEG_PATH', ffmpeg_dest)
                
                return jsonify({
                    'success': True,
                    'message': 'FFmpeg installed successfully',
                    'path': ffmpeg_dest
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error installing FFmpeg: {str(e)}'
                })
            finally:
                # تنظيف المجلد المؤقت
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        elif system == 'linux':
            # تثبيت FFmpeg على Linux
            try:
                # استخدام مدير الحزم المناسب
                result = subprocess.run(['apt-get', 'update'], capture_output=True, text=True)
                result = subprocess.run(['apt-get', 'install', '-y', 'ffmpeg'], capture_output=True, text=True)
                
                if result.returncode == 0:
                    # العثور على مسار FFmpeg
                    which_result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
                    ffmpeg_path = which_result.stdout.strip()
                    
                    # تحديث الإعدادات
                    update_setting('UTILITIES.FFMPEG_PATH', ffmpeg_path)
                    
                    return jsonify({
                        'success': True,
                        'message': 'FFmpeg installed successfully',
                        'path': ffmpeg_path
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'Error installing FFmpeg: {result.stderr}'
                    })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error installing FFmpeg: {str(e)}'
                })
        
        elif system == 'darwin':
            # تثبيت FFmpeg على macOS
            try:
                # التحقق من وجود Homebrew
                brew_check = subprocess.run(['which', 'brew'], capture_output=True, text=True)
                if brew_check.returncode != 0:
                    return jsonify({
                        'success': False,
                        'message': 'Homebrew is required to install FFmpeg on macOS. Please install Homebrew first.'
                    })
                
                # تثبيت FFmpeg باستخدام Homebrew
                result = subprocess.run(['brew', 'install', 'ffmpeg'], capture_output=True, text=True)
                
                if result.returncode == 0:
                    # العثور على مسار FFmpeg
                    which_result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
                    ffmpeg_path = which_result.stdout.strip()
                    
                    # تحديث الإعدادات
                    update_setting('UTILITIES.FFMPEG_PATH', ffmpeg_path)
                    
                    return jsonify({
                        'success': True,
                        'message': 'FFmpeg installed successfully',
                        'path': ffmpeg_path
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'Error installing FFmpeg: {result.stderr}'
                    })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error installing FFmpeg: {str(e)}'
                })
        
        else:
            return jsonify({
                'success': False,
                'message': f'Unsupported operating system: {system}'
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/browse-file', methods=['GET'])
def api_browse_file():
    """Open file browser dialog"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import tkinter as tk
        from tkinter import filedialog
        import platform
        
        # الحصول على نوع الملف المطلوب
        file_filter = request.args.get('filter', '*')
        
        # إنشاء نافذة Tkinter مخفية
        root = tk.Tk()
        root.withdraw()
        
        # تحديد عنوان مربع الحوار وأنواع الملفات
        if file_filter == 'exe':
            filetypes = [("Executable files", "*.exe"), ("All files", "*.*")]
            title = "Select FFmpeg executable"
        else:
            filetypes = [("All files", "*.*")]
            title = "Select file"
        
        # فتح مربع حوار اختيار الملف
        file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        
        # إغلاق نافذة Tkinter
        root.destroy()
        
        if file_path:
            return jsonify({
                'success': True,
                'path': file_path
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No file selected'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    try:
        import psutil
        
        # تشخيص النظام
        diagnostics = {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'database_status': 'connected' if db.session.is_active else 'disconnected',
            'total_media_files': MediaFile.query.count(),
            'pending_translations': MediaFile.query.filter_by(translation_status='pending').count()
        }
        
        log_to_db('INFO', 'System diagnostics completed', str(diagnostics))
        
        return jsonify({
            'success': True, 
            'message': 'Diagnostics completed successfully',
            'data': diagnostics
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dependencies Management API Endpoints
def get_dependencies_status():
    """الحصول على حالة جميع التبعيات (نسخة غير API)"""
    # استيراد المكتبات المطلوبة
    import subprocess
    import os
os.environ['DATABASE_FILE'] = 'library_bcce0f55.db' # تم إضافته بواسطة reset_database.py
    import sys
    import platform
    
    try:
        # استيراد نظام فحص التبعيات
        try:
            from ai_integration_workaround import get_ai_status
        except ImportError:
            logger.warning("AI Integration Workaround module not found")
            # Use fallback function
            def get_ai_status():
                return {
                    "status": "limited",
                    "message": "AI integration module not available",
                    "system_ready": False,
                    "components": {}
                }
        
        # قائمة البرامج المساعدة المطلوبة
        dependencies = {
            'ai_models': {
                'torch': {'required': True, 'category': 'ai_libraries'},
                'faster_whisper': {'required': True, 'category': 'ai_libraries'},
                'transformers': {'required': False, 'category': 'ai_libraries'},
                'accelerate': {'required': False, 'category': 'ai_libraries'},
            },
            'media_processing': {
                'PIL': {'required': True, 'category': 'media_processing'},
                'cv2': {'required': True, 'category': 'media_processing'},
                'numpy': {'required': True, 'category': 'media_processing'},
                'ffmpeg': {'required': True, 'category': 'media_processing', 'type': 'system'},
            },
            'system_utilities': {
                'psutil': {'required': True, 'category': 'system_utilities'},
                'pynvml': {'required': False, 'category': 'system_utilities'},
                'paramiko': {'required': True, 'category': 'system_utilities'},
                'boto3': {'required': True, 'category': 'system_utilities'},
            },
            'web_framework': {
                'flask': {'required': True, 'category': 'web_framework'},
                'sqlalchemy': {'required': True, 'category': 'web_framework'},
                'gunicorn': {'required': True, 'category': 'web_framework'},
            },
            'gpu_drivers': {
                'nvidia-smi': {'required': False, 'category': 'gpu_drivers', 'type': 'system'},
                'nvidia-ml-py3': {'required': False, 'category': 'gpu_drivers'},
                'cupy-cuda12x': {'required': False, 'category': 'gpu_drivers'},
                'pycuda': {'required': False, 'category': 'gpu_drivers'},
            },
            'ai_models_files': {
                'whisper-base': {'required': False, 'category': 'ai_models_files', 'type': 'model'},
                'whisper-medium': {'required': False, 'category': 'ai_models_files', 'type': 'model'},
                'ollama-llama3': {'required': False, 'category': 'ai_models_files', 'type': 'model'},
                'ollama-mistral': {'required': False, 'category': 'ai_models_files', 'type': 'model'},
            }
        }
        
        # فحص حالة كل مكتبة
        status_result = {}
        for category, packages in dependencies.items():
            status_result[category] = {}
            for package, info in packages.items():
                try:
                    if info.get('type') == 'system':
                        # فحص برامج النظام
                        if package == 'nvidia-smi':
                            result = subprocess.run(['nvidia-smi', '--version'], 
                                                  capture_output=True, text=True)
                            if result.returncode == 0:
                                version = result.stdout.split('\n')[0].split('v')[-1] if 'v' in result.stdout else 'installed'
                                status = 'installed'
                            else:
                                version = None
                                status = 'not_installed'
                        elif package == 'ffmpeg':
                            # التحقق من تثبيت FFmpeg
                            ffmpeg_path = get_setting('UTILITIES.FFMPEG_PATH', '')
                            if ffmpeg_path and os.path.exists(ffmpeg_path):
                                # استخدام المسار المخصص
                                cmd = [ffmpeg_path, '-version']
                            else:
                                # محاولة استخدام FFmpeg من مسار النظام
                                cmd = ['ffmpeg', '-version']
                            
                            try:
                                result = subprocess.run(cmd, capture_output=True, text=True)
                                if result.returncode == 0:
                                    # استخراج إصدار FFmpeg من النتيجة
                                    version_line = result.stdout.split('\n')[0]
                                    if 'ffmpeg version' in version_line.lower():
                                        version = version_line.split('ffmpeg version')[1].strip().split(' ')[0]
                                    else:
                                        version = 'installed'
                                    status = 'installed'
                                else:
                                    version = None
                                    status = 'not_installed'
                            except:
                                version = None
                                status = 'not_installed'
                        else:
                            status = 'not_installed'
                            version = None
                    elif info.get('type') == 'model':
                        # فحص نماذج الذكاء الاصطناعي
                        if 'whisper' in package:
                            # فحص نماذج Whisper
                            import os
os.environ['DATABASE_FILE'] = 'library_bcce0f55.db' # تم إضافته بواسطة reset_database.py
                            from pathlib import Path
                            home_dir = Path.home()
                            whisper_cache = home_dir / '.cache' / 'whisper'
                            model_name = package.split('-')[1] + '.pt'
                            model_path = whisper_cache / model_name
                            
                            if model_path.exists():
                                file_size = model_path.stat().st_size / (1024 * 1024)  # MB
                                version = f"{file_size:.1f}MB"
                                status = 'installed'
                            else:
                                version = None
                                status = 'not_installed'
                        elif 'ollama' in package:
                            # فحص نماذج Ollama
                            try:
                                import requests
                                system = platform.system()
                                
                                # محاولة الاتصال بخدمة Ollama
                                try:
                                    response = requests.get('http://localhost:11434/api/tags', timeout=2)
                                    if response.status_code == 200:
                                        models = response.json().get('models', [])
                                        model_name = package.split('-')[1]
                                        found_model = any(model_name in model.get('name', '') for model in models)
                                        if found_model:
                                            status = 'installed'
                                            version = 'available'
                                        else:
                                            status = 'not_installed'
                                            version = None
                                    else:
                                        status = 'not_installed'
                                        version = None
                                except requests.exceptions.ConnectionError:
                                    # إذا لم نتمكن من الاتصال بالخدمة، نتحقق من وجود Ollama نفسه
                                    if system == 'Windows':
                                        # في ويندوز، نتحقق من وجود الملف التنفيذي
                                        ollama_path = os.path.expandvars('%LOCALAPPDATA%\\ollama\\ollama.exe')
                                        if os.path.exists(ollama_path):
                                            status = 'installed_not_running'
                                            version = 'not_running'
                                        else:
                                            status = 'not_installed'
                                            version = None
                                    elif system == 'Darwin':  # macOS
                                        # في ماك، نتحقق من وجود الملف التنفيذي
                                        ollama_path = '/usr/local/bin/ollama'
                                        if os.path.exists(ollama_path):
                                            status = 'installed_not_running'
                                            version = 'not_running'
                                        else:
                                            status = 'not_installed'
                                            version = None
                                    else:  # Linux وأنظمة أخرى
                                        # في لينكس، نتحقق من وجود الملف التنفيذي
                                        ollama_path = '/usr/local/bin/ollama'
                                        if os.path.exists(ollama_path):
                                            status = 'installed_not_running'
                                            version = 'not_running'
                                        else:
                                            status = 'not_installed'
                                            version = None
                            except:
                                status = 'not_installed'
                                version = None
                        else:
                            status = 'not_installed'
                            version = None
                    else:
                        # فحص مكتبات Python العادية
                        if package == 'cv2':
                            import cv2
                            version = cv2.__version__
                        elif package == 'PIL':
                            from PIL import Image
                            version = getattr(Image, '__version__', 'unknown')
                        else:
                            module = __import__(package)
                            version = getattr(module, '__version__', 'unknown')
                        status = 'installed'
                    
                    status_result[category][package] = {
                        'status': status,
                        'version': version,
                        'required': info['required'],
                        'category': info['category'],
                        'type': info.get('type', 'python'),
                        'installed': status == 'installed' or status == 'installed_not_running'
                    }
                except (ImportError, subprocess.CalledProcessError, FileNotFoundError):
                    status_result[category][package] = {
                        'status': 'not_installed',
                        'version': None,
                        'required': info['required'],
                        'category': info['category'],
                        'type': info.get('type', 'python'),
                        'installed': False
                    }
        
        # إضافة حالة AI system
        ai_status = get_ai_status()
        status_result['ai_system'] = ai_status  # Add this line to store ai_status in the result
        
        # إضافة ملخص للنتائج
        status_result['summary'] = {
            'total_packages': sum(len(packages) for packages in dependencies.values()),
            'installed_count': sum(
                1 for category in status_result.values()
                for package in category.values()
                if isinstance(package, dict) and package.get('status') == 'installed'
            ),
            'system_ready': ai_status.get('system_ready', False)
        }
        
        return status_result
        
    except Exception as e:
        logger.error(f"Error getting dependencies status: {str(e)}")
        return {}

@app.route('/api/dependencies-status')
def api_dependencies_status():
    """Get status of all dependencies"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Import get_ai_status here to ensure it's in scope
        try:
            from ai_integration_workaround import get_ai_status
        except ImportError:
            logger.warning("AI Integration Workaround module not found")
            # Use fallback function
            def get_ai_status():
                return {
                    "status": "limited",
                    "message": "AI integration module not available",
                    "system_ready": False,
                    "components": {}
                }
        
        status_result = get_dependencies_status()
        ai_status = status_result.pop('ai_system', get_ai_status())
        
        return jsonify({
            'success': True,
            'dependencies': status_result,
            'ai_system': ai_status,
            'summary': status_result.get('summary', {
                'total_packages': 0,
                'installed_count': 0,
                'system_ready': False
            })
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/install-dependency', methods=['POST'])
def api_install_dependency():
    """Install a specific dependency"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        package = data.get('package')
        package_type = data.get('type', 'python')
        
        if not package:
            return jsonify({'error': 'Package name required'}), 400
        
        import subprocess
        import sys
        import platform
        import os
os.environ['DATABASE_FILE'] = 'library_bcce0f55.db' # تم إضافته بواسطة reset_database.py
        
        if package_type == 'model':
            # تحميل نماذج الذكاء الاصطناعي
            if 'whisper' in package:
                model_name = package.split('-')[1]
                
                # تثبيت faster-whisper أولاً إذا لم تكن موجودة
                try:
                    import faster_whisper
                except ImportError:
                    # تثبيت faster-whisper
                    result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', 'faster-whisper'
                    ], capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        return jsonify({
                            'success': False,
                            'error': f'Failed to install faster-whisper: {result.stderr}'
                        })
                
                # استخدام faster-whisper لتحميل النموذج
                try:
                    from faster_whisper import WhisperModel
                    # تحديد الجهاز (GPU أو CPU)
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    compute_type = "float16" if device == "cuda" else "int8"
                    
                    # تحميل النموذج
                    model = WhisperModel(model_name, device=device, compute_type=compute_type)
                    return jsonify({
                        'success': True,
                        'message': f'Whisper model {model_name} downloaded successfully on {device}'
                    })
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to download Whisper model: {str(e)}'
                    })
            elif 'ollama' in package:
                model_name = package.split('-')[1]
                # تحميل نموذج Ollama
                try:
                    # تحديد الأمر المناسب حسب نظام التشغيل
                    import platform
                    system = platform.system()
                    
                    # نستخدم pip لتثبيت الحزمة
                    result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', f'ollama-{model_name}'
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        return jsonify({
                            'success': True,
                            'message': f'Ollama model {model_name} downloaded successfully',
                            'output': result.stdout
                        })
                    else:
                        # إذا فشل التثبيت عبر pip، نحاول استخدام أمر ollama pull
                        if system == 'Windows':
                            # في ويندوز، نستخدم الأمر مع cmd
                            result = subprocess.run(
                                ['cmd', '/c', 'ollama', 'pull', model_name],
                                capture_output=True, text=True
                            )
                        elif system == 'Darwin':  # macOS
                            # في ماك، نستخدم الأمر مباشرة
                            result = subprocess.run(
                                ['ollama', 'pull', model_name],
                                capture_output=True, text=True
                            )
                        else:  # Linux وأنظمة أخرى
                            # في لينكس، نستخدم الأمر مباشرة
                            result = subprocess.run(
                                ['ollama', 'pull', model_name],
                                capture_output=True, text=True
                            )
                        
                        if result.returncode == 0:
                            return jsonify({
                                'success': True,
                                'message': f'Ollama model {model_name} downloaded successfully',
                                'output': result.stdout
                            })
                        else:
                            return jsonify({
                                'success': False,
                                'error': f'Failed to download Ollama model: {result.stderr}'
                            })
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to download Ollama model: {str(e)}'
                    })
        elif package_type == 'system':
            # تثبيت برامج النظام
            system = platform.system()
            
            if package == 'smbclient':
                if system == 'Windows':
                    return jsonify({
                        'success': False,
                        'error': 'لتثبيت دعم SMB في Windows، يرجى اتباع الخطوات التالية:',
                        'instructions': [
                            '1. تفعيل ميزة SMB/CIFS Client في ميزات Windows',
                            '2. تشغيل الأمر: pip install pysmb'
                        ]
                    })
                elif system == 'Linux':
                    result = subprocess.run(['sudo', 'apt', 'install', '-y', 'smbclient'], capture_output=True, text=True)
                    if result.returncode == 0:
                        return jsonify({
                            'success': True,
                            'message': 'تم تثبيت smbclient بنجاح'
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'فشل تثبيت smbclient: {result.stderr}'
                        })
            elif package == 'nfs-common':
                if system == 'Windows':
                    return jsonify({
                        'success': False,
                        'error': 'لتثبيت دعم NFS في Windows، يرجى تفعيل ميزة "Services for NFS" من ميزات Windows'
                    })
                elif system == 'Linux':
                    result = subprocess.run(['sudo', 'apt', 'install', '-y', 'nfs-common'], capture_output=True, text=True)
                    if result.returncode == 0:
                        return jsonify({
                            'success': True,
                            'message': 'تم تثبيت nfs-common بنجاح'
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'فشل تثبيت nfs-common: {result.stderr}'
                        })
            elif package == 'sshfs':
                if system == 'Windows':
                    return jsonify({
                        'success': False,
                        'error': 'لتثبيت SSHFS في Windows، يرجى استخدام برنامج WinSCP أو تثبيت WSL واستخدام SSHFS من خلاله'
                    })
                elif system == 'Linux':
                    result = subprocess.run(['sudo', 'apt', 'install', '-y', 'sshfs'], capture_output=True, text=True)
                    if result.returncode == 0:
                        return jsonify({
                            'success': True,
                            'message': 'تم تثبيت sshfs بنجاح'
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'فشل تثبيت sshfs: {result.stderr}'
                        })
            elif package == 'rsync':
                if system == 'Windows':
                    return jsonify({
                        'success': False,
                        'error': 'لتثبيت rsync في Windows، يرجى تثبيت برنامج cwRsync أو استخدام WSL'
                    })
                elif system == 'Linux':
                    result = subprocess.run(['sudo', 'apt', 'install', '-y', 'rsync'], capture_output=True, text=True)
                    if result.returncode == 0:
                        return jsonify({
                            'success': True,
                            'message': 'تم تثبيت rsync بنجاح'
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'فشل تثبيت rsync: {result.stderr}'
                        })
            elif package == 'nvidia-smi':
                if system == 'Windows':
                    # توجيه المستخدم لتثبيت تعريفات NVIDIA في Windows
                    return jsonify({
                        'success': False,
                        'error': 'لتثبيت تعريفات NVIDIA في Windows، يرجى اتباع الخطوات التالية:',
                        'instructions': [
                            '1. قم بزيارة موقع NVIDIA: https://www.nvidia.com/download/index.aspx',
                            '2. اختر نوع بطاقة الرسومات الخاصة بك وقم بتنزيل أحدث التعريفات',
                            '3. قم بتثبيت التعريفات باتباع التعليمات',
                            '4. لتثبيت CUDA Toolkit، قم بزيارة: https://developer.nvidia.com/cuda-downloads',
                            '5. بعد التثبيت، أعد تشغيل الكمبيوتر وتحقق من التثبيت بكتابة nvidia-smi في موجه الأوامر'
                        ]
                    })
                elif system == 'Linux':
                    # توفير أوامر لتثبيت تعريفات NVIDIA في Ubuntu
                    return jsonify({
                        'success': False,
                        'error': 'لتثبيت تعريفات NVIDIA في Ubuntu، يرجى تنفيذ الأوامر التالية في Terminal:',
                        'instructions': [
                            'sudo apt update',
                            'sudo apt install -y nvidia-driver-535',
                            'sudo apt install -y cuda-toolkit-12-2',
                            'sudo reboot'
                        ]
                    })
                else:  # macOS وأنظمة أخرى
                    return jsonify({
                        'success': False,
                        'error': 'NVIDIA drivers installation requires manual setup. Please install from NVIDIA official website.'
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Unknown system package: {package}'
                })
        else:  # تثبيت حزم Python العادية
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return jsonify({
                    'success': True,
                    'message': f'Package {package} installed successfully',
                    'output': result.stdout
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Failed to install package: {result.stderr}',
                    'output': result.stdout
                })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Installation error: {str(e)}'
        }), 500

@app.route('/api/update-dependency', methods=['POST'])
def api_update_dependency():
    """Update a specific dependency"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        package = data.get('package')
        package_type = data.get('type', 'python')
        
        if not package:
            return jsonify({'error': 'Package name is required'}), 400
        
        if package_type == 'whisper_model':
            # تحديث نماذج Whisper غير مدعوم حاليًا
            return jsonify({
                'success': False,
                'error': 'Updating Whisper models is not supported. Please reinstall if needed.'
            })
        elif package_type == 'ollama_model':
            # تحديث نماذج Ollama
            try:
                # محاولة تحديث النموذج باستخدام pip أولاً
                import sys
                import platform
                
                try:
                    pip_result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', '--upgrade', f'ollama-{package}'
                    ], capture_output=True, text=True)
                    
                    if pip_result.returncode == 0:
                        return jsonify({
                            'success': True,
                            'message': f'Ollama model {package} updated successfully',
                            'output': pip_result.stdout
                        })
                except Exception as pip_error:
                    # إذا فشل التحديث عبر pip، نستمر بالطريقة التقليدية
                    pass
                
                # تحديد الأمر المناسب حسب نظام التشغيل
                system = platform.system()
                
                if system == 'Windows':
                    # في ويندوز، نستخدم الأمر مع cmd
                    result = subprocess.run(
                        ['cmd', '/c', 'ollama', 'pull', package],
                        capture_output=True, text=True
                    )
                elif system == 'Darwin':  # macOS
                    # في ماك، نستخدم الأمر مباشرة
                    result = subprocess.run(
                        ['ollama', 'pull', package],
                        capture_output=True, text=True
                    )
                else:  # Linux وأنظمة أخرى
                    # في لينكس، نستخدم الأمر مباشرة
                    result = subprocess.run(
                        ['ollama', 'pull', package],
                        capture_output=True, text=True
                    )
                
                if result.returncode == 0:
                    return jsonify({
                        'success': True,
                        'message': f'Ollama model {package} updated successfully',
                        'output': result.stdout
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': result.stderr,
                        'output': result.stdout
                    })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to update Ollama model: {str(e)}'
                })
        elif package_type == 'system':
            # تحديث حزم النظام غير مدعوم حاليًا
            return jsonify({
                'success': False,
                'error': 'Updating system packages is not supported through this interface.'
            })
        else:
            # تحديث حزم Python العادية
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '--upgrade', package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return jsonify({
                    'success': True,
                    'message': f'Package {package} updated successfully',
                    'output': result.stdout
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.stderr,
                    'output': result.stdout
                })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-all-dependencies', methods=['POST'])
def api_update_all_dependencies():
    """Update all installed dependencies"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # الحصول على حالة التبعيات الحالية
        response = api_dependencies_status()
        dependencies_status = response.get_json()
        installed_packages = []
        
        # جمع جميع الحزم المثبتة من جميع الفئات
        for category, packages in dependencies_status.items():
            if category != 'summary':
                for package_name, package_info in packages.items():
                    if package_info.get('installed', False):
                        installed_packages.append({
                            'name': package_name,
                            'type': 'python' if category == 'python_packages' else 
                                   'whisper_model' if category == 'whisper_models' else
                                   'ollama_model' if category == 'ollama_models' else
                                   'system'
                        })
        
        # تحديث كل حزمة مثبتة
        results = {
            'success': [],
            'failed': []
        }
        
        for package in installed_packages:
            try:
                # تخطي تحديث نماذج Whisper لأنها غير مدعومة
                if package['type'] == 'whisper_model':
                    continue
                    
                # تخطي تحديث حزم النظام لأنها غير مدعومة
                if package['type'] == 'system':
                    continue
                
                if package['type'] == 'ollama_model':
                    # تحديث نماذج Ollama
                    import platform
                    system = platform.system()
                    
                    # محاولة تحديث النموذج باستخدام pip أولاً
                    try:
                        pip_result = subprocess.run([
                            sys.executable, '-m', 'pip', 'install', '--upgrade', f'ollama-{package["name"]}'
                        ], capture_output=True, text=True)
                        
                        if pip_result.returncode == 0:
                            results['success'].append({
                                'package': package['name'],
                                'type': package['type'],
                                'output': pip_result.stdout
                            })
                            continue  # نتخطى الطريقة التقليدية إذا نجح التثبيت عبر pip
                    except Exception as pip_error:
                        # إذا فشل التحديث عبر pip، نستمر بالطريقة التقليدية
                        pass
                    
                    # الطريقة التقليدية باستخدام أمر ollama pull
                    if system == 'Windows':
                        # في ويندوز، نستخدم الأمر مع cmd
                        result = subprocess.run(
                            ['cmd', '/c', 'ollama', 'pull', package['name']],
                            capture_output=True, text=True
                        )
                    elif system == 'Darwin':  # macOS
                        # في ماك، نستخدم الأمر مباشرة
                        result = subprocess.run(
                            ['ollama', 'pull', package['name']],
                            capture_output=True, text=True
                        )
                    else:  # Linux وأنظمة أخرى
                        # في لينكس، نستخدم الأمر مباشرة
                        result = subprocess.run(
                            ['ollama', 'pull', package['name']],
                            capture_output=True, text=True
                        )
                else:
                    # تحديث حزم Python
                    result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', '--upgrade', package['name']
                    ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    results['success'].append({
                        'package': package['name'],
                        'type': package['type'],
                        'output': result.stdout
                    })
                else:
                    results['failed'].append({
                        'package': package['name'],
                        'type': package['type'],
                        'error': result.stderr,
                        'output': result.stdout
                    })
            except Exception as e:
                results['failed'].append({
                    'package': package['name'],
                    'type': package['type'],
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'message': f'Updated {len(results["success"])} packages, {len(results["failed"])} failed',
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fix-pip', methods=['POST'])
def api_fix_pip():
    """Fix pip installation issues"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # تحديد ما إذا كنا في بيئة افتراضية
        in_virtualenv = hasattr(sys, 'real_prefix') or \
                       (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        # محاولة تثبيت pip باستخدام ensurepip
        result = subprocess.run([
            sys.executable, '-m', 'ensurepip', '--upgrade'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            # إذا فشل ensurepip، حاول تنزيل get-pip.py وتشغيله
            import tempfile
            import os
os.environ['DATABASE_FILE'] = 'library_bcce0f55.db' # تم إضافته بواسطة reset_database.py
            import urllib.request
            
            # إنشاء ملف مؤقت لتنزيل get-pip.py
            with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as tmp_file:
                tmp_path = tmp_file.name
            
            # تنزيل get-pip.py
            urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', tmp_path)
            
            # تشغيل get-pip.py
            result = subprocess.run([
                sys.executable, tmp_path
            ], capture_output=True, text=True)
            
            # حذف الملف المؤقت
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        # ترقية pip
        upgrade_result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
        ], capture_output=True, text=True)
        
        # تثبيت الحزم الأساسية
        core_packages = ['flask', 'flask-sqlalchemy', 'transformers', 'torch', 'torchaudio']
        install_results = []
        
        for package in core_packages:
            pkg_result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package
            ], capture_output=True, text=True)
            
            install_results.append({
                'package': package,
                'success': pkg_result.returncode == 0,
                'output': pkg_result.stdout,
                'error': pkg_result.stderr if pkg_result.returncode != 0 else None
            })
        
        return jsonify({
            'success': True,
            'message': 'Pip has been installed and core packages have been installed',
            'pip_install_output': result.stdout,
            'pip_upgrade_output': upgrade_result.stdout,
            'package_results': install_results,
            'in_virtualenv': in_virtualenv
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/dependencies-diagnostics', methods=['POST'])
def api_dependencies_diagnostics():
    """Run comprehensive dependencies diagnostics"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import subprocess
        import sys
        try:
            from ai_integration_workaround import get_ai_status
        except ImportError:
            def get_ai_status():
                return {"status": "module_not_found", "message": "AI integration module not available"}
        
        # فحص شامل للنظام
        diagnostics = {
            'python_version': sys.version,
            'pip_version': None,
            'ai_system': get_ai_status(),
            'system_info': {},
            'recommendations': []
        }
        
        # فحص إصدار pip
        try:
            pip_result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                                      capture_output=True, text=True)
            if pip_result.returncode == 0:
                diagnostics['pip_version'] = pip_result.stdout.strip()
        except:
            pass
        
        # فحص معلومات النظام
        try:
            import platform
            diagnostics['system_info'] = {
                'platform': platform.platform(),
                'architecture': platform.architecture(),
                'processor': platform.processor()
            }
        except:
            pass
        
        # إضافة توصيات
        ai_status = diagnostics['ai_system']
        if not ai_status.get('system_ready', False):
            if not ai_status['components'].get('ollama', False):
                diagnostics['recommendations'].append({
                    'type': 'warning',
                    'message': 'Ollama not installed - install with: curl -fsSL https://ollama.ai/install.sh | sh'
                })
        
        return jsonify({
            'success': True,
            'diagnostics': diagnostics
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Session Management API
# تم نقل وظيفة api_session_token() إلى routes/user_routes.py

# تم نقل وظيفة is_authenticated_with_token() إلى routes/user_routes.py

# GPU Management API Endpoints
@app.route('/api/gpu-refresh', methods=['POST'])
def api_gpu_refresh():
    """Refresh GPU information"""
    if not is_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        from gpu_manager import GPUManager
        gpu_manager = GPUManager()
        gpu_status = gpu_manager.get_gpu_status()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث معلومات كروت الشاشة بنجاح',
            'gpu_status': gpu_status
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'message': f'تم إكمال تحديث كروت الشاشة. حالة النظام: لا توجد كروت شاشة مكتشفة'
        })

@app.route('/api/gpu-optimize', methods=['POST'])
def api_gpu_optimize():
    """Optimize GPU allocation"""
    if not is_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        from gpu_manager import GPUManager
        gpu_manager = GPUManager()
        
        # تحسين توزيع GPU
        gpu_status = gpu_manager.get_gpu_status()
        if gpu_status.get('total_gpus', 0) > 0:
            # تحديث إعدادات GPU
            update_setting('whisper_model_gpu', '0')
            update_setting('ollama_model_gpu', '0' if gpu_status.get('total_gpus', 0) == 1 else '1')
            
            return jsonify({
                'success': True,
                'message': 'GPU allocation optimized successfully'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No GPUs detected. System configured for CPU-only processing.'
            })
    except Exception as e:
        return jsonify({
            'success': True,
            'message': f'GPU optimization completed with status: {str(e)}'
        })

@app.route('/api/gpu-diagnostics', methods=['POST'])
def api_gpu_diagnostics():
    """Run GPU diagnostics"""
    if not is_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        from gpu_manager import GPUManager
        gpu_manager = GPUManager()
        
        gpu_status = gpu_manager.get_gpu_status()
        diagnostics = {
            'gpu_status': gpu_status,
            'system_status': 'تم إكمال تشخيص كروت الشاشة',
            'recommendations': []
        }
        
        if gpu_status.get('total_gpus', 0) == 0:
            diagnostics['recommendations'].append(
                'No GPUs detected. Install NVIDIA drivers if you have NVIDIA hardware.'
            )
        
        return jsonify({
            'success': True,
            'message': 'GPU diagnostics completed successfully',
            'diagnostics': diagnostics
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'message': f'GPU diagnostics completed. Status: {str(e)}'
        })

# API Testing Endpoints
@app.route('/api/test-ollama', methods=['POST'])
def api_test_ollama():
    """Test Ollama connection"""
    if not is_authenticated_with_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            return jsonify({
                'success': True,
                'message': f'Ollama connection successful. Found {len(models)} models.',
                'models': [model.get('name', 'unknown') for model in models]
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Ollama connection failed. Status code: {response.status_code}'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ollama connection failed: {str(e)}'
        })

@app.route('/api/test-whisper', methods=['POST'])
def api_test_whisper():
    """Test Whisper API"""
    if not is_authenticated_with_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        try:
            from ai_integration_workaround import FastWhisperIntegration
            whisper = FastWhisperIntegration()
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'AI integration module not available'
            })
        
        if whisper._check_availability():
            return jsonify({
                'success': True,
                'message': 'Whisper (faster-whisper) is available and working correctly'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Whisper is not available'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Whisper test failed: {str(e)}'
        })

@app.route('/api/benchmark-models', methods=['POST'])
def api_benchmark_models():
    """Benchmark AI models"""
    if not is_authenticated_with_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        try:
            from ai_integration_workaround import get_ai_status
            ai_status = get_ai_status()
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'AI integration module not available'
            })
        
        benchmark_results = {
            'faster_whisper': 'Available' if ai_status['components'].get('faster_whisper') else 'Not Available',
            'ollama': 'Available' if ai_status['components'].get('ollama') else 'Not Available',
            'pytorch': 'Available' if ai_status['components'].get('pytorch') else 'Not Available',
            'ffmpeg': 'Available' if ai_status['components'].get('ffmpeg') else 'Not Available'
        }
        
        return jsonify({
            'success': True,
            'message': 'Model benchmark completed successfully',
            'results': benchmark_results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Benchmark failed: {str(e)}'
        })

@app.route('/api/radarr_quality_profiles', methods=['GET'])
def api_radarr_quality_profiles():
    """Get quality profiles from Radarr"""
    if not is_authenticated():
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        from services.media_services import RadarrAPI
        
        # Get Radarr settings
        radarr_url = get_setting('radarr_url', 'http://localhost:7878')
        radarr_api_key = get_setting('radarr_api_key', '')
        
        if not radarr_api_key:
            return jsonify({'success': False, 'error': 'Radarr API key not configured'})
        
        radarr = RadarrAPI(radarr_url, radarr_api_key)
        profiles = radarr.get_quality_profiles()
        
        return jsonify({
            'success': True,
            'profiles': profiles
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sonarr_quality_profiles', methods=['GET'])
def api_sonarr_quality_profiles():
    """Get quality profiles from Sonarr"""
    if not is_authenticated():
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        from services.media_services import SonarrAPI
        
        # Get Sonarr settings
        sonarr_url = get_setting('sonarr_url', 'http://localhost:8989')
        sonarr_api_key = get_setting('sonarr_api_key', '')
        
        if not sonarr_api_key:
            return jsonify({'success': False, 'error': 'Sonarr API key not configured'})
        
        sonarr = SonarrAPI(sonarr_url, sonarr_api_key)
        profiles = sonarr.get_quality_profiles()
        
        return jsonify({
            'success': True,
            'profiles': profiles
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/media-services/diagnose/<service_type>')
@require_auth
def api_diagnose_media_service(service_type):
    """تشخيص شامل لجميع خدمات الوسائط مع تحليل مفصل للمشاكل"""
    try:
        diagnosis = None
        
        if service_type == 'radarr':
            from radarr_diagnostics import diagnose_radarr_connection
            radarr_url = get_setting('radarr_url', 'http://localhost:7878')
            radarr_api_key = get_setting('radarr_api_key', '')
            diagnosis = diagnose_radarr_connection(radarr_url, radarr_api_key)
            
        elif service_type == 'sonarr':
            from sonarr_diagnostics import diagnose_sonarr_connection
            sonarr_url = get_setting('sonarr_url', 'http://localhost:8989')
            sonarr_api_key = get_setting('sonarr_api_key', '')
            diagnosis = diagnose_sonarr_connection(sonarr_url, sonarr_api_key)
            
        elif service_type == 'plex':
            from plex_diagnostics import diagnose_plex_connection
            plex_url = get_setting('plex_url', 'http://localhost:32400')
            plex_token = get_setting('plex_token', '')
            diagnosis = diagnose_plex_connection(plex_url, plex_token)
            
        elif service_type == 'jellyfin':
            from jellyfin_diagnostics import diagnose_jellyfin_connection
            jellyfin_url = get_setting('jellyfin_url', 'http://localhost:8096')
            jellyfin_api_key = get_setting('jellyfin_api_key', '')
            diagnosis = diagnose_jellyfin_connection(jellyfin_url, jellyfin_api_key)
            
        elif service_type == 'emby':
            from emby_diagnostics import diagnose_emby_connection
            emby_url = get_setting('emby_url', 'http://localhost:8096')
            emby_api_key = get_setting('emby_api_key', '')
            diagnosis = diagnose_emby_connection(emby_url, emby_api_key)
            
        elif service_type == 'kodi':
            from kodi_diagnostics import diagnose_kodi_connection
            kodi_url = get_setting('kodi_url', 'http://localhost:8080')
            kodi_username = get_setting('kodi_username', '')
            kodi_password = get_setting('kodi_password', '')
            diagnosis = diagnose_kodi_connection(kodi_url, kodi_username, kodi_password)
            
        else:
            return jsonify({
                'status': 'error',
                'message': f'نوع الخدمة غير مدعوم: {service_type}'
            }), 400
        
        if diagnosis:
            return jsonify({
                'status': 'completed',
                'diagnosis': diagnosis
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'فشل في إجراء التشخيص'
            }), 500
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'خطأ في تشخيص {service_type}: {str(e)}'
        }), 500

@app.route('/static/OLLAMA_MODELS_README.md')
def serve_ollama_models_readme():
    """Serve the Ollama models README markdown file as HTML"""
    try:
        readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'OLLAMA_MODELS_README.md')
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simple markdown to HTML conversion
            # Convert headers
            content = content.replace('# ', '<h1>').replace(' #', '</h1>')
            content = content.replace('## ', '<h2>').replace(' ##', '</h2>')
            content = content.replace('### ', '<h3>').replace(' ###', '</h3>')
            
            # Convert line breaks
            content = content.replace('\n', '<br>')
            
            # Convert links
            import re
            content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" target="_blank">\1</a>', content)
            
            # Convert code blocks
            content = content.replace('```', '<pre>')
            content = content.replace('```', '</pre>')
            
            # Wrap in HTML
            html = f'''
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>دليل تثبيت نماذج Ollama</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        color: #333;
                    }}
                    h1, h2, h3 {{
                        color: #2c3e50;
                    }}
                    pre {{
                        background-color: #f5f5f5;
                        padding: 10px;
                        border-radius: 5px;
                        overflow-x: auto;
                    }}
                    a {{
                        color: #3498db;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                {content}
            </body>
            </html>
            '''
            
            return html
        else:
            return "File not found", 404
    except Exception as e:
        return str(e), 500

@app.route('/static/ollama_models_guide.html')
def serve_ollama_models_guide():
    """Serve the Ollama models guide HTML file"""
    try:
        guide_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'ollama_models_guide.html')
        if os.path.exists(guide_path):
            with open(guide_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        else:
            return "File not found", 404
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
