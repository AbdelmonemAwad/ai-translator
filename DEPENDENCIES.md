# AI Translator - Dependencies and Requirements

## 🔐 Default Access Credentials

After installation, use these default credentials to access the system:
- **Username**: `admin`
- **Password**: `your_strong_password`
- **Important**: Change the password immediately after first login

## 🐍 Python Dependencies (requirements.txt)

### المكتبات الأساسية
```
Flask==3.0.0                 # إطار العمل الويب الأساسي
Flask-SQLAlchemy==3.1.1      # ORM قاعدة البيانات
Werkzeug==3.0.1              # أدوات Flask المساعدة
psycopg2-binary==2.9.9       # PostgreSQL connector
gunicorn==21.2.0              # خادم الويب للإنتاج
```

### المكتبات المساعدة
```
requests==2.31.0             # طلبات HTTP
psutil==5.9.6                # مراقبة النظام
pynvml==11.5.0               # إدارة GPU
email-validator==2.1.0       # التحقق من البريد الإلكتروني
```

## 🧠 تبعيات الذكاء الاصطناعي

### Whisper (تحويل الكلام لنص)
```bash
pip install openai-whisper
# أو
pip install git+https://github.com/openai/whisper.git
```

### PyTorch (للمعالجة بـ GPU)
```bash
# CPU only
pip install torch torchvision torchaudio

# GPU (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# GPU (CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## 🗄️ قاعدة البيانات

### PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install postgresql-14 postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql14-server postgresql14-contrib

# macOS
brew install postgresql@14
```

## 🎬 معالجة الوسائط

### FFmpeg (مطلوب)
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# CentOS/RHEL  
sudo yum install ffmpeg

# macOS
brew install ffmpeg

# Windows
# تحميل من https://ffmpeg.org/download.html
```

### الترميزات المدعومة
- **فيديو**: H.264, H.265, VP9, AV1, MPEG-4
- **صوت**: AAC, MP3, FLAC, Vorbis, Opus
- **حاويات**: MP4, MKV, AVI, MOV, WebM, WMV

## 🤖 خدمات الذكاء الاصطناعي

### Ollama (مطلوب للترجمة)
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# تحميل من https://ollama.ai/download

# تحميل نموذج Llama 3
ollama pull llama3
```

### النماذج المدعومة
- **llama3** (مُوصى به) - 8B parameters
- **llama3:70b** - للدقة العالية
- **codellama** - للترجمة التقنية
- **mistral** - بديل سريع

## 🌐 خوادم الوسائط (اختيارية)

### Plex Media Server
```bash
# تحميل من https://www.plex.tv/media-server-downloads/
# احصل على X-Plex-Token من إعدادات Plex
```

### Jellyfin
```bash
# Docker
docker run -d --name jellyfin -p 8096:8096 jellyfin/jellyfin

# Ubuntu/Debian
sudo apt install jellyfin
```

### Emby Server
```bash
# تحميل من https://emby.media/download.html
```

### Radarr & Sonarr
```bash
# راجع https://radarr.video/ و https://sonarr.tv/
```

## 🖥️ متطلبات النظام

### الحد الأدنى
- **نظام التشغيل**: Ubuntu 20.04+, CentOS 8+, macOS 12+, Windows 10+
- **Python**: 3.11 أو أحدث
- **ذاكرة**: 16GB RAM
- **تخزين**: 100GB متاح
- **معالج**: Intel i5/AMD Ryzen 5 أو أفضل

### المُوصى به
- **ذاكرة**: 32GB+ RAM  
- **تخزين**: 500GB+ SSD
- **معالج**: Intel i7/AMD Ryzen 7 أو أفضل
- **GPU**: NVIDIA RTX 3070+ مع 8GB+ VRAM

## 🔧 أدوات التطوير (اختيارية)

### لتطوير النظام
```bash
pip install pytest black flake8 mypy
pip install sphinx sphinx-rtd-theme  # للتوثيق
```

### محررات النصوص المُوصى بها
- **VS Code** مع Python extension
- **PyCharm Professional**
- **Vim/Neovim** مع Python plugins

## 🐳 Docker (قريباً)

### متطلبات Docker
```bash
# تثبيت Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# تثبيت Docker Compose
sudo apt install docker-compose-plugin
```

### تشغيل بـ Docker
```bash
# قريباً في الإصدار القادم
docker run -p 5000:5000 abdelmonemawad/ai-translator:latest
```

## 🔒 متطلبات الأمان

### شهادات SSL (للإنتاج)
```bash
# Let's Encrypt
sudo apt install certbot
sudo certbot --nginx -d yourdomain.com
```

### جدار الحماية
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5000/tcp  # التطبيق
sudo ufw enable

# iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

## 📊 مراقبة الأداء (اختيارية)

### أدوات المراقبة
```bash
# htop للمراقبة التفاعلية
sudo apt install htop

# nvidia-smi لمراقبة GPU
nvidia-smi

# postgres monitoring
sudo apt install postgresql-contrib
```

## 🔄 التحديث والصيانة

### تحديث التبعيات
```bash
# تحديث pip packages
pip install --upgrade pip
pip install --upgrade -r requirements.txt

# تحديث النظام
sudo apt update && sudo apt upgrade

# تحديث Ollama
ollama pull llama3  # يحدث النموذج تلقائياً
```

### نسخ احتياطية
```bash
# قاعدة البيانات
pg_dump ai_translator_db > backup.sql

# ملفات التكوين
tar -czf config_backup.tar.gz /path/to/config/
```

## 🌍 دعم البيئات المختلفة

### Replit
- جميع التبعيات مُثبتة مسبقاً
- PostgreSQL متوفر
- GPU محدود (للتجربة فقط)

### GitHub Codespaces
```bash
# .devcontainer/devcontainer.json
{
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "features": {
    "ghcr.io/devcontainers/features/postgresql:1": {}
  }
}
```

### Google Colab
```python
# تثبيت التبعيات في Colab
!pip install -r requirements.txt
!apt install postgresql postgresql-contrib
```

## 📞 الدعم الفني

إذا واجهت مشاكل في تثبيت التبعيات:

1. راجع [دليل المستخدم](USER_GUIDE_v2.1.0.md#استكشاف-الأخطاء-وإصلاحها)
2. تحقق من سجلات التثبيت
3. تواصل عبر [GitHub Issues](https://github.com/AbdelmonemAwad/ai-translator/issues)

---

**آخر تحديث**: 29 يونيو 2025  
**الإصدار**: 2.1.0