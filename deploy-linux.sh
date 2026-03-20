#!/bin/bash

################################################################################
# Nexus AI Receptionist - Linux Deployment Script
# Automates complete setup on Ubuntu/Debian servers
# Run as: sudo bash deploy-linux.sh
################################################################################

set -e  # Exit on any error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_USER="nexus"
APP_GROUP="nexus"
APP_DIR="/opt/nexus"
CONFIG_DIR="/etc/nexus"
VAR_DIR="/var/lib/nexus"
LOG_DIR="/var/log/nexus"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Nexus AI Receptionist - Linux Deployment                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root (use: sudo bash deploy-linux.sh)${NC}"
   exit 1
fi

# ============================================================================
# STEP 1: Install System Dependencies
# ============================================================================
echo -e "\n${YELLOW}[1/7]${NC} Installing system dependencies..."

apt-get update > /dev/null 2>&1 || true
apt-get install -y \
    python3 python3-venv python3-pip \
    ffmpeg \
    postgresql postgresql-contrib \
    git \
    curl \
    > /dev/null 2>&1

if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}❌ ffmpeg installation failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ System dependencies installed${NC}"

# ============================================================================
# STEP 2: Create Application User & Directories
# ============================================================================
echo -e "\n${YELLOW}[2/7]${NC} Creating application user and directories..."

# Create nexus user if it doesn't exist
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d "$APP_DIR" -m "$APP_USER"
    echo -e "${GREEN}✅ Created user: $APP_USER${NC}"
else
    echo -e "${GREEN}✅ User $APP_USER already exists${NC}"
fi

# Create required directories
mkdir -p "$CONFIG_DIR" "$VAR_DIR" "$LOG_DIR"
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR" "$VAR_DIR" "$LOG_DIR"
chmod -R 755 "$VAR_DIR" "$LOG_DIR"
chmod 755 "$CONFIG_DIR"

echo -e "${GREEN}✅ Directories created and permissions set${NC}"

# ============================================================================
# STEP 3: Pull Latest Code from Git
# ============================================================================
echo -e "\n${YELLOW}[3/7]${NC} Pulling latest code from GitHub..."

if [ ! -d "$APP_DIR/.git" ]; then
    echo -e "${YELLOW}   Cloning repository...${NC}"
    cd /tmp
    git clone https://github.com/skyywalkr/aireceptionist.git "$APP_DIR" || {
        echo -e "${RED}❌ Failed to clone repository${NC}"
        exit 1
    }
    chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"
else
    echo -e "${YELLOW}   Updating existing repository...${NC}"
    cd "$APP_DIR"
    sudo -u "$APP_USER" git config --global --add safe.directory "$APP_DIR"
    sudo -u "$APP_USER" git pull origin main
    echo -e "${GREEN}✅ Repository updated${NC}"
fi

echo -e "${GREEN}✅ Code pulled successfully${NC}"

# ============================================================================
# STEP 4: Create Configuration File
# ============================================================================
echo -e "\n${YELLOW}[4/7]${NC} Creating configuration file..."

if [ -f "$CONFIG_DIR/.env" ]; then
    echo -e "${YELLOW}   ⚠️  $CONFIG_DIR/.env already exists. Skipping...${NC}"
else
    # Generate random SECRET_KEY
    SECRET_KEY=$(python3 -c 'import uuid; print(str(uuid.uuid4()))')
    
    cat > "$CONFIG_DIR/.env" << EOF
# Asterisk & ARI Configuration (OPTIONAL - Asterisk integration disabled without Asterisk)
ARI_URL=http://127.0.0.1:8088
ARI_USER=asterisk
ARI_PASS=secret
ARI_APP_NAME=ai_receptionist
PJSIP_TRUNK_NAME=trunk-provider
ASTERISK_SOUNDS_DIR=/var/lib/asterisk/sounds/custom

# OpenAI Configuration (OPTIONAL - graceful degradation without API key)
# Set ENABLE_AI=true and provide OPENAI_API_KEY to enable AI features
ENABLE_AI=false
# OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini

# ElevenLabs Configuration (OPTIONAL - falls back to gTTS without API key)
# ELEVENLABS_API_KEY=your-actual-key-here

# Flask Configuration
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
DATABASE_URL=sqlite:////var/lib/nexus/receptionist.db

# Pricing
PRICING_MARGIN=1.3
MINIMUM_CHARGE_PER_CALL=0.15
EOF

    chmod 600 "$CONFIG_DIR/.env"
    chown "$APP_USER:$APP_GROUP" "$CONFIG_DIR/.env"
    echo -e "${GREEN}✅ Configuration file created at $CONFIG_DIR/.env${NC}"
fi

# ============================================================================
# STEP 5: Set Up Python Virtual Environment
# ============================================================================
echo -e "\n${YELLOW}[5/7]${NC} Setting up Python virtual environment..."

