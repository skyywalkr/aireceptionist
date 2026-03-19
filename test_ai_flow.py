#!/usr/bin/env python3
"""
Integration test for the two-way AI receptionist flow.

This script tests the conversation pipeline without requiring a live Asterisk instance.
It validates: TTS generation → MP3/WAV conversion → (mock) recording → transcription → AI reply → playback.

Run:
  python test_ai_flow.py
"""
import os
import sys
import tempfile
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from ai_receptionist import (
    _generate_tts_wav,
    transcribe_caller_audio,
    generate_ai_reply,
)

def test_tts_generation():
    """Test greeting generation and WAV conversion."""
    print("\n[1/4] Testing TTS generation...")
    try:
        # Use a temporary directory
        old_sounds_dir = os.environ.get('ASTERISK_SOUNDS_DIR')
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['ASTERISK_SOUNDS_DIR'] = tmpdir

            sound_name = _generate_tts_wav("Hello, thank you for calling. How can I help?")
            if sound_name:
                # Extract the basename
                basename = sound_name.split('/')[-1]
                wav_file = Path(tmpdir) / f"{basename}.wav"
                if wav_file.exists():
                    size = wav_file.stat().st_size
                    print(f"  ✓ Generated WAV: {wav_file} ({size} bytes)")
                    return True
                else:
                    print(f"  ✗ WAV file not found: {wav_file}")
                    return False
            else:
                print("  ✗ TTS generation returned None")
                return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    finally:
        if old_sounds_dir:
            os.environ['ASTERISK_SOUNDS_DIR'] = old_sounds_dir

def test_transcription():
    """Test audio transcription with a mock WAV file."""
    print("\n[2/4] Testing transcription...")
    
    # Check if OPENAI_API_KEY is set
    if not os.environ.get('OPENAI_API_KEY'):
        print("  ⊘ Skipped (OPENAI_API_KEY not set)")
        return None

    try:
        from gtts import gTTS
    except ImportError:
        print("  ✗ gTTS not installed")
        return False

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate a test WAV
            test_text = "I would like to speak with someone about my account"
            mp3_path = os.path.join(tmpdir, 'test.mp3')
            wav_path = os.path.join(tmpdir, 'test.wav')

            # Generate MP3
            tts = gTTS(text=test_text, lang='en')
            tts.save(mp3_path)

            # Convert to WAV
            import subprocess
            cmd = [
                'ffmpeg', '-i', mp3_path,
                '-ar', '8000', '-ac', '1',
                '-codec:a', 'pcm_mulaw',
                '-y', wav_path
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode != 0:
                print(f"  ✗ ffmpeg conversion failed")
                return False

            # Transcribe
            text = transcribe_caller_audio(wav_path)
            if text:
                print(f"  ✓ Transcribed: '{text}'")
                return True
            else:
                print("  ✗ Transcription returned empty")
                return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_ai_reply():
    """Test AI reply generation."""
    print("\n[3/4] Testing AI reply generation...")

    if not os.environ.get('OPENAI_API_KEY'):
        print("  ⊘ Skipped (OPENAI_API_KEY not set)")
        return None

    try:
        caller_text = "I need to speak with someone about my account"
        reply = generate_ai_reply(caller_text)
        if reply:
            print(f"  ✓ Generated reply: '{reply}'")
            return True
        else:
            print("  ✗ Reply generation returned empty")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_full_conversation():
    """Test the full conversation flow."""
    print("\n[4/4] Testing full conversation flow...")

    if not os.environ.get('OPENAI_API_KEY'):
        print("  ⊘ Skipped (OPENAI_API_KEY not set)")
        return None

    try:
        old_sounds_dir = os.environ.get('ASTERISK_SOUNDS_DIR')
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['ASTERISK_SOUNDS_DIR'] = tmpdir

            # Generate greeting
            greeting = _generate_tts_wav("Hello, thank you for calling. How can I help?")
            if not greeting:
                print("  ✗ Greeting generation failed")
                return False

            # Mock caller input
            caller_text = "I need help with my billing"

            # Generate reply
            reply = generate_ai_reply(caller_text)
            if not reply:
                print("  ✗ Reply generation failed")
                return False

            # Generate reply audio
            reply_audio = _generate_tts_wav(reply)
            if not reply_audio:
                print("  ✗ Reply audio generation failed")
                return False

            print(f"  ✓ Conversation flow:")
            print(f"    Greeting: {greeting}")
            print(f"    Caller said: {caller_text}")
            print(f"    AI replied: {reply}")
            print(f"    Reply audio: {reply_audio}")
            return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    finally:
        if old_sounds_dir:
            os.environ['ASTERISK_SOUNDS_DIR'] = old_sounds_dir

def main():
    print("=== AI Receptionist Integration Tests ===")
    print(f"OPENAI_API_KEY: {'set' if os.environ.get('OPENAI_API_KEY') else 'NOT SET'}")

    tests = [
        ("TTS Generation", test_tts_generation),
        ("Transcription", test_transcription),
        ("AI Reply", test_ai_reply),
        ("Full Conversation", test_full_conversation),
    ]

    results = {}
    for name, test_fn in tests:
        try:
            result = test_fn()
            results[name] = result
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            results[name] = False

    print("\n=== Test Summary ===")
    passed = sum(1 for v in results.values() if v is True)
    skipped = sum(1 for v in results.values() if v is None)
    failed = sum(1 for v in results.values() if v is False)

    for name, result in results.items():
        status = "✓ PASS" if result is True else ("⊘ SKIP" if result is None else "✗ FAIL")
        print(f"  {status}: {name}")

    print(f"\nResults: {passed} passed, {skipped} skipped, {failed} failed")

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
