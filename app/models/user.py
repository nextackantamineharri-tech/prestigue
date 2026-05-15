from datetime import datetime, timedelta
import random
import string
from app import db, login_manager, bcrypt
from flask_login import UserMixin
from app.models.investment import InvestmentPlan, UserInvestment, ProfitLog # Register models
from app.models.finance import Currency, Deposit, Withdrawal # Register models
from app.models.kyc import KYC # Register models
from app.models.notification import Notification # Register models

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Profile Info
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    country = db.Column(db.String(50))
    
    # Security & Status
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32)) # For OTP
    withdrawal_pin_hash = db.Column(db.String(128))
    
    # Financial summary (placeholders for dashboard phase)
    account_balance = db.Column(db.Numeric(20, 8), default=0.0)
    total_deposited = db.Column(db.Numeric(20, 8), default=0.0)
    total_withdrawn = db.Column(db.Numeric(20, 8), default=0.0)
    total_profit = db.Column(db.Numeric(20, 8), default=0.0)
    
    # Referral system
    referral_code = db.Column(db.String(10), unique=True)
    referred_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    referral_bonus = db.Column(db.Numeric(20, 8), default=0.0)
    
    # Relationships
    referred_users = db.relationship('User', backref=db.backref('referred_by', remote_side='User.id'), lazy=True, foreign_keys='User.referred_by_id')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def set_withdrawal_pin(self, pin):
        self.withdrawal_pin_hash = bcrypt.generate_password_hash(pin).decode('utf-8')

    def check_withdrawal_pin(self, pin):
        if not self.withdrawal_pin_hash:
            return False
        return bcrypt.check_password_hash(self.withdrawal_pin_hash, pin)

    @staticmethod
    def generate_referral_code():
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not User.query.filter_by(referral_code=code).first():
                return code

    def __repr__(self):
        return f'<User {self.email}>'

class OTP(db.Model):
    __tablename__ = 'otps'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), default='login') # login, reset_password, verification
    is_used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_code(length=6):
        return ''.join(random.choices(string.digits, k=length))

    def is_expired(self):
        return datetime.utcnow() > self.expires_at

class LoginHistory(db.Model):
    __tablename__ = 'login_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    status = db.Column(db.String(20)) # success, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Site Info
    site_name = db.Column(db.String(100), default='Prestige Finance Global')
    site_email = db.Column(db.String(100), default='support@prestigefinance.com')
    site_phone = db.Column(db.String(20), default='+1 (000) 000-0000')
    site_address = db.Column(db.Text)
    
    # Branding
    primary_color = db.Column(db.String(7), default='#1a237e') # Default deep blue
    secondary_color = db.Column(db.String(7), default='#0d47a1')
    accent_color = db.Column(db.String(7), default='#ffd600')
    logo_url = db.Column(db.String(255))
    favicon_url = db.Column(db.String(255))
    
    # SEO
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)
    
    # Social
    facebook_url = db.Column(db.String(255))
    twitter_url = db.Column(db.String(255))
    instagram_url = db.Column(db.String(255))
    telegram_url = db.Column(db.String(255))

    @staticmethod
    def get_settings():
        settings = SystemSettings.query.first()
        if not settings:
            settings = SystemSettings()
            db.session.add(settings)
            db.session.commit()
        return settings

    def __repr__(self):
        return f'<SystemSettings {self.site_name}>'
