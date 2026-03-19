# Web UI & Pricing Guide

## Overview

The web UI provides a modern interface for customers to:
- Configure AI models (GPT-4o-mini, GPT-4)
- Select text-to-speech providers (Google TTS, ElevenLabs)
- Import and select voices from ElevenLabs
- See real-time pricing breakdowns
- Originate test calls

All pricing is **transparent and cost-plus**: you pay for what you use, with a configurable operational margin.

## Features

### 1. Configuration Tab

#### AI Model Selection
- **GPT-4o-mini** (default): Fast, cheap, good quality. Best for most use cases.
- **GPT-4**: Slower, more expensive, excellent quality. For complex conversations.

#### TTS Provider Selection
- **Google TTS (Free)**: Standard quality, no API cost. Good for cost-conscious customers.
- **ElevenLabs**: Premium quality, low latency, natural-sounding voices. Per-character pricing.

#### Phone Number Input
- Enter the destination phone number
- Format: `+1 (555) 123-4567` or `+15551234567`

#### Call Duration Estimate
- Slider from 15 to 300 seconds
- Used to estimate transcription costs (Whisper charges per minute)

### 2. Voices Tab

When ElevenLabs is selected as the TTS provider:
- Displays all available voices from your ElevenLabs account
- Shows voice category, name, and preview URL
- Click a voice to select it
- Click "🔊 Preview" to listen to a sample

Note: Voice import is automatic via the ElevenLabs API. No manual import needed.

### 3. Pricing Tab

Real-time breakdown of costs:
- **Transcription (Whisper)**: $0.02 per minute
- **Greeting Generation**: LLM cost + TTS cost
- **Reply Generation**: LLM cost + TTS cost
- **Operational Margin**: 30% (configurable)
- **Total per Call**: Customer pays this amount

Costs are estimates based on:
- Typical greeting length (~50 words)
- Typical reply length (~25 words)
- Call duration (affects transcription time)

## Pricing Model

### Cost Components

1. **Transcription (Whisper API)**
   - $0.02 per minute of audio
   - Charged per call based on caller's recording duration

2. **Text Generation (GPT)**
   - Greeting: ~200 input tokens, ~50 output tokens
   - Reply: ~300 input tokens, ~100 output tokens
   - Costs vary by model:
     - GPT-4o-mini: $0.00015/1K input, $0.0006/1K output
     - GPT-4: $0.03/1K input, $0.06/1K output

3. **Text-to-Speech**
   - gTTS (Google): Free
   - ElevenLabs: $0.30 per 1,000,000 characters
   - Greeting ~50 chars, reply ~100 chars

4. **Operational Margin**
   - Default 30% markup (configured via `PRICING_MARGIN`)
   - Covers infrastructure, support, profit

### Example Costs

**Cheapest (GPT-4o-mini + gTTS)**
```
Transcription (30s):        $0.01
Greeting (GPT + gTTS):      $0.00
Reply (GPT + gTTS):         $0.00
Subtotal:                   $0.01
Margin (30%):               $0.00
Total per call:             $0.013
```

**Premium (GPT-4 + ElevenLabs)**
```
Transcription (30s):        $0.01
Greeting (GPT-4 + EL):      $0.05
Reply (GPT-4 + EL):         $0.10
Subtotal:                   $0.16
Margin (30%):               $0.048
Total per call:             $0.208
```

## API Integration

### Frontend → Backend Flow

1. User selects config (model, TTS provider, voice)
2. Frontend calls `/api/estimate-cost` with configuration
3. Backend returns pricing breakdown
4. User clicks "Originate Test Call"
5. Frontend calls `/call` with all configuration
6. Backend originate call via ARI with chosen settings

### API Endpoints

#### GET `/`
Serves the web UI (HTML/CSS/JS).

#### POST `/call`
Originate a call with custom configuration.

Request:
```json
{
  "to": "+15551234567",
  "use_ai": true,
  "llm_model": "gpt-4o-mini",
  "tts_provider": "elevenlabs",
  "elevenlabs_voice": "21m00Tcm4TlvDq8ikWAM"
}
```

Response:
```json
{
  "status": "originated",
  "endpoint": "PJSIP/15551234567@trunk-provider",
  "channel": "1234567890.0",
  "use_ai": true,
  "config": {
    "llm_model": "gpt-4o-mini",
    "tts_provider": "elevenlabs"
  }
}
```

