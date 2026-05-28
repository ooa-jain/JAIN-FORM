"""
Community Publishing Routes
Allows forms, newsletters, and deployed sites to be pushed as community posts.
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db
from bson import ObjectId
from datetime import datetime

publish_bp = Blueprint('publish', __name__, url_prefix='/publish')

COMMUNITY_CATEGORIES = [
    'general', 'startup', 'research', 'education', 'saas', 'ai',
    'hr', 'marketing', 'ecommerce', 'design', 'productivity', 'fun'
]

@publish_bp.route('/form/<form_id>', methods=['POST'])
@login_required
def publish_form(form_id):
    """Publish a form as a community post with category and tags."""
    from models.form import Form
    f = Form.get_by_id(form_id)
    if not f or f['user_id'] != current_user.id:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    category = request.form.get('category', 'general')
    tags_raw  = request.form.get('tags', '')
    tags      = [t.strip().lower() for t in tags_raw.split(',') if t.strip()]
    highlight = request.form.get('highlight') == '1'

    # Publish the form (make it live)
    update = {
        'settings.is_published': True,
        'template_category': category,
        'tags': tags,
        'community_post': True,
        'community_posted_at': datetime.utcnow(),
        'is_featured': highlight and current_user.plan in ('pro', 'basic'),
    }
    Form.update(form_id, update)
    current_user.add_xp(30)
    current_user.award_badge('first_publish')

    # Broadcast to discover feed via Socket.IO
    try:
        from routes.realtime import broadcast_discover_item
        broadcast_discover_item({'type': 'form', 'title': f['title'], 'creator': current_user.name})
    except:
        pass

    return jsonify({'success': True, 'message': 'Form published to community!'})

@publish_bp.route('/newsletter/<nl_id>', methods=['POST'])
@login_required
def publish_newsletter(nl_id):
    """Share a newsletter edition as a community post."""
    nl = db.newsletters.find_one({'_id': ObjectId(nl_id), 'user_id': current_user.id})
    if not nl:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    category = request.form.get('category', 'general')
    tags_raw  = request.form.get('tags', '')
    tags      = [t.strip().lower() for t in tags_raw.split(',') if t.strip()]

    # Create a community post doc in newsletters collection
    db.newsletters.update_one(
        {'_id': ObjectId(nl_id)},
        {'$set': {
            'community_post': True,
            'community_category': category,
            'community_tags': tags,
            'community_posted_at': datetime.utcnow(),
            'is_published': True,
        }}
    )
    current_user.add_xp(20)

    try:
        from routes.realtime import broadcast_discover_item
        broadcast_discover_item({'type': 'newsletter', 'title': nl.get('name', 'Newsletter'), 'creator': current_user.name})
    except:
        pass

    return jsonify({
        'success': True,
        'message': 'Newsletter shared to community!',
        'public_url': f'/newsletter/{nl_id}/read',
        'community_url': '/newsletter/community'
    })

@publish_bp.route('/site/<site_id>', methods=['POST'])
@login_required
def publish_site(site_id):
    """Push a deployed site to community with Live Site highlight badge."""
    site = db.published_sites.find_one({'_id': ObjectId(site_id), 'user_id': current_user.id})
    if not site:
        return jsonify({'success': False, 'error': 'Site not found'}), 404

    category    = request.form.get('category', 'general')
    description = request.form.get('description', '').strip()
    tags_raw    = request.form.get('tags', '')
    tags        = [t.strip().lower() for t in tags_raw.split(',') if t.strip()]
    env_file    = request.files.get('env_file')

    env_vars = {}
    if env_file and env_file.filename.endswith('.env'):
        try:
            content = env_file.read().decode('utf-8')
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, val = line.partition('=')
                    env_vars[key.strip()] = val.strip()
        except Exception as e:
            print(f'[env_file parse error] {e}')

    db.published_sites.update_one(
        {'_id': ObjectId(site_id)},
        {'$set': {
            'community_post': True,
            'community_category': category,
            'community_tags': tags,
            'community_description': description,
            'community_posted_at': datetime.utcnow(),
            'env_vars': {k: '***' for k in env_vars},  # Store key names only, not values
            'is_community_highlighted': True,
        }}
    )
    current_user.add_xp(50)
    current_user.award_badge('first_publish')

    # Create a project entry for visibility
    from models.project import Project
    slug = site.get('slug', site_id)
    site_url = f"/sites/{slug}/"
    existing = db.projects.find_one({'user_id': current_user.id, 'website_url': site_url})
    if not existing:
        p = Project.create(
            user_id=current_user.id,
            title=site.get('title', 'Deployed Site'),
            tagline=description or 'A live deployed site on Draftspace',
            description=description,
        )
        Project.update(str(p['_id']), {
            'status': 'live',
            'category': category,
            'tags': tags,
            'website_url': site_url,
            'is_featured': True,
            'launched_at': datetime.utcnow(),
        })

    try:
        from routes.realtime import broadcast_discover_item
        broadcast_discover_item({'type': 'site', 'title': site.get('title'), 'creator': current_user.name})
    except:
        pass

    return jsonify({'success': True, 'message': 'Site highlighted on community! 🎉', 'env_keys': list(env_vars.keys())})

@publish_bp.route('/categories')
def get_categories():
    return jsonify({'categories': COMMUNITY_CATEGORIES})
