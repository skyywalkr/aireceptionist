"""
Flask front-end to originate calls through ARI with two-way AI conversation.

Features:
- User authentication and onboarding
- Cyberpunk-themed landing page
- Originate outbound calls via ARI + PJSIP trunk
- Play initial greeting (AI-generated or static)
- Record caller's response
- Transcribe caller audio via Whisper
- Generate AI reply text
- Play AI reply back to caller
- All audio converted to Asterisk-compatible format (8kHz, mono, ulaw)
- Web UI with pricing, model selection, and ElevenLabs voice integration

Requires:
- Asterisk with ARI enabled
- ffmpeg installed (for audio conversion)
- OPENAI_API_KEY for AI features
- ELEVENLABS_API_KEY for premium TTS (optional)

Run:
  ARI_URL=http://127.0.0.1:8088 ARI_USER=asterisk ARI_PASS=secret \\
  ASTERISK_SOUNDS_DIR=/var/lib/asterisk/sounds/custom \\
  OPENAI_API_KEY=sk-... ELEVENLABS_API_KEY=... python app.py
"""

import os
import threading
import time
import json
import logging
import re
from functools import wraps
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

# ARI (Asterisk REST Interface) - only available on Linux with Asterisk installed
# On macOS/dev machines, this will gracefully fall back
try:
    import ari
    HAS_ARI = True
except ImportError:
    HAS_ARI = False
    logging.warning('⚠️  ARI not available - Asterisk integration disabled. Install on Linux with Asterisk.')

import openai
from ai_receptionist import (
    generate_receptionist_greeting,
    transcribe_caller_audio,
    generate_ai_reply,
    _generate_tts_wav,
)
from pricing import estimate_call_cost
from elevenlabs_tts import get_available_voices, synthesize_text_elevenlabs
from models import db, User, CallLog

# ===== OPTIONAL MODULE NOTES =====
# OpenAI & ElevenLabs are OPTIONAL and gracefully degrade if keys are missing:
#   - OPENAI_API_KEY: If missing, uses static greetings and basic transcription fallback
#   - ELEVENLABS_API_KEY: If missing, falls back to gTTS for TTS
# The server will start and function even without these keys.
# Features will simply degrade gracefully.

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Security configuration
app.config['SESSION_COOKIE_SECURE'] = not app.debug
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Database configuration - with fallback to SQLite if DATABASE_URL is invalid
database_url = os.environ.get('DATABASE_URL', 'sqlite:////var/lib/nexus/receptionist.db')
try:
    # Validate that the URL is parseable by SQLAlchemy
    from sqlalchemy import engine
    engine.url.make_url(database_url)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
except Exception as e:
    app.logger.warning(f'⚠️  Invalid DATABASE_URL "{database_url}", falling back to SQLite: {e}')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/lib/nexus/receptionist.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
if app.config['SECRET_KEY'] == 'dev-secret-change-in-production':
    app.logger.warning('⚠️  Using default SECRET_KEY - SET SECRET_KEY env var in production!')

# Initialize database
db.init_app(app)

# Initialize security
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=['200 per day', '50 per hour'])
Talisman(app, force_https=not app.debug, strict_transport_security=True, strict_transport_security_max_age=31536000)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'landing'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

ARI_URL = os.environ.get('ARI_URL', 'http://127.0.0.1:8088')
ARI_USER = os.environ.get('ARI_USER', 'asterisk')
ARI_PASS = os.environ.get('ARI_PASS', 'secret')
ARI_APP = os.environ.get('ARI_APP_NAME', 'ai_receptionist')
PJSIP_TRUNK = os.environ.get('PJSIP_TRUNK_NAME', 'trunk')
ASTERISK_SOUNDS_DIR = os.environ.get('ASTERISK_SOUNDS_DIR', '/var/lib/asterisk/sounds/custom')

# Connect to ARI (only on systems with Asterisk installed)
client = None
if HAS_ARI:
    try:
        client = ari.connect(ARI_URL, ARI_USER, ARI_PASS)
        app.logger.info(f"✅ ARI Connected to {ARI_URL}")
    except Exception as e:
        app.logger.error(f"❌ ARI Connection failed: {e}")
