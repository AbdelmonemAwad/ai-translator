import requests
import os
import sys
import time
import glob
import sqlite3
import subprocess
import json

# استيراد العامل من نفس المجلد
try:
    from process_video import main as process_single_file_task
except ImportError:
    print("FATAL: Could not import 'main' from process_video.py. It must be in the same directory.")
    sys.exit(1)

# --- الإعدادات والمسارات ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(PROJECT_DIR, "library.db")
STATUS_FILE = os.path.join(PROJECT_DIR, "status.json")
BLACKLIST_FILE = os.path.join(PROJECT_DIR, "blacklist.txt")
PROCESS_LOG_FILE = os.path.join(PROJECT_DIR, "process.log")

# --- دوال مساعدة ---
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def log_to_db(level, message, details=""):
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO logs (level, message, details) VALUES (?, ?, ?)", (level, message, str(details)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB_LOG_ERROR: {e}")

def log_to_file(message):
    try:
        with open(PROCESS_LOG_FILE, 'a', encoding='utf-8') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"FILE_LOG_ERROR: {e}")

def get_settings_from_db():
    conn = get_db_connection()
    settings = {row['key']: row['value'] for row in conn.execute("SELECT key, value FROM settings").fetchall()}
    conn.close()
    return settings

def update_status(progress, current_file, total_files=0, files_done=0):
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"progress": progress, "current_file": current_file, "total_files": total_files, "files_done": files_done}, f, ensure_ascii=False)
    except Exception as e:
        print(f"WARN: Could not write status: {e}")

def read_blacklist():
    try:
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
    except:
        pass
    return []

def map_path(path, config):
    # استخدام .get() مع قيمة افتراضية لتجنب الأخطاء
    remote_movies = config.get('remote_movies_root', '')
    local_movies = config.get('local_movies_mount', '')
    remote_tv = config.get('remote_tv_root', '')
    local_tv = config.get('local_tv_mount', '')
    
    if remote_movies and path.startswith(remote_movies):
        return path.replace(remote_movies, local_movies, 1)
    elif remote_tv and path.startswith(remote_tv):
        return path.replace(remote_tv, local_tv, 1)
    return None

def get_all_media_paths(config, media_type):
    arr_type = 'sonarr' if media_type == 'series' else 'radarr'
    api_url = config.get(f'{arr_type}_url')
    api_key = config.get(f'{arr_type}_api_key')
    
    if not api_url or not api_key:
        log_to_db("WARNING", f"API settings for {arr_type.capitalize()} are missing. Skipping sync.")
        return {}

    log_to_db("INFO", f"Getting paths from {arr_type.capitalize()}...")
    headers = {"X-Api-Key": api_key}
    paths_data = {}

    try:
        if media_type == "movies":
            endpoint = f"{api_url}/api/v3/movie"
            response = requests.get(endpoint, headers=headers, timeout=300)
            response.raise_for_status()
            for item in response.json():
                if item.get('hasFile') and item.get('movieFile'):
                    path = item['movieFile'].get('path')
                    poster = next((i.get('url') for i in item.get('images', []) if i.get('coverType') == 'poster'), None)
                    if path: paths_data[path] = {'type': 'movie', 'poster': poster}
        elif media_type == "series":
            series_endpoint = f"{api_url}/api/v3/series"
            series_response = requests.get(series_endpoint, headers=headers, timeout=120)
            series_response.raise_for_status()
            for series in series_response.json():
                series_id = series.get('id')
                poster = next((i.get('url') for i in series.get('images', []) if i.get('coverType') == 'poster'), None)
                episode_endpoint = f"{api_url}/api/v3/episode?seriesId={series_id}&includeEpisodeFile=true"
                ep_response = requests.get(episode_endpoint, headers=headers, timeout=60)
                if ep_response.ok:
                    for episode in ep_response.json():
                        if episode.get('hasFile') and episode.get('episodeFile'):
                            path = episode['episodeFile'].get('path')
                            if path: paths_data[path] = {'type': 'tv', 'poster': poster}
    except Exception as e:
        log_to_db("ERROR", f"Failed to fetch from {arr_type.capitalize()}", str(e))
    
    log_to_db("INFO", f"Found {len(paths_data)} paths from {arr_type.capitalize()}.")
    return paths_data

# --- الدوال الرئيسية للمهام ---