if [ ! -d "$APP_DIR/venv" ]; then
    echo -e "${YELLOW}   Creating venv...${NC}"
    cd "$APP_DIR"
    python3 -m venv venv
    
    echo -e "${YELLOW}   Installing dependencies...${NC}"
    source "$APP_DIR/venv/bin/activate"
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    pip install -r "$APP_DIR/requirements.txt" > /dev/null 2>&1 || {
        echo -e "${RED}❌ Failed to install Python dependencies${NC}"
        exit 1
    }
    deactivate
    
    chown -R "$APP_USER:$APP_GROUP" "$APP_DIR/venv"
    echo -e "${GREEN}✅ Virtual environment created and dependencies installed${NC}"
else
    echo -e "${YELLOW}   venv already exists. Updating dependencies...${NC}"
    source "$APP_DIR/venv/bin/activate"
    pip install -r "$APP_DIR/requirements.txt" > /dev/null 2>&1
    deactivate
    echo -e "${GREEN}✅ Dependencies updated${NC}"
fi

# ============================================================================
# STEP 6: Initialize Database
# ============================================================================
echo -e "\n${YELLOW}[6/7]${NC} Initializing database..."

cd "$APP_DIR"
source venv/bin/activate

# Export env vars for Flask app
export FLASK_ENV=production
export $(cat "$CONFIG_DIR/.env" | grep -v '^#' | grep -v '^$' | xargs)

# Initialize DB
python3 << PYTHON_SCRIPT
import sys
try:
    from models import db
    from app import app
    
    with app.app_context():
        db.create_all()
        print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️  Database initialization warning: {e}")
    print("   This may be normal if you're using an external database.")
    print("   The service will attempt to initialize on first run.")
PYTHON_SCRIPT

deactivate
echo -e "${GREEN}✅ Database initialization complete${NC}"

# ============================================================================
# STEP 7: Set Up Systemd Service
# ============================================================================
echo -e "\n${YELLOW}[7/7]${NC} Setting up systemd service..."

# Copy service file
cp "$APP_DIR/nexus.service" /etc/systemd/system/nexus.service

# Update paths in service file to match our setup
sed -i "s|^User=.*|User=$APP_USER|" /etc/systemd/system/nexus.service
sed -i "s|^Group=.*|Group=$APP_GROUP|" /etc/systemd/system/nexus.service
sed -i "s|^WorkingDirectory=.*|WorkingDirectory=$APP_DIR|" /etc/systemd/system/nexus.service
sed -i "s|^EnvironmentFile=.*|EnvironmentFile=-$CONFIG_DIR/.env|" /etc/systemd/system/nexus.service
sed -i "s|^ExecStart=.*|ExecStart=$APP_DIR/venv/bin/python $APP_DIR/app.py|" /etc/systemd/system/nexus.service
sed -i "s|^ReadWritePaths=.*|ReadWritePaths=$VAR_DIR $LOG_DIR|" /etc/systemd/system/nexus.service

# Reload systemd
systemctl daemon-reload
systemctl enable nexus.service

echo -e "${GREEN}✅ Systemd service configured${NC}"

# ============================================================================
# VERIFICATION
# ============================================================================
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Deployment Complete!                                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${YELLOW}📋 Next Steps:${NC}"
echo -e "   1. Edit configuration file with your API keys:"
echo -e "      ${GREEN}nano $CONFIG_DIR/.env${NC}"
echo -e ""
echo -e "   2. Start the service:"
echo -e "      ${GREEN}systemctl start nexus.service${NC}"
echo -e ""
echo -e "   3. Check status:"
echo -e "      ${GREEN}systemctl status nexus.service${NC}"
echo -e ""
echo -e "   4. View logs:"
echo -e "      ${GREEN}journalctl -xeu nexus.service --no-pager${NC}"
echo -e ""
echo -e "   5. Access web UI:"
echo -e "      ${GREEN}http://localhost:5000${NC}"

echo -e "\n${YELLOW}📝 Important Information:${NC}"
echo -e "   Application Directory: ${GREEN}$APP_DIR${NC}"
echo -e "   Configuration File:    ${GREEN}$CONFIG_DIR/.env${NC}"
echo -e "   Database Location:     ${GREEN}$VAR_DIR/receptionist.db${NC}"
echo -e "   Logs Location:         ${GREEN}$LOG_DIR${NC}"
echo -e "   System User:           ${GREEN}$APP_USER${NC}"

echo -e "\n${YELLOW}🔑 API Keys (Optional):${NC}"
echo -e "   • OPENAI_API_KEY:      Not required - graceful degradation without it"
echo -e "   • ELEVENLABS_API_KEY:  Not required - falls back to gTTS"

echo -e "\n${GREEN}✨ Deployment script complete!${NC}\n"
