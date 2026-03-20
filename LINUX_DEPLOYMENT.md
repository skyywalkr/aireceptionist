# Linux Deployment Checklist

Complete step-by-step guide for deploying Nexus AI Receptionist on a Linux server.

## ✅ Pre-Deployment

- [ ] Linux server running Ubuntu 20.04+ or Debian 11+
- [ ] SSH access to server as user with `sudo` privileges
- [ ] Sufficient disk space (~2GB for venv + data)
- [ ] Internet connectivity for package/dependency installation
- [ ] (Optional) PostgreSQL or other database credentials if using external DB

## 🚀 Quick Deployment (Automated)

### Option 1: One-Command Deploy (Recommended)

On your Linux server:

```bash
# Download and run deployment script
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/skyywalkr/aireceptionist/main/deploy-linux.sh)"
```

**OR** if you have the repo cloned:

```bash
cd /opt/nexus
sudo bash deploy-linux.sh
```

The script will:
- ✅ Install all system dependencies (ffmpeg, Python, PostgreSQL)
- ✅ Create application user (`nexus`)
- ✅ Clone/pull latest code from GitHub
- ✅ Create configuration directories
- ✅ Set up Python virtual environment
- ✅ Install all Python dependencies
- ✅ Initialize database
- ✅ Configure systemd service
- ✅ Print next steps

**Expected time: 2-5 minutes**

---

## 📋 Manual Deployment (If Preferred)

### Step 1: Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
    python3 python3-venv python3-pip \
    ffmpeg \
    postgresql postgresql-contrib \
    git curl

# Verify ffmpeg installed
ffmpeg -version
```

### Step 2: Create Application User & Directories

```bash
# Create nexus user
sudo useradd -r -s /bin/bash -d /opt/nexus -m nexus

# Create configuration and data directories
sudo mkdir -p /etc/nexus /var/lib/nexus /var/log/nexus
sudo chown -R nexus:nexus /var/lib/nexus /var/log/nexus
sudo chmod -R 755 /var/lib/nexus /var/log/nexus
```

### Step 3: Clone Repository

```bash
# Clone to /opt/nexus
sudo git clone https://github.com/skyywalkr/aireceptionist.git /opt/nexus
sudo chown -R nexus:nexus /opt/nexus

# If already cloned, just pull latest
cd /opt/nexus
sudo git config --global --add safe.directory /opt/nexus
sudo git pull origin main
```

### Step 4: Create Configuration File

```bash
# Create .env file with secure permissions
sudo tee /etc/nexus/.env > /dev/null << 'EOF'
# Asterisk & ARI Configuration (OPTIONAL)
ARI_URL=http://127.0.0.1:8088
ARI_USER=asterisk
ARI_PASS=secret
ARI_APP_NAME=ai_receptionist
PJSIP_TRUNK_NAME=trunk-provider
ASTERISK_SOUNDS_DIR=/var/lib/asterisk/sounds/custom

# OpenAI Configuration (OPTIONAL - graceful degradation without API key)
ENABLE_AI=false
# OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini

# ElevenLabs Configuration (OPTIONAL)
# ELEVENLABS_API_KEY=your-actual-key-here

# Flask Configuration
SECRET_KEY=$(python3 -c 'import uuid; print(str(uuid.uuid4()))')
FLASK_ENV=production

# Database
DATABASE_URL=sqlite:////var/lib/nexus/receptionist.db

# Pricing
PRICING_MARGIN=1.3
MINIMUM_CHARGE_PER_CALL=0.15
EOF

# Secure permissions
sudo chmod 600 /etc/nexus/.env
sudo chown nexus:nexus /etc/nexus/.env
```

### Step 5: Set Up Python Virtual Environment

```bash
cd /opt/nexus

# Create venv
sudo -u nexus python3 -m venv venv
sudo -u nexus ./venv/bin/pip install --upgrade pip

# Install dependencies
sudo -u nexus ./venv/bin/pip install -r requirements.txt

# Verify installation
./venv/bin/pip list | grep -E "Flask|openai|elevenlabs"
```

### Step 6: Initialize Database

```bash
cd /opt/nexus
source venv/bin/activate
export FLASK_ENV=production
export $(grep -v '^#' /etc/nexus/.env | xargs)

# Initialize database
python3 << PYTHON_SCRIPT
from models import db
from app import app

with app.app_context():
    db.create_all()
    print("✅ Database initialized")
PYTHON_SCRIPT

