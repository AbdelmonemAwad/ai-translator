#!/usr/bin/env python3
"""
وحدة إدارة الإعدادات للترجمان الآلي
"""

import logging
from datetime import datetime
from models import Settings, db
from contextlib import contextmanager

logger = logging.getLogger(__name__)

def get_settings():
    """الحصول على جميع الإعدادات كقاموس"""
    settings = {}
    for setting in Settings.query.all():
        settings[setting.key] = setting.value
    return settings

@contextmanager
def db_session_context():
    try:
        yield db.session
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise
    finally:
        db.session.close()

def get_setting(key, default=None):
    """الحصول على قيمة إعداد محدد"""
    max_retries = 5
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        try:
            with db_session_context() as session:
                setting = Settings.query.filter_by(key=key).first()
                return setting.value if setting else default
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Retry {attempt+1}/{max_retries} getting setting {key}: {str(e)}")
                time.sleep(retry_delay)
            else:
                logger.error(f"Error getting setting {key} after {max_retries} attempts: {str(e)}")
                return default

def update_setting(key, value):
    """تحديث أو إنشاء إعداد"""
    try:
        setting = Settings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = Settings()
            setting.key = key
            setting.value = value
            # Set default section if not specified
            if not hasattr(setting, 'section') or not setting.section:
                setting.section = 'DEFAULT'
            db.session.add(setting)
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating setting {key}: {str(e)}")
        db.session.rollback()
        return False

def is_development_feature_enabled(feature_key):
    """التحقق مما إذا كانت ميزة التطوير ممكّنة"""
    value = get_setting(feature_key, 'false')
    return value.lower() in ['true', '1', 'yes']

# ... باقي وظائف الإعدادات