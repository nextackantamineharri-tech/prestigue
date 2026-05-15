from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt, limiter
from app.models.user import User, OTP, LoginHistory
from app.forms.auth import RegistrationForm, LoginForm, OTPForm, ForgotPasswordForm, ResetPasswordForm, WithdrawalPinForm, ChangePasswordForm
from app.services.notification_service import notify_registration, notify_otp
from app.utils.security import check_login_lockout
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('dashboard.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        # Generate referral code
        user.referral_code = User.generate_referral_code()
        # Handle referral link
        ref_code = request.args.get('ref') or request.form.get('ref')
        if ref_code:
            referrer = User.query.filter_by(referral_code=ref_code).first()
            if referrer and referrer.id != user.id:
                user.referred_by_id = referrer.id
        db.session.add(user)
        db.session.commit()
        notify_registration(user)
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('dashboard.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # Check lockout
            is_locked, mins = check_login_lockout(user)
            if is_locked:
                flash(f'Account temporarily locked due to too many failed attempts. Try again in {mins} minute(s).', 'danger')
                return redirect(url_for('auth.login'))
            # Check if account is suspended
            if not user.is_active:
                flash('Your account has been suspended. Please contact support.', 'danger')
                return redirect(url_for('auth.login'))
            # Generate OTP instead of logging in immediately (unless admin)
            if not user.is_admin:
                otp_code = OTP.generate_code()
                otp = OTP(
                    user_id=user.id,
                    code=otp_code,
                    expires_at=datetime.utcnow() + timedelta(minutes=10)
                )
                db.session.add(otp)
                db.session.commit()
                
                notify_otp(user, otp_code)
                
                # Store user ID in session for OTP verification
                session['temp_user_id'] = user.id
                session['remember_me'] = form.remember.data
                
                flash('A verification code has been sent to your email.', 'info')
                return redirect(url_for('auth.verify_otp'))
            else:
                login_user(user, remember=form.remember.data)
                flash('Login successful!', 'success')
                return redirect(url_for('admin.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user_id = session.get('temp_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
        
    user = User.query.get(user_id)
    form = OTPForm()
    
    if form.validate_on_submit():
        otp = OTP.query.filter_by(user_id=user.id, code=form.code.data, is_used=False).order_by(OTP.created_at.desc()).first()
        
        if otp and not otp.is_expired():
            otp.is_used = True
            db.session.commit()
            
            # Log the successful login
            history = LoginHistory(
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                status='success'
            )
            db.session.add(history)
            
            login_user(user, remember=session.get('remember_me', False))
            
            # Clear temp session
            session.pop('temp_user_id', None)
            session.pop('remember_me', None)
            
            flash('Login successful!', 'success')
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('dashboard.index'))
        else:
            # Log failed attempt
            history = LoginHistory(
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                status='failed'
            )
            db.session.add(history)
            db.session.commit()
            flash('Invalid or expired OTP.', 'danger')
            
    return render_template('auth/otp.html', title='Verify OTP', form=form, user=user)

@auth_bp.route('/resend-otp')
def resend_otp():
    user_id = session.get('temp_user_id')
    current_app.logger.info(f"DEBUG: Resend OTP for user_id: {user_id}")
    if not user_id:
        current_app.logger.info("DEBUG: No user_id in session, redirecting to login")
        return redirect(url_for('auth.login'))
        
    user = User.query.get(user_id)
    otp_code = OTP.generate_code()
    otp = OTP(
        user_id=user.id,
        code=otp_code,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.session.add(otp)
    db.session.commit()
    
    current_app.logger.info(f"DEBUG: Triggering notify_otp for {user.email}")
    notify_otp(user, otp_code)
    flash('A new code has been sent to your email.', 'info')
    return redirect(url_for('auth.verify_otp'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Token generation and email sending logic would go here
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('If an account exists with that email, a reset link has been sent.', 'info')
    return render_template('auth/forgot_password.html', title='Forgot Password', form=form)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    pin_form = WithdrawalPinForm()
    password_form = ChangePasswordForm()
    
    # Handle PIN Change
    if 'submit_pin' in request.form or (pin_form.validate_on_submit() and not password_form.is_submitted()):
        if pin_form.validate():
            current_user.set_withdrawal_pin(pin_form.pin.data)
            db.session.commit()
            flash('Withdrawal PIN has been updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
            
    # Handle Password Change
    if 'submit_password' in request.form or (password_form.validate_on_submit() and not pin_form.is_submitted()):
        if password_form.validate():
            if current_user.check_password(password_form.current_password.data):
                current_user.set_password(password_form.new_password.data)
                db.session.commit()
                flash('Your password has been updated successfully.', 'success')
                return redirect(url_for('auth.profile'))
            else:
                flash('Invalid current password.', 'danger')
    
    return render_template('auth/profile.html', title='Profile', pin_form=pin_form, password_form=password_form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))
