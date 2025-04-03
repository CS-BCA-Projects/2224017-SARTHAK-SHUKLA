import os
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_mail import Mail  #  Import Flask-Mail
from models import User  #  

# Load environment variables
load_dotenv()

# Initialize Flask extensions
mongo = PyMongo()
login_manager = LoginManager()
mail = Mail()  #  Initialize Flask-Mail

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)  #  Load user from MongoDB

def init_db(app):
    raw_mongo_uri = os.getenv("MONGO_URI")

    if not raw_mongo_uri:
        raise ValueError(" MONGO_URI not found in environment variables! Check .env file.")

    print(f" Loaded MONGO_URI: {raw_mongo_uri}")  # Debugging

    #  Add connection timeout settings to prevent ServerSelectionTimeoutError
    app.config["MONGO_URI"] = raw_mongo_uri
    app.config["MONGO_CONNECT_TIMEOUT_MS"] = 60000  # 60 seconds timeout
    app.config["MONGO_SERVER_SELECTION_TIMEOUT_MS"] = 60000  # 60 seconds timeout
    
    mongo.init_app(app)

    if mongo.db is None:  #  Correct way to check initialization
        raise RuntimeError(" MongoDB initialization failed! Check if the database exists.")
    
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    #  Initialize Flask-Mail
    mail.init_app(app)
