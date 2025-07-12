from flask import Blueprint, jsonify, request
from models import Notification, db
from utils.auth import is_authenticated, get_user_language
from translations import get_translation  # تصحيح الاستيراد من translations بدلاً من utils.settings
import json

# إنشاء Blueprint للإشعارات
notifications_bp = Blueprint('notifications', __name__)


def create_notification(title_key, message_key, notification_type='info', **kwargs):
    """Create a new notification with translation support"""
    try:
        # Store translation keys instead of translated text
        notification = Notification()
        notification.title = title_key  # Store the translation key
        notification.message = message_key  # Store the translation key with parameters
        notification.type = notification_type
        
        # Store translation parameters as JSON if any
        if kwargs:
            notification.translation_params = json.dumps(kwargs)
        
        db.session.add(notification)
        db.session.commit()
        return True
    except Exception as e:
        from app import log_to_db
        log_to_db("ERROR", "Failed to create notification", str(e))
        return False


@notifications_bp.route('/api/notifications')
def api_notifications():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    notifications = Notification.query.order_by(Notification.created_at.desc()).all()
    user_language = get_user_language()
    
    notifications_data = []
    for notification in notifications:
        # Translate title and message
        translated_title = get_translation(notification.title, user_language)
        translated_message = get_translation(notification.message, user_language)
        
        # Apply translation parameters if they exist
        if notification.translation_params:
            try:
                params = json.loads(notification.translation_params)
                translated_message = translated_message.format(**params)
            except:
                pass  # Use message as is if formatting fails
        
        notifications_data.append({
            'id': notification.id,
            'title': translated_title,
            'message': translated_message,
            'type': notification.type,
            'read': notification.read,
            'created_at': notification.created_at.isoformat() if notification.created_at else None
        })
    
    return jsonify(notifications_data)


@notifications_bp.route('/api/notifications/count')
def api_notifications_count():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    count = Notification.query.filter_by(read=False).count()
    return jsonify({'count': count})


@notifications_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def api_mark_notification_read(notification_id):
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    notification = Notification.query.get_or_404(notification_id)
    notification.read = True
    db.session.commit()
    
    return jsonify({'success': True})


@notifications_bp.route('/api/notifications/<int:notification_id>/delete', methods=['POST'])
def api_delete_notification(notification_id):
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    notification = Notification.query.get_or_404(notification_id)
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'success': True})


@notifications_bp.route('/api/notifications/mark-all-read', methods=['POST'])
def api_mark_all_notifications_read():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    Notification.query.filter_by(read=False).update({'read': True})
    db.session.commit()
    
    return jsonify({'success': True})


@notifications_bp.route('/api/notifications/clear-all', methods=['POST'])
def api_clear_all_notifications():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    Notification.query.delete()
    db.session.commit()
    
    return jsonify({'success': True})


def get_unread_notifications():
    """Get unread notifications count"""
    return Notification.query.filter_by(read=False).count()