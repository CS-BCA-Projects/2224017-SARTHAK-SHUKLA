import os
from dotenv import load_dotenv
from flask_mail import Mail
import google.generativeai as genai

# Load environment variables
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    WTF_CSRF_ENABLED = True # ✅ Enable CSRF protection 

    # Flask-Mail Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "abhinavpandey56393@gmail.com"  # Replace with your email
    MAIL_PASSWORD  = "dwcgjgyvhqlvqgri"  # Use an app password
    MAIL_DEFAULT_SENDER  = "abhinavpandey56393@gmail.com"


genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
GEMINI_MODEL = "gemini-1.5-flash-002"

mail = Mail()  # Initialize Flask-Mail
