from datetime import datetime, timedelta
from app import db

class InvestmentPlan(db.Model):
    __tablename__ = 'investment_plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    min_amount = db.Column(db.Numeric(20, 2), nullable=False)
    max_amount = db.Column(db.Numeric(20, 2), nullable=False)
    roi_percentage = db.Column(db.Numeric(5, 2), nullable=False) # e.g. 5.50
    duration_days = db.Column(db.Integer, nullable=False)
    
    # Types: 'daily' or 'fixed'
    profit_type = db.Column(db.String(20), default='daily') 
    # Frequency: 'daily', 'weekly', 'monthly', 'fixed'
    payout_frequency = db.Column(db.String(20), default='daily')
    
    return_capital = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<InvestmentPlan {self.name}>'

class UserInvestment(db.Model):
    __tablename__ = 'user_investments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('investment_plans.id'), nullable=False)
    
    amount = db.Column(db.Numeric(20, 2), nullable=False)
    total_profit_earned = db.Column(db.Numeric(20, 2), default=0.0)
    
    status = db.Column(db.String(20), default='active') # active, completed, cancelled
    
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    last_profit_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('investments', lazy=True))
    plan = db.relationship('InvestmentPlan')

    def is_matured(self):
        return datetime.utcnow() >= self.end_date

class ProfitLog(db.Model):
    __tablename__ = 'profit_logs'
    id = db.Column(db.Integer, primary_key=True)
    investment_id = db.Column(db.Integer, db.ForeignKey('user_investments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(20, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
