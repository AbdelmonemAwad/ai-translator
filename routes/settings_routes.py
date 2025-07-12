#!/usr/bin/env python3
"""
مسارات API للإعدادات
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, session, redirect, url_for, render_template, flash
from utils.auth import is_authenticated, get_user_language, get_user_theme
from models import Settings, db
from routes.logs_routes import log_to_db

logger = logging.getLogger(__name__)

# إنشاء Blueprint للإعدادات
settings_bp = Blueprint('settings', __name__)

def update_setting(key, value):
    """Update or create a setting"""
    try:
        print(f"DEBUG: update_setting called with key={key}, value={value}")
        setting = Settings.query.filter_by(key=key).first()
        if setting:
            print(f"DEBUG: Found existing setting {key}: {setting.value} -> {value}")
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            print(f"DEBUG: Creating new setting {key} = {value}")
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
        db.session.rollback()
        log_to_db("ERROR", f"Failed to update setting {key}", str(e))
        return False

@settings_bp.route('/settings', methods=['GET', 'POST'])
def settings_page():
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update settings
        for key, value in request.form.items():
            if key.startswith('_'):  # Skip Flask form fields
                continue
            update_setting(key, value)
        
        flash('تم حفظ الإعدادات بنجاح')
        log_to_db("INFO", "Settings updated")
        return redirect(url_for('settings.settings_new'))
    
    # Redirect to new settings page
    return redirect(url_for('settings.settings_new'))

@settings_bp.route('/settings/new', methods=['GET', 'POST'])
def settings_new():
    """New modern settings page with tabs system"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update settings
        for key, value in request.form.items():
            if key.startswith('_'):  # Skip Flask form fields
                continue
            update_setting(key, value)
        
        flash('تم حفظ الإعدادات بنجاح', 'success')
        log_to_db("INFO", "Settings updated via new interface")
        return redirect(url_for('settings.settings_new'))
    
    # Get settings grouped by section
    settings_by_section = {}
    user_language = get_user_language()
    
    for setting in Settings.query.order_by(Settings.section, Settings.key).all():
        if setting.section not in settings_by_section:
            settings_by_section[setting.section] = []
        
        # Process display name for translation
        if hasattr(setting, 'display_name'):
            setting.display_name = setting.display_name or setting.key
        else:
            setting.display_name = setting.key
        
        # Process description for translation
        if setting.description:
            try:
                if isinstance(setting.description, str) and setting.description.startswith('{'):
                    desc_dict = json.loads(setting.description)
                    setting.description = desc_dict.get(user_language, desc_dict.get('en', setting.key))
                else:
                    setting.description = setting.description
            except:
                setting.description = setting.description or ""
        else:
            setting.description = ""
            
        # Process options for select fields
        if setting.type == 'select' and setting.options:
            options_text = setting.options
            
            # Check if options is JSON (multilingual)
            if isinstance(options_text, str) and options_text.startswith('{'):
                try:
                    options_dict = json.loads(options_text)
                    options_text = options_dict.get(user_language, options_dict.get('en', ''))
                except json.JSONDecodeError:
                    # If JSON parsing fails, use the raw text
                    pass
            
            # Store processed options text
            setting.options = options_text
        
        settings_by_section[setting.section].append(setting)
    
    return render_template('settings_new.html', settings_by_section=settings_by_section)

# New Hierarchical Settings Routes
@settings_bp.route('/settings/general', methods=['GET', 'POST'])
def settings_general():
    """General settings page"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update settings
        for key, value in request.form.items():
            if key.startswith('_'):
                continue
            update_setting(key, value)
        
        flash('تم حفظ الإعدادات العامة بنجاح', 'success')
        log_to_db("INFO", "General settings updated")
        return redirect(url_for('settings.settings_general'))
    
    # Get current settings
    current_settings = {}
    for setting in Settings.query.filter(Settings.section == 'DEFAULT').all():
        current_settings[setting.key] = setting.value
    
    return render_template('settings/general.html', 
                         current_section='general',
                         current_settings=current_settings)

@settings_bp.route('/settings/authentication', methods=['GET', 'POST'])
def settings_authentication():
    """Authentication settings page"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('_'):
                continue
            update_setting(key, value)
        
        flash('تم حفظ إعدادات المصادقة بنجاح', 'success')
        log_to_db("INFO", "Authentication settings updated")
        return redirect(url_for('settings.settings_authentication'))
    
    current_settings = {}
    for setting in Settings.query.filter(Settings.section == 'AUTH').all():
        current_settings[setting.key] = setting.value
    
    return render_template('settings/authentication.html', 
                         current_section='authentication',
                         current_settings=current_settings)

