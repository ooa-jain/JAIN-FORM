<<<<<<< HEAD
"""
routes/newsletter.py  —  FORM.AI Newsletter System  v4
"""
from flask import (Blueprint, render_template, request, jsonify,
                   redirect, url_for, Response)
=======
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_from_directory
>>>>>>> 9ea1a66fec365df468b76099a79796cc7c3ae0ce
from flask_login import login_required, current_user
from datetime import datetime
import smtplib, os, re, base64, uuid, mimetypes
from email.mime.multipart import MIMEMultipart
<<<<<<< HEAD
from email.mime.text      import MIMEText
from email.mime.image     import MIMEImage

newsletter_bp = Blueprint('newsletter', __name__, url_prefix='/newsletter')

# ── helpers ───────────────────────────────────────────────────────────────────
def _upload_dir():
    try:
        from flask import current_app; base = current_app.root_path
    except RuntimeError:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(base, 'static', 'nl_uploads')
    os.makedirs(d, exist_ok=True); return d
=======
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

newsletter_bp = Blueprint('newsletter', __name__, url_prefix='/newsletter')

# ── GIF / image upload folder ─────────────────────────────────────────────────
# Files saved here become /newsletter/uploads/<filename> — permanent URLs
def _upload_dir():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d    = os.path.join(base, 'static', 'nl_uploads')
    os.makedirs(d, exist_ok=True)
    return d

>>>>>>> 9ea1a66fec365df468b76099a79796cc7c3ae0ce

def _db():
    from app import db; return db

<<<<<<< HEAD
def _smtp():
    h = os.getenv('SMTP_HOST') or os.getenv('MAIL_SERVER','smtp.gmail.com')
    p = int(os.getenv('SMTP_PORT') or os.getenv('MAIL_PORT',587))
    u = os.getenv('SMTP_USER') or os.getenv('EMAIL_USER','')
    w = os.getenv('SMTP_PASS') or os.getenv('EMAIL_PASS','')
    f = os.getenv('MAIL_FROM', u)
    return h, p, u, w, f

# ── image helpers ─────────────────────────────────────────────────────────────
def _is_b64(v):
    return bool(v and isinstance(v,str) and v.strip().startswith('data:'))

def _extract_b64(du):
    if not du: return None, None
    m = re.match(r'data:([^;]+);base64,(.+)', du.strip(), re.DOTALL)
    if not m: return None, None
    try:    return m.group(1), base64.b64decode(m.group(2).strip())
    except: return None, None

def _strip_b64_html(html):
    return re.sub(r'src="data:[^"]*"','src=""',html) if html else html

def _b64_to_file(du, prefix='upload'):
    mime, bts = _extract_b64(du)
    if not bts: return None
    ext = {'image/gif':'.gif','image/png':'.png','image/jpeg':'.jpg',
           'image/jpg':'.jpg','image/webp':'.webp'}.get(
           mime, mimetypes.guess_extension(mime) or '.bin')
    fn = f'{prefix}_{uuid.uuid4().hex}{ext}'
    try:
        with open(os.path.join(_upload_dir(),fn),'wb') as f: f.write(bts)
        return f'/static/nl_uploads/{fn}'
    except Exception as e:
        print(f'[nl_upload] {e}'); return None

def _sanitize_blocks(blocks):
    out = []
    for blk in blocks:
        b = dict(blk); c = dict(b.get('content',{}))
        if b.get('type') in ('image','gif'):
            u = c.get('url','')
            if _is_b64(u):
                s = _b64_to_file(u, b['type'])
                c['url'] = s or ''; c.setdefault('_upload_failed', not s)
        if b.get('type') in ('text','heading','2col','quote','hdr','header'):
            for k in ('html','text','left','right'):
                if k in c: c[k] = _strip_b64_html(c[k])
        b['content'] = c; out.append(b)
    return out

def _sanitize_theme(theme):
    t = dict(theme)
    for k,l in [('header_image','hdr'),('logo_url','logo')]:
        if _is_b64(t.get(k,'')):
            s = _b64_to_file(t[k],l); t[k] = s or ''
    return t

def _serialize_nl(nl):
    nl['_id'] = str(nl['_id'])
    for k in ('created_at','updated_at','last_sent'):
        if isinstance(nl.get(k), datetime): nl[k] = nl[k].isoformat()
    return nl

