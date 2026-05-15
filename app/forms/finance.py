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
    currency_id = SelectField('Select Account/Currency', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Amount to Transfer ($)', validators=[DataRequired(), NumberRange(min=10)])
    network = StringField('Destination Bank / Network', validators=[DataRequired()], render_kw={"placeholder": "e.g. Chase Bank, ERC20, etc."})
    wallet_address = StringField('Account Number / Wallet Address', validators=[DataRequired()], render_kw={"placeholder": "Enter account or wallet details"})
    pin = PasswordField('Transaction PIN', validators=[DataRequired(), Length(min=4, max=6)])
    submit = SubmitField('Initialize Transfer')
