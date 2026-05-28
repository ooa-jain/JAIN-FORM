"""
Trending Engine — Draftspace
Computes engagement scores for content ranking using time-decay and activity signals.
"""
from datetime import datetime, timedelta

def _hours_since(dt):
    if not dt:
        return 720  # default 30 days old
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except:
            return 720
    return max(1, (datetime.utcnow() - dt).total_seconds() / 3600)

def compute_trending_score(doc):
    """
    Hacker News-style gravity decay formula:
    score = (likes*2 + comments*3 + views*0.1 + responses*4) / (hours_old + 2)^1.5
    """
    likes     = doc.get('likes_count', 0) or doc.get('upvotes_count', 0)
    comments  = doc.get('comments_count', 0)
    views     = doc.get('views_count', doc.get('response_count', 0))
    responses = doc.get('response_count', 0)
    created   = doc.get('created_at') or doc.get('launched_at')
    hours_old = _hours_since(created)

    raw = (likes * 2) + (comments * 3) + (views * 0.1) + (responses * 4)
    score = raw / ((hours_old + 2) ** 1.5)
    return round(score, 4)

def get_trending_forms(db, limit=20, skip=0, category=''):
    query = {'settings.is_published': True}
    if category:
        query['template_category'] = category.lower()

    pipeline = [
        {'$match': query},
        {'$addFields': {
            'hours_old': {
                '$divide': [
                    {'$subtract': [datetime.utcnow(), '$created_at']},
                    3600000  # ms to hours
                ]
            }
        }},
        {'$addFields': {
            'trend_score': {
                '$divide': [
                    {'$add': [
                        {'$multiply': [{'$ifNull': ['$likes_count', 0]}, 2]},
                        {'$multiply': [{'$ifNull': ['$comments_count', 0]}, 3]},
                        {'$multiply': [{'$ifNull': ['$response_count', 0]}, 4]},
                    ]},
                    {'$pow': [{'$add': ['$hours_old', 2]}, 1.5]}
                ]
            }
        }},
        {'$sort': {'trend_score': -1, 'created_at': -1}},
        {'$skip': skip},
        {'$limit': limit}
    ]
    results = list(db.forms.aggregate(pipeline))
    for r in results:
        r['_id'] = str(r['_id'])
    return results

def get_trending_projects(db, limit=20, skip=0, category=''):
    query = {'status': 'live'}
    if category:
        query['category'] = category.lower()

    pipeline = [
        {'$match': query},
        {'$addFields': {
            'hours_old': {
                '$divide': [
                    {'$subtract': [datetime.utcnow(), '$created_at']},
                    3600000
                ]
            }
        }},
        {'$addFields': {
            'trend_score': {
                '$divide': [
                    {'$add': [
                        {'$multiply': [{'$ifNull': ['$upvotes_count', 0]}, 3]},
                        {'$multiply': [{'$ifNull': ['$comments_count', 0]}, 2]},
                        {'$multiply': [{'$ifNull': ['$views_count', 0]}, 0.1]},
                    ]},
                    {'$pow': [{'$add': ['$hours_old', 2]}, 1.5]}
                ]
            }
        }},
        {'$sort': {'trend_score': -1, 'created_at': -1}},
        {'$skip': skip},
        {'$limit': limit}
    ]
    results = list(db.projects.aggregate(pipeline))
    for r in results:
        r['_id'] = str(r['_id'])
    return results

def get_hot_creators(db, limit=10):
    """Top XP earners in last 7 days (approximated via total XP leaderboard)."""
    results = list(db.users.find(
        {},
        {'name': 1, 'xp': 1, 'level': 1, 'streak_count': 1, 'verified_creator': 1, 'badges': 1}
    ).sort('xp', -1).limit(limit))
    for r in results:
        r['_id'] = str(r['_id'])
    return results

def get_discover_feed(db, user_id=None, page=1, per_page=20, content_type='all', sort='trending', category=''):
    """
    Unified discovery feed mixing forms + projects.
    Returns list of enriched content cards with type field.
    """
    from models.user import User
    skip = (page - 1) * per_page
    half = per_page // 2

    if content_type in ('all', 'forms'):
        forms = get_trending_forms(db, limit=half if content_type == 'all' else per_page, skip=skip, category=category)
        for f in forms:
            f['_content_type'] = 'form'
            creator = User.get_by_id(f.get('user_id', ''))
            f['creator_name'] = creator.name if creator else 'Anonymous'
            f['creator_level'] = creator.level if creator else 1
    else:
        forms = []

    if content_type in ('all', 'projects'):
        projects = get_trending_projects(db, limit=half if content_type == 'all' else per_page, skip=skip, category=category)
        for p in projects:
            p['_content_type'] = 'project'
            creator = User.get_by_id(p.get('user_id', ''))
            p['creator_name'] = creator.name if creator else 'Anonymous'
            p['creator_level'] = creator.level if creator else 1
    else:
        projects = []

    # Interleave forms and projects
    feed = []
    fi, pi = 0, 0
    while fi < len(forms) or pi < len(projects):
        if fi < len(forms):
            feed.append(forms[fi]); fi += 1
        if pi < len(projects):
            feed.append(projects[pi]); pi += 1

    return feed
