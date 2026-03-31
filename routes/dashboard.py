from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    from models.form import Form
    from models.response import Response
    forms = Form.get_by_user(current_user.id)
    for f in forms:
        f['response_count'] = Response.get_count(str(f['_id']))
    return render_template('dashboard/index.html', forms=forms)

@dashboard_bp.route('/forms/new', methods=['POST'])
@login_required
def new_form():
    from models.form import Form
    f = Form.create(current_user.id, request.form.get('title','Untitled Form'))
    return redirect(url_for('builder.edit', form_id=str(f['_id'])))

@dashboard_bp.route('/forms/<form_id>/delete', methods=['POST'])
@login_required
def delete_form(form_id):
    from models.form import Form
    f = Form.get_by_id(form_id)
    if f and f['user_id'] == current_user.id: Form.delete(form_id)
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/forms/<form_id>/duplicate', methods=['POST'])
@login_required
def duplicate_form(form_id):
    from models.form import Form
    orig = Form.get_by_id(form_id)
    if orig and orig['user_id'] == current_user.id:
        nf = Form.create(current_user.id, orig['title']+' (Copy)')
        Form.update(str(nf['_id']),{
            'pages':orig['pages'],'theme':orig['theme'],
            'settings':orig['settings'],'description':orig.get('description','')})
    return redirect(url_for('dashboard.index'))
