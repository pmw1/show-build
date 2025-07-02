from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from .models import API_KEYS, load_api_keys
import logging

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings from environment
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# Add API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.info(f"Verifying password:")
    logger.info(f"  Plain password: '{plain_password}' (type: {type(plain_password)}, length: {len(plain_password)})")
    logger.info(f"  Hashed password: '{hashed_password}' (type: {type(hashed_password)}, length: {len(hashed_password)})")
    logger.info(f"  Hash starts with: {hashed_password[:10] if hashed_password else 'None'}")
    
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        logger.info(f"  Verification result: {result}")
        return result
    except Exception as e:
        logger.error(f"  Verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if not SECRET_KEY:
            raise HTTPException(
                status_code=500,
                detail="JWT_SECRET_KEY not configured"
            )
            
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        # For now, return basic user info
        # TODO: Replace with actual DB lookup
        return {
            "username": username,
            "access_level": "admin"  # Hardcoded for testing
        }
    except JWTError:
        raise credentials_exception

async def get_current_user_or_key(
    api_key: Optional[str] = Depends(api_key_header),
    token: Optional[str] = Depends(oauth2_scheme)
) -> dict:
    """Validates either API key or JWT token"""
    print("=== AUTHENTICATION DEBUG START ===")  # Use print for immediate output
    print(f"API Key received: {api_key[:8] + '...' if api_key else 'None'}")
    print(f"JWT Token received: {'Yes' if token else 'No'}")
    
    logger.info("=== AUTHENTICATION DEBUG START ===")
    logger.info(f"API Key received: {api_key[:8] if api_key else 'None'}...")
    logger.info(f"JWT Token received: {'Yes' if token else 'No'}")

    # Load keys from persistent storage
    api_keys = load_api_keys()
    print(f"Loaded {len(api_keys)} keys from storage")
    logger.info(f"Loaded {len(api_keys)} keys from storage")
    logger.info(f"Available key prefixes: {[k[:8] for k in api_keys.keys()]}")

    # Try API key authentication first
    if api_key:
        print(f"Checking API key: {api_key[:8]}...")
        logger.info(f"Checking API key: {api_key[:8]}...")
        if api_key in api_keys:
            print("✅ API key found and authenticated!")
            logger.info("✅ API key found and authenticated!")
            return {
                "username": api_keys[api_key].client_name,
                "access_level": api_keys[api_key].access_level
            }
        print(f"❌ API key {api_key[:8]}... not found in storage")
        logger.warning(f"❌ API key {api_key[:8]}... not found in storage")
        print(f"Available keys: {list(api_keys.keys())[:3]}")  # Show first 3 full keys for comparison
        logger.warning(f"Available keys: {list(api_keys.keys())[:3]}")  # Show first 3 full keys for comparison

    # Try JWT token if no API key worked
    if token:
        print("Attempting JWT authentication...")
        logger.info("Attempting JWT authentication...")
        try:
            return await get_current_user(token)
        except HTTPException:
            print("JWT authentication failed")
            logger.warning("JWT authentication failed")

    print("❌ No valid authentication provided")
    logger.error("❌ No valid authentication provided")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )