from flask import Flask, render_template, session, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import Bcrypt
from app.utils.scheduler import init_scheduler
from app.utils.security import apply_security_headers
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)

    # Initialize Scheduler
    init_scheduler(app)

    # Authentication configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.dashboard import dashboard_bp
    
    from app.routes.kyc import kyc_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(kyc_bp, url_prefix='/kyc')

    # Register AuditLog model for migrations
    from app.models.audit import AuditLog

    # Security headers on every response
    app.after_request(apply_security_headers)

    # Keep the session cookie alive for its full lifetime instead of expiring
    # it when the browser closes — a tab left open across a browser restart
    # was losing its session cookie, which surfaces as a CSRF error on submit.
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    # Template context processors
    @app.context_processor
    def inject_globals():
        from app.models.user import SystemSettings
        from app.models.notification import Notification
        from flask_login import current_user
        settings = SystemSettings.get_settings()
        unread_count = 0
        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return dict(settings=settings, now=datetime.utcnow(), unread_count=unread_count)

    # Error handlers
    @app.errorhandler(CSRFError)
    def csrf_error(e):
        flash('Your session expired before the form was submitted. Please try again.', 'warning')
        return redirect(request.path)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Logging setup
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/prestige_finance.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Prestige Finance Startup')

    return app
