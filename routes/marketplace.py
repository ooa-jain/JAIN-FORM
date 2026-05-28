from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models.form import Form
from app import db
from bson import ObjectId

marketplace_bp = Blueprint('marketplace', __name__, url_prefix='/marketplace')

@marketplace_bp.route('/')
@login_required
def store():
    """Marketplace store page. Lists all publicly shared form templates."""
    category = request.args.get('category', '')
    
    query = {
        'settings.is_published': True,
        'is_template': True
    }
    if category:
        query['template_category'] = category.lower()

    templates = list(db.forms.find(query).sort('likes_count', -1).limit(40))
    for t in templates:
        t['_id'] = str(t['_id'])
        from models.user import User
        creator = User.get_by_id(t['user_id'])
        t['creator_name'] = creator.name if creator else "Anonymous"
        t['creator_avatar'] = creator.avatar if creator else "duck_default"
        t['liked_by_me'] = Form.is_liked(t['_id'], current_user.id)

    # Categories list
    categories = ['Startup', 'HR', 'SaaS', 'Education', 'Ecommerce', 'Marketing', 'Events', 'Creator Tools']

    return render_template(
        'marketplace/marketplace.html',
        templates=templates,
        categories=categories,
        active_category=category
    )

@marketplace_bp.route('/publish/<form_id>', methods=['POST'])
@login_required
def publish_template(form_id):
    """Flags an existing form as a reusable template in the public store."""
    f = Form.get_by_id(form_id)
    if not f or f['user_id'] != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized or form not found.'}), 403

    category = request.form.get('category', 'startup').lower()
    tags_raw = request.form.get('tags', '')
    tags = [t.strip().lower() for t in tags_raw.split(',') if t.strip()]

    Form.update(form_id, {
        'is_template': True,
        'template_category': category,
        'tags': tags,
        'settings.is_published': True # Templates must be published to be visible
    })

    # Award XP for template contribution
    current_user.add_xp(50)
    current_user.award_badge('first_publish')

    return jsonify({
        'success': True,
        'message': 'Successfully published form to the Template Marketplace!'
    })

@marketplace_bp.route('/duplicate/<form_id>', methods=['POST'])
@login_required
def duplicate_template(form_id):
    """Copies a template completely and registers it under the caller's workspace."""
    if not current_user.can_create_form():
        return jsonify({'success': False, 'error': 'Form limits reached for your current plan. Please upgrade.'}), 403

    orig = Form.get_by_id(form_id)
    if not orig or not orig.get('is_template'):
        return jsonify({'success': False, 'error': 'Template not found.'}), 404

    # Create new form copy
    copy_title = f"{orig['title']} (Template)"
    nf = Form.create(current_user.id, copy_title)
    
    # Update pages and themes from original
    Form.update(str(nf['_id']), {
        'pages': orig['pages'],
        'theme': orig['theme'],
        'description': orig.get('description', ''),
        'settings': {
            'is_published': False, # starts as draft
            'show_progress': orig['settings'].get('show_progress', True),
            'confirmation_message': orig['settings'].get('confirmation_message', 'Thank you!'),
            'redirect_url': orig['settings'].get('redirect_url', ''),
            'notify_email': current_user.email,
            'notify_on_submit': False
        }
    })

    # User gains some XP for starting from a template
    current_user.add_xp(15)

    return jsonify({
        'success': True,
        'form_id': str(nf['_id']),
        'redirect': url_for('builder.edit', form_id=str(nf['_id']))
    })
