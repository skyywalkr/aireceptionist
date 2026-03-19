"""
User authentication and database models.
"""
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User account model."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(255), nullable=True)
    api_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    # Preferences
    llm_model = db.Column(db.String(50), default='gpt-4o-mini')
    tts_provider = db.Column(db.String(50), default='gtts')
    elevenlabs_voice = db.Column(db.String(50), default='21m00Tcm4TlvDq8ikWAM')
    
    # Account status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Billing
    total_calls = db.Column(db.Integer, default=0)
    total_cost = db.Column(db.Float, default=0.0)
    
    calls = db.relationship('CallLog', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password: str):
        """Hash and set password."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def generate_api_key(self) -> str:
        """Generate a unique API key for this user."""
        import secrets
        self.api_key = secrets.token_urlsafe(48)
        return self.api_key


class CallLog(db.Model):
    """Log of all calls made."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    phone_number = db.Column(db.String(20), nullable=False)
    llm_model = db.Column(db.String(50), nullable=False)
    tts_provider = db.Column(db.String(50), nullable=False)
    elevenlabs_voice = db.Column(db.String(50), nullable=True)
    
    status = db.Column(db.String(20), default='pending')  # pending, connected, completed, failed
    duration_seconds = db.Column(db.Integer, default=0)
    cost = db.Column(db.Float, default=0.0)
    
    asterisk_channel = db.Column(db.String(100), nullable=True)
    transcription = db.Column(db.Text, nullable=True)
    ai_reply = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<CallLog {self.id} to {self.phone_number}>'
