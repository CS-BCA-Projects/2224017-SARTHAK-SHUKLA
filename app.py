from flask import Flask, render_template
from flask_login import login_required, current_user
from extensions import mongo, login_manager, init_db
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

init_db(app)  # ✅ Ensure MongoDB is initialized before importing routes

@app.route("/")
def home():
    return render_template("intro.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user_resumes = mongo.db.resumes.find({"email": current_user.email})  # Fetch user's resumes
    return render_template("dashboard.html", user=current_user, resumes=user_resumes)  # ✅ Pass `resumes`

if __name__ == "__main__":
    #  Import routes only after app is initialized
    from routes.auth_routes import auth_bp
    from routes.resume_routes import resume_bp
    from routes.user_routes import User  #  Import User class

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(resume_bp, url_prefix="/resume")

    app.run(debug=True)
