from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, email, username, password_hash):
        self.email = email
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_user(email, mongo):
        user_data = mongo.db.users.find_one({"email": email})
        if user_data:
            return User(user_data["email"], user_data["username"], user_data["password_hash"])
        return None
