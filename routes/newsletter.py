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


# ─── Image helpers ────────────────────────────────────────────────────────────

def _extract_b64(data_url):
    """
    Parse a data: URL into (mime_type, raw_bytes).
    Returns (None, None) if not a data URL.
    """
    if not data_url or not data_url.strip().startswith('data:'):
        return None, None
    m = re.match(r'data:([^;]+);base64,(.+)', data_url.strip(), re.DOTALL)
    if not m:
        return None, None
    try:
        return m.group(1), base64.b64decode(m.group(2).strip())
    except Exception:
        return None, None


def _is_external_url(url):
    return url and (url.startswith('http://') or url.startswith('https://'))


class ImageCollector:
    """
    Collects all images from blocks/theme, assigns CIDs,
    and replaces data: URLs with cid: references in the HTML.
    External URLs are kept as-is.
    """
    def __init__(self):
        self.attachments = []   # list of (cid, mime_type, bytes)
        self._cid_map    = {}   # data_url_hash -> cid

    def process(self, url, prefix='img'):
        """
        Given a URL (data: or https://), return the src to use in HTML.
        data: → attach + return cid:xxx
        https: → return as-is
        empty → return ''
        """
        if not url:
            return ''
        if _is_external_url(url):
            return url
        mime_type, img_bytes = _extract_b64(url)
        if not img_bytes:
            return ''
        # Deduplicate by checking first 100 chars of data URL
        key = url[:100]
        if key in self._cid_map:
            return f'cid:{self._cid_map[key]}'
        cid = f'{prefix}_{len(self.attachments)}@formcraft'
        self._cid_map[key] = cid
        self.attachments.append((cid, mime_type, img_bytes))
        return f'cid:{cid}'

    def process_html(self, html, prefix='img'):
        """Replace data: src= values in an HTML string with cid: references."""
        if not html:
            return html
        def replacer(m):
            data_url = m.group(1)
            src = self.process(data_url, prefix)
            return f'src="{src}"'
        return re.sub(r'src="(data:[^"]+)"', replacer, html)


# ─── Email builder ────────────────────────────────────────────────────────────

