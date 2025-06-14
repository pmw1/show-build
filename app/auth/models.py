from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Optional
from passlib.context import CryptContext
import json
from pathlib import Path
import logging

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define storage path relative to app directory
APP_DIR = Path(__file__).parent.parent  # Goes up from auth/ to app/
STORAGE_DIR = APP_DIR / "storage"
API_KEYS_FILE = STORAGE_DIR / "api_keys.json"

# Create storage directory if it doesn't exist
STORAGE_DIR.mkdir(exist_ok=True)

class User(BaseModel):
    username: str
    hashed_password: str
    access_level: str = "user"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

# Initialize with default admin user
USERS = {
    "admin": User(
        username="admin",
        hashed_password=pwd_context.hash("password123"),
        access_level="admin"
    )
}

class APIKey(BaseModel):
    key: str
    client_name: str
    access_level: str = "service"
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Initialize empty API_KEYS dictionary
API_KEYS: Dict[str, APIKey] = {}

def init_storage():
    """Initialize storage directory and file with valid JSON"""
    try:
        # Create storage directory
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create or validate API keys file
        if not API_KEYS_FILE.exists():
            # Initialize with empty JSON object
            API_KEYS_FILE.write_text("{}")
        else:
            # Validate existing JSON
            try:
                with API_KEYS_FILE.open("r") as f:
                    json.load(f)
            except json.JSONDecodeError:
                # Reset file if JSON is invalid
                API_KEYS_FILE.write_text("{}")
                
        return True
    except Exception as e:
        logging.error(f"Storage initialization failed: {str(e)}")
        return False

# Initialize storage when module loads
init_storage()

# Update load_api_keys with better error handling
def load_api_keys() -> Dict[str, APIKey]:
    """Load API keys from JSON file"""
    try:
        if not API_KEYS_FILE.exists():
            return {}
        with API_KEYS_FILE.open("r") as f:
            data = json.load(f)
            return {k: APIKey(**v) for k, v in data.items()}
    except Exception as e:
        logging.error(f"Failed to load API keys: {str(e)}")
        return {}

def save_api_keys(api_keys: Dict[str, APIKey]) -> bool:
    """Save API keys to JSON file"""
    try:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        
        serializable = {}
        for k, v in api_keys.items():
            serializable[k] = v.dict()
            if isinstance(serializable[k].get('created_at'), datetime):
                serializable[k]['created_at'] = serializable[k]['created_at'].isoformat()
        
        with API_KEYS_FILE.open("w") as f:
            json.dump(serializable, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Failed to save API keys: {str(e)}")
        return False