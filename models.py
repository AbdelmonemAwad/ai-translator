from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Settings(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    section = db.Column(db.String(50), default='DEFAULT')
    type = db.Column(db.String(20), default='string')
    options = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MediaFile(db.Model):
    __tablename__ = 'media_files'
    
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(500))
    year = db.Column(db.Integer)
    media_type = db.Column(db.String(20))  # 'movie' or 'episode'
    poster_url = db.Column(db.Text)
    thumbnail_url = db.Column(db.Text)
    thumbnail_data = db.Column(db.LargeBinary)  # Store thumbnail as binary data
    imdb_id = db.Column(db.String(20))
    tmdb_id = db.Column(db.Integer)
    sonarr_id = db.Column(db.Integer)
    radarr_id = db.Column(db.Integer)
    plex_id = db.Column(db.String(50))  # Plex media ID
    jellyfin_id = db.Column(db.String(50))  # Jellyfin media ID
    emby_id = db.Column(db.String(50))  # Emby media ID
    kodi_id = db.Column(db.String(50))  # Kodi media ID
    service_source = db.Column(db.String(20), default='radarr')  # Source service: radarr, sonarr, plex, jellyfin, emby, kodi
    has_subtitles = db.Column(db.Boolean, default=False)
    translated = db.Column(db.Boolean, default=False)
    blacklisted = db.Column(db.Boolean, default=False)
    file_size = db.Column(db.BigInteger)
    duration = db.Column(db.Integer)  # in seconds
    quality = db.Column(db.String(20))
    video_codec = db.Column(db.String(50))
    audio_codec = db.Column(db.String(50))
    resolution = db.Column(db.String(20))
    subtitle_language = db.Column(db.String(10), default='ar')  # Target translation language
    translation_completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Log(db.Model):
    __tablename__ = 'logs'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text)
    source = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TranslationJob(db.Model):
    __tablename__ = 'translation_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    media_file_id = db.Column(db.Integer, db.ForeignKey('media_files.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    progress = db.Column(db.Float, default=0.0)  # 0.0 to 100.0
    error_message = db.Column(db.Text)
    whisper_model = db.Column(db.String(50))
    ollama_model = db.Column(db.String(50))
    audio_duration = db.Column(db.Float)
    processing_time = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    media_file = db.relationship('MediaFile', backref='translation_jobs')

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  # info, success, warning, error
    read = db.Column(db.Boolean, default=False)
    translation_params = db.Column(db.Text)  # JSON string for translation parameters
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    language = db.Column(db.String(10), default='ar')  # ar, en
    theme = db.Column(db.String(20), default='system')  # light, dark, system
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TranslationHistory(db.Model):
    __tablename__ = 'translation_history'
    
    id = db.Column(db.Integer, primary_key=True)
    media_file_id = db.Column(db.Integer, db.ForeignKey('media_files.id'), nullable=False)
    original_language = db.Column(db.String(10), default='en')
    target_language = db.Column(db.String(10), default='ar')
    subtitle_path = db.Column(db.Text)
    file_size = db.Column(db.Integer)
    duration = db.Column(db.Float)
    lines_count = db.Column(db.Integer)
    processing_time = db.Column(db.Float)
    whisper_model_used = db.Column(db.String(50))
    ollama_model_used = db.Column(db.String(50))
    quality_score = db.Column(db.Float)  # User rating or auto-calculated score
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    media_file = db.relationship('MediaFile', backref='translation_history')

class TranslationLog(db.Model):
    __tablename__ = 'translation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.Text, nullable=False)
    file_name = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'success', 'failed', 'incomplete', 'started'
    progress = db.Column(db.Float, default=0.0)  # 0.0 to 100.0
    error_message = db.Column(db.Text)
    details = db.Column(db.Text)  # Additional details about the process
    file_size = db.Column(db.BigInteger)
    duration = db.Column(db.Float)  # Processing time in seconds
    whisper_model = db.Column(db.String(50))
    ollama_model = db.Column(db.String(50))
    subtitle_path = db.Column(db.Text)  # Path to generated subtitle file
    quality_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class DatabaseStats(db.Model):
    __tablename__ = 'database_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(100), nullable=False)
    record_count = db.Column(db.Integer, default=0)
    table_size_mb = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class MediaService(db.Model):
    __tablename__ = 'media_services'
    
    id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.String(20), nullable=False)  # plex, jellyfin, emby, kodi, radarr, sonarr
    service_name = db.Column(db.String(100), nullable=False)
    base_url = db.Column(db.Text, nullable=False)
    api_key = db.Column(db.String(200))
    username = db.Column(db.String(100))
    password = db.Column(db.String(200))
    enabled = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20), default='pending')  # pending, syncing, completed, failed
    error_message = db.Column(db.Text)
    media_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VideoFormat(db.Model):
    __tablename__ = 'video_formats'
    
    id = db.Column(db.Integer, primary_key=True)
    extension = db.Column(db.String(10), unique=True, nullable=False)
    format_name = db.Column(db.String(50), nullable=False)
    supported = db.Column(db.Boolean, default=True)
    ffmpeg_codec = db.Column(db.String(50))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)