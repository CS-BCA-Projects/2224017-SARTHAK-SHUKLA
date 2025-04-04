import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env variables
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    WTF_CSRF_ENABLED = True

    # Flask-Mail configuration (do NOT hardcode sensitive data)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")  # From .env
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")  # From .env
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")  # From .env

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
GEMINI_MODEL = "gemini-1.5-flash-002"
