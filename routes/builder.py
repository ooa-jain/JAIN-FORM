from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user

builder_bp = Blueprint('builder', __name__, url_prefix='/builder')

@builder_bp.route('/<form_id>')
@login_required
def edit(form_id):
    from models.form import Form
    form = Form.get_by_id(form_id)
    if not form or form['user_id'] != current_user.id:
        return redirect(url_for('dashboard.index'))
    return render_template('builder/edit.html', form=form, form_id=form_id)

@builder_bp.route('/<form_id>/save', methods=['POST'])
@login_required
def save(form_id):
    from models.form import Form
    form = Form.get_by_id(form_id)
    if not form or form['user_id'] != current_user.id:
        return jsonify({'error':'Not found'}), 404
    data = request.get_json()
    update = {k: data[k] for k in ('title','description','pages','theme','settings') if k in data}
    Form.update(form_id, update)
    return jsonify({'success': True})

@builder_bp.route('/<form_id>/publish', methods=['POST'])
@login_required
def publish(form_id):
    from models.form import Form
    form = Form.get_by_id(form_id)
    if not form or form['user_id'] != current_user.id:
        return jsonify({'error':'Not found'}), 404
    is_pub = not form['settings'].get('is_published', False)
    Form.update(form_id, {'settings.is_published': is_pub})
    return jsonify({'success': True, 'is_published': is_pub})
