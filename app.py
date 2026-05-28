from flask import Flask, jsonify, request
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
import os

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

MONGO_URI  = os.getenv('MONGO_URI',  'mongodb+srv://santoshks_db_user:viefoCaPp3CMCqTq@cluster0.v8wfkok.mongodb.net/Draftspace?retryWrites=true&w=majority&appName=Cluster0')
SECRET_KEY = os.getenv('SECRET_KEY', 'Draftspace-secret-jain-2024-xK9mP2qR')
MAIL_FROM  = os.getenv('MAIL_FROM',  'officeofacademicaffairs@jainuniversity.ac.in')

# ── SMTP — bridge both naming conventions ─────────────────────────────────────
_smtp_user = os.getenv('SMTP_USER') or os.getenv('EMAIL_USER', '')
_smtp_pass = os.getenv('SMTP_PASS') or os.getenv('EMAIL_PASS', '')
_smtp_host = os.getenv('SMTP_HOST') or os.getenv('MAIL_SERVER', 'smtp.gmail.com')
_smtp_port = os.getenv('SMTP_PORT') or os.getenv('MAIL_PORT', '587')
os.environ['SMTP_USER'] = _smtp_user
os.environ['SMTP_PASS'] = _smtp_pass
os.environ['SMTP_HOST'] = _smtp_host
os.environ['SMTP_PORT'] = str(_smtp_port)

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
db     = client.get_database('Draftspace')

login_manager = LoginManager()
bcrypt        = Bcrypt()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY']         = SECRET_KEY

    # ── CRITICAL for Hostinger: allow large JSON payloads (base64 images) ──
    # Nginx on Hostinger defaults to 1MB — we set Flask limit higher.
    # You ALSO need client_max_body_size 50m; in Nginx config (see README).
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

    # ── Session cookie settings for hosted HTTPS ──
    app.config['SESSION_COOKIE_SECURE']   = os.getenv('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    from routes.realtime import socketio
    socketio.init_app(app)
    
    login_manager.login_view    = 'auth.login'
    login_manager.login_message = 'Please log in.'

    # ── Handle 413 Request Entity Too Large gracefully ──
    @app.errorhandler(413)
    def too_large(e):
        return jsonify({
            'success': False,
            'error': 'Payload too large. Images may be too big — use external image URLs instead of uploaded files.'
        }), 413

    # ── Handle generic server errors ──
    @app.errorhandler(500)
    def server_error(e):
        import traceback
        traceback.print_exc()
        try:
            # Return JSON for API/AJAX, HTML for page requests
            wants_json = (
                request.path.startswith('/deploy/upload') or
                request.path.startswith('/deploy/analyze') or
                request.path.startswith('/deploy/publish') or
                request.path.startswith('/deploy/delete') or
                request.path.startswith('/deploy/site/') or
                request.path.startswith('/newsletter/save') or
                request.path.startswith('/newsletter/send') or
                request.path.startswith('/newsletter/upload') or
                request.path.startswith('/newsletter/preview-live') or
                'application/json' in request.headers.get('Accept', '') or
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            )
        except Exception:
            wants_json = True   # if request context is broken, return JSON

        if wants_json:
            return jsonify({'success': False, 'error': 'Server error. Check server logs.'}), 500

        err_str = str(e)
        return f'''<html><body style="font-family:monospace;padding:40px;background:#1A1A2E;color:#E63946">
            <h2 style="margin-bottom:12px">⚠ 500 Server Error</h2>
            <pre style="color:#aaa;font-size:.85rem;white-space:pre-wrap">{err_str}</pre>
            <p style="margin-top:20px"><a href="/dashboard" style="color:#FF8C00">← Dashboard</a>
            &nbsp;&nbsp;<a href="/newsletter/" style="color:#FF8C00">Newsletters</a>
            &nbsp;&nbsp;<a href="/deploy" style="color:#FF8C00">Deploy</a></p>
        </body></html>''', 500

    from routes.auth          import auth_bp
    from routes.nomination    import nomination_bp
    from routes.ai_builder    import ai_bp
    from routes.ai_newsletter import ai_nl_bp
    from routes.dashboard     import dashboard_bp
    from routes.builder       import builder_bp
    from routes.public        import public_bp
    from routes.responses     import responses_bp
    from routes.newsletter    import newsletter_bp
    from routes.admin         import admin_bp
    from routes.deploy        import deploy_bp
    from routes.pricing       import pricing_bp
    from routes.community     import community_bp
    from routes.research      import research_bp
    from routes.marketplace   import marketplace_bp
    from routes.projects      import projects_bp
    from routes.discover      import discover_bp
    from routes.challenges    import challenges_bp
    from routes.analytics     import analytics_bp
    from routes.publish       import publish_bp

    # ── Ensure static/sites folder exists ────────────────────────────────────
    sites_dir = os.path.join(basedir, 'static', 'sites')
    os.makedirs(sites_dir, exist_ok=True)

    # ── Register deploy_bp FIRST so /sites/<slug>/ routes take priority ──────
    app.register_blueprint(deploy_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(builder_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(responses_bp)
    app.register_blueprint(nomination_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(ai_nl_bp)
    app.register_blueprint(newsletter_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(pricing_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(research_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(discover_bp)
    app.register_blueprint(challenges_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(publish_bp)

    @login_manager.user_loader
    def load_user(user_id):
        from bson import ObjectId
        from models.user import User
        try:
            data = db.users.find_one({'_id': ObjectId(user_id)})
            return User(data) if data else None
        except Exception:
            return None

    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    return app


if __name__ == '__main__':
    try:
        client.admin.command('ping')
        print('[OK] MongoDB connected!')
    except Exception as e:
        print(f'[ERR] MongoDB error: {e}')

    print(f'[SMTP] User: {os.getenv("SMTP_USER")} via {os.getenv("SMTP_HOST")}:{os.getenv("SMTP_PORT")}')
    print(f'[SMTP] Pass: {"set" if os.getenv("SMTP_PASS") else "NOT SET"}')

    app = create_app()
    from routes.realtime import socketio
    socketio.run(app, debug=True, use_reloader=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
