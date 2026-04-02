from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import json

nomination_bp = Blueprint('nomination', __name__, url_prefix='/nomination')

def serialize_nominations(nominations):
    result = []
    for n in nominations:
        clean = {}
        for k, v in n.items():
            if k == '_id':
                clean[k] = str(v)
            elif isinstance(v, datetime):
                clean[k] = v.isoformat()
            else:
                clean[k] = v
        result.append(clean)
    return result

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
@login_required
def admin():
    from app import db
    nominations = list(db.nominations.find(
        {'form_type': 'expert_nomination'}
    ).sort('submitted_at', -1))

    # Count experts properly
    for nom in nominations:
        nom['expert_count'] = sum(1 for e in nom.get('experts', []) if e.get('name', '').strip())
        if nom.get('submitted_at'):
            nom['submitted_at_str'] = nom['submitted_at'].strftime('%d %b %Y, %H:%M')
        else:
            nom['submitted_at_str'] = '—'

    nominations_json = json.dumps(serialize_nominations(nominations))
    total_experts = sum(n['expert_count'] for n in nominations)

    return render_template('nomination/admin.html',
                           nominations=nominations,
                           nominations_json=nominations_json,
                           total_experts=total_experts)
