from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.investment import InvestmentPlan, UserInvestment
from app.models.finance import Currency, Deposit, Withdrawal
from app.models.notification import Notification
from app.services.notification_service import notify_withdrawal_received, notify_deposit_received
from app.forms.investment import InvestForm
from app.forms.finance import DepositForm, WithdrawalForm
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Fetch active investments
    active_invs = UserInvestment.query.filter_by(user_id=current_user.id, status='active').all()
    active_investments = sum(inv.amount for inv in active_invs)

    # Fetch pending withdrawals
    pending_withs = Withdrawal.query.filter_by(user_id=current_user.id, status='pending').all()
    pending_withdrawals = sum(w.amount for w in pending_withs)

    stats = {
        'total_deposits': current_user.total_deposited,
        'active_investments': active_investments,
        'total_profit': current_user.total_profit,
        'pending_withdrawals': pending_withdrawals,
        'total_withdrawn': current_user.total_withdrawn,
        'referral_earnings': current_user.referral_bonus,
        'account_balance': current_user.account_balance,
    }
    
    # Fetch recent transactions (deposits + withdrawals)
    deposits = Deposit.query.filter_by(user_id=current_user.id).order_by(Deposit.created_at.desc()).limit(5).all()
    withdrawals = Withdrawal.query.filter_by(user_id=current_user.id).order_by(Withdrawal.created_at.desc()).limit(5).all()
    
    txs = []
    for d in deposits:
        txs.append({
            'type': 'deposit',
            'amount': d.amount,
            'created_at': d.created_at,
            'status': d.status
        })
    for w in withdrawals:
        txs.append({
            'type': 'withdrawal',
            'amount': w.amount,
            'created_at': w.created_at,
            'status': w.status
        })
    
    # Sort by created_at desc and take top 5
    txs.sort(key=lambda x: x['created_at'], reverse=True)
    recent_transactions = txs[:5]
    
    return render_template('dashboard/index.html', title='Dashboard', stats=stats, transactions=recent_transactions)

@dashboard_bp.route('/invest', methods=['GET', 'POST'])
@login_required
def invest():
    plans = InvestmentPlan.query.filter_by(is_active=True).all()
    form = InvestForm()
    
    if request.method == 'POST':
        if form.validate_on_submit():
            plan = InvestmentPlan.query.get_or_404(form.plan_id.data)
            amount = form.amount.data
            
            # Validation
            if amount < plan.min_amount or amount > plan.max_amount:
                flash(f'Amount must be between ${plan.min_amount} and ${plan.max_amount}', 'danger')
                return redirect(url_for('dashboard.invest'))
                
            if current_user.account_balance < amount:
                flash('Insufficient account balance. Please deposit funds.', 'danger')
                return redirect(url_for('dashboard.invest'))
                
            # Process Investment
            current_user.account_balance -= amount
            investment = UserInvestment(
                user_id=current_user.id,
                plan_id=plan.id,
                amount=amount,
                end_date=datetime.utcnow() + timedelta(days=plan.duration_days)
            )
            db.session.add(investment)
            db.session.commit()
            
            flash(f'Successfully invested ${amount} in {plan.name}!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field.capitalize()}: {error}', 'danger')
            return redirect(url_for('dashboard.invest'))
            
    return render_template('dashboard/invest.html', title='Investment Plans', plans=plans, form=form)

@dashboard_bp.route('/my-investments')
@login_required
def my_investments():
    investments = UserInvestment.query.filter_by(user_id=current_user.id).order_by(UserInvestment.created_at.desc()).all()
    return render_template('dashboard/my_investments.html', title='My Investments', investments=investments)

@dashboard_bp.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    currencies = Currency.query.filter_by(is_active=True).all()
    form = DepositForm()
    form.currency_id.choices = [(c.id, f"{c.name} ({c.symbol})") for c in currencies]
    
    if form.validate_on_submit():
        file = form.proof_image.data
        filename = secure_filename(f"proof_{current_user.id}_{datetime.utcnow().timestamp()}.{file.filename.split('.')[-1]}")
        
        upload_path = os.path.join('app', 'static', 'uploads', 'deposits')
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
            
        file.save(os.path.join(upload_path, filename))
        
        deposit = Deposit(
            user_id=current_user.id,
            currency_id=form.currency_id.data,
            amount=form.amount.data,
            proof_image=filename
        )
        db.session.add(deposit)
        db.session.commit()
        
        notify_deposit_received(current_user, deposit)
        
        flash('Deposit submitted successfully! Our team will verify it soon.', 'success')
        return redirect(url_for('dashboard.history'))
        
    return render_template('dashboard/deposit.html', title='Fund Wallet', currencies=currencies, form=form)

@dashboard_bp.route('/history')
@login_required
def history():
    deposits = Deposit.query.filter_by(user_id=current_user.id).order_by(Deposit.created_at.desc()).all()
    withdrawals = Withdrawal.query.filter_by(user_id=current_user.id).order_by(Withdrawal.created_at.desc()).all()
    return render_template('dashboard/history.html', title='Transaction History', deposits=deposits, withdrawals=withdrawals)

@dashboard_bp.route('/referrals')
@login_required
def referrals():
    return render_template('dashboard/referrals.html', title='Referral Program')

@dashboard_bp.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    currencies = Currency.query.filter_by(is_active=True).all()
    form = WithdrawalForm()
    form.currency_id.choices = [(c.id, f"{c.name} ({c.symbol})") for c in currencies]
    
    if form.validate_on_submit():
        # PIN Verification
        if not current_user.check_withdrawal_pin(form.pin.data):
            flash('Invalid Transaction PIN.', 'danger')
            return redirect(url_for('dashboard.withdraw'))
            
        amount = form.amount.data
        if current_user.account_balance < amount:
            flash('Insufficient balance for withdrawal.', 'danger')
            return redirect(url_for('dashboard.withdraw'))
            
        # Deduct balance immediately or hold? Usually hold.
        current_user.account_balance -= amount
        
        withdrawal = Withdrawal(
            user_id=current_user.id,
            currency_id=form.currency_id.data,
            amount=amount,
            network=form.network.data,
            wallet_address=form.wallet_address.data
        )
        db.session.add(withdrawal)
        db.session.commit()
        
        notify_withdrawal_received(current_user, withdrawal)
        
        flash('Withdrawal request submitted successfully!', 'success')
        return redirect(url_for('dashboard.history'))
        
    return render_template('dashboard/withdraw.html', title='Transfer Funds', currencies=currencies, form=form)

@dashboard_bp.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('dashboard/notifications.html', title='Notifications', notifications=notifications)

@dashboard_bp.route('/notifications/read-all')
@login_required
def mark_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({Notification.is_read: True})
    db.session.commit()
    return redirect(url_for('dashboard.notifications'))
