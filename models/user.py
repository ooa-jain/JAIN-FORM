from flask_login import UserMixin
from bson import ObjectId
from datetime import datetime, timedelta

class User(UserMixin):
    def __init__(self, data):
        self.id               = str(data['_id'])
        self.name             = data.get('name', '')
        self.email            = data.get('email', '')
        self.avatar           = data.get('avatar', '')
        self.auth_provider    = data.get('auth_provider', 'email')
        self.password_hash    = data.get('password_hash', '')
        self.created_at       = data.get('created_at')
        self.plan             = data.get('plan', 'free')
        
        # Social & Gamification properties
        self.bio              = data.get('bio', '')
        self.interests        = data.get('interests', [])
        self.followers_count  = data.get('followers_count', 0)
        self.following_count  = data.get('following_count', 0)
        self.xp               = data.get('xp', 0)
        self.level            = data.get('level', 1)
        self.streak_count     = data.get('streak_count', 0)
        self.last_active      = data.get('last_active')
        self.verified_creator = data.get('verified_creator', False)
        self.badges           = data.get('badges', [])
        self.coins            = data.get('coins', 0)
        self.creator_title    = self.compute_title()

    def compute_title(self):
        xp = self.xp or 0
        lvl = self.level or 1
        if lvl >= 20 or xp >= 5000: return 'Legend'
        if lvl >= 15 or xp >= 3000: return 'Elite Builder'
        if lvl >= 10 or xp >= 1500: return 'Research Expert'
        if lvl >= 7  or xp >= 800:  return 'Influencer'
        if lvl >= 4  or xp >= 300:  return 'Creator'
        return 'Beginner'

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

    def add_xp(self, amount):
        """Adds XP and handles leveling up with dynamic notification triggers."""
        self.xp += amount
        leveled_up = False
        while self.xp >= self.level * 100:
            self.xp -= self.level * 100
            self.level += 1
            leveled_up = True
            
        update_data = {'xp': self.xp, 'level': self.level}
        self._db().users.update_one({'_id': ObjectId(self.id)}, {'$set': update_data})
        
        if leveled_up:
            # Trigger real-time alert/notification
            self.create_notification(
                sender_id="system",
                notif_type="level_up",
                text=f"Congratulations! You leveled up to Level {self.level}!"
            )
            # SocketIO real-time notification
            try:
                from routes.realtime import notify_user_socket
                notify_user_socket(self.id, {
                    'type': 'level_up',
                    'title': 'Level Up!',
                    'text': f'You reached Level {self.level}!',
                    'level': self.level,
                    'xp': self.xp
                })
            except Exception:
                pass
        return leveled_up

    def update_streak(self):
        """Verifies daily active checkins and increments streaks and awards XP."""
        now = datetime.utcnow()
        if not self.last_active:
            self.streak_count = 1
            self.last_active = now
            self.add_xp(50) # Daily active XP bonus
        else:
            last_date = self.last_active.date()
            today_date = now.date()
            diff = (today_date - last_date).days
            
            if diff == 1:
                self.streak_count += 1
                self.last_active = now
                self.add_xp(50 + min(self.streak_count * 10, 100)) # Escalating streak reward
                
                # Award streak achievements
                if self.streak_count == 3:
                    self.award_badge('streak_3')
                elif self.streak_count == 7:
                    self.award_badge('streak_7')
                elif self.streak_count == 30:
                    self.award_badge('streak_30')
            elif diff > 1:
                self.streak_count = 1
                self.last_active = now
                self.add_xp(50)
            # If diff == 0, already checked in today - do nothing
            
        self._db().users.update_one(
            {'_id': ObjectId(self.id)},
            {'$set': {'streak_count': self.streak_count, 'last_active': self.last_active}}
        )

    def award_badge(self, badge_id):
        """Awards a specific achievement badge if not already unlocked."""
        if badge_id not in self.badges:
            self.badges.append(badge_id)
            self._db().users.update_one(
                {'_id': ObjectId(self.id)},
                {'$push': {'badges': badge_id}}
            )
            badge_titles = {
                'first_publish': 'Form Pioneer',
                'streak_3': 'Warm-Up',
                'streak_7': 'Dedicated Creator',
                'streak_30': 'Streak Legend',
                'social_star': 'Social Star',
                'responses_10': 'Avid Researcher',
                'ai_guru': 'Mistral Guru'
            }
            title = badge_titles.get(badge_id, badge_id.replace('_', ' ').title())
            
            self.create_notification(
                sender_id="system",
                notif_type="badge",
                text=f"🎖️ Unlocked Achievement: {title}!"
            )
            self.add_xp(100) # Gaining badge grants 100 XP
            
            try:
                from routes.realtime import notify_user_socket
                notify_user_socket(self.id, {
                    'type': 'badge',
                    'title': 'New Achievement Unlocked!',
                    'text': f'🎖️ You unlocked: {title} (+100 XP)'
                })
            except Exception:
                pass

    def create_notification(self, sender_id, notif_type, text, form_id=None):
        """Helper to create DB notification for the user."""
        doc = {
            'user_id': self.id,
            'sender_id': sender_id,
            'type': notif_type,
            'text': text,
            'form_id': str(form_id) if form_id else None,
            'is_read': False,
            'created_at': datetime.utcnow()
        }
        self._db().notifications.insert_one(doc)

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
        doc = {
            'name': name,
            'email': email,
            'avatar': avatar or 'duck_default',
            'auth_provider': auth_provider,
            'created_at': datetime.utcnow(),
            'plan': 'free',
            'bio': '',
            'interests': [],
            'followers_count': 0,
            'following_count': 0,
            'xp': 0,
            'level': 1,
            'streak_count': 0,
            'last_active': datetime.utcnow(),
            'verified_creator': False,
            'badges': []
        }
        if password:
            doc['password_hash'] = bcrypt.generate_password_hash(password).decode('utf-8')
        r = User._db().users.insert_one(doc)
        doc['_id'] = r.inserted_id
        
        user_obj = User(doc)
        user_obj.add_xp(20) # Startup reward
        return user_obj