# ── image collector for email ─────────────────────────────────────────────────
class _ImgC:
    def __init__(self): self._m={}; self.atts=[]
    def process(self, url, pfx='img'):
        if not url: return ''
        if url.startswith(('http://','https://')): return url
        if url.startswith('/static/'):
            try:
                from flask import current_app
                fp = os.path.join(current_app.root_path, url.lstrip('/'))
            except RuntimeError:
                fp = os.path.join(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__))), url.lstrip('/'))
            if os.path.exists(fp):
                if url in self._m: return f'cid:{self._m[url]}'
                cid=f'{pfx}_{len(self.atts)}@formcraft'; self._m[url]=cid
                mt=mimetypes.guess_type(fp)[0] or 'image/png'
                with open(fp,'rb') as f: self.atts.append((cid,mt,f.read()))
                return f'cid:{cid}'
        mime,bts=_extract_b64(url)
        if not bts: return ''
        key=url[:80]
        if key in self._m: return f'cid:{self._m[key]}'
        cid=f'{pfx}_{len(self.atts)}@formcraft'; self._m[key]=cid
        self.atts.append((cid,mime or 'image/png',bts)); return f'cid:{cid}'
    def html(self, h, pfx='img'):
        if not h: return h
        return re.sub(r'src="(data:[^"]+|/static/[^"]+)"',
                      lambda m:f'src="{self.process(m.group(1),pfx)}"', h)