def sync_library_task():
    log_to_db("INFO", "Library Sync task started.")
    log_to_file("Starting library sync...")
    update_status(0, "Fetching settings...")
    config = get_settings_from_db()
    
    update_status(5, "Fetching paths from Sonarr...")
    log_to_file("Fetching TV series from Sonarr...")
    sonarr_files = get_all_media_paths(config, "series")
    
    update_status(25, "Fetching paths from Radarr...")
    log_to_file("Fetching movies from Radarr...")
    radarr_files = get_all_media_paths(config, "movies")

    all_api_files = {**sonarr_files, **radarr_files}
    if not all_api_files:
        update_status(100, "Sync finished: Could not retrieve media paths.")
        log_to_file("Sync failed: No media paths retrieved.")
        return
        
    try:
        from app import app, db
        from models import MediaFile
        from datetime import datetime
        
        with app.app_context():
            # Get existing paths from database
            existing_files = MediaFile.query.all()
            db_paths = {file.path for file in existing_files}
            api_local_paths = set()
            total_api_files = len(all_api_files)
            
            log_to_db("INFO", f"Syncing {total_api_files} files with database...")
            log_to_file(f"Processing {total_api_files} media files...")
            
            for i, (api_path, data) in enumerate(all_api_files.items()):
                progress = 50 + int((i/total_api_files)*40)
                update_status(progress, f"Syncing: {os.path.basename(api_path)}")
                
                local_path = map_path(api_path, config)
                if not local_path: 
                    continue
                
                api_local_paths.add(local_path)
                has_translation = os.path.exists(f"{os.path.splitext(local_path)[0]}.ar.srt")
                
                # Check if file exists in database
                existing_file = MediaFile.query.filter_by(path=local_path).first()
                
                if existing_file:
                    # Update existing file
                    existing_file.translated = has_translation
                    existing_file.has_subtitles = has_translation
                    existing_file.updated_at = datetime.utcnow()
                    if data.get('poster'):
                        existing_file.poster_url = data['poster']
                else:
                    # Create new file record
                    new_file = MediaFile()
                    new_file.path = local_path
                    new_file.media_type = data['type']
                    new_file.translated = has_translation
                    new_file.has_subtitles = has_translation
                    new_file.poster_url = data.get('poster')
                    new_file.service_source = 'radarr' if data['type'] == 'movie' else 'sonarr'
                    db.session.add(new_file)

            # Delete stale records
            paths_to_delete = db_paths - api_local_paths
            if paths_to_delete:
                log_to_db("INFO", f"Deleting {len(paths_to_delete)} stale records from DB.")
                log_to_file(f"Removing {len(paths_to_delete)} stale records from database...")
                MediaFile.query.filter(MediaFile.path.in_(paths_to_delete)).delete(synchronize_session=False)

            db.session.commit()
    except Exception as e:
        log_to_db("ERROR", f"Sync library error: {str(e)}")
        log_to_file(f"Sync library error: {str(e)}")
    update_status(100, "Library sync complete!")
    log_to_db("INFO", "Library Sync task finished.")
    log_to_file("Library sync completed successfully.")

