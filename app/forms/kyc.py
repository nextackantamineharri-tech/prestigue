from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

class KYCSubmitForm(FlaskForm):
    id_type = SelectField('ID Document Type', choices=[
        ('passport', 'International Passport'),
        ('national_id', 'National ID Card'),
        ('drivers_license', "Driver's License"),
    ], validators=[DataRequired()])
    
    id_image = FileField('Government-Issued ID (Front)', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images and PDFs only!')
    ])
    selfie_image = FileField('Selfie Holding Your ID', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    address_image = FileField('Proof of Address (Utility Bill, Bank Statement)', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images and PDFs only!')
    ])
    
    submit = SubmitField('Submit for Verification')

class KYCReviewForm(FlaskForm):
    admin_note = TextAreaField('Admin Note / Rejection Reason', validators=[Optional()])
    submit_approve = SubmitField('Verify & Approve')
    submit_reject = SubmitField('Reject')
    submit_reupload = SubmitField('Request Re-upload')
