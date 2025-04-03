from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import mongo

class User(UserMixin):
    def __init__(self, email, username, password_hash, is_verified=False):
        """
        Initializes the User object.

        :param email: User's email address
        :param username: User's username
        :param password_hash: Hashed password
        :param is_verified: Email verification status (default: False)
        """
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.is_verified = is_verified  # ✅ Added verification status

    def set_password(self, password):
        """
        Hashes and sets the user's password.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifies the provided password against the stored hash.
        """
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_user(email):
        """
        Fetches a user from MongoDB based on email.

        :param email: User's email address
        :return: User object if found, else None
        """
        user_data = mongo.db.users.find_one({"email": email})
        if user_data:
            return User(
                user_data["email"], 
                user_data.get("username", ""),  # Ensures no KeyError
                user_data["password_hash"], 
                user_data.get("is_verified", False)
            )
        return None