else:
    app.logger.warning('⚠️  ARI not available - Asterisk integration disabled')

# Track active channels and their state
channel_state = {}


def stasis_start(event, channel_obj):
    """Handle a channel entering Stasis.

    If greeting_file is provided, play it.
    Then record the caller's response and trigger the AI conversation.
    """
    try:
        channel = channel_obj.get('channel', channel_obj)
        chan_id = channel.id
        app.logger.info('StasisStart for channel %s', chan_id)

        # Initialize channel state
        channel_state[chan_id] = {
            'status': 'started',
            'greeting_file': None,
            'recording_file': None,
        }

        # Get greeting filename from channel variables (if provided)
        try:
            var_val = channel.getChannelVars().get('greeting_file')
            if var_val:
                channel_state[chan_id]['greeting_file'] = var_val
        except:
            pass

        # Play greeting if provided
        greeting = channel_state[chan_id]['greeting_file']
        if greeting:
            app.logger.info('Playing greeting %s to %s', greeting, chan_id)
            try:
                pb = client.playbacks.play(channel=chan_id, media='sound:{0}'.format(greeting))
                # Wait for playback to finish (blocking)
                while pb.state == 'playing':
                    time.sleep(0.1)
            except Exception as e:
                app.logger.error('Error playing greeting: %s', e)

        # Now record the caller's input
        app.logger.info('Recording for channel %s', chan_id)
        channel_state[chan_id]['status'] = 'recording'

        # Start recording (silence_threshold, max duration, etc.)
        recording_name = f"rec_{chan_id.replace('-', '_')}"
        try:
            recording = client.recordings.record(
                name=recording_name,
                format='wav',
                maxDurationSeconds=30,
                ifExists='overwrite',
                beep=True,
            )
            # Record the channel into this recording (subscribe to it)
            channel.record(name=recording_name, format='wav', maxDurationSeconds=30, beep=True)
            channel_state[chan_id]['recording_file'] = recording_name

            app.logger.info('Recording started: %s', recording_name)

            # Wait for recording to complete (we'll use a timeout or silence detection)
            time.sleep(15)  # Record for up to 15 seconds

            # Stop recording
            channel.stopRecording()
            channel_state[chan_id]['status'] = 'recorded'
            app.logger.info('Recording completed: %s', recording_name)

            # Transcribe the recording
            recording_path = os.path.join(ASTERISK_SOUNDS_DIR, f"{recording_name}.wav")
            caller_text = transcribe_caller_audio(recording_path)
            app.logger.info('Transcribed: %s', caller_text)

            if caller_text:
                # Generate AI reply
                reply_text = generate_ai_reply(caller_text)
                app.logger.info('AI reply: %s', reply_text)

                # Generate TTS for reply
                reply_sound = _generate_tts_wav(reply_text)
                if reply_sound:
                    app.logger.info('Playing AI reply: %s', reply_sound)
                    try:
                        client.playbacks.play(channel=chan_id, media='sound:{0}'.format(reply_sound))
                    except Exception as e:
                        app.logger.error('Error playing reply: %s', e)

            # Hang up
            channel_state[chan_id]['status'] = 'completed'
            channel.hangup()

        except Exception as e:
            app.logger.exception('Error during recording/AI flow: %s', e)
            channel.hangup()

    except Exception as e:
        app.logger.exception('Error in stasis_start: %s', e)


# Register ARI event handler (only if ARI is available)
if HAS_ARI and client:
    client.on_event('StasisStart', stasis_start)


def run_ari_loop():
    """Run ARI event loop (blocking)."""
    if not HAS_ARI or not client:
        app.logger.warning('⚠️  Skipping ARI event loop - ARI not available')
        return
    app.logger.info('Starting ARI event loop')
    try:
        client.run(apps=[ARI_APP])
    except Exception as e:
        app.logger.error('ARI event loop error: %s', e)


ari_thread = None
if HAS_ARI and client:
    ari_thread = threading.Thread(target=run_ari_loop, daemon=True)
    ari_thread.start()


