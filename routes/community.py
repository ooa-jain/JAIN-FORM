from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models.form import Form
from models.social import Comment, Follower, Notification
from models.user import User
from services.ai_service import moderate_text
from app import db
from bson import ObjectId
from datetime import datetime

community_bp = Blueprint('community', __name__)

@community_bp.route('/feed')
@login_required
def feed():
    """Main community discovery feed. Supports trending, newest, staff picks, and tags filtering."""
    filter_type = request.args.get('filter', 'trending') # trending, newest, featured
    category = request.args.get('category', '')
    tag = request.args.get('tag', '')

    query = {'settings.is_published': True}
    if category:
        query['template_category'] = category.lower()
    if tag:
        query['tags'] = tag.lower()

    if filter_type == 'featured':
        query['is_featured'] = True
        forms = list(db.forms.find(query).sort('created_at', -1))
    elif filter_type == 'newest':
        forms = list(db.forms.find(query).sort('created_at', -1))
    else: # trending defaults to sorting by likes_count + response_count
        # MongoDB aggregation pipeline for high-scale sorting
        pipeline = [
            {'$match': query},
            {
                '$addFields': {
                    'engagement_score': {'$add': ['$likes_count', '$response_count']}
                }
            },
            {'$sort': {'engagement_score': -1, 'created_at': -1}},
            {'$limit': 50}
        ]
        forms = list(db.forms.aggregate(pipeline))

    # Hydrate creator names and checking liked states
    for f in forms:
        f['_id'] = str(f['_id'])
        creator = User.get_by_id(f['user_id'])
        f['creator_name'] = creator.name if creator else "Anonymous"
        f['creator_avatar'] = creator.avatar if creator else "duck_default"
        f['creator_level'] = creator.level if creator else 1
        f['liked_by_me'] = Form.is_liked(f['_id'], current_user.id)

    # Fetch top creators for the leaderboards side widget
    leaderboard = list(db.users.find().sort('xp', -1).limit(5))
    
    # Fetch user notifications
    notifications = Notification.get_unread_by_user(current_user.id)
    
    # Check streak
    current_user.update_streak()

    return render_template(
        'community/feed.html', 
        forms=forms, 
        leaderboard=leaderboard, 
        notifications=notifications,
        active_filter=filter_type,
        active_category=category,
        active_tag=tag
    )

@community_bp.route('/forms/<form_id>/like', methods=['POST'])
@login_required
def like_form(form_id):
    """Liking/unliking forms. Denormalizes counts and awards XP to creators."""
    liked = Form.like(form_id, current_user.id)
    f = Form.get_by_id(form_id)
    likes_count = f.get('likes_count', 0) if f else 0
    return jsonify({
        'success': True,
        'liked': liked,
        'likes_count': likes_count
    })

@community_bp.route('/forms/<form_id>/comment', methods=['POST'])
@login_required
def add_comment(form_id):
    """Publishes a new comment. Moderate for toxicity prior to insertion."""
    text = request.form.get('text', '').strip()
    parent_id = request.form.get('parent_id')
    
    if not text:
        return jsonify({'success': False, 'error': 'Comment content cannot be empty.'}), 400

    # Mistral content moderation filter
    safety = moderate_text(text)
    if safety.get('is_flagged'):
        return jsonify({
            'success': False, 
            'error': f"Comment blocked by AI Content Moderation: {safety.get('reason', 'Inappropriate content detected')}"
        }), 403

    # Create comment
    c = Comment.create(
        form_id=form_id,
        user_id=current_user.id,
        username=current_user.name,
        user_avatar=current_user.avatar,
        text=text,
        parent_id=parent_id
    )

    # Award user XP for contributing feedback
    current_user.add_xp(10)

    # Send Notification to form creator
    f = Form.get_by_id(form_id)
    if f and f['user_id'] != current_user.id:
        creator = User.get_by_id(f['user_id'])
        if creator:
            creator.create_notification(
                sender_id=current_user.id,
                notif_type="comment",
                text=f"💬 commented: \"{text[:40]}...\"",
                form_id=form_id
            )
            try:
                from routes.realtime import notify_user_socket
                notify_user_socket(f['user_id'], {
                    'type': 'comment',
                    'title': 'New Comment!',
                    'text': f"💬 {current_user.name} commented on '{f['title']}'"
                })
            except:
                pass

    # Real-time WebSocket commentary stream broadcast
    try:
        from routes.realtime import broadcast_live_comment
        broadcast_live_comment(form_id, c)
    except Exception as e:
        print(f"WS comment broadcast error: {e}")

    return jsonify({
        'success': True,
        'comment': c
    })

@community_bp.route('/follow/<user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    """Enables followers mechanics and starts community tracking."""
    success = Follower.follow(current_user.id, user_id)
    if success:
        current_user.add_xp(15) # follower gains XP for community follow
        return jsonify({'success': True, 'following': True})
    return jsonify({'success': False, 'error': 'Could not follow creator.'}), 400

@community_bp.route('/unfollow/<user_id>', methods=['POST'])
@login_required
def unfollow_user(user_id):
    """Removes active following link."""
    success = Follower.unfollow(current_user.id, user_id)
    if success:
        return jsonify({'success': True, 'following': False})
    return jsonify({'success': False, 'error': 'Could not unfollow creator.'}), 400

@community_bp.route('/profile/<username>')
@login_required
def profile(username):
    """Renders user public dashboard, accomplishments, and created forms."""
    user_data = db.users.find_one({'name': username})
    if not user_data:
        return render_template('errors/404.html'), 404
        
    profile_user = User(user_data)
    
    # Check following status
    is_following_profile = Follower.is_following(current_user.id, profile_user.id)
    
    # Fetch published forms
    forms = list(db.forms.find({
        'user_id': profile_user.id,
        'settings.is_published': True
    }).sort('created_at', -1))
    
    for f in forms:
        f['_id'] = str(f['_id'])
        f['liked_by_me'] = Form.is_liked(f['_id'], current_user.id)

    badge_meta = {
        'first_publish': {'title': 'Form Pioneer', 'desc': 'Published your first public form', 'icon': 'ph ph-rocket-launch'},
        'streak_3': {'title': 'Warm-Up', 'desc': 'Maintained a 3-day active streak', 'icon': 'ph ph-fire-simple'},
        'streak_7': {'title': 'Dedicated Creator', 'desc': 'Maintained a 7-day active streak', 'icon': 'ph ph-fire'},
        'streak_30': {'title': 'Streak Legend', 'desc': 'Maintained a 30-day active streak', 'icon': 'ph ph-crown'},
        'social_star': {'title': 'Social Star', 'desc': 'Earned 10+ community followers', 'icon': 'ph ph-star-of-david'},
        'responses_10': {'title': 'Avid Researcher', 'desc': 'Collected 10+ form submissions', 'icon': 'ph ph-chats'},
        'ai_guru': {'title': 'Mistral Guru', 'desc': 'Created 5+ forms using AI builders', 'icon': 'ph ph-brain'}
    }

    user_badges = []
    for b_id in profile_user.badges:
        meta = badge_meta.get(b_id, {'title': b_id.replace('_', ' ').title(), 'desc': 'Unlocked Achievement', 'icon': 'ph ph-award'})
        user_badges.append(meta)

    return render_template(
        'community/profile.html', 
        user=profile_user, 
        forms=forms,
        badges=user_badges,
        is_following=is_following_profile
    )

@community_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def read_all_notifications():
    """Clear user notifications badge."""
    Notification.mark_all_read(current_user.id)
    return jsonify({'success': True})
