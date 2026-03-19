#!/bin/bash
#
# Nexus AI Receptionist - Automated Deployment Script
# Usage: sudo bash deploy.sh
#
# This script automates the deployment of Nexus on a fresh Ubuntu 20.04+ server
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Nexus AI Receptionist - Deployment${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Configuration
NEXUS_USER="nexus"
NEXUS_GROUP="nexus"
NEXUS_HOME="/opt/nexus"
NEXUS_DATA="/var/lib/nexus"
NEXUS_LOGS="/var/log/nexus"
DB_NAME="nexus_db"
DB_USER="nexus"
DB_PASS="${DB_PASS:-$(openssl rand -base64 32)}"
SECRET_KEY="$(openssl rand -hex 32)"
DOMAIN="${DOMAIN:-yourdomain.com}"

echo -e "${YELLOW}Configuration:${NC}"
echo "Nexus Home: $NEXUS_HOME"
echo "Database User: $DB_USER"
echo "Database Password: (auto-generated)"
echo "Domain: $DOMAIN"
echo ""

# Step 1: Update system
echo -e "${BLUE}[1/10]${NC} Updating system packages..."
apt update && apt upgrade -y

# Step 2: Install dependencies
echo -e "${BLUE}[2/10]${NC} Installing system dependencies..."
apt install -y \
    python3.11 python3.11-venv python3.11-dev \
    build-essential \
    postgresql postgresql-contrib \
    nginx \
    ffmpeg \
    curl wget git \
    certbot python3-certbot-nginx \
    ufw

# Step 3: Create system user
echo -e "${BLUE}[3/10]${NC} Creating nexus system user..."
if ! id "$NEXUS_USER" &>/dev/null; then
    useradd -r -m -s /usr/sbin/nologin -d "$NEXUS_DATA" "$NEXUS_USER"
    echo -e "${GREEN}User created: $NEXUS_USER${NC}"
else
    echo -e "${YELLOW}User already exists: $NEXUS_USER${NC}"
fi

# Step 4: Create directories
echo -e "${BLUE}[4/10]${NC} Creating application directories..."
mkdir -p "$NEXUS_HOME" "$NEXUS_DATA" "$NEXUS_LOGS" /etc/nexus
chown -R "$NEXUS_USER:$NEXUS_GROUP" "$NEXUS_DATA" "$NEXUS_LOGS"
chmod 700 "$NEXUS_DATA" "$NEXUS_LOGS" /etc/nexus

# Step 5: Setup Python virtual environment
echo -e "${BLUE}[5/10]${NC} Setting up Python virtual environment..."
if [ -d "$NEXUS_HOME" ] && [ -f "$NEXUS_HOME/requirements.txt" ]; then
    cd "$NEXUS_HOME"
    sudo -u "$NEXUS_USER" python3.11 -m venv venv
    sudo -u "$NEXUS_USER" bash -c "source venv/bin/activate && pip install --upgrade pip setuptools wheel"
    sudo -u "$NEXUS_USER" bash -c "source venv/bin/activate && pip install -r requirements.txt"
    echo -e "${GREEN}Virtual environment created${NC}"
else
    echo -e "${YELLOW}Skipping venv setup - clone repo first to $NEXUS_HOME${NC}"
fi

# Step 6: Setup PostgreSQL
echo -e "${BLUE}[6/10]${NC} Setting up PostgreSQL database..."
sudo -u postgres psql << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME ENCODING 'UTF8';
CREATE USER IF NOT EXISTS $DB_USER WITH PASSWORD '$DB_PASS';
ALTER USER $DB_USER CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOF
echo -e "${GREEN}Database created${NC}"

# Step 7: Create environment configuration
echo -e "${BLUE}[7/10]${NC} Creating environment configuration..."
cat > /etc/nexus/.env << EOF
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$SECRET_KEY
DEBUG=False

# Database
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME

# Asterisk ARI
ARI_URL=http://127.0.0.1:8088
ARI_USER=asterisk
ARI_PASS=change_me_in_production
ARI_APP_NAME=ai_receptionist
PJSIP_TRUNK_NAME=trunk

# Audio
ASTERISK_SOUNDS_DIR=/var/lib/asterisk/sounds/custom
ENABLE_AI=true

# API Keys
OPENAI_API_KEY=sk-your-key-here
ELEVENLABS_API_KEY=your-key-here

# Pricing
PRICING_MARGIN=1.3
MINIMUM_CHARGE_PER_CALL=0.15
EOF
chmod 600 /etc/nexus/.env
chown "$NEXUS_USER:$NEXUS_GROUP" /etc/nexus/.env
echo -e "${GREEN}Environment configuration created at /etc/nexus/.env${NC}"

# Step 8: Setup systemd service
echo -e "${BLUE}[8/10]${NC} Installing systemd service..."
if [ -f "$NEXUS_HOME/nexus.service" ]; then
    cp "$NEXUS_HOME/nexus.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable nexus
    echo -e "${GREEN}Systemd service installed${NC}"
else
    echo -e "${YELLOW}nexus.service not found in $NEXUS_HOME${NC}"
fi

# Step 9: Setup NGINX reverse proxy
echo -e "${BLUE}[9/10]${NC} Configuring NGINX reverse proxy..."
if [ -f "$NEXUS_HOME/nexus.nginx.conf" ]; then
    cp "$NEXUS_HOME/nexus.nginx.conf" /etc/nginx/sites-available/nexus
    ln -sf /etc/nginx/sites-available/nexus /etc/nginx/sites-enabled/nexus
    rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
    nginx -t && systemctl reload nginx
    echo -e "${GREEN}NGINX configured${NC}"
else
    echo -e "${YELLOW}nexus.nginx.conf not found in $NEXUS_HOME${NC}"
fi

# Step 10: Setup firewall
echo -e "${BLUE}[10/10]${NC} Configuring firewall..."
ufw allow 22/tcp comment "SSH"
ufw allow 80/tcp comment "HTTP"
ufw allow 443/tcp comment "HTTPS"
ufw allow from 127.0.0.1 to 127.0.0.1 port 8088 comment "ARI - Localhost"
ufw allow from 127.0.0.1 to 127.0.0.1 port 5432 comment "PostgreSQL - Localhost"
ufw default deny incoming
ufw default allow outgoing
echo "y" | ufw enable 2>/dev/null || true
echo -e "${GREEN}Firewall configured${NC}"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update /etc/nexus/.env with your actual API keys:"
echo "   - OPENAI_API_KEY"
echo "   - ELEVENLABS_API_KEY"
echo "   - ARI_PASS (Asterisk ARI password)"
echo ""
echo "2. Configure SSL certificate (Let's Encrypt):"
echo "   sudo certbot certonly --nginx -d $DOMAIN"
echo ""
echo "3. Update NGINX config with your domain:"
echo "   sudo nano /etc/nginx/sites-available/nexus"
echo "   # Replace 'yourdomain.com' with '$DOMAIN'"
echo "   sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "4. Start the Nexus service:"
echo "   sudo systemctl start nexus"
echo ""
echo "5. Check service status:"
echo "   sudo systemctl status nexus"
echo "   sudo journalctl -u nexus -f"
echo ""
echo -e "${YELLOW}Database Credentials (save to secure location):${NC}"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Password: $DB_PASS"
echo ""
echo -e "${YELLOW}Environment File:${NC}"
echo "/etc/nexus/.env"
echo ""
echo -e "${YELLOW}Application Directory:${NC}"
echo "$NEXUS_HOME"
echo ""