@app.route('/call', methods=['POST'])
@login_required
@limiter.limit('10 per hour')
def originate_call():
    """Originate an outbound call.

    JSON body: {
        "to": "+15551234567",
        "use_ai": true,
        "llm_model": "gpt-4o-mini",
        "tts_provider": "gtts",
        "elevenlabs_voice": "21m00Tcm4TlvDq8ikWAM"
    }

    If use_ai is true, an AI greeting will be generated and played.
    The caller's response will be recorded, transcribed, and the AI will reply.
    """
    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    to = body.get('to', '').strip()
    use_ai = body.get('use_ai', False)
    llm_model = body.get('llm_model', 'gpt-4o-mini')
    tts_provider = body.get('tts_provider', 'gtts')
    elevenlabs_voice = body.get('elevenlabs_voice', '21m00Tcm4TlvDq8ikWAM')

    if not to:
        return jsonify({'error': 'missing "to"'}), 400
    
    # Validate phone number (E.164 format or basic format)
    if not re.match(r'^\+?[1-9]\d{1,14}$', to.replace('-', '').replace(' ', '')):
        return jsonify({'error': 'invalid phone number format'}), 400

    # Log the call
    call_log = CallLog(
        user_id=current_user.id,
        phone_number=to,
        llm_model=llm_model,
        tts_provider=tts_provider,
        elevenlabs_voice=elevenlabs_voice,
        status='pending',
    )

    greeting_file_var = None
    if use_ai and os.environ.get('ENABLE_AI', 'false').lower() in ('1', 'true', 'yes'):
        app.logger.info('Generating AI greeting with %s/%s', llm_model, tts_provider)

        # Check if OpenAI API key is available
        if not os.environ.get('OPENAI_API_KEY'):
            app.logger.warning('OpenAI API key not set - using static greeting')
            greeting_text = "Hello, thank you for calling. How can I help?"
        else:
            # Generate greeting text via AI
            prompt = "You are a professional phone receptionist. Produce a short (one-sentence) friendly greeting when answering an incoming call. Introduce the company and ask how you can help. Keep it brief and natural."
            try:
                resp = openai.ChatCompletion.create(
                    model=llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=80,
                    temperature=0.6,
                )
                greeting_text = resp['choices'][0]['message']['content'].strip()
            except Exception as e:
                app.logger.error('Error generating greeting: %s', e)
                greeting_text = "Hello, thank you for calling. How can I help?"

        # Generate speech
        if tts_provider == 'elevenlabs':
            if not os.environ.get('ELEVENLABS_API_KEY'):
                app.logger.warning('ElevenLabs API key not set - falling back to gTTS')
                greeting_file_var = _generate_tts_wav(greeting_text)
            else:
                app.logger.info('Using ElevenLabs for TTS')
                greeting_file_var = synthesize_text_elevenlabs(greeting_text, elevenlabs_voice)
                if not greeting_file_var:
                    app.logger.warning('ElevenLabs TTS failed - falling back to gTTS')
                    greeting_file_var = _generate_tts_wav(greeting_text)
        else:
            # Default to gTTS
            app.logger.info('Using gTTS for TTS')
            greeting_file_var = _generate_tts_wav(greeting_text)

        if greeting_file_var:
            app.logger.info('Generated greeting: %s', greeting_file_var)
        else:
            app.logger.warning('Failed to generate greeting, continuing without')

    # Originate call
    if not HAS_ARI or not client:
        return jsonify({'error': 'Asterisk/ARI not available. Install on Linux with Asterisk.'}), 503
    
    endpoint = f"PJSIP/{to}@{PJSIP_TRUNK}"
    variables = {
        'greeting_file': greeting_file_var or '',
        'llm_model': llm_model,
        'tts_provider': tts_provider,
        'elevenlabs_voice': elevenlabs_voice,
        'call_log_id': str(call_log.id),
    }

    try:
        r = client.channels.create(
            endpoint=endpoint,
            app=ARI_APP,
            appArgs='',
            variables=json.dumps(variables) if variables else None,
        )
        call_log.asterisk_channel = getattr(r, 'id', None)
        call_log.status = 'connected'
        db.session.add(call_log)
        db.session.commit()

        return jsonify({
            'status': 'originated',
            'endpoint': endpoint,
            'channel': getattr(r, 'id', None),
            'use_ai': use_ai,
            'config': {
                'llm_model': llm_model,
                'tts_provider': tts_provider,
            },
        })
    except Exception as e:
        app.logger.exception('Error originating call')
        call_log.status = 'failed'
        db.session.add(call_log)
        db.session.commit()
        return jsonify({'error': str(e)}), 500


