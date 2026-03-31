from bson import ObjectId
from datetime import datetime
import secrets

class Form:
    @staticmethod
    def _db():
        from app import db; return db

    @staticmethod
    def create(user_id, title):
        doc = {
            'user_id': user_id, 'title': title, 'description': '',
            'slug': secrets.token_urlsafe(8),
            'pages': [{'id':'page_1','title':'Page 1','fields':[]}],
            'settings': {
                'is_published': False, 'show_progress': True,
                'confirmation_message': 'Thank you for your response!',
                'redirect_url': '', 'notify_email': '',
                'notify_on_submit': False,
            },
            'theme': {
                'bg_color':'#F8F9FA','header_color':'#1A1A2E',
                'accent_color':'#FF8C00','text_color':'#212529',
                'card_color':'#FFFFFF','font':'DM Sans',
                'cover_image':'','button_text':'Submit',
                'header_style':'gradient',
            },
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'response_count': 0
        }
        r = Form._db().forms.insert_one(doc)
        doc['_id'] = r.inserted_id
        return doc

    @staticmethod
    def get_by_id(fid):
        try: return Form._db().forms.find_one({'_id': ObjectId(fid)})
        except: return None

    @staticmethod
    def get_by_slug(slug):
        return Form._db().forms.find_one({'slug': slug})

    @staticmethod
    def get_by_user(uid):
        return list(Form._db().forms.find({'user_id': uid}).sort('created_at',-1))

    @staticmethod
    def update(fid, data):
        data['updated_at'] = datetime.utcnow()
        Form._db().forms.update_one({'_id': ObjectId(fid)}, {'$set': data})

    @staticmethod
    def delete(fid):
        Form._db().forms.delete_one({'_id': ObjectId(fid)})
        Form._db().responses.delete_many({'form_id': str(fid)})

    @staticmethod
    def increment_responses(fid):
        Form._db().forms.update_one({'_id': ObjectId(fid)}, {'$inc':{'response_count':1}})
