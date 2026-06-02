"""
routes/newsletter.py  —  Draftspace Newsletter System  v4
"""
from flask import (Blueprint, render_template, request, jsonify,
                   redirect, url_for, Response)
from flask_login import login_required, current_user
from datetime import datetime
import smtplib, os, re, base64, uuid, mimetypes
from email.mime.multipart import MIMEMultipart
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

def _db():
    from app import db; return db

def _smtp():
    from flask_login import current_user
    if current_user and current_user.is_authenticated:
        try:
            from bson import ObjectId
            u_doc = _db().users.find_one({'_id': ObjectId(current_user.id)})
            if u_doc and u_doc.get('smtp_settings'):
                cfg = u_doc['smtp_settings']
                if cfg.get('user') and cfg.get('pwd'):
                    h = cfg.get('host', 'smtp.gmail.com')
                    p = int(cfg.get('port', 587))
                    u = cfg.get('user')
                    w = cfg.get('pwd')
                    f = cfg.get('from_addr') or u
                    return h, p, u, w, f
        except Exception as e:
            print(f"Error loading user SMTP settings: {e}")

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
    try:
        from app import db
        r = db.images.insert_one({
            'mime': mime,
            'data': bts,
            'created_at': datetime.utcnow()
        })
        return f'/newsletter/image/{str(r.inserted_id)}'
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
        for local_prefix in ('http://localhost:5000/', 'http://127.0.0.1:5000/'):
            if url.startswith(local_prefix):
                url = '/' + url[len(local_prefix):]
            elif url.startswith(local_prefix.rstrip('/')):
                url = '/' + url[len(local_prefix.rstrip('/')):]
        if url.startswith(('http://','https://')): return url
        if url.startswith('/newsletter/image/'):
            try:
                from bson import ObjectId
                from app import db
                img_id = url.split('/')[-1]
                img = db.images.find_one({'_id': ObjectId(img_id)})
                if img and img.get('data'):
                    if url in self._m: return f'cid:{self._m[url]}'
                    cid = f'{pfx}_{len(self.atts)}@Draftspace'
                    self._m[url] = cid
                    self.atts.append((cid, img.get('mime', 'image/png'), img['data']))
                    print(f'[EMAIL_IMG] CID from DB: {url} -> {cid} ({len(img["data"])} bytes)')
                    return f'cid:{cid}'
                else:
                    print(f'[EMAIL_IMG] WARN: DB image not found: {url}')
            except Exception as e:
                print(f'[EMAIL_IMG] ERR loading DB image {url}: {e}')
            try:
                from flask import request as _req
                base = os.getenv('BASE_URL') or _req.host_url.rstrip('/')
                return base + url
            except:
                return url
        if url.startswith('/static/'):
            try:
                from flask import current_app
                fp = os.path.join(current_app.root_path, url.lstrip('/'))
            except RuntimeError:
                fp = os.path.join(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__))), url.lstrip('/'))
            if os.path.exists(fp):
                if url in self._m: return f'cid:{self._m[url]}'
                cid=f'{pfx}_{len(self.atts)}@Draftspace'; self._m[url]=cid
                mt=mimetypes.guess_type(fp)[0] or 'image/png'
                with open(fp,'rb') as f: self.atts.append((cid,mt,f.read()))
                print(f'[EMAIL_IMG] CID from file: {url} -> {cid}')
                return f'cid:{cid}'
            else:
                print(f'[EMAIL_IMG] WARN: file not found: {fp}')
                try:
                    from flask import request as _req
                    base = os.getenv('BASE_URL') or _req.host_url.rstrip('/')
                    return base + url
                except:
                    return url
        mime,bts=_extract_b64(url)
        if not bts:
            print(f'[EMAIL_IMG] WARN: unprocessable URL: {url[:80]}')
            return ''
        key=url[:80]
        if key in self._m: return f'cid:{self._m[key]}'
        cid=f'{pfx}_{len(self.atts)}@Draftspace'; self._m[key]=cid
        self.atts.append((cid,mime or 'image/png',bts)); return f'cid:{cid}'

    def html(self, h, pfx='img'):
        if not h: return h
        # Clean any absolute localhost URLs inside rich text src attributes back to relative
        h = re.sub(r'src="https?://(?:localhost|127\.0\.0\.1):5000(/static/[^"]+|/newsletter/image/[^"]+)"', r'src="\1"', h)
        return re.sub(r'src="(data:[^"]+|/static/[^"]+|/newsletter/image/[^"]+)"',
                      lambda m:f'src="{self.process(m.group(1),pfx)}"', h)

