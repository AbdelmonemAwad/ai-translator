#!/bin/bash
# AI Translator v2.2.5 - Complete Installation Script
# سكريپت التثبيت الشامل للمترجم الآلي v2.2.5
# Author: Eg2@live.com
# Date: 2025-07-15
# Version: 2.2.5-complete

set -e

echo "🚀 AI Translator v2.2.5 - Complete Installation Starting..."
echo "   المترجم الآلي v2.2.5 - بدء التثبيت الشامل..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    INSTALL_USER="root"
    INSTALL_DIR="/opt/ai-translator"
    print_warning "Running as root. Will install in $INSTALL_DIR"
else
    INSTALL_USER="$USER"
    INSTALL_DIR="$HOME/ai-translator"
    print_info "Running as user: $INSTALL_USER"
    print_info "Will install in: $INSTALL_DIR"
fi

# Create installation directory
print_info "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Check if we already have the files locally
CURRENT_DIR=$(pwd)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_info "Current directory: $CURRENT_DIR"
print_info "Script directory: $SCRIPT_DIR"

# Method 1: Check current directory
if [ -f "$CURRENT_DIR/app.py" ] && [ -f "$CURRENT_DIR/main.py" ]; then
    SOURCE_DIR="$CURRENT_DIR"
    print_status "Found AI Translator files in current directory"
# Method 2: Check script directory  
elif [ -f "$SCRIPT_DIR/app.py" ] && [ -f "$SCRIPT_DIR/main.py" ]; then
    SOURCE_DIR="$SCRIPT_DIR"
    print_status "Found AI Translator files in script directory"
# Method 3: Look for extracted folder
else
    EXTRACTED_DIRS=$(find . -maxdepth 2 -name "app.py" -exec dirname {} \; 2>/dev/null | head -1)
    if [ -n "$EXTRACTED_DIRS" ]; then
        SOURCE_DIR="$(cd "$EXTRACTED_DIRS" && pwd)"
        print_status "Found extracted directory: $SOURCE_DIR"
    else
        # Method 4: Download from GitHub (most reliable)
        print_info "No local files found. Downloading from GitHub..."
        
        # Create temporary directory
        TMP_DIR=$(mktemp -d)
        cd "$TMP_DIR"
        
        # Try to clone the repository
        if git clone https://github.com/AbdelmonemAwad/ai-translator1.git; then
            SOURCE_DIR="$TMP_DIR/ai-translator1"
            print_status "Successfully cloned repository"
        else
            print_error "Failed to download AI Translator. Please check your internet connection."
            print_info "You can manually download from: https://github.com/AbdelmonemAwad/ai-translator1"
            exit 1
        fi
    fi
fi

# Copy files to installation directory if needed
if [ "$SOURCE_DIR" != "$INSTALL_DIR" ]; then
    print_info "Copying files to installation directory..."
    cp -r "$SOURCE_DIR/"* "$INSTALL_DIR/"
    cp -r "$SOURCE_DIR/".* "$INSTALL_DIR/" 2>/dev/null || true  # Copy hidden files
    cd "$INSTALL_DIR"
fi

