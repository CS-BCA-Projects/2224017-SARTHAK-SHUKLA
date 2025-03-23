import os
from dotenv import load_dotenv

# ✅ Load environment variables from .env
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print("❌ .env file not found!")

# ✅ Print variables to check if they are loaded correctly
print("MONGO_URI:", os.getenv("MONGO_URI"))
print("MAIL_USERNAME:", os.getenv("MAIL_USERNAME"))
print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))
