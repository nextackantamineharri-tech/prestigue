from flask import Blueprint, render_template
from app.models.user import SystemSettings

main_bp = Blueprint('main', __name__)

@main_bp.app_context_processor
def inject_settings():
    return dict(settings=SystemSettings.get_settings())

@main_bp.route('/')
def index():
    return render_template('main/index.html')

@main_bp.route('/about')
def about():
    return render_template('main/about.html')

@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500