# ── email builder ─────────────────────────────────────────────────────────────
def _build_email(nl):
    th=nl.get('theme',{}); acc=th.get('accent_color','#FF8C00')
    title=nl.get('title','Newsletter'); subtitle=nl.get('subtitle','')
    footer=nl.get('footer','Sent by FORM.AI'); blocks=nl.get('blocks',[])
    col=_ImgC()
    hi=col.process(th.get('header_image',''),'hdr')
    hbg=(f"background:{th.get('header_color','#1A1A2E')};background-image:url('{hi}');background-size:cover;background-position:center" if hi else f"background:{th.get('header_color','#1A1A2E')}")
    lu=col.process(th.get('logo_url',''),'logo')
    lt=th.get('logo_text','◈ FORM.AI'); lw=th.get('logo_width',140)
    lh=th.get('logo_height',50); lr=th.get('logo_radius',6)
    ta=th.get('logo_align','center')
    logo=(f'<img src="{lu}" width="{lw}" height="{lh}" style="border-radius:{lr}px;display:block;{"margin:0 auto" if ta=="center" else ""}" alt="Logo"><br>' if lu else f'<div style="font-size:13px;color:rgba(255,255,255,.55);letter-spacing:.2em;font-family:Arial,sans-serif;text-align:{ta};margin-bottom:12px">{lt}</div>')
    rows=''; pp=[]
    for i,blk in enumerate(blocks):
        c=blk.get('content',{}); t=blk.get('type','')
        if t=='text':
            r=col.html(c.get('html',''),f't{i}'); pp.append(re.sub(r'<[^>]+>','',r).strip())
            rows+=f'<tr><td style="padding:14px 28px;font-size:15px;line-height:1.75;color:#212529;font-family:Arial,sans-serif">{r}</td></tr>\n'
        elif t=='heading':
            lvl=c.get('level','h2'); fs={'h1':'26px','h2':'20px','h3':'16px'}.get(lvl,'20px')
            txt=col.html(c.get('text',''),f'h{i}'); pp.append('\n'+re.sub(r'<[^>]+>','',txt).strip())
            rows+=f'<tr><td style="padding:14px 28px"><{lvl} style="font-family:Georgia,serif;font-size:{fs};color:#1A1A2E;margin:0;line-height:1.25;font-weight:700">{txt}</{lvl}></td></tr>\n'
        elif t in ('image','gif'):
            src=col.process(c.get('url',''),f'img{i}')
            if src:
                rw=str(c.get('img_width') or c.get('gif_width') or '100%')
                try: n=float(re.sub(r'[^\d.]','',rw)); pw=int(560*n/100) if '%' in rw else min(int(n),560)
                except: pw=560
                al=c.get('img_align') or c.get('gif_align') or 'center'
                cap=c.get('caption','')
                pp.append(f'[{"GIF" if t=="gif" else "Image"}]')
                rows+=(f'<tr><td style="padding:10px 20px" align="{al}"><img src="{src}" width="{pw}" style="display:block;border-radius:{c.get("img_radius",8)}px;max-width:100%" alt="">'
                       +(f'<p style="font-size:12px;color:#999;text-align:center;margin:6px 0 0;font-family:Arial,sans-serif">{cap}</p>' if cap else '')
                       +'</td></tr>\n')
        elif t=='video':
            yt=c.get('youtube_id','')
            if yt:
                pp.append(f'[Video] https://www.youtube.com/watch?v={yt}')
                rows+=(f'<tr><td style="padding:14px 28px"><a href="https://www.youtube.com/watch?v={yt}" style="display:block;text-decoration:none"><img src="https://img.youtube.com/vi/{yt}/hqdefault.jpg" width="560" style="display:block;border-radius:10px;max-width:100%" alt="Watch on YouTube"><p style="text-align:center;font-size:13px;color:#999;font-family:Arial,sans-serif;margin:6px 0 0">▶ Watch on YouTube</p></a></td></tr>\n')
        elif t=='cta':
            bt=re.sub(r'<[^>]+>','',c.get('text','Click Here')).strip(); bu=c.get('url','#'); bc=c.get('color',acc)
            pp.append(f'→ {bt}: {bu}')
            rows+=f'<tr><td style="padding:20px 28px;text-align:center"><a href="{bu}" style="display:inline-block;padding:13px 36px;border-radius:8px;background:{bc};color:white;font-weight:700;text-decoration:none;font-size:15px;font-family:Arial,sans-serif">{bt}</a></td></tr>\n'
        elif t=='divider':
            rows+='<tr><td style="padding:8px 28px"><hr style="border:none;border-top:2px solid #E8E0D5;margin:0"></td></tr>\n'
        elif t=='quote':
            qt=col.html(c.get('text',''),f'q{i}'); auth=c.get('author','')
            pp.append(f'"{re.sub(r"<[^>]+>","",qt).strip()}"'+(f' — {auth}' if auth else ''))
            rows+=(f'<tr><td style="padding:8px 28px"><table width="100%" cellpadding="0" cellspacing="0"><tr><td style="border-left:4px solid {acc};background:#FFF8F0;padding:14px 18px;border-radius:0 8px 8px 0"><blockquote style="font-family:Georgia,serif;font-size:16px;color:#1A1A2E;margin:0;line-height:1.6;font-style:italic">{qt}</blockquote>'
                   +(f'<p style="margin:6px 0 0;font-size:12px;color:#999;font-family:Arial,sans-serif">— {auth}</p>' if auth else '')
                   +'</td></tr></table></td></tr>\n')
        elif t=='2col':
            l=col.html(c.get('left',''),f'l{i}'); r2=col.html(c.get('right',''),f'r{i}')
            rows+=(f'<tr><td style="padding:10px 28px"><table width="100%" cellpadding="0" cellspacing="0"><tr><td width="49%" valign="top" style="background:#FAFAFA;border-radius:8px;padding:12px;font-size:13px;font-family:Arial,sans-serif;line-height:1.6">{l}</td><td width="2%"></td><td width="49%" valign="top" style="background:#FAFAFA;border-radius:8px;padding:12px;font-size:13px;font-family:Arial,sans-serif;line-height:1.6">{r2}</td></tr></table></td></tr>\n')
        elif t=='spacer':
            h=int(c.get('height',24)); rows+=f'<tr><td height="{h}" style="font-size:1px;line-height:1px">&nbsp;</td></tr>\n'
        elif t in ('hdr','header'):
            bg=c.get('bg','#1A1A2E'); color=c.get('color','#ffffff'); txt=col.html(c.get('text',''),f'b{i}')
            rows+=f'<tr><td style="background:{bg};padding:18px 28px;text-align:center"><p style="font-family:Georgia,serif;font-size:18px;font-weight:700;color:{color};margin:0">{txt}</p></td></tr>\n'
        elif t=='social':
            btns=''.join(f'<a href="{lk.get("url","#")}" style="display:inline-block;margin:0 6px;padding:8px 16px;border-radius:6px;background:#F0EEF4;color:#1A1A2E;text-decoration:none;font-size:13px;font-family:Arial,sans-serif">{lk.get("icon","🔗")} {lk.get("name","")}</a>' for lk in c.get('links',[]))
            if btns: rows+=f'<tr><td style="padding:14px 28px;text-align:center">{btns}</td></tr>\n'

    hdr_color = th.get('header_color', '#1A1A2E')
    # Clean hbg: remove any double quotes that would break style="..." attribute
    hbg_clean = hbg.replace('"', "'")
    sub_row = (f'<p style="color:rgba(255,255,255,.7);margin:0;font-size:15px;'
               f'line-height:1.5;font-family:Arial,sans-serif">{subtitle}</p>'
               if subtitle else '')
    html = (
        '<!DOCTYPE html>'
        '<html lang="en">'
        '<head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        '<title>' + title + '</title>'
        '</head>'
        '<body style="margin:0;padding:0;background:#F0EEF4">'
        '<table width="100%" cellpadding="0" cellspacing="0" border="0"'
        ' bgcolor="#F0EEF4" style="background:#F0EEF4;padding:24px 0">'
        '<tr><td align="center" style="padding:24px 16px">'
        '<table width="600" cellpadding="0" cellspacing="0" border="0"'
        ' style="max-width:600px;width:100%;background:#ffffff;'
        'border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10)">'
        '<tr><td bgcolor="' + hdr_color + '" style="' + hbg_clean + ';padding:36px 32px 28px;text-align:center">'
        + logo
        + '<h1 style="font-family:Georgia,serif;font-size:28px;color:#ffffff;'
          'margin:0 0 10px;line-height:1.2;font-weight:700">' + title + '</h1>'
        + sub_row
        + '</td></tr>'
        + rows
        + '<tr><td style="background:#F8F9FA;padding:20px 32px;text-align:center;border-top:1px solid #E0E0E0">'
          '<p style="font-size:11px;color:#999;margin:0;line-height:1.8;font-family:Arial,sans-serif">'
        + footer
        + '</p>'
          '<p style="font-size:10px;color:#ccc;margin:6px 0 0;font-family:Arial,sans-serif">'
          'Sent via ◈ FORM.AI</p>'
          '</td></tr>'
          '</table></td></tr></table>'
          '</body></html>'
    )
    plain=f'{title}\n{"="*min(len(title),60)}\n{""+subtitle+chr(10) if subtitle else ""}' + '\n'.join(pp)+f'\n\n---\n{footer}\n'
    return html, plain, col.atts


