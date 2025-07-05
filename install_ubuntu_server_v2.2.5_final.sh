#!/bin/bash
# AI Translator v2.2.5 Final - Ubuntu Server Installation Script
# تثبيت الترجمان الآلي الإصدار 2.2.5 النهائي - خادم أوبونتو

set -e

echo "🚀 AI Translator v2.2.5 Final - Ubuntu Server Installation"
echo "📅 Build Date: $(date +%Y-%m-%d)"
echo "🔧 Installing with cache fixes and enhanced remote storage support..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root (sudo)${NC}"
   echo "Usage: sudo ./install_ubuntu_server_v2.2.5_final.sh"
   exit 1
fi

# Detect username and home directory
if [ -n "$SUDO_USER" ]; then
    ACTUAL_USER="$SUDO_USER"
    USER_HOME="/home/$ACTUAL_USER"
else
    ACTUAL_USER="root"
    USER_HOME="/root"
fi

echo -e "${BLUE}👤 Installing for user: $ACTUAL_USER${NC}"
echo -e "${BLUE}🏠 User home directory: $USER_HOME${NC}"

# Installation directory
INSTALL_DIR="$USER_HOME/ai-translator"
echo -e "${BLUE}📁 Installation directory: $INSTALL_DIR${NC}"

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Download and extract the application
echo -e "${YELLOW}📦 Downloading AI Translator v2.2.5 Final...${NC}"
cd "$INSTALL_DIR"

# Download from GitHub (replace with actual URL)
if command -v wget > /dev/null; then
    wget -O ai-translator-v2.2.5-final.zip "https://github.com/AbdelmonemAwad/ai-translator/releases/latest/download/ai-translator-v2.2.5-final-cache-fix.zip" || {
        echo -e "${YELLOW}⚠️  Direct download failed, using curl...${NC}"
        curl -L -o ai-translator-v2.2.5-final.zip "https://github.com/AbdelmonemAwad/ai-translator/releases/latest/download/ai-translator-v2.2.5-final-cache-fix.zip"
    }
elif command -v curl > /dev/null; then
    curl -L -o ai-translator-v2.2.5-final.zip "https://github.com/AbdelmonemAwad/ai-translator/releases/latest/download/ai-translator-v2.2.5-final-cache-fix.zip"
else
    echo -e "${RED}❌ Neither wget nor curl is available. Please install one of them.${NC}"
    exit 1
fi

# Extract the package
if command -v unzip > /dev/null; then
    unzip -q ai-translator-v2.2.5-final.zip
    rm ai-translator-v2.2.5-final.zip
else
    echo -e "${RED}❌ unzip is not available. Installing...${NC}"
    apt-get update
    apt-get install -y unzip
    unzip -q ai-translator-v2.2.5-final.zip
    rm ai-translator-v2.2.5-final.zip
fi

echo -e "${GREEN}✅ Application downloaded and extracted${NC}"

# Update system packages
echo -e "${YELLOW}🔄 Updating system packages...${NC}"
apt-get update

# Install system dependencies
echo -e "${YELLOW}🔧 Installing system dependencies...${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    postgresql \
    postgresql-contrib \
    postgresql-server-dev-all \
    nginx \
    ffmpeg \
    supervisor \
    htop \
    curl \
    wget \
    unzip \
    git \
    tree \
    nano \
    vim

echo -e "${GREEN}✅ System dependencies installed${NC}"

# Create Python virtual environment
echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}📚 Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo -e "${YELLOW}📚 Installing Python dependencies...${NC}"
if [ -f "requirements_github.txt" ]; then
    pip install -r requirements_github.txt
elif [ -f "requirements_complete.txt" ]; then
    pip install -r requirements_complete.txt
else
    echo -e "${YELLOW}⚠️  Requirements file not found, installing basic dependencies...${NC}"
    pip install flask flask-sqlalchemy psycopg2-binary gunicorn requests psutil pynvml
fi

echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Configure PostgreSQL
echo -e "${YELLOW}🗄️  Configuring PostgreSQL...${NC}"

# Start PostgreSQL service
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE ai_translator;" 2>/dev/null || echo -e "${YELLOW}⚠️  Database already exists${NC}"
sudo -u postgres psql -c "CREATE USER ai_translator WITH PASSWORD 'ai_translator_pass2024';" 2>/dev/null || echo -e "${YELLOW}⚠️  User already exists${NC}"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_translator TO ai_translator;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER ai_translator CREATEDB;" 2>/dev/null || true

echo -e "${GREEN}✅ PostgreSQL configured${NC}"

# Set up environment variables
echo -e "${YELLOW}🌍 Setting up environment variables...${NC}"
cat > "$INSTALL_DIR/.env" << EOL
DATABASE_URL=postgresql://ai_translator:ai_translator_pass2024@localhost/ai_translator
SESSION_SECRET=$(openssl rand -hex 32)
FLASK_ENV=production
FLASK_DEBUG=false
EOL

echo -e "${GREEN}✅ Environment variables configured${NC}"

