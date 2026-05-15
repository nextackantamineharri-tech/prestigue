"""
Security utilities — headers, upload validation, lockout helpers.
"""
import os
from functools import wraps
from flask import request, abort, current_app

# ── Allowed upload extensions ─────────────────────────────────────────────────
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_DOC_EXTENSIONS   = {'jpg', 'jpeg', 'png', 'pdf'}
MAX_UPLOAD_BYTES         = 8 * 1024 * 1024  # 8 MB

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_doc(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXTENSIONS

def validate_upload_size(file):
    """Return True if file is within size limit."""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size <= MAX_UPLOAD_BYTES

# ── Security headers ──────────────────────────────────────────────────────────
def apply_security_headers(response):
    """Attach security headers to every response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options']        = 'SAMEORIGIN'
    response.headers['X-XSS-Protection']       = '1; mode=block'
    response.headers['Referrer-Policy']         = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy']      = 'geolocation=(), microphone=(), camera=()'
    if not current_app.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# ── Login lockout helpers ─────────────────────────────────────────────────────
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES   = 15

def check_login_lockout(user):
    """
    Check recent failed logins. Returns (is_locked: bool, minutes_remaining: int).
    Requires LoginHistory to be imported by caller.
    """
    from app.models.user import LoginHistory
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(minutes=LOCKOUT_MINUTES)
    recent_failures = LoginHistory.query.filter(
        LoginHistory.user_id == user.id,
        LoginHistory.status == 'failed',
        LoginHistory.created_at >= cutoff
    ).count()
    if recent_failures >= MAX_FAILED_LOGINS:
        # Find oldest failure in window to calculate remaining time
        oldest = LoginHistory.query.filter(
            LoginHistory.user_id == user.id,
            LoginHistory.status == 'failed',
            LoginHistory.created_at >= cutoff
        ).order_by(LoginHistory.created_at.asc()).first()
        if oldest:
            unlock_at = oldest.created_at + timedelta(minutes=LOCKOUT_MINUTES)
            remaining = max(0, int((unlock_at - datetime.utcnow()).total_seconds() / 60))
            return True, remaining
    return False, 0