# ═══════════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════════
=======

def _smtp_config():
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
    if not html:
        return html
    return re.sub(r'src="data:[^"]*"', 'src=""', html)


def _b64_to_file(data_url, prefix='upload'):
    """
    Convert a base64 data URL to a file on disk.
    Returns the public URL path like /static/nl_uploads/abc123.gif
    Returns None on failure.
    """
    mime_type, img_bytes = _extract_b64(data_url)
    if not img_bytes:
        return None
    # Pick extension from mime type
    ext_map = {
        'image/gif':  '.gif',
        'image/png':  '.png',
        'image/jpeg': '.jpg',
        'image/jpg':  '.jpg',
        'image/webp': '.webp',
    }
    ext = ext_map.get(mime_type, mimetypes.guess_extension(mime_type) or '.bin')
    fname = f'{prefix}_{uuid.uuid4().hex}{ext}'
    fpath = os.path.join(_upload_dir(), fname)
    try:
        with open(fpath, 'wb') as f:
            f.write(img_bytes)
        return f'/static/nl_uploads/{fname}'
    except Exception as e:
        print(f'[nl_upload] write failed: {e}')
        return None


def _sanitize_blocks_for_save(blocks):
    """
    Convert base64 image/gif URLs to disk files.
    - GIF/image blocks: base64 → saved to disk → permanent /static/nl_uploads/ URL
    - Text/heading blocks: strip any stray inline base64 srcs
    """
    cleaned = []
    for blk in blocks:
        b = dict(blk)
        c = dict(b.get('content', {}))

        if b.get('type') in ('image', 'gif'):
            url = c.get('url', '')
            if _is_base64(url):
                # Save to disk, replace with real URL
                public_url = _b64_to_file(url, prefix=b['type'])
                if public_url:
                    c['url'] = public_url
                    print(f"[nl_upload] Saved {b['type']} → {public_url}")
                else:
                    c['url'] = ''
                    c['_upload_failed'] = True

        if b.get('type') in ('text', 'heading', '2col', 'quote', 'hdr', 'header'):
            for key in ('html', 'text', 'left', 'right'):
                if key in c:
                    c[key] = _strip_base64_html(c[key])

        b['content'] = c
        cleaned.append(b)
    return cleaned