# Initialize database
echo -e "${YELLOW}🗄️  Initializing database...${NC}"
cd "$INSTALL_DIR"
source venv/bin/activate

# Run database setup
python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from database_setup import init_database
    init_database()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'⚠️  Database initialization: {e}')
    # Try alternative initialization
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
        print('✅ Database tables created via app context')
    except Exception as e2:
        print(f'⚠️  Alternative initialization failed: {e2}')
"

echo -e "${GREEN}✅ Database initialization completed${NC}"

# Create systemd service
echo -e "${YELLOW}🔧 Creating systemd service...${NC}"
cat > /etc/systemd/system/ai-translator.service << EOL
[Unit]
Description=AI Translator v2.2.5 Final - Arabic Subtitle Translation System
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
Environment=DATABASE_URL=postgresql://ai_translator:ai_translator_pass2024@localhost/ai_translator
Environment=SESSION_SECRET=$(openssl rand -hex 32)
Environment=FLASK_ENV=production
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 300 --keepalive 2 --max-requests 1000 --max-requests-jitter 50 --access-logfile - --error-logfile - main:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL

echo -e "${GREEN}✅ Systemd service created${NC}"

# Configure Nginx
echo -e "${YELLOW}🌐 Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/ai-translator << 'EOL'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 2G;
    client_body_timeout 300s;
    client_header_timeout 300s;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    location /static/ {
        alias /var/www/ai-translator/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/ai-translator/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOL

# Enable Nginx site
ln -sf /etc/nginx/sites-available/ai-translator /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

echo -e "${GREEN}✅ Nginx configured${NC}"

# Create static files directory
mkdir -p /var/www/ai-translator/static
mkdir -p /var/www/ai-translator/media

# Set proper permissions
echo -e "${YELLOW}🔒 Setting file permissions...${NC}"
chown -R $ACTUAL_USER:$ACTUAL_USER "$INSTALL_DIR"
chown -R $ACTUAL_USER:$ACTUAL_USER /var/www/ai-translator

echo -e "${GREEN}✅ File permissions set${NC}"

# Start and enable services
echo -e "${YELLOW}🚀 Starting services...${NC}"
systemctl daemon-reload
systemctl enable ai-translator
systemctl start ai-translator
systemctl restart nginx

echo -e "${GREEN}✅ Services started${NC}"

# Wait for services to start
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 5

# Check service status
echo -e "${BLUE}📋 Service Status:${NC}"
echo -e "${BLUE}==================${NC}"

# Check AI Translator service
if systemctl is-active --quiet ai-translator; then
    echo -e "${GREEN}✅ AI Translator service: Running${NC}"
else
    echo -e "${RED}❌ AI Translator service: Not running${NC}"
    echo -e "${YELLOW}🔧 Checking logs...${NC}"
    journalctl -u ai-translator --no-pager -l -n 10
fi

# Check Nginx service
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx service: Running${NC}"
else
    echo -e "${RED}❌ Nginx service: Not running${NC}"
fi

# Check PostgreSQL service
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✅ PostgreSQL service: Running${NC}"
else
    echo -e "${RED}❌ PostgreSQL service: Not running${NC}"
fi

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo -e "${BLUE}==================${NC}"
echo -e "${GREEN}🎉 AI Translator v2.2.5 Final installation completed!${NC}"
echo -e "${BLUE}==================${NC}"
echo -e "${GREEN}🌐 Access your application at: http://$SERVER_IP${NC}"
echo -e "${GREEN}🔐 Default credentials:${NC}"
echo -e "${GREEN}   Username: admin${NC}"
echo -e "${GREEN}   Password: your_strong_password${NC}"
echo -e "${BLUE}==================${NC}"
echo -e "${YELLOW}📋 Useful commands:${NC}"
echo -e "${YELLOW}   Check service status: sudo systemctl status ai-translator${NC}"
echo -e "${YELLOW}   View logs: sudo journalctl -u ai-translator -f${NC}"
echo -e "${YELLOW}   Restart service: sudo systemctl restart ai-translator${NC}"
echo -e "${YELLOW}   Application directory: $INSTALL_DIR${NC}"
echo -e "${BLUE}==================${NC}"
echo -e "${GREEN}📚 Documentation: https://github.com/AbdelmonemAwad/ai-translator${NC}"
echo -e "${GREEN}🐛 Issues: https://github.com/AbdelmonemAwad/ai-translator/issues${NC}"
echo -e "${BLUE}==================${NC}"

# Final health check
echo -e "${YELLOW}🏥 Performing health check...${NC}"
sleep 2

if curl -s "http://localhost:5000" > /dev/null; then
    echo -e "${GREEN}✅ Application is responding on port 5000${NC}"
else
    echo -e "${RED}❌ Application is not responding on port 5000${NC}"
    echo -e "${YELLOW}🔧 Please check the logs: sudo journalctl -u ai-translator -f${NC}"
fi

echo -e "${BLUE}==================${NC}"
echo -e "${GREEN}🚀 Installation complete! Enjoy using AI Translator v2.2.5 Final!${NC}"
echo -e "${BLUE}==================${NC}"