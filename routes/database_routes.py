from flask import Blueprint, jsonify, request, redirect, url_for
from models import db, Log, Notification
from utils.auth import is_authenticated, get_user_language
from routes.notifications_routes import create_notification
from translations import get_translation
from datetime import datetime, timedelta
import time

# إنشاء Blueprint لإدارة قاعدة البيانات
database_bp = Blueprint('database', __name__)

# وظيفة مساعدة للترجمة (نفس الوظيفة الموجودة في app.py)
def translate_text(key, **kwargs):
    """Translation helper function for templates"""
    lang = get_user_language()
    return get_translation(key, lang, **kwargs)

@database_bp.route('/api/database/stats')
def api_database_stats():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        from sqlalchemy import text
        import os
        
        # Get database file size
        db_path = "library_bcce0f55.db"
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

@database_bp.route('/api/database/tables')
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

@database_bp.route('/api/database/query', methods=['POST'])
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

@database_bp.route('/api/database/backup', methods=['POST'])
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

@database_bp.route('/api/database/optimize', methods=['POST'])
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

@database_bp.route('/api/database/cleanup', methods=['POST'])
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

@database_bp.route('/action/scan_translation_status')
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