deactivate
```

### Step 7: Install Systemd Service

```bash
# Copy service file
sudo cp /opt/nexus/nexus.service /etc/systemd/system/

# Update service file with correct paths (if needed)
sudo sed -i 's|/opt/nexus/venv/bin/python|/opt/nexus/venv/bin/python3|g' /etc/systemd/system/nexus.service

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl enable nexus.service
```

---

## 🔑 Configure API Keys (Optional)

Edit the configuration file to add your API keys:

```bash
sudo nano /etc/nexus/.env
```

**OpenAI Integration (Optional)**
- Set `ENABLE_AI=true`
- Add your OpenAI API key: `OPENAI_API_KEY=sk-...`
- Without this: static greetings will be used

**ElevenLabs TTS (Optional)**
- Add your ElevenLabs API key: `ELEVENLABS_API_KEY=...`
- Without this: gTTS will be used for text-to-speech

**Save and exit** (`Ctrl+X`, then `Y`, then Enter)

---

## 🚀 Start the Service

```bash
# Start the service
sudo systemctl start nexus.service

# Verify it's running
sudo systemctl status nexus.service

# View real-time logs
sudo journalctl -xeu nexus.service -f
```

**Expected output**: Service should be `active (running)`

---

## 🧪 Verify Deployment

```bash
# Check if service is running
sudo systemctl is-active nexus.service

# Check if listening on port 5000
sudo netstat -tlnp | grep 5000

# Test API endpoint
curl http://localhost:5000/

# Full diagnostic
sudo journalctl -xeu nexus.service --no-pager | tail -50
```

---

## 📊 Accessing the Application

Once running, access the web UI:

```
http://<your-server-ip>:5000
```

Default login credentials are configured in the database.

---

## 🔧 Common Tasks

### Restart Service
```bash
sudo systemctl restart nexus.service
```

### Stop Service
```bash
sudo systemctl stop nexus.service
```

### View Logs (Last 100 lines)
```bash
sudo journalctl -u nexus.service -n 100
```

### View Logs (Real-time)
```bash
sudo journalctl -u nexus.service -f
```

### Regenerate Database
```bash
sudo rm /var/lib/nexus/receptionist.db
sudo -u nexus bash -c 'cd /opt/nexus && source venv/bin/activate && python3 -c "from models import db; from app import app; app.app_context().push(); db.create_all()"'
```

### Update to Latest Code
```bash
cd /opt/nexus
sudo git pull origin main
sudo systemctl restart nexus.service
```

---

## 🐛 Troubleshooting

### Service fails to start with "Failed with result 'resources'"

**Check:**
1. Directories exist with correct permissions:
   ```bash
   ls -la /etc/nexus/.env
   ls -la /var/lib/nexus/
   ls -la /var/log/nexus/
   ```

2. Configuration file exists:
   ```bash
   cat /etc/nexus/.env | head -5
   ```

3. Python venv is valid:
   ```bash
   /opt/nexus/venv/bin/python3 --version
   ```

### API keys not working

1. Verify they're in the config file:
   ```bash
   grep OPENAI_API_KEY /etc/nexus/.env
   ```

2. Check environment is being loaded:
   ```bash
   sudo journalctl -u nexus.service -n 20 | grep -i "api\|openai\|eleven"
   ```

3. Restart service after updating:
   ```bash
   sudo systemctl restart nexus.service
   ```

### Database connection error

1. Check database file exists and has correct permissions:
   ```bash
   ls -la /var/lib/nexus/receptionist.db
   sudo chown nexus:nexus /var/lib/nexus/receptionist.db
   sudo chmod 644 /var/lib/nexus/receptionist.db
   ```

2. Reinitialize database:
   ```bash
   sudo rm /var/lib/nexus/receptionist.db
   cd /opt/nexus && source venv/bin/activate && python3 -c "from models import db; from app import app; app.app_context().push(); db.create_all()"
   ```

### ffmpeg not found

```bash
sudo apt-get install -y ffmpeg
which ffmpeg
```

---

## ✨ You're Done!

Your Nexus AI Receptionist is now running on your Linux server.

**Next Steps:**
- [ ] Access the web UI at `http://<your-ip>:5000`
- [ ] Configure API keys in `/etc/nexus/.env`
- [ ] Test call functionality
- [ ] Set up reverse proxy (NGINX recommended for production)
- [ ] Enable HTTPS with Let's Encrypt
- [ ] Monitor logs regularly

For more information, see:
- [README.md](README.md) - Project overview
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [PRICING.md](PRICING.md) - Pricing logic documentation
