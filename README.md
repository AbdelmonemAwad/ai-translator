# AI Translator - Advanced Multilingual Subtitle Translation System

<div align="center">

![AI Translator Logo](https://img.shields.io/badge/AI-Translator-2563eb?style=for-the-badge&logo=robot&logoColor=white)
![Version](https://img.shields.io/badge/Version-2.2.5-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-GPL%20v3-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Ubuntu%20Server-orange?style=for-the-badge&logo=ubuntu)

**Advanced AI-powered translation system for converting movies and TV shows to Arabic with exceptional accuracy and efficiency.**

[![Quick Install](https://img.shields.io/badge/Quick%20Install-One%20Command-brightgreen?style=for-the-badge&logo=terminal&logoColor=white)](https://github.com/AbdelmonemAwad/ai-translator/blob/main/QUICK_INSTALL.md)

```bash
curl -fsSL https://raw.githubusercontent.com/AbdelmonemAwad/ai-translator/main/install.sh | bash
```

[Features](#features) • [Installation](#installation) • [Documentation](#documentation) • [Support](#support)

</div>

## 🎯 Overview

AI Translator is a comprehensive media translation system designed to automatically translate movies and TV shows from English to Arabic using cutting-edge AI technologies. The system provides a complete web interface for managing and monitoring all aspects of the translation process.

## 🌟 Key Features

### 🤖 AI-Powered Translation
- **Advanced Speech Recognition**: Faster-Whisper integration for accurate audio-to-text conversion
- **Intelligent Translation**: Ollama LLM with specialized Arabic translation models
- **Subtitle Generation**: Automatic SRT file creation with proper Arabic text encoding
- **Batch Processing**: Process multiple files simultaneously with queue management

### 🎬 Media Server Integration
- **Plex Media Server**: Complete library synchronization with poster images
- **Jellyfin**: API integration with metadata and poster retrieval
- **Emby Media Server**: Full API support with user authentication
- **Kodi Media Center**: JSON-RPC integration for home media centers
- **Radarr**: Movie management with automatic metadata retrieval
- **Sonarr**: TV series management with episode tracking

### 🖥️ Professional Web Interface
- **Modern Arabic RTL Design**: Beautiful dark theme with Arabic typography
- **Responsive Layout**: Mobile-optimized interface with collapsible sidebar
- **Real-time Monitoring**: Live progress tracking and system status updates
- **Multi-language Support**: Complete Arabic/English translation system
- **Advanced Settings**: Tabbed configuration interface with file browser

### 📊 System Monitoring & Management
- **Hardware Detection**: Automatic CPU, GPU, memory, and storage monitoring
- **Performance Tracking**: Real-time system resource usage with alerts
- **Process Management**: Background task monitoring with detailed logging
- **Database Administration**: Built-in PostgreSQL management tools
- **Diagnostic Tools**: Comprehensive system health assessment

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (Python 3.9+ supported)
- **PostgreSQL 14+** for data storage
- **FFmpeg** for video/audio processing
- **4GB+ RAM** recommended for AI processing
- **Ubuntu 22.04+** or **Debian 11+** (recommended)

### Quick Installation (Recommended)

**One-line installation for Ubuntu/Debian:**

```bash
curl -fsSL https://raw.githubusercontent.com/AbdelmonemAwad/ai-translator/main/install.sh | bash
```

This command automatically:
- Installs all system dependencies (Python, PostgreSQL, FFmpeg)
- Clones the repository and sets up virtual environment
- Configures database with secure credentials
- Creates systemd service for automatic startup
- Installs Ollama for AI translation

### Manual Installation

<details>
<summary>Click to expand manual installation steps</summary>

1. **Clone the Repository**
```bash
git clone https://github.com/AbdelmonemAwad/ai-translator.git
cd ai-translator
```

2. **Install Dependencies**
```bash
# Install Python dependencies
pip install -r requirements_github.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install ffmpeg postgresql postgresql-contrib python3-venv
```

3. **Configure Database**
```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE ai_translator;
CREATE USER ai_translator WITH PASSWORD 'ai_translator_pass2024';
GRANT ALL PRIVILEGES ON DATABASE ai_translator TO ai_translator;
\q
```

4. **Initialize Application**
```bash
# Set environment variables
export DATABASE_URL="postgresql://ai_translator:ai_translator_pass2024@localhost/ai_translator"
export SESSION_SECRET="your-secret-key-here"

# Initialize database
python database_setup.py

# Start the application
python main.py
```

</details>

### Access Web Interface

```
Open browser to: http://localhost:5000
Default credentials: admin / your_strong_password
```

## 🏗️ Architecture

### Backend Components
- **Flask Web Framework**: RESTful API with session-based authentication
- **SQLAlchemy ORM**: Database management with PostgreSQL backend
- **Background Processing**: Asynchronous task execution with psutil monitoring
- **AI Integration**: Modular AI system with fallback capabilities

### Frontend Design
- **Jinja2 Templates**: Server-side rendering with Arabic RTL support
- **Responsive CSS**: Mobile-first design with professional dark theme
- **Vanilla JavaScript**: Dynamic interactions without heavy frameworks
- **Real-time Updates**: WebSocket-like polling for live status updates

### AI Pipeline
1. **Audio Extraction**: FFmpeg extracts audio from video files
2. **Speech Recognition**: Faster-Whisper converts speech to English text
3. **Translation**: Ollama LLM translates English to Arabic
4. **Subtitle Generation**: Creates properly formatted SRT files

## 📋 System Requirements

### Minimum Requirements
- **CPU**: 2+ cores, 2.0 GHz
- **RAM**: 4GB (8GB recommended for AI processing)
- **Storage**: 10GB free space
- **Network**: Internet connection for media server APIs

### Recommended Setup
- **CPU**: 4+ cores, 3.0 GHz
- **RAM**: 16GB+ for optimal AI performance
- **GPU**: NVIDIA GPU with 6GB+ VRAM (optional but recommended)
- **Storage**: SSD with 50GB+ free space

### Supported Platforms
- **Ubuntu Server 22.04+** (Primary)
- **Debian 11+** (Tested)
- **CentOS 8+** (Community support)
- **Docker** (Container deployment available)

## 🔧 Configuration

### Media Server Setup
Configure your media servers in the Settings panel:

```python
# Radarr Configuration
RADARR_URL = "http://localhost:7878"
RADARR_API_KEY = "your_api_key_here"

# Sonarr Configuration  
SONARR_URL = "http://localhost:8989"
SONARR_API_KEY = "your_api_key_here"
```

### AI Model Configuration
```python
# Whisper Models (choose based on accuracy vs speed)
WHISPER_MODEL = "medium.en"  # Options: tiny, base, small, medium, large

# Ollama Models (for translation)
OLLAMA_MODEL = "llama3"      # Options: llama3, mistral, qwen
```

### Path Mapping
```python
# Map remote storage to local mount points
REMOTE_MOVIES_PATH = "/volume1/movies"
LOCAL_MOVIES_MOUNT = "/mnt/movies"
```

## 🎯 Usage Examples

### Translate Single File
```python
from process_video import main as process_video

# Process a single video file
result = process_video("/path/to/movie.mp4")
print(f"Translation status: {result['status']}")
```

### Batch Translation
```python
# Use the web interface for batch operations:
# 1. Navigate to File Management
# 2. Select multiple files
# 3. Click "Start Batch Translation"
```

### API Usage
```bash
# Get system status
curl http://localhost:5000/api/status

# Get file list
curl http://localhost:5000/api/files

# Start translation
curl -X POST http://localhost:5000/action/start-batch
```

## 📁 Project Structure

```
ai-translator/
├── app.py                    # Main Flask application
├── main.py                   # Application entry point
├── models.py                 # Database models
├── database_setup.py         # Database initialization
├── background_tasks.py       # Async task processing
├── process_video.py          # Video processing pipeline
├── ai_integration_workaround.py  # AI system integration
├── auth_manager.py           # Authentication system
├── gpu_manager.py            # GPU detection and management
├── system_monitor.py         # System monitoring tools
├── translations.py           # Multilingual support
├── templates/                # HTML templates
│   ├── layout.html          # Base template
│   ├── dashboard.html       # Main dashboard
│   ├── settings.html        # Configuration interface
│   └── ...
├── static/                   # CSS, JS, and assets
│   ├── css/style.css        # Main stylesheet
│   ├── js/                  # JavaScript files
│   └── images/              # Image assets
├── services/                 # External service integrations
│   ├── media_services.py    # Media server APIs
│   └── remote_storage.py    # Remote storage management
└── requirements.txt          # Python dependencies
```

## 🔒 Security Features

- **Session-based Authentication**: Secure user authentication without external dependencies
- **CSRF Protection**: Built-in cross-site request forgery protection
- **Path Validation**: Prevents directory traversal attacks
- **SQL Injection Prevention**: Parameterized queries with SQLAlchemy
- **Input Sanitization**: All user inputs are validated and sanitized

## 🌐 Supported Video Formats

The system supports 16 video formats:
- **MP4, MKV, AVI** (Most common)
- **MOV, WMV, FLV** (Standard formats)  
- **M4V, WEBM, OGV** (Web formats)
- **TS, M2TS, VOB** (Broadcast formats)
- **ASF, RM, RMVB** (Legacy formats)
- **3GP** (Mobile format)

## 📊 Performance Benchmarks

### Translation Speed (approximate)
- **1-hour movie**: 15-30 minutes processing time
- **TV episode (45 min)**: 10-20 minutes processing time
- **Batch processing**: 3-5 files simultaneously

### System Requirements by Workload
- **Light usage**: 2GB RAM, 2 CPU cores
- **Medium usage**: 8GB RAM, 4 CPU cores
- **Heavy usage**: 16GB RAM, 8 CPU cores, GPU acceleration

## 🛠️ Development

### Setting Up Development Environment
```bash
# Clone repository
git clone https://github.com/AbdelmonemAwad/ai-translator.git
cd ai-translator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run in development mode
export FLASK_ENV=development
python main.py
```

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Testing
```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Check code coverage
python -m pytest --cov=app tests/
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Documentation**: [GitHub Wiki](https://github.com/AbdelmonemAwad/ai-translator/wiki)
- **Issues**: [GitHub Issues](https://github.com/AbdelmonemAwad/ai-translator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AbdelmonemAwad/ai-translator/discussions)

## 🚀 Roadmap

### Version 2.3.0 (Q3 2025)
- [ ] Docker containerization
- [ ] Advanced GPU management
- [ ] Subtitle synchronization tools
- [ ] Multi-language output support

### Version 2.4.0 (Q4 2025)
- [ ] Cloud storage integration (AWS S3, Google Cloud)
- [ ] Real-time translation preview
- [ ] Advanced subtitle editing tools
- [ ] Performance optimization

## 🏆 Acknowledgments

- **OpenAI Whisper** for speech recognition technology
- **Ollama** for local LLM inference
- **FFmpeg** for multimedia processing
- **Flask** and **SQLAlchemy** for web framework
- **Bootstrap** and **Feather Icons** for UI components

---

**AI Translator v2.2.5** - Built with ❤️ for the Arabic-speaking community