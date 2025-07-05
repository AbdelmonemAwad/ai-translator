#!/usr/bin/env python3
"""
AI Translator - Main Entry Point for Replit
المترجم الذكي - نقطة البداية الرئيسية لـ Replit
"""

import os
import sys
import logging

# إعداد المسار للاستيراد
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# فحص المتطلبات الأساسية
logger.info("🔍 Checking required dependencies...")

CORE_DEPENDENCIES = {
    'ai_models': ['torch', 'faster_whisper'],
    'media_processing': ['PIL', 'cv2', 'numpy'],
    'storage': ['paramiko', 'boto3'],
    'monitoring': ['psutil', 'pynvml'],
    'web': ['flask', 'sqlalchemy', 'gunicorn']
}

missing_deps = []
for category, deps in CORE_DEPENDENCIES.items():
    for dep in deps:
        try:
            if dep == 'cv2':
                import cv2
                logger.info(f"✓ {dep} available")
            elif dep == 'torch':
                # تجنب تحميل torch إذا كان معطوباً
                try:
                    import torch
                    logger.info(f"✓ {dep} available (version: {torch.__version__})")
                except Exception as e:
                    logger.warning(f"⚠ {dep} loading issue: {str(e)}")
                    missing_deps.append(dep)
                    continue
            else:
                __import__(dep)
                logger.info(f"✓ {dep} available")
        except ImportError:
            missing_deps.append(dep)
            logger.warning(f"⚠ {dep} not found")
        except Exception as e:
            missing_deps.append(dep)
            logger.warning(f"⚠ {dep} error: {str(e)}")

if missing_deps:
    logger.warning(f"Missing dependencies: {', '.join(missing_deps)}")
    logger.info("Run: pip install -r requirements_complete.txt")

# استيراد التطبيق الأساسي
logger.info("✓ Attempting to import original AI Translator...")

try:
    from app import app
    logger.info("✓ Successfully imported original AI Translator v2.2.5")
    
    # فحص إضافي للبرامج المساعدة المتقدمة
    logger.info("🔧 Checking advanced components...")
    
    # فحص GPU
    try:
        import pynvml
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        logger.info(f"✓ NVIDIA GPUs detected: {gpu_count}")
    except:
        logger.info("ℹ No NVIDIA GPUs detected (normal in cloud environments)")
    
    # فحص Ollama
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            logger.info(f"✓ Ollama running with {len(models)} models")
        else:
            logger.info("ℹ Ollama not running (will start on demand)")
    except:
        logger.info("ℹ Ollama not accessible (install with: curl -fsSL https://ollama.ai/install.sh | sh)")
    
    # فحص FFmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            logger.info("✓ FFmpeg available")
        else:
            logger.warning("⚠ FFmpeg not working properly")
    except:
        logger.warning("⚠ FFmpeg not found")
    
    # فحص قاعدة البيانات
    db_url = os.environ.get("DATABASE_URL")
    if db_url and 'postgresql' in db_url:
        logger.info("✓ PostgreSQL database configured")
    elif db_url:
        logger.info(f"✓ Database configured: {db_url.split('://')[0]}")
    else:
        logger.info("ℹ Using SQLite database (fallback)")

except Exception as e:
    logger.error(f"❌ Error importing AI Translator: {e}")
    
    # إنشاء تطبيق بسيط للطوارئ
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return f'''
        <h1>AI Translator - الترجمان الذكي</h1>
        <p>خطأ في تحميل التطبيق الأساسي</p>
        <p>Error loading main application</p>
        <p>Error: {str(e)}</p>
        '''

# تصدير التطبيق لـ Gunicorn
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)