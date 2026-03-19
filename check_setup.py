#!/usr/bin/env python3
"""
Helper script to check ffmpeg, test audio conversion, and validate setup.
"""
import os
import sys
import subprocess
import tempfile
from pathlib import Path

def check_ffmpeg():
    """Verify ffmpeg is installed."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✓ ffmpeg is installed")
            return True
    except FileNotFoundError:
        print("✗ ffmpeg not found. Install with:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  CentOS/RHEL: sudo yum install ffmpeg")
        return False

def check_asterisk_sounds_dir():
    """Verify ASTERISK_SOUNDS_DIR exists and is writable."""
    sounds_dir = os.environ.get('ASTERISK_SOUNDS_DIR', '/var/lib/asterisk/sounds/custom')
    if os.path.isdir(sounds_dir):
        if os.access(sounds_dir, os.W_OK):
            print(f"✓ {sounds_dir} exists and is writable")
            return True
        else:
            print(f"✗ {sounds_dir} exists but not writable. Fix with:")
            print(f"  sudo chown asterisk:asterisk {sounds_dir}")
            return False
    else:
        print(f"✗ {sounds_dir} does not exist. Create with:")
        print(f"  sudo mkdir -p {sounds_dir}")
        print(f"  sudo chown asterisk:asterisk {sounds_dir}")
        return False

def test_mp3_to_wav_conversion():
    """Test MP3 to WAV conversion pipeline."""
    try:
        from gtts import gTTS
    except ImportError:
        print("✗ gTTS not installed. Install with: pip install gTTS")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        mp3_path = os.path.join(tmpdir, 'test.mp3')
        wav_path = os.path.join(tmpdir, 'test.wav')

        # Generate MP3
        try:
            tts = gTTS(text="Testing audio conversion", lang='en')
            tts.save(mp3_path)
            print(f"✓ Generated test MP3: {mp3_path}")
        except Exception as e:
            print(f"✗ Failed to generate MP3: {e}")
            return False

        # Convert to WAV
        try:
            cmd = [
                'ffmpeg', '-i', mp3_path,
                '-ar', '8000',
                '-ac', '1',
                '-codec:a', 'pcm_mulaw',
                '-y', wav_path
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0 and os.path.exists(wav_path):
                file_size = os.path.getsize(wav_path)
                print(f"✓ Converted MP3 to Asterisk-compatible WAV: {wav_path} ({file_size} bytes)")
                return True
            else:
                print(f"✗ ffmpeg conversion failed: {result.stderr.decode()}")
                return False
        except Exception as e:
            print(f"✗ Error running ffmpeg: {e}")
            return False

def check_env_vars():
    """Check required environment variables."""
    required = ['ARI_URL', 'ARI_USER', 'ARI_PASS', 'ASTERISK_SOUNDS_DIR']
    optional = ['OPENAI_API_KEY', 'OPENAI_MODEL', 'PJSIP_TRUNK_NAME']

    print("\nEnvironment variables:")
    all_ok = True
    for var in required:
        val = os.environ.get(var)
        if val:
            print(f"  ✓ {var}={val[:50]}...")
        else:
            print(f"  ✗ {var} (required, not set)")
            all_ok = False

    for var in optional:
        val = os.environ.get(var)
        if val:
            print(f"  ✓ {var}={val[:50]}...")
        else:
            print(f"  ○ {var} (optional, not set)")

    return all_ok

def main():
    print("=== Asterisk + Flask AI Receptionist Setup Check ===\n")

    checks = [
        ("ffmpeg", check_ffmpeg),
        ("Asterisk sounds dir", check_asterisk_sounds_dir),
        ("Audio conversion", test_mp3_to_wav_conversion),
        ("Environment variables", check_env_vars),
    ]

    results = {}
    for name, check_fn in checks:
        print(f"\nChecking {name}...")
        try:
            results[name] = check_fn()
        except Exception as e:
            print(f"✗ Error: {e}")
            results[name] = False

    print("\n=== Summary ===")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"{passed}/{total} checks passed")

    if passed == total:
        print("\n✓ All checks passed! Ready to run Flask app.")
        sys.exit(0)
    else:
        print("\n✗ Some checks failed. See above for details.")
        sys.exit(1)

if __name__ == '__main__':
    main()
