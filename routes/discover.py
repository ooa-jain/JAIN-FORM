from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from services.trending import get_discover_feed, get_hot_creators
from models.social import Notification
from app import db

discover_bp = Blueprint('discover', __name__, url_prefix='/discover')

CONTENT_TYPES = ['all', 'forms', 'projects', 'newsletters', 'research']
SORT_OPTIONS  = ['trending', 'newest', 'top']
CATEGORIES    = ['startup', 'saas', 'hr', 'education', 'ai', 'marketing', 'design', 'open-source', 'ecommerce']

@discover_bp.route('/')
@login_required
def feed():
    page         = max(1, int(request.args.get('page', 1)))
    content_type = request.args.get('type', 'all')
    sort         = request.args.get('sort', 'trending')
    category     = request.args.get('category', '')

    items = get_discover_feed(
        db=db,
        user_id=current_user.id,
        page=page,
        per_page=24,
        content_type=content_type,
        sort=sort,
        category=category,
    )

    hot_creators   = get_hot_creators(db, limit=8)
    notifications  = Notification.get_unread_by_user(current_user.id)

    # Update streak on discovery
    try:
        current_user.update_streak()
    except:
        pass

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Infinite scroll JSON response
        return jsonify({
            'items': items,
            'has_more': len(items) >= 24,
            'next_page': page + 1
        })

    return render_template('discover/feed.html',
        items=items,
        hot_creators=hot_creators,
        notifications=notifications,
        page=page,
        active_type=content_type,
        active_sort=sort,
        active_category=category,
        content_types=CONTENT_TYPES,
        categories=CATEGORIES,
    )

@discover_bp.route('/search')
@login_required
def search():
    q        = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    results  = {'forms': [], 'projects': [], 'creators': []}

    if q:
        # Forms full-text search
        try:
            db.forms.create_index([('title', 'text'), ('description', 'text')])
            form_results = list(db.forms.find(
                {'$text': {'$search': q}, 'settings.is_published': True},
                {'score': {'$meta': 'textScore'}}
            ).sort([('score', {'$meta': 'textScore'})]).limit(10))
            for f in form_results:
                f['_id'] = str(f['_id'])
                f['_content_type'] = 'form'
            results['forms'] = form_results
        except:
            results['forms'] = list(db.forms.find(
                {'title': {'$regex': q, '$options': 'i'}, 'settings.is_published': True}
            ).limit(10))
            for f in results['forms']:
                f['_id'] = str(f['_id'])

        # Projects search
        try:
            proj_results = list(db.projects.find(
                {'$or': [
                    {'title': {'$regex': q, '$options': 'i'}},
                    {'tagline': {'$regex': q, '$options': 'i'}},
                    {'tags': {'$in': [q.lower()]}},
                ], 'status': 'live'}
            ).limit(10))
            for p in proj_results:
                p['_id'] = str(p['_id'])
                p['_content_type'] = 'project'
            results['projects'] = proj_results
        except:
            pass

        # Creator search
        try:
            creator_results = list(db.users.find(
                {'name': {'$regex': q, '$options': 'i'}},
                {'name': 1, 'bio': 1, 'xp': 1, 'level': 1, 'followers_count': 1}
            ).limit(8))
            for c in creator_results:
                c['_id'] = str(c['_id'])
            results['creators'] = creator_results
        except:
            pass

    return render_template('discover/search.html',
        q=q,
        results=results,
        categories=CATEGORIES,
        active_category=category,
    )

@discover_bp.route('/bookmark/<content_type>/<item_id>', methods=['POST'])
@login_required
def bookmark(content_type, item_id):
    existing = db.bookmarks.find_one({
        'user_id': current_user.id,
        'item_id': item_id,
        'content_type': content_type
    })
    if existing:
        db.bookmarks.delete_one({'_id': existing['_id']})
        return jsonify({'success': True, 'bookmarked': False})
    else:
        from datetime import datetime
        db.bookmarks.insert_one({
            'user_id': current_user.id,
            'item_id': item_id,
            'content_type': content_type,
            'created_at': datetime.utcnow()
        })
        return jsonify({'success': True, 'bookmarked': True})

@discover_bp.route('/bookmarks')
@login_required
def bookmarks():
    items = list(db.bookmarks.find({'user_id': current_user.id}).sort('created_at', -1))
    enriched = []
    for b in items:
        b['_id'] = str(b['_id'])
        if b['content_type'] == 'form':
            from models.form import Form
            item = Form.get_by_id(b['item_id'])
            if item:
                item['_content_type'] = 'form'
                enriched.append(item)
        elif b['content_type'] == 'project':
            from models.project import Project
            item = Project.get_by_id(b['item_id'])
            if item:
                item['_content_type'] = 'project'
                enriched.append(item)
    return render_template('discover/bookmarks.html', items=enriched)
