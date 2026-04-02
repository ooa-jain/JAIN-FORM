from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import secrets, smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

newsletter_bp = Blueprint('newsletter', __name__, url_prefix='/newsletter')

def _db():
    from app import db; return db

def _render_blocks_html(blocks, theme):
    """Convert blocks array to HTML string for email."""
    html = ''
    accent = theme.get('accent_color', '#FF8C00')
    for block in blocks:
        c = block.get('content', {})
        t = block.get('type', '')
        if t == 'text':
            html += f'<div style="padding:16px 20px;font-size:15px;line-height:1.7;color:#212529">{c.get("html","")}</div>'
        elif t == 'heading':
            tag = c.get('level','h2')
            html += f'<div style="padding:12px 20px"><{tag} style="font-family:Georgia,serif;margin:0;color:#1A1A2E">{c.get("text","")}</{tag}></div>'
        elif t == 'image' and c.get('url'):
            html += f'<div><img src="{c["url"]}" alt="{c.get("alt","")}" style="width:100%;display:block"></div>'
        elif t == 'video' and c.get('youtube_id'):
            yt = c['youtube_id']
            html += f'<div style="padding:12px 20px"><a href="https://www.youtube.com/watch?v={yt}" style="display:block;text-align:center;background:#000;padding:40px;border-radius:10px;text-decoration:none"><span style="font-size:3rem">▶</span><br><span style="color:white;font-size:.9rem;display:block;margin-top:8px">Watch on YouTube</span></a></div>'
        elif t == 'cta':
            color = c.get('color', accent)
            html += f'<div style="padding:20px;text-align:center"><a href="{c.get("url","#")}" style="display:inline-block;padding:13px 36px;border-radius:10px;background:{color};color:white;font-weight:700;text-decoration:none;font-size:15px">{c.get("text","Click Here")}</a></div>'
        elif t == 'divider':
            html += '<div style="padding:8px 20px"><hr style="border:none;border-top:2px solid #E8E0D5"></div>'
        elif t == 'quote':
            author_html = f'<div style="margin-top:6px;font-size:.8rem;color:#999">— {c["author"]}</div>' if c.get('author') else ''
            html += f'<div style="margin:8px 20px;padding:16px 20px;border-left:4px solid {accent};background:#FFF8F0"><blockquote style="font-family:Georgia,serif;font-size:1.05rem;color:#1A1A2E;margin:0;line-height:1.6">{c.get("text","")}</blockquote>{author_html}</div>'
        elif t == '2col':
            html += f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px 20px"><div style="padding:12px;background:#FAFAFA;border-radius:8px">{c.get("left","")}</div><div style="padding:12px;background:#FAFAFA;border-radius:8px">{c.get("right","")}</div></div>'
        elif t == 'spacer':
            h = c.get('height', 32)
            html += f'<div style="height:{h}px"></div>'
        elif t == 'header':
            bg = c.get('bg', '#1A1A2E')
            color = c.get('color', '#ffffff')
            html += f'<div style="background:{bg};padding:20px;text-align:center"><div style="font-family:Georgia,serif;font-size:1.2rem;font-weight:700;color:{color}">{c.get("text","")}</div></div>'
    return html

@newsletter_bp.route('/')
@login_required
def index():
    newsletters = list(_db().newsletters.find({'user_id': current_user.id}).sort('updated_at', -1))
    return render_template('newsletter/index.html', newsletters=newsletters)

