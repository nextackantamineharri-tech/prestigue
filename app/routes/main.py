from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user
from app.models.user import SystemSettings

from app.models.investment import InvestmentPlan

main_bp = Blueprint('main', __name__)

@main_bp.app_context_processor
def inject_settings():
    return dict(settings=SystemSettings.get_settings())

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('dashboard.index'))
    plans = InvestmentPlan.query.filter_by(is_active=True).all()
    return render_template('main/index.html', plans=plans)

@main_bp.route('/about')
def about():
    return render_template('main/about.html')

@main_bp.route('/how-it-works')
def how_it_works():
    return render_template('main/how_it_works.html')

@main_bp.route('/faq')
def faq():
    return render_template('main/faq.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # placeholder — just flash a success message for now
        flash('Your message has been received. We will get back to you within 24 hours.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('main/contact.html')

@main_bp.route('/terms')
def terms():
    return render_template('main/terms.html')

@main_bp.route('/privacy')
def privacy():
    return render_template('main/privacy.html')

@main_bp.route('/blog')
def blog():
    return render_template('main/blog.html')

@main_bp.route('/kyc-policy')
def kyc_policy():
    return render_template('main/kyc_policy.html')

@main_bp.route('/aml-policy')
def aml_policy():
    return render_template('main/aml_policy.html')

@main_bp.route('/risk-disclaimer')
def risk_disclaimer():
    return render_template('main/risk_disclaimer.html')

@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500
