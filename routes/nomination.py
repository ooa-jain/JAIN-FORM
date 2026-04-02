from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import datetime

nomination_bp = Blueprint('nomination', __name__, url_prefix='/nomination')

@nomination_bp.route('/')
def index():
    return render_template('nomination/index.html')

@nomination_bp.route('/submit', methods=['POST'])
def submit():
    from app import db
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data received'}), 400

    doc = {
        'form_type': 'expert_nomination',
        'dept': data.get('dept', ''),
        'submitted_by': data.get('subName', ''),
        'submitted_email': data.get('subEmail', ''),
        'submission_date': data.get('date', ''),
        'experts': data.get('experts', []),
        'submitted_at': datetime.utcnow()
    }
    result = db.nominations.insert_one(doc)
    return jsonify({'success': True, 'id': str(result.inserted_id)})

@nomination_bp.route('/admin')
def admin():
    from app import db
    from flask_login import current_user
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    nominations = list(db.nominations.find({'form_type': 'expert_nomination'}).sort('submitted_at', -1))
    return render_template('nomination/admin.html', nominations=nominations)
