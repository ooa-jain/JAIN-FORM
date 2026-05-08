from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
import os, requests as req

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        from models.user import User
        name  = request.form.get('name','').strip()
        email = request.form.get('email','').strip().lower()
        pw    = request.form.get('password','')
        if not name or not email or not pw:
            flash('All fields required.','error'); return render_template('auth/register.html')
        if len(pw) < 6:
            flash('Password must be 6+ characters.','error'); return render_template('auth/register.html')
        if User.get_by_email(email):
            flash('Email already registered.','error'); return render_template('auth/register.html')
        user = User.create(name, email, pw)
        login_user(user)
        return redirect(url_for('dashboard.index'))
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        from models.user import User
        email = request.form.get('email','').strip().lower()
        pw    = request.form.get('password','')
        user  = User.get_by_email(email)
        if user and user.check_password(pw):
            login_user(user, remember=True)
            return redirect(request.args.get('next') or url_for('dashboard.index'))
        flash('Invalid email or password.','error')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user(); return redirect(url_for('auth.login'))
