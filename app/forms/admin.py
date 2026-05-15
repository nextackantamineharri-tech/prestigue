from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, URLField, EmailField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Optional

class SystemSettingsForm(FlaskForm):
    # ... (rest of SystemSettingsForm stays the same)
    # I'll just keep the whole file structure for simplicity in replacement
    site_name = StringField('Website Name', validators=[DataRequired(), Length(max=100)])
    site_email = EmailField('Support Email', validators=[DataRequired()])
    site_phone = StringField('Support Phone', validators=[Optional()])
    site_address = TextAreaField('Physical Address', validators=[Optional()])
    
    # Branding
    primary_color = StringField('Primary Color (Hex)', validators=[DataRequired(), Length(min=4, max=7)])
    secondary_color = StringField('Secondary Color (Hex)', validators=[DataRequired(), Length(min=4, max=7)])
    accent_color = StringField('Accent Color (Hex)', validators=[DataRequired(), Length(min=4, max=7)])
    logo_url = URLField('Logo URL', validators=[Optional()])
    favicon_url = URLField('Favicon URL', validators=[Optional()])
    
    # SEO
    meta_title = StringField('SEO Meta Title', validators=[Optional()])
    meta_description = TextAreaField('SEO Meta Description', validators=[Optional()])
    
    # Social Links
    facebook_url = URLField('Facebook URL', validators=[Optional()])
    twitter_url = URLField('Twitter URL', validators=[Optional()])
    instagram_url = URLField('Instagram URL', validators=[Optional()])
    telegram_url = URLField('Telegram URL', validators=[Optional()])
    
    # SMTP (Basic info - full logic in config/env for security, but labels here for display)
    smtp_info = StringField('SMTP Server (Read Only)', render_kw={'readonly': True})
    
    submit = SubmitField('Save All Settings')

class InvestmentPlanForm(FlaskForm):
    name = StringField('Plan Name', validators=[DataRequired(), Length(max=100)])
    min_amount = StringField('Minimum Deposit ($)', validators=[DataRequired()])
    max_amount = StringField('Maximum Deposit ($)', validators=[DataRequired()])
    roi_percentage = StringField('ROI Percentage (%)', validators=[DataRequired()])
    duration_days = StringField('Duration (Days)', validators=[DataRequired()])
    
    profit_type = SelectField('Profit Type', choices=[('daily', 'Daily Profit'), ('fixed', 'Fixed Profit (at end)')], validators=[DataRequired()])
    payout_frequency = SelectField('Payout Frequency', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('fixed', 'At the end of duration')
    ], validators=[DataRequired()])
    
    return_capital = BooleanField('Return Capital at End')
    is_active = BooleanField('Active')
    is_featured = BooleanField('Featured Plan')
    
    submit = SubmitField('Save Plan')

class CurrencyForm(FlaskForm):
    name = StringField('Currency Name (e.g. Bitcoin)', validators=[DataRequired()])
    symbol = StringField('Symbol (e.g. BTC)', validators=[DataRequired()])
    network = StringField('Network (e.g. ERC20, TRC20)', validators=[Optional()])
    wallet_address = StringField('Wallet Address', validators=[DataRequired()])
    logo = FileField('Currency Logo', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg', 'svg'], 'Images only!')
    ])
    is_active = BooleanField('Active')
    submit = SubmitField('Save Currency')

class DepositProcessForm(FlaskForm):
    admin_note = TextAreaField('Admin Note / Rejection Reason', validators=[Optional()])
    submit_approve = SubmitField('Approve & Credit')
    submit_reject = SubmitField('Reject')

class WithdrawalProcessForm(FlaskForm):
    admin_note = TextAreaField('Admin Note / Rejection Reason', validators=[Optional()])
    submit_approve = SubmitField('Approve Request')
    submit_reject = SubmitField('Reject')
    submit_paid = SubmitField('Mark as Paid')