def _sanitize_theme_for_save(theme):
    t = dict(theme)
    for key, label in [('header_image', '_hdr'), ('logo_url', '_logo')]:
        if _is_base64(t.get(key, '')):
            public_url = _b64_to_file(t[key], prefix=label.strip('_'))
            if public_url:
                t[key] = public_url
            else:
                t[key] = ''
                t[f'{label}_upload_failed'] = True
    return t


# ─── Email builder ────────────────────────────────────────────────────────────

class ImageCollector:
    def __init__(self):
        self.attachments = []
        self._cid_map    = {}

    def process(self, url, prefix='img'):
        if not url:
            return ''
        if url.startswith('http://') or url.startswith('https://'):
            return url
        if url.startswith('/static/'):
            # Local file — embed as CID
            fpath = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                url.lstrip('/')
            )
            if os.path.exists(fpath):
                key = url
                if key in self._cid_map:
                    return f'cid:{self._cid_map[key]}'
                cid = f'{prefix}_{len(self.attachments)}@formcraft'
                self._cid_map[key] = cid
                mime_type = mimetypes.guess_type(fpath)[0] or 'image/gif'
                with open(fpath, 'rb') as f:
                    self.attachments.append((cid, mime_type, f.read()))
                return f'cid:{cid}'
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
        return re.sub(r'src="(data:[^"]+|/static/[^"]+)"', replacer, html)


def _build_email(nl):
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
    logo_txt   = theme.get('logo_text', '◈ FORM.AI')
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
                    f'<p style="text-align:center;font-size:13px;color:#999;font-family:Arial,sans-serif;margin:6px 0 0">▶ Watch on YouTube</p>'
                    f'</a></td></tr>\n'
                )

        elif t == 'cta':
            btn_color = c.get('color', accent)
            btn_url   = c.get('url', '#')
            btn_txt   = re.sub(r'<[^>]+>', '', c.get('text', 'Click Here')).strip()
            plain_parts.append(f'\n→ {btn_txt}: {btn_url}\n')
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
            plain_parts.append(f'"{re.sub(r"<[^>]+>","",q_text).strip()}"' + (f' — {q_author}' if q_author else '') + '\n')
            author_html = f'<p style="margin:6px 0 0;font-size:12px;color:#999;font-family:Arial,sans-serif">— {q_author}</p>' if q_author else ''
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
<p style="font-size:10px;color:#cccccc;margin:6px 0 0;font-family:Arial,sans-serif">Sent via ◈ FORM.AI</p>
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
>>>>>>> 9ea1a66fec365df468b76099a79796cc7c3ae0ce

@newsletter_bp.route('/')
@login_required
def index():
<<<<<<< HEAD
    import traceback
    try:
        nls_raw = list(_db().newsletters.find({'user_id': current_user.id}).sort('updated_at', -1))
    except Exception as e:
        traceback.print_exc()
        nls_raw = []

    nls = []
    for n in nls_raw:
        try:
            n['_id'] = str(n['_id'])
            # Safely convert dates
            for k in ('created_at', 'updated_at', 'last_sent'):
                v = n.get(k)
                if isinstance(v, datetime):
                    n[k] = v.strftime('%d %b %Y')
                elif v and not isinstance(v, str):
                    n[k] = str(v)
            # Ensure required fields exist with safe defaults
            n.setdefault('title', 'Untitled')
            n.setdefault('subtitle', '')
            n.setdefault('footer', '')
            n.setdefault('blocks', [])
            n.setdefault('send_count', 0)
            n.setdefault('theme', {})
            # Ensure send_count is int
            try:    n['send_count'] = int(n['send_count'])
            except: n['send_count'] = 0
            # Ensure blocks is a list
            if not isinstance(n['blocks'], list): n['blocks'] = []
            # Ensure theme is a dict
            if not isinstance(n['theme'], dict): n['theme'] = {}
            n['theme'].setdefault('accent_color', '#FF8C00')
            n['theme'].setdefault('header_color', '#1A1A2E')
            nls.append(n)
        except Exception:
            traceback.print_exc()
            continue

    return render_template('newsletter/index.html', newsletters=nls)