@app.route('/channels', methods=['GET'])
def list_channels():
    """List active channels and their state."""
    return jsonify({'channels': channel_state})


@app.route('/', methods=['GET'])
def landing():
    """Serve the cyberpunk landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')


@app.route('/auth/signup', methods=['POST'])
@limiter.limit('5 per hour')
def signup():
    """Register a new user."""
    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    email = body.get('email', '').strip().lower()
    password = body.get('password', '')
    company_name = body.get('company_name', '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Validate email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password strength (minimum 8 chars)
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    # Create new user
    user = User(email=email, company_name=company_name or email)
    user.set_password(password)
    user.generate_api_key()

    try:
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return jsonify({'status': 'success', 'message': 'Account created'})
    except Exception as e:
        db.session.rollback()
        app.logger.exception('Error creating user')
        return jsonify({'error': 'Registration failed'}), 500


@app.route('/auth/login', methods=['POST'])
@limiter.limit('5 per hour')
def login():
    """Login a user."""
    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    email = body.get('email', '').strip().lower()
    password = body.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        # Generic error to prevent email enumeration
        return jsonify({'error': 'Invalid email or password'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403

    login_user(user)
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Logged in'})


@app.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """Logout a user."""
    logout_user()
    return jsonify({'status': 'success'})


@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Serve the user dashboard."""
    return render_template('dashboard.html')


@app.route('/', methods=['GET'])
def index():
    """Serve the web UI."""
    return render_template('index.html')


@app.route('/api/estimate-cost', methods=['POST'])
@limiter.limit('20 per hour')
def estimate_cost():
    """Estimate the cost of a call with given configuration."""
    body = request.get_json(force=True)
    llm_model = body.get('llm_model', 'gpt-4o-mini')
    tts_provider = body.get('tts_provider', 'gtts')
    duration = body.get('estimated_duration_seconds', 30)

    try:
        pricing = estimate_call_cost(llm_model, tts_provider, duration)
        return jsonify(pricing)
    except Exception as e:
        app.logger.exception('Error estimating cost')
        return jsonify({'error': str(e)}), 500


@app.route('/api/elevenlabs-voices', methods=['GET'])
def elevenlabs_voices():
    """Get available ElevenLabs voices."""
    try:
        voices = get_available_voices()
        return jsonify({'voices': voices})
    except Exception as e:
        app.logger.exception('Error fetching voices')
        return jsonify({'error': str(e), 'voices': []}), 200


@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    """Get current user info (API key masked for security)."""
    api_key = current_user.api_key
    # Mask API key: show only first 6 and last 4 chars
    masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
    
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'company': current_user.company_name,
        'api_key_masked': masked_key,  # Never expose full key
        'total_calls': current_user.total_calls,
        'total_cost': float(current_user.total_cost),
        'preferences': {
            'llm_model': current_user.llm_model,
            'tts_provider': current_user.tts_provider,
            'elevenlabs_voice': current_user.elevenlabs_voice,
        },
    })


@app.route('/api/call-history', methods=['GET'])
@login_required
def call_history():
    """Get user's call history."""
    limit = request.args.get('limit', 50, type=int)
    calls = CallLog.query.filter_by(user_id=current_user.id).order_by(CallLog.created_at.desc()).limit(limit).all()
    return jsonify({
        'calls': [
            {
                'id': c.id,
                'phone': c.phone_number,
                'model': c.llm_model,
                'provider': c.tts_provider,
                'status': c.status,
                'cost': c.cost,
                'duration': c.duration_seconds,
                'created': c.created_at.isoformat(),
            }
            for c in calls
        ]
    })


if __name__ == '__main__':
    is_prod = os.environ.get('FLASK_ENV') == 'production'
    app.run(host='127.0.0.1' if is_prod else '0.0.0.0', port=5000, debug=not is_prod)