#### POST `/api/estimate-cost`
Get pricing estimate for a configuration.

Request:
```json
{
  "llm_model": "gpt-4o-mini",
  "tts_provider": "elevenlabs",
  "estimated_duration_seconds": 30
}
```

Response:
```json
{
  "transcription": {
    "cost": 0.01,
    "details": "0.5 min @ $0.02/min"
  },
  "greeting_llm": {
    "cost": 0.0001,
    "details": "~200 input, ~50 output tokens"
  },
  "greeting_tts": {
    "cost": 0.000015,
    "details": "50 chars @ $0.30/M"
  },
  "reply_llm": {
    "cost": 0.00015,
    "details": "~300 input, ~100 output tokens"
  },
  "reply_tts": {
    "cost": 0.00003,
    "details": "100 chars @ $0.30/M"
  },
  "subtotal": 0.010315,
  "margin": 0.003095,
  "total": 0.01341
}
```

#### GET `/api/elevenlabs-voices`
Fetch list of available ElevenLabs voices.

Response:
```json
{
  "voices": [
    {
      "id": "21m00Tcm4TlvDq8ikWAM",
      "name": "Rachel",
      "category": "female",
      "preview_url": "https://..."
    },
    ...
  ]
}
```

## Configuration

### Environment Variables

```bash
# Pricing margin (multiplier on API costs)
PRICING_MARGIN=1.3  # 30% margin

# ElevenLabs API key (optional)
ELEVENLABS_API_KEY=...

# OpenAI API key (required for AI features)
OPENAI_API_KEY=sk-...
```

### Customizing Pricing

Edit `pricing.py` to adjust:
- Base API costs
- Margin percentage
- Default TTS provider
- Estimate calculations

### Customizing Voices

ElevenLabs voices are fetched automatically from your account. To add custom voices:
1. Create them in ElevenLabs dashboard
2. They'll appear in the UI automatically
3. Select and use them in calls

## Cost Tracking & Analytics

The system passes through costs transparently:
- All API costs are calculated in real-time
- Margin is fixed and known upfront
- Customers see exact price before call
- No hidden fees

### Future Enhancements

- Store call history with costs
- Monthly invoice generation
- Usage analytics dashboard
- Custom pricing per customer
- Bulk call discounts

## Deployment

### Production Checklist

- [ ] Set `PRICING_MARGIN` to your desired markup
- [ ] Configure `ELEVENLABS_API_KEY` (optional)
- [ ] Test all TTS providers and models
- [ ] Verify cost estimates match actual API bills
- [ ] Set up call history logging
- [ ] Configure HTTPS/TLS for web UI

### Running Behind Reverse Proxy

For production, run behind nginx or Apache:

```nginx
location / {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Troubleshooting

### Voices not loading
- Check `ELEVENLABS_API_KEY` is set and valid
- Verify ElevenLabs account has active subscription
- Check API limits haven't been exceeded

### Pricing not calculating
- Ensure OpenAI API key is valid
- Check `PRICING_MARGIN` environment variable
- Verify `pricing.py` module is installed

### ElevenLabs preview not playing
- Check browser audio permissions
- Verify CORS headers allow audio streaming
- Test preview URLs directly in browser

### Call not originating
- Check Asterisk ARI connection
- Verify PJSIP trunk is registered
- Review Asterisk logs for dialplan errors

## Cost Savings Tips

### For End Users

1. Use GPT-4o-mini (3-5x cheaper than GPT-4)
2. Use Google TTS instead of ElevenLabs (free vs $0.30/M chars)
3. Keep greetings/replies short
4. Optimize call duration (record 15-30s instead of 60s)

### For Your Business

1. Negotiate volume discounts with OpenAI/ElevenLabs
2. Cache common greetings to avoid repeated TTS
3. Monitor API costs and adjust margins accordingly
4. Offer tiered pricing (economy, standard, premium)

## Example Pricing Tiers

```
Economy:
  - GPT-4o-mini + gTTS
  - ~$0.01-0.02 per call
  - Good for high volume

Standard:
  - GPT-4o-mini + ElevenLabs
  - ~$0.03-0.05 per call
  - Balanced quality/cost

Premium:
  - GPT-4 + ElevenLabs
  - ~$0.15-0.25 per call
  - Best quality and accuracy
```

Customers choose based on their needs and budget!
