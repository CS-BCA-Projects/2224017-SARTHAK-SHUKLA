from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import mongo, login_manager  # ✅ Import fixed login_manager
from forms import RegistrationForm, LoginForm
from models.user import User  # ✅ Correctly import User from models/user.py

auth_bp = Blueprint("auth", __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        users_collection = mongo.db.users
        existing_user = users_collection.find_one({"email": form.email.data})

        if existing_user:
            flash("Email already registered.", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(form.password.data)
        user = User({"email": form.email.data, "username": form.username.data, "password_hash": hashed_password})

        user.save_to_db()  # ✅ Ensure `_id` is assigned before using the user object

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "danger")

    print("❌ Login failed. Form errors:", form.errors)  # ✅ Debugging form errors
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
