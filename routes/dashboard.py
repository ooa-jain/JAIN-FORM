from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/home')
@login_required
def index():
    from models.form import Form
    from models.response import Response
    from app import db
    forms = Form.get_by_user(current_user.id)
    for f in forms:
        f['response_count'] = Response.get_count(str(f['_id']))
    try:
        newsletter_count = db.newsletters.count_documents({'user_id': current_user.id})
    except Exception:
        newsletter_count = 0
    return render_template('dashboard/index.html', forms=forms, newsletter_count=newsletter_count)

@dashboard_bp.route('/create')
@login_required
def create():
    from models.form import Form
    from models.response import Response
    forms = Form.get_by_user(current_user.id)
    for f in forms:
        f['response_count'] = Response.get_count(str(f['_id']))
    return render_template('dashboard/create.html', forms=forms)



@dashboard_bp.route('/forms/new', methods=['POST'])
@login_required
def new_form():
    if not current_user.can_create_form():
        return jsonify({'error': 'Form limit reached for your plan. Please upgrade.'}), 403
    from models.form import Form
    f = Form.create(current_user.id, request.form.get('title','Untitled Form'))
    return redirect(url_for('builder.edit', form_id=str(f['_id'])))

@dashboard_bp.route('/forms/new-api', methods=['POST'])
@login_required
def new_form_api():
    if not current_user.can_create_form():
        return jsonify({'success': False, 'error': 'Form limit reached for your plan. Please upgrade.'}), 403
    from models.form import Form
    data = request.get_json() or {}
    title = data.get('title', 'AI Generated Form')
    presentation_style = data.get('default_style', 'form')

    f = Form.create(current_user.id, title)
    form_id = str(f['_id'])

    # Immediately persist the presentation_style so public view reads it
    if presentation_style:
        Form.update(form_id, {
            'settings.presentation_style': presentation_style
        })

    return jsonify({
        'success': True,
        'form_id': form_id,
        'presentation_style': presentation_style
    })

@dashboard_bp.route('/forms/<form_id>/delete', methods=['POST'])
@login_required
def delete_form(form_id):
    from models.form import Form
    f = Form.get_by_id(form_id)
    if f and f['user_id'] == current_user.id:
        Form.delete(form_id)
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/forms/<form_id>/duplicate', methods=['POST'])
@login_required
def duplicate_form(form_id):
    if not current_user.can_create_form():
        return jsonify({'error': 'Form limit reached for your plan. Please upgrade.'}), 403
    from models.form import Form
    orig = Form.get_by_id(form_id)
    if orig and orig['user_id'] == current_user.id:
        nf = Form.create(current_user.id, orig['title']+' (Copy)')
        Form.update(str(nf['_id']), {
            'pages':    orig['pages'],
            'theme':    orig['theme'],
            'settings': orig['settings'],
            'description': orig.get('description','')
        })
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/forms/import', methods=['POST'])
@login_required
def import_form():
    if not current_user.can_create_form():
        return jsonify({'success': False, 'error': 'Form limit reached for your plan. Please upgrade.'}), 403

    file = request.files.get('file')
    if not file:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400

    from models.form import Form
    import csv, io, uuid
    filename = file.filename.lower()
    headers = []
    try:
        if filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            reader = csv.reader(stream)
            headers = [str(c).strip() for c in next(reader, []) if str(c).strip()]
        elif filename.endswith('.xlsx'):
            import openpyxl
            wb = openpyxl.load_workbook(file.stream, data_only=True)
            sheet = wb.active
            raw_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True), [])
            for cell in raw_row:
                if cell is not None:
                    val = str(cell).strip()
                    if val:
                        headers.append(val)
        else:
            return jsonify({'success': False, 'error': 'Please upload a .csv or .xlsx file'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to parse file: {str(e)}'}), 400

    if not headers:
        return jsonify({'success': False, 'error': 'Could not read columns from file'}), 400

    # Only skip auto-system 'timestamp' column; preserve date/time/etc headers
    skip_cols = {'timestamp'}
    headers = [h for h in headers if h.strip().lower() not in skip_cols]

    title = request.form.get('title', 'Imported Form') or 'Imported Form'
    f = Form.create(current_user.id, title)

    def guess_field_type(col_name):
        name = col_name.strip().lower()
        if name in ('date', 'dob', 'birth date', 'start date', 'end date', 'event date'):
            return 'date'
        if name in ('time', 'start time', 'end time', 'event time'):
            return 'time'
        if 'email' in name:
            return 'email'
        if name in ('phone', 'mobile', 'contact', 'phone number', 'mobile number'):
            return 'phone'
        if name in ('number', 'quantity', 'age', 'count', 'amount', 'score', 'roll no', 'roll number', 'reg no'):
            return 'number'
        if name in ('url', 'website', 'link'):
            return 'url'
        return 'short_text'

    elements = []
    for h in headers:
        elements.append({
            'id': 'el_' + uuid.uuid4().hex[:8],
            'type': guess_field_type(h),
            'title': str(h),
            'required': False
        })

    Form.update(str(f['_id']), {
        'pages': [{'id': 'p1', 'title': 'Page 1', 'description': '', 'elements': elements}]
    })

    return jsonify({'success': True, 'form_id': str(f['_id'])})



