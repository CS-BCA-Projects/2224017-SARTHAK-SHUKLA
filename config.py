import os
from dotenv import load_dotenv
from flask_mail import Mail
import google.generativeai as genai

# Load environment variables
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "46e34af016958ae561720ababb44906ec271d7df1e0f08bdd2f89cb37805f687") # ✅ Add this line
    WTF_CSRF_ENABLED = True  # ✅ Enable CSRF protection

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

# Initialize Flask-Mail
mail = Mail()

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
GEMINI_MODEL = "gemini-1.5-flash-002"
