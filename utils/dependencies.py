#!/usr/bin/env python3
"""
وحدة إدارة التبعيات للترجمان الآلي
"""

import os
import sys
import json
import logging
import subprocess
import platform
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def get_ai_status():
    """
الحصول على حالة نظام الذكاء الاصطناعي (دالة احتياطية)
    """
    try:
        from ai_integration_workaround import get_ai_status as ai_status_func
        return ai_status_func()
    except ImportError:
        logger.warning("AI Integration Workaround module not found")
        return {
            "status": "limited",
            "message": "AI integration module not available",
            "system_ready": False,
            "components": {}
        }

def get_dependencies_status():
    """الحصول على حالة جميع التبعيات"""
    # استيراد المكتبات المطلوبة
    import subprocess
    import os
    import sys
    import platform
    
    try:
        # قائمة البرامج المساعدة المطلوبة
        dependencies = {
            'ai_models': {
                'torch': {'required': True, 'category': 'ai_libraries'},
                'faster_whisper': {'required': True, 'category': 'ai_libraries'},
                'transformers': {'required': False, 'category': 'ai_libraries'},
                'accelerate': {'required': False, 'category': 'ai_libraries'},
            },
            'media_processing': {
                'PIL': {'required': True, 'category': 'media_processing'},
                'cv2': {'required': True, 'category': 'media_processing'},
                'numpy': {'required': True, 'category': 'media_processing'},
                'ffmpeg': {'required': True, 'category': 'media_processing', 'type': 'system'},
            },
            'system_utilities': {
                'psutil': {'required': True, 'category': 'system_utilities'},
                'pynvml': {'required': False, 'category': 'system_utilities'},
                'paramiko': {'required': True, 'category': 'system_utilities'},
                'boto3': {'required': True, 'category': 'system_utilities'},
            },
            'web_framework': {
                'flask': {'required': True, 'category': 'web_framework'},
                'sqlalchemy': {'required': True, 'category': 'web_framework'},
                'gunicorn': {'required': True, 'category': 'web_framework'},
            },
            'gpu_drivers': {
                'nvidia-smi': {'required': False, 'category': 'gpu_drivers', 'type': 'system'},
                'nvidia-ml-py3': {'required': False, 'category': 'gpu_drivers'},
                'cupy-cuda12x': {'required': False, 'category': 'gpu_drivers'},
                'pycuda': {'required': False, 'category': 'gpu_drivers'},
            },
            'ai_models_files': {
                'whisper-base': {'required': False, 'category': 'ai_models_files', 'type': 'model'},
                'whisper-medium': {'required': False, 'category': 'ai_models_files', 'type': 'model'},
                'ollama-llama3': {'required': False, 'category': 'ai_models_files', 'type': 'model'},
                'ollama-mistral': {'required': False, 'category': 'ai_models_files', 'type': 'model'},
            }
        }
        
        # فحص حالة كل مكتبة
        status_result = {}
        for category, packages in dependencies.items():
            status_result[category] = {}
            for package, info in packages.items():
                try:
                    if info.get('type') == 'system':
                        # فحص برامج النظام
                        if package == 'nvidia-smi':
                            result = subprocess.run(['nvidia-smi', '--version'], 
                                                  capture_output=True, text=True)
                            if result.returncode == 0:
                                version = result.stdout.split('\n')[0].split('v')[-1] if 'v' in result.stdout else 'installed'
                                status = 'installed'
                            else:
                                version = None
                                status = 'not_installed'
                        elif package == 'ffmpeg':
                            # التحقق من تثبيت FFmpeg
                            from utils.settings import get_setting
                            ffmpeg_path = get_setting('UTILITIES.FFMPEG_PATH', '')
                            if ffmpeg_path and os.path.exists(ffmpeg_path):
                                # استخدام المسار المخصص
                                cmd = [ffmpeg_path, '-version']
                            else:
                                # محاولة استخدام FFmpeg من مسار النظام
                                cmd = ['ffmpeg', '-version']
                            
                            try:
                                result = subprocess.run(cmd, capture_output=True, text=True)
                                if result.returncode == 0:
                                    # استخراج إصدار FFmpeg من النتيجة
                                    version_line = result.stdout.split('\n')[0]
                                    if 'ffmpeg version' in version_line.lower():
                                        version = version_line.split('ffmpeg version')[1].strip().split(' ')[0]
                                    else:
                                        version = 'installed'
                                    status = 'installed'
                                else:
                                    version = None
                                    status = 'not_installed'
                            except:
                                version = None
                                status = 'not_installed'
                        else:
                            status = 'not_installed'
                            version = None
                    elif info.get('type') == 'model':
                        # فحص نماذج الذكاء الاصطناعي
                        if 'whisper' in package:
                            # فحص نماذج Whisper
                            import os
                            from pathlib import Path
                            home_dir = Path.home()
                            whisper_cache = home_dir / '.cache' / 'whisper'
                            model_name = package.split('-')[1] + '.pt'
                            model_path = whisper_cache / model_name
                            
                            if model_path.exists():
                                file_size = model_path.stat().st_size / (1024 * 1024)  # MB
                                version = f"{file_size:.1f}MB"
                                status = 'installed'
                            else:
                                version = None
                                status = 'not_installed'
                        elif 'ollama' in package:
                            # فحص نماذج Ollama
                            try:
                                import requests
                                system = platform.system()
                                
                                # محاولة الاتصال بخدمة Ollama
                                try:
                                    response = requests.get('http://localhost:11434/api/tags', timeout=2)
                                    if response.status_code == 200:
                                        models = response.json().get('models', [])
                                        model_name = package.split('-')[1]
                                        found_model = any(model_name in model.get('name', '') for model in models)
                                        if found_model:
                                            status = 'installed'
                                            version = 'available'
                                        else:
                                            status = 'not_installed'
                                            version = None
                                    else:
                                        status = 'not_installed'
                                        version = None
                                except requests.exceptions.ConnectionError:
                                    # إذا لم نتمكن من الاتصال بالخدمة، نتحقق من وجود Ollama نفسه
                                    if system == 'Windows':
                                        # في ويندوز، نتحقق من وجود الملف التنفيذي
                                        ollama_path = os.path.expandvars('%LOCALAPPDATA%\\ollama\\ollama.exe')
                                        if os.path.exists(ollama_path):
                                            status = 'installed_not_running'
                                            version = 'not_running'
                                        else:
                                            status = 'not_installed'
                                            version = None
                                    elif system == 'Darwin':  # macOS
                                        # في ماك، نتحقق من وجود الملف التنفيذي
                                        ollama_path = '/usr/local/bin/ollama'
                                        if os.path.exists(ollama_path):
                                            status = 'installed_not_running'
                                            version = 'not_running'
                                        else:
                                            status = 'not_installed'
                                            version = None
                                    else:  # Linux وأنظمة أخرى
                                        # في لينكس، نتحقق من وجود الملف التنفيذي
                                        ollama_path = '/usr/local/bin/ollama'
                                        if os.path.exists(ollama_path):
                                            status = 'installed_not_running'
                                            version = 'not_running'
                                        else:
                                            status = 'not_installed'
                                            version = None
                            except:
                                status = 'not_installed'
                                version = None
                        else:
                            status = 'not_installed'
                            version = None
                    else:
                        # فحص مكتبات Python العادية
                        if package == 'cv2':
                            import cv2
                            version = cv2.__version__
                        elif package == 'PIL':
                            from PIL import Image
                            version = getattr(Image, '__version__', 'unknown')
                        else:
                            module = __import__(package)
                            version = getattr(module, '__version__', 'unknown')
                        status = 'installed'
                    
                    status_result[category][package] = {
                        'status': status,
                        'version': version,
                        'required': info['required'],
                        'category': info['category'],
                        'type': info.get('type', 'python'),
                        'installed': status == 'installed' or status == 'installed_not_running'
                    }
                except (ImportError, subprocess.CalledProcessError, FileNotFoundError):
                    status_result[category][package] = {
                        'status': 'not_installed',
                        'version': None,
                        'required': info['required'],
                        'category': info['category'],
                        'type': info.get('type', 'python'),
                        'installed': False
                    }
        
        # إضافة حالة AI system
        ai_status = get_ai_status()
        status_result['ai_system'] = ai_status
        
        # إضافة ملخص للنتائج
        status_result['summary'] = {
            'total_packages': sum(len(packages) for packages in dependencies.values()),
            'installed_count': sum(
                1 for category in status_result.values()
                for package in category.values()
                if isinstance(package, dict) and package.get('status') == 'installed'
            ),
            'system_ready': ai_status.get('system_ready', False)
        }
        
        return status_result
        
    except Exception as e:
        logger.error(f"Error getting dependencies status: {str(e)}")
        return {}