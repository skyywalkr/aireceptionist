# Production Deployment Files Summary

## Files Created

### 1. **nexus.service** - Systemd Unit
- Location: `/etc/systemd/system/nexus.service`
- Purpose: Runs Flask application as a managed systemd service
- Features:
  - Runs as non-root `nexus` user
  - Automatic restart on failure
  - Resource limits (1GB memory, 50% CPU)
  - Security hardening (ProtectSystem, NoNewPrivileges)
  - Graceful shutdown with 30s timeout
  - Journal logging integration
  - Health check ready

### 2. **nexus.nginx.conf** - NGINX Reverse Proxy
- Location: `/etc/nginx/sites-available/nexus`
- Purpose: HTTP(S) reverse proxy with security features
- Features:
  - HTTP to HTTPS redirect
  - SSL/TLS configuration (TLSv1.2+)
  - Security headers (HSTS, CSP, X-Frame-Options)
  - Rate limiting zones (general, API, auth, calls)
  - Request/response buffering
  - Connection pooling (keepalive)
  - Static file caching
  - Different timeouts per endpoint type
  - Deny sensitive files (dotfiles, backups)
  - Access/error logging

### 3. **firewall.sh** - UFW Firewall Configuration
- Location: Run as `sudo bash firewall.sh` or execute commands manually
- Purpose: Configure Linux firewall (UFW) for security
- Features:
  - SSH security (enable first!)
  - Allow HTTP/HTTPS for public access
  - Restrict ARI to localhost only
  - Restrict PostgreSQL to localhost only
  - Optional SIP trunk access rules
  - Rate limiting on SSH
  - Default deny incoming policy
  - Backup/restore capability
  - Troubleshooting commands

### 4. **asterisk-ari.conf** - Asterisk Configuration Guide
- Location: Reference guide (copy relevant sections to `/etc/asterisk/`)
- Purpose: Configure Asterisk for AI receptionist integration
- Covers:
  - ARI enabled and secured (`ari.conf`)
  - PJSIP trunk setup (`pjsip.conf`)
  - Asterisk dialplan configuration
  - Module loading requirements
  - Logger setup for debugging
  - Testing and verification commands
  - Performance tuning
  - Troubleshooting guide

### 5. **deploy.sh** - Automated Deployment Script
- Location: Run as `sudo bash deploy.sh` from `/opt/nexus`
- Purpose: Automated server setup (10-step process)
- Automates:
  1. System updates
  2. Dependency installation
  3. Nexus system user creation
  4. Application directories
  5. Python virtual environment setup
  6. PostgreSQL database creation
  7. Environment configuration
  8. Systemd service installation
  9. NGINX reverse proxy setup
  10. UFW firewall configuration

