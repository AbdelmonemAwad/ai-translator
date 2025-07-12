"""
Media Services Integration for AI Translator
تكامل خدمات الوسائط للترجمان الآلي
"""

import requests
import logging
from typing import Dict, List, Optional, Any
import json
import os
import requests
from datetime import datetime

# إضافة استيراد نموذج MediaFile
from models import MediaFile, db

logger = logging.getLogger(__name__)

class MediaServicesManager:
    """Unified manager for all media services"""
    
    def __init__(self):
        self.services = {}
        self.active_services = []
    
    def register_service(self, service_name: str, service_instance):
        """Register a media service"""
        self.services[service_name] = service_instance
        logger.info(f"Registered media service: {service_name}")
    
    def get_service(self, service_name: str):
        """Get a specific service instance"""
        return self.services.get(service_name)
    
    def test_all_services(self) -> Dict[str, bool]:
        """Test connectivity to all registered services"""
        results = {}
        for name, service in self.services.items():
            try:
                results[name] = service.test_connection()
            except Exception as e:
                logger.error(f"Error testing {name}: {e}")
                results[name] = False
        return results

class PlexMediaServer:
    """Plex Media Server integration"""
    
    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.token = token
        self.headers = {'X-Plex-Token': token}
    
    def test_connection(self) -> bool:
        """Test Plex server connection"""
        try:
            response = requests.get(f"{self.url}/status/sessions", 
                                  headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Plex connection error: {e}")
            return False
    
    def get_libraries(self) -> List[Dict]:
        """Get Plex libraries"""
        try:
            response = requests.get(f"{self.url}/library/sections", 
                                  headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json().get('MediaContainer', {}).get('Directory', [])
            return []
        except Exception as e:
            logger.error(f"Error getting Plex libraries: {e}")
            return []

class JellyfinServer:
    """Jellyfin Server integration"""
    
    def __init__(self, url: str, api_key: str):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.headers = {'X-Emby-Authorization': f'MediaBrowser Token={api_key}'}
    
    def test_connection(self) -> bool:
        """Test Jellyfin server connection"""
        try:
            response = requests.get(f"{self.url}/System/Info", 
                                  headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Jellyfin connection error: {e}")
            return False
    
    def get_libraries(self) -> List[Dict]:
        """Get Jellyfin libraries"""
        try:
            response = requests.get(f"{self.url}/Library/VirtualFolders", 
                                  headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error getting Jellyfin libraries: {e}")
            return []

class RadarrAPI:
    """Radarr API integration for movie management"""
    
    def __init__(self, url: str, api_key: str):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.headers = {'X-Api-Key': api_key}
    
    def test_connection(self) -> bool:
        """Test Radarr connection"""
        try:
            response = requests.get(f"{self.url}/api/v3/system/status", 
                                  headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Radarr connection error: {e}")
            return False
    
    def get_movies(self) -> List[Dict]:
        """Get movies from Radarr"""
        try:
            response = requests.get(f"{self.url}/api/v3/movie", 
                                  headers=self.headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error getting Radarr movies: {e}")
            return []
    
    def get_quality_profiles(self) -> List[Dict]:
        """Get quality profiles from Radarr"""
        try:
            response = requests.get(f"{self.url}/api/v3/qualityprofile", 
                                  headers=self.headers, timeout=10)
            
            # تحقق من نوع المحتوى المُستلم
            content_type = response.headers.get('content-type', '').lower()
            
            if response.status_code == 200:
                # إذا كان المحتوى HTML بدلاً من JSON، فهذا خطأ مصادقة
                if 'text/html' in content_type or response.text.strip().startswith('<!doctype'):
                    logger.error("Radarr returned HTML instead of JSON - likely authentication error")
                    return []
                
                try:
                    profiles = response.json()
                    return [{'id': p['id'], 'name': p['name']} for p in profiles]
                except json.JSONDecodeError as json_err:
                    logger.error(f"Radarr returned invalid JSON: {json_err}")
                    logger.error(f"Response content: {response.text[:200]}")
                    return []
            
            elif response.status_code == 401:
                logger.error("Radarr authentication failed - check API key")
                return []
            elif response.status_code == 404:
                logger.error("Radarr API endpoint not found - check URL")
                return []
            else:
                logger.error(f"Radarr API error: {response.status_code} - {response.text[:200]}")
                return []
                
        except requests.exceptions.ConnectTimeout:
            logger.error("Connection timeout to Radarr - check if service is running")
            return []
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Connection error to Radarr: {conn_err}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting Radarr quality profiles: {e}")
            return []

    def sync_movies(self) -> Dict:
        """Sync movies from Radarr to the database"""
        try:
            # جلب قائمة الأفلام من Radarr
            movies = self.get_movies()
            if not movies:
                return {
                    'status': 'error',
                    'message': 'No movies found in Radarr',
                    'count': 0
                }
            
            # عداد للأفلام التي تمت إضافتها أو تحديثها
            added_count = 0
            updated_count = 0
            
            for movie in movies:
                # التحقق مما إذا كان الفيلم موجودًا بالفعل في قاعدة البيانات
                existing_media = MediaFile.query.filter_by(radarr_id=movie.get('id')).first()
                
                # استخراج معلومات الفيلم
                movie_data = {
                    'title': movie.get('title'),
                    'year': movie.get('year'),
                    'media_type': 'movie',
                    'path': movie.get('path', ''),
                    'imdb_id': movie.get('imdbId'),
                    'tmdb_id': movie.get('tmdbId'),
                    'radarr_id': movie.get('id'),
                    'service_source': 'radarr',
                    'has_subtitles': False,  # سيتم تحديثه لاحقًا
                    'translated': False,
                    'quality': movie.get('qualityProfileId'),
                    'updated_at': datetime.utcnow()
                }
                
                # جلب الصورة المصغرة إذا كانت متوفرة
                if movie.get('images'):
                    for image in movie.get('images', []):
                        if image.get('coverType') == 'poster':
                            movie_data['poster_url'] = image.get('remoteUrl')
                        elif image.get('coverType') == 'fanart':
                            movie_data['thumbnail_url'] = image.get('remoteUrl')
                
                # تحميل الصورة المصغرة إذا كانت متوفرة
                if movie_data.get('thumbnail_url'):
                    try:
                        thumbnail_response = requests.get(movie_data['thumbnail_url'], timeout=10)
                        if thumbnail_response.status_code == 200:
                            movie_data['thumbnail_data'] = thumbnail_response.content
                    except Exception as thumb_err:
                        logger.error(f"Error downloading thumbnail for {movie_data['title']}: {thumb_err}")
                
                if existing_media:
                    # تحديث السجل الموجود
                    for key, value in movie_data.items():
                        setattr(existing_media, key, value)
                    updated_count += 1
                else:
                    # إنشاء سجل جديد
                    new_media = MediaFile(**movie_data)
                    db.session.add(new_media)
                    added_count += 1
            
            # حفظ التغييرات في قاعدة البيانات
            db.session.commit()
            
            return {
                'status': 'success',
                'message': f'Successfully synced {len(movies)} movies from Radarr. Added: {added_count}, Updated: {updated_count}',
                'count': len(movies),
                'added': added_count,
                'updated': updated_count
            }
            
        except Exception as e:
            logger.error(f"Error syncing movies from Radarr: {e}")
            db.session.rollback()
            return {
                'status': 'error',
                'message': f'Failed to sync movies: {str(e)}',
                'count': 0
            }

class SonarrAPI:
    """Sonarr API integration for TV series management"""
    
    def __init__(self, url: str, api_key: str):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.headers = {'X-Api-Key': api_key}
    
    def test_connection(self) -> bool:
        """Test Sonarr connection"""
        try:
            response = requests.get(f"{self.url}/api/v3/system/status", 
                                  headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Sonarr connection error: {e}")
            return False
    
    def get_series(self) -> List[Dict]:
        """Get TV series from Sonarr"""
        try:
            response = requests.get(f"{self.url}/api/v3/series", 
                                  headers=self.headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error getting Sonarr series: {e}")
            return []
    
    def get_quality_profiles(self) -> List[Dict]:
        """Get quality profiles from Sonarr"""
        try:
            response = requests.get(f"{self.url}/api/v3/qualityprofile", 
                                  headers=self.headers, timeout=10)
            
            # تحقق من نوع المحتوى المُستلم
            content_type = response.headers.get('content-type', '').lower()
            
            if response.status_code == 200:
                # إذا كان المحتوى HTML بدلاً من JSON، فهذا خطأ مصادقة
                if 'text/html' in content_type or response.text.strip().startswith('<!doctype'):
                    logger.error("Sonarr returned HTML instead of JSON - likely authentication error")
                    return []
                
                try:
                    profiles = response.json()
                    return [{'id': p['id'], 'name': p['name']} for p in profiles]
                except json.JSONDecodeError as json_err:
                    logger.error(f"Sonarr returned invalid JSON: {json_err}")
                    logger.error(f"Response content: {response.text[:200]}")
                    return []
            
            elif response.status_code == 401:
                logger.error("Sonarr authentication failed - check API key")
                return []
            elif response.status_code == 404:
                logger.error("Sonarr API endpoint not found - check URL")
                return []
            else:
                logger.error(f"Sonarr API error: {response.status_code} - {response.text[:200]}")
                return []
                
        except requests.exceptions.ConnectTimeout:
            logger.error("Connection timeout to Sonarr - check if service is running")
            return []
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Connection error to Sonarr: {conn_err}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting Sonarr quality profiles: {e}")
            return []

    def sync_series(self) -> Dict:
        """Sync TV series and episodes from Sonarr to the database"""
        try:
            # جلب قائمة المسلسلات من Sonarr
            series_list = self.get_series()
            if not series_list:
                return {
                    'status': 'error',
                    'message': 'No series found in Sonarr',
                    'count': 0
                }
            
            # عداد للحلقات التي تمت إضافتها أو تحديثها
            added_count = 0
            updated_count = 0
            total_episodes = 0
            
            for series in series_list:
                series_id = series.get('id')
                
                # جلب حلقات المسلسل
                try:
                    episode_response = requests.get(
                        f"{self.url}/api/v3/episode?seriesId={series_id}&includeEpisodeFile=true", 
                        headers=self.headers, 
                        timeout=30
                    )
                    
                    if episode_response.status_code != 200:
                        logger.error(f"Failed to get episodes for series {series.get('title')}: {episode_response.status_code}")
                        continue
                        
                    episodes = episode_response.json()
                    total_episodes += len(episodes)
                    
                    # استخراج معلومات الصور من المسلسل
                    poster_url = None
                    fanart_url = None
                    for image in series.get('images', []):
                        if image.get('coverType') == 'poster':
                            poster_url = image.get('remoteUrl')
                        elif image.get('coverType') == 'fanart':
                            fanart_url = image.get('remoteUrl')
                    
                    # معالجة كل حلقة
                    for episode in episodes:
                        if not episode.get('hasFile') or not episode.get('episodeFile'):
                            continue
                            
                        episode_file = episode.get('episodeFile', {})
                        file_path = episode_file.get('path')
                        
                        if not file_path or not os.path.exists(file_path):
                            continue
                            
                        # التحقق مما إذا كانت الحلقة موجودة بالفعل في قاعدة البيانات
                        existing_media = MediaFile.query.filter_by(sonarr_id=episode.get('id')).first()
                        
                        # استخراج معلومات الحلقة
                        episode_data = {
                            'title': f"{series.get('title')} S{episode.get('seasonNumber', 0):02d}E{episode.get('episodeNumber', 0):02d} - {episode.get('title')}",
                            'year': series.get('year'),
                            'media_type': 'episode',
                            'path': file_path,
                            'imdb_id': series.get('imdbId'),
                            'tmdb_id': series.get('tvdbId'),  # Sonarr يستخدم tvdbId بدلاً من tmdbId
                            'sonarr_id': episode.get('id'),
                            'service_source': 'sonarr',
                            'has_subtitles': False,  # سيتم تحديثه لاحقًا
                            'translated': False,
                            'quality': episode_file.get('quality', {}).get('quality', {}).get('id'),
                            'updated_at': datetime.utcnow()
                        }
                        
                        # إضافة روابط الصور
                        if poster_url:
                            episode_data['poster_url'] = poster_url
                        if fanart_url:
                            episode_data['thumbnail_url'] = fanart_url
                        
                        # تحميل الصورة المصغرة إذا كانت متوفرة
                        if episode_data.get('thumbnail_url'):
                            try:
                                thumbnail_response = requests.get(episode_data['thumbnail_url'], timeout=10)
                                if thumbnail_response.status_code == 200:
                                    episode_data['thumbnail_data'] = thumbnail_response.content
                            except Exception as thumb_err:
                                logger.error(f"Error downloading thumbnail for {episode_data['title']}: {thumb_err}")
                        
                        if existing_media:
                            # تحديث السجل الموجود
                            for key, value in episode_data.items():
                                setattr(existing_media, key, value)
                            updated_count += 1
                        else:
                            # إنشاء سجل جديد
                            new_media = MediaFile(**episode_data)
                            db.session.add(new_media)
                            added_count += 1
                            
                except Exception as episode_err:
                    logger.error(f"Error processing episodes for series {series.get('title')}: {episode_err}")
                    continue
            
            # حفظ التغييرات في قاعدة البيانات
            db.session.commit()
            
            return {
                'status': 'success',
                'message': f'Successfully synced {total_episodes} episodes from {len(series_list)} series. Added: {added_count}, Updated: {updated_count}',
                'count': total_episodes,
                'series_count': len(series_list),
                'added': added_count,
                'updated': updated_count
            }
            
        except Exception as e:
            logger.error(f"Error syncing series from Sonarr: {e}")
            db.session.rollback()
            return {
                'status': 'error',
                'message': f'Failed to sync series: {str(e)}',
                'count': 0
            }

def create_media_services_manager() -> MediaServicesManager:
    """Create and configure media services manager"""
    manager = MediaServicesManager()
    
    # Services will be configured from database settings
    logger.info("Media services manager created")
    
    return manager