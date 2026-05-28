from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.challenge import Challenge
from services.trending import get_hot_creators
from app import db

challenges_bp = Blueprint('challenges', __name__, url_prefix='/challenges')

@challenges_bp.route('/')
@login_required
def index():
    Challenge.seed_if_empty()
    challenges = Challenge.get_active()
    user_progress = Challenge.get_user_progress(current_user.id)

    enriched = []
    for c in challenges:
        prog = user_progress.get(c['_id'], {})
        c['user_progress']  = prog.get('progress', 0)
        c['user_claimed']   = prog.get('claimed', False)
        c['completed']      = c['user_progress'] >= c['target_count']
        c['percent']        = min(100, int((c['user_progress'] / c['target_count']) * 100))
        enriched.append(c)

    # Weekly leaderboard
    leaderboard = get_hot_creators(db, limit=10)

    return render_template('challenges/index.html',
        challenges=enriched,
        leaderboard=leaderboard,
    )

@challenges_bp.route('/<challenge_id>/claim', methods=['POST'])
@login_required
def claim(challenge_id):
    result = Challenge.claim(current_user.id, challenge_id)
    return jsonify(result)

@challenges_bp.route('/leaderboard')
@login_required
def leaderboard():
    top_users = get_hot_creators(db, limit=50)
    # Enrich with rank
    for i, u in enumerate(top_users):
        u['rank'] = i + 1
    return render_template('challenges/leaderboard.html', top_users=top_users)