@settings_bp.route('/settings/ai')
@settings_bp.route('/settings/ai/<subsection>', methods=['GET', 'POST'])
def settings_ai(subsection='models'):
    """AI settings page with sub-sections"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('_'):
                continue
            update_setting(key, value)
        
        flash('تم حفظ إعدادات الذكاء الاصطناعي بنجاح', 'success')
        log_to_db("INFO", f"AI settings updated - {subsection}")
        return redirect(url_for('settings.settings_ai', subsection=subsection))
    
    # Define sub-tabs for AI section
    sub_tabs = [
        {'key': 'models', 'label': 'ai_models', 'icon': 'cpu', 'url': url_for('settings.settings_ai', subsection='models')},
        {'key': 'gpu', 'label': 'gpu_configuration', 'icon': 'monitor', 'url': url_for('settings.settings_ai', subsection='gpu')},
        {'key': 'api', 'label': 'api_configuration', 'icon': 'link', 'url': url_for('settings.settings_ai', subsection='api')}
    ]
    
    current_settings = {}
    # Include MODELS, API, and GPU sections for AI settings
    for setting in Settings.query.filter(Settings.section.in_(['MODELS', 'API', 'GPU'])).all():
        current_settings[setting.key] = setting.value
    
    return render_template('settings/ai.html', 
                         current_section='ai',
                         current_subsection=subsection,
                         sub_tabs=sub_tabs,
                         current_settings=current_settings)

@settings_bp.route('/settings/paths', methods=['GET', 'POST'])
def settings_paths():
    """File paths settings page"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        print(f"DEBUG: POST data received: {dict(request.form)}")
        for key, value in request.form.items():
            if key.startswith('_'):
                continue
            print(f"DEBUG: Updating setting {key} = {value}")
            update_setting(key, value)
        
        flash('تم حفظ إعدادات المسارات بنجاح', 'success')
        log_to_db("INFO", "Paths settings updated")
        return redirect(url_for('settings.settings_paths'))
    
    current_settings = {}
    # Include PATHS, REMOTE_STORAGE, and legacy DEFAULT section settings
    for setting in Settings.query.filter(Settings.section.in_(['PATHS', 'REMOTE_STORAGE', 'DEFAULT'])).all():
        # Only include remote-related settings from DEFAULT section
        if setting.section == 'DEFAULT' and 'remote' not in setting.key:
            continue
        current_settings[setting.key] = setting.value
    
    return render_template('settings/paths.html', 
                         current_section='paths',
                         current_settings=current_settings)

@settings_bp.route('/settings/media', methods=['GET', 'POST'])
def settings_media():
    """Media settings page"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update settings
        for key, value in request.form.items():
            if key.startswith('_'):
                continue
            update_setting(key, value)
        
        flash('تم حفظ إعدادات الوسائط بنجاح', 'success')
        log_to_db("INFO", "Media settings updated")
        return redirect(url_for('settings.settings_media'))
    
    # Get current settings
    current_settings = {}
    for setting in Settings.query.filter(Settings.section.in_(['MEDIA', 'API'])).all():
        current_settings[setting.key] = setting.value
    
    return render_template('settings/media.html', 
                         current_section='media',
                         current_settings=current_settings)

@settings_bp.route('/settings/corrections', methods=['GET', 'POST'])
def settings_corrections():
    """Corrections settings page"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update settings
        for key, value in request.form.items():
            if key.startswith('_'):
                continue
            update_setting(key, value)
        
        flash('تم حفظ إعدادات التصحيحات بنجاح', 'success')
        log_to_db("INFO", "Corrections settings updated")
        return redirect(url_for('settings.settings_corrections'))
    
    # Get current settings
    current_settings = {}
    for setting in Settings.query.filter(Settings.section.in_(['CORRECTIONS'])).all():
        current_settings[setting.key] = setting.value
    
    return render_template('settings/corrections.html', 
                         current_section='corrections',
                         current_settings=current_settings)

@settings_bp.route('/settings/system', methods=['GET', 'POST'])
def settings_system():
    """System settings page"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update settings
        for key, value in request.form.items():
            if key.startswith('_'):
                continue
            update_setting(key, value)
        
        flash('تم حفظ إعدادات النظام بنجاح', 'success')
        log_to_db("INFO", "System settings updated")
        return redirect(url_for('settings.settings_system'))
    
    # Get current settings
    current_settings = {}
    for setting in Settings.query.filter(Settings.section.in_(['SYSTEM'])).all():
        current_settings[setting.key] = setting.value
    
    return render_template('settings/system.html', 
                         current_section='system',
                         current_settings=current_settings)

@settings_bp.route('/settings/utilities', methods=['GET', 'POST'])
def settings_utilities():
    """Utilities settings page"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update settings
        for key, value in request.form.items():
            if key.startswith('_'):
                continue
            update_setting(key, value)
        
        flash('تم حفظ إعدادات الأدوات المساعدة بنجاح', 'success')
        log_to_db("INFO", "Utilities settings updated")
        return redirect(url_for('settings.settings_utilities'))
    
    # Get current settings
    current_settings = {}
    for setting in Settings.query.filter(Settings.section.in_(['UTILITIES'])).all():
        current_settings[setting.key] = setting.value
    
    return render_template('settings/utilities.html', 
                         current_section='utilities',
                         current_settings=current_settings)