def corrections_task():
    log_to_db("INFO", "Corrections task started.")
    log_to_file("Starting subtitle corrections...")
    
    try:
        from app import app, db
        from models import MediaFile, Settings
        import glob
        from datetime import datetime
        
        with app.app_context():
            # Get settings
            rename_hi_setting = Settings.query.filter_by(key='rename_hi_srt').first()
            rename_generic_setting = Settings.query.filter_by(key='rename_generic_srt').first()
            
            rename_hi = rename_hi_setting.value.lower() == 'yes' if rename_hi_setting else True
            rename_generic = rename_generic_setting.value.lower() == 'yes' if rename_generic_setting else True
            
            # Get all media files
            media_files = MediaFile.query.all()
            total_files = len(media_files)
            fixed_count = 0
            
            log_to_file(f"Processing {total_files} media files for corrections...")
            
            for i, media_file in enumerate(media_files):
                file_path = media_file.path
                progress = int((i / total_files) * 100) if total_files > 0 else 0
                update_status(progress, f"Correcting: {os.path.basename(file_path)}")
                
                if not os.path.exists(file_path):
                    continue
                    
                base_path = os.path.splitext(file_path)[0]
                target_srt = f"{base_path}.ar.srt"
                
                # Skip if Arabic subtitle already exists
                if os.path.exists(target_srt):
                    continue
                
                # Look for .hi.srt files
                if rename_hi:
                    hi_files = glob.glob(f"{base_path}*.hi.srt")
                    for hi_file in hi_files:
                        try:
                            os.rename(hi_file, target_srt)
                            fixed_count += 1
                            log_to_file(f"Renamed {hi_file} to {target_srt}")
                            # Update database status
                            media_file.has_subtitles = True
                            media_file.translated = True
                            media_file.translation_completed_at = datetime.utcnow()
                            break
                        except Exception as e:
                            log_to_file(f"Failed to rename {hi_file}: {e}")
                
                # Look for generic .srt files (only if no other subtitles exist)
                if rename_generic and not os.path.exists(target_srt):
                    generic_srt = f"{base_path}.srt"
                    if os.path.exists(generic_srt):
                        # Check if there are other subtitle files
                        other_subs = glob.glob(f"{base_path}*.srt")
                        other_subs = [f for f in other_subs if not f.endswith('.ar.srt')]
                        
                        if len(other_subs) == 1:  # Only the generic one
                            try:
                                os.rename(generic_srt, target_srt)
                                fixed_count += 1
                                log_to_file(f"Renamed {generic_srt} to {target_srt}")
                                # Update database status
                                media_file.has_subtitles = True
                                media_file.translated = True
                                media_file.translation_completed_at = datetime.utcnow()
                            except Exception as e:
                                log_to_file(f"Failed to rename {generic_srt}: {e}")
            
            # Final database update - scan all files for actual subtitle existence
            for media_file in media_files:
                srt_path = f"{os.path.splitext(media_file.path)[0]}.ar.srt"
                has_sub = os.path.exists(srt_path)
                media_file.has_subtitles = has_sub
                media_file.translated = has_sub
                
            db.session.commit()
            
            update_status(100, f"Corrections completed. Fixed {fixed_count} files.")
            log_to_db("INFO", f"Corrections task finished. Fixed {fixed_count} files.")
            log_to_file(f"Corrections completed. Fixed {fixed_count} files.")
            
    except Exception as e:
        log_to_db("ERROR", f"Corrections task error: {str(e)}")
        log_to_file(f"Corrections error: {str(e)}")

def batch_translate_task():
    log_to_db("INFO", "Batch translate task started.")
    log_to_file("Starting batch translation...")
    
    try:
        from app import app, db
        from models import MediaFile
        
        with app.app_context():
            # Get untranslated files not in blacklist
            blacklist = read_blacklist()
            
            # Query untranslated files using SQLAlchemy
            untranslated_files = MediaFile.query.filter_by(translated=False).order_by(MediaFile.path).all()
            
            # Filter out blacklisted files and check file existence
            files_to_process = [file.path for file in untranslated_files 
                               if file.path not in blacklist and os.path.exists(file.path)]
            
            total_files = len(files_to_process)
            
            if total_files == 0:
                update_status(100, "No files to translate.")
                log_to_file("No files found for translation.")
                return
            
            log_to_file(f"Found {total_files} files to translate.")
            
            for i, file_path in enumerate(files_to_process, 1):
                progress = int((i / total_files) * 100) if total_files > 0 else 0
                current_file_name = os.path.basename(file_path)
                update_status(progress, f"({i}/{total_files}) {current_file_name}", total_files, i-1)
                
                log_to_file(f"Processing file {i}/{total_files}: {current_file_name}")
                
                try:
                    # Find media file in database
                    media_file = MediaFile.query.filter_by(path=file_path).first()
                    if media_file:
                        # Update status to processing
                        media_file.has_subtitles = False
                        db.session.commit()
                    
                    # Process single file
                    process_single_file_task(file_path)
                    
                    # Check if translation was created
                    srt_path = f"{os.path.splitext(file_path)[0]}.ar.srt"
                    if os.path.exists(srt_path):
                        if media_file:
                            media_file.translated = True
                            media_file.has_subtitles = True
                            from datetime import datetime
                            media_file.translation_completed_at = datetime.utcnow()
                            db.session.commit()
                        log_to_file(f"Successfully translated: {current_file_name}")
                    else:
                        log_to_file(f"Translation failed: {current_file_name}")
                        
                except Exception as e:
                    log_to_file(f"Error processing {current_file_name}: {str(e)}")
                    log_to_db("ERROR", f"Error processing {current_file_name}", str(e))
            
            update_status(100, "Batch translation finished.", total_files, total_files)
            log_to_db("INFO", "Batch translate task finished.")
            log_to_file("Batch translation completed.")
            
    except Exception as e:
        log_to_db("ERROR", f"Batch translate task error: {str(e)}")
        log_to_file(f"Batch translation error: {str(e)}")

