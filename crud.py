from models_db import UserDB
from auth import get_password_hash
from database import users_collection
from bson import ObjectId


def _to_user_db(user_doc: dict) -> UserDB:
    """Convert a raw MongoDB user document into a UserDB model"""
    user_doc = dict(user_doc)  # avoid mutating the original
    user_doc["_id"] = str(user_doc["_id"])
    return UserDB(**user_doc)


def get_user_by_email(email: str):
    user = users_collection.find_one({"email": email})
    if user:
        return _to_user_db(user)
    return None


def get_user_by_id(user_id: str):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        return _to_user_db(user)
    return None


def create_user(email: str, password: str):
    hashed_password = get_password_hash(password)
    user_data = {
        "email": email,
        "hashed_password": hashed_password
    }
    result = users_collection.insert_one(user_data)
    created_user = users_collection.find_one({"_id": result.inserted_id})
    return _to_user_db(created_user)


def get_all_users(skip: int = 0, limit: int = 100):
    users = list(users_collection.find().skip(skip).limit(limit))
    return [_to_user_db(user) for user in users]