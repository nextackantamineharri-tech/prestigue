from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.kyc import KYC
from app.forms.kyc import KYCSubmitForm
import os
from werkzeug.utils import secure_filename
from datetime import datetime

kyc_bp = Blueprint('kyc', __name__)

def save_kyc_file(file, prefix):
    """Save a KYC document and return the filename."""
    upload_path = os.path.join('app', 'static', 'uploads', 'kyc')
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    ext = file.filename.rsplit('.', 1)[-1]
    filename = secure_filename(f"{prefix}_{current_user.id}_{int(datetime.utcnow().timestamp())}.{ext}")
    file.save(os.path.join(upload_path, filename))
    return filename

@kyc_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    existing = current_user.kyc_record
    form = KYCSubmitForm()

    if form.validate_on_submit():
        # If rejected, update existing record instead of creating new one
        if existing and existing.status == 'rejected':
            existing.id_type = form.id_type.data
            existing.id_image = save_kyc_file(form.id_image.data, 'id')
            existing.selfie_image = save_kyc_file(form.selfie_image.data, 'selfie')
            existing.address_image = save_kyc_file(form.address_image.data, 'address')
            existing.status = 'pending'
            existing.admin_note = None
            existing.submitted_at = datetime.utcnow()
            db.session.commit()
            flash('KYC documents re-submitted successfully. Our team will review them shortly.', 'success')
        elif not existing:
            kyc = KYC(
                user_id=current_user.id,
                id_type=form.id_type.data,
                id_image=save_kyc_file(form.id_image.data, 'id'),
                selfie_image=save_kyc_file(form.selfie_image.data, 'selfie'),
                address_image=save_kyc_file(form.address_image.data, 'address')
            )
            db.session.add(kyc)
            db.session.commit()
            flash('KYC documents submitted successfully! Our team will review them shortly.', 'success')
        else:
            flash('Your KYC is already submitted or verified.', 'info')

        return redirect(url_for('kyc.status'))

    return render_template('kyc/submit.html', title='KYC Verification', form=form, kyc=existing)

@kyc_bp.route('/status')
@login_required
def status():
    kyc = current_user.kyc_record
    return render_template('kyc/status.html', title='KYC Status', kyc=kyc)
