from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import smtplib, os, re, base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

newsletter_bp = Blueprint('newsletter', __name__, url_prefix='/newsletter')


def _db():
    from app import db; return db


def _smtp_config():
    """Supports SMTP_* and EMAIL_*/MAIL_* naming conventions."""
    host = os.getenv('SMTP_HOST') or os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    port = int(os.getenv('SMTP_PORT') or os.getenv('MAIL_PORT', 587))
    user = os.getenv('SMTP_USER') or os.getenv('EMAIL_USER', '')
    pwd  = os.getenv('SMTP_PASS') or os.getenv('EMAIL_PASS', '')
    frm  = os.getenv('MAIL_FROM', user)
    return host, port, user, pwd, frm


# ─── Base64 helpers ───────────────────────────────────────────────────────────

def _is_base64(value):
    return bool(value and isinstance(value, str) and value.strip().startswith('data:'))


def _extract_b64(data_url):
    """Parse data:mime/type;base64,... → (mime_type, bytes)"""
    if not data_url:
        return None, None
    m = re.match(r'data:([^;]+);base64,(.+)', data_url.strip(), re.DOTALL)
    if not m:
        return None, None
    try:
        return m.group(1), base64.b64decode(m.group(2).strip())
    except Exception:
        return None, None


def _strip_base64_html(html):
    """Remove base64 src= from HTML strings to keep size down."""
    if not html:
        return html
    return re.sub(r'src="data:[^"]*"', 'src=""', html)


def _sanitize_blocks_for_save(blocks):
    """
    Strip base64 image data from blocks before saving to MongoDB.
    Base64 images make the document huge (MB) and cause:
      - Nginx 413 errors on Hostinger
      - MongoDB 16MB document limit errors
      - Slow page loads
    Users should use external image URLs (Unsplash, etc.) for production.
    We keep a flag 'had_base64': True so the UI can warn the user.
    """
    cleaned = []
    for blk in blocks:
        b = dict(blk)
        c = dict(b.get('content', {}))

        # Image / GIF blocks — strip base64 src
        if b.get('type') in ('image', 'gif'):
            if _is_base64(c.get('url', '')):
                c['url'] = ''
                c['_had_base64'] = True  # flag for UI warning

        # Logo in theme — handled separately in theme
        # Text/heading blocks — strip base64 from inline HTML
        if b.get('type') in ('text', 'heading', '2col', 'quote', 'hdr', 'header'):
            for key in ('html', 'text', 'left', 'right'):
                if key in c:
                    c[key] = _strip_base64_html(c[key])

        b['content'] = c
        cleaned.append(b)
    return cleaned


def _sanitize_theme_for_save(theme):
    """Strip base64 from theme (header image, logo)."""
    t = dict(theme)
    if _is_base64(t.get('header_image', '')):
        t['header_image'] = ''
        t['_hdr_had_base64'] = True
    if _is_base64(t.get('logo_url', '')):
        t['logo_url'] = ''
        t['_logo_had_base64'] = True
    return t


# ─── Email builder ────────────────────────────────────────────────────────────

class ImageCollector:
    """Collects images, assigns CIDs, replaces data: URLs with cid: refs."""
    def __init__(self):
        self.attachments = []
        self._cid_map    = {}

    def process(self, url, prefix='img'):
        if not url:
            return ''
        if url.startswith('http://') or url.startswith('https://'):
            return url
        mime_type, img_bytes = _extract_b64(url)
        if not img_bytes:
            return ''
        key = url[:80]
        if key in self._cid_map:
            return f'cid:{self._cid_map[key]}'
        cid = f'{prefix}_{len(self.attachments)}@formcraft'
        self._cid_map[key] = cid
        self.attachments.append((cid, mime_type, img_bytes))
        return f'cid:{cid}'

    def process_html(self, html, prefix='img'):
        if not html:
            return html
        def replacer(m):
            return f'src="{self.process(m.group(1), prefix)}"'
        return re.sub(r'src="(data:[^"]+)"', replacer, html)


