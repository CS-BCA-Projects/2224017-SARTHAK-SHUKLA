from flask import Blueprint, request, jsonify, session, flash, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import User
from forms import LoginForm, RegisterForm
from extensions import mongo  # ✅ Correct import from extensions.py

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        print(f'Attempting login for email: {email}')
        existing_user = mongo.db.users.find_one({'email': email})  # ✅ Corrected

        if existing_user:
            print(f'User found: {existing_user}')
            if check_password_hash(existing_user['password_hash'], password):  # ✅ Fix password field
                user = User(existing_user)  # ✅ Fix object creation
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))  # ✅ Fix redirection
            else:
                print('Password mismatch')
                flash('Invalid email or password', 'danger')
        else:
            print('User not found')
            flash('Invalid email or password', 'danger')
    else:
        print(f'Form validation failed. Errors: {form.errors}')  # ✅ Improved error logging
        flash(f'Login failed: {form.errors}', 'danger')

    return render_template('login.html', form=form)


@auth_bp.route('/auth/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/auth/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        password = generate_password_hash(form.password.data)
        
        existing_user = mongo.db.users.find_one({'email': email})
        if existing_user:
            flash('Email already registered', 'danger')
        else:
            mongo.db.users.insert_one({'email': email, 'password_hash': password})  # ✅ Fixed field name
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)
