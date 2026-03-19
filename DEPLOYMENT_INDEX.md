# Nexus AI Receptionist - Production Files Index

## 📋 Quick Navigation

### 🚀 Getting Started
- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Overview of all deployment files and quick links
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete step-by-step deployment guide (10 steps)
- **[deploy.sh](deploy.sh)** - Automated deployment script (execute as root)

### ✅ Checklists & Planning
- **[PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)** - Comprehensive pre-launch checklist (150+ items)
- **[PRODUCTION_QUICKREF.md](PRODUCTION_QUICKREF.md)** - Daily operations and quick reference commands
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture diagrams and data flow

### 🔧 Configuration Files
- **[nexus.service](nexus.service)** - Systemd unit file (Linux - runs Flask app as service)
- **[com.nexus.ai-receptionist.plist](com.nexus.ai-receptionist.plist)** - Launchd plist file (macOS - runs Flask app as service)
- **[nexus.nginx.conf](nexus.nginx.conf)** - NGINX reverse proxy configuration
- **[asterisk-ari.conf](asterisk-ari.conf)** - Asterisk ARI, PJSIP, and dialplan config
- **[firewall.sh](firewall.sh)** - UFW firewall configuration script (Linux)

### 📖 Documentation
- **[SECURITY.md](SECURITY.md)** - Security audit results and hardening measures
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - In-depth deployment procedures
- **[PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)** - Pre-deployment verification
- **[PRODUCTION_QUICKREF.md](PRODUCTION_QUICKREF.md)** - Fast reference for operations

---

## 📁 File Organization

### For Deployment

**Linux (Ubuntu)**:
```
Repository Root (git clone here)
├── nexus.service          → Copy to /etc/systemd/system/
├── nexus.nginx.conf       → Copy to /etc/nginx/sites-available/
├── asterisk-ari.conf      → Reference for /etc/asterisk/*.conf
├── firewall.sh            → Run as: sudo bash firewall.sh
└── deploy.sh              → Run as: sudo bash deploy.sh
```

**macOS**:
```
Repository Root (git clone here)
├── com.nexus.ai-receptionist.plist → Copy to /Library/LaunchDaemons/
├── nexus.nginx.conf       → Copy to /usr/local/etc/nginx/sites-available/ (Homebrew)
├── asterisk-ari.conf      → Reference for Asterisk config
└── Manual setup required (see DEPLOYMENT.md)
```

### For Documentation

```
Repository Root
├── DEPLOYMENT.md          → Step-by-step guide
├── DEPLOYMENT_SUMMARY.md  → Overview
├── PRODUCTION_CHECKLIST.md → Pre-launch verification
├── PRODUCTION_QUICKREF.md  → Daily operations
├── ARCHITECTURE.md        → System diagrams
└── SECURITY.md            → Security details
```

### Production Server After Deployment

**Linux (Ubuntu)**:
```
/etc/
├── nexus/
│   └── .env               ← Secrets (600 permissions)
├── nginx/
│   ├── sites-available/
│   │   └── nexus
│   └── sites-enabled/
│       └── nexus → ../sites-available/nexus
├── systemd/
│   └── system/
│       └── nexus.service
├── asterisk/
│   ├── ari.conf
│   ├── pjsip.conf
│   └── extensions.conf
└── logrotate.d/
    └── nexus

/opt/
└── nexus/
    ├── app.py
    ├── models.py
    ├── pricing.py
    ├── ai_receptionist.py
    ├── elevenlabs_tts.py
    ├── templates/
    ├── static/
    ├── venv/              ← Python virtual environment
    └── requirements.txt

/var/
├── lib/nexus/
│   └── receptionist.db    ← or PostgreSQL (recommended)
├── log/nexus/
│   ├── app.log
│   └── error.log
└── backups/
    └── nexus_db_*.sql.gz

/var/lib/asterisk/sounds/
└── custom/
    ├── greeting_*.wav     ← AI-generated greetings
    └── reply_*.wav        ← AI response audio
```

**macOS**:
```
/Library/
└── LaunchDaemons/
    └── com.nexus.ai-receptionist.plist

/usr/local/etc/
└── nginx/
    ├── sites-available/
    │   └── nexus
    └── sites-enabled/
        └── nexus → ../sites-available/nexus

/opt/
└── nexus/
    ├── app.py
    ├── models.py
    ├── pricing.py
    ├── ai_receptionist.py
    ├── elevenlabs_tts.py
    ├── templates/
    ├── static/
    ├── venv/              ← Python virtual environment
    └── requirements.txt

/var/
├── lib/nexus/
│   └── receptionist.db    ← or PostgreSQL (recommended)
├── log/nexus/
│   ├── app.log
│   └── error.log
└── backups/
    └── nexus_db_*.sql.gz

/usr/local/var/lib/asterisk/sounds/
└── custom/
    ├── greeting_*.wav     ← AI-generated greetings
    └── reply_*.wav        ← AI response audio
```