def _build_email(nl):
    """Build table-based HTML email with CID inline images."""
    theme      = nl.get('theme', {})
    hdr_color  = theme.get('header_color', '#1A1A2E')
    accent     = theme.get('accent_color', '#FF8C00')
    title      = nl.get('title', 'Newsletter')
    subtitle   = nl.get('subtitle', '')
    footer_txt = nl.get('footer', 'Sent by FORM.AI')
    blocks     = nl.get('blocks', [])

    collector = ImageCollector()

    hdr_img_url = collector.process(theme.get('header_image', ''), 'hdr')
    hdr_bg = (
        f'background-color:{hdr_color};background-image:url("{hdr_img_url}");background-size:cover;background-position:center'
        if hdr_img_url else f'background-color:{hdr_color}'
    )

    logo_url   = collector.process(theme.get('logo_url', ''), 'logo')
    logo_txt   = theme.get('logo_text', '\u25c8 FORM.AI')
    logo_w     = theme.get('logo_width', 140)
    logo_h     = theme.get('logo_height', 50)
    logo_r     = theme.get('logo_radius', 6)
    logo_align = theme.get('logo_align', 'center')
    ta         = logo_align if logo_align in ('left', 'right') else 'center'

    logo_html = (
        f'<img src="{logo_url}" width="{logo_w}" height="{logo_h}" '
        f'style="border-radius:{logo_r}px;display:block;{"margin:0 auto" if ta=="center" else ""}" alt="Logo"><br>'
        if logo_url else
        f'<div style="font-size:13px;color:rgba(255,255,255,.55);letter-spacing:.2em;font-family:Arial,sans-serif;text-align:{ta};margin-bottom:12px">{logo_txt}</div>'
    )

    blocks_rows = ''
    plain_parts = []

    for idx, blk in enumerate(blocks):
        c = blk.get('content', {})
        t = blk.get('type', '')

        if t == 'text':
            raw = collector.process_html(c.get('html', ''), f'txt{idx}')
            plain_parts.append(re.sub(r'<[^>]+>', '', raw).strip() + '\n')
            blocks_rows += f'<tr><td style="padding:14px 28px;font-size:15px;line-height:1.75;color:#212529;font-family:Arial,sans-serif">{raw}</td></tr>\n'

        elif t == 'heading':
            tag     = c.get('level', 'h2')
            fs      = '26px' if tag == 'h1' else '20px' if tag == 'h2' else '16px'
            content = collector.process_html(c.get('text', ''), f'hd{idx}')
            plain_parts.append('\n' + re.sub(r'<[^>]+>', '', content).strip() + '\n')
            blocks_rows += f'<tr><td style="padding:14px 28px"><{tag} style="font-family:Georgia,serif;font-size:{fs};color:#1A1A2E;margin:0;line-height:1.25;font-weight:700">{content}</{tag}></td></tr>\n'

        elif t in ('image', 'gif'):
            raw_url = c.get('url', '')
            img_src = collector.process(raw_url, f'blk{idx}')
            if img_src:
                raw_w = str(c.get('img_width') or c.get('gif_width') or '100%')
                try:
                    num  = float(re.sub(r'[^\d.]', '', raw_w))
                    px_w = int(560 * num / 100) if '%' in raw_w else min(int(num), 560)
                except Exception:
                    px_w = 560
                img_r   = c.get('img_radius', 8)
                img_a   = c.get('img_align') or c.get('gif_align') or 'center'
                align   = img_a if img_a in ('left', 'right') else 'center'
                caption = c.get('caption', '')
                plain_parts.append('[Image]\n' if t == 'image' else '[GIF]\n')
                blocks_rows += (
                    f'<tr><td style="padding:10px 20px" align="{align}">'
                    f'<img src="{img_src}" width="{px_w}" style="display:block;border-radius:{img_r}px;max-width:100%" alt="">'
                    + (f'<p style="font-size:12px;color:#999;text-align:center;margin:6px 0 0;font-family:Arial,sans-serif">{caption}</p>' if caption else '')
                    + '</td></tr>\n'
                )

        elif t == 'video':
            yt_id = c.get('youtube_id', '')
            if yt_id:
                thumb = f'https://img.youtube.com/vi/{yt_id}/hqdefault.jpg'
                url   = f'https://www.youtube.com/watch?v={yt_id}'
                plain_parts.append(f'[Video] {url}\n')
                blocks_rows += (
                    f'<tr><td style="padding:14px 28px">'
                    f'<a href="{url}" style="display:block;text-decoration:none">'
                    f'<img src="{thumb}" width="560" style="display:block;border-radius:10px;max-width:100%" alt="Watch on YouTube">'
                    f'<p style="text-align:center;font-size:13px;color:#999;font-family:Arial,sans-serif;margin:6px 0 0">\u25b6 Watch on YouTube</p>'
                    f'</a></td></tr>\n'
                )

        elif t == 'cta':
            btn_color = c.get('color', accent)
            btn_url   = c.get('url', '#')
            btn_txt   = re.sub(r'<[^>]+>', '', c.get('text', 'Click Here')).strip()
            plain_parts.append(f'\n\u2192 {btn_txt}: {btn_url}\n')
            blocks_rows += (
                f'<tr><td style="padding:20px 28px;text-align:center">'
                f'<a href="{btn_url}" style="display:inline-block;padding:13px 36px;border-radius:8px;background:{btn_color};color:white;font-weight:700;text-decoration:none;font-size:15px;font-family:Arial,sans-serif">{btn_txt}</a>'
                f'</td></tr>\n'
            )

        elif t == 'divider':
            blocks_rows += '<tr><td style="padding:8px 28px"><hr style="border:none;border-top:2px solid #E8E0D5;margin:0"></td></tr>\n'

        elif t == 'quote':
            q_text   = collector.process_html(c.get('text', ''), f'q{idx}')
            q_author = c.get('author', '')
            plain_parts.append(f'"{re.sub(r"<[^>]+>","",q_text).strip()}"' + (f' \u2014 {q_author}' if q_author else '') + '\n')
            author_html = f'<p style="margin:6px 0 0;font-size:12px;color:#999;font-family:Arial,sans-serif">\u2014 {q_author}</p>' if q_author else ''
            blocks_rows += (
                f'<tr><td style="padding:8px 28px">'
                f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
                f'<td style="border-left:4px solid {accent};background:#FFF8F0;padding:14px 18px;border-radius:0 8px 8px 0">'
                f'<blockquote style="font-family:Georgia,serif;font-size:16px;color:#1A1A2E;margin:0;line-height:1.6;font-style:italic">{q_text}</blockquote>'
                f'{author_html}</td></tr></table></td></tr>\n'
            )

        elif t == '2col':
            left  = collector.process_html(c.get('left',  ''), f'l{idx}')
            right = collector.process_html(c.get('right', ''), f'r{idx}')
            blocks_rows += (
                f'<tr><td style="padding:10px 28px">'
                f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
                f'<td width="49%" valign="top" style="background:#FAFAFA;border-radius:8px;padding:12px;font-size:13px;font-family:Arial,sans-serif;line-height:1.6">{left}</td>'
                f'<td width="2%"></td>'
                f'<td width="49%" valign="top" style="background:#FAFAFA;border-radius:8px;padding:12px;font-size:13px;font-family:Arial,sans-serif;line-height:1.6">{right}</td>'
                f'</tr></table></td></tr>\n'
            )

        elif t == 'spacer':
            h = int(c.get('height', 24))
            blocks_rows += f'<tr><td height="{h}" style="font-size:1px;line-height:1px">&nbsp;</td></tr>\n'

        elif t in ('hdr', 'header'):
            bg    = c.get('bg', '#1A1A2E')
            color = c.get('color', '#ffffff')
            txt   = collector.process_html(c.get('text', ''), f'b{idx}')
            plain_parts.append(f'\n[{re.sub(r"<[^>]+>","",txt).strip()}]\n')
            blocks_rows += (
                f'<tr><td style="background:{bg};padding:18px 28px;text-align:center">'
                f'<p style="font-family:Georgia,serif;font-size:18px;font-weight:700;color:{color};margin:0">{txt}</p>'
                f'</td></tr>\n'
            )

    html = f'''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{title}</title></head>
<body style="margin:0;padding:0;background-color:#F0EEF4">
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#F0EEF4" style="background-color:#F0EEF4;padding:24px 0">
<tr><td align="center" style="padding:24px 16px">
<table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;background-color:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10)">
<tr><td style="{hdr_bg};padding:40px 36px 32px;text-align:center">
{logo_html}
<h1 style="font-family:Georgia,serif;font-size:28px;color:#ffffff;margin:0 0 10px;line-height:1.2;font-weight:700">{title}</h1>
{f'<p style="color:rgba(255,255,255,.7);margin:0;font-size:15px;line-height:1.5;font-family:Arial,sans-serif">{subtitle}</p>' if subtitle else ''}
</td></tr>
{blocks_rows}
<tr><td style="background-color:#F8F9FA;padding:20px 32px;text-align:center;border-top:1px solid #E0E0E0">
<p style="font-size:11px;color:#999999;margin:0;line-height:1.8;font-family:Arial,sans-serif">{footer_txt}</p>
<p style="font-size:10px;color:#cccccc;margin:6px 0 0;font-family:Arial,sans-serif">Sent via \u25c8 FORM.AI</p>
</td></tr>
</table></td></tr></table>
</body></html>'''

    plain = f'{title}\n{"=" * min(len(title),60)}\n'
    if subtitle:
        plain += f'{subtitle}\n'
    plain += '\n' + '\n'.join(plain_parts) + f'\n\n---\n{footer_txt}\n'

    size_kb = len(html.encode('utf-8')) / 1024
    print(f'📧 Email HTML: {size_kb:.1f}KB | CID images: {len(collector.attachments)}')

    return html, plain, collector.attachments


