# Quick Reference: Web UI & Pricing

## For Your Customers

### 🌐 Visit the Web UI
```
http://your-domain:5000
```

### 📋 3-Step Setup
1. **Pick a model**: GPT-4o-mini (fast/cheap) or GPT-4 (powerful)
2. **Pick TTS**: Google (free) or ElevenLabs (premium)
3. **Set phone**: Enter destination number
4. **Check price**: See exact cost before calling

### 💰 Example Costs (Per Call)

| Config | Cost |
|--------|------|
| GPT-4o-mini + Google TTS | $0.01–0.02 |
| GPT-4o-mini + ElevenLabs | $0.03–0.05 |
| GPT-4 + ElevenLabs | $0.15–0.25 |

All prices include 30% operational margin.

---

## For Deployment

### Setup ElevenLabs Integration

1. **Get API Key**
   - Sign up at elevenlabs.io
   - Create workspace
   - Copy API key

2. **Add to `.env`**
   ```bash
   ELEVENLABS_API_KEY=your-key-here
   ```

3. **Restart Flask**
   - Voices auto-populate in UI
   - No manual import needed

### Customize Pricing Margin

```bash
# In .env
PRICING_MARGIN=1.3   # 30% margin (default)
PRICING_MARGIN=1.5   # 50% margin
PRICING_MARGIN=1.0   # No margin
```

Margin is applied to **all API costs**, so you stay profitable regardless of which model/TTS customers choose.

### Cost Tracking

The system calculates and returns costs in the API response:

```json
{
  "transcription": { "cost": 0.01 },
  "greeting_llm": { "cost": 0.0001 },
  "greeting_tts": { "cost": 0.000015 },
  "reply_llm": { "cost": 0.00015 },
  "reply_tts": { "cost": 0.00003 },
  "subtotal": 0.010315,
  "margin": 0.003095,
  "total": 0.01341
}
```

Store this with each call for billing and analytics.

### Integrate with Your Billing System

Web UI calls `/api/estimate-cost` before origination. You can:

1. **Log costs to database** (add to app.py)
2. **Bill customer after call completes** (store in DB)
3. **Show usage analytics** (dashboard extension)
4. **Offer billing tiers** (standard, premium, etc.)

Example integration:

```python
@app.route('/api/estimate-cost', methods=['POST'])
def estimate_cost():
    # ... existing code ...
    pricing = estimate_call_cost(llm_model, tts_provider, duration)
    
    # NEW: Log to database
    db.log_cost_estimate(
        customer_id=request.user_id,
        config={'llm': llm_model, 'tts': tts_provider},
        pricing=pricing
    )
    
    return jsonify(pricing)
```

---

## File Summary

| File | Purpose |
|------|---------|
| `pricing.py` | Cost calculation, margin logic |
| `elevenlabs_tts.py` | ElevenLabs API, voice fetching |
| `templates/index.html` | Web UI (HTML/CSS/JS) |
| `app.py` | Flask endpoints + ARI handler |
| `PRICING.md` | Detailed pricing documentation |

---

## Common Customizations

### Change Default Margin
Edit `pricing.py`, line 15:
```python
MARGIN_MULTIPLIER = Decimal('1.3')  # Change to your desired margin
```

### Change Estimated Costs
Edit `pricing.py`, function `estimate_call_cost()` to adjust token counts or durations.

### Add Custom Voices
ElevenLabs voices auto-populate. To filter or reorder:
- Modify `/api/elevenlabs-voices` endpoint in `app.py`
- Filter by category or name

### Customize UI Colors
Edit `templates/index.html`, line 12-20:
```css
:root {
    --primary: #667eea;   /* Change this */
    --secondary: #764ba2;
    /* ... */
}
```

---

## Troubleshooting

### No voices showing?
```bash
# Check ElevenLabs API key
echo $ELEVENLABS_API_KEY

# Test API directly
curl https://api.elevenlabs.io/v1/voices \
  -H "xi-api-key: your-key"
```

### Pricing shows $0.00?
- Check OpenAI API key is set
- Verify `pricing.py` is imported
- Check logs: `grep -i "price" /var/log/asterisk/full`

### UI not loading?
- Check Flask is running: `curl http://localhost:5000`
- Check templates directory exists: `ls templates/index.html`
- Restart Flask app

---

## Production Checklist

- [ ] Set ELEVENLABS_API_KEY in .env
- [ ] Configure PRICING_MARGIN for desired profit
- [ ] Test all model/TTS combinations
- [ ] Verify costs match actual API bills
- [ ] Set up call logging (for billing)
- [ ] Deploy behind HTTPS proxy
- [ ] Monitor API costs weekly
- [ ] Test UI on mobile devices
- [ ] Set up automated billing/invoicing
- [ ] Create usage dashboard for customers

---

## Support

For detailed pricing info: see `PRICING.md`
For deployment: see `DEPLOYMENT.md`
For API docs: see `README.md`
