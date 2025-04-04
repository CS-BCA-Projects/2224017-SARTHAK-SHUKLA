from flask import Blueprint, request, flash, redirect, url_for, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from flask_mail import Message
from extensions import mongo, mail
from models import User
from forms import LoginForm, RegisterForm
import random
import datetime
from forms import OTPForm

auth_bp = Blueprint('auth', __name__)

# 🔐 Helper: Generate and send OTP
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    msg = Message("🔐 Your OTP for Verification", recipients=[email])
    msg.body = f"Hello!\n\nYour OTP for email verification is: {otp}\n\nIt is valid for 10 minutes.\n\n🤖 Resume Analyzer"
    mail.send(msg)

# 📝 Register Route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password_hash = generate_password_hash(form.password.data)

        if mongo.db.users.find_one({"email": email}):
            flash("⚠️ Email already exists. Try logging in.", "warning")
            return redirect(url_for("auth.register"))

        otp = generate_otp()
        session["pending_user"] = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "otp": otp,
            "otp_sent_time": datetime.datetime.utcnow().isoformat()
        }

        try:
            send_otp_email(email, otp)
            flash("✅ OTP sent to your email!", "success")
        except:
            flash("❌ Failed to send OTP. Please try again.", "danger")

        return redirect(url_for("auth.verify_otp"))

    return render_template("register.html", form=form)

# 🔁 Resend OTP
@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    user = session.get("pending_user")
    if user:
        last_sent = datetime.datetime.fromisoformat(user["otp_sent_time"])
        now = datetime.datetime.utcnow()
        if (now - last_sent).total_seconds() < 60:
            flash("⏳ Please wait before resending the OTP.", "warning")
        else:
            new_otp = generate_otp()
            user["otp"] = new_otp
            user["otp_sent_time"] = now.isoformat()
            session["pending_user"] = user
            try:
                send_otp_email(user["email"], new_otp)
                flash("📩 OTP resent to your email.", "success")
            except:
                flash("❌ Could not resend OTP. Try again.", "danger")
    return redirect(url_for("auth.verify_otp"))

# ✅ OTP Verification
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    form = OTPForm()
    if form.validate_on_submit():
        entered_otp = form.otp.data
        user_data = session.get('pending_user')

        if not user_data:
            flash("⚠️ Session expired. Please register again.", "danger")
            return redirect(url_for("auth.register"))

        if entered_otp == user_data["otp"]:
            mongo.db.users.insert_one({
                "username": user_data["username"],
                "email": user_data["email"],
                "password_hash": user_data["password_hash"],
                "is_verified": True
            })
            session.pop("pending_user", None)
            flash("🎉 Registration complete! You can now log in.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("❌ Invalid OTP. Please try again.", "danger")

    return render_template("otp_verification.html", form=form)

# 🔐 Login Route
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = mongo.db.users.find_one({"email": email})

        if not user:
            flash("❌ No account found with this email.", "danger")
        elif not user.get("is_verified", False):
            flash("⚠️ Account not verified. Please register again.", "warning")
        elif not check_password_hash(user["password_hash"], password):
            flash("🔑 Incorrect password.", "danger")
        else:
            login_user(User(user))
            flash("✅ Login successful!", "success")
            return redirect(url_for("resume.dashboard"))

    return render_template("login.html", form=form)

# 🚪 Logout Route
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("👋 Logged out successfully.", "info")
    return redirect(url_for('auth.login'))
