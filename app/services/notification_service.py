from flask import current_app, render_template
from app import db
from app.models.notification import Notification
import threading
import requests


def _send_via_brevo(app, subject, recipients, html_content):
    """Send email through Brevo's transactional HTTP API (port 443 — no firewall issues)."""
    with app.app_context():
        api_key = app.config.get('BREVO_API_KEY')
        sender_email = app.config.get('MAIL_DEFAULT_SENDER', 'noreply@prestigefinanceglobal.net')
        app_name = app.config.get('APP_NAME', 'Prestige Finance Global')

        if not api_key:
            app.logger.error('[Mail Error] BREVO_API_KEY is not set in config.')
            return

        payload = {
            "sender": {"name": app_name, "email": sender_email},
            "to": [{"email": r} for r in recipients],
            "subject": subject,
            "htmlContent": html_content,
        }

        try:
            app.logger.info(f"Sending email via Brevo API to {recipients}")
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=15,
            )
            if response.status_code in (200, 201):
                app.logger.info(f"Email sent successfully to {recipients}")
            else:
                app.logger.error(
                    f"[Mail Error] Brevo API returned {response.status_code}: {response.text}"
                )
        except Exception as e:
            app.logger.error(f"[Mail Error] Brevo API exception: {e}")


def send_email(subject, recipients, template, **kwargs):
    """Generic send function — renders template and dispatches via Brevo HTTP API in background thread."""
    app = current_app._get_current_object()
    from app.models.user import SystemSettings
    settings = SystemSettings.get_settings()

    full_subject = f"[{settings.site_name}] {subject}"
    recipient_list = recipients if isinstance(recipients, list) else [recipients]

    # Render HTML inside the request context before handing off to the thread
    html_content = render_template(template, settings=settings, **kwargs)

    threading.Thread(
        target=_send_via_brevo,
        args=(app, full_subject, recipient_list, html_content),
    ).start()


def create_notification(user, title, message, type='info'):
    """Create an in-app notification."""
    notif = Notification(user_id=user.id, title=title, message=message, type=type)
    db.session.add(notif)
    db.session.commit()


# ──────────────────────────────────────────
# Notification helpers — one per event
# ──────────────────────────────────────────

def get_all_admin_emails():
    """Retrieve all admin email addresses from the database with config fallback."""
    try:
        from app.models.user import User
        admins = User.query.filter_by(is_admin=True).all()
        emails = [a.email for a in admins if a.email]
        if not emails:
            config_admin = current_app.config.get('ADMIN_EMAIL')
            if config_admin:
                emails = [config_admin]
        return list(set(emails))
    except Exception as e:
        current_app.logger.error(f"Error fetching admin emails: {e}")
        config_admin = current_app.config.get('ADMIN_EMAIL')
        return [config_admin] if config_admin else []


def notify_registration(user):
    send_email('Welcome to the Platform', user.email, 'emails/welcome.html', user=user)
    create_notification(user, 'Welcome!', 'Welcome to Prestige Finance Global. Your account is ready.', 'success')
    admin_emails = get_all_admin_emails()
    if admin_emails:
        send_email('New User Registration Alert', admin_emails, 'emails/admin_registration_alert.html', user=user)

def notify_otp(user, otp_code):
    send_email('Your Login Verification Code', user.email, 'emails/otp.html', user=user, otp_code=otp_code)

def notify_password_reset(user, link):
    send_email('Reset Your Password', user.email, 'emails/password_reset.html', user=user, link=link)

def notify_deposit_received(user, deposit):
    send_email('Deposit Request Received', user.email, 'emails/deposit_received.html', user=user, deposit=deposit)
    admin_emails = get_all_admin_emails()
    if admin_emails:
        send_email('New Deposit Request', admin_emails, 'emails/admin_deposit_alert.html', user=user, deposit=deposit)

def notify_deposit_approved(user, deposit):
    send_email('Your Deposit Has Been Approved', user.email, 'emails/deposit_approved.html', user=user, deposit=deposit)
    create_notification(user, 'Deposit Approved', f'Your deposit of ${deposit.amount} has been approved and credited to your balance.', 'success')

def notify_deposit_rejected(user, deposit):
    send_email('Deposit Update', user.email, 'emails/deposit_rejected.html', user=user, deposit=deposit)
    create_notification(user, 'Deposit Rejected', f'Your deposit request of ${deposit.amount} was not approved. Please contact support.', 'danger')

def notify_withdrawal_received(user, withdrawal):
    send_email('Withdrawal Request Received', user.email, 'emails/withdrawal_received.html', user=user, withdrawal=withdrawal)
    admin_emails = get_all_admin_emails()
    if admin_emails:
        send_email('New Withdrawal Request', admin_emails, 'emails/admin_withdrawal_alert.html', user=user, withdrawal=withdrawal)

def notify_withdrawal_approved(user, withdrawal):
    send_email('Withdrawal Approved', user.email, 'emails/withdrawal_approved.html', user=user, withdrawal=withdrawal)
    create_notification(user, 'Withdrawal Approved', f'Your withdrawal request of ${withdrawal.amount} has been approved and processed.', 'success')

def notify_withdrawal_rejected(user, withdrawal):
    send_email('Withdrawal Update', user.email, 'emails/withdrawal_rejected.html', user=user, withdrawal=withdrawal)
    create_notification(user, 'Withdrawal Rejected', f'Your withdrawal request of ${withdrawal.amount} was rejected. Reason: {withdrawal.admin_note}', 'danger')

def notify_kyc_received(user, kyc):
    admin_emails = get_all_admin_emails()
    if admin_emails:
        send_email('New KYC Submission', admin_emails, 'emails/admin_kyc_alert.html', user=user, kyc=kyc)

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
