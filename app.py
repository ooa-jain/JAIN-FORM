from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
import os

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

MONGO_URI = os.getenv('MONGO_URI','mongodb+srv://santoshks_db_user:viefoCaPp3CMCqTq@cluster0.v8wfkok.mongodb.net/formcraft?retryWrites=true&w=majority&appName=Cluster0')
SECRET_KEY = os.getenv('SECRET_KEY','formcraft-secret-2024-jain')
MAIL_FROM  = os.getenv('MAIL_FROM','officeofacademicaffairs@jainuniversity.ac.in')

client = MongoClient(MONGO_URI)
db     = client.get_database('formcraft')

login_manager = LoginManager()
bcrypt        = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY

    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view    = 'auth.login'
    login_manager.login_message = 'Please log in.'

    from routes.auth       import auth_bp
    from routes.nomination import nomination_bp
    from routes.ai_builder    import ai_bp
    from routes.ai_newsletter import ai_nl_bp
    from routes.dashboard  import dashboard_bp
    from routes.builder    import builder_bp
    from routes.public     import public_bp
    from routes.responses  import responses_bp
    from routes.newsletter import newsletter_bp
    from routes.admin      import admin_bp

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
    app = create_app()
    app.run(debug=True)