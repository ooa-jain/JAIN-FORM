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
                'auth_provider':auth_provider,'created_at':datetime.utcnow()}
        if password:
            doc['password_hash'] = bcrypt.generate_password_hash(password).decode('utf-8')
        r = User._db().users.insert_one(doc)
        doc['_id'] = r.inserted_id
        return User(doc)