def single_file_translate_task(file_path):
    log_to_db("INFO", f"Single file translate task started for: {file_path}")
    log_to_file(f"Starting translation for: {os.path.basename(file_path)}")
    
    update_status(0, f"Translating: {os.path.basename(file_path)}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update status in database
        cursor.execute("UPDATE media_files SET status = 'processing' WHERE local_path = ?", (file_path,))
        conn.commit()
        
        # Process the file
        process_single_file_task(file_path)
        
        # Check if translation was created
        srt_path = f"{os.path.splitext(file_path)[0]}.ar.srt"
        if os.path.exists(srt_path):
            cursor.execute("UPDATE media_files SET has_arabic_subtitle = 1, status = 'completed' WHERE local_path = ?", 
                          (file_path,))
            log_to_file(f"Successfully translated: {os.path.basename(file_path)}")
            update_status(100, f"Translation completed: {os.path.basename(file_path)}")
        else:
            cursor.execute("UPDATE media_files SET status = 'failed' WHERE local_path = ?", (file_path,))
            log_to_file(f"Translation failed: {os.path.basename(file_path)}")
            update_status(100, f"Translation failed: {os.path.basename(file_path)}")
            
    except Exception as e:
        cursor.execute("UPDATE media_files SET status = 'failed' WHERE local_path = ?", (file_path,))
        log_to_file(f"Error translating {os.path.basename(file_path)}: {str(e)}")
        log_to_db("ERROR", f"Error translating {os.path.basename(file_path)}", str(e))
        update_status(100, f"Translation error: {os.path.basename(file_path)}")
    
    conn.commit()
    conn.close()

def scan_translation_status_task():
    """Scan all media files and update translation status based on existing subtitle files"""
    log_to_db("INFO", "Translation status scan started")
    log_to_file("Starting translation status scan...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all media files
        media_files = cursor.execute("SELECT id, path FROM media_files").fetchall()
        total_files = len(media_files)
        updated_count = 0
        
        update_status(0, "Scanning translation status...", total_files, 0)
        
        for i, row in enumerate(media_files):
            file_id = row['id']
            file_path = row['path']
            
            if not file_path or not os.path.exists(file_path):
                continue
                
            # Check if Arabic subtitle exists
            video_dir = os.path.dirname(file_path)
            video_name = os.path.splitext(os.path.basename(file_path))[0]
            arabic_srt_path = os.path.join(video_dir, f"{video_name}.ar.srt")
            
            has_translation = os.path.exists(arabic_srt_path)
            
            # Update database if status has changed
            cursor.execute("SELECT translated FROM media_files WHERE id = ?", (file_id,))
            current_status = cursor.fetchone()
            
            if current_status and current_status['translated'] != has_translation:
                from datetime import datetime
                cursor.execute("""
                    UPDATE media_files 
                    SET translated = ?, translation_completed_at = ? 
                    WHERE id = ?
                """, (has_translation, datetime.now().isoformat() if has_translation else None, file_id))
                updated_count += 1
                log_to_file(f"Updated translation status for: {os.path.basename(file_path)} -> {'Translated' if has_translation else 'Not Translated'}")
            
            # Update progress
            progress = int((i / total_files) * 100) if total_files > 0 else 0
            update_status(progress, f"Scanning: {os.path.basename(file_path)}", total_files, i + 1)
        
        conn.commit()
        update_status(100, f"Translation status scan complete! Updated {updated_count} files", total_files, total_files)
        log_to_db("INFO", f"Translation status scan completed. Updated {updated_count} files.")
        log_to_file(f"Translation status scan completed successfully. Updated {updated_count} files.")
        
    except Exception as e:
        error_msg = f"Translation status scan error: {str(e)}"
        log_to_db("ERROR", error_msg)
        log_to_file(error_msg)
    finally:
        conn.close()

# --- نقطة الدخول الرئيسية ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        task_name = sys.argv[1]
        args = sys.argv[2:]
        
        if task_name == "single_file_translate_task":
            if args:
                single_file_translate_task(args[0])
            else:
                log_to_db("ERROR", "No file path provided for single file translation.")
        elif task_name in globals() and callable(globals()[task_name]):
            globals()[task_name](*args)
        else:
            log_to_db("ERROR", f"Background task '{task_name}' not found.")
    else:
        log_to_db("ERROR", "No task name provided to background_tasks.py")
