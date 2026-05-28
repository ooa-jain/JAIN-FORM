from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.form import Form
from models.response import Response
from services.ai_service import summarize_responses
from app import db
from bson import ObjectId
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/forms/<form_id>')
@login_required
def form_analytics(form_id):
    f = Form.get_by_id(form_id)
    if not f or f['user_id'] != current_user.id:
        return render_template('errors/404.html'), 404

    responses = Response.get_by_form(form_id)
    response_count = len(responses)

    # Time-series: responses per day (last 14 days)
    days_data = {}
    cutoff = datetime.utcnow() - timedelta(days=14)
    for r in responses:
        ts = r.get('submitted_at')
        if ts and ts >= cutoff:
            day_key = ts.strftime('%b %d')
            days_data[day_key] = days_data.get(day_key, 0) + 1

    timeline_labels = sorted(days_data.keys())
    timeline_values = [days_data[k] for k in timeline_labels]

    # Field-level tallies for choice/rating fields
    charts = {}
    for page in f.get('pages', []):
        for field in page.get('fields', []):
            ftype = field.get('type')
            fid   = field.get('id')
            flabel= field.get('label', fid)
            if ftype in ('radio', 'checkbox', 'dropdown', 'rating', 'scale'):
                options = field.get('options', [])
                if ftype == 'rating':
                    max_r = field.get('max_rating', 5)
                    options = [str(i) for i in range(1, int(max_r)+1)]
                tally = {opt: 0 for opt in options}
                for r in responses:
                    ans = r.get('data', {}).get(fid)
                    if ans:
                        for a in (ans if isinstance(ans, list) else [ans]):
                            key = str(a)
                            if key in tally:
                                tally[key] += 1
                charts[fid] = {
                    'label': flabel,
                    'type': 'bar' if ftype == 'checkbox' else 'doughnut',
                    'labels': list(tally.keys()),
                    'values': list(tally.values()),
                }

    # Social stats
    likes_count    = f.get('likes_count', 0)
    comments_count = f.get('comments_count', 0)

    # Cached AI summary
    ai_summary = None
    cache = db.analytics.find_one({'form_id': form_id})
    if cache:
        ai_summary = cache.get('report')

    return render_template('analytics/form_analytics.html',
        form=f,
        response_count=response_count,
        timeline_labels=timeline_labels,
        timeline_values=timeline_values,
        charts=charts,
        likes_count=likes_count,
        comments_count=comments_count,
        ai_summary=ai_summary,
    )

@analytics_bp.route('/forms/<form_id>/ai-explain', methods=['POST'])
@login_required
def ai_explain(form_id):
    f = Form.get_by_id(form_id)
    if not f or f['user_id'] != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    responses = Response.get_by_form(form_id)
    if not responses:
        return jsonify({'success': False, 'error': 'No responses to analyze'}), 400

    try:
        summary = summarize_responses(f, responses)
        # Cache it
        db.analytics.update_one(
            {'form_id': form_id},
            {'$set': {'form_id': form_id, 'report': summary, 'updated_at': datetime.utcnow()}},
            upsert=True
        )
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
