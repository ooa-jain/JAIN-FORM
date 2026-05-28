from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models.project import Project
from models.social import Comment, Notification
from models.user import User
from models.challenge import Challenge
from services.ai_service import moderate_text
from app import db
from bson import ObjectId
from datetime import datetime

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

CATEGORIES = ['general', 'startup', 'saas', 'tool', 'design', 'open-source', 'ai', 'mobile', 'game']

@projects_bp.route('/')
@login_required
def feed():
    sort = request.args.get('sort', 'trending')
    category = request.args.get('category', '')
    page = int(request.args.get('page', 1))
    per_page = 18

    projects = Project.get_live(limit=per_page, skip=(page-1)*per_page, category=category, sort=sort)

    for p in projects:
        creator = User.get_by_id(p['user_id'])
        p['creator_name'] = creator.name if creator else 'Anonymous'
        p['creator_level'] = creator.level if creator else 1
        p['upvoted_by_me'] = Project.is_upvoted(p['_id'], current_user.id)

    # Featured projects for hero banner
    featured = list(db.projects.find({'status': 'live', 'is_featured': True}).limit(3))
    for f in featured:
        f['_id'] = str(f['_id'])

    return render_template('projects/feed.html',
        projects=projects,
        featured=featured,
        categories=CATEGORIES,
        active_sort=sort,
        active_category=category,
        page=page,
    )

@projects_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        tagline     = request.form.get('tagline', '').strip()
        description = request.form.get('description', '').strip()
        demo_url    = request.form.get('demo_url', '').strip()
        github_url  = request.form.get('github_url', '').strip()
        website_url = request.form.get('website_url', '').strip()
        category    = request.form.get('category', 'general')
        tags_raw    = request.form.get('tags', '')
        screenshots = [s.strip() for s in request.form.get('screenshots', '').split('\n') if s.strip()]
        tags        = [t.strip().lower() for t in tags_raw.split(',') if t.strip()]
        publish     = request.form.get('publish') == '1'

        if not title:
            return jsonify({'success': False, 'error': 'Title is required'}), 400

        p = Project.create(current_user.id, title, tagline, description)
        pid = str(p['_id'])
        Project.update(pid, {
            'demo_url': demo_url,
            'github_url': github_url,
            'website_url': website_url,
            'category': category,
            'tags': tags,
            'screenshots': screenshots,
            'status': 'live' if publish else 'draft',
            'launched_at': datetime.utcnow() if publish else None,
        })

        if publish:
            current_user.add_xp(50)
            current_user.award_badge('first_publish')
            Challenge.increment_progress(current_user.id, 'launch_project')

        return redirect(url_for('projects.detail', project_id=pid))

    return render_template('projects/new.html', categories=CATEGORIES)

@projects_bp.route('/<project_id>')
@login_required
def detail(project_id):
    p = Project.get_by_id(project_id)
    if not p:
        return render_template('errors/404.html'), 404

    Project.increment_views(project_id)

    creator = User.get_by_id(p['user_id'])
    p['creator_name'] = creator.name if creator else 'Anonymous'
    p['creator_level'] = creator.level if creator else 1
    p['upvoted_by_me'] = Project.is_upvoted(project_id, current_user.id)

    # Fetch comments
    comments = list(db.comments.find({
        'form_id': f'project_{project_id}',
        'parent_id': None
    }).sort('created_at', -1).limit(50))
    for c in comments:
        c['_id'] = str(c['_id'])

    return render_template('projects/detail.html', project=p, creator=creator, comments=comments)

@projects_bp.route('/<project_id>/upvote', methods=['POST'])
@login_required
def upvote(project_id):
    upvoted = Project.upvote(project_id, current_user.id)
    p = Project.get_by_id(project_id)
    count = p.get('upvotes_count', 0) if p else 0

    # Broadcast live
    try:
        from routes.realtime import broadcast_project_upvote
        broadcast_project_upvote(project_id, count)
    except:
        pass

    return jsonify({'success': True, 'upvoted': upvoted, 'count': count})

@projects_bp.route('/<project_id>/comment', methods=['POST'])
@login_required
def comment(project_id):
    text = request.form.get('text', '').strip()
    if not text:
        return jsonify({'success': False, 'error': 'Comment cannot be empty'}), 400

    safety = moderate_text(text)
    if safety.get('is_flagged'):
        return jsonify({'success': False, 'error': f"AI Moderation: {safety.get('reason', 'Inappropriate content')}"}), 403

    from models.social import Comment
    c = Comment.create(
        form_id=f'project_{project_id}',
        user_id=current_user.id,
        username=current_user.name,
        user_avatar=current_user.avatar,
        text=text,
    )
    current_user.add_xp(10)
    Challenge.increment_progress(current_user.id, 'add_comment')
    return jsonify({'success': True, 'comment': c})

@projects_bp.route('/mine')
@login_required
def my_projects():
    projects = Project.get_by_user(current_user.id)
    return render_template('projects/mine.html', projects=projects, categories=CATEGORIES)

@projects_bp.route('/<project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_id):
    p = Project.get_by_id(project_id)
    if not p or p['user_id'] != current_user.id:
        return redirect(url_for('projects.my_projects'))

    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        tagline     = request.form.get('tagline', '').strip()
        description = request.form.get('description', '').strip()
        demo_url    = request.form.get('demo_url', '').strip()
        github_url  = request.form.get('github_url', '').strip()
        website_url = request.form.get('website_url', '').strip()
        category    = request.form.get('category', 'general')
        tags_raw    = request.form.get('tags', '')
        screenshots = [s.strip() for s in request.form.get('screenshots', '').split('\n') if s.strip()]
        tags        = [t.strip().lower() for t in tags_raw.split(',') if t.strip()]
        publish     = request.form.get('publish') == '1'

        update_data = {
            'title': title, 'tagline': tagline, 'description': description,
            'demo_url': demo_url, 'github_url': github_url, 'website_url': website_url,
            'category': category, 'tags': tags, 'screenshots': screenshots,
        }
        if publish and p.get('status') != 'live':
            update_data['status'] = 'live'
            update_data['launched_at'] = datetime.utcnow()
            current_user.add_xp(50)
            Challenge.increment_progress(current_user.id, 'launch_project')

        Project.update(project_id, update_data)
        return redirect(url_for('projects.detail', project_id=project_id))

    return render_template('projects/new.html', project=p, categories=CATEGORIES, editing=True)

@projects_bp.route('/<project_id>/delete', methods=['POST'])
@login_required
def delete(project_id):
    p = Project.get_by_id(project_id)
    if p and p['user_id'] == current_user.id:
        Project.delete(project_id)
    return redirect(url_for('projects.my_projects'))

@projects_bp.route('/ai-describe', methods=['POST'])
@login_required
def ai_describe():
    """Generate project description using Mistral AI."""
    title   = request.json.get('title', '')
    tagline = request.json.get('tagline', '')
    if not title:
        return jsonify({'success': False, 'error': 'Title required'}), 400
    try:
        from services.ai_service import call_mistral
        msgs = [
            {'role': 'system', 'content': 'Write a compelling, concise product description for a creator showcase page. 2-3 paragraphs max. Use markdown.'},
            {'role': 'user', 'content': f'Product: {title}\nTagline: {tagline}'}
        ]
        desc = call_mistral(msgs, temperature=0.7, max_tokens=500)
        return jsonify({'success': True, 'description': desc})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