# ─── Routes ───────────────────────────────────────────────────────────────────

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
        'user_id':    current_user.id,
        'title':      data.get('title', 'Untitled Newsletter'),
        'subtitle':   '',
        'footer':     'Sent by FORM.AI \xb7 Unsubscribe',
        'blocks':     [],
        'theme':      {'header_color': '#1A1A2E', 'accent_color': '#FF8C00'},
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
    except Exception:
        nl = None
    if not nl:
        return redirect(url_for('newsletter.index'))
    nl['_id'] = str(nl['_id'])
    return render_template('newsletter/edit.html', newsletter=nl)


@newsletter_bp.route('/save', methods=['POST'])
@login_required
def save():
    from bson import ObjectId

    # Handle JSON parse errors gracefully
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid JSON — payload may be too large. Use external image URLs.'}), 400

    nl_id  = data.get('nl_id')
    blocks = data.get('blocks', [])
    theme  = data.get('theme', {})

    # ── Strip base64 before saving — THIS FIXES THE 413/SAVE FAILED ──
    clean_blocks = _sanitize_blocks_for_save(blocks)
    clean_theme  = _sanitize_theme_for_save(theme)

    # Warn if base64 was stripped
    had_b64 = (
        any(b.get('content', {}).get('_had_base64') for b in clean_blocks) or
        clean_theme.get('_hdr_had_base64') or
        clean_theme.get('_logo_had_base64')
    )

    update = {
        'title':      data.get('title', 'Untitled'),
        'subtitle':   data.get('subtitle', ''),
        'footer':     data.get('footer', ''),
        'blocks':     clean_blocks,
        'theme':      clean_theme,
        'updated_at': datetime.utcnow()
    }

    warning = ('⚠ Uploaded images were removed to save space. Use external image URLs (e.g. from Unsplash or your server) for images to persist.'
               if had_b64 else None)

    if nl_id and nl_id != 'null':
        try:
            _db().newsletters.update_one(
                {'_id': ObjectId(nl_id), 'user_id': current_user.id},
                {'$set': update}
            )
            return jsonify({'success': True, 'nl_id': nl_id, 'warning': warning})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        update['user_id']    = current_user.id
        update['created_at'] = datetime.utcnow()
        try:
            r = _db().newsletters.insert_one(update)
            return jsonify({'success': True, 'nl_id': str(r.inserted_id), 'warning': warning})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})


