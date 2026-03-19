"""
ElevenLabs TTS integration with voice management.

Provides:
- Voice listing and import from ElevenLabs
- Text-to-speech synthesis via ElevenLabs API
- Automatic WAV conversion for Asterisk compatibility
"""
import os
import subprocess
import tempfile
import requests
from typing import List, Dict, Optional

ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"
ASTERISK_SOUNDS_DIR = os.environ.get('ASTERISK_SOUNDS_DIR', '/var/lib/asterisk/sounds/custom')


def get_available_voices() -> List[Dict]:
    """Fetch list of available voices from ElevenLabs."""
    if not ELEVENLABS_API_KEY:
        return []

    try:
        resp = requests.get(
            f"{ELEVENLABS_API_URL}/voices",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            voices = data.get('voices', [])
            return [
                {
                    'id': v['voice_id'],
                    'name': v['name'],
                    'category': v.get('category', 'unknown'),
                    'preview_url': v.get('preview_url'),
                }
                for v in voices
            ]
    except Exception as e:
        print(f"Error fetching ElevenLabs voices: {e}")

    return []


def synthesize_text_elevenlabs(
    text: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default: Rachel
    stability: float = 0.5,
    similarity_boost: float = 0.75,
) -> Optional[str]:
    """Synthesize text to speech using ElevenLabs API.

    Args:
        text: Text to synthesize
        voice_id: ElevenLabs voice ID
        stability: Voice stability (0.0-1.0, higher = more stable)
        similarity_boost: Similarity boost (0.0-1.0, higher = more similar to voice)

    Returns:
        Basename for Asterisk playback, or None on error
    """
    if not ELEVENLABS_API_KEY:
        return None

    try:
        resp = requests.post(
            f"{ELEVENLABS_API_URL}/text-to-speech/{voice_id}",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                },
            },
            timeout=30,
        )

        if resp.status_code == 200:
            # Save MP3 and convert to WAV
            os.makedirs(ASTERISK_SOUNDS_DIR, exist_ok=True)

            import uuid
            basename = f"el_{int(uuid.uuid4().int % (10**8))}"
            mp3_path = os.path.join(ASTERISK_SOUNDS_DIR, f"{basename}_temp.mp3")
            wav_path = os.path.join(ASTERISK_SOUNDS_DIR, f"{basename}.wav")

            # Write MP3
            with open(mp3_path, 'wb') as f:
                f.write(resp.content)

            # Convert to Asterisk WAV
            cmd = [
                'ffmpeg', '-i', mp3_path,
                '-ar', '8000', '-ac', '1',
                '-codec:a', 'pcm_mulaw',
                '-y', wav_path
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=30)

            # Clean up MP3
            try:
                os.remove(mp3_path)
            except:
                pass

            if result.returncode == 0:
                return f"custom/{basename}"
            else:
                print(f"ffmpeg conversion failed: {result.stderr.decode()}")
                return None
        else:
            print(f"ElevenLabs API error: {resp.status_code} {resp.text}")
            return None

    except Exception as e:
        print(f"Error synthesizing with ElevenLabs: {e}")
        return None


def get_voice_info(voice_id: str) -> Optional[Dict]:
    """Get details for a specific voice."""
    if not ELEVENLABS_API_KEY:
        return None

    try:
        resp = requests.get(
            f"{ELEVENLABS_API_URL}/voices/{voice_id}",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            timeout=10,
        )
        if resp.status_code == 200:
            v = resp.json()
            return {
                'id': v['voice_id'],
                'name': v['name'],
                'category': v.get('category', 'unknown'),
                'description': v.get('description', ''),
                'preview_url': v.get('preview_url'),
                'labels': v.get('labels', {}),
            }
    except Exception as e:
        print(f"Error fetching voice info: {e}")

    return None
