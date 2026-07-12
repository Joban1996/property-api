from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Any

from models import UserSignup, UserLogin, Token, UserResponse
from crud import get_user_by_email, create_user, get_user_by_id
from auth import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user
)
from database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=Token)
async def signup(user_data: UserSignup, db=Depends(get_db)):
    """
    Register a new user.
    
    - Validates email format
    - Checks if email already exists
    - Validates password strength
    - Ensures passwords match
    - Returns JWT token upon success
    """
    
    # Check if email already registered
    db_user = get_user_by_email(user_data.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = create_user(email=user_data.email, password=user_data.password)
    print(type(new_user))
    print(new_user)
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """
    Login with email and password.
    
    - OAuth2 compatible (username field is used for email)
    - Validates credentials
    - Returns JWT token upon success
    """
    
    # Authenticate user
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_active_user)):
    """
    Get current user information.
    
    - Requires valid JWT token in Authorization header
    - Returns user details (excluding password)
    """

    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "created_at": current_user.get("created_at")
    }