# ── email builder ─────────────────────────────────────────────────────────────
def _build_email(nl):
    th=nl.get('theme',{}); acc=th.get('accent_color','#FF8C00')
    title=nl.get('title','Newsletter'); subtitle=nl.get('subtitle','')
    footer=nl.get('footer','Sent by Draftspace'); blocks=nl.get('blocks',[])
    col=_ImgC()
    hi=col.process(th.get('header_image',''),'hdr')
    hbg=(f"background:{th.get('header_color','#1A1A2E')};background-image:url('{hi}');background-size:cover;background-position:center" if hi else f"background:{th.get('header_color','#1A1A2E')}")
    lu=col.process(th.get('logo_url',''),'logo')
    lt=th.get('logo_text','◈ Draftspace'); lw=th.get('logo_width',140)
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
          'Sent via ◈ Draftspace</p>'
          '</td></tr>'
          '</table></td></tr></table>'
          '</body></html>'
    )
    plain=f'{title}\n{"="*min(len(title),60)}\n'+(subtitle+'\n' if subtitle else '') + '\n'.join(pp)+f'\n\n---\n{footer}\n'
    return html, plain, col.atts


def _build_preview_html(nl, base_url='http://localhost:5000', b64=False):
    """Build newsletter HTML for browser preview — uses absolute hosted URLs by default to ensure maximum email client compatibility."""
    th=nl.get('theme',{}); acc=th.get('accent_color','#FF8C00')
    title=nl.get('title','Newsletter'); subtitle=nl.get('subtitle','')
    footer=nl.get('footer','Sent by Draftspace'); blocks=nl.get('blocks',[])

    def to_b64(u):
        if not u: return ''
        if u.startswith('data:'): return u
        # Convert local absolute URLs back to relative /static/
        for local_prefix in ('http://localhost:5000/', 'http://127.0.0.1:5000/', base_url + '/'):
            if u.startswith(local_prefix):
                u = '/' + u[len(local_prefix):]
            elif u.startswith(local_prefix.rstrip('/')):
                u = '/' + u[len(local_prefix.rstrip('/')):]

        if not b64:
            if u.startswith('/static/') or u.startswith('/newsletter/image/'):
                return base_url + u
            return u

        if u.startswith('/newsletter/image/'):
            try:
                import base64 as _base64
                from bson import ObjectId
                from app import db
                img_id = u.split('/')[-1]
                img = db.images.find_one({'_id': ObjectId(img_id)})
                if img and img.get('data'):
                    encoded = _base64.b64encode(img['data']).decode('utf-8')
                    return f"data:{img.get('mime','image/png')};base64,{encoded}"
            except: pass
            return base_url + u

        if u.startswith('/static/'):
            try:
                from flask import current_app
                fp = os.path.join(current_app.root_path, u.lstrip('/'))
            except RuntimeError:
                fp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), u.lstrip('/'))
            if os.path.exists(fp):
                import base64 as _base64, mimetypes as _mimetypes
                mt = _mimetypes.guess_type(fp)[0] or 'image/png'
                try:
                    with open(fp, 'rb') as f:
                        encoded = _base64.b64encode(f.read()).decode('utf-8')
                    return f'data:{mt};base64,{encoded}'
                except:
                    pass
            return base_url + u
        return u

    def clean_html(h):
        if not h: return ''
        import re as _re
        # Clean any absolute localhost URLs inside rich text src attributes back to relative
        h = _re.sub(r'src="https?://(?:localhost|127\.0\.0\.1):5000(/static/[^"]+|/newsletter/image/[^"]+)"', r'src="\1"', h)
        h = _re.sub(r'src="' + base_url + r'(/static/[^"]+|/newsletter/image/[^"]+)"', r'src="\1"', h)
        return _re.sub(r'src="(/static/[^"]+|/newsletter/image/[^"]+)"', lambda m: f'src="{to_b64(m.group(1))}"', h)

    hi = to_b64(th.get('header_image',''))
    hdr_color = th.get('header_color','#1A1A2E')
    hbg = (f"background:{hdr_color};background-image:url('{hi}');background-size:cover;background-position:center"
           if hi else f"background:{hdr_color}")

    lu = to_b64(th.get('logo_url',''))
    lt = th.get('logo_text','◈ Draftspace')
    logo = (f'<img src="{lu}" style="max-width:140px;max-height:50px;border-radius:6px;display:block;margin:0 auto 10px" alt="Logo"><br>'
            if lu else f'<div style="font-size:13px;color:rgba(255,255,255,.55);letter-spacing:.2em;font-family:Arial,sans-serif;text-align:center;margin-bottom:12px">{lt}</div>')

    rows = ''
    for i, blk in enumerate(blocks):
        c = blk.get('content', {}); t = blk.get('type', '')
        if t == 'text':
            align = c.get('align', 'left')
            color = c.get('color', '#212529')
            fs = f"{c.get('font_size')}px" if c.get('font_size') else '15px'
            lh = c.get('line_height', '1.75')
            bg = f"background-color:{c.get('bg_color')};" if c.get('bg_color') else ''
            pad = f"{c.get('padding', 14)}px 28px"
            rows += f'<tr><td style="padding:{pad};font-size:{fs};line-height:{lh};color:{color};text-align:{align};{bg}font-family:Arial,sans-serif">{clean_html(c.get("html",""))}</td></tr>\n'
        elif t == 'heading':
            lvl = c.get('level','h2')
            default_fs = {'h1':'26px','h2':'20px','h3':'16px'}.get(lvl,'20px')
            fs = f"{c.get('font_size')}px" if c.get('font_size') else default_fs
            align = c.get('align', 'left')
            color = c.get('color', '#1A1A2E')
            bg = f"background-color:{c.get('bg_color')};" if c.get('bg_color') else ''
            rows += f'<tr><td style="padding:14px 28px;{bg}"><{lvl} style="font-family:Georgia,serif;font-size:{fs};color:{color};text-align:{align};margin:0;line-height:1.25;font-weight:700">{clean_html(c.get("text",""))}</{lvl}></td></tr>\n'
        elif t in ('image','gif'):
            src = to_b64(c.get('url',''))
            if src:
                rw = str(c.get('img_width') or c.get('gif_width') or '100%')
                try:
                    import re as _re
                    n = float(_re.sub(r'[^\d.]','',rw)); pw = int(560*n/100) if '%' in rw else min(int(n),560)
                except: pw = 560
                al = c.get('img_align') or c.get('gif_align') or 'center'
                cap = c.get('caption','')
                rows += (f'<tr><td style="padding:10px 20px" align="{al}"><img src="{src}" width="{pw}" style="display:block;border-radius:{c.get("img_radius",8)}px;max-width:100%" alt="">'
                         + (f'<p style="font-size:12px;color:#999;text-align:center;margin:6px 0 0;font-family:Arial,sans-serif">{cap}</p>' if cap else '')
                         + '</td></tr>\n')
        elif t == 'video':
            yt = c.get('youtube_id','')
            if yt:
                rows += (f'<tr><td style="padding:14px 28px"><a href="https://www.youtube.com/watch?v={yt}" style="display:block;text-decoration:none">'
                         f'<img src="https://img.youtube.com/vi/{yt}/hqdefault.jpg" width="560" style="display:block;border-radius:10px;max-width:100%" alt="Watch on YouTube">'
                         f'<p style="text-align:center;font-size:13px;color:#999;font-family:Arial,sans-serif;margin:6px 0 0">▶ Watch on YouTube</p></a></td></tr>\n')
        elif t == 'cta':
            import re as _re
            bt = _re.sub(r'<[^>]+>','',c.get('text','Click Here')).strip(); bu = c.get('url','#'); bc = c.get('color',acc)
            rows += f'<tr><td style="padding:20px 28px;text-align:center"><a href="{bu}" style="display:inline-block;padding:13px 36px;border-radius:8px;background:{bc};color:white;font-weight:700;text-decoration:none;font-size:15px;font-family:Arial,sans-serif">{bt}</a></td></tr>\n'
        elif t == 'divider':
            rows += '<tr><td style="padding:8px 28px"><hr style="border:none;border-top:2px solid #E8E0D5;margin:0"></td></tr>\n'
        elif t == 'quote':
            qt = clean_html(c.get('text','')); auth = c.get('author','')
            align = c.get('align', 'left')
            color = c.get('color', '#1A1A2E')
            fs = f"{c.get('font_size')}px" if c.get('font_size') else '16px'
            bg = c.get('bg_color', '#FFF8F0')
            rows += (f'<tr><td style="padding:8px 28px"><table width="100%" cellpadding="0" cellspacing="0"><tr>'
                     f'<td style="border-left:4px solid {acc};background:{bg};padding:14px 18px;border-radius:0 8px 8px 0">'
                     f'<blockquote style="font-family:Georgia,serif;font-size:{fs};color:{color};text-align:{align};margin:0;line-height:1.6;font-style:italic">{qt}</blockquote>'
                     + (f'<p style="margin:6px 0 0;font-size:12px;color:#999;font-family:Arial,sans-serif;text-align:{align}">— {auth}</p>' if auth else '')
                     + '</td></tr></table></td></tr>\n')
        elif t == '2col':
            l = clean_html(c.get('left','')); r2 = clean_html(c.get('right',''))
            rows += (f'<tr><td style="padding:10px 28px"><table width="100%" cellpadding="0" cellspacing="0"><tr>'
                     f'<td width="49%" valign="top" style="background:#FAFAFA;border-radius:8px;padding:12px;font-size:13px;font-family:Arial,sans-serif;line-height:1.6">{l}</td>'
                     f'<td width="2%"></td>'
                     f'<td width="49%" valign="top" style="background:#FAFAFA;border-radius:8px;padding:12px;font-size:13px;font-family:Arial,sans-serif;line-height:1.6">{r2}</td>'
                     f'</tr></table></td></tr>\n')
        elif t == 'spacer':
            h = int(c.get('height',24))
            rows += f'<tr><td height="{h}" style="font-size:1px;line-height:1px">&nbsp;</td></tr>\n'
        elif t in ('hdr','header'):
            bg = c.get('bg','#1A1A2E'); color = c.get('color','#ffffff'); txt = clean_html(c.get('text',''))
            rows += f'<tr><td style="background:{bg};padding:18px 28px;text-align:center"><p style="font-family:Georgia,serif;font-size:18px;font-weight:700;color:{color};margin:0">{txt}</p></td></tr>\n'
        elif t == 'social':
            btns = ''.join(f'<a href="{lk.get("url","#")}" style="display:inline-block;margin:0 6px;padding:8px 16px;border-radius:6px;background:#F0EEF4;color:#1A1A2E;text-decoration:none;font-size:13px;font-family:Arial,sans-serif">{lk.get("icon","🔗")} {lk.get("name","")}</a>' for lk in c.get('links',[]))
            if btns: rows += f'<tr><td style="padding:14px 28px;text-align:center">{btns}</td></tr>\n'

    sub_row = (f'<p style="color:rgba(255,255,255,.7);margin:0;font-size:15px;line-height:1.5;font-family:Arial,sans-serif">{subtitle}</p>' if subtitle else '')
    html = (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
        f'<title>{title}</title></head>'
        '<body style="margin:0;padding:0;background:#F0EEF4">'
        '<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#F0EEF4" style="background:#F0EEF4;padding:24px 0">'
        '<tr><td align="center" style="padding:24px 16px">'
        '<table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10)">'
        f'<tr><td bgcolor="{hdr_color}" style="{hbg.replace(chr(34),chr(39))};padding:36px 32px 28px;text-align:center">'
        + logo
        + f'<h1 style="font-family:Georgia,serif;font-size:28px;color:#ffffff;margin:0 0 10px;line-height:1.2;font-weight:700">{title}</h1>'
        + sub_row
        + '</td></tr>'
        + rows
        + '<tr><td style="background:#F8F9FA;padding:20px 32px;text-align:center;border-top:1px solid #E0E0E0">'
        f'<p style="font-size:11px;color:#999;margin:0;line-height:1.8;font-family:Arial,sans-serif">{footer}</p>'
        '<p style="font-size:10px;color:#ccc;margin:6px 0 0;font-family:Arial,sans-serif">Sent via ◈ Draftspace</p>'
        '</td></tr></table></td></tr></table></body></html>'
    )
    return html



