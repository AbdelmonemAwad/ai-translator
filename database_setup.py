#!/usr/bin/env python3
"""
Database Setup for AI Translator
إعداد قاعدة البيانات للترجمان الآلي
"""

import os
import sys
from models import db, Settings

def create_default_settings():
    """إنشاء الإعدادات الافتراضية"""
    
    default_settings = [
        # DEFAULT section
        {'key': 'admin_username', 'value': 'admin', 'section': 'DEFAULT', 'type': 'string', 'description': 'Admin username'},
        {'key': 'admin_password', 'value': 'your_strong_password', 'section': 'DEFAULT', 'type': 'password', 'description': 'Admin password'},
        {'key': 'user_language', 'value': 'ar', 'section': 'DEFAULT', 'type': 'select', 'options': 'ar:العربية,en:English', 'description': 'User interface language'},
        {'key': 'user_theme', 'value': 'dark', 'section': 'DEFAULT', 'type': 'select', 'options': 'dark:داكن,light:فاتح,system:النظام', 'description': 'User interface theme'},
        {'key': 'items_per_page', 'value': '24', 'section': 'DEFAULT', 'type': 'select', 'options': '12:12,24:24,48:48,96:96', 'description': 'Number of items per page'},
        
        # API section
        {'key': 'sonarr_url', 'value': 'http://localhost:8989', 'section': 'API', 'type': 'string', 'description': 'Sonarr server URL'},
        {'key': 'sonarr_api_key', 'value': '', 'section': 'API', 'type': 'string', 'description': 'Sonarr API key'},
        {'key': 'radarr_url', 'value': 'http://localhost:7878', 'section': 'API', 'type': 'string', 'description': 'Radarr server URL'},
        {'key': 'radarr_api_key', 'value': '', 'section': 'API', 'type': 'string', 'description': 'Radarr API key'},
        {'key': 'ollama_url', 'value': 'http://localhost:11434', 'section': 'API', 'type': 'string', 'description': 'Ollama server URL'},
        
        # PATHS section
        {'key': 'remote_movies_path', 'value': '/volume1/movies', 'section': 'PATHS', 'type': 'string', 'description': 'Remote movies directory path'},
        {'key': 'remote_series_path', 'value': '/volume1/tv', 'section': 'PATHS', 'type': 'string', 'description': 'Remote TV series directory path'},
        {'key': 'local_movies_mount', 'value': '/mnt/movies', 'section': 'PATHS', 'type': 'string', 'description': 'Local movies mount point'},
        {'key': 'local_series_mount', 'value': '/mnt/series', 'section': 'PATHS', 'type': 'string', 'description': 'Local TV series mount point'},
        
        # MODELS section
        {'key': 'whisper_model', 'value': 'medium.en', 'section': 'MODELS', 'type': 'select', 'options': 'tiny.en:Tiny,base.en:Base,small.en:Small,medium.en:Medium,large-v2:Large', 'description': 'Whisper speech-to-text model'},
        {'key': 'ollama_model', 'value': 'llama3', 'section': 'MODELS', 'type': 'select', 'options': 'llama3:Llama 3,llama2:Llama 2,codellama:Code Llama,mistral:Mistral', 'description': 'Ollama translation model'},
        {'key': 'whisper_model_gpu', 'value': 'auto', 'section': 'MODELS', 'type': 'select', 'options': 'auto:تلقائي,cpu:المعالج فقط', 'description': 'GPU allocation for Whisper'},
        {'key': 'ollama_model_gpu', 'value': 'auto', 'section': 'MODELS', 'type': 'select', 'options': 'auto:تلقائي,cpu:المعالج فقط', 'description': 'GPU allocation for Ollama'},
        
        # CORRECTIONS section
        {'key': 'auto_correct_filenames', 'value': 'true', 'section': 'CORRECTIONS', 'type': 'select', 'options': 'true:نعم,false:لا', 'description': 'Automatically correct subtitle filenames'},
        {'key': 'correct_hi_to_ar', 'value': 'true', 'section': 'CORRECTIONS', 'type': 'select', 'options': 'true:نعم,false:لا', 'description': 'Convert .hi.srt files to .ar.srt'},
        
        # MEDIA_SERVICES section
        {'key': 'plex_enabled', 'value': 'false', 'section': 'MEDIA_SERVICES', 'type': 'select', 'options': 'true:نعم,false:لا', 'description': 'Enable Plex integration'},
        {'key': 'plex_url', 'value': 'http://localhost:32400', 'section': 'MEDIA_SERVICES', 'type': 'string', 'description': 'Plex server URL'},
        {'key': 'plex_token', 'value': '', 'section': 'MEDIA_SERVICES', 'type': 'string', 'description': 'Plex authentication token'},
        
        {'key': 'jellyfin_enabled', 'value': 'false', 'section': 'MEDIA_SERVICES', 'type': 'select', 'options': 'true:نعم,false:لا', 'description': 'Enable Jellyfin integration'},
        {'key': 'jellyfin_url', 'value': 'http://localhost:8096', 'section': 'MEDIA_SERVICES', 'type': 'string', 'description': 'Jellyfin server URL'},
        {'key': 'jellyfin_api_key', 'value': '', 'section': 'MEDIA_SERVICES', 'type': 'string', 'description': 'Jellyfin API key'},
        
        {'key': 'emby_enabled', 'value': 'false', 'section': 'MEDIA_SERVICES', 'type': 'select', 'options': 'true:نعم,false:لا', 'description': 'Enable Emby integration'},
        {'key': 'emby_url', 'value': 'http://localhost:8096', 'section': 'MEDIA_SERVICES', 'type': 'string', 'description': 'Emby server URL'},
        {'key': 'emby_api_key', 'value': '', 'section': 'MEDIA_SERVICES', 'type': 'string', 'description': 'Emby API key'},
        
        # REMOTE_STORAGE section
        {'key': 'remote_storage_enabled', 'value': 'false', 'section': 'REMOTE_STORAGE', 'type': 'select', 'options': 'true:نعم,false:لا', 'description': 'Enable remote storage mounting'},
        {'key': 'remote_storage_protocol', 'value': 'sftp', 'section': 'REMOTE_STORAGE', 'type': 'select', 'options': 'sftp:SFTP,ftp:FTP,smb:SMB/CIFS,nfs:NFS', 'description': 'Remote storage protocol'},
        {'key': 'remote_storage_host', 'value': '', 'section': 'REMOTE_STORAGE', 'type': 'string', 'description': 'Remote storage server hostname/IP'},
        {'key': 'remote_storage_username', 'value': '', 'section': 'REMOTE_STORAGE', 'type': 'string', 'description': 'Remote storage username'},
        {'key': 'remote_storage_password', 'value': '', 'section': 'REMOTE_STORAGE', 'type': 'password', 'description': 'Remote storage password'},
        
        # SYSTEM section
        {'key': 'enable_monitoring', 'value': 'true', 'section': 'SYSTEM', 'type': 'select', 'options': 'true:نعم,false:لا', 'description': 'Enable system monitoring'},
        {'key': 'log_level', 'value': 'INFO', 'section': 'SYSTEM', 'type': 'select', 'options': 'DEBUG:Debug,INFO:Info,WARNING:Warning,ERROR:Error', 'description': 'Application log level'},
        
        # DEVELOPMENT section
        {'key': 'debug_mode', 'value': 'false', 'section': 'DEVELOPMENT', 'type': 'select', 'options': 'true:نعم,false:لا', 'description': 'Enable debug mode'},
        {'key': 'enable_testing_features', 'value': 'false', 'section': 'DEVELOPMENT', 'type': 'select', 'options': 'true:نعم,false:لا', 'description': 'Enable testing features'},
    ]
    
    for setting in default_settings:
        existing = Settings.query.filter_by(key=setting['key']).first()
        if not existing:
            new_setting = Settings(
                key=setting['key'],
                value=setting['value'],
                section=setting['section'],
                type=setting['type'],
                options=setting.get('options', ''),
                description=setting['description']
            )
            db.session.add(new_setting)
    
    try:
        db.session.commit()
        print("✓ Default settings created successfully")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error creating default settings: {str(e)}")
        return False

def setup_database():
    """إعداد قاعدة البيانات الكاملة"""
    try:
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Create default settings
        create_default_settings()
        
        print("✓ Database setup completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Database setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    from app import app
    
    with app.app_context():
        setup_database()