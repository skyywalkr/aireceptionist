# Nexus AI Receptionist - Production Architecture

## System Architecture Diagram

```
╔════════════════════════════════════════════════════════════════════════╗
║                           INTERNET / USERS                             ║
║                    (External, Untrusted Network)                       ║
╚════════════════════════════════════════════════════════════════════════╝
                                    │
                    HTTPS Port 443   │   DNS Resolution
                    (Encrypted)      │   yourdomain.com
                                    │
                    ┌───────────────▼───────────────┐
                    │    Let's Encrypt Cert         │
                    │  (Valid, Auto-Renewed)        │
                    └───────────────┬───────────────┘
                                    │
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║  ╔──────────────────────────────────────────────────────────────────╗ ║
║  │                    NGINX REVERSE PROXY                          │ ║
║  │                   (:80 → 443 Redirect)                          │ ║
║  │                                                                  │ ║
║  │  ┌────────────────────────────────────────────────────────────┐ │ ║
║  │  │ SSL/TLS Termination (HTTPS)                               │ ║
║  │  │ - TLSv1.2+, Strong Ciphers                                │ ║
║  │  │ - HSTS, CSP Headers                                       │ ║
║  │  │ - Security Headers (X-Frame, X-Content-Type, etc)        │ ║
║  │  │ - Request Rate Limiting (Zones)                           │ ║
║  │  │ - Connection Pooling                                      │ ║
║  │  │ - Access Logging                                          │ ║
║  │  └────────────────────────────────────────────────────────────┘ │ ║
║  │                          │                                       │ ║
║  │         Proxy to http://127.0.0.1:5000                         │ ║
║  │         (Localhost Only)                                        │ ║
║  │                          │                                       │ ║
║  └──────────────────────────┼───────────────────────────────────────┘ ║
║                             │                                         ║
║                ╔────────────▼──────────────╗                         ║
║                │                          │                          ║
║                │ UFW Firewall Rules       │                          ║
║                │ - :22 SSH (Rate Limited)│                          ║
║                │ - :80 HTTP (Public)     │                          ║
║                │ - :443 HTTPS (Public)   │                          ║
║                │ - Allow Others: DENY    │                          ║
║                └────────────┬─────────────┘                          ║
║                             │                                        ║
║                             ▼                                        ║
║        ╔────────────────────────────────────────────┐               ║
║        │      FLASK APPLICATION (Nexus)            │               ║
║        │      Running as: nexus user               │               ║
║        │      Process: systemd managed             │               ║
║        │                                            │               ║
║        │  ┌──────────────────────────────────────┐ │               ║
║        │  │ Request Processing                   │ │               ║
║        │  │ - Route: /, /auth/*, /api/*, /call   │ │               ║
║        │  │ - Authentication: Flask-Login        │ │               ║
║        │  │ - Rate Limiting: Flask-Limiter       │ │               ║
║        │  │ - Input Validation: Custom           │ │               ║
║        │  │ - CSRF Protection: Flask-WTF (ready)│ │               ║
║        │  │ - Password Hashing: bcrypt           │ │               ║
║        │  │ - Session Management: Secure Cookies │ │               ║
║        │  └──────────────────────────────────────┘ │               ║
║        │                                            │               ║
║        │  ┌──────────────────────────────────────┐ │               ║
║        │  │ Features                              │ │               ║
║        │  │ - User Signup/Login/Logout           │ │               ║
║        │  │ - Dashboard with Analytics           │ │               ║
║        │  │ - Call Origination (via ARI)         │ │               ║
║        │  │ - Call Logging                       │ │               ║
║        │  │ - Cost Tracking & Estimates          │ │               ║
║        │  │ - API Endpoints (REST)               │ │               ║
║        │  └──────────────────────────────────────┘ │               ║
║        │          │                    │           │               ║
║        │          │                    │           │               ║
║        └──────────┼────────────────────┼───────────┘               ║
║                   │                    │                           ║
║        ┌──────────▼─┐          ┌───────▼────────┐                 ║
║        │             │          │                │                 ║
║        ▼             │          ▼                ▼                 ║
║  ┌──────────────┐    │  ┌──────────────────────────────────┐      ║
║  │ PostgreSQL   │    │  │   Asterisk (PBX)               │      ║
║  │ Database     │    │  │   Separate Server              │      ║
║  │              │    │  │ (or same host in small setup)  │      ║
║  │ Tables:      │    │  │                                 │      ║
║  │ - users      │    │  │ ┌──────────────────────────────┐│      ║
║  │ - call_logs  │    │  │ │ ARI (Asterisk REST Interface)││      ║
║  │              │    │  │ │ http://127.0.0.1:8088        ││      ║
║  │ Features:    │    │  │ │ Auth: asterisk / password     ││      ║
║  │ - Indexed    │    │  │ │ Endpoints:                    ││      ║
║  │ - Encrypted  │    │  │ │ - /channels                   ││      ║
║  │ - Backups    │    │  │ │ - /playback                   ││      ║
║  │ - Local only │    │  │ │ - /recordings                 ││      ║
║  │   (localhost)│    │  │ │ - /events                     ││      ║
║  │              │    │  │ └──────────────────────────────┘│      ║
║  └──────────────┘    │  │                                 │      ║
║                      │  │ ┌──────────────────────────────┐│      ║
║   Backups:           │  │ │ PJSIP Trunk                  ││      ║
║   - Daily            │  │ │ (SIP Provider - e.g., Twilio)││      ║
║   - /var/backups/    │  │ │                               ││      ║
║   - gzip compressed  │  │ │ Inbound:  DID → Dialplan     ││      ║
║   - 30-day retention │  │ │ Outbound: /call → PJSIP      ││      ║
║                      │  │ └──────────────────────────────┘│      ║
║                      │  │                                 │      ║
║                      │  │ ┌──────────────────────────────┐│      ║
║                      │  │ │ Stasis App (ai_receptionist) ││      ║
║                      │  │ │                               ││      ║
║                      │  │ │ - Handles incoming calls      ││      ║
║                      │  │ │ - Records audio              ││      ║
║                      │  │ │ - Plays TTS responses        ││      ║
║                      │  │ │ - Event-driven via ARI       ││      ║
║                      │  │ └──────────────────────────────┘│      ║
║                      │  │                                 │      ║
║                      │  │ Dialplan:                        │      ║
║                      │  │ - from_trunk (incoming calls)    │      ║
║                      │  │ - ai_receptionist_app (routing)  │      ║
║                      │  │ - outbound_calls (originated)    │      ║
║                      │  │                                 │      ║
║                      │  │ Sounds Dir:                      │      ║
║                      │  │ /var/lib/asterisk/sounds/custom │      ║
║                      │  │ - Greetings (AI-generated)       │      ║
║                      │  │ - Responses (TTS)                │      ║
║                      │  │ - 8kHz mono ulaw format          │      ║
║                      │  └──────────────────────────────────┘      ║
║                      │                                            ║
║                      └────────────────────────────────────────────┘
║                                                                    ║
║  ┌──────────────────────────────────────────────────────────────┐ ║
║  │                    SECURITY LAYER                           │ ║
║  │                                                              │ ║
║  │  ✓ Rate Limiting (NGINX + Flask)                           │ ║
║  │  ✓ Input Validation (Phone, Email, Passwords)             │ ║
║  │  ✓ Password Hashing (bcrypt)                              │ ║
║  │  ✓ Session Security (Secure, HttpOnly, SameSite)          │ ║
║  │  ✓ HTTPS/TLS (Let's Encrypt, Auto-renewed)               │ ║
║  │  ✓ Security Headers (HSTS, CSP, X-Frame-Options)         │ ║
║  │  ✓ Firewall Rules (UFW, Deny by Default)                 │ ║
║  │  ✓ Database Encryption (Optional PostgreSQL SSL)         │ ║
║  │  ✓ Non-root Service User (nexus)                         │ ║
║  │  ✓ systemd Hardening (ProtectSystem, NoNewPrivileges)   │ ║
║  │  ✓ Localhost-only Services (DB, ARI)                     │ ║
║  │  ✓ API Key Masking (No exposure in responses)            │ ║
║  │  ✓ Secure Logging (No secrets in logs)                   │ ║
║  │                                                              │ ║
║  └──────────────────────────────────────────────────────────────┘ ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
                              │
        ┌───────────────────────┴──────────────────────┐
        │                                              │
    ┌───▼─────────┐                        ┌────────────▼───┐
    │ Monitoring  │                        │ Backups        │
    │ - Metrics   │                        │ - Daily        │
    │ - Logs      │                        │ - Encrypted    │
    │ - Alerts    │                        │ - Verified     │
    └─────────────┘                        └────────────────┘


## External Dependencies

┌──────────────────────────────────────────┐
│ External APIs (via Flask App)            │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ OpenAI API                         │  │
│ │ - GPT-4o-mini (fast & cheap)      │  │
│ │ - GPT-4 (powerful)                │  │
│ │ - Whisper (transcription)          │  │
│ │                                    │  │
│ │ Uses: OPENAI_API_KEY               │  │
│ │ Security: Secret in /etc/nexus/.env│ │
│ └────────────────────────────────────┘  │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ ElevenLabs API (Premium TTS)       │  │
│ │ - Voice synthesis                  │  │
│ │ - Voice library management        │  │
│ │ - Fallback: gTTS (free)            │  │
│ │                                    │  │
│ │ Uses: ELEVENLABS_API_KEY           │  │
│ │ Security: Secret in /etc/nexus/.env│ │
│ └────────────────────────────────────┘  │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ SIP Provider (e.g., Twilio)       │  │
│ │ - BYOC (Bring Your Own Carrier)   │  │
│ │ - Outbound call termination       │  │
│ │ - Inbound call delivery (optional)│  │
│ │                                    │  │
│ │ Uses: PJSIP trunk configuration    │  │
│ │ Security: Credentials in pjsip.conf│ │
│ └────────────────────────────────────┘  │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ Let's Encrypt (SSL Certificate)   │  │
│ │ - Auto-renewal                    │  │
│ │ - ACME protocol                   │  │
│ │                                    │  │
│ │ Uses: certbot automation           │  │
│ │ Security: TLS only, no secrets     │  │
│ └────────────────────────────────────┘  │
│                                          │
└──────────────────────────────────────────┘


## Data Flow Diagram

### Inbound Call (if configured)

    SIP Provider
         │
         │ SIP INVITE
         ▼
    ┌─────────────┐
    │  Asterisk   │
    │  PJSIP      │ ── Dialplan ──► Stasis(ai_receptionist)
    └─────────────┘
         │
         │ Stasis Events (WebSocket)
         ▼
    ┌─────────────────────┐
    │  ARI (:8088)        │
    │  http://127.0.0.1   │
    └──────────┬──────────┘
               │
               │ HTTP REST
               ▼
    ┌─────────────────────────────┐
    │  Flask App                  │
    │ - Handle StasisStart        │
    │ - Record audio              │
    │ - Transcribe (Whisper)      │
    │ - Generate reply (OpenAI)   │
    │ - Synthesize TTS (gTTS/EL)  │
    │ - Play back to caller       │
    │ - Log call (PostgreSQL)     │
    └──────────┬──────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  PostgreSQL Database │
    │  Insert CallLog      │
    └──────────────────────┘


### Outbound Call (Web UI)

    User Browser
         │
         │ HTTPS POST /call
         ▼
    ┌──────────────────┐
    │ NGINX Proxy      │
    │ - Rate Limit     │
    │ - SSL/TLS        │
    │ - Route to Flask │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ Flask /call Endpoint     │
    │ - Require Login          │
    │ - Validate Phone         │
    │ - Create CallLog entry   │
    │ - Generate AI greeting   │
    │ - Invoke ARI             │
    └────────┬─────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ ARI API          │
    │ channels.create()│
    │ PJSIP/+1555...@  │
    │ trunk            │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ PJSIP Trunk      │
    │ Send SIP INVITE  │
    │ to Provider      │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Remote Phone     │
    │ Rings...         │
    │ Call connects    │
    └──────────────────┘

```

## Container/Cloud Deployment (Optional)

For Docker/Kubernetes deployments, adjust:

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV FLASK_ENV=production
CMD ["python", "app.py"]
```

Deploy as container with:
- Volume mounts for `/var/lib/nexus`, `/var/log/nexus`
- Environment variables from secrets manager
- Network policy: PostgreSQL & ARI localhost only
- Resource requests/limits: Similar to systemd constraints
- Health check: HTTP GET /health endpoint
- Graceful shutdown: SIGTERM handling in app.py

---

**Architecture Version**: 1.0  
**Last Updated**: March 2, 2026  
**Deployment Status**: Production Ready ✅
