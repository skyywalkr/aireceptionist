# Production Deployment Checklist - Nexus AI Receptionist

## Pre-Deployment Planning

- [ ] Obtain SSL certificate (Let's Encrypt recommended)
- [ ] Configure domain DNS records pointing to server IP
- [ ] Create database backup strategy
- [ ] Plan monitoring and alerting
- [ ] Document all API keys and credentials (in secure vault)
- [ ] Prepare disaster recovery plan
- [ ] Review security policy and compliance requirements
- [ ] Obtain necessary approvals from stakeholders

## Infrastructure Setup

### Server Provisioning
- [ ] Provision Ubuntu 20.04+ server with minimum 2GB RAM, 20GB disk
- [ ] Configure static IP address
- [ ] Enable automatic security updates
- [ ] Configure NTP for time synchronization
- [ ] Set timezone appropriately
- [ ] Disable IPv6 if not used (`/etc/sysctl.conf`)
- [ ] Set up SSH key-based authentication (no passwords)
- [ ] Disable SSH password login
- [ ] Enable SSH key agent forwarding for deployment

### Network Security
- [ ] Configure UFW firewall (run firewall.sh)
- [ ] Allow only necessary ports (22, 80, 443)
- [ ] Restrict ARI to localhost via firewall
- [ ] Restrict PostgreSQL to localhost via firewall
- [ ] Enable DDoS protection (CloudFlare, AWS Shield)
- [ ] Configure reverse DNS (PTR records)
- [ ] Set up VPN or jump host for admin access (optional)

## Application Deployment

### System Setup
- [ ] Create `nexus` system user (non-root)
- [ ] Create application directory `/opt/nexus`
- [ ] Create data directory `/var/lib/nexus`
- [ ] Create log directory `/var/log/nexus`
- [ ] Set correct ownership: `nexus:nexus`
- [ ] Set correct permissions: 700 (rwx------)
- [ ] Clone/upload application code
- [ ] Create Python 3.11 virtual environment
- [ ] Install all Python dependencies
- [ ] Copy `.env.example` to `/etc/nexus/.env`

### Configuration
- [ ] Generate secure SECRET_KEY (32 hex chars minimum)
- [ ] Set FLASK_ENV=production
- [ ] Configure DATABASE_URL (PostgreSQL)
- [ ] Set Asterisk ARI credentials
- [ ] Add OpenAI API key
- [ ] Add ElevenLabs API key (if using premium TTS)
- [ ] Set PJSIP trunk name
- [ ] Configure audio directory path
- [ ] Set pricing parameters (MARGIN, MINIMUM_CHARGE)
- [ ] Verify all secrets are NOT in version control
- [ ] Set /etc/nexus/.env permissions to 600 (read-only for nexus user)

### Database
- [ ] Create PostgreSQL database (not SQLite)
- [ ] Create database user with limited privileges
- [ ] Run database migrations/schema creation
- [ ] Set up database backups (daily)
- [ ] Configure backup retention policy (30+ days)
- [ ] Test backup restoration process
- [ ] Enable PostgreSQL SSL connections (optional but recommended)
- [ ] Monitor database size and performance

### Systemd Service
- [ ] Copy `nexus.service` to `/etc/systemd/system/`
- [ ] Review service file for correctness
- [ ] `systemctl daemon-reload`
- [ ] `systemctl enable nexus` (auto-start on boot)
- [ ] Test service start/stop/restart
- [ ] Verify service restarts after failure
- [ ] Configure restart limits (avoid crash loops)
- [ ] Test graceful shutdown (30 second timeout)

### NGINX Reverse Proxy
- [ ] Copy `nexus.nginx.conf` to `/etc/nginx/sites-available/nexus`
- [ ] Create symbolic link in `sites-enabled`
- [ ] Replace `yourdomain.com` with actual domain
- [ ] Update SSL certificate paths (Let's Encrypt)
- [ ] Validate NGINX configuration: `nginx -t`
- [ ] Configure security headers (CSP, HSTS, etc.)
- [ ] Set up rate limiting zones
- [ ] Configure logging (separate access/error logs)
- [ ] Enable gzip compression
- [ ] Test HTTPS redirect (HTTP → HTTPS)
- [ ] Verify SSL A+ rating (ssllabs.com)

### SSL/TLS Certificate
- [ ] Obtain SSL certificate (Let's Encrypt)
- [ ] Verify certificate validity and chain
- [ ] Configure certificate auto-renewal (certbot)
- [ ] Test certificate renewal process
- [ ] Add certificate renewal to cron/systemd timer
- [ ] Ensure certificate has at least 30 days before expiry alerts

## Asterisk Configuration

### ARI Setup
- [ ] Enable ARI in `/etc/asterisk/ari.conf`
- [ ] Set ARI to bind to 127.0.0.1:8088 only
- [ ] Configure ARI user credentials (secure password)
- [ ] Load required ARI modules
- [ ] Test ARI connectivity: `curl -u asterisk:pass http://127.0.0.1:8088/ari/asterisk/info`
- [ ] Verify ARI events are received

### PJSIP Configuration
- [ ] Configure PJSIP trunk in `/etc/asterisk/pjsip.conf`
- [ ] Test trunk registration: `pjsip show registrations`
- [ ] Verify trunk is online and available
- [ ] Configure transport (TLS recommended for security)
- [ ] Set up SIP provider credentials securely
- [ ] Test outbound calls via trunk
- [ ] Verify inbound calls from trunk (if applicable)

### Dialplan
- [ ] Create dialplan context `ai_receptionist_app`
- [ ] Create dialplan context `from_trunk`
- [ ] Verify Stasis app invocation
- [ ] Test dialplan with test calls
- [ ] Confirm calls reach Stasis app
- [ ] Monitor dialplan logs

### Audio Configuration
- [ ] Create custom sounds directory: `/var/lib/asterisk/sounds/custom`
- [ ] Set ownership: `asterisk:asterisk`
- [ ] Verify ffmpeg can write to directory
- [ ] Test audio file generation and conversion
- [ ] Verify 8kHz mono ulaw format (Asterisk native)

## Security Hardening

### System Security
- [ ] Disable unnecessary services
- [ ] Enable SELinux or AppArmor (optional)
- [ ] Configure fail2ban for brute force protection
- [ ] Set up intrusion detection (Tripwire or AIDE)
- [ ] Configure secure SSH: key-based only, no passwords
- [ ] Disable SSH root login
- [ ] Enable SSH key agent
- [ ] Configure sudo without password (for automation)
- [ ] Disable swap (or encrypt swap)
- [ ] Set up AIDE/Tripwire file integrity monitoring

### Application Security
- [ ] Verify SECRET_KEY is unique and secure
- [ ] Ensure no API keys in version control
- [ ] Enable Flask security features (SESSION_COOKIE_SECURE, etc.)
- [ ] Configure CSRF protection (Flask-WTF)
- [ ] Enable rate limiting (Flask-Limiter)
- [ ] Verify HTTPS enforcement
- [ ] Check for SQL injection vulnerabilities
- [ ] Review input validation
- [ ] Audit API endpoints for exposure
- [ ] Implement request signing (optional)

### Database Security
- [ ] Use strong database password
- [ ] Restrict database access to localhost only
- [ ] Enable PostgreSQL connection logging
- [ ] Monitor slow queries
- [ ] Implement query timeout limits
- [ ] Disable unnecessary extensions
- [ ] Set up read-only replicas (optional)
- [ ] Enable audit logging

### Network Security
- [ ] Firewall rules in place (UFW verified)
- [ ] No open ports beyond 22, 80, 443
- [ ] ARI not accessible from public network
- [ ] PostgreSQL not accessible from public network
- [ ] Rate limiting enabled in NGINX
- [ ] DDoS protection enabled (CloudFlare, AWS, etc.)
- [ ] IP whitelisting for admin panels (optional)

## Monitoring and Logging

### Application Monitoring
- [ ] Set up application monitoring (New Relic, DataDog, etc.)
- [ ] Monitor error rates and exceptions
- [ ] Track response times
- [ ] Monitor API endpoint performance
- [ ] Set up alerts for high error rates
- [ ] Monitor database connection pool
- [ ] Track active channels (Asterisk)
- [ ] Monitor disk usage
- [ ] Monitor memory usage
- [ ] Monitor CPU usage

### Logging
- [ ] Configure structured logging (JSON format)
- [ ] Ship logs to centralized location (ELK, Splunk, etc.)
- [ ] Configure log rotation (logrotate)
- [ ] Set up log retention policy
- [ ] Monitor logs for errors and warnings
- [ ] Exclude sensitive data from logs (passwords, API keys)
- [ ] Implement audit logging for user actions
- [ ] Set up alerting for critical errors

### Health Checks
- [ ] Implement `/health` endpoint
- [ ] Monitor Flask application health
- [ ] Monitor Asterisk ARI connectivity
- [ ] Monitor PostgreSQL connectivity
- [ ] Monitor NGINX status
- [ ] Set up health check monitoring (Uptime Robot, Pingdom)
- [ ] Configure automated alerting for down services

## Testing and Validation

### Functionality Testing
- [ ] Test user signup and login flow
- [ ] Test call origination (outbound)
- [ ] Test inbound call handling (if configured)
- [ ] Test AI greeting generation
- [ ] Test call recording and transcription
- [ ] Test AI reply generation
- [ ] Test TTS (both gTTS and ElevenLabs)
- [ ] Test pricing calculation
- [ ] Test database logging of calls
- [ ] Test user dashboard and analytics

### Load Testing
- [ ] Perform load testing (Apache Bench, wrk)
- [ ] Test with expected concurrent calls
- [ ] Verify system stability under load
- [ ] Monitor resource usage during load test
- [ ] Identify and fix performance bottlenecks
- [ ] Test database connection pool limits
- [ ] Test rate limiting behavior

### Security Testing
- [ ] Run vulnerability scanner (OWASP ZAP, Burp Suite)
- [ ] Test authentication bypass
- [ ] Test API parameter tampering
- [ ] Test SQL injection
- [ ] Test XSS attacks
- [ ] Test CSRF attacks
- [ ] Test for information disclosure
- [ ] Test for privilege escalation
- [ ] Review security headers

### Disaster Recovery
- [ ] Test database backup restoration
- [ ] Test application deployment rollback
- [ ] Test data recovery from backups
- [ ] Document RTO and RPO
- [ ] Practice disaster recovery drills
- [ ] Maintain runbooks for common issues

## Operational Procedures

### Runbooks
- [ ] Create incident response runbook
- [ ] Create deployment runbook
- [ ] Create rollback runbook
- [ ] Create backup/restore runbook
- [ ] Create scaling/performance tuning runbook
- [ ] Create database maintenance runbook
- [ ] Document all manual procedures

### Backup and Recovery
- [ ] Automated daily database backups
- [ ] Off-site backup storage (AWS S3, Azure, etc.)
- [ ] Backup encryption enabled
- [ ] Backup verification process
- [ ] Document recovery procedures
- [ ] Test recovery process monthly
- [ ] Monitor backup job completion
- [ ] Alert on backup failures

### Updates and Patches
- [ ] Enable automatic security updates
- [ ] Plan and test OS updates
- [ ] Plan and test Python package updates
- [ ] Plan and test Asterisk updates
- [ ] Plan and test PostgreSQL updates
- [ ] Document update procedures
- [ ] Maintain version inventory
- [ ] Test updates in staging first

### Maintenance Windows
- [ ] Schedule maintenance windows (low-traffic times)
- [ ] Notify users before maintenance
- [ ] Create status page for status updates
- [ ] Have rollback plan ready
- [ ] Document all changes made
- [ ] Monitor closely after maintenance

## Documentation

- [ ] Document system architecture diagram
- [ ] Document deployment procedures
- [ ] Document configuration management
- [ ] Document troubleshooting guide
- [ ] Document API documentation
- [ ] Document database schema
- [ ] Document security policies
- [ ] Document disaster recovery procedures
- [ ] Document operational procedures
- [ ] Document escalation contacts
- [ ] Document system dependencies
- [ ] Create architecture decision records (ADRs)

## Post-Deployment

- [ ] Verify all services running correctly
- [ ] Verify SSL certificate validity
- [ ] Verify database backups working
- [ ] Verify monitoring and alerting active
- [ ] Verify logging working correctly
- [ ] Verify firewalls blocking unwanted traffic
- [ ] Perform smoke tests
- [ ] Notify stakeholders of successful deployment
- [ ] Schedule post-deployment review meeting
- [ ] Update runbooks with any discovered issues
- [ ] Monitor closely for first week (24/7 if possible)

## Ongoing Maintenance

Weekly:
- [ ] Review logs for errors
- [ ] Monitor resource usage trends
- [ ] Verify backups completed successfully
- [ ] Check SSL certificate expiry (>30 days)

Monthly:
- [ ] Review security logs
- [ ] Test disaster recovery procedures
- [ ] Review and update documentation
- [ ] Analyze performance metrics
- [ ] Review and update firewall rules

Quarterly:
- [ ] Conduct security audit
- [ ] Update system packages
- [ ] Review and optimize performance
- [ ] Update disaster recovery procedures
- [ ] Conduct penetration testing (optional)

Annually:
- [ ] Full security assessment
- [ ] Update business continuity plan
- [ ] Review licensing and compliance
- [ ] Update infrastructure
- [ ] Full disaster recovery drill
