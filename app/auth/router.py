from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .utils import verify_password, create_access_token, get_current_user, get_current_user_or_key, get_password_hash
from .db_service import AuthService
from pydantic import BaseModel
from datetime import timedelta
from typing import List
from secrets import token_urlsafe
import logging

# Pydantic models for API responses
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
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