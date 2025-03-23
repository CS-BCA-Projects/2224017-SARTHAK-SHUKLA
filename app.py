from flask import Flask, render_template
from extensions import mongo, login_manager, init_db
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

init_db(app)  # ✅ Ensure MongoDB is initialized before importing routes

from routes.auth_routes import auth_bp
from routes.resume_routes import resume_bp

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(resume_bp, url_prefix="/resume")

@app.route("/")
def home():
    return render_template("intro.html")

if __name__ == "__main__":
    app.run(debug=True)
