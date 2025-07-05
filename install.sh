#!/bin/bash
# AI Translator v2.2.5 - Installation Script
# المترجم الآلي v2.2.5 - سكريبت التثبيت

set -e

echo "🚀 AI Translator v2.2.5 - Installation Starting..."
echo "   المترجم الآلي v2.2.5 - بدء التثبيت..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
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
    print_warning "Running as root. Consider creating a dedicated user for the application."
fi

# Update system packages
print_info "Updating system packages..."
sudo apt update

# Install system dependencies
print_info "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    ffmpeg \
    git \
    curl \
    build-essential \
    pkg-config \
    libpq-dev

# Clone repository
print_info "Cloning AI Translator repository..."
if [ -d "ai-translator" ]; then
    print_warning "Directory ai-translator already exists. Removing..."
    rm -rf ai-translator
fi

git clone https://github.com/AbdelmonemAwad/ai-translator.git
cd ai-translator

# Create virtual environment
print_info "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements_github.txt

# Setup PostgreSQL database
print_info "Setting up PostgreSQL database..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ai_translator;" 2>/dev/null || true
sudo -u postgres psql -c "DROP USER IF EXISTS ai_translator;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE ai_translator;"
sudo -u postgres psql -c "CREATE USER ai_translator WITH PASSWORD 'ai_translator_pass2024';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_translator TO ai_translator;"

# Set environment variables
print_info "Setting up environment variables..."
cat > .env << EOF
DATABASE_URL=postgresql://ai_translator:ai_translator_pass2024@localhost/ai_translator
SESSION_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
FLASK_ENV=production
EOF

# Initialize database
print_info "Initializing database schema..."
export DATABASE_URL="postgresql://ai_translator:ai_translator_pass2024@localhost/ai_translator"
export SESSION_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
python database_setup.py

# Create systemd service
print_info "Creating systemd service..."
INSTALL_DIR=$(pwd)
sudo tee /etc/systemd/system/ai-translator.service > /dev/null << EOF
[Unit]
Description=AI Translator v2.2.5 Service
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python main.py
Restart=always
RestartSec=3
TimeoutStartSec=30
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
print_info "Enabling and starting AI Translator service..."
sudo systemctl daemon-reload
sudo systemctl enable ai-translator
sudo systemctl start ai-translator

# Check service status
sleep 3
if sudo systemctl is-active --quiet ai-translator; then
    print_status "AI Translator service is running!"
else
    print_error "Service failed to start. Check logs with: sudo journalctl -u ai-translator -f"
    exit 1
fi

# Install Ollama (optional)
print_info "Installing Ollama for AI translation..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
    print_status "Ollama installed successfully"
else
    print_status "Ollama already installed"
fi

# Final instructions
echo ""
echo "🎉 Installation completed successfully!"
echo "   التثبيت اكتمل بنجاح!"
echo ""
echo -e "${GREEN}📋 Next Steps:${NC}"
echo "1. Access the web interface: http://localhost:5000"
echo "2. Default login: admin / your_strong_password"
echo "3. Configure your media servers in Settings"
echo "4. Install Ollama models: ollama pull llama3"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "• Start service:   sudo systemctl start ai-translator"
echo "• Stop service:    sudo systemctl stop ai-translator"
echo "• View logs:       sudo journalctl -u ai-translator -f"
echo "• Service status:  sudo systemctl status ai-translator"
echo ""
echo -e "${YELLOW}📖 Documentation:${NC}"
echo "• GitHub: https://github.com/AbdelmonemAwad/ai-translator"
echo "• Issues: https://github.com/AbdelmonemAwad/ai-translator/issues"
echo ""
print_status "AI Translator v2.2.5 is now ready to use!"