def _build_email(nl):
    """
    Build a table-based HTML email with all images attached inline (CID).
    Returns (html_str, plain_str, [(cid, mime_type, bytes), ...])
    """
    theme      = nl.get('theme', {})
    hdr_color  = theme.get('header_color', '#1A1A2E')
    accent     = theme.get('accent_color', '#FF8C00')
    title      = nl.get('title', 'Newsletter')
    subtitle   = nl.get('subtitle', '')
    footer_txt = nl.get('footer', 'Sent by FORM.AI')
    blocks     = nl.get('blocks', [])

    collector = ImageCollector()

    # ── Header image ──
    hdr_img_url = collector.process(theme.get('header_image', ''), 'hdr')
    if hdr_img_url:
        hdr_bg = (
            f'background-color:{hdr_color};'
            f'background-image:url("{hdr_img_url}");'
            f'background-size:cover;background-position:center'
        )
    else:
        hdr_bg = f'background-color:{hdr_color}'

    # ── Logo ──
    logo_raw   = theme.get('logo_url', '')
    logo_url   = collector.process(logo_raw, 'logo')
    logo_txt   = theme.get('logo_text', '\u25c8 FORM.AI')
    logo_w     = theme.get('logo_width', 140)
    logo_h     = theme.get('logo_height', 50)
    logo_r     = theme.get('logo_radius', 6)
    logo_align = theme.get('logo_align', 'center')
    ta         = logo_align if logo_align in ('left', 'right') else 'center'

    if logo_url:
        logo_html = (
            f'<img src="{logo_url}" width="{logo_w}" height="{logo_h}" '
            f'style="border-radius:{logo_r}px;display:block;{"margin:0 auto" if ta=="center" else ""}" '
            f'alt="Logo"><br>'
        )
    else:
        logo_html = (
            f'<div style="font-size:13px;color:rgba(255,255,255,.55);letter-spacing:.2em;'
            f'font-family:Arial,sans-serif;text-align:{ta};margin-bottom:12px">{logo_txt}</div>'
        )

    # ── Blocks ──
    blocks_rows = ''
    plain_parts = []

    for idx, blk in enumerate(blocks):
        c = blk.get('content', {})
        t = blk.get('type', '')

        if t == 'text':
            raw = collector.process_html(c.get('html', ''), f'txt{idx}')
            plain_parts.append(re.sub(r'<[^>]+>', '', raw).strip() + '\n')
            blocks_rows += (
                f'<tr><td style="padding:14px 28px;font-size:15px;line-height:1.75;'
                f'color:#212529;font-family:Arial,sans-serif">{raw}</td></tr>\n'
            )

        elif t == 'heading':
            tag     = c.get('level', 'h2')
            fs      = '26px' if tag == 'h1' else '20px' if tag == 'h2' else '16px'
            content = collector.process_html(c.get('text', ''), f'hd{idx}')
            plain_parts.append('\n' + re.sub(r'<[^>]+>', '', content).strip() + '\n')
            blocks_rows += (
                f'<tr><td style="padding:14px 28px">'
                f'<{tag} style="font-family:Georgia,serif;font-size:{fs};color:#1A1A2E;'
                f'margin:0;line-height:1.25;font-weight:700">{content}</{tag}>'
                f'</td></tr>\n'
            )

        elif t == 'image':
            raw_url = c.get('url', '')
            img_src = collector.process(raw_url, f'blk{idx}')
            if img_src:
                raw_w = str(c.get('img_width', '100%'))
                try:
                    num  = float(re.sub(r'[^\d.]', '', raw_w))
                    px_w = int(560 * num / 100) if '%' in raw_w else min(int(num), 560)
                except Exception:
                    px_w = 560
                img_r   = c.get('img_radius', 8)
                img_a   = c.get('img_align', 'center')
                align   = img_a if img_a in ('left', 'right') else 'center'
                caption = c.get('caption', '')
                plain_parts.append('[Image]\n')
                blocks_rows += (
                    f'<tr><td style="padding:10px 20px" align="{align}">'
                    f'<img src="{img_src}" width="{px_w}" '
                    f'style="display:block;border-radius:{img_r}px;max-width:100%" alt="{c.get("alt","")}">'
                    + (f'<p style="font-size:12px;color:#999;text-align:center;margin:6px 0 0;font-family:Arial,sans-serif">{caption}</p>' if caption else '')
                    + '</td></tr>\n'
                )

        elif t == 'video':
            yt_id = c.get('youtube_id', '')
            if yt_id:
                # Use YouTube thumbnail as clickable image
                thumb = f'https://img.youtube.com/vi/{yt_id}/hqdefault.jpg'
                url   = f'https://www.youtube.com/watch?v={yt_id}'
                plain_parts.append(f'[Video] {url}\n')
                blocks_rows += (
                    f'<tr><td style="padding:14px 28px">'
                    f'<a href="{url}" style="display:block;text-decoration:none">'
                    f'<img src="{thumb}" width="560" '
                    f'style="display:block;border-radius:10px;max-width:100%" alt="Watch on YouTube">'
                    f'<p style="text-align:center;font-size:13px;color:#999;'
                    f'font-family:Arial,sans-serif;margin:6px 0 0">\u25b6 Watch on YouTube</p>'
                    f'</a></td></tr>\n'
                )

        elif t == 'cta':
            btn_color = c.get('color', accent)
            btn_url   = c.get('url', '#')
            btn_txt   = re.sub(r'<[^>]+>', '', c.get('text', 'Click Here')).strip()
            plain_parts.append(f'\n\u2192 {btn_txt}: {btn_url}\n')
            blocks_rows += (
                f'<tr><td style="padding:20px 28px;text-align:center">'
                f'<a href="{btn_url}" style="display:inline-block;padding:13px 36px;'
                f'border-radius:8px;background:{btn_color};color:white;font-weight:700;'
                f'text-decoration:none;font-size:15px;font-family:Arial,sans-serif">{btn_txt}</a>'
                f'</td></tr>\n'
            )

        elif t == 'divider':
            blocks_rows += (
                '<tr><td style="padding:8px 28px">'
                '<hr style="border:none;border-top:2px solid #E8E0D5;margin:0">'
                '</td></tr>\n'
            )

        elif t == 'quote':
            q_text   = collector.process_html(c.get('text', ''), f'q{idx}')
            q_author = c.get('author', '')
            plain_q  = re.sub(r'<[^>]+>', '', q_text).strip()
            plain_parts.append(f'"{plain_q}"' + (f' \u2014 {q_author}' if q_author else '') + '\n')
            author_html = (
                f'<p style="margin:6px 0 0;font-size:12px;color:#999;font-family:Arial,sans-serif">'
                f'\u2014 {q_author}</p>' if q_author else ''
            )
            blocks_rows += (
                f'<tr><td style="padding:8px 28px">'
                f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
                f'<td style="border-left:4px solid {accent};background:#FFF8F0;'
                f'padding:14px 18px;border-radius:0 8px 8px 0">'
                f'<blockquote style="font-family:Georgia,serif;font-size:16px;color:#1A1A2E;'
                f'margin:0;line-height:1.6;font-style:italic">{q_text}</blockquote>'
                f'{author_html}</td></tr></table></td></tr>\n'
            )

        elif t == '2col':
            left  = collector.process_html(c.get('left', ''),  f'l{idx}')
            right = collector.process_html(c.get('right', ''), f'r{idx}')
            blocks_rows += (
                f'<tr><td style="padding:10px 28px">'
                f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
                f'<td width="49%" valign="top" style="background:#FAFAFA;border-radius:8px;'
                f'padding:12px;font-size:13px;font-family:Arial,sans-serif;line-height:1.6">{left}</td>'
                f'<td width="2%"></td>'
                f'<td width="49%" valign="top" style="background:#FAFAFA;border-radius:8px;'
                f'padding:12px;font-size:13px;font-family:Arial,sans-serif;line-height:1.6">{right}</td>'
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
                f'<p style="font-family:Georgia,serif;font-size:18px;font-weight:700;'
                f'color:{color};margin:0">{txt}</p></td></tr>\n'
            )

    # ── Final HTML ──
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background-color:#F0EEF4">
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#F0EEF4"
  style="background-color:#F0EEF4;padding:24px 0">
