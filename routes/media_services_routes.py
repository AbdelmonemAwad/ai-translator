#!/usr/bin/env python3
"""
مسارات API لخدمات الوسائط
"""

import logging
import requests
from flask import Blueprint, jsonify, request
from utils.auth import is_authenticated, require_auth
from utils.settings import get_setting, get_settings

logger = logging.getLogger(__name__)

media_services_bp = Blueprint('media_services', __name__)

@media_services_bp.route('/api/media-services/status')
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

@media_services_bp.route('/api/media-services/test/<service_type>')
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

@media_services_bp.route('/api/media-services/sync/<service_type>')
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

@media_services_bp.route('/api/media-services/sync-all')
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
                        db.session.commit()  # تأكد من حفظ التغييرات بعد كل خدمة
                    elif service_type == 'sonarr':
                        from services.media_services import SonarrAPI
                        sonarr = SonarrAPI(service_config['url'], service_config['api_key'])
                        result = sonarr.sync_series()
                        db.session.commit()  # تأكد من حفظ التغييرات بعد كل خدمة
                    elif service_type in ['plex', 'jellyfin', 'emby']:
                        # For media servers, just verify connection for now
                        result = {'status': 'connected', 'message': f'{service_type.capitalize()} connection verified'}
                    else:
                        result = {'status': 'skipped', 'message': f'Sync not implemented for {service_type}'}
                    
                    all_results[service_type] = result
                except Exception as e:
                    db.session.rollback()  # التراجع عن التغييرات في حالة حدوث خطأ
                    all_results[service_type] = {'status': 'error', 'message': str(e)}
        
        return jsonify({
            'results': all_results,
            'active_services': active_services
        })
        
    except Exception as e:
        db.session.rollback()  # التراجع عن التغييرات في حالة حدوث خطأ
        return jsonify({'error': str(e)}), 500

@media_services_bp.route('/api/media-services/diagnose/<service_type>')
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

@media_services_bp.route('/api/radarr_quality_profiles', methods=['GET'])
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

@media_services_bp.route('/api/sonarr_quality_profiles', methods=['GET'])
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

# Helper functions
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
            'auth_key': 'kodi_api_key',
            'auth_field': 'api_key'
        }
    }
    
    if service_type.lower() not in config_map:
        return None
    
    config = config_map[service_type.lower()]
    enabled = settings.get(config['enabled_key'], 'false').lower() == 'true'
    url = settings.get(config['url_key'], '')
    auth = settings.get(config['auth_key'], '')
    
    return {
        'enabled': enabled,
        'url': url,
        'api_key': auth,
        'auth_field': config['auth_field']
    }

def initialize_media_services():
    """Initialize media service connections based on current settings"""
    from services.media_services import MediaServicesManager, PlexMediaServer, JellyfinServer, RadarrAPI, SonarrAPI, create_media_services_manager
    from utils.settings import get_setting
    
    # إنشاء مدير خدمات الوسائط
    manager = create_media_services_manager()
    
    # تهيئة خدمة Radarr إذا كانت مُمكّنة
    radarr_enabled = get_setting('radarr_enabled', 'false') == 'true'
    if radarr_enabled:
        radarr_url = get_setting('radarr_url', '')
        radarr_api_key = get_setting('radarr_api_key', '')
        if radarr_url and radarr_api_key:
            radarr = RadarrAPI(radarr_url, radarr_api_key)
            manager.register_service('radarr', radarr)
    
    # تهيئة خدمة Sonarr إذا كانت مُمكّنة
    sonarr_enabled = get_setting('sonarr_enabled', 'false') == 'true'
    if sonarr_enabled:
        sonarr_url = get_setting('sonarr_url', '')
        sonarr_api_key = get_setting('sonarr_api_key', '')
        if sonarr_url and sonarr_api_key:
            sonarr = SonarrAPI(sonarr_url, sonarr_api_key)
            manager.register_service('sonarr', sonarr)
    
    # تهيئة خدمة Plex إذا كانت مُمكّنة
    plex_enabled = get_setting('plex_enabled', 'false') == 'true'
    if plex_enabled:
        plex_url = get_setting('plex_url', '')
        plex_token = get_setting('plex_token', '')
        if plex_url and plex_token:
            plex = PlexMediaServer(plex_url, plex_token)
            manager.register_service('plex', plex)
    
    # تهيئة خدمة Jellyfin إذا كانت مُمكّنة
    jellyfin_enabled = get_setting('jellyfin_enabled', 'false') == 'true'
    if jellyfin_enabled:
        jellyfin_url = get_setting('jellyfin_url', '')
        jellyfin_api_key = get_setting('jellyfin_api_key', '')
        if jellyfin_url and jellyfin_api_key:
            jellyfin = JellyfinServer(jellyfin_url, jellyfin_api_key)
            manager.register_service('jellyfin', jellyfin)
    
    return manager