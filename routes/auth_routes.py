from flask import Blueprint, request, flash, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_mail import Message
from extensions import mongo, mail
from models import User
from forms import LoginForm, RegisterForm
import os

auth_bp = Blueprint('auth', __name__)

# Serializer for token generation
serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY"))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = generate_password_hash(form.password.data)

            existing_user = mongo.db.users.find_one({'email': email})
            if existing_user:
                flash('Email already registered', 'danger')
                return redirect(url_for('auth.register'))

            # ✅ Save user in MongoDB with `is_verified=False`
            mongo.db.users.insert_one({
                'email': email, 
                'password_hash': password, 
                'is_verified': False
            })

            # ✅ Send verification email
            token = serializer.dumps(email, salt='email-confirm')
            verify_url = url_for('auth.verify_email', token=token, _external=True)
            msg = Message('Verify Your Email', recipients=[email])
            msg.body = f'Click the link to verify your email: {verify_url}'

            try:
                mail.send(msg)
                print(f"Verification email sent to {email}")  # ✅ Debugging
                flash('Registration successful! A verification email has been sent.', 'success')
            except Exception as e:
                print(f"Error sending email: {e}")  # ✅ Debugging
                flash('Error sending verification email. Try again later.', 'danger')

            return redirect(url_for('auth.login'))  # ✅ Redirect only to login page
        else:
            print("Form validation failed.")  # ✅ Debugging
    
    return render_template('register.html', form=form)


@auth_bp.route('/verify/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)  # Token expires in 1 hour
        user = mongo.db.users.find_one({'email': email})

        if user and not user.get('is_verified', False):
            mongo.db.users.update_one({'email': email}, {'$set': {'is_verified': True}})
            flash('Email verified! You can now log in.', 'success')
        else:
            flash('Invalid or already verified email.', 'warning')
    except SignatureExpired:
        flash('Verification link expired. Please register again.', 'danger')
    except BadSignature:
        flash('Invalid verification link.', 'danger')

    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = mongo.db.users.find_one({'email': email})

        if user:
            if not user.get('is_verified', False):  # ✅ Ensure email is verified
                flash('Your email is not verified. Please check your inbox.', 'warning')
                return redirect(url_for('auth.login'))

            if check_password_hash(user['password_hash'], password):
                user_obj = User(user)  # ✅ Pass entire user dictionary to `User`
                login_user(user_obj)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect password. Please try again.', 'danger')
        else:
            flash('Email not found. Please register first.', 'danger')

    return render_template('login.html', form=form)
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