<tr><td align="center" style="padding:24px 16px">

<table width="600" cellpadding="0" cellspacing="0" border="0"
  style="max-width:600px;width:100%;background-color:#ffffff;border-radius:14px;
         overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10)">

  <!-- HEADER -->
  <tr><td style="{hdr_bg};padding:40px 36px 32px;text-align:center">
    {logo_html}
    <h1 style="font-family:Georgia,serif;font-size:28px;color:#ffffff;
      margin:0 0 10px;line-height:1.2;font-weight:700">{title}</h1>
    {f'<p style="color:rgba(255,255,255,.7);margin:0;font-size:15px;line-height:1.5;font-family:Arial,sans-serif">{subtitle}</p>' if subtitle else ''}
  </td></tr>

  <!-- CONTENT BLOCKS -->
  {blocks_rows}

  <!-- FOOTER -->
  <tr><td style="background-color:#F8F9FA;padding:20px 32px;text-align:center;border-top:1px solid #E0E0E0">
    <p style="font-size:11px;color:#999999;margin:0;line-height:1.8;font-family:Arial,sans-serif">{footer_txt}</p>
    <p style="font-size:10px;color:#cccccc;margin:6px 0 0;font-family:Arial,sans-serif">Sent via \u25c8 FORM.AI</p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>'''

    # ── Plain text ──
    plain = f'{title}\n{"=" * min(len(title), 60)}\n'
    if subtitle:
        plain += f'{subtitle}\n'
    plain += '\n' + '\n'.join(plain_parts) + f'\n\n---\n{footer_txt}\n'

    size_kb = len(html.encode('utf-8')) / 1024
    print(f'📧 HTML size: {size_kb:.1f} KB | Images attached: {len(collector.attachments)}')

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
        'footer':     'Sent by FORM.AI \xb7 Unsubscribe \xb7 View in browser',
        'blocks':     [],
        'theme':      {'header_color': '#1A1A2E', 'accent_color': '#FF8C00', 'bg_color': '#ffffff'},
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
    data  = request.get_json() or {}
    nl_id = data.get('nl_id')
    update = {
        'title':      data.get('title', 'Untitled'),
        'subtitle':   data.get('subtitle', ''),
        'footer':     data.get('footer', ''),
        'blocks':     data.get('blocks', []),
        'theme':      data.get('theme', {}),
        'updated_at': datetime.utcnow()
    }
    if nl_id and nl_id != 'null':
        try:
            _db().newsletters.update_one(
                {'_id': ObjectId(nl_id), 'user_id': current_user.id},
                {'$set': update}
            )
            return jsonify({'success': True, 'nl_id': nl_id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        update['user_id']    = current_user.id
        update['created_at'] = datetime.utcnow()
        r = _db().newsletters.insert_one(update)
        return jsonify({'success': True, 'nl_id': str(r.inserted_id)})


@newsletter_bp.route('/send', methods=['POST'])
@login_required
def send():
    from bson import ObjectId
    data         = request.get_json() or {}
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
        return jsonify({
            'success': False,
            'error': 'SMTP not configured. Check .env: SMTP_USER + SMTP_PASS (or EMAIL_USER + EMAIL_PASS).'
        })

    try:
        html_body, plain_body, image_attachments = _build_email(nl)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Build error: {str(e)}'})

    # Preview text hidden preheader
    if preview_text:
        preheader = (
            f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;'
            f'font-size:1px;color:transparent">{preview_text}{"&nbsp;" * 80}</div>'
        )
        html_body = html_body.replace('<body', f'<body>\n{preheader}', 1)

    sent_count = 0
    errors     = []

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(smtp_user, smtp_pass)

            for to_addr in recipients:
                if not to_addr or '@' not in to_addr:
                    continue
                try:
                    if image_attachments:
                        # ── multipart/related wraps HTML + inline images ──
                        outer = MIMEMultipart('mixed')
                        outer['Subject'] = subject
                        outer['From']    = f'FORM.AI <{from_addr}>'
                        outer['To']      = to_addr

                        # alternative part: plain + html
                        alt = MIMEMultipart('alternative')
                        alt.attach(MIMEText(plain_body, 'plain', 'utf-8'))

                        # related: html + cid images
                        related = MIMEMultipart('related')
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
                        # ── no inline images — simple alternative ──
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
        return jsonify({
            'success': False,
            'error': (
                'Gmail auth failed. Use an App Password: '
                'Google Account \u2192 Security \u2192 2-Step Verification \u2192 App passwords.'
            )
        })
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