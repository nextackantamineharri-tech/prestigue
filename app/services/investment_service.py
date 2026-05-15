from datetime import datetime
from decimal import Decimal

def process_daily_profits():
    """
    Background task to process daily profits for all active investments.
    Runs daily.
    """
    from app import db
    from app.models.investment import UserInvestment, ProfitLog
    
    active_investments = UserInvestment.query.filter_by(status='active').all()
    
    for inv in active_investments:
        plan = inv.plan
        now = datetime.utcnow()
        
        # Check if investment has matured
        if now >= inv.end_date:
            finalize_investment(inv)
            continue
            
        # Process Daily Profits
        if plan.profit_type == 'daily':
            # Calculate daily profit: (Total ROI % / Duration Days) * Amount
            daily_roi = Decimal(plan.roi_percentage) / Decimal(plan.duration_days)
            profit_amount = (daily_roi / Decimal(100)) * Decimal(inv.amount)
            
            # Update Investment and User Balance
            inv.total_profit_earned += profit_amount
            inv.user.account_balance += profit_amount
            inv.user.total_profit += profit_amount
            inv.last_profit_at = now
            
            # Log Profit
            log = ProfitLog(
                investment_id=inv.id,
                user_id=inv.user_id,
                amount=profit_amount
            )
            db.session.add(log)
            
    db.session.commit()

def finalize_investment(inv):
    """
    Handle matured investments: return capital if applicable and mark as completed.
    """
    from app import db
    from app.models.investment import ProfitLog
    plan = inv.plan
    
    # If it was a fixed maturity plan, credit the full profit now
    if plan.profit_type == 'fixed':
        total_roi = Decimal(plan.roi_percentage)
        profit_amount = (total_roi / Decimal(100)) * Decimal(inv.amount)
        
        inv.total_profit_earned = profit_amount
        inv.user.account_balance += profit_amount
        inv.user.total_profit += profit_amount
        
        # Log Profit
        log = ProfitLog(
            investment_id=inv.id,
            user_id=inv.user_id,
            amount=profit_amount
        )
        db.session.add(log)
    
    # Return Capital if configured
    if plan.return_capital:
        inv.user.account_balance += Decimal(inv.amount)
        
    inv.status = 'completed'
    db.session.add(inv)
