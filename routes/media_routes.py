#!/usr/bin/env python3
"""
مسارات API للوسائط والملفات
"""

import os
import logging
from flask import Blueprint, jsonify, request, session, redirect, url_for, render_template, flash
from utils.auth import is_authenticated, get_user_language, get_user_theme
from utils.settings import get_setting, update_setting
from models import MediaFile, TranslationLog, db
from translations import get_translation, t

logger = logging.getLogger(__name__)

# تعريف مسار ملف القائمة السوداء
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLACKLIST_FILE = os.path.join(PROJECT_DIR, "blacklist.txt")

media_bp = Blueprint('media', __name__)

# دوال القائمة السوداء
def read_blacklist():
    """Read blacklisted paths from file"""
    if not os.path.exists(BLACKLIST_FILE):
        return []
    try:
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def add_to_blacklist(path):
    """Add path to blacklist"""
    blacklist = read_blacklist()
    if path not in blacklist:
        blacklist.append(path)
        try:
            with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(blacklist))
            
            # Update database record
            media_file = MediaFile.query.filter_by(path=path).first()
            if media_file:
                media_file.blacklisted = True
                db.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to add to blacklist: {path} - {str(e)}")
    return False

def remove_from_blacklist(path):
    """Remove path from blacklist"""
    blacklist = read_blacklist()
    if path in blacklist:
        blacklist.remove(path)
        try:
            with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(blacklist))
            
            # Update database record
            media_file = MediaFile.query.filter_by(path=path).first()
            if media_file:
                media_file.blacklisted = False
                db.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to remove from blacklist: {path} - {str(e)}")
    return False

