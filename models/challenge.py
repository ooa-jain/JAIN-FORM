from bson import ObjectId
from datetime import datetime, timedelta

CHALLENGE_TYPES = ['post_form', 'get_likes', 'follow_creator', 'add_comment', 'launch_project', 'daily_login']

# Static daily challenges seeded into the DB on first run
SEED_CHALLENGES = [
    {
        'title': 'Share Your Knowledge',
        'description': 'Publish a new public form today',
        'icon': 'ph-note-pencil',
        'type': 'post_form',
        'xp_reward': 100,
        'coins_reward': 20,
        'target_count': 1,
        'difficulty': 'easy',
    },
    {
        'title': 'Community Builder',
        'description': 'Like 5 forms from other creators',
        'icon': 'ph-heart',
        'type': 'get_likes',
        'xp_reward': 75,
        'coins_reward': 15,
        'target_count': 5,
        'difficulty': 'easy',
    },
    {
        'title': 'Social Connector',
        'description': 'Follow 3 new creators',
        'icon': 'ph-user-plus',
        'type': 'follow_creator',
        'xp_reward': 60,
        'coins_reward': 10,
        'target_count': 3,
        'difficulty': 'easy',
    },
    {
        'title': 'Conversation Starter',
        'description': 'Leave 3 thoughtful comments',
        'icon': 'ph-chat-circle',
        'type': 'add_comment',
        'xp_reward': 80,
        'coins_reward': 15,
        'target_count': 3,
        'difficulty': 'medium',
    },
    {
        'title': 'Product Launcher',
        'description': 'Launch a project in the showcase',
        'icon': 'ph-rocket-launch',
        'type': 'launch_project',
        'xp_reward': 200,
        'coins_reward': 50,
        'target_count': 1,
        'difficulty': 'hard',
    },
    {
        'title': 'Daily Check-in',
        'description': 'Visit the platform and stay active',
        'icon': 'ph-calendar-check',
        'type': 'daily_login',
        'xp_reward': 30,
        'coins_reward': 5,
        'target_count': 1,
        'difficulty': 'easy',
    },
]

class Challenge:
    @staticmethod
    def _db():
        from app import db; return db

    @staticmethod
    def seed_if_empty():
        db = Challenge._db()
        if db.challenges.count_documents({}) == 0:
            for c in SEED_CHALLENGES:
                c['created_at'] = datetime.utcnow()
                c['active'] = True
            db.challenges.insert_many(SEED_CHALLENGES)

    @staticmethod
    def get_active():
        challenges = list(Challenge._db().challenges.find({'active': True}))
        for c in challenges:
            c['_id'] = str(c['_id'])
        return challenges

    @staticmethod
    def get_user_progress(user_id):
        """Returns dict of {challenge_id: {progress, claimed}}"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        records = list(Challenge._db().user_challenges.find({
            'user_id': str(user_id),
            'date': {'$gte': today_start}
        }))
        return {str(r['challenge_id']): r for r in records}

    @staticmethod
    def increment_progress(user_id, challenge_type, amount=1):
        """Called from routes when user performs an action matching a challenge type."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        db = Challenge._db()
        challenges = list(db.challenges.find({'type': challenge_type, 'active': True}))
        for c in challenges:
            cid = str(c['_id'])
            existing = db.user_challenges.find_one({
                'user_id': str(user_id),
                'challenge_id': cid,
                'date': {'$gte': today_start}
            })
            if existing:
                if not existing.get('claimed') and existing.get('progress', 0) < c['target_count']:
                    db.user_challenges.update_one(
                        {'_id': existing['_id']},
                        {'$inc': {'progress': amount}}
                    )
            else:
                db.user_challenges.insert_one({
                    'user_id': str(user_id),
                    'challenge_id': cid,
                    'progress': amount,
                    'claimed': False,
                    'date': today_start,
                    'created_at': datetime.utcnow()
                })

    @staticmethod
    def claim(user_id, challenge_id):
        """Awards XP + coins if challenge is completed and not yet claimed."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        db = Challenge._db()
        c = db.challenges.find_one({'_id': ObjectId(challenge_id)})
        if not c:
            return {'success': False, 'error': 'Challenge not found'}

        record = db.user_challenges.find_one({
            'user_id': str(user_id),
            'challenge_id': str(challenge_id),
            'date': {'$gte': today_start}
        })
        if not record:
            return {'success': False, 'error': 'No progress recorded today'}
        if record.get('claimed'):
            return {'success': False, 'error': 'Already claimed'}
        if record.get('progress', 0) < c['target_count']:
            return {'success': False, 'error': f"Need {c['target_count']}, have {record.get('progress', 0)}"}

        # Mark claimed
        db.user_challenges.update_one({'_id': record['_id']}, {'$set': {'claimed': True}})

        # Award XP + coins
        try:
            from models.user import User
            user = User.get_by_id(str(user_id))
            if user:
                user.add_xp(c.get('xp_reward', 50))
                db.users.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$inc': {'coins': c.get('coins_reward', 10)}}
                )
        except Exception as e:
            print(f'Challenge claim XP error: {e}')

        return {
            'success': True,
            'xp': c.get('xp_reward', 50),
            'coins': c.get('coins_reward', 10)
        }
