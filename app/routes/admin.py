from flask import Blueprint, render_template, abort, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import SystemSettings, User
from app.models.investment import InvestmentPlan, UserInvestment, ProfitLog
from app.models.finance import Currency, Deposit, Withdrawal
from app.models.kyc import KYC
from app.forms.kyc import KYCReviewForm
from app.forms.admin import SystemSettingsForm, InvestmentPlanForm, CurrencyForm, DepositProcessForm, WithdrawalProcessForm
from app.services.notification_service import (
    notify_deposit_approved, notify_deposit_rejected,
    notify_withdrawal_approved, notify_withdrawal_rejected,
    notify_kyc_approved, notify_kyc_rejected
)
from datetime import datetime, timedelta
from sqlalchemy import func
from decimal import Decimal
import os
from werkzeug.utils import secure_filename
from flask import current_app

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def restrict_to_admin():
    if not current_user.is_admin:
        abort(403)

@admin_bp.route('/dashboard')
def dashboard():
    total_users          = User.query.filter_by(is_admin=False).count()
    verified_users       = User.query.filter_by(is_verified=True, is_admin=False).count()
    active_investments   = UserInvestment.query.filter_by(status='active').count()
    pending_deposits     = Deposit.query.filter_by(status='pending').count()
    pending_withdrawals  = Withdrawal.query.filter_by(status='pending').count()
    pending_kyc          = KYC.query.filter_by(status='pending').count()
    total_deposits       = db.session.query(func.sum(Deposit.amount)).filter_by(status='approved').scalar() or 0
    total_withdrawals    = db.session.query(func.sum(Withdrawal.amount)).filter_by(status='paid').scalar() or 0
    total_profit         = db.session.query(func.sum(ProfitLog.amount)).scalar() or 0
    recent_deposits      = Deposit.query.order_by(Deposit.created_at.desc()).limit(5).all()
    recent_withdrawals   = Withdrawal.query.order_by(Withdrawal.created_at.desc()).limit(5).all()
    recent_users         = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
        total_users=total_users, verified_users=verified_users,
        active_investments=active_investments,
        pending_deposits=pending_deposits, pending_withdrawals=pending_withdrawals, pending_kyc=pending_kyc,
        total_deposits=total_deposits, total_withdrawals=total_withdrawals, total_profit=total_profit,
        recent_deposits=recent_deposits, recent_withdrawals=recent_withdrawals, recent_users=recent_users
    )

# User Management
@admin_bp.route('/users')
def users():
    search = request.args.get('q', '')
    query = User.query.filter_by(is_admin=False)
    if search:
        query = query.filter(
            (User.email.ilike(f'%{search}%')) |
            (User.username.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%'))
        )
    all_users = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users/index.html', title='Manage Users', users=all_users, search=search)

@admin_bp.route('/users/<int:id>')
def view_user(id):
    user        = User.query.get_or_404(id)
    investments = UserInvestment.query.filter_by(user_id=id).all()
    deposits    = Deposit.query.filter_by(user_id=id).all()
    withdrawals = Withdrawal.query.filter_by(user_id=id).all()
    return render_template('admin/users/view.html', title='User Detail',
                           user=user, investments=investments,
                           deposits=deposits, withdrawals=withdrawals)

@admin_bp.route('/users/<int:id>/suspend', methods=['POST'])
def suspend_user(id):
    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    action = 'reactivated' if user.is_active else 'suspended'
    flash(f'User {user.email} has been {action}.', 'success')
    return redirect(url_for('admin.view_user', id=id))

@admin_bp.route('/users/<int:id>/adjust-balance', methods=['POST'])
def adjust_balance(id):
    user = User.query.get_or_404(id)
    try:
        amount = Decimal(request.form.get('amount', '0'))
        action = request.form.get('action', 'add')
        if action == 'add':
            user.account_balance += amount
            flash(f'Added ${amount} to {user.email}\'s balance.', 'success')
        elif action == 'deduct':
            if user.account_balance < amount:
                flash('Insufficient balance to deduct.', 'danger')
                return redirect(url_for('admin.view_user', id=id))
            user.account_balance -= amount
            flash(f'Deducted ${amount} from {user.email}\'s balance.', 'warning')
        db.session.commit()
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('admin.view_user', id=id))

