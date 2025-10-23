from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from .utils import verify_password, create_access_token, get_current_user, get_current_user_or_key, get_password_hash
from .db_service import AuthService
from pydantic import BaseModel
from datetime import timedelta
from typing import List, Optional
from secrets import token_urlsafe
import logging
import os
import uuid
from pathlib import Path

# Pydantic models for API responses
class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    access_level: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
async def login_json(login_data: UserLogin):
    logger.info(f"JSON Login attempt for username: {login_data.username}")

    user = AuthService.get_user(login_data.username)
    if not user:
        logger.warning(f"User not found: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"User found: {user['username']}, checking password...")

    password_valid = verify_password(login_data.password, user['hashed_password'])
    logger.info(f"Password verification result: {password_valid}")

    if not password_valid:
        logger.warning(f"Password verification failed for user: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login timestamp
    AuthService.update_last_login(user['username'])

    access_token = create_access_token(
        data={"sub": user['username']},
        expires_delta=timedelta(minutes=2880)  # 48 hours
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "username": user['username'],
            "access_level": user['access_level']
        }
    )

@router.post("/login-form", response_model=Token)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Login attempt for username: {form_data.username}")
    
    user = AuthService.get_user(form_data.username)
    if not user:
        logger.warning(f"User not found: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User found: {user['username']}, checking password...")
    logger.info(f"Password provided: '{form_data.password}' (length: {len(form_data.password)})")
    logger.info(f"Stored hash: {user['hashed_password'][:20]}...")
    
    password_valid = verify_password(form_data.password, user['hashed_password'])
    logger.info(f"Password verification result: {password_valid}")
    
    if not password_valid:
        logger.warning(f"Password verification failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login timestamp
    AuthService.update_last_login(user['username'])

    access_token = create_access_token(
        data={"sub": user['username']},
        expires_delta=timedelta(minutes=2880)  # 48 hours
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "username": user['username'],
            "access_level": user['access_level']
        }
    )

@router.post("/upload-profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload profile picture for current user"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

    # Create profile pictures directory if it doesn't exist
    profile_pics_dir = Path("/home/profile_pictures")
    profile_pics_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{current_user['username']}_{uuid.uuid4()}.{file_extension}"
    file_path = profile_pics_dir / unique_filename

    # Save file
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        logger.error(f"Error saving profile picture: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save profile picture"
        )

    # Update user's profile_picture field in database
    profile_picture_url = f"/api/profile-pictures/{unique_filename}"
    user = AuthService.update_user(
        current_user["username"],
        profile_picture=profile_picture_url
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

    return {
        "success": True,
        "profile_picture": profile_picture_url,
        "message": "Profile picture uploaded successfully"
    }

@router.get("/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile information"""
    user = AuthService.get_user(current_user["username"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "id": user["id"],
        "username": user["username"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "email": user["email"],
        "phone": user["phone"],
        "profile_picture": user["profile_picture"],
        "access_level": user["access_level"],
        "is_active": user["is_active"]
    }

@router.get("/test-auth")
async def test_protected_route():
    return {"message": "You accessed a protected route"}

# Test auth endpoint
@router.get("/test")
async def test_auth():
    return {"message": "Auth module loaded successfully"}

# Admin-only: Create new user
@router.post("/users", response_model=dict)
async def create_user(
    new_user: UserLogin,
    current_user: dict = Depends(get_current_user_or_key)
):
    if current_user["access_level"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create users"
        )
    
    # Create new user
    user = AuthService.create_user(
        username=new_user.username,
        password=new_user.password,
        access_level="user"  # Default to regular user
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    return {
        "username": user.username,
        "access_level": user.access_level,
        "created_at": user.created_at.isoformat()
    }

# Admin-only: List all users
@router.get("/users", response_model=List[dict])
async def list_users(current_user: dict = Depends(get_current_user_or_key)):
    if current_user["access_level"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list users"
        )
    
    users = AuthService.list_users()
    return [
        {
            "username": user.username,
            "access_level": user.access_level,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        for user in users
    ]

@router.post("/apikey", response_model=dict)
async def create_api_key(
    client_name: str,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Create a permanent API key for automated systems"""
    if current_user["access_level"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create API keys"
        )
    
    # Generate secure random key
    api_key = token_urlsafe(32)
    
    # Create new key in database
    new_key = AuthService.create_api_key(
        api_key=api_key,
        client_name=client_name,
        created_by=current_user["username"],
        access_level="service"
    )
    
    if not new_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )
    
    # Debug logging
    logger.info(f"Created API key for {client_name}")
    
    return {
        "key": api_key,  # Return the actual key (only shown once)
        "client_name": new_key.client_name,
        "access_level": new_key.access_level,
        "created_by": new_key.created_by_username,
        "created_at": new_key.created_at.isoformat()
    }

@router.get("/apikeys", response_model=List[dict])
async def list_api_keys(current_user: dict = Depends(get_current_user_or_key)):
    """List all API keys (admin only)"""
    if current_user["access_level"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list API keys"
        )
    
    api_keys = AuthService.list_api_keys()
    return [
        {
            "key_prefix": key.key_prefix,
            "client_name": key.client_name,
            "access_level": key.access_level,
            "created_by": key.created_by_username,
            "created_at": key.created_at.isoformat() if key.created_at else None,
            "last_used": key.last_used.isoformat() if key.last_used else None,
            "usage_count": key.usage_count,
            "is_active": key.is_active
        }
        for key in api_keys
    ]

@router.get("/apikeys/debug", response_model=List[dict])
async def debug_api_keys(current_user: dict = Depends(get_current_user_or_key)):
    """Debug endpoint to list stored API keys (admin only)"""
    if current_user["access_level"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Load keys from database
    api_keys = AuthService.list_api_keys()
    return [{"key": key.key_hash, "client": key.client_name} for key in api_keys]

# Admin-only: Update user
@router.put("/users/{username}", response_model=dict)
async def update_user(
    username: str,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Update user information (admin only)"""
    if current_user["access_level"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update users"
        )

    # Build update dict from provided fields
    update_data = {}
    if user_update.first_name is not None:
        update_data['first_name'] = user_update.first_name
    if user_update.last_name is not None:
        update_data['last_name'] = user_update.last_name
    if user_update.email is not None:
        update_data['email'] = user_update.email
    if user_update.phone is not None:
        update_data['phone'] = user_update.phone
    if user_update.profile_picture is not None:
        update_data['profile_picture'] = user_update.profile_picture
    if user_update.access_level is not None:
        update_data['access_level'] = user_update.access_level
    if user_update.is_active is not None:
        update_data['is_active'] = user_update.is_active
    if user_update.password is not None:
        update_data['password'] = user_update.password

    user = AuthService.update_user(username, **update_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "access_level": user.access_level,
        "is_active": user.is_active,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }

# Admin-only: Delete user
@router.delete("/users/{username}", response_model=dict)
async def delete_user(
    username: str,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Delete user (admin only)"""
    if current_user["access_level"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete users"
        )

    # Prevent deleting yourself
    if username == current_user.get("username"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    success = AuthService.delete_user(username)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "success": True,
        "message": f"User '{username}' deleted successfully"
    }

# Debug endpoint for testing password hashing
@router.post("/debug/hash")
async def debug_hash_password(password: str):
    """Debug endpoint to generate and test password hashes"""
    from .utils import get_password_hash, verify_password
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Debug hash request for password: '{password}'")
    
    # Generate hash
    new_hash = get_password_hash(password)
    logger.info(f"Generated hash: {new_hash}")
    
    # Test verification
    verification_result = verify_password(password, new_hash)
    logger.info(f"Verification test: {verification_result}")
    
    return {
        "password": password,
        "hash": new_hash,
        "verification_test": verification_result,
        "hash_length": len(new_hash),
        "hash_prefix": new_hash[:10] if new_hash else None
    }