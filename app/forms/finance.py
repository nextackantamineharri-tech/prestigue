from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, DecimalField, SelectField, SubmitField, PasswordField
from wtforms.validators import DataRequired, NumberRange, Length

class DepositForm(FlaskForm):
    currency_id = SelectField('Select Coin', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Amount to Deposit ($)', validators=[DataRequired(), NumberRange(min=10)])
    proof_image = FileField('Upload Payment Proof', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Submit Deposit')

class WithdrawalForm(FlaskForm):
    currency_id = SelectField('Select Coin', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Amount to Withdraw ($)', validators=[DataRequired(), NumberRange(min=10)])
    network = StringField('Network (e.g. ERC20, TRC20)', validators=[DataRequired()])
    wallet_address = StringField('Destination Wallet Address', validators=[DataRequired()])
    pin = PasswordField('Transaction PIN', validators=[DataRequired(), Length(min=4, max=6)])
    submit = SubmitField('Request Withdrawal')
