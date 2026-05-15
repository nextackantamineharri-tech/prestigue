from datetime import datetime
from app import db

class Currency(db.Model):
    __tablename__ = 'currencies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False) # Bitcoin, Ethereum, etc.
    symbol = db.Column(db.String(10), nullable=False) # BTC, ETH
    network = db.Column(db.String(50)) # e.g. ERC20, TRC20, BEP20
    wallet_address = db.Column(db.String(255), nullable=False)
    logo_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Currency {self.symbol}>'

class Deposit(db.Model):
    __tablename__ = 'deposits'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'), nullable=False)
    
    amount = db.Column(db.Numeric(20, 2), nullable=False)
    proof_image = db.Column(db.String(255), nullable=False) # Screenshot path
    
    # Status: pending, approved, rejected
    status = db.Column(db.String(20), default='pending')
    admin_note = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('deposits', lazy=True))
    currency = db.relationship('Currency')

    def __repr__(self):
        return f'<Deposit {self.id} - {self.status}>'

class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'), nullable=False)
    
    amount = db.Column(db.Numeric(20, 2), nullable=False)
    wallet_address = db.Column(db.String(255), nullable=False)
    network = db.Column(db.String(50))
    
    # Status: pending, approved, paid, rejected
    status = db.Column(db.String(20), default='pending')
    admin_note = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('withdrawals', lazy=True))
    currency = db.relationship('Currency')

    def __repr__(self):
        return f'<Withdrawal {self.id} - {self.status}>'
