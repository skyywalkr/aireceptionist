Run instructions and checklist

1) Install Asterisk (on Linux) and enable ARI
- Asterisk should be configured to listen on the ARI port (default 8088).
- Place the `ari.conf` snippet into `/etc/asterisk/ari.conf` and restart Asterisk.

2) Place sounds folder
- Ensure `ASTERISK_SOUNDS_DIR` exists and is readable by the Asterisk user, e.g.
  `sudo mkdir -p /var/lib/asterisk/sounds/custom && sudo chown asterisk:asterisk /var/lib/asterisk/sounds/custom`

3) Configure `pjsip.conf` and `extensions.conf`
- Copy sample snippets and customize credentials, trunk name, etc.

4) Start Flask app
- Create Python virtualenv, install `requirements.txt` and run `python app.py`.

5) Test
- Use `curl` to originate a call:

```bash
curl -X POST http://localhost:5000/call -H 'Content-Type: application/json' \
 -d '{"to":"15551234567","use_ai":true}'
```

6) Troubleshooting notes
- If generated audio doesn't play, convert MP3 to WAV using ffmpeg:
  `ffmpeg -i greeting.mp3 -ar 8000 -ac 1 greeting.wav` and use `custom/greeting` as the sound name.
- Check Asterisk logs (`/var/log/asterisk/full`) for ARI errors.

