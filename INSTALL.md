# AI Translator Installation Guide
# دليل تنصيب المترجم الآلي

This guide provides detailed instructions for installing AI Translator on Ubuntu Server with Casa OS support.

## 📋 Pre-Installation Requirements

### System Requirements
- **Operating System**: Ubuntu Server 22.04 LTS or higher
- **Memory**: Minimum 4GB RAM (8GB+ recommended for multiple media services)
- **Storage**: Minimum 20GB free space (100GB+ recommended)
- **CPU**: 4+ cores (8+ cores recommended for optimal performance)
- **GPU**: NVIDIA Graphics Card with 8GB+ VRAM (required for AI processing)
- **Network**: Internet connection for downloading dependencies and media service APIs
- **Permissions**: Root or sudo access

### Media Services Integration (Version 2.1.0)
AI Translator now supports complete integration with 6 major media platforms:

#### Media Servers
- **Plex Media Server**: Token-based authentication with full library synchronization
- **Jellyfin Media Server**: API key integration with metadata and poster retrieval
- **Emby Media Server**: Complete API support with user authentication
- **Kodi Media Center**: JSON-RPC integration for home media centers

#### Content Managers
- **Radarr**: Movie management with automatic metadata and poster retrieval
- **Sonarr**: TV series management with episode tracking and library updates

#### New Features in 2.1.0
- Real-time service connection testing and status monitoring
- Automatic media library synchronization from all configured services
- Centralized media services manager with unified API endpoints
- Enhanced error handling and connection management

### Recommended Specifications
- **GPU**: NVIDIA RTX series or better with 8GB+ VRAM
- **SSD**: Solid State Drive for better I/O performance
- **Casa OS**: For easier application management

## 🚀 Quick Installation (Recommended)

### One-Command Installation
```bash
# Download the installer
wget https://raw.githubusercontent.com/AbdelmonemAwad/ai-translator/main/install.sh

# Make it executable
chmod +x install.sh

# Run the installer (requires sudo)
sudo ./install.sh
```

The installer will:
1. ✅ Check system compatibility
2. ✅ Install all required dependencies
3. ✅ Set up PostgreSQL database
4. ✅ Install and configure Ollama with Llama 3
5. ✅ Download Whisper models
6. ✅ Configure web server (Nginx)
7. ✅ Set up systemd services
8. ✅ Configure firewall
9. ✅ Create default admin user
10. ✅ Start all services

**Installation time**: 15-30 minutes (depending on internet speed)

## 🛠️ Manual Installation

If you prefer manual installation or need custom configuration:

### Step 1: System Dependencies
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    curl wget git build-essential \
    python3.11 python3.11-dev python3.11-venv python3-pip \
    postgresql postgresql-contrib postgresql-server-dev-all \
    ffmpeg nginx supervisor ufw htop unzip
```

### Step 2: Python Environment
```bash
# Set Python 3.11 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Install pip for Python 3.11
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.11
```

### Step 3: PostgreSQL Database
```bash
# Start PostgreSQL service
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE ai_translator_db;
CREATE USER ai_translator WITH PASSWORD 'ai_translator_2025';
GRANT ALL PRIVILEGES ON DATABASE ai_translator_db TO ai_translator;
ALTER USER ai_translator CREATEDB;
EOF
```

### Step 4: Ollama Installation
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Download Llama 3 model (this takes time)
ollama pull llama3
```

### Step 5: Application Installation
```bash
# Create application directory
sudo mkdir -p /opt/ai-translator
cd /opt/ai-translator

# Clone application (replace with actual repository)
sudo git clone https://github.com/username/ai-translator.git .

# Create virtual environment
sudo python3.11 -m venv venv

# Activate virtual environment and install dependencies
sudo venv/bin/pip install --upgrade pip
sudo venv/bin/pip install \
    flask flask-sqlalchemy gunicorn psycopg2-binary \
    psutil pynvml requests email-validator werkzeug
```

### Step 6: Create Application User
```bash
# Create system user for the application
sudo useradd --system --home-dir /opt/ai-translator --shell /bin/bash ai-translator

# Set proper permissions
sudo chown -R ai-translator:ai-translator /opt/ai-translator
```

### Step 7: Database Initialization
```bash
# Initialize database
sudo -u ai-translator bash -c "
    cd /opt/ai-translator
    source venv/bin/activate
    python database_setup.py
"
```

