# Nexus AI Receptionist - Production Quick Reference

## Key Files

| File | Location | Purpose |
|------|----------|---------|
| `nexus.service` | `/etc/systemd/system/` | Systemd service unit |
| `.env` | `/etc/nexus/.env` | Environment variables & secrets |
| `nexus.nginx.conf` | `/etc/nginx/sites-available/` | NGINX reverse proxy config |
| Database | PostgreSQL localhost:5432 | User data, call logs, settings |
| Asterisk ARI | `http://127.0.0.1:8088` | Call origination & control |
| Application | `/opt/nexus/app.py` | Flask application |

## Start/Stop/Restart

```bash
# Start service
sudo systemctl start nexus

# Stop service
sudo systemctl stop nexus

# Restart service
sudo systemctl restart nexus

# Enable auto-start on boot
sudo systemctl enable nexus

# Check status
sudo systemctl status nexus

# View logs (real-time)
sudo journalctl -u nexus -f

# View logs (last 100 lines)
sudo journalctl -u nexus -n 100

# View logs (errors only)
sudo journalctl -u nexus -p err
```

## Health Checks

```bash
# Application health
curl -I https://yourdomain.com/dashboard

# NGINX status
curl -I http://127.0.0.1/health 2>/dev/null || echo "NGINX OK"

# Asterisk ARI
curl -u asterisk:password http://127.0.0.1:8088/ari/asterisk/info

# PostgreSQL
sudo -u postgres psql -c "SELECT version();"

# System resources
free -h
df -h
top -b -n 1 | head -20
```

## Common Tasks

### View Application Logs
```bash
# Last 50 lines
sudo journalctl -u nexus -n 50 --no-pager

# Follow in real-time
sudo journalctl -u nexus -f

# Search for error
sudo journalctl -u nexus | grep -i error
```

### Restart NGINX
```bash
sudo nginx -t  # Test config
sudo systemctl reload nginx  # Reload
sudo systemctl restart nginx  # Restart
```

### View Database Status
```bash
# Connect to database
sudo -u postgres psql nexus_db

# Check connections
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

# Check slow queries (if enabled)
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

# Check database size
SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname))
FROM pg_database ORDER BY pg_database_size(pg_database.datname) DESC;
```

### Backup Database
```bash
sudo -u postgres pg_dump nexus_db | gzip > /var/backups/nexus_db_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore Database
```bash
sudo -u postgres psql nexus_db < /var/backups/nexus_db_YYYYMMDD_HHMMSS.sql.gz
```

### Check Disk Usage
```bash
df -h /opt/nexus /var/lib/nexus /var/log/nexus
du -sh /opt/nexus /var/lib/nexus /var/log/nexus
```

### Check CPU/Memory Usage
```bash
ps aux | grep python | grep nexus
htop -p $(pidof python)
```

### Monitor Active Calls (Asterisk)
```bash
sudo asterisk -rvvv
asterisk*CLI> core show calls
asterisk*CLI> core show channels verbose
```

### Check Firewall Status
```bash
sudo ufw status verbose
```

### Certificate Information
```bash
# Check expiry date
sudo certbot certificates

# Manual renewal
sudo certbot renew --dry-run
sudo certbot renew
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u nexus -n 50

# Test configuration
sudo systemctl cat nexus

# Manual startup (for debugging)
sudo -u nexus /opt/nexus/venv/bin/python /opt/nexus/app.py
```

### Database Connection Failed
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
sudo -u nexus psql postgresql://nexus@localhost/nexus_db -c "SELECT 1;"

# Check connection credentials in .env
sudo cat /etc/nexus/.env | grep DATABASE_URL
```

### NGINX Errors
```bash
# Test configuration
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log

# Check proxy connectivity
curl -v http://127.0.0.1:5000/
```

### Asterisk ARI Issues
```bash
# Check ARI is enabled
sudo asterisk -rvvv
asterisk*CLI> ari show status

# Check connectivity
curl -v -u asterisk:password http://127.0.0.1:8088/ari/asterisk/info

# Enable debug logging
asterisk*CLI> ari set debug all
```

### High Memory Usage
```bash
# Check Python process
ps aux | grep python

# Check database connections
sudo -u postgres psql -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Monitor actively
watch -n 1 'ps aux | grep python | head -5'
```

### High Disk Usage
```bash
# Find large files
sudo find /var/log -size +1G -type f

# Check log rotation
sudo cat /etc/logrotate.d/nexus

# Manually rotate logs
sudo logrotate -f /etc/logrotate.d/nexus

# Clean old logs
sudo find /var/log/nexus -name "*.log.*" -mtime +30 -delete
```

## Environment Variables

Located in `/etc/nexus/.env`:

