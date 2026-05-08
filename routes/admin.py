from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

admin_bp = Blueprint('admin_panel', __name__, url_prefix='/admin')

def _db():
    from app import db; return db

def is_admin():
    admin_emails = os.getenv('ADMIN_EMAILS', 'admin@formcraft.ai').split(',')
    return current_user.email.strip() in [e.strip() for e in admin_emails]

@admin_bp.route('/')
@login_required
def index():
    # Get all users
    users = list(_db().users.find({}).sort('created_at', -1))
    # Get all forms with user info
    forms = list(_db().forms.find({}).sort('created_at', -1))
    # Get form counts per user
    user_form_counts = {}
    for f in forms:
        uid = f.get('user_id', '')
        user_form_counts[uid] = user_form_counts.get(uid, 0) + 1
    # Enrich users
    for u in users:
        u['_id'] = str(u['_id'])
        u['form_count'] = user_form_counts.get(str(u['_id']), 0)
        if u.get('created_at'):
            u['created_str'] = u['created_at'].strftime('%d %b %Y')
    # Enrich forms
    user_map = {str(u['_id']): u.get('name','?') for u in users}
    for f in forms:
        f['_id'] = str(f['_id'])
        f['user_name'] = user_map.get(f.get('user_id',''), 'Unknown')
        f['response_count_real'] = _db().responses.count_documents({'form_id': f['_id']})
        if f.get('updated_at'):
            f['updated_str'] = f['updated_at'].strftime('%d %b %Y')
    total_responses = _db().responses.count_documents({})
    newsletters = _db().newsletters.count_documents({})
    return render_template('admin/index.html',
        users=users, forms=forms,
        total_users=len(users),
        total_forms=len(forms),
        total_responses=total_responses,
        total_newsletters=newsletters,
        user_map=user_map
    )

@admin_bp.route('/delete-form/<form_id>', methods=['POST'])
@login_required
def delete_form(form_id):
    from bson import ObjectId
    try:
        _db().forms.delete_one({'_id': ObjectId(form_id)})
        _db().responses.delete_many({'form_id': form_id})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/delete-user/<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    from bson import ObjectId
    try:
        # Delete all user forms and responses
        user_forms = list(_db().forms.find({'user_id': user_id}))
        for f in user_forms:
            _db().responses.delete_many({'form_id': str(f['_id'])})
        _db().forms.delete_many({'user_id': user_id})
        _db().newsletters.delete_many({'user_id': user_id})
        _db().users.delete_one({'_id': ObjectId(user_id)})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/notify', methods=['POST'])
@login_required
def notify():
    data = request.get_json() or {}
    target = data.get('target', 'all')  # 'all' or user_id
    subject = data.get('subject', 'Notification from FORM.AI')
    message = data.get('message', '')

    if not message:
        return jsonify({'success': False, 'error': 'Message is required'})

    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_pass = os.getenv('SMTP_PASS', '')
    from_addr = os.getenv('MAIL_FROM', 'noreply@formcraft.ai')

    if not smtp_user or not smtp_pass:
        # Store notification in DB even if email fails
        notif = {
            'target': target,
            'subject': subject,
            'message': message,
            'sent_by': current_user.id,
            'sent_at': datetime.utcnow(),
            'email_sent': False,
            'error': 'SMTP not configured'
        }
        _db().notifications.insert_one(notif)
        return jsonify({'success': False, 'error': 'SMTP not configured. Notification saved to database only.'})

    # Get target emails
    if target == 'all':
        users = list(_db().users.find({}, {'email': 1, 'name': 1}))
    else:
        from bson import ObjectId
        try:
            u = _db().users.find_one({'_id': ObjectId(target)}, {'email': 1, 'name': 1})
            users = [u] if u else []
        except:
            return jsonify({'success': False, 'error': 'Invalid user ID'})

    html_body = f'''<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08)">
  <div style="background:#1A1A2E;padding:28px 32px">
    <div style="font-size:1.1rem;font-weight:800;color:#FF8C00">◈ FORM.AI</div>
    <h2 style="color:white;margin:10px 0 0;font-size:1.3rem">{subject}</h2>
  </div>
  <div style="padding:24px 32px;line-height:1.8;color:#333">{message.replace(chr(10),"<br>")}</div>
  <div style="padding:16px 32px;background:#f8f9fa;font-size:.75rem;color:#999;text-align:center">Sent via FORM.AI Admin Panel</div>
</div>'''

    sent_count = 0
    errors = []
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            for u in users:
                if not u or not u.get('email'):
                    continue
                try:
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = subject
                    msg['From'] = from_addr
                    msg['To'] = u['email']
                    msg.attach(MIMEText(html_body, 'html'))
                    s.sendmail(from_addr, u['email'], msg.as_string())
                    sent_count += 1
                except Exception as e:
                    errors.append(str(e))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

    # Save notification record
    notif = {
        'target': target,
        'subject': subject,
        'message': message,
        'sent_by': current_user.id,
        'sent_at': datetime.utcnow(),
        'email_sent': True,
        'sent_count': sent_count
    }
    _db().notifications.insert_one(notif)
    return jsonify({'success': True, 'sent_count': sent_count, 'errors': errors[:5]})

@admin_bp.route('/stats')
@login_required
def stats():
    return jsonify({
        'users': _db().users.count_documents({}),
        'forms': _db().forms.count_documents({}),
        'responses': _db().responses.count_documents({}),
        'newsletters': _db().newsletters.count_documents({}),
    })