=======
    newsletters = list(_db().newsletters.find({'user_id': current_user.id}).sort('updated_at', -1))
    return render_template('newsletter/index.html', newsletters=newsletters)
>>>>>>> 9ea1a66fec365df468b76099a79796cc7c3ae0ce


@newsletter_bp.route('/new', methods=['POST'])
@login_required
def new():
<<<<<<< HEAD
    data = request.get_json(silent=True) or {}
    doc  = {'user_id':current_user.id,'title':data.get('title','Untitled Newsletter'),
             'subtitle':'','footer':'Sent by FORM.AI · Unsubscribe','blocks':[],
             'theme':{'header_color':'#1A1A2E','accent_color':'#FF8C00',
                      'logo_text':'◈ FORM.AI','logo_align':'center'},
             'created_at':datetime.utcnow(),'updated_at':datetime.utcnow()}
    r = _db().newsletters.insert_one(doc)
    return jsonify({'success':True,'nl_id':str(r.inserted_id)})
=======
    data = request.get_json() or {}
    doc = {
        'user_id':    current_user.id,
        'title':      data.get('title', 'Untitled Newsletter'),
        'subtitle':   '',
        'footer':     'Sent by FORM.AI · Unsubscribe',
        'blocks':     [],
        'theme':      {'header_color': '#1A1A2E', 'accent_color': '#FF8C00'},
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    r = _db().newsletters.insert_one(doc)
    return jsonify({'success': True, 'nl_id': str(r.inserted_id)})
>>>>>>> 9ea1a66fec365df468b76099a79796cc7c3ae0ce


@newsletter_bp.route('/<nl_id>/edit')
@login_required
def edit(nl_id):
    from bson import ObjectId
<<<<<<< HEAD
    try: nl = _db().newsletters.find_one({'_id':ObjectId(nl_id),'user_id':current_user.id})
    except: nl = None
    if not nl: return redirect(url_for('newsletter.index'))
    return render_template('newsletter/edit.html', newsletter=_serialize_nl(nl))


@newsletter_bp.route('/<nl_id>/duplicate', methods=['POST'])
@login_required
def duplicate(nl_id):
    from bson import ObjectId
    try: nl = _db().newsletters.find_one({'_id':ObjectId(nl_id),'user_id':current_user.id})
    except: nl = None
    if not nl: return jsonify({'success':False,'error':'Not found'})
    nl.pop('_id')
    nl['title']      = nl.get('title','')+ ' (Copy)'
    nl['created_at'] = nl['updated_at'] = datetime.utcnow()
    r = _db().newsletters.insert_one(nl)
    return jsonify({'success':True,'nl_id':str(r.inserted_id)})


@newsletter_bp.route('/<nl_id>/delete', methods=['POST'])
@login_required
def delete(nl_id):
    from bson import ObjectId
    try: _db().newsletters.delete_one({'_id':ObjectId(nl_id),'user_id':current_user.id})
    except: pass
    return redirect(url_for('newsletter.index'))


@newsletter_bp.route('/upload-gif',   methods=['POST'])
@newsletter_bp.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    try:
        data = request.get_json(force=True,silent=True) or {}
        du   = data.get('data_url','')
        if not du: return jsonify({'success':False,'error':'No data_url'})
        if not _is_b64(du): return jsonify({'success':True,'url':du})
        _,bts = _extract_b64(du)
        if bts and len(bts)>20*1024*1024: return jsonify({'success':False,'error':'Max 20 MB'})
        url = _b64_to_file(du,'img')
        if not url: return jsonify({'success':False,'error':'Save failed'})
        return jsonify({'success':True,'url':url})
    except Exception as e: return jsonify({'success':False,'error':str(e)})
=======
    try:
        nl = _db().newsletters.find_one({'_id': ObjectId(nl_id), 'user_id': current_user.id})
    except Exception:
        nl = None
    if not nl:
        return redirect(url_for('newsletter.index'))
    nl['_id'] = str(nl['_id'])
    return render_template('newsletter/edit.html', newsletter=nl)


@newsletter_bp.route('/upload-gif', methods=['POST'])
@login_required
def upload_gif():
    """
    Receives a base64 GIF (or any image) from the editor,
    saves it to static/nl_uploads/, returns a permanent public URL.
    This URL is then stored in nlState and MongoDB — no base64 in the DB.
    """
    try:
        data     = request.get_json(force=True, silent=True) or {}
        data_url = data.get('data_url', '')
        if not data_url:
            return jsonify({'success': False, 'error': 'No data_url provided'})

        if not _is_base64(data_url):
            # Already a URL — just return it
            return jsonify({'success': True, 'url': data_url})

        public_url = _b64_to_file(data_url, prefix='gif')
        if not public_url:
            return jsonify({'success': False, 'error': 'Failed to save GIF file'})

        return jsonify({'success': True, 'url': public_url})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
>>>>>>> 9ea1a66fec365df468b76099a79796cc7c3ae0ce


@newsletter_bp.route('/save', methods=['POST'])
@login_required
def save():
    from bson import ObjectId
<<<<<<< HEAD
    try: data = request.get_json(force=True,silent=True) or {}
    except: return jsonify({'success':False,'error':'Invalid JSON'}),400
    nl_id=data.get('nl_id')
    upd = {'title':data.get('title','Untitled'),'subtitle':data.get('subtitle',''),
           'footer':data.get('footer',''),'blocks':_sanitize_blocks(data.get('blocks',[])),
           'theme':_sanitize_theme(data.get('theme',{})),'updated_at':datetime.utcnow()}
    if nl_id and nl_id not in ('null','',None):
        try:
            _db().newsletters.update_one({'_id':ObjectId(nl_id),'user_id':current_user.id},{'$set':upd})
            return jsonify({'success':True,'nl_id':nl_id})
        except Exception as e: return jsonify({'success':False,'error':str(e)})
    else:
        upd['user_id']=current_user.id; upd['created_at']=datetime.utcnow()
        try:
            r=_db().newsletters.insert_one(upd)
            return jsonify({'success':True,'nl_id':str(r.inserted_id)})
        except Exception as e: return jsonify({'success':False,'error':str(e)})


@newsletter_bp.route('/<nl_id>/preview')
@login_required
def preview(nl_id):
    from bson import ObjectId
    try: nl=_db().newsletters.find_one({'_id':ObjectId(nl_id),'user_id':current_user.id})
    except: nl=None
    if not nl: return Response('<p>Not found</p>',mimetype='text/html',status=404)
    html,_,_ = _build_email(nl)
    return Response(html, mimetype='text/html;charset=utf-8')


@newsletter_bp.route('/preview-live', methods=['POST'])
@login_required
def preview_live():
    try:
        data=request.get_json(force=True,silent=True) or {}
        html,_,_=_build_email({'title':data.get('title','Preview'),'subtitle':data.get('subtitle',''),
                                'footer':data.get('footer',''),'blocks':data.get('blocks',[]),
                                'theme':data.get('theme',{})})
        return jsonify({'success':True,'html':html})
    except Exception as e: return jsonify({'success':False,'error':str(e)})
=======
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid JSON'}), 400

    nl_id  = data.get('nl_id')
    blocks = data.get('blocks', [])
    theme  = data.get('theme', {})

    # Convert any remaining base64 to disk files, keep https:// URLs as-is
    clean_blocks = _sanitize_blocks_for_save(blocks)
    clean_theme  = _sanitize_theme_for_save(theme)

    update = {
        'title':      data.get('title', 'Untitled'),
        'subtitle':   data.get('subtitle', ''),
        'footer':     data.get('footer', ''),
        'blocks':     clean_blocks,
        'theme':      clean_theme,
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
        try:
            r = _db().newsletters.insert_one(update)
            return jsonify({'success': True, 'nl_id': str(r.inserted_id)})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
>>>>>>> 9ea1a66fec365df468b76099a79796cc7c3ae0ce


@newsletter_bp.route('/send', methods=['POST'])
@login_required
def send():
    from bson import ObjectId
<<<<<<< HEAD
    try: data=request.get_json(force=True,silent=True) or {}
    except: return jsonify({'success':False,'error':'Invalid request'}),400
    nl_id=data.get('nl_id'); subject=data.get('subject','Newsletter from FORM.AI')
    recipients=[r.strip() for r in data.get('recipients',[]) if r and r.strip()]
    prev=data.get('preview_text','')
    if not recipients: return jsonify({'success':False,'error':'No recipients provided.'})
    try: nl=_db().newsletters.find_one({'_id':ObjectId(nl_id),'user_id':current_user.id})
    except: nl=None
    if not nl: return jsonify({'success':False,'error':'Newsletter not found.'})
    host,port,user,pwd,frm=_smtp()
    if not user or not pwd: return jsonify({'success':False,'error':'SMTP not configured. Set SMTP_USER + SMTP_PASS in .env'})
    try: html_body,plain_body,img_atts=_build_email(nl)
    except Exception as e: return jsonify({'success':False,'error':f'Email build error: {e}'})
    if prev:
        pre = (f'<div style="display:none;max-height:0;overflow:hidden;'
               f'font-size:1px;line-height:1px;color:transparent;visibility:hidden">'
               f'{prev}{"&nbsp;"*60}</div>')
        # Inject AFTER <body ...> closing > — find the end of the body opening tag
        body_end = html_body.find('>', html_body.find('<body'))
        if body_end > -1:
            html_body = html_body[:body_end+1] + '\n' + pre + html_body[body_end+1:]
        else:
            html_body = html_body.replace('</head>', f'</head>\n{pre}', 1)
    sent=0; errors=[]
    try:
        with smtplib.SMTP(host,port,timeout=30) as s:
            s.ehlo(); s.starttls(); s.ehlo(); s.login(user,pwd)
            for to in recipients:
                if '@' not in to: continue
                try:
                    if img_atts:
                        outer=MIMEMultipart('mixed'); outer['Subject']=subject; outer['From']=f'FORM.AI <{frm}>'; outer['To']=to
                        alt=MIMEMultipart('alternative'); rel=MIMEMultipart('related')
                        alt.attach(MIMEText(plain_body,'plain','utf-8'))
                        rel.attach(MIMEText(html_body,'html','utf-8'))
                        for cid,mt,bts in img_atts:
                            ip=MIMEImage(bts,_subtype=mt.split('/')[-1]); ip.add_header('Content-ID',f'<{cid}>'); ip.add_header('Content-Disposition','inline'); rel.attach(ip)
                        alt.attach(rel); outer.attach(alt); msg=outer
                    else:
                        msg=MIMEMultipart('alternative'); msg['Subject']=subject; msg['From']=f'FORM.AI <{frm}>'; msg['To']=to
                        msg.attach(MIMEText(plain_body,'plain','utf-8')); msg.attach(MIMEText(html_body,'html','utf-8'))
                    s.sendmail(frm,to,msg.as_string()); sent+=1
                except Exception as e: errors.append(f'{to}: {e}')
    except smtplib.SMTPAuthenticationError: return jsonify({'success':False,'error':'Gmail auth failed. Use an App Password.'})
    except Exception as e: return jsonify({'success':False,'error':str(e)})
    _db().newsletters.update_one({'_id':ObjectId(nl_id)},{'$set':{'last_sent':datetime.utcnow(),'send_count':sent}})
    if sent==0 and errors: return jsonify({'success':False,'error':errors[0]})
    return jsonify({'success':True,'sent_count':sent,'errors':errors[:3]})


@newsletter_bp.route('/ai-write', methods=['POST'])
@login_required
def ai_write():
    """Generate newsletter text using Mistral AI."""
    try:
        data   = request.get_json(force=True, silent=True) or {}
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({'success': False, 'error': 'No prompt provided'})

        # Try Mistral first, fall back to basic generation
        api_key = os.getenv('MISTRAL_API_KEY', '')

        if api_key:
            import urllib.request, json as _json
            req_data = _json.dumps({
                'model': 'mistral-small-latest',
                'messages': [
                    {'role': 'system', 'content': 'You are a professional email newsletter writer. Write clear, engaging, concise content. Return plain text only, no markdown.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 400,
                'temperature': 0.7,
            }).encode()
            req = urllib.request.Request(
                'https://api.mistral.ai/v1/chat/completions',
                data=req_data,
                headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                result = _json.loads(resp.read())
            text = result['choices'][0]['message']['content'].strip()
            return jsonify({'success': True, 'text': text})
        else:
            # No API key — return a helpful message
            return jsonify({
                'success': False,
                'error': 'AI not configured. Add MISTRAL_API_KEY to your .env file to enable AI writing.'
            })

    except Exception as e:
        return jsonify({'success': False, 'error': f'AI error: {str(e)}'})
=======
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
        return jsonify({'success': False, 'error': 'Gmail auth failed. Use an App Password.'})
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
>>>>>>> 9ea1a66fec365df468b76099a79796cc7c3ae0ce
