from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Optional
from passlib.context import CryptContext
import json
from pathlib import Path
import logging

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define storage paths relative to app directory
APP_DIR = Path(__file__).parent.parent  # Goes up from auth/ to app/
STORAGE_DIR = APP_DIR / "storage"
API_KEYS_FILE = STORAGE_DIR / "api_keys.json"
USERS_FILE = STORAGE_DIR / "users.json"

# Create storage directory if it doesn't exist
STORAGE_DIR.mkdir(exist_ok=True)

class User(BaseModel):
    username: str
    hashed_password: str
    access_level: str = "user"
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    profile_picture: str = ""

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

# Initialize empty USERS dictionary - will be loaded from JSON
USERS: Dict[str, User] = {}

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

def init_users():
    """Initialize users file with default users if it doesn't exist"""
    try:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        
        if not USERS_FILE.exists():
            # Create default users
            default_users = {
                "admin": User(
                    username="admin",
                    hashed_password=pwd_context.hash("password123"),
                    access_level="admin",
                    first_name="Admin",
                    last_name="User",
                    email="admin@showbuild.local",
                    phone="555-0000",
                    profile_picture="/static/avatars/admin.png"
                ),
                "kevin": User(
                    username="kevin",
                    hashed_password=pwd_context.hash("1234"),
                    access_level="admin",
                    first_name="Kevin",
                    last_name="Manager",
                    email="kevin@showbuild.local",
                    phone="555-0001",
                    profile_picture="/static/avatars/kevin.png"
                ),
                "josh": User(
                    username="josh",
                    hashed_password=pwd_context.hash("1234"),
                    access_level="user",
                    first_name="Josh",
                    last_name="Producer",
                    email="josh@showbuild.local",
                    phone="555-0002",
                    profile_picture="/static/avatars/josh.png"
                )
            }
            save_users(default_users)
        
        return True
    except Exception as e:
        logging.error(f"User initialization failed: {str(e)}")
        return False

def load_users() -> Dict[str, User]:
    """Load users from JSON file"""
    try:
        logging.info(f"Loading users from: {USERS_FILE}")
        if not USERS_FILE.exists():
            logging.warning(f"Users file does not exist: {USERS_FILE}")
            init_users()
        
        with USERS_FILE.open("r") as f:
            data = json.load(f)
            logging.info(f"Loaded {len(data)} users from file: {list(data.keys())}")
            users = {k: User(**v) for k, v in data.items()}
            
            # Log user details for debugging
            for username, user in users.items():
                logging.info(f"User {username}: hash={user.hashed_password[:20]}...")
            
            return users
    except Exception as e:
        logging.error(f"Failed to load users: {str(e)}")
        return {}

def save_users(users: Dict[str, User]) -> bool:
    """Save users to JSON file"""
    try:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        
        serializable = {}
        for k, v in users.items():
            serializable[k] = v.dict()
        
        with USERS_FILE.open("w") as f:
            json.dump(serializable, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Failed to save users: {str(e)}")
        return False

def get_user(username: str) -> Optional[User]:
    """Get a specific user by username"""
    users = load_users()
    return users.get(username)

# Initialize users when module loads
init_users()
USERS = load_users()