# ═══════════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════════

@newsletter_bp.route('/')
@login_required
def index():
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


@newsletter_bp.route('/new', methods=['POST'])
@login_required
def new():
    if not current_user.can_create_newsletter():
        return jsonify({'success': False, 'error': 'Newsletter limit reached for your plan. Please upgrade.'}), 403
    data = request.get_json(silent=True) or {}
    doc  = {'user_id':current_user.id,'title':data.get('title','Untitled Newsletter'),
             'subtitle':'','footer':'Sent by Draftspace · Unsubscribe','blocks':[],
             'theme':{'header_color':'#1A1A2E','accent_color':'#FF8C00',
                      'logo_text':'◈ Draftspace','logo_align':'center'},
             'created_at':datetime.utcnow(),'updated_at':datetime.utcnow()}
    r = _db().newsletters.insert_one(doc)
    return jsonify({'success':True,'nl_id':str(r.inserted_id)})


@newsletter_bp.route('/<nl_id>/edit')
@login_required
def edit(nl_id):
    from bson import ObjectId
    try: nl = _db().newsletters.find_one({'_id':ObjectId(nl_id),'user_id':current_user.id})
    except: nl = None
    if not nl: return redirect(url_for('newsletter.index'))
    return render_template('newsletter/edit.html', newsletter=_serialize_nl(nl))