# Analytics JSON endpoints for Chart.js
@admin_bp.route('/analytics/deposits-chart')
def deposits_chart_data():
    data, labels = [], []
    for i in range(6, -1, -1):
        day = (datetime.utcnow() - timedelta(days=i)).date()
        total = db.session.query(func.sum(Deposit.amount)).filter(
            func.date(Deposit.created_at) == day, Deposit.status == 'approved'
        ).scalar() or 0
        data.append(float(total))
        labels.append(day.strftime('%b %d'))
    return jsonify({'labels': labels, 'data': data})

@admin_bp.route('/analytics/users-chart')
def users_chart_data():
    data, labels = [], []
    for i in range(6, -1, -1):
        day = (datetime.utcnow() - timedelta(days=i)).date()
        count = User.query.filter(func.date(User.created_at) == day).count()
        data.append(count)
        labels.append(day.strftime('%b %d'))
    return jsonify({'labels': labels, 'data': data})

@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    settings = SystemSettings.get_settings()
    form = SystemSettingsForm(obj=settings)
    
    if form.validate_on_submit():
        form.populate_obj(settings)
        db.session.commit()
        flash('System settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))
        
    return render_template('admin/settings.html', title='System Settings', form=form)

# Investment Plan Routes
@admin_bp.route('/plans')
def plans():
    plans = InvestmentPlan.query.all()
    return render_template('admin/plans/index.html', title='Investment Plans', plans=plans)

@admin_bp.route('/plans/add', methods=['GET', 'POST'])
def add_plan():
    form = InvestmentPlanForm()
    if form.validate_on_submit():
        plan = InvestmentPlan(
            name=form.name.data,
            min_amount=float(form.min_amount.data),
            max_amount=float(form.max_amount.data),
            roi_percentage=float(form.roi_percentage.data),
            duration_days=int(form.duration_days.data),
            profit_type=form.profit_type.data,
            payout_frequency=form.payout_frequency.data,
            return_capital=form.return_capital.data,
            is_active=form.is_active.data,
            is_featured=form.is_featured.data
        )
        db.session.add(plan)
        db.session.commit()
        flash('Investment plan added successfully!', 'success')
        return redirect(url_for('admin.plans'))
    return render_template('admin/plans/add_edit.html', title='Add Plan', form=form)

@admin_bp.route('/plans/edit/<int:id>', methods=['GET', 'POST'])
def edit_plan(id):
    plan = InvestmentPlan.query.get_or_404(id)
    form = InvestmentPlanForm(obj=plan)
    if form.validate_on_submit():
        form.populate_obj(plan)
        # Ensure numeric fields are correctly typed
        plan.min_amount = Decimal(form.min_amount.data)
        plan.max_amount = Decimal(form.max_amount.data)
        plan.roi_percentage = Decimal(form.roi_percentage.data)
        plan.duration_days = int(form.duration_days.data)
        db.session.commit()
        flash('Investment plan updated successfully!', 'success')
        return redirect(url_for('admin.plans'))
    return render_template('admin/plans/add_edit.html', title='Edit Plan', form=form, plan=plan)

# Currency Management
@admin_bp.route('/currencies')
def currencies():
    currencies = Currency.query.all()
    return render_template('admin/currencies/index.html', title='Crypto Currencies', currencies=currencies)

@admin_bp.route('/currencies/add', methods=['GET', 'POST'])
def add_currency():
    form = CurrencyForm()
    if form.validate_on_submit():
        logo_url = None
        if form.logo.data:
            filename = secure_filename(form.logo.data.filename)
            # Create directory if it doesn't exist
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'currencies')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # Save file
            file_path = os.path.join(upload_dir, filename)
            form.logo.data.save(file_path)
            logo_url = f'uploads/currencies/{filename}'

        currency = Currency(
            name=form.name.data,
            symbol=form.symbol.data,
            network=form.network.data,
            wallet_address=form.wallet_address.data,
            logo_url=logo_url,
            is_active=form.is_active.data
        )
        db.session.add(currency)
        db.session.commit()
        flash('Currency added successfully!', 'success')
        return redirect(url_for('admin.currencies'))
    return render_template('admin/currencies/add_edit.html', title='Add Currency', form=form)

@admin_bp.route('/currencies/edit/<int:id>', methods=['GET', 'POST'])
def edit_currency(id):
    currency = Currency.query.get_or_404(id)
    form = CurrencyForm(obj=currency)
    if form.validate_on_submit():
        if form.logo.data:
            filename = secure_filename(form.logo.data.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'currencies')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            file_path = os.path.join(upload_dir, filename)
            form.logo.data.save(file_path)
            currency.logo_url = f'uploads/currencies/{filename}'

        form.populate_obj(currency)
        db.session.commit()
        flash('Currency updated successfully!', 'success')
        return redirect(url_for('admin.currencies'))
    return render_template('admin/currencies/add_edit.html', title='Edit Currency', form=form, currency=currency)

