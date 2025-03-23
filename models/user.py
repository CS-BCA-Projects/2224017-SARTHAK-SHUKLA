from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

def get_mongo():
    from extensions import mongo  # ✅ Import inside function to prevent circular import
    return mongo

class User(UserMixin):
    def __init__(self, user_data):
        if "_id" not in user_data:
            user_data["_id"] = ObjectId()
        
        self.id = str(user_data["_id"])
        self.email = user_data["email"]
        self.username = user_data.get("username", "Unknown")  # ✅ Prevent KeyError
        self.password_hash = user_data.get("password_hash", "")

    @staticmethod
    def get_by_email(email):
        user_data = get_mongo().db.users.find_one({"email": email})  # ✅ Fix circular import
        return User(user_data) if user_data else None

    @staticmethod
    def get_by_id(user_id):
        try:
            user_data = get_mongo().db.users.find_one({"_id": ObjectId(user_id)})  # ✅ Fix circular import
            return User(user_data) if user_data else None
        except:
            return None