```bash
# Core Flask config
FLASK_ENV=production
SECRET_KEY=<generated-hex-32>
DEBUG=False

# Database (PostgreSQL)
DATABASE_URL=postgresql://nexus:password@localhost:5432/nexus_db

# Asterisk ARI
ARI_URL=http://127.0.0.1:8088
ARI_USER=asterisk
ARI_PASS=<secure-password>
ARI_APP_NAME=ai_receptionist
PJSIP_TRUNK_NAME=trunk

# Audio & AI
ASTERISK_SOUNDS_DIR=/var/lib/asterisk/sounds/custom
ENABLE_AI=true

# API Keys (keep secret!)
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...

# Pricing
PRICING_MARGIN=1.3
MINIMUM_CHARGE_PER_CALL=0.15
```

To update an environment variable:
```bash
sudo nano /etc/nexus/.env
sudo systemctl restart nexus  # Changes take effect on restart
```

## Port Reference

| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| 22 | SSH | Public | Remote administration |
| 80 | HTTP | Public | Redirect to HTTPS |
| 443 | HTTPS | Public | Web application |
| 5000 | Flask | Localhost | Application (proxied by NGINX) |
| 5432 | PostgreSQL | Localhost | Database |
| 8088 | Asterisk ARI | Localhost | Call control API |
| 5060 | SIP | Trunk IP | SIP trunk (if external) |
| 10000-20000 | RTP | Trunk IP | Media streams (if external) |

## Performance Tuning

### Flask Application
- Edit `/opt/nexus/app.py` for `workers` parameter
- Increase `SQLALCHEMY_POOL_SIZE` for high concurrency

### PostgreSQL
- Edit `/etc/postgresql/13/main/postgresql.conf`
- Increase `max_connections` for more concurrent users
- Tune `shared_buffers`, `effective_cache_size`, `maintenance_work_mem`

### NGINX
- Edit `/etc/nginx/nginx.conf`
- Increase `worker_processes` = number of CPU cores
- Increase `worker_connections` = (total RAM MB / 2)

### System
- Increase file descriptors: `ulimit -n 65536`
- Tune TCP: `/etc/sysctl.conf` parameters
- Monitor with `htop`, `iostat`, `netstat`

## Useful Commands

```bash
# View application version
grep -i version /opt/nexus/README.md

# List running processes
ps aux | grep nexus

# Count active Python threads
cat /proc/$(pgrep -f "python.*app.py")/status | grep Threads

# Monitor network connections
netstat -an | grep ESTABLISHED | wc -l

# Check SSL certificate
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | grep -i subject

# Test HTTPS redirect
curl -I http://yourdomain.com

# Benchmark response time
ab -n 100 -c 10 https://yourdomain.com/

# Check DNS resolution
nslookup yourdomain.com
dig yourdomain.com
```

## Emergency Procedures

### Service Completely Down
```bash
# 1. Check if service is running
sudo systemctl status nexus

# 2. Try to restart
sudo systemctl restart nexus

# 3. Check logs
sudo journalctl -u nexus -n 100

# 4. Check dependencies (database, NGINX)
sudo systemctl status postgresql
sudo systemctl status nginx

# 5. If still failing, start manually with debugging
sudo -u nexus /opt/nexus/venv/bin/python /opt/nexus/app.py 2>&1 | head -50
```

### Database Corruption
```bash
# 1. Stop service
sudo systemctl stop nexus

# 2. Restore from latest backup
sudo -u postgres psql nexus_db < /var/backups/nexus_db_LATEST.sql.gz

# 3. Verify database
sudo -u postgres psql nexus_db -c "SELECT COUNT(*) FROM user;"

# 4. Restart service
sudo systemctl start nexus
```

### Disk Full
```bash
# 1. Find large files
sudo find / -type f -size +100M 2>/dev/null | sort -k5 -rn

# 2. Clean logs
sudo find /var/log -name "*.log*" -mtime +30 -delete
sudo logrotate -f /etc/logrotate.d/nexus

# 3. Clean database backups
sudo find /var/backups -name "*.sql.gz" -mtime +30 -delete

# 4. Check disk again
df -h
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

## Monitoring Checklist (Daily)

- [ ] No errors in `sudo journalctl -u nexus -p err`
- [ ] Database backups completed: `ls -lh /var/backups/nexus_db*.sql.gz | head -1`
- [ ] Disk usage < 80%: `df -h | grep -v tmpfs`
- [ ] SSL certificate valid: `sudo certbot certificates | grep "Expiry Date"`
- [ ] Asterisk ARI up: `curl -s -u asterisk:pass http://127.0.0.1:8088/ari/asterisk/info`
- [ ] NGINX accessible: `curl -s https://yourdomain.com -I | head -1`
- [ ] Service running: `sudo systemctl is-active nexus`

## Contact Information

- **On-Call Engineer**: [contact]
- **Manager**: [contact]
- **Security Team**: [contact]
- **Database Admin**: [contact]
- **Asterisk Expert**: [contact]

## Related Documentation

- Deployment Guide: `DEPLOYMENT.md`
- Security Guide: `SECURITY.md`
- Production Checklist: `PRODUCTION_CHECKLIST.md`
- Asterisk Configuration: `asterisk-ari.conf`
- NGINX Configuration: `nexus.nginx.conf`
- Firewall Setup: `firewall.sh`
