import os
import urllib.parse
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from flask_login import LoginManager

load_dotenv()

mongo = PyMongo()
login_manager = LoginManager()

def init_db(app):
    raw_mongo_uri = os.getenv("MONGO_URI")

    if not raw_mongo_uri:
        raise ValueError("❌ MONGO_URI not found in environment variables! Check .env file.")

    print(f"✅ Loaded MONGO_URI: {raw_mongo_uri}")  # Debugging

    app.config["MONGO_URI"] = raw_mongo_uri
    mongo.init_app(app)

    if mongo.db is None:  # ✅ Correct way to check initialization
        raise RuntimeError("❌ MongoDB initialization failed! Check if the database exists.")
    
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