### Step 8: Systemd Service
```bash
# Create systemd service file
sudo tee /etc/systemd/system/ai-translator.service > /dev/null << EOF
[Unit]
Description=AI Translator Web Application
After=network.target postgresql.service ollama.service
Wants=postgresql.service ollama.service

[Service]
Type=exec
User=ai-translator
Group=ai-translator
WorkingDirectory=/opt/ai-translator
Environment=PATH=/opt/ai-translator/venv/bin
Environment=DATABASE_URL=postgresql://ai_translator:ai_translator_2025@localhost:5432/ai_translator_db
Environment=SESSION_SECRET=$(openssl rand -base64 32)
Environment=FLASK_ENV=production
ExecStart=/opt/ai-translator/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable ai-translator
```

### Step 9: Nginx Configuration
```bash
# Create Nginx site configuration
sudo tee /etc/nginx/sites-available/ai-translator > /dev/null << EOF
server {
    listen 80;
    server_name localhost;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    location /static {
        alias /opt/ai-translator/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site and restart Nginx
sudo ln -sf /etc/nginx/sites-available/ai-translator /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

### Step 10: Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

### Step 11: Start Services
```bash
# Start all services
sudo systemctl start ai-translator
sudo systemctl start nginx

# Check service status
sudo systemctl status ai-translator
sudo systemctl status nginx
```

## 🏠 Casa OS Integration

If you have Casa OS installed, the installer automatically creates an app entry:

### Manual Casa OS Setup
```bash
# Create Casa OS app configuration
sudo mkdir -p /var/lib/casaos/apps

sudo tee /var/lib/casaos/apps/ai-translator.json > /dev/null << EOF
{
    "name": "AI Translator",
    "icon": "🤖",
    "description": "Advanced AI-powered translation system for movies and TV shows",
    "url": "http://localhost:80",
    "category": "Media",
    "port": 80,
    "tags": ["ai", "translation", "media", "subtitles"],
    "author": "عبدالمنعم عوض",
    "version": "1.0.0"
}
EOF
```

## ✅ Post-Installation Verification

### 1. Check Services
```bash
# Verify all services are running
sudo systemctl status ai-translator
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status ollama

# Check if Ollama has models
ollama list
```

### 2. Database Verification
```bash
# Test database connection
sudo -u postgres psql -d ai_translator_db -c "\dt"
```

### 3. Web Interface Test
```bash
# Test local access
curl -I http://localhost

# Should return: HTTP/1.1 200 OK or 302 Found
```

### 4. Application Logs
```bash
# View application logs
sudo journalctl -u ai-translator -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🔧 Default Configuration

After installation, you can access the application with these defaults:

- **URL**: `http://your-server-ip`
- **Username**: `admin`
- **Password**: `your_strong_password`

**⚠️ Important**: Change the default password immediately after first login!

## 🔄 Updates and Maintenance

### Updating the Application
```bash
# Pull latest changes
cd /opt/ai-translator
sudo -u ai-translator git pull origin main

# Restart services
sudo systemctl restart ai-translator
```

### Database Backup
```bash
# Create database backup
sudo -u postgres pg_dump ai_translator_db > ai_translator_backup_$(date +%Y%m%d_%H%M%S).sql
```

### Log Rotation
The installer configures automatic log rotation. Logs are kept for 30 days by default.

## ❌ Uninstallation

To completely remove AI Translator:

```bash
# Stop services
sudo systemctl stop ai-translator nginx

# Remove service files
sudo systemctl disable ai-translator
sudo rm /etc/systemd/system/ai-translator.service
sudo systemctl daemon-reload

# Remove application
sudo rm -rf /opt/ai-translator

# Remove user
sudo userdel ai-translator

# Remove database (optional)
sudo -u postgres psql -c "DROP DATABASE ai_translator_db;"
sudo -u postgres psql -c "DROP USER ai_translator;"

# Remove Nginx site
sudo rm /etc/nginx/sites-enabled/ai-translator
sudo rm /etc/nginx/sites-available/ai-translator
sudo systemctl restart nginx
```

## 🆘 Troubleshooting

### Service Won't Start
```bash
# Check detailed logs
sudo journalctl -u ai-translator -n 50 --no-pager

# Common fixes:
sudo systemctl restart postgresql
sudo systemctl restart ollama
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
sudo -u postgres psql -c "\l"

# Reset database user password
sudo -u postgres psql -c "ALTER USER ai_translator PASSWORD 'ai_translator_2025';"
```

### Ollama Issues
```bash
# Restart Ollama
sudo systemctl restart ollama

# Redownload model if needed
ollama pull llama3
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R ai-translator:ai-translator /opt/ai-translator
sudo chmod +x /opt/ai-translator/install.sh
```

## 📞 Support

For additional help:
1. Check the built-in documentation at `/docs`
2. Review application logs in the web interface
3. Check system logs with `journalctl`
4. Visit the project repository for issues and discussions

---

**Installation completed successfully!** 🎉

Your AI Translator is now ready to process media files and generate Arabic subtitles.