@newsletter_bp.route('/new', methods=['POST'])
@login_required
def new():
    data = request.get_json() or {}
    doc = {
        'user_id': current_user.id,
        'title': data.get('title', 'Untitled Newsletter'),
        'subtitle': '',
        'footer': 'Sent by FORM.AI · Unsubscribe · View in browser',
        'blocks': [],
        'theme': { 'header_color': '#1A1A2E', 'accent_color': '#FF8C00', 'bg_color': '#ffffff' },
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    r = _db().newsletters.insert_one(doc)
    return jsonify({'success': True, 'nl_id': str(r.inserted_id)})

@newsletter_bp.route('/<nl_id>/edit')
@login_required
def edit(nl_id):
    from bson import ObjectId
    try:
        nl = _db().newsletters.find_one({'_id': ObjectId(nl_id), 'user_id': current_user.id})
    except:
        nl = None
    if not nl:
        return redirect(url_for('newsletter.index'))
    nl['_id'] = str(nl['_id'])
    return render_template('newsletter/edit.html', newsletter=nl)

@newsletter_bp.route('/save', methods=['POST'])
@login_required
def save():
    from bson import ObjectId
    data = request.get_json() or {}
    nl_id = data.get('nl_id')
    update = {
        'title': data.get('title', 'Untitled'),
        'subtitle': data.get('subtitle', ''),
        'footer': data.get('footer', ''),
        'blocks': data.get('blocks', []),
        'theme': data.get('theme', {}),
        'updated_at': datetime.utcnow()
    }
    if nl_id and nl_id != 'null':
        try:
            _db().newsletters.update_one({'_id': ObjectId(nl_id), 'user_id': current_user.id}, {'$set': update})
            return jsonify({'success': True, 'nl_id': nl_id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        update['user_id'] = current_user.id
        update['created_at'] = datetime.utcnow()
        r = _db().newsletters.insert_one(update)
        return jsonify({'success': True, 'nl_id': str(r.inserted_id)})

@newsletter_bp.route('/send', methods=['POST'])
@login_required
def send():
    from bson import ObjectId
    data = request.get_json() or {}
    nl_id = data.get('nl_id')
    subject = data.get('subject', 'Newsletter from FORM.AI')
    recipients = data.get('recipients', [])
    preview_text = data.get('preview_text', '')

    if not recipients:
        return jsonify({'success': False, 'error': 'No recipients'})

    try:
        nl = _db().newsletters.find_one({'_id': ObjectId(nl_id), 'user_id': current_user.id})
    except:
        nl = None

    if not nl:
        return jsonify({'success': False, 'error': 'Newsletter not found'})

    theme = nl.get('theme', {})
    hdr_color = theme.get('header_color', '#1A1A2E')
    accent = theme.get('accent_color', '#FF8C00')
    blocks_html = _render_blocks_html(nl.get('blocks', []), theme)

    html_body = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>body{{font-family:'Helvetica Neue',Arial,sans-serif;background:#F0EEF4;margin:0;padding:20px}}
.wrap{{max-width:600px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.1)}}
</style></head><body>
<div class="wrap">
<div style="background:{hdr_color};padding:40px 36px 32px;text-align:center">
<div style="font-size:1rem;color:rgba(255,255,255,.5);margin-bottom:10px;letter-spacing:.15em">◈ FORM.AI</div>
<h1 style="font-family:Georgia,serif;font-size:2rem;color:#fff;margin:0;line-height:1.2">{nl.get("title","Newsletter")}</h1>
{f'<p style="color:rgba(255,255,255,.65);margin-top:10px;font-size:.95rem">{nl.get("subtitle","")}</p>' if nl.get("subtitle") else ""}
</div>
{blocks_html}
<div style="background:#F8F9FA;padding:24px 36px;text-align:center;border-top:1px solid #E0E0E0">
<p style="font-size:.75rem;color:#999;margin:0;line-height:1.8">{nl.get("footer","Sent by FORM.AI")}</p>
</div>
</div>
</body></html>'''

    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_pass = os.getenv('SMTP_PASS', '')
    from_addr = os.getenv('MAIL_FROM', 'noreply@formcraft.ai')

    if not smtp_user or not smtp_pass:
        return jsonify({'success': False, 'error': 'SMTP not configured in .env file. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS.'})

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            for to_addr in recipients:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = from_addr
                msg['To'] = to_addr
                if preview_text:
                    msg.add_header('X-Preview', preview_text)
                msg.attach(MIMEText(html_body, 'html'))
                s.sendmail(from_addr, to_addr, msg.as_string())
        _db().newsletters.update_one({'_id': ObjectId(nl_id)}, {'$set': {'last_sent': datetime.utcnow(), 'send_count': len(recipients)}})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@newsletter_bp.route('/<nl_id>/delete', methods=['POST'])
@login_required
def delete(nl_id):
    from bson import ObjectId
    try:
        _db().newsletters.delete_one({'_id': ObjectId(nl_id), 'user_id': current_user.id})
    except:
        pass
    return redirect(url_for('newsletter.index'))