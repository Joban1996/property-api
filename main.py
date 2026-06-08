import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from bson import ObjectId
import certifi
from datetime import datetime

app = FastAPI(
    title="Property API",
    description="API for managing property listings with image upload",
    version="2.0.0"
)

# Create upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Load environment variables
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

# Use database and collections
db = client[database_name]
collection = db["properties"]
expenses_collection = db["expenses"]

# ✅ Response model for GET requests
class PropertyResponse(BaseModel):
    id: str
    title: str
    description: str
    price: str
    location: str
    image_url: str = ""

# ✅ Response model for POST requests
class PropertyCreateResponse(BaseModel):
    id: str
    image_url: str
    message: str = "Property created successfully"

# Expense Model
class Expense(BaseModel):
    title: str
    category: str
    subCategory: str
    amount: float
    date: str
    notes: Optional[str] = None
    vendorName: Optional[str] = None

def property_helper(property_doc) -> dict:
    return {
        "id": str(property_doc["_id"]),
        "title": property_doc["title"],
        "description": property_doc["description"],
        "price": str(property_doc["price"]), 
        "location": property_doc["location"],
        "image_url": property_doc.get("image_url", ""),
    }

@app.get("/")
def read_root():
    return {"message": "Property API is running with MongoDB Atlas!"}

@app.get("/properties", response_model=List[PropertyResponse])
def get_properties():
    properties = []
    for prop in collection.find():
        properties.append(property_helper(prop))
    return properties

@app.get("/properties/{property_id}", response_model=PropertyResponse)
def get_property(property_id: str):
    try:
        property_doc = collection.find_one({"_id": ObjectId(property_id)})
        if property_doc is None:
            raise HTTPException(status_code=404, detail="Property not found")
        return property_helper(property_doc)
    except:
        raise HTTPException(status_code=400, detail="Invalid property ID")

# POST Endpoint for properties
@app.post(
    "/properties",
    response_model=PropertyCreateResponse,
    summary="Create a new property",
    description="Upload a property image and submit property details. The image will be saved and a URL returned."
)
async def create_property(
    image: UploadFile = File(..., description="Property image file (JPEG, PNG, GIF, WEBP)"),
    title: str = Form(..., description="Property title (e.g., '2BHK Apartment')"),
    description: str = Form(..., description="Detailed property description"),
    price: str = Form(..., description="Price in Rupees (e.g., '4500000')"),
    location: str = Form(..., description="Property location (e.g., 'Sector 66, Mohali')"),
    type: str = Form(..., description="Property type (e.g., '2BHK', '3BHK')"),
    ownerName: Optional[str] = Form(None, description="Owner's name (optional)"),
    contact: Optional[str] = Form(None, description="Contact number (optional)"),
):
    try:
        # Validate image format
        file_extension = os.path.splitext(image.filename)[1].lower()
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported image format. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save image
        unique_filename = f"{ObjectId()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Generate image URL
        image_url = f"http://localhost:8000/uploads/{unique_filename}"
        
        # Create property document
        property_data = {
            "title": title,
            "description": description,
            "price": price,
            "location": location,
            "type": type,
            "image_url": image_url,
            "ownerName": ownerName,
            "contact": contact,
        }
        
        result = collection.insert_one(property_data)
        
        return PropertyCreateResponse(
            id=str(result.inserted_id),
            image_url=image_url,
            message="Property created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating property: {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# Expense management endpoints
@app.post("/expenses")
async def create_expense(expense: Expense):
    expense_dict = expense.dict()
    expense_dict["createdAt"] = datetime.now().isoformat()
    result = expenses_collection.insert_one(expense_dict)
    return {"success": True, "id": str(result.inserted_id)}

@app.get("/expenses")
async def get_all_expenses():
    expenses = []
    for exp in expenses_collection.find():
        exp["_id"] = str(exp["_id"])
        expenses.append(exp)
    return expenses

@app.get("/expenses/total")
async def get_total_expenses():
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    result = list(expenses_collection.aggregate(pipeline))
    total = result[0]["total"] if result else 0
    return {"total": total}

@app.put("/expenses/{expenseId}")
async def update_expense(expenseId: str, expense: Expense):
    try:
        expense_dict = expense.dict()
        
        result = expenses_collection.update_one(
            {"_id": ObjectId(expenseId)},
            {"$set": expense_dict}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        return {"success": True, "message": "Expense updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))