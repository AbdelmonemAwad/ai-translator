"""
Services package for AI Translator
حزمة الخدمات للترجمان الآلي
"""

from .remote_storage import RemoteStorageManager, setup_remote_mount, get_mount_status

__all__ = ['RemoteStorageManager', 'setup_remote_mount', 'get_mount_status']