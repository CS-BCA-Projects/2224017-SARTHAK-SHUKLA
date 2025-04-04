import os
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf import CSRFProtect
from models import User
from pymongo.errors import ServerSelectionTimeoutError  # ✅ Corrected import

# Load environment variables
load_dotenv()

# Initialize Flask extensions
mongo = PyMongo()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()  # ✅ CSRF protection for forms

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)  # Load user from MongoDB

def init_db(app):
    raw_mongo_uri = os.getenv("MONGO_URI")
    if not raw_mongo_uri:
        raise ValueError("MONGO_URI not found in environment variables! Check .env file.")
    
    print(f"Loaded MONGO_URI: {raw_mongo_uri}")

    # Database config with timeout handling
    app.config["MONGO_URI"] = raw_mongo_uri
    app.config["MONGO_CONNECT_TIMEOUT_MS"] = 60000
    app.config["MONGO_SERVER_SELECTION_TIMEOUT_MS"] = 60000

    # Init extensions
    try:
        mongo.init_app(app)
        if mongo.db is None:
            raise RuntimeError("MongoDB initialization failed! Check if the database exists.")
        
        # Check if the connection works by pinging the database
        mongo.db.command("ping")
        print("✅ MongoDB connection established successfully.")
    
    except ServerSelectionTimeoutError as e:  # ✅ Corrected error handling
        print(f"❌ MongoDB connection error: {e}")
        raise RuntimeError("Failed to connect to MongoDB. Please check your MongoDB URI and network connection.")

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    mail.init_app(app)
    csrf.init_app(app)  # ✅ Important for Flask-WTF CSRF protection
