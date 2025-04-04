from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegisterForm(FlaskForm):
    username = StringField("🧑 Username", validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=30, message="Username must be between 3 and 30 characters")
    ])
    email = StringField("📧 Email", validators=[
        DataRequired(message="Email is required"),
        Email(message="Invalid email address")
    ])
    password = PasswordField("🔐 Password", validators=[
        DataRequired(message="Password is required"),
        Length(min=6, message="Password must be at least 6 characters long")
    ])
    confirm_password = PasswordField("🔁 Confirm Password", validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo("password", message="Passwords must match")
    ])
    submit = SubmitField("✅ Register")


class LoginForm(FlaskForm):
    email = StringField("📧 Email", validators=[
        DataRequired(message="Email is required"),
        Email(message="Invalid email address")
    ])
    password = PasswordField("🔐 Password", validators=[
        DataRequired(message="Password is required")
    ])
    submit = SubmitField("🔓 Login")


class OTPForm(FlaskForm):
    otp = StringField("🔑 Enter OTP", validators=[
        DataRequired(message="OTP is required"),
        Length(min=4, max=6, message="OTP must be between 4 to 6 digits")
    ])
    submit = SubmitField("🔍 Verify")