# نقل وظائف الوسائط والملفات من app.py
@media_bp.route('/files')
@media_bp.route('/files/<status>')
def file_management(status='all'):
    if not is_authenticated():
        return redirect(url_for('user.login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = int(get_setting('items_per_page', '24'))
    search = request.args.get('search', '')
    media_type = request.args.get('type', '')
    
    # Build query
    query = MediaFile.query
    
    if search:
        query = query.filter(MediaFile.title.contains(search))
    
    if media_type:
        query = query.filter_by(media_type=media_type)
    
    if status == 'untranslated':
        query = query.filter_by(translated=False, blacklisted=False)
    elif status == 'translated':
        query = query.filter_by(translated=True)
    elif status == 'blacklisted':
        query = query.filter_by(blacklisted=True)
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    files = pagination.items
    
    # Set page title based on status
    if status == 'untranslated':
        page_title = t('files_to_translate')
    elif status == 'translated':
        page_title = t('translated_files')
    elif status == 'blacklisted':
        page_title = t('blacklisted_files')
    else:
        page_title = t('all_files')

    return render_template('file_management.html', 
                         files=files, 
                         pagination=pagination,
                         status=status,
                         page_title=page_title,
                         search=search,
                         media_type=media_type)

@media_bp.route('/corrections')
def corrections_page():
    if not is_authenticated():
        return redirect(url_for('user.login'))
    return render_template('corrections.html')

@media_bp.route('/blacklist')
def blacklist_page():
    if not is_authenticated():
        return redirect(url_for('user.login'))
    
    # Get blacklisted media files from database with full information
    blacklisted_files = MediaFile.query.filter_by(blacklisted=True).all()
    
    # Also read blacklist from file for paths not in database
    file_blacklist = read_blacklist()
    
    return render_template('blacklist.html', blacklisted_files=blacklisted_files, file_blacklist=file_blacklist)

@media_bp.route('/action/single-blacklist', methods=['POST'])
def action_single_blacklist():
    """Add or remove a single file from blacklist"""
    if not is_authenticated():
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
    
    # تحقق من نوع المحتوى وقراءة البيانات بالطريقة المناسبة
    if request.is_json:
        data = request.get_json()
        path = data.get('path')
        action = data.get('action', 'add')
    else:
        # للطلبات من نوع application/x-www-form-urlencoded
        path = request.form.get('path')
        action = request.form.get('action', 'add')
    
    if not path:
        return jsonify({"status": "error", "message": "No path provided"}), 400
    
    if action == 'add':
        success = add_to_blacklist(path)
    else:
        success = remove_from_blacklist(path)
    
    return jsonify({"status": "success" if success else "error"})

@media_bp.route('/action/remove-from-blacklist', methods=['POST'])
def action_remove_from_blacklist():
    """Remove a file from blacklist"""
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    # تحقق من نوع المحتوى وقراءة البيانات بالطريقة المناسبة
    if request.is_json:
        data = request.get_json()
        path = data.get('path')
    else:
        # للطلبات من نوع form-data
        path = request.form.get('path')
    
    if not path:
        return jsonify({'error': 'مسار الملف مطلوب'}), 400
    
    if remove_from_blacklist(path):
        # إذا كان الطلب من نموذج HTML، قم بإعادة التوجيه إلى صفحة القائمة السوداء
        if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
            flash('تم إزالة الملف من القائمة السوداء بنجاح', 'success')
            return redirect(url_for('media.blacklist_page'))
        # إذا كان الطلب من AJAX، أرجع JSON
        return jsonify({'success': True, 'message': 'تم إزالة الملف من القائمة السوداء'})
    else:
        if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
            flash('فشل في إزالة الملف من القائمة السوداء', 'error')
            return redirect(url_for('media.blacklist_page'))
        return jsonify({'error': 'فشل في إزالة الملف من القائمة السوداء'}), 500

@media_bp.route('/api/files')
def api_files():
    page = request.args.get('page', 1, type=int)
    per_page = int(get_setting('items_per_page', '24'))
    search = request.args.get('search', '', type=str)
    media_type = request.args.get('media_type', 'all', type=str)
    status = request.args.get('status', 'all', type=str)
    
    query = MediaFile.query
    
    # Apply search filter
    if search:
        query = query.filter(MediaFile.title.contains(search))
    
    # Apply media type filter
    if media_type != 'all':
        if media_type == 'movies':
            query = query.filter(MediaFile.media_type == 'movie')
        elif media_type == 'tv':
            query = query.filter(MediaFile.media_type == 'episode')
    
    # Apply status filter (translated/untranslated)
    if status == 'translated':
        query = query.filter(MediaFile.translated == True)
    elif status == 'untranslated':
        query = query.filter(MediaFile.translated == False)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    files_data = []
    for file in pagination.items:
        files_data.append({
            'id': file.id,
            'path': file.path,
            'title': file.title,
            'year': file.year,
            'media_type': file.media_type,
            'poster_url': file.poster_url,
            'translated': file.translated,
            'blacklisted': file.blacklisted,
            'file_size': file.file_size,
            'quality': file.quality
        })
    
    return jsonify({
        'files': files_data,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'total': pagination.total,
            'per_page': pagination.per_page,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    })


@media_bp.route('/api/create_sample_blacklist', methods=['POST'])
def api_create_sample_blacklist():
    """Create sample blacklist entries for testing"""
    if not is_authenticated():
        return jsonify({'error': translate_text('not_authenticated')}), 401
    
    try:
        sample_blacklist_paths = [
            '/media/movies/Old.Movie.1995.DVDRip.XviD-RARBG.avi',
            '/media/movies/Low.Quality.Film.2000.CAM-TERRIBLE.mp4',
            '/media/movies/Broken.Audio.Movie.2010.720p.HDTV.x264-BROKEN.mkv',
            '/media/tv/Old Series/Season 01/Old.Series.S01E01.480p.WEB-DL.x264-OLD.mkv',
            '/media/tv/Corrupted Show/Season 02/Corrupted.Show.S02E05.CORRUPT.mkv',
            '/media/movies/Sample.Movie.SAMPLE.mkv',
            '/media/tv/Test Series/Test.Series.S01E01.TEST.mkv',
            '/media/movies/Trailer.Only.Movie.2024.TRAILER.mp4'
        ]
        
        # Create sample media files in database first
        sample_media_data = [
            {
                'path': '/media/movies/Old.Movie.1995.DVDRip.XviD-RARBG.avi',
                'title': 'Old Movie',
                'year': 1995,
                'media_type': 'movie',
                'poster_url': 'https://image.tmdb.org/t/p/w500/sample1.jpg',
                'blacklisted': True
            },
            {
                'path': '/media/movies/Low.Quality.Film.2000.CAM-TERRIBLE.mp4',
                'title': 'Low Quality Film',
                'year': 2000,
                'media_type': 'movie',
                'poster_url': 'https://image.tmdb.org/t/p/w500/sample2.jpg',
                'blacklisted': True
            },
            {
                'path': '/media/movies/Broken.Audio.Movie.2010.720p.HDTV.x264-BROKEN.mkv',
                'title': 'Broken Audio Movie',
                'year': 2010,
                'media_type': 'movie',
                'poster_url': 'https://image.tmdb.org/t/p/w500/sample3.jpg',
                'blacklisted': True
            },
            {
                'path': '/media/tv/Old Series/Season 01/Old.Series.S01E01.480p.WEB-DL.x264-OLD.mkv',
                'title': 'Old Series - S01E01',
                'year': 2005,
                'media_type': 'episode',
                'poster_url': 'https://image.tmdb.org/t/p/w500/sample4.jpg',
                'blacklisted': True
            },
            {
                'path': '/media/tv/Corrupted Show/Season 02/Corrupted.Show.S02E05.CORRUPT.mkv',
                'title': 'Corrupted Show - S02E05',
                'year': 2018,
                'media_type': 'episode',
                'poster_url': 'https://image.tmdb.org/t/p/w500/sample5.jpg',
                'blacklisted': True
            },
            {
                'path': '/media/movies/Sample.Movie.SAMPLE.mkv',
                'title': 'Sample Movie',
                'year': 2023,
                'media_type': 'movie',
                'poster_url': 'https://image.tmdb.org/t/p/w500/sample6.jpg',
                'blacklisted': True
            },
            {
                'path': '/media/tv/Test Series/Test.Series.S01E01.TEST.mkv',
                'title': 'Test Series - S01E01',
                'year': 2024,
                'media_type': 'episode',
                'poster_url': 'https://image.tmdb.org/t/p/w500/sample7.jpg',
                'blacklisted': True
            },
            {
                'path': '/media/movies/Trailer.Only.Movie.2024.TRAILER.mp4',
                'title': 'Trailer Only Movie',
                'year': 2024,
                'media_type': 'movie',
                'poster_url': 'https://image.tmdb.org/t/p/w500/sample8.jpg',
                'blacklisted': True
            }
        ]
        
        # Add or update media files in database
        for media_data in sample_media_data:
            media_file = MediaFile.query.filter_by(path=media_data['path']).first()
            if not media_file:
                media_file = MediaFile(**media_data)
                db.session.add(media_file)
            else:
                for key, value in media_data.items():
                    setattr(media_file, key, value)
        
        db.session.commit()
        
        added_count = 0
        for path in sample_blacklist_paths:
            if add_to_blacklist(path):
                added_count += 1
        
        log_to_db("INFO", f"Created {added_count} sample blacklist entries")
        
        return jsonify({
            'success': True, 
            'message': f'Added {added_count} sample paths to blacklist',
            'added_count': added_count,
            'total_paths': len(sample_blacklist_paths)
        })
    except Exception as e:
        log_to_db("ERROR", f"Error creating sample blacklist: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@media_bp.route('/api/clear_sample_blacklist', methods=['POST'])
def api_clear_sample_blacklist():
    """Clear sample blacklist entries"""
    if not is_authenticated():
        return jsonify({'error': translate_text('not_authenticated')}), 401
    
    try:
        sample_blacklist_paths = [
            '/media/movies/Old.Movie.1995.DVDRip.XviD-RARBG.avi',
            '/media/movies/Low.Quality.Film.2000.CAM-TERRIBLE.mp4',
            '/media/movies/Broken.Audio.Movie.2010.720p.HDTV.x264-BROKEN.mkv',
            '/media/tv/Old Series/Season 01/Old.Series.S01E01.480p.WEB-DL.x264-OLD.mkv',
            '/media/tv/Corrupted Show/Season 02/Corrupted.Show.S02E05.CORRUPT.mkv',
            '/media/movies/Sample.Movie.SAMPLE.mkv',
            '/media/tv/Test Series/Test.Series.S01E01.TEST.mkv',
            '/media/movies/Trailer.Only.Movie.2024.TRAILER.mp4'
        ]
        
        removed_count = 0
        for path in sample_blacklist_paths:
            if remove_from_blacklist(path):
                removed_count += 1
        
        log_to_db("INFO", f"Removed {removed_count} sample blacklist entries")
        
        return jsonify({
            'success': True, 
            'message': f'Removed {removed_count} sample paths from blacklist',
            'removed_count': removed_count
        })
    except Exception as e:
        log_to_db("ERROR", f"Error clearing sample blacklist: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@media_bp.route('/action/run_corrections', methods=['POST'])
def action_run_corrections():
    if not is_authenticated():
        return jsonify({'error': 'غير مصرح'}), 401
    
    def generate():
        yield "data: بدء عملية التصحيح...\n\n"
        
        try:
            # Find and rename subtitle files
            corrections_made = 0
            
            for media_file in MediaFile.query.filter_by(translated=True).all():
                file_dir = os.path.dirname(media_file.path)
                filename = os.path.splitext(os.path.basename(media_file.path))[0]
                
                # Look for .hi.srt files
                hi_srt = os.path.join(file_dir, f"{filename}.hi.srt")
                ar_srt = os.path.join(file_dir, f"{filename}.ar.srt")
                
                if os.path.exists(hi_srt) and not os.path.exists(ar_srt):
                    try:
                        os.rename(hi_srt, ar_srt)
                        corrections_made += 1
                        yield f"data: تم تصحيح: {filename}\n\n"
                        time.sleep(0.1)
                    except Exception as e:
                        yield f"data: خطأ في تصحيح {filename}: {str(e)}\n\n"
            
            yield f"data: تم الانتهاء. عدد الملفات المصححة: {corrections_made}\n\n"
            
        except Exception as e:
            yield f"data: خطأ: {str(e)}\n\n"
    
    return Response(generate(), mimetype='text/plain')

@media_bp.route('/action/scan_translation_status')
def action_scan_translation_status():
    if not is_authenticated():
        return redirect(url_for('user.login'))
    
    if is_task_running():
        return jsonify({'error': translate_text('task_already_running')}), 400
    
    success = run_background_task("scan_translation_status_task")
    
    if success:
        return jsonify({'success': True, 'message': translate_text('task_started')})
    else:
        return jsonify({'error': translate_text('failed_to_start_task')}), 500

@media_bp.route('/action/single-translate', methods=['POST'])
def action_single_translate():
    """Start translation for a single file"""
    if not is_authenticated():
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
    
    path = request.form.get('path')
    if not path:
        return jsonify({"status": "error", "message": "No path provided"}), 400
    
    # هنا يمكنك استدعاء الدالة المناسبة لبدء الترجمة
    # على سبيل المثال: success = run_background_task("single_file_translate_task", path)
    
    return jsonify({"status": "success"})

@media_bp.route('/action/single-delete', methods=['POST'])
def action_single_delete():
    """Delete translation for a single file"""
    if not is_authenticated():
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
    
    path = request.form.get('path')
    if not path:
        return jsonify({"status": "error", "message": "No path provided"}), 400
    
    # هنا يمكنك استدعاء الدالة المناسبة لحذف الترجمة
    # على سبيل المثال: success = delete_translation(path)
    
    return jsonify({"status": "success"})