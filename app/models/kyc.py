from datetime import datetime
from app import db

class KYC(db.Model):
    __tablename__ = 'kyc_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    id_type = db.Column(db.String(50), nullable=False) # Passport, Driver License, etc.
    id_image = db.Column(db.String(255), nullable=False)
    selfie_image = db.Column(db.String(255), nullable=False)
    address_image = db.Column(db.String(255), nullable=False)
    
    # Status: pending, verified, rejected
    status = db.Column(db.String(20), default='pending')
    admin_note = db.Column(db.Text)
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('kyc_record', uselist=False, lazy=True))

    def __repr__(self):
        return f'<KYC {self.user_id} - {self.status}>'