@newsletter_bp.route('/<nl_id>/duplicate', methods=['POST'])
@login_required
def duplicate(nl_id):
    if not current_user.can_create_newsletter():
        return jsonify({'success': False, 'error': 'Newsletter limit reached for your plan. Please upgrade.'}), 403
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


@newsletter_bp.route('/image/<img_id>')
def serve_image(img_id):
    from bson import ObjectId
    try:
        from app import db
        img = db.images.find_one({'_id': ObjectId(img_id)})
    except Exception:
        img = None
    if not img: return Response("Not found", status=404)
    return Response(img.get('data', b''), mimetype=img.get('mime', 'image/png'))


@newsletter_bp.route('/save', methods=['POST'])
@login_required
def save():
    from bson import ObjectId
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
    from flask import request as _req
    try: nl=_db().newsletters.find_one({'_id':ObjectId(nl_id),'user_id':current_user.id})
    except: nl=None
    if not nl: return Response('<p>Not found</p>',mimetype='text/html',status=404)
    base = os.getenv('BASE_URL') or _req.host_url.rstrip('/')
    b64_param = _req.args.get('b64', 'false').lower() != 'false'
    html = _build_preview_html(nl, base_url=base, b64=b64_param)
    return Response(html, mimetype='text/html;charset=utf-8')


