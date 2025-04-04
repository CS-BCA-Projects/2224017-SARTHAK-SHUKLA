from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

def get_mongo():
    from extensions import mongo
    return mongo

class User(UserMixin):
    def __init__(self, user_data):
        if "_id" not in user_data:
            user_data["_id"] = ObjectId()

        self.id = str(user_data["_id"])
        self.email = user_data["email"]
        self.username = user_data.get("username", "Unknown")
        self.password_hash = user_data.get("password_hash", "")
        self.is_verified = user_data.get("is_verified", False)

    @staticmethod
    def get_by_email(email):
        user_data = get_mongo().db.users.find_one({"email": email})
        return User(user_data) if user_data else None

    @staticmethod
    def get_by_id(user_id):
        try:
            user_data = get_mongo().db.users.find_one({"_id": ObjectId(user_id)})
            return User(user_data) if user_data else None
        except:
            return None

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
