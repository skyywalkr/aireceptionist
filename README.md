# Asterisk + Flask AI Receptionist

This project provides a complete turnkey Asterisk + Flask setup for an AI-powered receptionist that can make and receive calls via SIP, record caller input, transcribe it, generate intelligent replies, and play them back—all using OpenAI APIs. Includes a **modern web dashboard** for pricing, model selection, and voice configuration.

## Features

- **Web UI Dashboard** – Modern interface for configuration and call origination
- **Transparent Per-Call Pricing** – Cost-plus model with configurable margin
- **Multiple AI Models** – GPT-4o-mini (fast/cheap) or GPT-4 (powerful)
- **Multiple TTS Providers** – Google TTS (free) or ElevenLabs (premium)
- **Voice Selection** – Import and select from ElevenLabs voices
- **Outbound calling** via PJSIP SIP trunk
- **AI-generated greetings** (GPT + TTS)
- **Call recording** (Asterisk native)
- **Speech-to-text** transcription (Whisper API)
- **AI conversation** (GPT generates replies)
- **Text-to-speech playback** (gTTS or ElevenLabs + ffmpeg conversion)
- **Asterisk-compatible audio** (8kHz mono ulaw WAV files)
- **ARI integration** for call control
- **REST API** for programmatic access

## Project Structure

```
.
├── app.py                  # Flask app + ARI + web UI server
├── ai_receptionist.py      # AI/TTS/transcription helpers
├── pricing.py              # Cost calculation & pricing logic
├── elevenlabs_tts.py      # ElevenLabs API integration
├── requirements.txt        # Python dependencies
├── check_setup.py         # Pre-flight validation script
├── test_ai_flow.py        # Integration tests
├── systemd.service        # Systemd unit file
├── .env.example           # Environment variables template
├── README.md              # This file
├── PRICING.md             # Detailed pricing documentation
├── DEPLOYMENT.md          # Detailed setup & troubleshooting
├── run_instructions.md    # Quick start guide
├── templates/
│   └── index.html         # Modern web UI dashboard
└── asterisk/              # Sample Asterisk configs
    ├── pjsip.conf         # SIP trunk configuration
    ├── extensions.conf    # Dialplan
    └── ari.conf           # ARI server configuration
```

## Quick Start

### 1. Install dependencies

```bash
# Python packages
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# System packages (Ubuntu/Debian - primary Linux deployment)
sudo apt-get update
sudo apt-get install ffmpeg python3-dev

# Alternative for CentOS/RHEL
# sudo yum install ffmpeg python3-devel
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Asterisk ARI credentials and OpenAI API key
# Optionally add ElevenLabs API key for premium voices
```

### 3. Validate setup

```bash
python check_setup.py
```

### 4. Start Flask app

```bash
python app.py
```

Flask listens on `http://localhost:5000`.

### 5. Open the web UI

Visit `http://localhost:5000` in your browser and:
- Select an AI model (GPT-4o-mini or GPT-4)
- Select a TTS provider (Google TTS or ElevenLabs)
- Review pricing breakdown
- Enter a phone number
- Click "Originate Test Call"

## How It Works

### Incoming Call Flow (Optional)

1. Caller dials your SIP trunk
2. Asterisk routes to Stasis app (`ai_receptionist`)
3. Flask handler plays greeting, records response, replies via AI

### Outbound Call Flow (POST `/call`)

1. **Originate** – Flask sends ARI request to originate a call to `to` number via PJSIP trunk
2. **Greeting** – If `use_ai=true`, AI generates a greeting (GPT-4o-mini or GPT-4) and converts to speech
3. **Playback** – Asterisk plays greeting to answering party
4. **Recording** – Asterisk records caller's response (up to 30 seconds)
5. **Transcription** – Whisper API transcribes the recording
6. **Reply** – GPT generates a receptionist response
7. **TTS** – gTTS or ElevenLabs generates speech from reply text
8. **Playback** – Asterisk plays AI reply to caller
9. **Hangup** – Call ends

## Web UI Features

### 🎯 Configuration Tab
- **Model Selection**: Choose between GPT-4o-mini or GPT-4
- **TTS Provider**: Select Google TTS (free) or ElevenLabs (premium)
- **Voice Selection**: Pick from available ElevenLabs voices with preview
- **Phone Input**: Enter destination number
- **Duration Estimate**: Slider for estimated call length (affects pricing)
- **Instant Cost Estimate**: Real-time pricing breakdown

### 🎤 Voices Tab
- Browse available voices from your ElevenLabs account
- Listen to voice previews
- Select preferred voice for calls

### 💰 Pricing Tab
- Transparent cost breakdown:
  - Transcription (Whisper)
  - Greeting generation (LLM + TTS)
  - Reply generation (LLM + TTS)
  - Operational margin
  - **Total per call**
- All costs passed through with configurable margin (default 30%)

### 📱 Call Origination
- One-click test call origination
- Real-time call status
- Channel monitoring

## API Endpoints

### GET `/`
Serves the modern web UI dashboard.

### POST `/call`
Originate an outbound call with custom configuration.

**Request:**
```json
{
  "to": "+15551234567",
  "use_ai": true,
  "llm_model": "gpt-4o-mini",
  "tts_provider": "elevenlabs",
  "elevenlabs_voice": "21m00Tcm4TlvDq8ikWAM"
}
```