### 6. **DEPLOYMENT.md** - Complete Deployment Guide
- Location: `/opt/nexus/DEPLOYMENT.md`
- Purpose: Step-by-step production deployment instructions
- Includes:
  - Architecture overview diagram
  - Prerequisites and requirements
  - 10-step manual deployment procedure
  - PostgreSQL setup with security
  - SSL certificate configuration (Let's Encrypt)
  - Firewall setup details
  - Systemd service configuration
  - Log rotation setup
  - Verification checklist
  - Monitoring and maintenance procedures
  - Troubleshooting guide
  - Security best practices
  - Rollback procedures

### 7. **PRODUCTION_CHECKLIST.md** - Pre-Deployment Checklist
- Location: `/opt/nexus/PRODUCTION_CHECKLIST.md`
- Purpose: Comprehensive checklist for production deployment
- Covers:
  - Pre-deployment planning (30+ items)
  - Infrastructure setup (networking, security)
  - Application deployment (system, config, DB)
  - Asterisk configuration (ARI, PJSIP, dialplan)
  - Security hardening (system, app, DB, network)
  - Monitoring and logging setup
  - Testing and validation procedures
  - Operational procedures and runbooks
  - Documentation requirements
  - Post-deployment verification
  - Ongoing maintenance schedule
  - 150+ items total to verify before launch

### 8. **PRODUCTION_QUICKREF.md** - Quick Reference Guide
- Location: `/opt/nexus/PRODUCTION_QUICKREF.md`
- Purpose: Fast access to common commands and tasks
- Includes:
  - Key file locations and purposes
  - Start/stop/restart service commands
  - Health check procedures
  - Common maintenance tasks
  - Database backup/restore
  - Troubleshooting flowchart
  - Environment variable reference
  - Port reference table
  - Performance tuning tips
  - Emergency procedures
  - Daily monitoring checklist
  - Useful Linux commands

## Deployment Flow

### Option 1: Automated (Using deploy.sh)
```bash
# 1. SSH to server
ssh ubuntu@your-server

# 2. Clone repository
cd /opt
sudo git clone <repo> nexus
cd nexus

# 3. Run automated deployment
sudo bash deploy.sh

# 4. Configure domain and secrets
sudo nano /etc/nexus/.env

# 5. Setup SSL
sudo certbot certonly --nginx -d yourdomain.com

# 6. Start service
sudo systemctl start nexus
```

**Time: ~10 minutes**

### Option 2: Manual (Following DEPLOYMENT.md)
```bash
# Follow 10 steps in DEPLOYMENT.md:
# 1. Create system user
# 2. Setup application
# 3. Configure environment
# 4. Setup database
# 5. Configure NGINX
# 6. Setup SSL
# 7. Configure firewall
# 8. Install systemd service
# 9. Setup log rotation
# 10. Configure Asterisk
```

**Time: ~30 minutes** (more control, better for understanding)

## Security Architecture

```
┌─────────────────────────────────────────────────┐
│ User (HTTPS)                                    │
└────────────────┬────────────────────────────────┘
                 │ :443 (encrypted)
                 ▼
┌─────────────────────────────────────────────────┐
│ NGINX Reverse Proxy                             │
│ - Rate limiting                                 │
│ - SSL/TLS termination                          │
│ - Security headers                              │
│ - Request validation                            │
└────────────────┬────────────────────────────────┘
                 │ :5000 (localhost only)
                 ▼
┌─────────────────────────────────────────────────┐
│ Flask Application (Nexus)                       │
│ - Authentication (Flask-Login)                  │
│ - Rate limiting (Flask-Limiter)                │
│ - Input validation                              │
│ - Secure session management                    │
└────┬───────────────────────────────────┬────────┘
     │ :5432                             │ :8088
     │ (localhost only)                  │ (localhost only)
     ▼                                   ▼
┌──────────────┐              ┌──────────────────────┐
│ PostgreSQL   │              │ Asterisk             │
│ - Encrypted  │              │ ARI API              │
│ - Backups    │              │ - PJSIP trunk       │
│ - Auditing   │              │ - Recording & AI    │
└──────────────┘              └──────────────────────┘
```

## Key Security Features

✅ **Implemented in Deployment:**
- Non-root service user (nexus)
- systemd security hardening
- Localhost-only access for sensitive services
- Firewall rules (UFW)
- HTTPS enforcement
- SSL/TLS with Let's Encrypt
- HSTS headers
- Security headers (CSP, X-Frame-Options)
- Rate limiting (NGINX + Flask)
- Input validation and sanitization
- Password hashing (bcrypt)
- Session management (Flask-Login)
- Database security (PostgreSQL, no root)
- Log rotation
- Automatic backups

## File Permissions

| File | User | Group | Mode | Purpose |
|------|------|-------|------|---------|
| `/etc/nexus/.env` | nexus | nexus | 600 | Secrets file |
| `/opt/nexus` | nexus | nexus | 755 | App directory |
| `/var/lib/nexus` | nexus | nexus | 700 | Data directory |
| `/var/log/nexus` | nexus | nexus | 700 | Log directory |
| `/etc/nginx/sites-available/nexus` | root | root | 644 | NGINX config |
| `/etc/systemd/system/nexus.service` | root | root | 644 | Service unit |

## Ports Reference

| Port | Service | Direction | Access |
|------|---------|-----------|--------|
| 22 | SSH | Inbound | Public (restricted) |
| 80 | HTTP | Inbound | Public (redirect) |
| 443 | HTTPS | Inbound | Public |
| 5000 | Flask | Inbound | Localhost only |
| 5432 | PostgreSQL | Inbound | Localhost only |
| 8088 | Asterisk ARI | Inbound | Localhost only |

## Monitoring Tools

Recommended for production:

- **Application Monitoring**: New Relic, DataDog, Sentry, Prometheus
- **Log Aggregation**: ELK Stack, Splunk, LogentStack
- **Status Page**: Statuspage.io, StatusCake
- **Uptime Monitoring**: Pingdom, UptimeRobot
- **Performance Testing**: Apache Bench, wrk, Locust
- **Security Scanning**: OWASP ZAP, Burp Suite, Nessus

## Post-Deployment Verification

Run these to verify everything is working:

```bash
# Service running
sudo systemctl is-active nexus

# Database accessible
sudo -u nexus psql postgresql://nexus@localhost/nexus_db -c "SELECT 1"

# NGINX responding
curl -I https://yourdomain.com

# Asterisk ARI accessible
curl -u asterisk:password http://127.0.0.1:8088/ari/asterisk/info

# Backups being created
ls -lh /var/backups/nexus_db*.sql.gz | head -1

# Disk usage healthy
df -h | grep -v tmpfs

# Logs clean
sudo journalctl -u nexus -p err
```

## Disaster Recovery Plan

### Backup Strategy
- **What**: PostgreSQL database + application code
- **When**: Daily at 02:00 UTC
- **Where**: Off-site (AWS S3, Azure, GCS)
- **Retention**: 30 days
- **Test**: Monthly restoration drill

### Recovery Procedures
1. **Service Crash**: `sudo systemctl restart nexus` (auto-restarts)
2. **Database Corruption**: Restore from backup
3. **Disk Full**: Clean logs, expand storage
4. **Certificate Expired**: Renew with certbot
5. **Complete Failure**: Re-run deploy.sh from latest backup

## Next Steps

1. **Immediate**: Run PRODUCTION_CHECKLIST.md before going live
2. **Pre-deployment**: Test in staging environment first
3. **Deployment**: Use deploy.sh or follow DEPLOYMENT.md
4. **Post-deployment**: Verify with checklist and quick reference
5. **Ongoing**: Use PRODUCTION_QUICKREF.md for daily operations

## Support Resources

- **Asterisk Documentation**: https://wiki.asterisk.org/
- **Flask Deployment**: https://flask.palletsprojects.com/deployment/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **NGINX**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/docs/
- **Ubuntu**: https://ubuntu.com/server/docs

---

**Last Updated**: March 2, 2026
**Version**: 1.0
**Status**: Production Ready ✅
