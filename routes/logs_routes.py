#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسارات السجلات - AI Translator
Logs Routes - AI Translator
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from models import Log, TranslationLog, db
from utils.auth import is_authenticated

# إنشاء Blueprint لمسارات السجلات
logs_bp = Blueprint('logs', __name__)

# تعريف المتغيرات العامة
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESS_LOG_FILE = os.path.join(PROJECT_DIR, "process.log")
APP_LOG_FILE = os.path.join(PROJECT_DIR, "app.log")

# دالة مساعدة لتسجيل الرسائل في قاعدة البيانات
def log_to_db(level, message, details=""):
    """Log message to database"""
    try:
        log_entry = Log()
        log_entry.level = level
        log_entry.message = message
        log_entry.details = details
        log_entry.source = "web_app"
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Failed to log to database: {e}")

@logs_bp.route('/api/get_log')
def api_get_log():
    log_type = request.args.get('type', 'app')
    lines = int(request.args.get('lines', 100))
    
    try:
        # Get logs from database first
        log_entries = Log.query.order_by(Log.created_at.desc()).limit(lines).all()
        
        if log_entries:
            log_content = []
            for entry in reversed(log_entries):  # Show oldest first
                timestamp = entry.created_at.strftime('%Y-%m-%d %H:%M:%S')
                log_line = f"[{timestamp}] {entry.level}: {entry.message}"
                if entry.details:
                    log_line += f" - {entry.details}"
                log_content.append(log_line)
            
            return jsonify({'content': '\n'.join(log_content)})
        
        # If no database logs, try file logs
        if log_type == 'process':
            log_file = PROCESS_LOG_FILE
        else:
            log_file = APP_LOG_FILE
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.readlines()
                if len(content) > lines:
                    content = content[-lines:]
                return jsonify({'content': ''.join(content)})
        
        return jsonify({'content': 'لا توجد سجلات'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@logs_bp.route('/api/clear_log', methods=['POST'])
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

@logs_bp.route('/api/delete_selected_logs', methods=['POST'])
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

@logs_bp.route('/api/translation_logs', methods=['GET'])
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

@logs_bp.route('/api/clear_sample_translation_logs', methods=['POST'])
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

@logs_bp.route('/api/create_sample_translation_logs', methods=['POST'])
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
            # Create a new TranslationLog entry
            log = TranslationLog()
            for key, value in log_data.items():
                if hasattr(log, key):
                    setattr(log, key, value)
            
            db.session.add(log)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'تم إنشاء {len(sample_logs)} سجل تجريبي'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


def log_to_file(message):
    """Log message to file"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(APP_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Failed to log to file: {e}")

def log_translation_event(file_path, file_name, status, progress=0.0, error_message=None, details=None, **kwargs):
    """Log translation event to database"""
    try:
        # Check if log already exists for this file
        existing_log = TranslationLog.query.filter_by(file_path=file_path).first()
        
        if existing_log:
            # Update existing log
            existing_log.status = status
            existing_log.progress = progress
            existing_log.error_message = error_message
            existing_log.details = details
            existing_log.updated_at = datetime.utcnow()
            
            # Update other fields if provided
            for key, value in kwargs.items():
                if hasattr(existing_log, key) and value is not None:
                    setattr(existing_log, key, value)
            
            if status in ['success', 'failed']:
                existing_log.completed_at = datetime.utcnow()
        else:
            # Create new log
            new_log = TranslationLog()
            new_log.file_path = file_path
            new_log.file_name = file_name
            new_log.status = status
            new_log.progress = progress
            new_log.error_message = error_message
            new_log.details = details
            
            # Set additional fields
            for key, value in kwargs.items():
                if hasattr(new_log, key) and value is not None:
                    setattr(new_log, key, value)
            db.session.add(new_log)
        
        db.session.commit()
        log_to_db("INFO", f"سجل الترجمة: {file_name} - {status}")
        
    except Exception as e:
        log_to_db("ERROR", f"خطأ في تسجيل حدث الترجمة: {str(e)}")
        db.session.rollback()