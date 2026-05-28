from bson import ObjectId
from datetime import datetime
import secrets

class Project:
    @staticmethod
    def _db():
        from app import db; return db

    @staticmethod
    def create(user_id, title, tagline='', description=''):
        doc = {
            'user_id': str(user_id),
            'title': title,
            'tagline': tagline,
            'description': description,
            'screenshots': [],       # list of URLs
            'demo_url': '',
            'github_url': '',
            'website_url': '',
            'tags': [],
            'category': 'general',   # general, startup, saas, tool, design, open-source
            'status': 'draft',       # draft | live
            'upvotes_count': 0,
            'comments_count': 0,
            'views_count': 0,
            'bookmarks_count': 0,
            'is_featured': False,
            'trending_score': 0.0,
            'slug': secrets.token_urlsafe(8),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'launched_at': None,
        }
        r = Project._db().projects.insert_one(doc)
        doc['_id'] = r.inserted_id
        # Award creator XP
        try:
            from models.user import User
            creator = User.get_by_id(str(user_id))
            if creator:
                creator.add_xp(25)
        except:
            pass
        return doc

    @staticmethod
    def get_by_id(pid):
        try:
            p = Project._db().projects.find_one({'_id': ObjectId(pid)})
            if p:
                p['_id'] = str(p['_id'])
            return p
        except:
            return None

    @staticmethod
    def update(pid, data):
        data['updated_at'] = datetime.utcnow()
        Project._db().projects.update_one(
            {'_id': ObjectId(pid)},
            {'$set': data}
        )

    @staticmethod
    def delete(pid):
        Project._db().projects.delete_one({'_id': ObjectId(pid)})
        Project._db().project_upvotes.delete_many({'project_id': str(pid)})

    @staticmethod
    def upvote(pid, user_id):
        """Toggle upvote. Returns True if now upvoted, False if removed."""
        pid, user_id = str(pid), str(user_id)
        db = Project._db()
        existing = db.project_upvotes.find_one({'project_id': pid, 'user_id': user_id})
        if existing:
            db.project_upvotes.delete_one({'project_id': pid, 'user_id': user_id})
            db.projects.update_one({'_id': ObjectId(pid)}, {'$inc': {'upvotes_count': -1}})
            return False
        else:
            db.project_upvotes.insert_one({
                'project_id': pid, 'user_id': user_id,
                'created_at': datetime.utcnow()
            })
            db.projects.update_one({'_id': ObjectId(pid)}, {'$inc': {'upvotes_count': 1}})
            # Award creator XP
            p = Project.get_by_id(pid)
            if p and p['user_id'] != user_id:
                try:
                    from models.user import User
                    creator = User.get_by_id(p['user_id'])
                    if creator:
                        creator.add_xp(5)
                        creator.create_notification(
                            sender_id=user_id,
                            notif_type='upvote',
                            text=f"upvoted your project '{p['title']}'"
                        )
                except:
                    pass
            return True

    @staticmethod
    def is_upvoted(pid, user_id):
        return Project._db().project_upvotes.find_one({
            'project_id': str(pid), 'user_id': str(user_id)
        }) is not None

    @staticmethod
    def increment_views(pid):
        Project._db().projects.update_one(
            {'_id': ObjectId(pid)}, {'$inc': {'views_count': 1}}
        )

    @staticmethod
    def get_by_user(user_id):
        projects = list(Project._db().projects.find(
            {'user_id': str(user_id)}
        ).sort('created_at', -1))
        for p in projects:
            p['_id'] = str(p['_id'])
        return projects

    @staticmethod
    def get_live(limit=30, skip=0, category='', sort='trending'):
        db = Project._db()
        query = {'status': 'live'}
        if category:
            query['category'] = category.lower()

        if sort == 'newest':
            projects = list(db.projects.find(query).sort('created_at', -1).skip(skip).limit(limit))
        elif sort == 'top':
            projects = list(db.projects.find(query).sort('upvotes_count', -1).skip(skip).limit(limit))
        else:  # trending — weighted score
            pipeline = [
                {'$match': query},
                {'$addFields': {
                    'score': {
                        '$add': [
                            {'$multiply': ['$upvotes_count', 3]},
                            {'$multiply': ['$comments_count', 2]},
                            '$views_count'
                        ]
                    }
                }},
                {'$sort': {'score': -1, 'created_at': -1}},
                {'$skip': skip},
                {'$limit': limit}
            ]
            projects = list(db.projects.aggregate(pipeline))

        for p in projects:
            p['_id'] = str(p['_id'])
        return projects

    @staticmethod
    def ensure_indexes():
        db = Project._db()
        db.projects.create_index([('status', 1), ('created_at', -1)])
        db.projects.create_index([('status', 1), ('upvotes_count', -1)])
        db.projects.create_index([('user_id', 1)])
        db.project_upvotes.create_index([('project_id', 1), ('user_id', 1)], unique=True)
