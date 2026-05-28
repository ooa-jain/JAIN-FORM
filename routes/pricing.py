from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
import os, requests, hmac, hashlib
from requests.auth import HTTPBasicAuth

pricing_bp = Blueprint('pricing', __name__, url_prefix='/pricing')

@pricing_bp.route('/')
@login_required
def index():
    key_id = os.getenv('RAZORPAY_KEY_ID', '')
    return render_template('pricing/index.html', key_id=key_id, current_plan=current_user.plan)

@pricing_bp.route('/create-order', methods=['POST'])
@login_required
def create_order():
    data = request.get_json()
    plan = data.get('plan')
    
    amount = 0
    if plan == 'basic':
        amount = 29900 # 299 INR in paise
    elif plan == 'pro':
        amount = 49900 # 499 INR in paise
    else:
        return jsonify({'error': 'Invalid plan'}), 400

    key_id = os.getenv('RAZORPAY_KEY_ID')
    key_secret = os.getenv('RAZORPAY_KEY_SECRET')
    
    if not key_id or not key_secret:
        return jsonify({'error': 'Razorpay credentials not configured'}), 500

    url = "https://api.razorpay.com/v1/orders"
    payload = {
        "amount": amount,
        "currency": "INR",
        "receipt": f"receipt_{current_user.id}_{plan}"
    }
    try:
        response = requests.post(url, json=payload, auth=HTTPBasicAuth(key_id, key_secret))
        order_data = response.json()
        if 'id' in order_data:
            return jsonify({'order_id': order_data['id'], 'amount': amount})
        return jsonify({'error': 'Failed to create order', 'details': order_data}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pricing_bp.route('/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    data = request.get_json()
    payment_id = data.get('razorpay_payment_id')
    order_id = data.get('razorpay_order_id')
    signature = data.get('razorpay_signature')
    plan = data.get('plan')

    key_secret = os.getenv('RAZORPAY_KEY_SECRET')

    # Verify signature
    msg = f"{order_id}|{payment_id}"
    generated_signature = hmac.new(
        key_secret.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()

    if generated_signature == signature:
        # Update user plan
        from models.user import User
        from bson import ObjectId
        try:
            User._db().users.update_one(
                {'_id': ObjectId(current_user.id)},
                {'$set': {'plan': plan}}
            )
            # update session current_user plan
            current_user.plan = plan
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    else:
        return jsonify({'success': False, 'error': 'Invalid signature'}), 400
