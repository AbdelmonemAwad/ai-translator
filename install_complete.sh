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
    INSTALL_DIR="/root/ai-translator"
    print_warning "Running as root"
else
    INSTALL_USER="$USER"
    INSTALL_DIR="$HOME/ai-translator"
    print_info "Running as user: $INSTALL_USER"
fi

print_info "Installation directory: $INSTALL_DIR"

# Check if we already have the files locally
CURRENT_DIR=$(pwd)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_info "Current directory: $CURRENT_DIR"
print_info "Script directory: $SCRIPT_DIR"

# Method 1: Check current directory
if [ -f "$CURRENT_DIR/app.py" ] && [ -f "$CURRENT_DIR/main.py" ]; then
    INSTALL_DIR="$CURRENT_DIR"
    print_status "Found AI Translator files in current directory"
# Method 2: Check script directory  
elif [ -f "$SCRIPT_DIR/app.py" ] && [ -f "$SCRIPT_DIR/main.py" ]; then
    INSTALL_DIR="$SCRIPT_DIR"
    print_status "Found AI Translator files in script directory"
# Method 3: Look for extracted folder
else
    EXTRACTED_DIRS=$(find . -maxdepth 2 -name "app.py" -exec dirname {} \; 2>/dev/null | head -1)
    if [ -n "$EXTRACTED_DIRS" ]; then
        INSTALL_DIR="$(cd "$EXTRACTED_DIRS" && pwd)"
        print_status "Found extracted directory: $INSTALL_DIR"
    else
        print_error "Could not find AI Translator files."
        print_info "Please ensure you have extracted the AI Translator package first:"
        print_info "1. Download: ai-translator-complete-v2.2.5.tar.gz"
        print_info "2. Extract: tar -xzf ai-translator-complete-v2.2.5.tar.gz"
        print_info "3. Run: cd ai-translator && sudo ./install_complete.sh"
        exit 1
    fi
fi

cd "$INSTALL_DIR"
print_status "Working in: $INSTALL_DIR"

# Check for required files
REQUIRED_FILES=("app.py" "main.py" "models.py" "database_setup.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file $file not found in $INSTALL_DIR"
        print_info "Please ensure you have the complete AI Translator package extracted."
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

# Create database and user
print_info "Creating AI Translator database..."
sudo -u postgres createuser ai_translator 2>/dev/null || true
sudo -u postgres createdb ai_translator 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER ai_translator PASSWORD 'ai_translator_pass2024';" 2>/dev/null
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_translator TO ai_translator;" 2>/dev/null

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

# Create comprehensive requirements file
cat > requirements_complete.txt << EOF
# AI Translator v2.2.5 - Complete Requirements
flask>=2.3.0
flask-sqlalchemy>=3.0.0
psycopg2-binary>=2.9.0
gunicorn>=21.0.0
requests>=2.31.0
psutil>=5.9.0
numpy>=1.24.0
pillow>=10.0.0
torch>=2.0.0
faster-whisper>=0.9.0
pandas>=2.0.0
matplotlib>=3.7.0
opencv-python>=4.7.0
pynvml>=11.5.0
werkzeug>=2.3.0
jinja2>=3.1.0
itsdangerous>=2.1.0
click>=8.1.0
markupsafe>=2.1.0
SQLAlchemy>=2.0.0
WTForms>=3.0.0
flask-wtf>=1.1.0
flask-login>=0.6.0
flask-migrate>=4.0.0
flask-cors>=4.0.0
python-dotenv>=1.0.0
passlib>=1.7.0
email-validator>=2.0.0
pyjwt>=2.6.0
huggingface-hub>=0.16.0
transformers>=4.30.0
protobuf>=4.23.0
tqdm>=4.65.0
colorlog>=6.7.0
ffmpeg-python>=0.2.0
requests-toolbelt>=1.0.0
bs4>=0.0.1
lxml>=4.9.0
chardet>=5.1.0
PyYAML>=6.0.0
tenacity>=8.2.0
typing-extensions>=4.6.0
typing_inspect>=0.8.0
typing>=3.7.4
retrying>=1.3.0
retry>=0.9.0
backoff>=2.2.0
ratelimit>=2.2.0
ratelimiter>=1.2.0
throttling>=0.9.0
throttle>=1.0.0
throttler>=1.2.0
EOF

# Install from the comprehensive requirements file
pip install -r requirements_complete.txt

# Setup database tables
print_info "Setting up database tables..."
export DATABASE_URL="postgresql://ai_translator:ai_translator_pass2024@localhost/ai_translator"
python3 database_setup.py

# Configure Nginx
print_info "Configuring Nginx..."
cat > /etc/nginx/sites-available/ai-translator << EOF
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
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/ai-translator /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Create systemd service
print_info "Creating systemd service..."
cat > /etc/systemd/system/ai-translator.service << EOF
[Unit]
Description=AI Translator Service
After=network.target postgresql.service

[Service]
Type=simple
User=$INSTALL_USER
WorkingDirectory=$INSTALL_DIR
Environment=DATABASE_URL=postgresql://ai_translator:ai_translator_pass2024@localhost/ai_translator
Environment=FLASK_APP=main.py
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
Restart=always
RestartSec=3
TimeoutStartSec=120

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable ai-translator
systemctl start ai-translator

# Install Ollama for AI models
print_info "Installing Ollama for AI models..."
curl -fsSL https://ollama.com/install.sh | sh

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

print_status "AI Translator installation completed successfully!"
print_info "Service status: $(systemctl is-active ai-translator)"
print_info "Access your AI Translator at: http://$(hostname -I | awk '{print $1}')"
print_info "Default credentials: admin / your_strong_password"
print_info "Database: ai_translator (ai_translator:ai_translator_pass2024@localhost)"

# Show final status
print_info "Final system status:"
systemctl status ai-translator --no-pager -l

print_info "To verify your installation, run: ./verify_installation.sh"
print_info "To prepare for GitHub upload, run: ./prepare_for_github.sh"