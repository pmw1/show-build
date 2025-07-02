from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .utils import verify_password, create_access_token, get_current_user, get_password_hash
from .models import (
    load_users, 
    save_users,
    get_user,
    UserLogin, 
    Token, 
    User, 
    APIKey, 
    load_api_keys, 
    save_api_keys
)
from datetime import timedelta
from typing import List
from secrets import token_urlsafe
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Login attempt for username: {form_data.username}")
    
    user = get_user(form_data.username)
    if not user:
        logger.warning(f"User not found: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User found: {user.username}, checking password...")
    logger.info(f"Password provided: '{form_data.password}' (length: {len(form_data.password)})")
    logger.info(f"Stored hash: {user.hashed_password[:20]}...")
    
    password_valid = verify_password(form_data.password, user.hashed_password)
    logger.info(f"Password verification result: {password_valid}")
    
    if not password_valid:
        logger.warning(f"Password verification failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=2880)  # 48 hours
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "username": user.username,
            "access_level": user.access_level
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
@router.post("/users", response_model=User)
async def create_user(
    new_user: UserLogin,
    current_user: dict = Depends(get_current_user)
):
    if current_user["access_level"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create users"
        )
    users = load_users()
    if new_user.username in users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    user = User(
        username=new_user.username,
        hashed_password=get_password_hash(new_user.password),
        access_level="user"  # Default to regular user
    )
    users[user.username] = user
    save_users(users)
    
    return user

# Admin-only: List all users
@router.get("/users", response_model=List[User])
async def list_users(current_user: dict = Depends(get_current_user)):
    if current_user["access_level"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list users"
        )
    users = load_users()
    return list(users.values())

@router.post("/apikey", response_model=APIKey)
async def create_api_key(
    client_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a permanent API key for automated systems"""
    if current_user["access_level"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create API keys"
        )
    
    # Load existing keys
    api_keys = load_api_keys()
    
    # Generate secure random key
    api_key = token_urlsafe(32)
    
    # Create new key
    new_key = APIKey(
        key=api_key,
        client_name=client_name,
        access_level="service",
        created_by=current_user["username"]
    )
    
    # Add to keys and save
    api_keys[api_key] = new_key
    save_api_keys(api_keys)
    
    # Debug logging
    logger.info(f"Created API key for {client_name}")
    logger.info(f"Total keys in storage: {len(api_keys)}")
    
    return new_key

@router.get("/apikeys", response_model=List[APIKey])
async def list_api_keys(current_user: dict = Depends(get_current_user)):
    """List all API keys (admin only)"""
    if current_user["access_level"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list API keys"
        )
    api_keys = load_api_keys()
    return list(api_keys.values())

@router.get("/apikeys/debug", response_model=List[dict])
async def debug_api_keys(current_user: dict = Depends(get_current_user)):
    """Debug endpoint to list stored API keys (admin only)"""
    if current_user["access_level"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Load keys from persistent storage
    api_keys = load_api_keys()
    return [{"key": k, "client": v.client_name} for k, v in api_keys.items()]

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