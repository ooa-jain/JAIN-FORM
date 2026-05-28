from bson import ObjectId
from datetime import datetime

class Comment:
    @staticmethod
    def _db():
        from app import db; return db

    @staticmethod
    def create(form_id, user_id, username, user_avatar, text, parent_id=None):
        doc = {
            'form_id': str(form_id),
            'user_id': str(user_id),
            'username': username,
            'user_avatar': user_avatar or 'duck_default',
            'text': text,
            'parent_id': str(parent_id) if parent_id else None,
            'likes': [],
            'created_at': datetime.utcnow()
        }
        r = Comment._db().comments.insert_one(doc)
        doc['_id'] = str(r.inserted_id)
        
        # Denormalize comment counts on the form
        Comment._db().forms.update_one(
            {'_id': ObjectId(form_id)},
            {'$inc': {'comments_count': 1}}
        )
        return doc

    @staticmethod
    def get_by_form(form_id):
        # Fetch all flat comments, then format them into threads on client side or python side
        comments = list(Comment._db().comments.find({'form_id': str(form_id)}).sort('created_at', 1))
        for c in comments:
            c['_id'] = str(c['_id'])
            c['likes_count'] = len(c.get('likes', []))
        return comments

    @staticmethod
    def like(comment_id, user_id):
        user_id = str(user_id)
        comment = Comment._db().comments.find_one({'_id': ObjectId(comment_id)})
        if not comment:
            return False
            
        likes = comment.get('likes', [])
        if user_id in likes:
            # Unlike
            Comment._db().comments.update_one(
                {'_id': ObjectId(comment_id)},
                {'$pull': {'likes': user_id}}
            )
            return False
        else:
            # Like
            Comment._db().comments.update_one(
                {'_id': ObjectId(comment_id)},
                {'$push': {'likes': user_id}}
            )
            return True


class Follower:
    @staticmethod
    def _db():
        from app import db; return db

    @staticmethod
    def follow(follower_id, following_id):
        follower_id = str(follower_id)
        following_id = str(following_id)
        if follower_id == following_id:
            return False
            
        existing = Follower._db().followers.find_one({
            'follower_id': follower_id,
            'following_id': following_id
        })
        if existing:
            return False
            
        Follower._db().followers.insert_one({
            'follower_id': follower_id,
            'following_id': following_id,
            'created_at': datetime.utcnow()
        })
        
        # Increment following tallies
        Follower._db().users.update_one({'_id': ObjectId(follower_id)}, {'$inc': {'following_count': 1}})
        Follower._db().users.update_one({'_id': ObjectId(following_id)}, {'$inc': {'followers_count': 1}})
        
        # Notify user in database
        from models.user import User
        follower_user = User.get_by_id(follower_id)
        following_user = User.get_by_id(following_id)
        
        if follower_user and following_user:
            following_user.create_notification(
                sender_id=follower_id,
                notif_type="follow",
                text=f"👥 {follower_user.name} started following you!"
            )
            
            # Badge checks for following user
            f_count = Follower._db().followers.count_documents({'following_id': following_id})
            if f_count >= 10:
                following_user.award_badge('social_star')
                
            try:
                from routes.realtime import notify_user_socket
                notify_user_socket(following_id, {
                    'type': 'follow',
                    'title': 'New Follower!',
                    'text': f'👥 {follower_user.name} is now following you!'
                })
            except Exception:
                pass
        return True

    @staticmethod
    def unfollow(follower_id, following_id):
        follower_id = str(follower_id)
        following_id = str(following_id)
        
        existing = Follower._db().followers.find_one({
            'follower_id': follower_id,
            'following_id': following_id
        })
        if not existing:
            return False
            
        Follower._db().followers.delete_one({
            'follower_id': follower_id,
            'following_id': following_id
        })
        
        # Decrement counts
        Follower._db().users.update_one({'_id': ObjectId(follower_id)}, {'$inc': {'following_count': -1}})
        Follower._db().users.update_one({'_id': ObjectId(following_id)}, {'$inc': {'followers_count': -1}})
        return True

    @staticmethod
    def is_following(follower_id, following_id):
        return Follower._db().followers.find_one({
            'follower_id': str(follower_id),
            'following_id': str(following_id)
        }) is not None


class Notification:
    @staticmethod
    def _db():
        from app import db; return db

    @staticmethod
    def get_unread_by_user(user_id):
        notifs = list(Notification._db().notifications.find({
            'user_id': str(user_id),
            'is_read': False
        }).sort('created_at', -1))
        for n in notifs:
            n['_id'] = str(n['_id'])
        return notifs

    @staticmethod
    def mark_as_read(notif_id):
        Notification._db().notifications.update_one(
            {'_id': ObjectId(notif_id)},
            {'$set': {'is_read': True}}
        )

    @staticmethod
    def mark_all_read(user_id):
        Notification._db().notifications.update_one(
            {'user_id': str(user_id)},
            {'$set': {'is_read': True}}
        )