---

## 🎯 Deployment Path

### Option A: Automated - Linux (Recommended for First-Time)
```bash
# 1. SSH to fresh Ubuntu 20.04+ server
ssh ubuntu@your-server

# 2. Clone repository
cd /opt
git clone https://github.com/yourusername/nexus-ai-receptionist.git nexus
cd nexus

# 3. Run automated deployment
sudo bash deploy.sh

# 4. Configure secrets
sudo nano /etc/nexus/.env
# Edit: OPENAI_API_KEY, ELEVENLABS_API_KEY, ARI_PASS, DATABASE_URL

# 5. Setup SSL
sudo certbot certonly --nginx -d yourdomain.com

# 6. Start service
sudo systemctl start nexus

# 7. Verify
sudo systemctl status nexus
```

**Time: 10-15 minutes**

### Option B: Manual - Linux
```bash
# Follow each step in DEPLOYMENT.md:
1. Create system user
2. Clone application
3. Setup Python venv
4. Configure PostgreSQL
5. Create .env file
6. Configure NGINX
7. Setup SSL (Let's Encrypt)
8. Configure firewall
9. Install systemd service
10. Verify all components
```

### Option C: Manual - macOS
```bash
# 1. Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install dependencies
brew install python@3.11 postgresql nginx asterisk

# 3. Clone repository
cd /opt
sudo git clone https://github.com/yourusername/nexus-ai-receptionist.git nexus
sudo chown -R $(whoami) nexus
cd nexus

# 4. Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 6. Setup launchd service
sudo cp com.nexus.ai-receptionist.plist /Library/LaunchDaemons/
sudo launchctl load -w /Library/LaunchDaemons/com.nexus.ai-receptionist.plist

# 7. Setup NGINX
sudo cp nexus.nginx.conf /usr/local/etc/nginx/sites-available/nexus
sudo ln -s /usr/local/etc/nginx/sites-available/nexus /usr/local/etc/nginx/sites-enabled/nexus
sudo nginx -t
sudo brew services restart nginx

# 8. Verify
sudo launchctl list | grep nexus
tail -f /var/log/nexus/nexus.log
```

**Time: 20-30 minutes**

**Time: 30-45 minutes**

### Option C: Production With Monitoring
```bash
# Do Option A or B, then:
1. Setup log aggregation (ELK, Splunk)
2. Setup application monitoring (DataDog, New Relic)
3. Setup uptime monitoring (UptimeRobot)
4. Create status page
5. Setup PagerDuty alerts
6. Configure automated backups to S3
7. Setup database replicas (optional)
```

**Time: 1-2 hours additional**

---

## 🔐 Security Checklist

Before launching, verify:

