# UFW (Uncomplicated Firewall) Configuration for Nexus AI Receptionist
# Ubuntu/Debian systems
# File: Run these commands on your production server

# ============================================================================
# CRITICAL: Enable SSH FIRST before enabling firewall!
# ============================================================================

sudo ufw allow 22/tcp comment "SSH - CRITICAL: Enable before ufw enable"

# ============================================================================
# Enable Firewall
# ============================================================================

sudo ufw enable

# ============================================================================
# Allow Public Access (HTTPS)
# ============================================================================

# HTTP (redirect to HTTPS)
sudo ufw allow 80/tcp comment "HTTP - Redirect to HTTPS"

# HTTPS (main web interface)
sudo ufw allow 443/tcp comment "HTTPS - Web interface"

# ============================================================================
# Allow Local Services Only (via localhost)
# ============================================================================

# Asterisk ARI (local only - behind NGINX)
sudo ufw allow from 127.0.0.1 to 127.0.0.1 port 8088 comment "Asterisk ARI - Localhost only"

# PostgreSQL (local only)
sudo ufw allow from 127.0.0.1 to 127.0.0.1 port 5432 comment "PostgreSQL - Localhost only"

# Flask development (if needed, local only)
sudo ufw allow from 127.0.0.1 to 127.0.0.1 port 5000 comment "Flask - Localhost only"

# ============================================================================
# Asterisk VoIP (optional, if accepting SIP trunks)
# ============================================================================

# Uncomment and configure if your Asterisk box receives external SIP trunks

# SIP (UDP) - replace 203.0.113.0/24 with your SIP provider's IP range
# sudo ufw allow from 203.0.113.0/24 to any port 5060 proto udp comment "SIP - From trunk provider"

# RTP (UDP) - media streams
# sudo ufw allow 10000:20000/udp comment "RTP - Media streams"

# ============================================================================
# Default Policies
# ============================================================================

# Already set during enable, but be explicit:
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw default deny routed

# ============================================================================
# Verification
# ============================================================================

sudo ufw status verbose

# ============================================================================
# Expected Output:
# ============================================================================
# Status: active
#
# To                         Action      From
# --                         ------      ----
# 22/tcp                     ALLOW       Anywhere
# 80/tcp                     ALLOW       Anywhere
# 443/tcp                    ALLOW       Anywhere
# 8088 (v6)                  ALLOW       127.0.0.1
# 5432 (v6)                  ALLOW       127.0.0.1
# 5000 (v6)                  ALLOW       127.0.0.1
# 22/tcp (v6)                ALLOW       Anywhere (v6)
# 80/tcp (v6)                ALLOW       Anywhere (v6)
# 443/tcp (v6)               ALLOW       Anywhere (v6)

# ============================================================================
# Optional: Restrict specific IPs (office/VPN only)
# ============================================================================

# If you want only specific IPs to access HTTPS:
# sudo ufw allow from 203.0.113.10 to any port 443 comment "HTTPS - Office"
# sudo ufw deny 443/tcp
# (Deny the open rule if IP-restricted)

# ============================================================================
# Advanced: Rate Limiting at Firewall Level (optional)
# ============================================================================

# Limit connection attempts per IP (helps against brute force)
sudo ufw limit 22/tcp comment "SSH - Rate limited"

# Limit HTTP requests
sudo ufw limit 80/tcp comment "HTTP - Rate limited"

# ============================================================================
# Backup and Restore Firewall Rules
# ============================================================================

# Backup rules
sudo cp /etc/ufw/user.rules /etc/ufw/user.rules.backup
sudo cp /etc/ufw/before.rules /etc/ufw/before.rules.backup

# Restore from backup (if needed)
# sudo cp /etc/ufw/user.rules.backup /etc/ufw/user.rules
# sudo ufw reload

# ============================================================================
# Troubleshooting
# ============================================================================

# Check firewall logs
sudo tail -f /var/log/ufw.log

# Disable firewall (emergency only)
# sudo ufw disable

# Reset to defaults (dangerous!)
# sudo ufw reset