@newsletter_bp.route('/send', methods=['POST'])
@login_required
def send():
    from bson import ObjectId
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    nl_id        = data.get('nl_id')
    subject      = data.get('subject', 'Newsletter from FORM.AI')
    recipients   = data.get('recipients', [])
    preview_text = data.get('preview_text', '')

    if not recipients:
        return jsonify({'success': False, 'error': 'No recipients provided.'})

    try:
        nl = _db().newsletters.find_one({'_id': ObjectId(nl_id), 'user_id': current_user.id})
    except Exception:
        nl = None
    if not nl:
        return jsonify({'success': False, 'error': 'Newsletter not found.'})

    smtp_host, smtp_port, smtp_user, smtp_pass, from_addr = _smtp_config()
    if not smtp_user or not smtp_pass:
        return jsonify({'success': False, 'error': 'SMTP not configured. Check .env: SMTP_USER + SMTP_PASS.'})

    try:
        html_body, plain_body, image_attachments = _build_email(nl)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Email build error: {str(e)}'})

    if preview_text:
        preheader = f'<div style="display:none;max-height:0;overflow:hidden;font-size:1px;color:transparent">{preview_text}{"&nbsp;"*80}</div>'
        html_body = html_body.replace('<body', f'<body>\n{preheader}', 1)

    sent_count = 0
    errors     = []

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as s:
            s.ehlo(); s.starttls(); s.ehlo()
            s.login(smtp_user, smtp_pass)

            for to_addr in recipients:
                if not to_addr or '@' not in to_addr:
                    continue
                try:
                    if image_attachments:
                        outer = MIMEMultipart('mixed')
                        outer['Subject'] = subject
                        outer['From']    = f'FORM.AI <{from_addr}>'
                        outer['To']      = to_addr
                        alt     = MIMEMultipart('alternative')
                        related = MIMEMultipart('related')
                        alt.attach(MIMEText(plain_body, 'plain', 'utf-8'))
                        related.attach(MIMEText(html_body, 'html', 'utf-8'))
                        for cid, mime_type, img_bytes in image_attachments:
                            img_part = MIMEImage(img_bytes, _subtype=mime_type.split('/')[-1])
                            img_part.add_header('Content-ID', f'<{cid}>')
                            img_part.add_header('Content-Disposition', 'inline')
                            related.attach(img_part)
                        alt.attach(related)
                        outer.attach(alt)
                        msg = outer
                    else:
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = subject
                        msg['From']    = f'FORM.AI <{from_addr}>'
                        msg['To']      = to_addr
                        msg.attach(MIMEText(plain_body, 'plain', 'utf-8'))
                        msg.attach(MIMEText(html_body,  'html',  'utf-8'))

                    s.sendmail(from_addr, to_addr, msg.as_string())
                    sent_count += 1
                except Exception as e:
                    errors.append(f'{to_addr}: {str(e)}')

    except smtplib.SMTPAuthenticationError:
        return jsonify({'success': False, 'error': 'Gmail auth failed. Use an App Password: Google Account → Security → 2-Step Verification → App passwords.'})
    except smtplib.SMTPException as e:
        return jsonify({'success': False, 'error': f'SMTP error: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

    _db().newsletters.update_one(
        {'_id': ObjectId(nl_id)},
        {'$set': {'last_sent': datetime.utcnow(), 'send_count': sent_count}}
    )

    if sent_count == 0 and errors:
        return jsonify({'success': False, 'error': errors[0]})

    return jsonify({'success': True, 'sent_count': sent_count, 'errors': errors[:3]})


@newsletter_bp.route('/<nl_id>/delete', methods=['POST'])
@login_required
def delete(nl_id):
    from bson import ObjectId
    try:
        _db().newsletters.delete_one({'_id': ObjectId(nl_id), 'user_id': current_user.id})
    except Exception:
        pass
    return redirect(url_for('newsletter.index'))