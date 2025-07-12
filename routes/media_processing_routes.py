#!/usr/bin/env python3
"""
مسارات ودوال معالجة الوسائط
"""

import os
import sys
import json
import logging
import psutil
import requests
import subprocess
from flask import Blueprint, jsonify, request, session, redirect, url_for
from models import MediaFile, db
from routes.logs_routes import log_to_db

logger = logging.getLogger(__name__)

# تعريف البلوبرنت
media_processing_bp = Blueprint('media_processing', __name__)

# تعريف المتغيرات العامة
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS_FILE = os.path.join(PROJECT_DIR, "status.json")

def get_supported_video_formats():
    """Get list of supported video formats from database"""
    try:
        from models import VideoFormat
        formats = VideoFormat.query.filter_by(supported=True).all()
        return [fmt.extension.lower() for fmt in formats]
    except Exception as e:
        # Fallback to default formats if database is not available
        log_to_db("WARNING", f"Could not load video formats from database: {str(e)}")
        default_formats = 'mp4,mkv,avi,mov,m4v,wmv,flv,webm,ts,mts,m2ts,3gp,ogv,vob,asf,rm,rmvb'
        return [fmt.strip().lower() for fmt in default_formats.split(',')]

def is_video_file_supported(file_path):
    """Check if video file format is supported"""
    if not file_path:
        return False
    
    file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    supported_formats = get_supported_video_formats()
    return file_ext in supported_formats

def download_thumbnail(url, media_file_id):
    """Download and save thumbnail for media file"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Save thumbnail data to database
            media_file = MediaFile.query.get(media_file_id)
            if media_file:
                media_file.thumbnail_data = response.content
                media_file.thumbnail_url = url
                db.session.commit()
                return True
    except Exception as e:
        log_to_db("ERROR", f"Failed to download thumbnail: {url}", str(e))
    return False

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
    from utils.settings import get_settings
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

def is_task_running():
    """Check if any background task is running"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            cmdline = proc.info['cmdline']
            if cmdline and any('background_tasks.py' in arg for arg in cmdline):
                return True
    except:
        pass
    return False

def run_background_task(task_name, *args):
    """Run a background task"""
    if is_task_running():
        return False, "مهمة أخرى قيد التشغيل حالياً"
    
    try:
        cmd = [sys.executable, 'background_tasks.py', task_name] + list(args)
        subprocess.Popen(cmd, cwd=PROJECT_DIR)
        log_to_db("INFO", f"Started background task: {task_name}")
        return True, f"تم بدء المهمة: {task_name}"
    except Exception as e:
        log_to_db("ERROR", f"Failed to start task: {task_name}", str(e))
        return False, f"فشل في بدء المهمة: {str(e)}"

# مسارات API المتعلقة بمعالجة الوسائط
@media_processing_bp.route('/api/status')
def api_status():
    """Get current processing status"""
    return jsonify(get_current_status())

@media_processing_bp.route('/api/start-task/<task_name>', methods=['POST'])
def api_start_task(task_name):
    """Start a background task"""
    args = request.json.get('args', [])
    success, message = run_background_task(task_name, *args)
    return jsonify({'success': success, 'message': message})