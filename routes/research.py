from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models.form import Form
from models.response import Response
from services.ai_service import summarize_responses, generate_marketing_assets
from app import db
from bson import ObjectId

research_bp = Blueprint('research', __name__, url_prefix='/research')

@research_bp.route('/')
@login_required
def hub():
    """Research Hub Dashboard. Displays active surveys, opinion polls, and startup validators."""
    category = request.args.get('category', 'startup') # startup, market, academic, poll
    
    query = {
        'settings.is_published': True,
        'is_poll': True if category == 'poll' else False
    }
    if category != 'poll':
        query['template_category'] = category

    forms = list(db.forms.find(query).sort('response_count', -1).limit(30))
    for f in forms:
        f['_id'] = str(f['_id'])
        f['liked_by_me'] = Form.is_liked(f['_id'], current_user.id)
        from models.user import User
        creator = User.get_by_id(f['user_id'])
        f['creator_name'] = creator.name if creator else "Anonymous"
        f['creator_avatar'] = creator.avatar if creator else "duck_default"

    return render_template(
        'research/hub.html', 
        forms=forms, 
        active_category=category
    )

@research_bp.route('/<form_id>/report')
@login_required
def report(form_id):
    """Renders the AI-powered response report containing sentiment summaries and Chart.js feeds."""
    f = Form.get_by_id(form_id)
    if not f:
        return render_template('errors/404.html'), 404
        
    # Security check: only the creator or featured public listings can view research insights
    if f['user_id'] != current_user.id and not f['settings'].get('is_published'):
        return render_template('errors/unpublished.html', form=f), 403

    responses = Response.get_by_form(form_id)
    response_count = len(responses)

    # 1. Standard aggregations (e.g. choice distributions) for Chart.js rendering
    # We will build a helper dictionary of fields and answer tallies
    charts_data = {}
    
    for page in f.get('pages', []):
        for field in page.get('fields', []):
            f_type = field.get('type')
            f_id = field.get('id')
            f_label = field.get('label')
            
            if f_type in ('radio', 'checkbox', 'dropdown', 'rating', 'scale'):
                options = field.get('options', [])
                if f_type in ('rating', 'scale'):
                    max_val = field.get('max_rating', 5) if f_type == 'rating' else field.get('scale_max', 10)
                    options = [str(i) for i in range(1, int(max_val) + 1)]
                
                # Tally answers
                tally = {opt: 0 for opt in options}
                for r in responses:
                    ans = r.get('data', {}).get(f_id)
                    if ans:
                        if isinstance(ans, list):
                            for a in ans:
                                if str(a) in tally:
                                    tally[str(a)] += 1
                        else:
                            if str(ans) in tally:
                                tally[str(ans)] += 1
                                
                charts_data[f_id] = {
                    'label': f_label,
                    'type': 'bar' if f_type == 'checkbox' else 'pie',
                    'labels': list(tally.keys()),
                    'values': list(tally.values())
                }

    # 2. AI-powered summary insights (with cache capabilities on MongoDB)
    analysis_cache = db.analytics.find_one({'form_id': str(form_id)})
    
    if analysis_cache and (datetime.utcnow() - analysis_cache['updated_at']).seconds < 3600:
        # Cache hit
        ai_summary = analysis_cache['report']
    else:
        # Cache miss - compile from Mistral
        if response_count > 0:
            ai_summary = summarize_responses(f, responses)
        else:
            ai_summary = {
                "insights": ["Waiting for responses to begin AI summaries."],
                "sentiment": {"label": "No Data", "score": 0, "explanation": "No feedback collected yet."},
                "trends": [],
                "recommendations": ["Share your form link publicly to collect community entries."]
            }
            
        # Update cache
        from datetime import datetime
        db.analytics.update_one(
            {'form_id': str(form_id)},
            {'$set': {
                'form_id': str(form_id),
                'report': ai_summary,
                'updated_at': datetime.utcnow()
            }},
            upsert=True
        )

    return render_template(
        'research/report.html',
        form=f,
        response_count=response_count,
        charts_data=charts_data,
        ai_summary=ai_summary
    )

@research_bp.route('/<form_id>/generate-assets', methods=['POST'])
@login_required
def generate_assets(form_id):
    """Triggers Mistral AI content generation engines to draft promotional campaigns."""
    f = Form.get_by_id(form_id)
    if not f or f['user_id'] != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized or form not found.'}), 403

    asset_type = request.form.get('type', 'insight_report') # blog_post, newsletter, social_thread, insight_report
    responses = Response.get_by_form(form_id)
    
    if not responses:
        return jsonify({'success': False, 'error': 'No response data collected yet.'}), 400

    content = generate_marketing_assets(f, responses, asset_type)
    return jsonify({
        'success': True,
        'content': content
    })
