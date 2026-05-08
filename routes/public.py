from flask import Blueprint, render_template, request, jsonify
import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

public_bp = Blueprint('forms', __name__, url_prefix='/f')

@public_bp.route('/<slug>')
def view(slug):
    from models.form import Form
    form = Form.get_by_slug(slug)
    if not form: return render_template('errors/404.html'), 404
    if not form['settings'].get('is_published', False):
        return render_template('errors/unpublished.html', form=form), 403
    return render_template('forms/view.html', form=form)

@public_bp.route('/<slug>/submit', methods=['POST'])
def submit(slug):
    from models.form import Form
    from models.response import Response
    form = Form.get_by_slug(slug)
    if not form or not form['settings'].get('is_published', False):
        return jsonify({'error': 'Form not available'}), 404
    data = request.get_json()
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    Response.create(str(form['_id']), data, respondent_ip=ip)
    Form.increment_responses(str(form['_id']))

    # Email notification
    if form['settings'].get('notify_on_submit') and form['settings'].get('notify_email'):
        try:
            send_notification(form, data)
        except Exception as e:
            print(f'Email notify failed: {e}')

    return jsonify({
        'success': True,
        'message': form['settings'].get('confirmation_message','Thank you!'),
        'redirect': form['settings'].get('redirect_url','')
    })

def send_notification(form, response_data):
    smtp_host = os.getenv('SMTP_HOST','smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT','587'))
    smtp_user = os.getenv('SMTP_USER','')
    smtp_pass = os.getenv('SMTP_PASS','')
    from_addr = os.getenv('MAIL_FROM','officeofacademicaffairs@jainuniversity.ac.in')
    to_addr   = form['settings']['notify_email']

    if not smtp_user or not smtp_pass:
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'New response: {form["title"]}'
    msg['From']    = from_addr
    msg['To']      = to_addr

    rows = ''
    for page in form.get('pages', []):
        for field in page.get('fields', []):
            if field['type'] in ('header','divider'): continue
            val = response_data.get(field['id'], '—')
            if isinstance(val, list): val = ', '.join(val)
            rows += f'<tr><td style="padding:8px 12px;font-weight:600;color:#555;border-bottom:1px solid #f0f0f0">{field["label"]}</td><td style="padding:8px 12px;border-bottom:1px solid #f0f0f0">{val or "—"}</td></tr>'

    html = f'''
    <div style="font-family:DM Sans,sans-serif;max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08)">
      <div style="background:{form["theme"]["header_color"]};padding:32px 36px">
        <h2 style="color:white;margin:0;font-size:1.4rem">New Response Received</h2>
        <p style="color:rgba(255,255,255,0.7);margin:6px 0 0">{form["title"]}</p>
      </div>
      <div style="padding:24px 36px">
        <table style="width:100%;border-collapse:collapse">{rows}</table>
      </div>
      <div style="padding:16px 36px;background:#f8f9fa;font-size:0.8rem;color:#aaa;text-align:center">
        Sent by FormCraft · {form["title"]}
      </div>
    </div>'''

    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.starttls()
        s.login(smtp_user, smtp_pass)
        s.sendmail(from_addr, to_addr, msg.as_string())
