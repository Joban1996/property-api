from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class UserDB(BaseModel):
    """MongoDB User Model"""
    id: Optional[str] = Field(default=None, alias="_id")
    email: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}