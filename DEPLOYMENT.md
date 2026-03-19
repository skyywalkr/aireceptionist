# Deployment & Troubleshooting Guide

## Two-Way AI Conversation Flow

When a call is initiated via `/call` with `use_ai=true`:

1. **Initial greeting** – AI generates a greeting, converts to WAV, and plays it to the caller
2. **Recording** – Asterisk records the caller's response (up to 30 seconds or until silence)
3. **Transcription** – Whisper API transcribes the recorded audio to text
4. **AI reply** – GPT-4o-mini generates a receptionist response
5. **Playback** – Reply is converted to speech and played back to caller
6. **Hangup** – Call is terminated

## Prerequisites

### System packages
- **ffmpeg** (for audio conversion)
- **Python 3.8+**
- **Asterisk 18+** with ARI enabled

Install ffmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

### Python dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Verify setup
```bash
python check_setup.py
```

## Configuration

### 1. Asterisk ARI Setup

Edit `/etc/asterisk/ari.conf`:
```ini
[general]
enabled = yes
pretty = yes

[asterisk]
type = user
read_only = no
password = secret
```

Then reload:
```bash
asterisk -rx "module reload res_ari.so"
```

### 2. PJSIP Trunk Configuration

Edit `/etc/asterisk/pjsip.conf` and add your SIP trunk credentials:
```ini
[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0

[trunk-provider-reg]
type=registration
outbound_auth=trunk-auth
server_uri=sip:your-provider.example
client_uri=sip:YOUR_USERNAME@your-provider.example

[trunk-auth]
type=auth
auth_type=userpass
password=YOUR_TRUNK_PASSWORD
username=YOUR_TRUNK_USERNAME

[trunk-endpoint]
type=endpoint
transport=transport-udp
context=from-trunk
disallow=all
allow=ulaw,alaw
outbound_auth=trunk-auth
```

Reload:
```bash
asterisk -rx "pjsip reload"
```

### 3. Dialplan (extensions.conf)

Add to `/etc/asterisk/extensions.conf`:
```ini
[from-trunk]
exten => _X.,1,NoOp(Incoming call to ${EXTEN})
 same => n,Answer()
 same => n,Stasis(ai_receptionist)
 same => n,Hangup()

[from-local]
; For outbound calls originated via ARI
exten => _X.,1,NoOp(Local call to ${EXTEN})
 same => n,Stasis(ai_receptionist)
 same => n,Hangup()
```

### 4. Environment Variables

Copy `.env.example` to `.env` and customize:
```bash
cp .env.example .env
```

Edit `.env`:
```bash
ARI_URL=http://127.0.0.1:8088
ARI_USER=asterisk
ARI_PASS=secret
ARI_APP_NAME=ai_receptionist
PJSIP_TRUNK_NAME=trunk-endpoint
ASTERISK_SOUNDS_DIR=/var/lib/asterisk/sounds/custom
ENABLE_AI=true
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Ensure Asterisk sounds directory exists and is writable:
```bash
sudo mkdir -p /var/lib/asterisk/sounds/custom
sudo chown asterisk:asterisk /var/lib/asterisk/sounds/custom
```

## Running

### Development mode
```bash
source .venv/bin/activate
python app.py
```

Flask will be available at `http://localhost:5000`.

### Production deployment

See `systemd.service` for a systemd unit example.

## Testing

### Check setup
```bash
python check_setup.py
```

### Originate a call
```bash
curl -X POST http://localhost:5000/call \
  -H 'Content-Type: application/json' \
  -d '{"to":"15551234567","use_ai":true}'
```

### Check active channels
```bash
curl http://localhost:5000/channels | jq
```

### View Asterisk logs
```bash
# Real-time
tail -f /var/log/asterisk/full

# Search for errors
grep -i "error\|warning" /var/log/asterisk/full
```

## Troubleshooting

### Audio not playing

**Symptom**: Greeting or reply doesn't play, but call connects.

**Cause**: Asterisk audio format mismatch.

**Fix**:
1. Check Asterisk log for codec errors
2. Verify WAV files are 8kHz, mono, ulaw:
   ```bash
   ffprobe /var/lib/asterisk/sounds/custom/greeting_*.wav
   ```
3. If converting manually:
   ```bash
   ffmpeg -i input.mp3 -ar 8000 -ac 1 -codec:a pcm_mulaw output.wav
   ```

### Transcription not working

**Symptom**: Recording is made but transcription returns empty.

**Cause**: Whisper API issue or recording quality.

**Fix**:
1. Verify `OPENAI_API_KEY` is set and valid
2. Check recording file exists:
   ```bash
   ls -la /var/lib/asterisk/sounds/custom/rec_*.wav
   ```
3. Test Whisper directly:
   ```python
   import openai
   with open('rec_*.wav', 'rb') as f:
       resp = openai.Audio.transcribe(model='whisper-1', file=f)
   print(resp['text'])
   ```

### ARI connection fails

**Symptom**: "Failed to connect to ARI" error.

**Cause**: ARI not enabled or credentials wrong.

**Fix**:
1. Check ARI is enabled:
   ```bash
   asterisk -rx "module show like res_ari"
   ```
   Should show `res_ari.so` as loaded.
2. Check ARI config:
   ```bash
   asterisk -rx "ari show status"
   ```
3. Verify credentials in `.env` match `ari.conf`
4. Check firewall:
   ```bash
   sudo netstat -tlnp | grep 8088
   ```

### Call won't originate

**Symptom**: POST `/call` returns "originated" but no ringing.

**Cause**: PJSIP trunk not registered or dialplan issue.

**Fix**:
1. Check trunk status:
   ```bash
   asterisk -rx "pjsip show registrations"
   ```
   Should show trunk as "Registered".
2. Check dialplan:
   ```bash
   asterisk -rx "dialplan show from-local"
   ```
3. Test manually:
   ```bash
   asterisk -rx "channel originate PJSIP/15551234567@trunk-endpoint application Playback hello-world"
   ```

### Memory leaks or hanging calls

**Symptom**: Flask app memory grows or calls don't hang up.

**Cause**: Unclosed recording objects or missing hangup calls.

**Fix**:
1. Restart Asterisk and Flask app
2. Check for orphaned recordings:
   ```bash
   asterisk -rx "recording show"
   ```
3. Kill lingering channels:
   ```bash
   asterisk -rx "channel request hangup all"
   ```

## Security Notes

- **Never expose ARI to the public internet** without TLS/firewall
- Use strong ARI credentials
- Rate-limit the `/call` endpoint in production
- Monitor AI API costs (Whisper and GPT calls add up)
- Use a separate SIP trunk with limited credentials

## Performance Tips

- Use `gpt-4o-mini` for fast responses; upgrade to `gpt-4` if needed
- Cache greetings if they're static
- Consider streaming TTS (e.g., Eleven Labs) for lower latency
- Run Flask behind gunicorn/uWSGI + nginx for production

## Next Steps

- Integrate with your CRM/ticketing system
- Add call recording to S3/cloud storage
- Implement call routing logic (e.g., transfer to human agent)
- Add metrics/monitoring (Prometheus, Datadog)