# Deposit Management
@admin_bp.route('/deposits')
def deposits():
    deposits = Deposit.query.order_by(Deposit.created_at.desc()).all()
    return render_template('admin/deposits/index.html', title='Manage Deposits', deposits=deposits)

@admin_bp.route('/deposits/process/<int:id>', methods=['GET', 'POST'])
def process_deposit(id):
    deposit = Deposit.query.get_or_404(id)
    form = DepositProcessForm()
    
    if form.validate_on_submit():
        if 'submit_approve' in request.form:
            deposit.status = 'approved'
            deposit.user.account_balance += deposit.amount
            deposit.user.total_deposited += deposit.amount
            notify_deposit_approved(deposit.user, deposit)
            flash(f'Deposit of ${deposit.amount} approved and credited!', 'success')
        else:
            deposit.status = 'rejected'
            deposit.admin_note = form.admin_note.data
            notify_deposit_rejected(deposit.user, deposit)
            flash('Deposit rejected.', 'warning')
            
        deposit.processed_at = datetime.utcnow()
        db.session.commit()
        # TODO: Send email notification
        return redirect(url_for('admin.deposits'))
        
    return render_template('admin/deposits/process.html', title='Process Deposit', deposit=deposit, form=form)

# Withdrawal Management
@admin_bp.route('/withdrawals')
def withdrawals():
    withdrawals = Withdrawal.query.order_by(Withdrawal.created_at.desc()).all()
    return render_template('admin/withdrawals/index.html', title='Manage Withdrawals', withdrawals=withdrawals)

@admin_bp.route('/withdrawals/process/<int:id>', methods=['GET', 'POST'])
def process_withdrawal(id):
    withdrawal = Withdrawal.query.get_or_404(id)
    form = WithdrawalProcessForm()
    
    if form.validate_on_submit():
        if 'submit_approve' in request.form:
            withdrawal.status = 'approved'
            notify_withdrawal_approved(withdrawal.user, withdrawal)
            flash('Withdrawal request approved!', 'success')
        elif 'submit_paid' in request.form:
            withdrawal.status = 'paid'
            withdrawal.user.total_withdrawn += withdrawal.amount
            flash('Withdrawal marked as paid!', 'success')
        else:
            # Rejection returns funds to user
            withdrawal.status = 'rejected'
            withdrawal.admin_note = form.admin_note.data
            withdrawal.user.account_balance += withdrawal.amount
            notify_withdrawal_rejected(withdrawal.user, withdrawal)
            flash('Withdrawal rejected and funds returned to user.', 'warning')
            
        withdrawal.processed_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('admin.withdrawals'))
        
    return render_template('admin/withdrawals/process.html', title='Process Withdrawal', withdrawal=withdrawal, form=form)

# KYC Management
@admin_bp.route('/kyc')
def kyc_list():
    records = KYC.query.order_by(KYC.submitted_at.desc()).all()
    return render_template('admin/kyc/index.html', title='KYC Verification', records=records)

@admin_bp.route('/kyc/review/<int:id>', methods=['GET', 'POST'])
def review_kyc(id):
    kyc = KYC.query.get_or_404(id)
    form = KYCReviewForm()
    if form.validate_on_submit():
        if 'submit_approve' in request.form:
            kyc.status = 'verified'
            kyc.user.is_verified = True
            notify_kyc_approved(kyc.user)
            flash(f'KYC for {kyc.user.email} approved!', 'success')
        elif 'submit_reject' in request.form:
            kyc.status = 'rejected'
            kyc.admin_note = form.admin_note.data
            notify_kyc_rejected(kyc.user, kyc.admin_note)
            flash('KYC rejected.', 'warning')
        elif 'submit_reupload' in request.form:
            kyc.status = 'rejected'
            kyc.admin_note = form.admin_note.data or 'Please re-upload clearer documents.'
            notify_kyc_rejected(kyc.user, kyc.admin_note)
            flash('Re-upload requested.', 'info')
        kyc.processed_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('admin.kyc_list'))
    return render_template('admin/kyc/review.html', title='Review KYC', kyc=kyc, form=form)
