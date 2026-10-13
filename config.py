import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    uri = os.environ.get('DATABASE_URL')
    if uri:
        if uri.startswith('postgres://'):
            uri = uri.replace('postgres://', 'postgresql://', 1)
        # Force the psycopg2 driver explicitly — SQLAlchemy's default dialect
        # for a bare "postgresql://" URL is version-dependent, and only
        # psycopg2-binary is installed (see requirements.txt).
        if uri.startswith('postgresql://'):
            uri = uri.replace('postgresql://', 'postgresql+psycopg2://', 1)
    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings (Brevo HTTP API — bypasses Railway SMTP port blocks)
    BREVO_API_KEY = os.environ.get('BREVO_API_KEY')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@prestigefinanceglobal.net')

    # App Branding
    APP_NAME = os.environ.get('APP_NAME', 'Prestige Finance Global')
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')

    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600 # 1 hour
