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
            'user_id': str(user_id), 
            'title': title, 
            'description': '',
            'slug': secrets.token_urlsafe(8),
            'pages': [{'id':'page_1','title':'Page 1','fields':[]}],
            'settings': {
                'is_published': False, 
                'show_progress': True,
                'confirmation_message': 'Thank you for your response!',
                'redirect_url': '', 
                'notify_email': '',
                'notify_on_submit': False,
                'presentation_style': 'form' # default
            },
            'theme': {
                'bg_color':'#F8F9FA',
                'header_color':'#1A1A2E',
                'accent_color':'#FF8C00',
                'text_color':'#212529',
                'card_color':'#FFFFFF',
                'font':'DM Sans',
                'cover_image':'',
                'button_text':'Submit',
                'header_style':'gradient',
            },
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'response_count': 0,
            
            # Social discovery fields
            'likes_count': 0,
            'comments_count': 0,
            'is_template': False,
            'template_category': '',
            'tags': [],
            'estimated_completion_time': 2, # default in minutes
            'is_featured': False,
            'is_poll': False
        }
        r = Form._db().forms.insert_one(doc)
        doc['_id'] = r.inserted_id
        
        # Award creator XP for creating a form
        try:
            from models.user import User
            creator = User.get_by_id(user_id)
            if creator:
                creator.add_xp(20) # +20 XP for creating a form
        except:
            pass
            
        return doc

    @staticmethod
    def get_by_id(fid):
        try:
            f = Form._db().forms.find_one({'_id': ObjectId(fid)})
            if f:
                # Ensure defaults for backward compatibility
                f.setdefault('likes_count', 0)
                f.setdefault('comments_count', 0)
                f.setdefault('is_template', False)
                f.setdefault('tags', [])
                f.setdefault('estimated_completion_time', 2)
                f.setdefault('is_featured', False)
                f.setdefault('is_poll', False)
            return f
        except: return None

    @staticmethod
    def get_by_slug(slug):
        f = Form._db().forms.find_one({'slug': slug})
        if f:
            f.setdefault('likes_count', 0)
            f.setdefault('comments_count', 0)
            f.setdefault('is_template', False)
            f.setdefault('tags', [])
            f.setdefault('estimated_completion_time', 2)
            f.setdefault('is_featured', False)
            f.setdefault('is_poll', False)
        return f

    @staticmethod
    def get_by_user(uid):
        forms = list(Form._db().forms.find({'user_id': str(uid)}).sort('created_at', -1))
        for f in forms:
            f.setdefault('likes_count', 0)
            f.setdefault('comments_count', 0)
            f.setdefault('is_template', False)
            f.setdefault('tags', [])
            f.setdefault('estimated_completion_time', 2)
            f.setdefault('is_featured', False)
            f.setdefault('is_poll', False)
        return forms

    @staticmethod
    def update(fid, data):
        data['updated_at'] = datetime.utcnow()
        Form._db().forms.update_one({'_id': ObjectId(fid)}, {'$set': data})

    @staticmethod
    def delete(fid):
        Form._db().forms.delete_one({'_id': ObjectId(fid)})
        Form._db().responses.delete_many({'form_id': str(fid)})
        Form._db().comments.delete_many({'form_id': str(fid)})
        Form._db().likes.delete_many({'form_id': str(fid)})

    @staticmethod
    def increment_responses(fid):
        Form._db().forms.update_one({'_id': ObjectId(fid)}, {'$inc':{'response_count':1}})
        
        # Award creator XP for receiving a submission
        try:
            f = Form.get_by_id(fid)
            if f:
                from models.user import User
                creator = User.get_by_id(f['user_id'])
                if creator:
                    creator.add_xp(5) # +5 XP for each submission
                    
                    # Challenge checks: check if reached 10 submissions
                    total_res = Form._db().responses.count_documents({'form_id': str(fid)})
                    if total_res >= 10:
                        creator.award_badge('responses_10')
        except:
            pass

    @staticmethod
    def like(form_id, user_id):
        user_id = str(user_id)
        form_id = str(form_id)
        db = Form._db()
        
        liked = db.likes.find_one({'user_id': user_id, 'form_id': form_id})
        if liked:
            # Unlike
            db.likes.delete_one({'user_id': user_id, 'form_id': form_id})
            db.forms.update_one({'_id': ObjectId(form_id)}, {'$inc': {'likes_count': -1}})
            return False
        else:
            # Like
            db.likes.insert_one({
                'user_id': user_id,
                'form_id': form_id,
                'created_at': datetime.utcnow()
            })
            db.forms.update_one({'_id': ObjectId(form_id)}, {'$inc': {'likes_count': 1}})
            
            # Notify creator
            f = Form.get_by_id(form_id)
            if f and f['user_id'] != user_id:
                from models.user import User
                creator = User.get_by_id(f['user_id'])
                if creator:
                    creator.add_xp(10) # Liked grants XP
                    creator.create_notification(
                        sender_id=user_id,
                        notif_type="like",
                        text=f"❤️ liked your form '{f['title']}'",
                        form_id=form_id
                    )
                    try:
                        from routes.realtime import notify_user_socket
                        notify_user_socket(f['user_id'], {
                            'type': 'like',
                            'title': 'New Like!',
                            'text': f"❤️ Someone liked your form '{f['title']}'!"
                        })
                    except:
                        pass
            return True

    @staticmethod
    def is_liked(form_id, user_id):
        return Form._db().likes.find_one({
            'user_id': str(user_id),
            'form_id': str(form_id)
        }) is not None
