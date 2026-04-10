from flask import Flask, jsonify
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
import os

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

MONGO_URI  = os.getenv('MONGO_URI',  'mongodb+srv://santoshks_db_user:viefoCaPp3CMCqTq@cluster0.v8wfkok.mongodb.net/formcraft?retryWrites=true&w=majority&appName=Cluster0')
SECRET_KEY = os.getenv('SECRET_KEY', 'formcraft-secret-jain-2024-xK9mP2qR')
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

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db     = client.get_database('formcraft')

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
        return jsonify({'success': False, 'error': 'Server error. Check server logs.'}), 500

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

    @login_manager.user_loader
    def load_user(user_id):
        from bson import ObjectId
        from models.user import User
        try:
            data = db.users.find_one({'_id': ObjectId(user_id)})
            return User(data) if data else None
        except Exception:
            return None

    return app


if __name__ == '__main__':
    try:
        client.admin.command('ping')
        print('✅ MongoDB connected!')
    except Exception as e:
        print(f'❌ MongoDB error: {e}')

    print(f'📧 SMTP: {os.getenv("SMTP_USER")} via {os.getenv("SMTP_HOST")}:{os.getenv("SMTP_PORT")}')
    print(f'📧 Pass: {"✅ set" if os.getenv("SMTP_PASS") else "❌ NOT SET"}')

    app = create_app()
    app.run(debug=False, host='0.0.0.0', port=5000)