- [ ] `SECRET_KEY` is random 32-character hex string
- [ ] `OPENAI_API_KEY` is set (sk-...)
- [ ] `ELEVENLABS_API_KEY` is set (if using premium TTS)
- [ ] `ARI_PASS` is strong password (not default)
- [ ] Database credentials are strong/random
- [ ] SSL certificate is valid (Let's Encrypt)
- [ ] Firewall rules are in place (UFW enabled)
- [ ] NGINX is running and responding
- [ ] Flask service is running and healthy
- [ ] PostgreSQL is running and accessible
- [ ] Asterisk ARI is accessible from Flask
- [ ] No API keys in version control (.gitignore)
- [ ] /etc/nexus/.env has 600 permissions
- [ ] nexus user owns application directories
- [ ] Database backups are configured
- [ ] Monitoring and alerting are active

---

## 📊 Component Checklist

### Application (Flask)
- **File**: `/opt/nexus/app.py`
- **Service**: systemd unit `nexus.service`
- **User**: `nexus` (non-root)
- **Status**: `sudo systemctl status nexus`
- **Logs**: `sudo journalctl -u nexus -f`

### Reverse Proxy (NGINX)
- **File**: `/etc/nginx/sites-available/nexus`
- **Service**: `nginx`
- **Listen**: Port 80 (HTTP) and 443 (HTTPS)
- **Status**: `sudo systemctl status nginx`
- **Logs**: `/var/log/nginx/nexus_access.log`, error.log

### Database (PostgreSQL)
- **Service**: `postgresql`
- **Database**: `nexus_db`
- **User**: `nexus` (limited privileges)
- **Port**: 5432 (localhost only)
- **Status**: `sudo systemctl status postgresql`
- **Backups**: `/var/backups/nexus_db_*.sql.gz` (daily)

### Voice Server (Asterisk)
- **Service**: `asterisk`
- **ARI Port**: 8088 (localhost only)
- **SIP Trunk**: Configured in pjsip.conf
- **Dialplan**: from_trunk, ai_receptionist_app
- **Status**: `sudo asterisk -rvvv`
- **Sounds**: `/var/lib/asterisk/sounds/custom/`

### Firewall (UFW)
- **Service**: `ufw`
- **Status**: `sudo ufw status verbose`
- **Allow**: SSH (22), HTTP (80), HTTPS (443)
- **Deny**: Everything else (default)
- **Restrict**: ARI (8088), PostgreSQL (5432) to localhost

---

## 🚨 Emergency Procedures

### Service Down
```bash
# 1. Check status
sudo systemctl status nexus

# 2. Check logs
sudo journalctl -u nexus -n 50

# 3. Restart
sudo systemctl restart nexus

# 4. If still down, check dependencies
sudo systemctl status postgresql nginx

# 5. Contact database admin if needed
```

### Database Corrupted
```bash
# 1. Stop application
sudo systemctl stop nexus

# 2. List backups
ls -lh /var/backups/nexus_db*.sql.gz

# 3. Restore latest backup
sudo -u postgres psql nexus_db < /var/backups/nexus_db_YYYYMMDD.sql.gz

# 4. Restart
sudo systemctl start nexus
```

### Disk Full
```bash
# 1. Find space hogs
sudo find /var/log -type f -size +100M 2>/dev/null

# 2. Clean old logs
sudo find /var/log -name "*.log.*" -mtime +30 -delete
sudo logrotate -f /etc/logrotate.d/nexus

# 3. Clean old backups
sudo find /var/backups -name "*.sql.gz" -mtime +30 -delete

# 4. Check again
df -h /var/
```

### Certificate Expired
```bash
# 1. Renew certificate
sudo certbot renew

# 2. Reload NGINX
sudo systemctl reload nginx

# 3. Verify
sudo certbot certificates
```

---

## 📞 Key Contacts & Resources

### Asterisk Resources
- **Documentation**: https://wiki.asterisk.org/wiki/display/AST/Getting+Started+with+ARI
- **ARI API**: https://wiki.asterisk.org/wiki/display/AST/Asterisk+REST+Interface
- **PJSIP**: https://wiki.asterisk.org/wiki/display/AST/PJSIP+Configuration+Wizard

### Flask & Python
- **Flask Docs**: https://flask.palletsprojects.com/
- **Flask-Login**: https://flask-login.readthedocs.io/
- **SQLAlchemy**: https://www.sqlalchemy.org/

### System Administration
- **Ubuntu Docs**: https://ubuntu.com/server/docs
- **NGINX**: https://nginx.org/en/docs/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **UFW**: https://wiki.ubuntu.com/UncomplicatedFirewall

### Security
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **Let's Encrypt**: https://letsencrypt.org/docs/
- **SSL Labs**: https://www.ssllabs.com/ssltest/

---

## 📝 Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-03-02 | 1.0 | Initial production deployment documentation |

---

## ✨ File Statistics

| File | Lines | Purpose |
|------|-------|---------|
| `nexus.service` | 45 | Systemd unit |
| `nexus.nginx.conf` | 200+ | NGINX configuration |
| `firewall.sh` | 150+ | Firewall setup |
| `asterisk-ari.conf` | 400+ | Asterisk reference |
| `deploy.sh` | 250+ | Automated deployment |
| `DEPLOYMENT.md` | 600+ | Complete guide |
| `DEPLOYMENT_SUMMARY.md` | 300+ | Overview |
| `PRODUCTION_CHECKLIST.md` | 400+ | Pre-launch checklist |
| `PRODUCTION_QUICKREF.md` | 500+ | Quick reference |
| `ARCHITECTURE.md` | 500+ | Architecture diagrams |
| **TOTAL** | **3,400+** | **Complete production documentation** |

---

## 🎓 Learning Resources

1. **Start Here**: DEPLOYMENT_SUMMARY.md
2. **Understand Architecture**: ARCHITECTURE.md
3. **Deploy Application**: DEPLOYMENT.md or deploy.sh
4. **Verify Setup**: PRODUCTION_CHECKLIST.md
5. **Daily Operations**: PRODUCTION_QUICKREF.md
6. **Troubleshooting**: Consult relevant docs above + journalctl logs

---

## 🔄 Update Cycle

- **Weekly**: Check logs, verify backups, monitor resource usage
- **Monthly**: Review security logs, test disaster recovery, update docs
- **Quarterly**: Full security audit, performance optimization, patch updates
- **Annually**: Comprehensive infrastructure review, capacity planning

---

**Last Updated**: March 2, 2026  
**Status**: ✅ Production Ready  
**Maintained By**: DevOps Team
