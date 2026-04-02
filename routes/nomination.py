from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from flask_login import login_required, current_user
from datetime import datetime
import json

nomination_bp = Blueprint('nomination', __name__, url_prefix='/nomination')

# ── Simple hard-coded admin credentials for nomination admin ──────────────────
NOMINATION_ADMIN_USER = 'admin'
NOMINATION_ADMIN_PASS = 'admin123'

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

# ── Public form ───────────────────────────────────────────────────────────────
@nomination_bp.route('/')
def index():
    return render_template('nomination/index.html')

# ── Submit (public, no login needed) ─────────────────────────────────────────
@nomination_bp.route('/submit', methods=['POST'])
def submit():
    from app import db
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data received'}), 400
    doc = {
        'form_type':       'expert_nomination',
        'dept':            data.get('dept', ''),
        'submitted_by':    data.get('subName', ''),
        'submitted_email': data.get('subEmail', ''),
        'submission_date': data.get('date', ''),
        'experts':         data.get('experts', []),
        'submitted_at':    datetime.utcnow()
    }
    result = db.nominations.insert_one(doc)
    return jsonify({'success': True, 'id': str(result.inserted_id)})

# ── Delete (requires nomination admin session) ────────────────────────────────
@nomination_bp.route('/delete/<nom_id>', methods=['POST'])
def delete(nom_id):
    if not session.get('nom_admin_logged_in'):
        return jsonify({'success': False, 'error': 'Not authorised'}), 403
    from app import db
    from bson import ObjectId
    try:
        db.nominations.delete_one({'_id': ObjectId(nom_id)})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ── Nomination admin login ────────────────────────────────────────────────────
@nomination_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == NOMINATION_ADMIN_USER and password == NOMINATION_ADMIN_PASS:
            session['nom_admin_logged_in'] = True
            return redirect(url_for('nomination.admin'))
        else:
            error = 'Invalid username or password.'
    return render_template('nomination/admin_login.html', error=error)

@nomination_bp.route('/admin/logout')
def admin_logout():
    session.pop('nom_admin_logged_in', None)
    return redirect(url_for('nomination.admin_login'))

# ── Nomination admin dashboard ────────────────────────────────────────────────
@nomination_bp.route('/admin')
def admin():
    if not session.get('nom_admin_logged_in'):
        return redirect(url_for('nomination.admin_login'))

    from app import db
    nominations = list(db.nominations.find(
        {'form_type': 'expert_nomination'}
    ).sort('submitted_at', -1))

    for nom in nominations:
        nom['_id'] = str(nom['_id'])
        nom['expert_count'] = sum(
            1 for e in nom.get('experts', []) if e.get('name', '').strip()
        )
        if nom.get('submitted_at'):
            nom['submitted_at_str'] = nom['submitted_at'].strftime('%d %b %Y, %H:%M')
        else:
            nom['submitted_at_str'] = '—'

    nominations_json = json.dumps(serialize_nominations(nominations))
    total_experts = sum(n['expert_count'] for n in nominations)

    return render_template(
        'nomination/admin.html',
        nominations=nominations,
        nominations_json=nominations_json,
        total_experts=total_experts
    )