**Response:**
```json
{
  "status": "originated",
  "endpoint": "PJSIP/15551234567@trunk",
  "channel": "1234567890.0",
  "use_ai": true,
  "config": {
    "llm_model": "gpt-4o-mini",
    "tts_provider": "elevenlabs"
  }
}
```

### POST `/api/estimate-cost`
Get pricing estimate for a configuration.

**Request:**
```json
{
  "llm_model": "gpt-4o-mini",
  "tts_provider": "elevenlabs",
  "estimated_duration_seconds": 30
}
```

**Response:**
```json
{
  "transcription": { "cost": 0.01, "details": "..." },
  "greeting_llm": { "cost": 0.0001, "details": "..." },
  "greeting_tts": { "cost": 0.000015, "details": "..." },
  "reply_llm": { "cost": 0.00015, "details": "..." },
  "reply_tts": { "cost": 0.00003, "details": "..." },
  "subtotal": 0.010315,
  "margin": 0.003095,
  "total": 0.01341
}
```

### GET `/api/elevenlabs-voices`
Fetch available ElevenLabs voices.

**Response:**
```json
{
  "voices": [
    {
      "id": "21m00Tcm4TlvDq8ikWAM",
      "name": "Rachel",
      "category": "female",
      "preview_url": "https://..."
    }
  ]
}
```

### GET `/channels`
List active channels and their state.

**Response:**
```json
{
  "channels": {
    "1234567890.0": {
      "status": "recording",
      "greeting_file": "custom/greeting_123456",
      "recording_file": "rec_1234567890_0"
    }
  }
}
```

## Audio Format Details

All generated audio is converted to **Asterisk-compatible WAV**:
- **Sample rate:** 8 kHz
- **Channels:** 1 (mono)
- **Codec:** μ-law (PCMU)
- **Extension:** `.wav`

This is done automatically via ffmpeg when TTS is generated.

## Configuration

See `DEPLOYMENT.md` for detailed Asterisk setup, PJSIP trunk configuration, and troubleshooting.

### Key Environment Variables

```bash
# Asterisk & ARI
ARI_URL=http://127.0.0.1:8088
ARI_USER=asterisk
ARI_PASS=secret
ARI_APP_NAME=ai_receptionist
PJSIP_TRUNK_NAME=trunk-provider
ASTERISK_SOUNDS_DIR=/var/lib/asterisk/sounds/custom

# OpenAI (required for AI features)
ENABLE_AI=true
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# ElevenLabs (optional, for premium TTS)
ELEVENLABS_API_KEY=...

# Pricing
PRICING_MARGIN=1.3  # 30% margin on top of API costs
```

### Pricing Configuration

The system uses a **cost-plus pricing model**:
1. Calculate actual API costs (Whisper, GPT, TTS)
2. Apply margin multiplier (default 30%)
3. Present total to customer

This ensures you stay cost-neutral while providing flexibility for profit margins.

**Adjust margin in `.env`:**
```bash
PRICING_MARGIN=1.5   # 50% margin
PRICING_MARGIN=1.2   # 20% margin
PRICING_MARGIN=1.0   # No margin (cost-only)
```

See `PRICING.md` for detailed cost breakdown and examples.

## Testing

### Pre-flight checks
```bash
python check_setup.py
```

### Run integration tests
```bash
python test_ai_flow.py
```

### Manual testing via web UI
1. Visit `http://localhost:5000`
2. Configure model and TTS provider
3. See pricing in real-time
4. Enter phone number
5. Click "Originate Test Call"

### View Asterisk logs
```bash
tail -f /var/log/asterisk/full
```

### Check active channels
```bash
curl http://localhost:5000/channels | jq
```

## Security & Production Notes

⚠️ **Important:**
- **Never expose ARI to the public internet** without TLS and firewall
- Use strong ARI credentials
- Rate-limit the `/call` endpoint
- Monitor API costs (Whisper and GPT calls are not free)
- Deploy behind a reverse proxy (nginx, Apache)
- Use a dedicated SIP trunk with limited permissions

See `DEPLOYMENT.md` for production deployment steps, including systemd integration.

## Customization

### Change AI model
Edit `.env` and set `OPENAI_MODEL`:
```bash
OPENAI_MODEL=gpt-4  # More capable but slower/costlier
```

### Change TTS provider
Replace gTTS in `ai_receptionist.py` with:
- **Eleven Labs** (lower latency, better quality)
- **AWS Polly** (high quality, wide language support)
- **Google Cloud TTS** (good quality, cheap)

### Add call routing
Extend `app.py` to transfer calls based on caller input, e.g.:
```python
if "billing" in caller_text:
    transfer_to = "sip:billing@internal"
```

### Add persistent logging
Connect to a database to log calls, transcripts, and replies for auditing.

## Troubleshooting

See `DEPLOYMENT.md` for detailed troubleshooting:
- Audio not playing
- Transcription failing
- ARI connection errors
- PJSIP trunk not registering
- Memory leaks or hanging calls

## Next Steps

- [ ] Add call transfer to human agent
- [ ] Integrate with CRM/helpdesk
- [ ] Add metrics and monitoring
- [ ] Implement callback functionality
- [ ] Add multi-language support
- [ ] Stream audio for lower latency

## License

MIT

## Support

For issues or questions, check `DEPLOYMENT.md` or review Asterisk logs at `/var/log/asterisk/full`.

