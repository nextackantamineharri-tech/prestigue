from flask_wtf import FlaskForm
from wtforms import DecimalField, HiddenField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class InvestForm(FlaskForm):
    amount = DecimalField('Investment Amount ($)', validators=[DataRequired(), NumberRange(min=0.01)])
    plan_id = HiddenField('Plan ID', validators=[DataRequired()])
    submit = SubmitField('Confirm Investment')
