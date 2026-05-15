from flask import render_template, current_app
from flask_mail import Message
from app import mail
import threading

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Email sending failed: {str(e)}")

def send_email(subject, recipient, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(
        subject=f"[{app.config['APP_NAME']}] {subject}",
        recipients=[recipient],
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    msg.html = render_template(template, **kwargs)
    
    # Send email in a separate thread to avoid blocking the main request
    threading.Thread(target=send_async_email, args=(app, msg)).start()

def send_otp_email(user, otp_code):
    send_email(
        subject="Login Verification Code",
        recipient=user.email,
        template="emails/otp.html",
        user=user,
        otp_code=otp_code
    )

def send_password_reset_email(user, token):
    # Implementation for phase 2 password reset
    pass

def send_verification_email(user, token):
    # Implementation for phase 2 email verification
    pass
