from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import os
import smtplib
from email.mime.text import MIMEText
import random
import secrets

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        from models.user import User
        email = request.form.get('email','').strip().lower()
        pw    = request.form.get('password','')
        
        if email and pw:
            user = User.get_by_email(email)
            if user:
                if user.check_password(pw):
                    login_user(user, remember=True)
                    return jsonify({'success': True, 'redirect': request.args.get('next') or url_for('dashboard.index')})
                else:
                    return jsonify({'success': False, 'message': 'Invalid password.'})
            else:
                return jsonify({'success': False, 'message': 'Account not found. Please flip to register.'})
                
        return jsonify({'success': False, 'message': 'Email and password required.'})
                
    return render_template('auth/login.html')

@auth_bp.route('/send_otp', methods=['POST'])
def send_otp():
    if current_user.is_authenticated: return jsonify({'success': False, 'message': 'Already logged in.'})
    from models.user import User
    email = request.form.get('email','').strip().lower()
    pw    = request.form.get('password','')
    
    if not email or len(pw) < 6:
        return jsonify({'success': False, 'message': 'Valid email and password (min 6 chars) required.'})
        
    if User.get_by_email(email):
        return jsonify({'success': False, 'message': 'Email already registered. Please login.'})
        
    otp = str(random.randint(100000, 999999))
    session['reg_email'] = email
    session['reg_pw'] = pw
    session['reg_otp'] = otp
    
    # Try sending email
    smtp_user = os.getenv('SMTP_USER') or os.getenv('EMAIL_USER', '')
    smtp_pass = os.getenv('SMTP_PASS') or os.getenv('EMAIL_PASS', '')
    smtp_host = os.getenv('SMTP_HOST') or os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT') or os.getenv('MAIL_PORT', 587))
    
    if smtp_user and smtp_pass:
        try:
            msg = MIMEText(f"Your Draftspace registration OTP is: {otp}")
            msg['Subject'] = "Draftspace Verification Code"
            msg['From'] = smtp_user
            msg['To'] = email
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Error sending OTP via email: {e}")
            # If email fails, we still allow them to proceed in dev environment, we'll log it
            print(f"DEV OTP for {email}: {otp}")
    else:
        # Fallback for dev without email config
        print(f"DEV OTP for {email}: {otp}")
        
    return jsonify({'success': True, 'message': 'OTP sent to email (check console if local)'})

@auth_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    if current_user.is_authenticated: return jsonify({'success': False, 'message': 'Already logged in.'})
    from models.user import User
    entered_otp = request.form.get('otp', '').strip()
    
    if 'reg_email' not in session or 'reg_otp' not in session:
        return jsonify({'success': False, 'message': 'Session expired. Please start over.'})
        
    if entered_otp == session['reg_otp']:
        email = session['reg_email']
        pw = session['reg_pw']
        name = email.split('@')[0]
        
        user = User.create(name, email, pw)
        login_user(user)
        
        session.pop('reg_email', None)
        session.pop('reg_pw', None)
        session.pop('reg_otp', None)
        
        return jsonify({'success': True, 'redirect': url_for('dashboard.index')})
    else:
        return jsonify({'success': False, 'message': 'Invalid OTP.'})

@auth_bp.route('/google_login', methods=['POST'])
def google_login():
    if current_user.is_authenticated: return jsonify({'success': False, 'message': 'Already logged in.'})
    
    from models.user import User
    
    email = request.form.get('email', '').strip().lower()
    name = request.form.get('name', '').strip()
    avatar = request.form.get('avatar', '').strip()
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required.'})
        
    user = User.get_by_email(email)
    
    if user:
        # User exists, log them in
        login_user(user, remember=True)
        return jsonify({'success': True, 'redirect': request.args.get('next') or url_for('dashboard.index')})
    else:
        # New user via Google
        if not name:
            name = email.split('@')[0]
            
        dummy_pw = secrets.token_hex(16)
        user = User.create(name=name, email=email, password=dummy_pw, auth_provider='google', avatar=avatar)
        login_user(user, remember=True)
        return jsonify({'success': True, 'redirect': url_for('dashboard.index')})

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

