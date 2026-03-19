"""
AI helper: record, transcribe, generate replies, and produce Asterisk-compatible audio.

This module provides:
- `generate_receptionist_greeting(destination)`: create initial greeting TTS audio
- `transcribe_caller_audio(audio_path)`: convert caller recording to text via Whisper
- `generate_ai_reply(caller_text)`: ask AI for a receptionist response
- `generate_tts_wav(text)`: create TTS audio and convert to Asterisk-compatible WAV

Notes:
- Generates MP3 via gTTS, then converts to WAV (8kHz mono, ulaw) via ffmpeg.
- Requires `ffmpeg` installed on the system.
- Asterisk playback works best with `sound:` prefix and the basename without extension.
"""
import os
import uuid
import subprocess
import openai
from gtts import gTTS
from pydub import AudioSegment

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
ASTERISK_SOUNDS_DIR = os.environ.get('ASTERISK_SOUNDS_DIR', '/var/lib/asterisk/sounds/custom')

openai.api_key = OPENAI_API_KEY


def _convert_mp3_to_asterisk_wav(mp3_path: str, wav_path: str) -> bool:
    """Convert MP3 to WAV (8kHz, mono, ulaw) for Asterisk playback.

    Returns True if successful, False otherwise.
    """
    try:
        # Use ffmpeg to convert: 8kHz mono, ulaw codec (PCMU)
        cmd = [
            'ffmpeg', '-i', mp3_path,
            '-ar', '8000',
            '-ac', '1',
            '-codec:a', 'pcm_mulaw',
            '-y',  # overwrite
            wav_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode != 0:
            print(f"ffmpeg error: {result.stderr.decode()}")
            return False
        return True
    except Exception as e:
        print(f"Error converting MP3 to WAV: {e}")
        return False


def generate_receptionist_greeting(dest_number: str) -> str:
    """Generate a short receptionist greeting and return sound basename.

    Returns the basename (no extension) to be used as `custom/<basename>`.
    """
    if not OPENAI_API_KEY:
        text = f"Hello, thank you for calling. How can I help you today?"
    else:
        prompt = f"You are a professional phone receptionist. Produce a short (one-sentence) friendly greeting when answering an incoming call. Introduce the company and ask how you can help. Keep it brief and natural."
        resp = openai.ChatCompletion.create(
            model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.6,
        )
        text = resp['choices'][0]['message']['content'].strip()

    return _generate_tts_wav(text)


def _generate_tts_wav(text: str) -> str:
    """Generate TTS audio from text and convert to Asterisk-compatible WAV.

    Returns the basename (no extension) for playback as `custom/<basename>`.
    """
    os.makedirs(ASTERISK_SOUNDS_DIR, exist_ok=True)

    basename = f"greeting_{int(uuid.uuid4().int % (10**8))}"
    mp3_path = os.path.join(ASTERISK_SOUNDS_DIR, f"{basename}_temp.mp3")
    wav_path = os.path.join(ASTERISK_SOUNDS_DIR, f"{basename}.wav")

    # Generate MP3 via gTTS
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(mp3_path)
    except Exception as e:
        print(f"Error generating TTS: {e}")
        return None

    # Convert to Asterisk WAV (8kHz, mono, ulaw)
    if _convert_mp3_to_asterisk_wav(mp3_path, wav_path):
        # Clean up temp MP3
        try:
            os.remove(mp3_path)
        except:
            pass
        return f"custom/{basename}"
    else:
        print(f"Failed to convert {mp3_path} to {wav_path}")
        return None


def transcribe_caller_audio(audio_path: str) -> str:
    """Transcribe recorded audio (from Asterisk) to text using Whisper API.

    Expects audio in a format Whisper can handle (WAV, MP3, etc.).
    Returns the transcribed text or empty string on error.
    """
    if not OPENAI_API_KEY:
        return ""

    try:
        with open(audio_path, 'rb') as audio_file:
            resp = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
            )
        text = resp.get('text', '').strip()
        return text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return ""


def generate_ai_reply(caller_text: str) -> str:
    """Generate a receptionist reply to the caller's input.

    Returns the reply text (to be converted to TTS).
    """
    if not OPENAI_API_KEY:
        return "I'm sorry, I didn't understand. Please try again."

    try:
        prompt = f"""You are a professional phone receptionist. The caller just said:

"{caller_text}"

Respond with a short, natural, and helpful message. Keep it to one or two sentences.
Do not be verbose. Be concise and professional."""

        resp = openai.ChatCompletion.create(
            model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.6,
        )
        reply = resp['choices'][0]['message']['content'].strip()
        return reply
    except Exception as e:
        print(f"Error generating AI reply: {e}")
        return "I'm sorry, something went wrong. Please try again."

