from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

load_dotenv()

# Get MongoDB URI from environment
mongodb_uri = os.getenv("MONGODB_URL")
database_name = os.getenv("DATABASE_NAME", "property_db")

if not mongodb_uri:
    raise ValueError("MONGODB_URL environment variable is not set")

# Connect to MongoDB
client = MongoClient(mongodb_uri, server_api=ServerApi(version='1'))

try:
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"❌ Connection failed: {e}")

# Use database
db = client[database_name]

# Collections
properties_collection = db["properties"]
expenses_collection = db["expenses"]
users_collection = db["users"]  # For authentication

# Function to get database
def get_db():
    return db