@newsletter_bp.route('/<nl_id>/export')
@login_required
def export_html(nl_id):
    """Download newsletter as HTML file — images show, ready to open in any email client."""
    from bson import ObjectId
    from flask import request as _req
    try: nl=_db().newsletters.find_one({'_id':ObjectId(nl_id),'user_id':current_user.id})
    except: nl=None
    if not nl: return Response('<p>Not found</p>',mimetype='text/html',status=404)
    base = os.getenv('BASE_URL') or _req.host_url.rstrip('/')
    html = _build_preview_html(nl, base_url=base)
    title = nl.get('title','newsletter').replace(' ','_').lower()[:40]
    return Response(
        html,
        mimetype='text/html;charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{title}.html"'}
    )


@newsletter_bp.route('/<nl_id>/public-preview')
def public_preview(nl_id):
    """Public preview iframe — no login needed, only for published newsletters."""
    from bson import ObjectId
    from flask import request as _req
    try: nl=_db().newsletters.find_one({'_id':ObjectId(nl_id),'is_published':True})
    except: nl=None
    if not nl: return Response('<p style="font-family:sans-serif;padding:20px;color:#aaa">Preview not available</p>',mimetype='text/html',status=404)
    base = os.getenv('BASE_URL') or _req.host_url.rstrip('/')
    html = _build_preview_html(nl, base_url=base)
    return Response(html, mimetype='text/html;charset=utf-8')


@newsletter_bp.route('/community')
def community():
    """Public community newsletter feed — no login required."""
    cat = request.args.get('cat', '')
    query = {'is_published': True, 'community_post': True}
    if cat:
        query['community_category'] = cat
    try:
        nls_raw = list(_db().newsletters.find(query).sort('community_posted_at', -1).limit(60))
    except Exception:
        nls_raw = []

    from models.user import User
    newsletters = []
    creator_ids = set()
    for n in nls_raw:
        try:
            n['_id'] = str(n['_id'])
            for k in ('created_at','updated_at','last_sent','community_posted_at'):
                v = n.get(k)
                if isinstance(v, datetime):
                    n[k] = v.strftime('%d %b %Y')
                    if k == 'community_posted_at':
                        n['community_posted_at_str'] = v.strftime('%d %b %Y')
            n.setdefault('title','Untitled')
            n.setdefault('subtitle','')
            n.setdefault('blocks',[])
            n.setdefault('theme',{})
            n.setdefault('community_tags',[])
            n.setdefault('community_category','general')
            creator = User.get_by_id(n.get('user_id',''))
            n['creator_name'] = creator.name if creator else 'Draftspace Creator'
            creator_ids.add(n.get('user_id',''))
            newsletters.append(n)
        except Exception:
            continue

    total_count = len(newsletters)
    creator_count = len(creator_ids)
    return render_template('newsletter/community.html',
        newsletters=newsletters,
        total_count=total_count,
        creator_count=creator_count,
        active_cat=cat
    )


