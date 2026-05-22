from flask_login import UserMixin
from bson import ObjectId
from datetime import datetime

class User(UserMixin):
    def __init__(self, data):
        self.id           = str(data['_id'])
        self.name         = data.get('name','')
        self.email        = data.get('email','')
        self.avatar       = data.get('avatar','')
        self.auth_provider= data.get('auth_provider','email')
        self.password_hash= data.get('password_hash','')
        self.created_at   = data.get('created_at')
        self.plan         = data.get('plan', 'free')

    def get_quotas(self):
        limits = {
            'free': {'forms': 3, 'newsletters': 10, 'deploys': 10},
            'basic': {'forms': 30, 'newsletters': 30, 'deploys': 15},
            'pro': {'forms': float('inf'), 'newsletters': float('inf'), 'deploys': float('inf')}
        }
        return limits.get(self.plan, limits['free'])

    def can_create_form(self):
        if self.plan == 'pro': return True
        count = self._db().forms.count_documents({'user_id': self.id})
        return count < self.get_quotas()['forms']

    def can_create_newsletter(self):
        if self.plan == 'pro': return True
        count = self._db().newsletters.count_documents({'user_id': self.id})
        return count < self.get_quotas()['newsletters']

    def can_deploy(self):
        if self.plan == 'pro': return True
        count = self._db().published_sites.count_documents({'user_id': self.id})
        return count < self.get_quotas()['deploys']

    def get_id(self): return self.id

    def check_password(self, pw):
        from app import bcrypt
        return bcrypt.check_password_hash(self.password_hash, pw)

    @staticmethod
    def _db():
        from app import db; return db

    @staticmethod
    def get_by_id(uid):
        try:
            d = User._db().users.find_one({'_id': ObjectId(uid)})
            return User(d) if d else None
        except: return None

    @staticmethod
    def get_by_email(email):
        d = User._db().users.find_one({'email': email})
        return User(d) if d else None

    @staticmethod
    def create(name, email, password=None, auth_provider='email', avatar=''):
        from app import bcrypt
        doc = {'name':name,'email':email,'avatar':avatar,
                'auth_provider':auth_provider,'created_at':datetime.utcnow(), 'plan': 'free'}
        if password:
            doc['password_hash'] = bcrypt.generate_password_hash(password).decode('utf-8')
        r = User._db().users.insert_one(doc)
        doc['_id'] = r.inserted_id
        return User(doc)
