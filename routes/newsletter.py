"""
routes/newsletter.py  —  FORM.AI Newsletter System  v4
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
    data = request.get_json(silent=True) or {}
    doc  = {'user_id':current_user.id,'title':data.get('title','Untitled Newsletter'),
             'subtitle':'','footer':'Sent by FORM.AI · Unsubscribe','blocks':[],
             'theme':{'header_color':'#1A1A2E','accent_color':'#FF8C00',
                      'logo_text':'◈ FORM.AI','logo_align':'center'},
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


@newsletter_bp.route('/send', methods=['POST'])
@login_required
def send():
    from bson import ObjectId
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