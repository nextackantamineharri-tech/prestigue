from flask import current_app, render_template
from flask_mail import Message
from app import mail, db
from app.models.notification import Notification
import threading

def _send_async(app, msg):
    with app.app_context():
        try:
            app.logger.info(f"DEBUG: Background thread starting to send email to {msg.recipients}")
            mail.send(msg)
            app.logger.info("DEBUG: Background thread successfully sent email")
        except Exception as e:
            app.logger.error(f"DEBUG: Background thread FAILED to send email: {e}")
            app.logger.error(f"[Mail Error] {e}")

def send_email(subject, recipients, template, **kwargs):
    """Generic send function — runs in background thread."""
    app = current_app._get_current_object()
    from app.models.user import SystemSettings
    settings = SystemSettings.get_settings()
    msg = Message(
        subject=f"[{settings.site_name}] {subject}",
        recipients=recipients if isinstance(recipients, list) else [recipients],
        sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@prestigefinance.com')
    )
    msg.html = render_template(template, settings=settings, **kwargs)
    threading.Thread(target=_send_async, args=(app, msg)).start()

def create_notification(user, title, message, type='info'):
    """Create an in-app notification."""
    notif = Notification(user_id=user.id, title=title, message=message, type=type)
    db.session.add(notif)
    db.session.commit()

# ──────────────────────────────────────────
# Notification helpers — one per event
# ──────────────────────────────────────────

def notify_registration(user):
    send_email('Welcome to the Platform', user.email, 'emails/welcome.html', user=user)
    create_notification(user, 'Welcome!', 'Welcome to Prestige Finance Global. Your account is ready.', 'success')

def notify_otp(user, otp_code):
    send_email('Your Login Verification Code', user.email, 'emails/otp.html', user=user, otp_code=otp_code)

def notify_password_reset(user, link):
    send_email('Reset Your Password', user.email, 'emails/password_reset.html', user=user, link=link)

def notify_deposit_received(user, deposit):
    send_email('Deposit Request Received', user.email, 'emails/deposit_received.html', user=user, deposit=deposit)
    admin_email = current_app.config.get('ADMIN_EMAIL')
    if admin_email:
        send_email('New Deposit Request', admin_email, 'emails/admin_deposit_alert.html', user=user, deposit=deposit)

def notify_deposit_approved(user, deposit):
    send_email('Your Deposit Has Been Approved', user.email, 'emails/deposit_approved.html', user=user, deposit=deposit)
    create_notification(user, 'Deposit Approved', f'Your deposit of ${deposit.amount} has been approved and credited to your balance.', 'success')

def notify_deposit_rejected(user, deposit):
    send_email('Deposit Update', user.email, 'emails/deposit_rejected.html', user=user, deposit=deposit)
    create_notification(user, 'Deposit Rejected', f'Your deposit request of ${deposit.amount} was not approved. Please contact support.', 'danger')

def notify_withdrawal_received(user, withdrawal):
    send_email('Withdrawal Request Received', user.email, 'emails/withdrawal_received.html', user=user, withdrawal=withdrawal)
    admin_email = current_app.config.get('ADMIN_EMAIL')
    if admin_email:
        send_email('New Withdrawal Request', admin_email, 'emails/admin_withdrawal_alert.html', user=user, withdrawal=withdrawal)

def notify_withdrawal_approved(user, withdrawal):
    send_email('Withdrawal Approved', user.email, 'emails/withdrawal_approved.html', user=user, withdrawal=withdrawal)
    create_notification(user, 'Withdrawal Approved', f'Your withdrawal request of ${withdrawal.amount} has been approved and processed.', 'success')

def notify_withdrawal_rejected(user, withdrawal):
    send_email('Withdrawal Update', user.email, 'emails/withdrawal_rejected.html', user=user, withdrawal=withdrawal)
    create_notification(user, 'Withdrawal Rejected', f'Your withdrawal request of ${withdrawal.amount} was rejected. Reason: {withdrawal.admin_note}', 'danger')

def notify_kyc_received(user, kyc):
    admin_email = current_app.config.get('ADMIN_EMAIL')
    if admin_email:
        send_email('New KYC Submission', admin_email, 'emails/admin_kyc_alert.html', user=user, kyc=kyc)

def notify_kyc_approved(user):
    send_email('Identity Verified ✓', user.email, 'emails/kyc_approved.html', user=user)
    create_notification(user, 'Identity Verified', 'Your identity has been successfully verified. You now have full access to our services.', 'success')

def notify_kyc_rejected(user, reason):
    send_email('KYC Submission Update', user.email, 'emails/kyc_rejected.html', user=user, reason=reason)
    create_notification(user, 'Verification Failed', f'Your identity verification was rejected. Reason: {reason}', 'danger')

def notify_investment_active(user, investment):
    send_email('Investment Activated', user.email, 'emails/investment_active.html', user=user, investment=investment)

def notify_profit_credited(user, investment, amount):
    send_email('Profit Credited to Your Account', user.email, 'emails/profit_credited.html',
               user=user, investment=investment, amount=amount)

def notify_investment_completed(user, investment):
    send_email('Investment Plan Completed', user.email, 'emails/investment_completed.html', user=user, investment=investment)
