import os
from flask import Flask, render_template
from dotenv import load_dotenv
from flask_login import current_user, login_required

from extensions import mongo, login_manager, mail, csrf, init_db
from config import Config

# Load environment variables
load_dotenv()

# Initialize Flask App
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Extensions
init_db(app)

# Import Models for Flask-Login
from models import User

# Register Blueprints
from routes.auth_routes import auth_bp
from routes.resume_routes import resume_bp

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(resume_bp, url_prefix="/resume")

# Home Route
@app.route("/")
def home():
    return render_template("intro.html")

# Run App
if __name__ == "__main__":
    app.run(debug=True)