@newsletter_bp.route('/<nl_id>/read')
def read(nl_id):
    """Public full-page read view — no login required."""
    from bson import ObjectId
    try: nl=_db().newsletters.find_one({'_id':ObjectId(nl_id),'is_published':True})
    except: nl=None
    if not nl:
        return Response('<h2 style="font-family:sans-serif;padding:40px">Newsletter not found or not published.</h2>', mimetype='text/html', status=404)
    nl['_id'] = str(nl['_id'])
    from models.user import User
    creator = User.get_by_id(nl.get('user_id',''))
    creator_name = creator.name if creator else 'Draftspace Creator'
    posted_at = nl.get('community_posted_at')
    if isinstance(posted_at, datetime):
        posted_date = posted_at.strftime('%d %B %Y')
    else:
        posted_date = str(posted_at or nl.get('updated_at',''))
    return render_template('newsletter/read.html', nl=nl, creator_name=creator_name, posted_date=posted_date)


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


@newsletter_bp.route('/send', methods=['POST'])
@login_required
def send():
    from bson import ObjectId
    try: data=request.get_json(force=True,silent=True) or {}
    except: return jsonify({'success':False,'error':'Invalid request'}),400
    nl_id=data.get('nl_id'); subject=data.get('subject','Newsletter from Draftspace')
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
                        msg = MIMEMultipart('related')
                        msg['Subject'] = subject
                        msg['From'] = f'Draftspace <{frm}>'
                        msg['To'] = to
                        
                        alt = MIMEMultipart('alternative')
                        alt.attach(MIMEText(plain_body, 'plain', 'utf-8'))
                        alt.attach(MIMEText(html_body, 'html', 'utf-8'))
                        msg.attach(alt)
                        
                        for cid, mt, bts in img_atts:
                            subtype = mt.split('/')[-1] if '/' in mt else 'png'
                            ip = MIMEImage(bts, _subtype=subtype)
                            ip.add_header('Content-ID', f'<{cid}>')
                            ip.add_header('Content-Disposition', 'inline')
                            msg.attach(ip)
                    else:
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = subject
                        msg['From'] = f'Draftspace <{frm}>'
                        msg['To'] = to
                        msg.attach(MIMEText(plain_body, 'plain', 'utf-8'))
                        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
                    s.sendmail(frm, to, msg.as_string())
                    sent += 1
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


@newsletter_bp.route('/settings/smtp', methods=['POST'])
@login_required
def save_smtp_settings():
    try:
        from bson import ObjectId
        data = request.get_json(force=True, silent=True) or {}
        host = data.get('host', 'smtp.gmail.com').strip()
        port = int(data.get('port', 587))
        user = data.get('user', '').strip()
        pwd = data.get('pwd', '').strip()
        from_addr = data.get('from_addr', '').strip() or user

        if not user:
            return jsonify({'success': False, 'error': 'Username/Email is required.'})

        # Fetch existing settings to keep password if a new one was not submitted
        u_doc = _db().users.find_one({'_id': ObjectId(current_user.id)})
        existing = (u_doc or {}).get('smtp_settings', {})
        final_pwd = pwd if pwd else existing.get('pwd', '')

        if not final_pwd:
            return jsonify({'success': False, 'error': 'Password is required.'})

        _db().users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': {
                'smtp_settings': {
                    'host': host,
                    'port': port,
                    'user': user,
                    'pwd': final_pwd,
                    'from_addr': from_addr
                }
            }}
        )
        return jsonify({'success': True, 'message': 'SMTP settings saved successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@newsletter_bp.route('/settings/smtp', methods=['GET'])
@login_required
def get_smtp_settings():
    try:
        from bson import ObjectId
        u_doc = _db().users.find_one({'_id': ObjectId(current_user.id)})
        smtp = (u_doc or {}).get('smtp_settings', {})
        has_pwd = bool(smtp.get('pwd'))
        return jsonify({
            'success': True,
            'host': smtp.get('host', 'smtp.gmail.com'),
            'port': smtp.get('port', 587),
            'user': smtp.get('user', ''),
            'from_addr': smtp.get('from_addr', ''),
            'has_pwd': has_pwd
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