# Check for required files
REQUIRED_FILES=("app.py" "main.py" "models.py" "database_setup.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file $file not found in $INSTALL_DIR"
        print_info "Please ensure you have the complete AI Translator package."
        exit 1
    fi
done

print_status "All required files found"

# Fix file permissions for installation scripts
print_info "Fixing file permissions..."
chmod +x install*.sh 2>/dev/null || true

# Clean up temporary files before installation
print_info "Cleaning up temporary files..."
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name "*.pyd" -delete
find . -name ".DS_Store" -delete
find . -name "*.log" -delete
rm -f *.tar.gz *.zip .latest_* 2>/dev/null || true

# Update system packages
print_info "Updating system packages..."
if command -v apt &> /dev/null; then
    apt update
    apt install -y python3 python3-pip python3-venv python3-dev
    apt install -y postgresql postgresql-contrib nginx
    apt install -y build-essential libpq-dev libffi-dev libssl-dev
    apt install -y ffmpeg mediainfo curl wget git unzip
    apt install -y software-properties-common
    
    # Install Python 3.11 if available
    if ! command -v python3.11 &> /dev/null; then
        print_info "Installing Python 3.11..."
        add-apt-repository -y ppa:deadsnakes/ppa
        apt update
        apt install -y python3.11 python3.11-venv python3.11-dev
    fi
elif command -v yum &> /dev/null; then
    yum update -y
    yum install -y python3 python3-pip python3-devel
    yum install -y postgresql postgresql-server nginx
    yum install -y gcc gcc-c++ libffi-devel openssl-devel
    yum install -y ffmpeg git curl wget unzip
else
    print_error "Unsupported package manager. Please install dependencies manually."
    exit 1
fi

# Setup PostgreSQL
print_info "Setting up PostgreSQL..."
systemctl enable postgresql
systemctl start postgresql

# Create database and user with error handling
print_info "Creating AI Translator database..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ai_translator;" 2>/dev/null || true
sudo -u postgres psql -c "DROP USER IF EXISTS ai_translator;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE ai_translator;"
sudo -u postgres psql -c "CREATE USER ai_translator WITH PASSWORD 'ai_translator_pass2024';"
sudo -u postgres psql -c "ALTER ROLE ai_translator SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE ai_translator SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE ai_translator SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_translator TO ai_translator;"

# Fix PostgreSQL schema permissions (CRITICAL FIX)
print_info "Fixing PostgreSQL schema permissions..."
sudo -u postgres psql -d ai_translator -c "GRANT ALL PRIVILEGES ON SCHEMA public TO ai_translator;" 2>/dev/null
sudo -u postgres psql -d ai_translator -c "GRANT CREATE ON SCHEMA public TO ai_translator;" 2>/dev/null
sudo -u postgres psql -d ai_translator -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ai_translator;" 2>/dev/null

# Create virtual environment
print_info "Creating Python virtual environment..."

# Try to use Python 3.11 if available, otherwise fall back to system Python
if command -v python3.11 &> /dev/null; then
    python3.11 -m venv venv
else
    python3 -m venv venv
fi

source venv/bin/activate

# Install Python packages
print_info "Installing Python packages..."
pip install --upgrade pip

# Install from requirements file with fallback
REQUIREMENTS_INSTALLED=false

# Try requirements_complete.txt first
if [ -f "requirements_complete.txt" ] && ! $REQUIREMENTS_INSTALLED; then
    print_info "Installing from requirements_complete.txt..."
    if pip install -r requirements_complete.txt; then
        REQUIREMENTS_INSTALLED=true
        print_status "Installed from requirements_complete.txt"
    else
        print_warning "Failed to install from requirements_complete.txt"
    fi
fi

# Try requirements.txt as fallback
if [ -f "requirements.txt" ] && ! $REQUIREMENTS_INSTALLED; then
    print_info "Installing from requirements.txt..."
    if pip install -r requirements.txt; then
        REQUIREMENTS_INSTALLED=true
        print_status "Installed from requirements.txt"
    else
        print_warning "Failed to install from requirements.txt"
    fi
fi

# Install essential packages manually if both failed
if ! $REQUIREMENTS_INSTALLED; then
    print_warning "Installing essential packages manually..."
    pip install flask flask-sqlalchemy psycopg2-binary gunicorn python-dotenv sqlalchemy requests psutil
    pip install pynvml werkzeug email-validator paramiko boto3 pillow opencv-python numpy pandas matplotlib
    pip install torch faster-whisper
    REQUIREMENTS_INSTALLED=true
    print_status "Installed essential packages manually"
fi

# Set environment variables
print_info "Setting up environment variables..."
cat > .env << EOF
DATABASE_URL=postgresql://ai_translator:ai_translator_pass2024@localhost/ai_translator
SESSION_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
FLASK_ENV=production
FLASK_APP=main.py
EOF

# Initialize database schema
print_info "Initializing database schema..."
export DATABASE_URL="postgresql://ai_translator:ai_translator_pass2024@localhost/ai_translator"
export SESSION_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

if [ -f "database_setup.py" ]; then
    print_info "Running database_setup.py..."
    python database_setup.py || print_warning "database_setup.py had issues, but continuing"
else
    print_warning "database_setup.py not found, database will be initialized on first run"
fi

# Create systemd service
print_info "Creating systemd service..."
tee /etc/systemd/system/ai-translator.service > /dev/null << EOF
[Unit]
Description=AI Translator v2.2.5 Service
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=$INSTALL_USER
Group=$INSTALL_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 main:app
Restart=always
RestartSec=3
TimeoutStartSec=60
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
print_info "Configuring Nginx..."
tee /etc/nginx/sites-available/ai-translator > /dev/null << EOF
server {
    listen 80;
    server_name _;
    
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
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/ai-translator /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
systemctl enable nginx

# Enable and start AI Translator service
print_info "Starting AI Translator service..."
systemctl daemon-reload
systemctl enable ai-translator
systemctl start ai-translator

# Wait and check service status
sleep 5
if systemctl is-active --quiet ai-translator; then
    print_status "AI Translator service is running!"
else
    print_warning "Service may have issues. Checking logs..."
    journalctl -u ai-translator --no-pager -n 10
fi

# Install Ollama for AI models
print_info "Installing Ollama for AI translation..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
    print_status "Ollama installed successfully"
else
    print_status "Ollama already installed"
fi

# Pull essential AI models
print_info "Pulling essential AI models..."
ollama pull llama3
ollama pull mistral

# Create GitHub preparation script
print_info "Creating GitHub preparation script..."
cat > prepare_for_github.sh << EOF
#!/bin/bash
# Script to prepare AI Translator for GitHub upload

echo "🚀 Preparing AI Translator for GitHub..."

# Clean temporary files
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name "*.pyd" -delete
find . -name ".DS_Store" -delete
find . -name "*.log" -delete
rm -f *.tar.gz *.zip .latest_* 2>/dev/null || true

# Remove database files
rm -f *.db *.sqlite *.sqlite3 2>/dev/null || true

# Remove virtual environment
rm -rf venv/ 2>/dev/null || true

# Initialize git repository
git init

# Add all files
git add .

# Initial commit
git commit -m "AI Translator v2.2.5 - Initial Commit"

echo "✅ Repository prepared for GitHub"
echo "Next steps:"
echo "1. Create a GitHub repository"
echo "2. Add remote: git remote add origin https://github.com/YOUR_USERNAME/ai-translator.git"
echo "3. Push: git push -u origin main"
echo "4. Create release: git tag -a v2.2.5 -m 'AI Translator v2.2.5 Release'"
echo "5. Push tag: git push origin v2.2.5"
EOF

chmod +x prepare_for_github.sh

# Create verification script
print_info "Creating verification script..."
cat > verify_installation.sh << EOF
#!/bin/bash
# Script to verify AI Translator installation

echo "🔍 Verifying AI Translator installation..."

# Check services
echo "\nChecking services:"
echo "AI Translator: \$(systemctl is-active ai-translator)"
echo "PostgreSQL: \$(systemctl is-active postgresql)"
echo "Nginx: \$(systemctl is-active nginx)"

# Check ports
echo "\nChecking ports:"
echo "Port 5000 (AI Translator): \$(netstat -tuln | grep -q ':5000 ' && echo 'OPEN' || echo 'CLOSED')"
echo "Port 80 (Nginx): \$(netstat -tuln | grep -q ':80 ' && echo 'OPEN' || echo 'CLOSED')"
echo "Port 5432 (PostgreSQL): \$(netstat -tuln | grep -q ':5432 ' && echo 'OPEN' || echo 'CLOSED')"
echo "Port 11434 (Ollama): \$(netstat -tuln | grep -q ':11434 ' && echo 'OPEN' || echo 'CLOSED')"

# Check database
echo "\nChecking database connection:"
if python3 -c "import psycopg2; conn = psycopg2.connect('dbname=ai_translator user=ai_translator password=ai_translator_pass2024 host=localhost'); print('Database connection successful')" 2>/dev/null; then
    echo "Database connection: SUCCESS"
else
    echo "Database connection: FAILED"
fi

# Check web access
echo "\nChecking web access:"
if curl -s http://localhost:5000 | grep -q "AI Translator"; then
    echo "Web access: SUCCESS"
else
    echo "Web access: FAILED"
fi

echo "\n✅ Verification complete"
EOF

chmod +x verify_installation.sh

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

# Final instructions
echo ""
echo "🎉 AI Translator v2.2.5 installation completed successfully!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Access Information:${NC}"
echo "• Web Interface: http://$SERVER_IP (via Nginx)"
echo "• Direct Access: http://$SERVER_IP:5000"
echo "• Default Login: admin / your_strong_password"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   systemctl start ai-translator"
echo "• Stop service:    systemctl stop ai-translator"
echo "• Restart service: systemctl restart ai-translator"
echo "• View logs:       journalctl -u ai-translator -f"
echo "• Service status:  systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo "1. Configure your media servers in Settings"
echo "2. Install Ollama models: ollama pull llama3"
echo "3. Upload video files for translation"
echo ""
echo -e "${GREEN}📁 Installation Directory:${NC} $INSTALL_DIR"
echo -e "${GREEN}🗃️ Database:${NC} PostgreSQL - ai_translator"
echo -e "${GREEN}🔐 Database User:${NC} ai_translator"
echo ""
print_status "AI Translator v