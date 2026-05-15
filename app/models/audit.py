"""
Audit logging service — records all sensitive admin actions.
"""
from app import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action      = db.Column(db.String(100), nullable=False)
    target      = db.Column(db.String(255))          # e.g. "user:42", "deposit:7"
    ip_address  = db.Column(db.String(45))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))

    def __repr__(self):
        return f'<AuditLog {self.action} by user {self.user_id}>'


def log_action(user_id, action, target=None, ip=None):
    """Helper to write an audit log entry."""
    entry = AuditLog(user_id=user_id, action=action, target=target, ip_address=ip)
    db.session.add(entry)
    # Don't commit here — caller controls the transaction
