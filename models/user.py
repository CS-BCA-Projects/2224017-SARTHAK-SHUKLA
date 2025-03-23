from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from extensions import mongo

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"]) if "_id" in user_data else None  # ✅ Fix: Handle missing _id
        self.email = user_data["email"]
        self.username = user_data["username"]
        self.password_hash = user_data.get("password_hash", "")

    @staticmethod
    def get_by_email(email):
        user_data = mongo.db.users.find_one({"email": email})
        return User(user_data) if user_data else None

    @staticmethod
    def get_by_id(user_id):
        try:
            user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            return User(user_data) if user_data else None
        except:
            return None

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def save_to_db(self):
        user_data = {
            "email": self.email,
            "username": self.username,
            "password_hash": self.password_hash
        }
        result = mongo.db.users.insert_one(user_data)  # ✅ Insert into MongoDB first
        self.id = str(result.inserted_id)  # ✅ Get the `_id` from the insertion result
