"""
routes/deploy.py  —  FORM.AI Deploy System  v3
═══════════════════════════════════════════════
Sources:
  • Upload ZIP  (any framework)
  • Upload single HTML / CSS / JS files
  • Pull from GitHub repo URL

Pipeline:
  1. Extract / fetch files
  2. Detect framework (HTML / Flask / React / Django)
  3. Ask user: convert to Flask?  (optional)
  4. User sets homepage + MongoDB URI
  5. Inject MongoDB helpers + fix asset paths
  6. Save to disk under static/sites/<slug>/
  7. Publish at  /sites/<slug>/
  8. View, edit, unpublish, delete
"""

import io, os, re, json, zipfile, uuid, shutil, urllib.request, urllib.parse
from datetime import datetime
from flask import (Blueprint, jsonify, render_template, request,
                   send_file, abort, Response)
from flask_login import login_required, current_user

deploy_bp = Blueprint('deploy', __name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — paths
# ═══════════════════════════════════════════════════════════════════════════════
def _sites_root() -> str:
    try:
        from flask import current_app
        base = current_app.root_path
    except RuntimeError:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(base, 'static', 'sites')
    os.makedirs(d, exist_ok=True)
    return d

def _site_dir(slug: str) -> str:
    return os.path.join(_sites_root(), slug)

def _db():
    from app import db; return db

def _col():
    return _db().published_sites


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — slugs
# ═══════════════════════════════════════════════════════════════════════════════
def _slugify(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r'[^\w\s-]', '', t)
    t = re.sub(r'[\s_]+', '-', t)
    t = re.sub(r'-+', '-', t).strip('-')
    return t[:50] or uuid.uuid4().hex[:10]

def _unique_slug(base: str, exclude_id=None) -> str:
    slug = base
    for i in range(1, 99):
        doc = _col().find_one({'slug': slug})
        if not doc: return slug
        if exclude_id and str(doc.get('_id')) == str(exclude_id): return slug
        slug = f'{base}-{i}'
    return base + '-' + uuid.uuid4().hex[:6]


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — user data
# ═══════════════════════════════════════════════════════════════════════════════
def _app_mongo_uri() -> str:
    """Get the app's own MongoDB URI — always correct, never wrong."""
    try:
        from app import MONGO_URI as APP_URI
        return APP_URI
    except Exception:
        return os.getenv('MONGO_URI', 'mongodb://localhost:27017/formcraft')


def _user_data(user_id: str) -> dict:
    forms = list(_db().forms.find({'user_id': user_id}))
    for f in forms:
        f['_id'] = str(f['_id'])
        for k in ('created_at','updated_at'):
            if isinstance(f.get(k), datetime): f[k] = f[k].isoformat()
        responses = list(_db().responses.find({'form_id': str(f['_id'])}))
        for r in responses:
            r['_id'] = str(r['_id'])
            if isinstance(r.get('submitted_at'), datetime):
                r['submitted_at'] = r['submitted_at'].isoformat()
        f['responses'] = responses
    nls = list(_db().newsletters.find({'user_id': user_id}))
    for n in nls:
        n['_id'] = str(n['_id'])
        for k in ('created_at','updated_at'):
            if isinstance(n.get(k), datetime): n[k] = n[k].isoformat()
    return {'forms': forms, 'newsletters': nls}


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — framework detection
# ═══════════════════════════════════════════════════════════════════════════════
def _detect_fw(file_list: list, file_contents: dict) -> str:
    names = [f.lower() for f in file_list]
    pkg   = file_contents.get('package.json','')
    if 'package.json' in names and ('"react"' in pkg or "'react'" in pkg):
        return 'react'
    if 'manage.py' in names: return 'django'
    for n in names:
        if n.endswith('settings.py') and 'INSTALLED_APPS' in file_contents.get(n,''): return 'django'
    for n in ('requirements.txt','pipfile'):
        if 'flask' in file_contents.get(n,'').lower(): return 'flask'
    for n,c in file_contents.items():
        if n.endswith('.py') and ('from flask' in c or 'import flask' in c): return 'flask'
    return 'html'


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — asset path fixer
# ═══════════════════════════════════════════════════════════════════════════════
def _fix_paths(html: str) -> str:
    """Rewrite relative src/href so they work from /sites/<slug>/"""
    def fix(m):
        attr, quote, val = m.group(1), m.group(2), m.group(3).strip()
        if not val or val.startswith(('http','//','#','data:','mailto:','tel:',
                                       'javascript:','./','../','/')):
            return m.group(0)
        return f'{attr}={quote}./{val}{quote}'
    return re.sub(r'\b(href|src)=(["\'])([^"\'#\s>]{1,400})\2', fix, html)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — ZIP prefix stripping
# ═══════════════════════════════════════════════════════════════════════════════
def _strip_zip_prefix(raw_files: dict) -> dict:
    """Remove common leading folder from all paths (e.g. mysite/index.html → index.html)"""
    paths = list(raw_files.keys())
    if not paths: return raw_files
    parts = paths[0].split('/')
    if len(parts) > 1:
        candidate = parts[0] + '/'
        if all(p.startswith(candidate) for p in paths):
            return {p[len(candidate):]: v for p, v in raw_files.items() if p[len(candidate):]}
    return raw_files


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — MongoDB injectors
# ═══════════════════════════════════════════════════════════════════════════════
def _inject_html(files: dict, data_json: str, mongo_uri: str) -> dict:
    script = (
        f'<script>\n/* FORM.AI Deploy */\n'
        f'window.FORMCRAFT_MONGO_URI="{mongo_uri}";\n'
        f'window.FORMCRAFT_DATA={data_json};\n'
        f'window.FORMCRAFT_FORMS=window.FORMCRAFT_DATA.forms;\n'
        f'window.FORMCRAFT_NL=window.FORMCRAFT_DATA.newsletters;\n</script>\n'
    )
    out = {}
    for name, content in files.items():
        if name.lower().endswith(('.html','.htm')):
            content = _fix_paths(content)
            inj = script
            if '</head>' in content:
                content = content.replace('</head>', inj+'</head>', 1)
            elif '<body' in content:
                content = re.sub(r'(<body[^>]*>)', r'\1'+inj, content, count=1)
            else:
                content = inj + content
        out[name] = content
    return out


def _inject_flask_conversion(files: dict, data_json: str,
                              mongo_uri: str, user_data: dict,
                              homepage: str = 'index.html') -> dict:
    """
    Convert an HTML-only project into a minimal Flask app.
    Moves HTML files into templates/, assets into static/,
    creates app.py + formcraft_db.py + requirements.txt
    """
    out     = {}
    fj      = json.dumps(user_data['forms'],       default=str, indent=2)
    nj      = json.dumps(user_data['newsletters'],  default=str, indent=2)
    rand_key = uuid.uuid4().hex[:20]

    tpl_files = {}   # filename → html content (for templates/)
    sta_files = {}   # path → bytes/str (for static/)

    ASSET_EXTS = {'.css','.js','.png','.jpg','.jpeg','.gif','.svg','.ico',
                  '.woff','.woff2','.ttf','.eot','.otf','.mp4','.webm',
                  '.mp3','.pdf','.json','.xml','.txt','.md'}

    for path, content in files.items():
        ext = os.path.splitext(path)[-1].lower()
        if ext in ('.html', '.htm'):
            tpl_files[path] = content
        elif ext in ASSET_EXTS:
            sta_files[path] = content
        else:
            sta_files[path] = content   # everything else → static/

    # ── Rewrite HTML files for Flask (Jinja2 templates) ───────────────────────
    for path, html in tpl_files.items():
        html = _fix_paths(html)
        # Rewrite asset links to use url_for('static', filename=...)
        def _to_jinja(m):
            attr  = m.group(1); quote = m.group(2); val = m.group(3).strip()
            if not val or val.startswith(('http','//','#','data:','mailto:',
                                          'javascript:','{{','/')):
                return m.group(0)
            # val is like "css/style.css" or "./js/app.js"
            clean = val.lstrip('./')
            return f'{attr}={quote}{{{{ url_for("static", filename="{clean}") }}}}{quote}'
        html = re.sub(r'\b(href|src)=(["\'])([^"\'#\s>]{1,400})\2', _to_jinja, html)
        # Inject FORMCRAFT data
        inj = (f'<script>\nwindow.FORMCRAFT_MONGO_URI="{mongo_uri}";\n'
               f'window.FORMCRAFT_DATA={data_json};\n</script>\n')
        if '</head>' in html:
            html = html.replace('</head>', inj+'</head>', 1)
        tpl_files[path] = html

    # ── Build app.py ──────────────────────────────────────────────────────────
    # Create routes for each HTML file
    routes = []
    for path in tpl_files:
        slug = path.replace('/', '_').replace('.html','').replace('.htm','').lower()
        endpoint = 'index' if path == homepage or path == 'index.html' else slug
        url = '/' if endpoint == 'index' else f'/{slug}'
        routes.append(f'''
@app.route("{url}")
def {endpoint}():
    return render_template("{path}")''')

    app_py = f'''"""Flask app — converted by FORM.AI Deploy"""
import os
from flask import Flask, render_template
from dotenv import load_dotenv
import formcraft_db

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "{rand_key}")

{"".join(routes)}

if __name__ == "__main__":
    app.run(debug=False)
'''

    # ── formcraft_db.py ──────────────────────────────────────────────────────
    db_py = f'''"""FORM.AI Deploy — MongoDB helper"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "{mongo_uri}")
try:
    _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    _db     = _client.get_database("formcraft")
    _ok     = True
except Exception as e:
    print(f"[formcraft_db] offline: {{e}}")
    _db = None; _ok = False

_FORMS = {fj}
_NL    = {nj}

def get_forms(uid=None):
    if _ok: return list(_db.forms.find({{"user_id":uid}} if uid else {{}}))
    return _FORMS

def get_responses(fid):
    if _ok: return list(_db.responses.find({{"form_id":str(fid)}}))
    return []

def get_newsletters(uid=None):
    if _ok: return list(_db.newsletters.find({{"user_id":uid}} if uid else {{}}))
    return _NL

def is_connected(): return _ok
'''

    out['.env']              = f'MONGO_URI={mongo_uri}\nSECRET_KEY={rand_key}\n'
    out['app.py']            = app_py
    out['formcraft_db.py']   = db_py
    out['requirements.txt']  = 'flask\npymongo==4.6.1\npython-dotenv==1.0.0\ndnspython==2.4.2\ngunicorn\n'
    out['Procfile']          = 'web: gunicorn app:app\n'
    out['FORMCRAFT_README.md'] = f'''# Converted by FORM.AI Deploy

## Run locally
```bash
pip install -r requirements.txt
python app.py
```

## Deploy to Railway / Render / Heroku
1. Push this folder to GitHub
2. Connect repo → set env var MONGO_URI
3. Deploy!

## MongoDB URI
{mongo_uri}
'''

    # Add templates/ and static/
    for path, content in tpl_files.items():
        out[f'templates/{path}'] = content
    for path, content in sta_files.items():
        out[f'static/{path}'] = content

    return out


def _inject_existing_flask(files: dict, data_json: str,
                            mongo_uri: str, user_data: dict) -> dict:
    out  = dict(files)
    fj   = json.dumps(user_data['forms'],       default=str, indent=2)
    nj   = json.dumps(user_data['newsletters'],  default=str, indent=2)
    out['.env']           = f'MONGO_URI={mongo_uri}\nSECRET_KEY={uuid.uuid4().hex[:20]}\n'
    out['formcraft_db.py'] = f'''"""FORM.AI Deploy — MongoDB helper"""
import os
from pymongo import MongoClient
MONGO_URI = os.getenv("MONGO_URI", "{mongo_uri}")
try:
    _client=MongoClient(MONGO_URI,serverSelectionTimeoutMS=5000)
    _db=_client.get_database("formcraft"); _ok=True
except Exception as e:
    print(f"offline: {{e}}"); _db=None; _ok=False
_FORMS={fj}; _NL={nj}
def get_forms(uid=None):
    if _ok: return list(_db.forms.find({{"user_id":uid}} if uid else {{}}))
    return _FORMS
def get_responses(fid):
    if _ok: return list(_db.responses.find({{"form_id":str(fid)}}))
    return []
def get_newsletters(uid=None):
    if _ok: return list(_db.newsletters.find({{"user_id":uid}} if uid else {{}}))
    return _NL
def is_connected(): return _ok
'''
    req = next((k for k in out if k.lower()=='requirements.txt'), None)
    pkgs= ['pymongo==4.6.1','python-dotenv==1.0.0','dnspython==2.4.2']
    if req:
        ex=out[req]
        out[req]=ex.rstrip()+'\n'+'\n'.join(p for p in pkgs if p.split('=')[0] not in ex)+'\n'
    else:
        out['requirements.txt']='flask\n'+'\n'.join(pkgs)+'\ngunicorn\n'
    return out


def _inject_react(files: dict, data_json: str, mongo_uri: str) -> dict:
    out = dict(files)
    out['.env'] = f'REACT_APP_MONGO_URI={mongo_uri}\n'
    out['src/formcraft/data.js'] = (
        f'export const FORMCRAFT_DATA={data_json};\n'
        f'export const FORMS=FORMCRAFT_DATA.forms;\n'
        f'export const NL=FORMCRAFT_DATA.newsletters;\n'
    )
    out['src/formcraft/db.js'] = f'''const URI=process.env.REACT_APP_MONGO_URI||"{mongo_uri}";
async function q(col,f={{}}){{const r=await fetch(`${{URI}}/action/find`,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{collection:col,database:'formcraft',filter:f}})}});const d=await r.json();return d.documents||[];}}
export const fetchForms=(uid)=>q('forms',uid?{{user_id:uid}}:{{}});
export const fetchNL=(uid)=>q('newsletters',uid?{{user_id:uid}}:{{}});
export default{{fetchForms,fetchNL}};'''
    if 'package.json' in out:
        try:
            pkg=json.loads(out['package.json'])
            pkg.setdefault('dependencies',{})['mongodb']='^6.0.0'
            out['package.json']=json.dumps(pkg,indent=2)
        except Exception: pass
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — disk I/O
# ═══════════════════════════════════════════════════════════════════════════════
def _write_to_disk(slug: str, files: dict):
    site_dir = _site_dir(slug)
    if os.path.exists(site_dir): shutil.rmtree(site_dir)
    os.makedirs(site_dir, exist_ok=True)
    for rel, content in files.items():
        rel = rel.lstrip('/').replace('..','')
        if not rel: continue
        full = os.path.join(site_dir, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        if isinstance(content, str):
            with open(full,'w',encoding='utf-8',errors='replace') as f: f.write(content)
        else:
            with open(full,'wb') as f: f.write(content)


def _read_from_disk(slug: str) -> dict:
    site_dir = _site_dir(slug)
    if not os.path.isdir(site_dir): return {}
    out = {}
    TEXT = {'html','htm','css','js','json','txt','md','py','env','yaml','yml'}
    for root, dirs, fnames in os.walk(site_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in fnames:
            full = os.path.join(root, fname)
            rel  = os.path.relpath(full, site_dir)
            ext  = fname.rsplit('.',1)[-1].lower() if '.' in fname else ''
            if ext in TEXT:
                try:
                    with open(full, encoding='utf-8', errors='replace') as f:
                        out[rel] = f.read()
                except Exception: pass
    return out


def _list_disk_files(slug: str) -> list:
    site_dir = _site_dir(slug)
    result = []
    if not os.path.isdir(site_dir): return result
    for root, dirs, fnames in os.walk(site_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in fnames:
            full = os.path.join(root, fname)
            rel  = os.path.relpath(full, site_dir)
            result.append({'path': rel, 'size': os.path.getsize(full)})
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — GitHub fetch
# ═══════════════════════════════════════════════════════════════════════════════
def _fetch_github(repo_url: str) -> dict:
    """
    Fetch a public GitHub repo as a ZIP and return flat dict of path→bytes.
    Accepts:  https://github.com/user/repo
              https://github.com/user/repo/tree/branch
    """
    url = repo_url.strip().rstrip('/')
    # Extract owner/repo
    m = re.search(r'github\.com/([^/]+/[^/]+?)(?:/tree/([^/\s]+))?$', url)
    if not m:
        raise ValueError('Invalid GitHub URL. Use: https://github.com/owner/repo')
    repo_path = m.group(1).rstrip('.git')
    branch    = m.group(2) or 'main'

    zip_url = f'https://github.com/{repo_path}/archive/refs/heads/{branch}.zip'
    try:
        req = urllib.request.Request(zip_url, headers={'User-Agent': 'FORMAI-Deploy/1.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
    except Exception:
        # Try 'master' branch
        zip_url = f'https://github.com/{repo_path}/archive/refs/heads/master.zip'
        req = urllib.request.Request(zip_url, headers={'User-Agent': 'FORMAI-Deploy/1.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()

    raw_files = {}
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            if name.endswith('/'): continue
            raw_files[name] = zf.read(name)

    return _strip_zip_prefix(raw_files)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — auto-generate site
# ═══════════════════════════════════════════════════════════════════════════════
def _autogen_site(user_data: dict, user_name: str, title: str, accent='#FF8C00') -> dict:
    forms = user_data['forms'];  nl = user_data['newsletters']
    acc   = accent

    css = f"""<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--acc:{acc};--dark:#1A1A2E;--card:#fff;--bd:#E8E4DE;--light:#F8F7F4}}
body{{font-family:'Segoe UI',sans-serif;background:var(--light);color:#212529;line-height:1.6}}
a{{color:var(--acc);text-decoration:none}}
nav{{background:var(--dark);height:54px;padding:0 32px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:99;box-shadow:0 2px 12px rgba(0,0,0,.3)}}
.brand{{font-size:1.05rem;font-weight:700;color:#fff}}.brand span{{color:var(--acc)}}
.nav-links a{{padding:7px 14px;border-radius:8px;font-size:.82rem;color:rgba(255,255,255,.55);border:1px solid rgba(255,255,255,.1);margin-left:4px;transition:.15s}}
.nav-links a:hover{{color:#fff;border-color:var(--acc)}}
.hero{{background:var(--dark);padding:72px 32px;text-align:center}}
.hero h1{{font-size:clamp(1.8rem,5vw,3.2rem);font-weight:800;color:#fff;margin-bottom:12px}}
.hero p{{color:rgba(255,255,255,.55);max-width:500px;margin:0 auto 28px}}
.btn{{display:inline-block;padding:12px 28px;border-radius:40px;font-weight:700;font-size:.92rem;text-decoration:none;transition:.2s}}
.btn-p{{background:var(--acc);color:#fff;box-shadow:0 6px 20px rgba(255,140,0,.3)}}
.btn-g{{background:transparent;color:#fff;border:2px solid rgba(255,255,255,.25)}}
.hero-cta{{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}}
.wrap{{max-width:1060px;margin:0 auto;padding:48px 24px}}
.sec-title{{font-size:1.35rem;font-weight:700;margin-bottom:18px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px;margin-bottom:40px}}
.stat{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:18px;border-left:4px solid var(--acc)}}
.stat .n{{font-size:2rem;font-weight:800;color:var(--acc);line-height:1}}
.stat .l{{font-size:.7rem;color:#aaa;text-transform:uppercase;letter-spacing:.07em;margin-top:3px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:14px;overflow:hidden;transition:.2s}}
.card:hover{{box-shadow:0 6px 24px rgba(0,0,0,.09);transform:translateY(-2px)}}
.c-cover{{height:110px;background:var(--dark);display:flex;align-items:center;justify-content:center;position:relative}}
.c-cover img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.badge{{position:absolute;top:9px;right:9px;padding:2px 9px;border-radius:20px;font-size:.66rem;font-weight:700;background:rgba(45,106,79,.85);color:#fff}}
.badge.d{{background:rgba(0,0,0,.45);color:rgba(255,255,255,.6)}}
.c-body{{padding:14px 16px}}
.c-name{{font-weight:700;font-size:.9rem;margin-bottom:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.c-meta{{font-size:.75rem;color:#aaa}}
.c-foot{{padding:10px 16px;border-top:1px solid var(--bd)}}
footer{{background:var(--dark);padding:28px;text-align:center;color:rgba(255,255,255,.3);font-size:.78rem;margin-top:60px}}
footer span{{color:var(--acc)}}
</style>"""

    nav  = f'<nav><div class="brand">◈ {title}</div><div class="nav-links"><a href="index.html">Home</a><a href="forms.html">Forms</a><a href="newsletters.html">Newsletters</a></div></nav>'
    foot = f'<footer>Built with <span>◈ FORM.AI</span> by {user_name}</footer>'

    tr   = sum(len(f.get('responses',[])) for f in forms)
    lf   = sum(1 for f in forms if f.get('settings',{}).get('is_published'))

    def fcard(f):
        hdr  = f.get('theme',{}).get('header_color','#1A1A2E')
        img  = f.get('theme',{}).get('cover_image','')
        live = f.get('settings',{}).get('is_published',False)
        rc   = len(f.get('responses',[])); pc = len(f.get('pages',[]))
        slug = f.get('slug','')
        img_tag = f'<img src="{img}" alt="">' if img and img.startswith('http') else ''
        badge   = '<span class="badge">Live</span>' if live else '<span class="badge d">Draft</span>'
        foot_lnk= f'<div class="c-foot"><a href="/f/{slug}" class="btn btn-p" style="font-size:.78rem;padding:7px 16px" target="_blank">Open →</a></div>' if live else ''
        return f'<div class="card"><div class="c-cover" style="background:{hdr}">{img_tag}{badge}</div><div class="c-body"><div class="c-name">{f.get("title","Untitled")}</div><div class="c-meta">{pc} page{"s" if pc!=1 else ""} · {rc} response{"s" if rc!=1 else ""}</div></div>{foot_lnk}</div>'

    def ncard(n):
        hdr = n.get('theme',{}).get('header_color','#1A1A2E')
        bc  = len(n.get('blocks',[]))
        return f'<div class="card"><div class="c-cover" style="background:{hdr}"><span style="font-size:1.8rem">📰</span></div><div class="c-body"><div class="c-name">{n.get("title","Untitled")}</div><div class="c-meta">{bc} block{"s" if bc!=1 else ""}</div></div></div>'

    def pg(t, body):
        return f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{t}</title>{css}</head><body>{nav}{body}{foot}</body></html>'

    idx = (f'<div class="hero"><h1>{title}</h1><p>Your forms and newsletters, all in one place.</p>'
           f'<div class="hero-cta"><a href="forms.html" class="btn btn-p">View Forms →</a><a href="newsletters.html" class="btn btn-g">Newsletters</a></div></div>'
           f'<div class="wrap"><div class="stats">'
           f'<div class="stat"><div class="n">{len(forms)}</div><div class="l">Forms</div></div>'
           f'<div class="stat"><div class="n">{lf}</div><div class="l">Live</div></div>'
           f'<div class="stat"><div class="n">{tr}</div><div class="l">Responses</div></div>'
           f'<div class="stat"><div class="n">{len(nl)}</div><div class="l">Newsletters</div></div>'
           f'</div>'
           +(f'<div class="sec-title">Recent Forms</div><div class="grid">{"".join(fcard(f) for f in forms[:6])}</div>' if forms else '<p style="color:#aaa;text-align:center;padding:40px">No forms yet.</p>')
           +(f'<div class="sec-title" style="margin-top:36px">Newsletters</div><div class="grid">{"".join(ncard(n) for n in nl[:3])}</div>' if nl else '')
           +'</div>')

    frm = (f'<div class="hero" style="padding:40px 32px"><h1 style="font-size:2rem">📋 Forms</h1><p style="color:rgba(255,255,255,.5)">{len(forms)} total · {lf} live · {tr} responses</p></div>'
           f'<div class="wrap">{"<div class=grid>"+"".join(fcard(f) for f in forms)+"</div>" if forms else "<p style=color:#aaa;text-align:center;padding:40px>No forms.</p>"}</div>')

    nls = (f'<div class="hero" style="padding:40px 32px"><h1 style="font-size:2rem">📰 Newsletters</h1></div>'
           f'<div class="wrap">{"<div class=grid>"+"".join(ncard(n) for n in nl)+"</div>" if nl else "<p style=color:#aaa;text-align:center;padding:40px>No newsletters.</p>"}</div>')

    data = json.dumps({
        'generated_at': datetime.utcnow().isoformat(), 'user': user_name,
        'forms': [{'id': f['_id'],'title':f.get('title'),'slug':f.get('slug'),
                   'responses':len(f.get('responses',[])), 'pages':len(f.get('pages',[]))} for f in forms],
        'newsletters': [{'id':n['_id'],'title':n.get('title')} for n in nl],
    }, indent=2, default=str)

    return {'index.html': pg(title, idx), 'forms.html': pg(f'Forms — {title}', frm),
            'newsletters.html': pg(f'Newsletters — {title}', nls), 'data.json': data}


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC SERVING  /sites/<slug>/[path]
# ═══════════════════════════════════════════════════════════════════════════════
@deploy_bp.route('/sites/<slug>', strict_slashes=False)
@deploy_bp.route('/sites/<slug>/', defaults={'path': ''})
@deploy_bp.route('/sites/<slug>/<path:path>')
def serve_site(slug, path=''):
    doc = _col().find_one({'slug': slug})
    if not doc:
        return Response(
            f'<html><body style="font-family:sans-serif;padding:60px;text-align:center">'
            f'<h2 style="color:#E63946">Site not found: <code>/sites/{slug}/</code></h2>'
            f'<p><a href="/deploy" style="color:#FF8C00">← Deploy page</a></p></body></html>',
            mimetype='text/html;charset=utf-8', status=404)

    if not doc.get('is_published'):
        from flask_login import current_user as cu
        if not cu.is_authenticated or str(cu.id) != str(doc.get('user_id')):
            return Response('<html><body style="font-family:sans-serif;padding:60px;text-align:center">'
                            '<h2 style="color:#aaa">🔒 This site is not published yet.</h2></body></html>',
                            mimetype='text/html;charset=utf-8', status=403)

    site_dir = _site_dir(slug)
    if not os.path.isdir(site_dir):
        return Response('<html><body style="font-family:sans-serif;padding:60px;text-align:center">'
                        '<h2 style="color:#E63946">⚠ Site files missing — please re-deploy.</h2>'
                        '<p><a href="/deploy" style="color:#FF8C00">← Deploy page</a></p></body></html>',
                        mimetype='text/html;charset=utf-8', status=500)

    if not path: path = 'index.html'

    fp = os.path.realpath(os.path.join(site_dir, path))
    if not fp.startswith(os.path.realpath(site_dir)): abort(403)

    if os.path.isdir(fp): fp = os.path.join(fp, 'index.html')

    if not os.path.isfile(fp):
        ext = path.rsplit('.',1)[-1].lower() if '.' in path else ''
        ASSETS = {'css','js','png','jpg','jpeg','gif','svg','ico','woff','woff2',
                  'ttf','eot','otf','mp4','webm','mp3','pdf','json'}
        if ext in ASSETS:
            return Response(f'/* not found: {path} */', status=404,
                            mimetype='text/css' if ext=='css' else 'application/javascript')
        # SPA fallback
        fb = os.path.join(site_dir, 'index.html')
        if os.path.isfile(fb): fp = fb
        else: return Response(f'<h3 style="font-family:sans-serif;padding:40px;color:#aaa">Not found: {path}</h3>',
                              mimetype='text/html;charset=utf-8', status=404)

    MIME = {
        'html':'text/html;charset=utf-8','htm':'text/html;charset=utf-8',
        'css':'text/css;charset=utf-8','js':'application/javascript;charset=utf-8',
        'json':'application/json','png':'image/png','jpg':'image/jpeg',
        'jpeg':'image/jpeg','gif':'image/gif','svg':'image/svg+xml',
        'ico':'image/x-icon','woff':'font/woff','woff2':'font/woff2',
        'ttf':'font/ttf','pdf':'application/pdf','txt':'text/plain',
        'mp4':'video/mp4','webm':'video/webm','mp3':'audio/mpeg',
    }
    ext  = fp.rsplit('.',1)[-1].lower() if '.' in fp else ''
    mime = MIME.get(ext, 'application/octet-stream')
    with open(fp,'rb') as fh: data = fh.read()
    resp = Response(data, mimetype=mime)
    resp.headers['Cache-Control'] = 'no-cache'
    return resp


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
@deploy_bp.route('/deploy')
@login_required
def deploy_index():
    default_uri = _app_mongo_uri()
    sites = list(_col().find({'user_id': current_user.id}).sort('updated_at',-1))
    for s in sites:
        s['_id'] = str(s['_id'])
        for k in ('created_at','updated_at','published_at'):
            if isinstance(s.get(k), datetime): s[k] = s[k].isoformat()
    return render_template('deploy/index.html', default_mongo_uri=default_uri, sites=sites)


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYZE — detect framework, list HTML files
# ═══════════════════════════════════════════════════════════════════════════════
@deploy_bp.route('/deploy/analyze', methods=['POST'])
@login_required
def deploy_analyze():
    source = request.form.get('source','zip')   # 'zip' | 'html' | 'git'

    raw_files    = {}  # flat path → bytes
    file_contents= {}  # basename → text (for detection)

    try:
        if source == 'git':
            repo_url = request.form.get('git_url','').strip()
            if not repo_url: return jsonify({'success':False,'error':'GitHub URL required'})
            raw_files = _fetch_github(repo_url)

        elif source == 'html':
            uploaded_files = request.files.getlist('files')
            if not uploaded_files: return jsonify({'success':False,'error':'No files uploaded'})
            for uf in uploaded_files:
                fname = os.path.basename(uf.filename)
                raw_files[fname] = uf.read()

        else:  # zip
            zf_file = request.files.get('folder')
            if not zf_file: return jsonify({'success':False,'error':'No ZIP uploaded'})
            if not zf_file.filename.lower().endswith('.zip'):
                return jsonify({'success':False,'error':'Please upload a .zip file'})
            zf_file.stream.seek(0)
            tmp_raw = {}
            with zipfile.ZipFile(zf_file.stream,'r') as zf:
                for name in zf.namelist():
                    if name.endswith('/'): continue
                    tmp_raw[name] = zf.read(name)
            raw_files = _strip_zip_prefix(tmp_raw)

    except Exception as e:
        return jsonify({'success':False,'error':str(e)})

    # Build file_contents for framework detection
    TEXT_DETECT = ('.py','.js','.ts','.json','.txt','.html','.htm','.env','pipfile','requirements.txt')
    for path, raw in raw_files.items():
        lb = path.lower().split('/')[-1]
        if any(lb.endswith(e) for e in TEXT_DETECT):
            try: file_contents[lb] = raw[:51200].decode('utf-8',errors='replace')
            except Exception: pass

    fw      = _detect_fw(list(raw_files.keys()), file_contents)
    exts    = {}
    for f in raw_files:
        if '.' in f:
            e = f.rsplit('.',1)[-1].lower(); exts[e] = exts.get(e,0)+1

    html_files = sorted(p for p in raw_files if p.lower().endswith(('.html','.htm')))
    has_db     = any(k in '\n'.join(file_contents.values())
                     for k in ('MongoClient','mongoose','pymongo','DATABASES','sqlite'))

    # Get index.html preview
    preview_html = ''
    for candidate in ('index.html','index.htm','home.html','main.html'):
        if candidate in raw_files:
            try: preview_html = raw_files[candidate].decode('utf-8',errors='replace'); break
            except Exception: pass
    if not preview_html and html_files:
        try: preview_html = raw_files[html_files[0]].decode('utf-8',errors='replace')
        except Exception: pass

    return jsonify({
        'success':      True,
        'framework':    fw,
        'file_count':   len(raw_files),
        'extensions':   exts,
        'has_db':       has_db,
        'html_files':   html_files,
        'index_preview': preview_html[:60000],
        'can_convert':  fw == 'html',   # only offer Flask conversion for HTML sites
    })


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOAD → PROCESS → SAVE DRAFT
# ═══════════════════════════════════════════════════════════════════════════════
@deploy_bp.route('/deploy/upload', methods=['POST'])
@login_required
def deploy_upload():
    source     = request.form.get('source','zip')
    mongo_uri  = (request.form.get('mongo_uri','') or _app_mongo_uri()).strip()
    homepage   = request.form.get('homepage','index.html').strip()
    convert_to_flask = request.form.get('convert_flask','').lower() in ('1','true','yes')
    site_title = request.form.get('site_title','').strip() or 'My Site'

    try:
        user_data = _user_data(current_user.id)
    except Exception as e:
        return jsonify({'success':False,'error':f'DB error: {e}'})

    data_json = json.dumps(user_data, default=str)

    # ── Fetch raw files ──────────────────────────────────────────────────────
    raw_files = {}
    try:
        if source == 'git':
            repo_url = request.form.get('git_url','').strip()
            raw_files = _fetch_github(repo_url)

        elif source == 'html':
            for uf in request.files.getlist('files'):
                raw_files[os.path.basename(uf.filename)] = uf.read()

        else:
            zf_file = request.files.get('folder')
            tmp = {}
            with zipfile.ZipFile(zf_file.stream,'r') as zf:
                for name in zf.namelist():
                    if name.endswith('/'): continue
                    tmp[name] = zf.read(name)
            raw_files = _strip_zip_prefix(tmp)
    except Exception as e:
        return jsonify({'success':False,'error':str(e)})

    # ── Detect framework ─────────────────────────────────────────────────────
    file_contents = {}
    TEXT_DETECT = ('.py','.js','.ts','.json','.txt','.html','.htm','.env')
    for path, raw in raw_files.items():
        lb = path.lower().split('/')[-1]
        if any(lb.endswith(e) for e in TEXT_DETECT):
            try: file_contents[lb] = raw[:51200].decode('utf-8',errors='replace')
            except Exception: pass

    fw = _detect_fw(list(raw_files.keys()), file_contents)

    # ── Split text / binary ──────────────────────────────────────────────────
    TEXT_EXTS = {'.py','.js','.ts','.jsx','.tsx','.html','.htm','.css',
                 '.json','.txt','.md','.env','.cfg','.ini','.yaml','.yml','.sh'}
    text_files = {}; binary_files = {}
    for path, raw in raw_files.items():
        ext = os.path.splitext(path)[-1].lower()
        if ext in TEXT_EXTS or os.path.basename(path).lower() in ('pipfile','dockerfile','requirements.txt','procfile'):
            try:    text_files[path] = raw.decode('utf-8',errors='replace')
            except: binary_files[path] = raw
        else:
            binary_files[path] = raw

    # ── If user chose a homepage that's not index.html, copy it ─────────────
    if homepage and homepage != 'index.html' and homepage in text_files:
        text_files['index.html'] = _fix_paths(text_files[homepage])

    # Ensure index.html exists
    if 'index.html' not in text_files:
        for cand in ('index.htm','home.html','main.html','default.html'):
            if cand in text_files:
                text_files['index.html'] = _fix_paths(text_files[cand]); break
        else:
            html_any = next((k for k in text_files if k.lower().endswith(('.html','.htm'))),None)
            if html_any:
                text_files['index.html'] = _fix_paths(text_files[html_any])

    # ── Inject / convert ─────────────────────────────────────────────────────
    effective_fw = fw
    if convert_to_flask and fw == 'html':
        text_files   = _inject_flask_conversion(text_files, data_json, mongo_uri,
                                                user_data, homepage or 'index.html')
        effective_fw = 'flask'
    elif fw == 'react':
        text_files   = _inject_react(text_files, data_json, mongo_uri)
    elif fw == 'flask':
        text_files   = _inject_existing_flask(text_files, data_json, mongo_uri, user_data)
    else:
        text_files   = _inject_html(text_files, data_json, mongo_uri)

    # ── Merge and write to disk ───────────────────────────────────────────────
    all_files = {p: c.encode('utf-8',errors='replace') if isinstance(c,str) else c
                 for p,c in text_files.items()}
    all_files.update(binary_files)

    draft_slug = 'draft-' + uuid.uuid4().hex[:12]
    now = datetime.utcnow()

    _write_to_disk(draft_slug, all_files)

    html_files_flat = sorted(p for p in all_files if p.lower().endswith(('.html','.htm')))

    # Preview from disk
    index_preview = ''
    if 'index.html' in text_files:
        index_preview = text_files['index.html'] if isinstance(text_files['index.html'],str) else ''

    doc = {
        'user_id':      current_user.id,
        'slug':         draft_slug,
        'title':        site_title,
        'framework':    effective_fw,
        'source':       source,
        'mongo_uri':    mongo_uri,
        'homepage':     homepage,
        'is_published': False,
        'is_draft':     True,
        'converted_to_flask': convert_to_flask,
        'html_files':   html_files_flat,
        'file_count':   len(all_files),
        'created_at':   now,
        'updated_at':   now,
    }
    res = _col().insert_one(doc)

    return jsonify({
        'success':       True,
        'site_id':       str(res.inserted_id),
        'draft_slug':    draft_slug,
        'framework':     effective_fw,
        'converted':     convert_to_flask,
        'file_count':    len(all_files),
        'html_files':    html_files_flat,
        'index_preview': index_preview[:80000],
    })


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-GENERATE
# ═══════════════════════════════════════════════════════════════════════════════
@deploy_bp.route('/deploy/generate', methods=['POST'])
@login_required
def deploy_generate():
    data  = request.get_json(silent=True) or {}
    title = (data.get('site_title') or f"{current_user.name}'s Site")[:80]
    acc   = data.get('accent_color','#FF8C00') or '#FF8C00'
    if not re.match(r'^#[0-9A-Fa-f]{6}$', acc): acc = '#FF8C00'
    try:
        ud = _user_data(current_user.id)
        files = _autogen_site(ud, current_user.name, title, acc)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as zf:
            for n,c in files.items(): zf.writestr(n,c)
        buf.seek(0)
        safe = re.sub(r'[^a-z0-9_]','_',title.lower())[:30]
        return send_file(buf, mimetype='application/zip', as_attachment=True,
                         download_name=f'{safe}.zip')
    except Exception as e:
        return jsonify({'success':False,'error':str(e)})


@deploy_bp.route('/deploy/preview-generated', methods=['POST'])
@login_required
def preview_generated():
    data  = request.get_json(silent=True) or {}
    title = (data.get('site_title') or f"{current_user.name}'s Site")[:80]
    acc   = data.get('accent_color','#FF8C00') or '#FF8C00'
    if not re.match(r'^#[0-9A-Fa-f]{6}$', acc): acc = '#FF8C00'
    try:
        ud    = _user_data(current_user.id)
        files = _autogen_site(ud, current_user.name, title, acc)
        return jsonify({'success':True,'html':files['index.html']})
    except Exception as e:
        return jsonify({'success':False,'error':str(e)})


@deploy_bp.route('/deploy/publish-generated', methods=['POST'])
@login_required
def publish_generated():
    data  = request.get_json(silent=True) or {}
    title = (data.get('site_title') or f"{current_user.name}'s Site")[:80]
    acc   = data.get('accent_color','#FF8C00') or '#FF8C00'
    if not re.match(r'^#[0-9A-Fa-f]{6}$', acc): acc = '#FF8C00'
    try:
        ud    = _user_data(current_user.id)
        files = _autogen_site(ud, current_user.name, title, acc)
    except Exception as e:
        return jsonify({'success':False,'error':str(e)})

    draft_slug = 'draft-' + uuid.uuid4().hex[:12]
    disk_files = {k:(v.encode('utf-8') if isinstance(v,str) else v) for k,v in files.items()}
    _write_to_disk(draft_slug, disk_files)
    now = datetime.utcnow()
    doc = {'user_id':current_user.id,'slug':draft_slug,'title':title,'framework':'html',
           'is_published':False,'is_draft':True,'created_at':now,'updated_at':now,'file_count':len(files)}
    res = _col().insert_one(doc)
    return jsonify({'success':True,'site_id':str(res.inserted_id),'draft_slug':draft_slug})


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLISH / UNPUBLISH / DELETE
# ═══════════════════════════════════════════════════════════════════════════════
@deploy_bp.route('/deploy/publish', methods=['POST'])
@login_required
def deploy_publish():
    from bson import ObjectId
    data    = request.get_json(silent=True) or {}
    site_id = data.get('site_id','')
    slug_in = _slugify(data.get('slug',''))
    title   = data.get('title','My Site')
    if not site_id or not slug_in:
        return jsonify({'success':False,'error':'site_id and slug required'})
    try:
        doc = _col().find_one({'_id':ObjectId(site_id),'user_id':current_user.id})
    except Exception:
        return jsonify({'success':False,'error':'Not found'})
    if not doc: return jsonify({'success':False,'error':'Not found'})

    final = _unique_slug(slug_in, exclude_id=site_id)
    old   = doc['slug']
    if old != final:
        od = _site_dir(old); nd = _site_dir(final)
        if os.path.isdir(od):
            if os.path.isdir(nd): shutil.rmtree(nd)
            shutil.move(od, nd)

    now = datetime.utcnow()
    _col().update_one({'_id':ObjectId(site_id)},
                      {'$set':{'slug':final,'title':title,'is_published':True,
                               'is_draft':False,'published_at':now,'updated_at':now}})
    return jsonify({'success':True,'slug':final,'live_url':f'/sites/{final}/'})


@deploy_bp.route('/deploy/unpublish', methods=['POST'])
@login_required
def deploy_unpublish():
    from bson import ObjectId
    data = request.get_json(silent=True) or {}
    try:
        doc = _col().find_one({'_id':ObjectId(data.get('site_id','')),'user_id':current_user.id})
    except Exception: return jsonify({'success':False,'error':'Not found'})
    if not doc: return jsonify({'success':False,'error':'Not found'})
    _col().update_one({'_id':doc['_id']},{'$set':{'is_published':False,'updated_at':datetime.utcnow()}})
    return jsonify({'success':True})


@deploy_bp.route('/deploy/delete', methods=['POST'])
@login_required
def deploy_delete():
    from bson import ObjectId
    data = request.get_json(silent=True) or {}
    try:
        doc = _col().find_one({'_id':ObjectId(data.get('site_id','')),'user_id':current_user.id})
    except Exception: return jsonify({'success':False,'error':'Not found'})
    if not doc: return jsonify({'success':False,'error':'Not found'})
    sd = _site_dir(doc.get('slug',''))
    if os.path.isdir(sd): shutil.rmtree(sd)
    _col().delete_one({'_id':doc['_id']})
    return jsonify({'success':True})


# ═══════════════════════════════════════════════════════════════════════════════
# EDITOR
# ═══════════════════════════════════════════════════════════════════════════════
@deploy_bp.route('/deploy/site/<site_id>/files')
@login_required
def site_files(site_id):
    from bson import ObjectId
    try: doc = _col().find_one({'_id':ObjectId(site_id),'user_id':current_user.id})
    except Exception: return jsonify({'success':False,'error':'Not found'})
    if not doc: return jsonify({'success':False,'error':'Not found'})
    return jsonify({'success':True,'files':_read_from_disk(doc['slug']),
                    'all_files':_list_disk_files(doc['slug'])})


@deploy_bp.route('/deploy/site/<site_id>/save-file', methods=['POST'])
@login_required
def site_save_file(site_id):
    from bson import ObjectId
    try: doc = _col().find_one({'_id':ObjectId(site_id),'user_id':current_user.id})
    except Exception: return jsonify({'success':False,'error':'Not found'})
    if not doc: return jsonify({'success':False,'error':'Not found'})
    d = request.get_json(silent=True) or {}
    fname = d.get('filename','').lstrip('/').replace('..','')
    if not fname: return jsonify({'success':False,'error':'No filename'})
    full = os.path.join(_site_dir(doc['slug']), fname)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full,'w',encoding='utf-8',errors='replace') as f: f.write(d.get('content',''))
    _col().update_one({'_id':doc['_id']},{'$set':{'updated_at':datetime.utcnow()}})
    return jsonify({'success':True})


@deploy_bp.route('/deploy/download/<site_id>')
@login_required
def deploy_download(site_id):
    from bson import ObjectId
    try: doc = _col().find_one({'_id':ObjectId(site_id),'user_id':current_user.id})
    except Exception: abort(404)
    if not doc: abort(404)
    site_dir = _site_dir(doc['slug'])
    if not os.path.isdir(site_dir): abort(404)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as zf:
        for root,dirs,fnames in os.walk(site_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for fn in fnames:
                full = os.path.join(root,fn)
                zf.write(full, os.path.relpath(full, site_dir))
    buf.seek(0)
    safe = re.sub(r'[^a-z0-9_-]','_',doc.get('title','site').lower())[:40]
    return send_file(buf,mimetype='application/zip',as_attachment=True,
                     download_name=f'{safe}.zip')


@deploy_bp.route('/deploy/edit/<site_id>')
@login_required
def deploy_edit(site_id):
    from bson import ObjectId
    try: doc = _col().find_one({'_id':ObjectId(site_id),'user_id':current_user.id})
    except Exception: abort(404)
    if not doc: abort(404)
    doc['_id'] = str(doc['_id'])
    return render_template('deploy/editor.html', site=doc,
                           files=_read_from_disk(doc['slug']))


@deploy_bp.route('/deploy/debug')
@login_required
def deploy_debug():
    sr = _sites_root()
    on_disk = []
    if os.path.isdir(sr):
        for name in os.listdir(sr):
            d = os.path.join(sr,name)
            if os.path.isdir(d):
                fc = sum(len(ff) for _,_,ff in os.walk(d))
                on_disk.append({'slug':name,'files':fc})
    in_db = [{'_id':str(s['_id']),'slug':s.get('slug'),'published':s.get('is_published')}
             for s in _col().find({'user_id':current_user.id})]
    return jsonify({'sites_root':sr,'on_disk':on_disk,'in_db':in_db})


# ═══════════════════════════════════════════════════════════════════════════════
# DATA VIEWER  — /deploy/data  (Excel-style view of all form responses)
# ═══════════════════════════════════════════════════════════════════════════════
@deploy_bp.route('/deploy/data-test')
@login_required  
def data_viewer_test():
    """Diagnostic — shows the real error without the 500 handler masking it."""
    import traceback
    try:
        forms_raw = list(_db().forms.find({'user_id': current_user.id}))
        result = {'db_ok': True, 'form_count': len(forms_raw)}
        
        # Test template exists
        import os
        from flask import current_app
        tpl_path = os.path.join(current_app.root_path, 'templates', 'deploy', 'data_viewer.html')
        result['template_exists'] = os.path.isfile(tpl_path)
        result['template_path'] = tpl_path
        
        # Test responses collection
        total_r = _db().responses.count_documents({})
        result['total_responses_in_db'] = total_r
        
        # Test form serialization
        form_list = []
        for f in forms_raw:
            fid = str(f['_id'])
            created_at = f.get('created_at','')
            if isinstance(created_at, datetime):
                created_at = created_at.strftime('%Y-%m-%d')
            form_list.append({'_id': fid, 'title': f.get('title',''), 
                              'created_at': str(created_at)[:10]})
        result['forms'] = form_list
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()})


@deploy_bp.route('/deploy/data')
@login_required
def data_viewer():
    """Main data viewer dashboard — lists all forms with response counts."""
    try:
        forms_raw = list(_db().forms.find({'user_id': current_user.id}))
    except Exception as e:
        import traceback; traceback.print_exc()
        forms_raw = []

    form_list = []
    for f in forms_raw:
        try:
            fid   = str(f['_id'])
            count = _db().responses.count_documents({'form_id': fid})

            # Safely serialize created_at
            created_at = f.get('created_at', '')
            if isinstance(created_at, datetime):
                created_at = created_at.strftime('%Y-%m-%d')
            elif isinstance(created_at, str) and 'T' in created_at:
                created_at = created_at[:10]
            else:
                created_at = str(created_at)[:10] if created_at else ''

            form_list.append({
                '_id':            fid,
                'title':          f.get('title', 'Untitled'),
                'slug':           f.get('slug', ''),
                'is_published':   f.get('settings', {}).get('is_published', False),
                'response_count': count,
                'pages':          len(f.get('pages', [])),
                'created_at':     created_at,
            })
        except Exception as e:
            import traceback; traceback.print_exc()
            continue

    form_list.sort(key=lambda x: x['response_count'], reverse=True)
    return render_template('deploy/data_viewer.html', forms=form_list)


@deploy_bp.route('/deploy/data/<form_id>')
@login_required
def form_data(form_id):
    """Excel-style table view of all responses for a specific form."""
    from bson import ObjectId
    try:
        form = _db().forms.find_one({'_id': ObjectId(form_id), 'user_id': current_user.id})
    except Exception:
        abort(404)
    if not form:
        abort(404)

    # Get all responses
    responses = list(_db().responses.find({'form_id': form_id}).sort('submitted_at', -1))

    # Build column headers from all questions across all pages
    columns = []
    seen_keys = set()
    for page in form.get('pages', []):
        for q in page.get('questions', []):
            key = q.get('id') or q.get('label') or q.get('question', '')
            label = q.get('label') or q.get('question') or key
            if key and key not in seen_keys:
                seen_keys.add(key)
                columns.append({'key': key, 'label': label, 'type': q.get('type', 'text')})

    # If no columns from schema, derive from responses
    if not columns:
        all_keys = set()
        for r in responses:
            ans = r.get('answers') or r.get('data') or {}
            if isinstance(ans, dict):
                all_keys.update(ans.keys())
        for k in sorted(all_keys):
            columns.append({'key': k, 'label': k, 'type': 'text'})

    # Build rows
    rows = []
    for r in responses:
        rid  = str(r['_id'])
        ans  = r.get('answers') or r.get('data') or {}
        ts   = r.get('submitted_at') or r.get('created_at', '')
        if isinstance(ts, datetime): ts = ts.strftime('%Y-%m-%d %H:%M')
        elif isinstance(ts, str) and 'T' in ts: ts = ts.replace('T', ' ')[:16]
        rows.append({
            '_id':         rid,
            'submitted_at': ts,
            'answers':     ans,
        })

    form['_id'] = str(form['_id'])
    return render_template('deploy/form_data.html',
                           form=form, columns=columns, rows=rows)


@deploy_bp.route('/deploy/data/<form_id>/export-excel')
@login_required
def export_excel(form_id):
    """Export form responses as Excel (.xlsx) using openpyxl."""
    from bson import ObjectId
    try:
        import openpyxl
        from openpyxl.styles import (Font, PatternFill, Alignment,
                                     Border, Side, GradientFill)
        from openpyxl.utils import get_column_letter
    except ImportError:
        return jsonify({'error': 'openpyxl not installed. Run: pip install openpyxl'}), 500

    try:
        form = _db().forms.find_one({'_id': ObjectId(form_id), 'user_id': current_user.id})
    except Exception:
        abort(404)
    if not form: abort(404)

    responses = list(_db().responses.find({'form_id': form_id}).sort('submitted_at', -1))

    # Build columns
    columns = []
    seen = set()
    for page in form.get('pages', []):
        for q in page.get('questions', []):
            key   = q.get('id') or q.get('label') or q.get('question', '')
            label = q.get('label') or q.get('question') or key
            if key and key not in seen:
                seen.add(key); columns.append((key, label))
    if not columns:
        all_keys = set()
        for r in responses:
            ans = r.get('answers') or r.get('data') or {}
            if isinstance(ans, dict): all_keys.update(ans.keys())
        for k in sorted(all_keys): columns.append((k, k))

    # ── Build workbook ───────────────────────────────────────────────────────
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Responses'

    # Colour palette
    ORANGE      = 'FFFF8C00'
    ORANGE_LIGHT= 'FFFFF5E8'
    DARK        = 'FF1A1A2E'
    GREY_HDR    = 'FFF0EEE8'
    WHITE       = 'FFFFFFFF'
    BORDER_CLR  = 'FFE8E4DE'

    thin = Border(
        left=Side(style='thin', color=BORDER_CLR),
        right=Side(style='thin', color=BORDER_CLR),
        top=Side(style='thin', color=BORDER_CLR),
        bottom=Side(style='thin', color=BORDER_CLR),
    )

    # ── Title row ────────────────────────────────────────────────────────────
    title_text = form.get('title', 'Untitled Form')
    total_cols  = len(columns) + 2   # #, timestamp, + questions
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(total_cols, 3))
    tc = ws.cell(row=1, column=1, value=f'◈ {title_text} — Responses')
    tc.font      = Font(name='Segoe UI', bold=True, size=14, color=WHITE)
    tc.fill      = PatternFill('solid', fgColor=DARK)
    tc.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[1].height = 32

    # ── Subtitle row ─────────────────────────────────────────────────────────
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=max(total_cols, 3))
    sc = ws.cell(row=2, column=1,
                 value=f'Exported {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}  ·  '
                       f'{len(responses)} response{"s" if len(responses)!=1 else ""}  ·  FORM.AI')
    sc.font      = Font(name='Segoe UI', size=9, color='FF888888')
    sc.fill      = PatternFill('solid', fgColor=GREY_HDR)
    sc.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[2].height = 18

    # ── Header row ───────────────────────────────────────────────────────────
    headers = ['#', 'Submitted At'] + [lbl for _, lbl in columns]
    for ci, hdr in enumerate(headers, start=1):
        c = ws.cell(row=3, column=ci, value=hdr)
        c.font      = Font(name='Segoe UI', bold=True, size=10,
                           color=WHITE if ci <= 2 else DARK)
        c.fill      = PatternFill('solid', fgColor=ORANGE if ci <= 2 else ORANGE_LIGHT)
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border    = thin
    ws.row_dimensions[3].height = 22

    # ── Data rows ────────────────────────────────────────────────────────────
    for ri, resp in enumerate(responses, start=1):
        ans = resp.get('answers') or resp.get('data') or {}
        ts  = resp.get('submitted_at') or resp.get('created_at', '')
        if isinstance(ts, datetime): ts = ts.strftime('%Y-%m-%d %H:%M')
        elif isinstance(ts, str) and 'T' in ts: ts = ts.replace('T',' ')[:16]

        row_num = ri + 3
        bg = WHITE if ri % 2 == 0 else 'FFFFF9F3'   # alternating row colour

        # # column
        c0 = ws.cell(row=row_num, column=1, value=ri)
        c0.font      = Font(name='Segoe UI', size=9, bold=True, color='FF888888')
        c0.fill      = PatternFill('solid', fgColor=ORANGE_LIGHT)
        c0.alignment = Alignment(horizontal='center', vertical='center')
        c0.border    = thin

        # Timestamp column
        c1 = ws.cell(row=row_num, column=2, value=str(ts))
        c1.font      = Font(name='Segoe UI', size=9, color='FF555555')
        c1.fill      = PatternFill('solid', fgColor=ORANGE_LIGHT)
        c1.alignment = Alignment(horizontal='center', vertical='center')
        c1.border    = thin

        # Answer columns
        for ci, (key, _) in enumerate(columns, start=3):
            val = ans.get(key, '')
            if isinstance(val, list): val = ', '.join(str(v) for v in val)
            elif isinstance(val, dict): val = json.dumps(val)
            cell = ws.cell(row=row_num, column=ci, value=str(val) if val is not None else '')
            cell.font      = Font(name='Segoe UI', size=9)
            cell.fill      = PatternFill('solid', fgColor=bg)
            cell.alignment = Alignment(vertical='center', wrap_text=True)
            cell.border    = thin

        ws.row_dimensions[row_num].height = 18

    # ── Column widths ────────────────────────────────────────────────────────
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 18
    for ci in range(3, len(columns) + 3):
        col_letter = get_column_letter(ci)
        max_len    = max(
            (len(str(responses[ri].get('answers',{}).get(columns[ci-3][0],'') or ''))
             for ri in range(len(responses))),
            default=0
        )
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, len(columns[ci-3][1]) + 2, 12), 40)

    # Freeze top 3 rows + first 2 columns
    ws.freeze_panes = 'C4'

    # ── Summary sheet ────────────────────────────────────────────────────────
    ws2 = wb.create_sheet('Summary')
    ws2.cell(row=1, column=1, value='Metric').font     = Font(bold=True, name='Segoe UI')
    ws2.cell(row=1, column=2, value='Value').font      = Font(bold=True, name='Segoe UI')
    ws2.cell(row=2, column=1, value='Form Title')
    ws2.cell(row=2, column=2, value=title_text)
    ws2.cell(row=3, column=1, value='Total Responses')
    ws2.cell(row=3, column=2, value=len(responses))
    ws2.cell(row=4, column=1, value='Total Questions')
    ws2.cell(row=4, column=2, value=len(columns))
    ws2.cell(row=5, column=1, value='Export Date')
    ws2.cell(row=5, column=2, value=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'))
    ws2.column_dimensions['A'].width = 20
    ws2.column_dimensions['B'].width = 40
    for i,c in [(2,'A'),(2,'B'),(3,'A'),(3,'B'),(4,'A'),(4,'B'),(5,'A'),(5,'B')]:
        ws2.cell(row=i, column=ord(c)-64).fill   = PatternFill('solid', fgColor='FFFFF9F3')
        ws2.cell(row=i, column=ord(c)-64).border = thin

    # Save to buffer
    buf = io.BytesIO()
    wb.save(buf); buf.seek(0)

    safe_title = re.sub(r'[^a-z0-9_]', '_', title_text.lower())[:30]
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name=f'{safe_title}_responses_{datetime.utcnow().strftime("%Y%m%d")}.xlsx')


@deploy_bp.route('/deploy/data/<form_id>/export-csv')
@login_required
def export_csv(form_id):
    """Export form responses as CSV."""
    import csv as csv_mod
    from bson import ObjectId
    try:
        form = _db().forms.find_one({'_id': ObjectId(form_id), 'user_id': current_user.id})
    except Exception:
        abort(404)
    if not form: abort(404)

    responses = list(_db().responses.find({'form_id': form_id}).sort('submitted_at', -1))

    columns = []
    seen = set()
    for page in form.get('pages', []):
        for q in page.get('questions', []):
            key   = q.get('id') or q.get('label') or q.get('question', '')
            label = q.get('label') or q.get('question') or key
            if key and key not in seen:
                seen.add(key); columns.append((key, label))
    if not columns:
        all_keys = set()
        for r in responses:
            ans = r.get('answers') or r.get('data') or {}
            if isinstance(ans, dict): all_keys.update(ans.keys())
        for k in sorted(all_keys): columns.append((k, k))

    buf = io.StringIO()
    writer = csv_mod.writer(buf)
    writer.writerow(['#', 'Submitted At'] + [lbl for _, lbl in columns])
    for i, r in enumerate(responses, 1):
        ans = r.get('answers') or r.get('data') or {}
        ts  = r.get('submitted_at') or r.get('created_at', '')
        if isinstance(ts, datetime): ts = ts.strftime('%Y-%m-%d %H:%M')
        elif isinstance(ts, str) and 'T' in ts: ts = ts.replace('T', ' ')[:16]
        row = [i, ts]
        for key, _ in columns:
            val = ans.get(key, '')
            if isinstance(val, list): val = ', '.join(str(v) for v in val)
            elif isinstance(val, dict): val = json.dumps(val)
            row.append(val)
        writer.writerow(row)

    buf.seek(0)
    safe_title = re.sub(r'[^a-z0-9_]', '_', form.get('title','form').lower())[:30]
    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{safe_title}_{datetime.utcnow().strftime("%Y%m%d")}.csv"'}
    )


@deploy_bp.route('/deploy/data/<form_id>/delete-response', methods=['POST'])
@login_required
def delete_response(form_id):
    """Delete a single response."""
    from bson import ObjectId
    try:
        form = _db().forms.find_one({'_id': ObjectId(form_id), 'user_id': current_user.id})
    except Exception:
        return jsonify({'success': False, 'error': 'Not found'})
    if not form: return jsonify({'success': False, 'error': 'Not found'})

    data = request.get_json(silent=True) or {}
    rid  = data.get('response_id', '')
    try:
        _db().responses.delete_one({'_id': ObjectId(rid)})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})