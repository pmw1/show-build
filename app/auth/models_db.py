"""
Database-backed authentication models for Show-Build
Replaces JSON file storage with proper database operations
"""
from datetime import datetime
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_user import User as DBUser, APIKey as DBAPIKey

# Create separate database connection to avoid import conflicts
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://showbuild:showbuild@localhost:5432/showbuild")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from passlib.context import CryptContext
import logging
import hashlib

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configure logging
logger = logging.getLogger(__name__)


class UserService:
    """Service class for user database operations"""
    
    @staticmethod
    def get_db() -> Session:
        """Get database session"""
        return SessionLocal()
    
    @classmethod
    def get_user(cls, username: str) -> Optional[DBUser]:
        """Get a user by username"""
        db = cls.get_db()
        try:
            user = db.query(DBUser).filter(DBUser.username == username).first()
            return user
        except Exception as e:
            logger.error(f"Error getting user {username}: {e}")
            return None
        finally:
            db.close()
    
    @classmethod
    def create_user(cls, username: str, password: str, **kwargs) -> Optional[DBUser]:
        """Create a new user"""
        db = cls.get_db()
        try:
            # Check if user already exists
            existing = db.query(DBUser).filter(DBUser.username == username).first()
            if existing:
                logger.warning(f"User {username} already exists")
                return None
            
            # Create new user
            hashed_password = pwd_context.hash(password)
            user = DBUser(
                username=username,
                hashed_password=hashed_password,
                access_level=kwargs.get('access_level', 'user'),
                first_name=kwargs.get('first_name', ''),
                last_name=kwargs.get('last_name', ''),
                email=kwargs.get('email', ''),
                phone=kwargs.get('phone', ''),
                profile_picture=kwargs.get('profile_picture', ''),
                is_active=kwargs.get('is_active', True),
                is_verified=kwargs.get('is_verified', False),
                settings=kwargs.get('settings', {})
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Created user: {username}")
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user {username}: {e}")
            return None
        finally:
            db.close()
    
    @classmethod
    def update_user(cls, username: str, **updates) -> Optional[DBUser]:
        """Update user information"""
        db = cls.get_db()
        try:
            user = db.query(DBUser).filter(DBUser.username == username).first()
            if not user:
                return None
            
            # Update fields
            for field, value in updates.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            logger.info(f"Updated user: {username}")
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user {username}: {e}")
            return None
        finally:
            db.close()
    
    @classmethod
    def list_users(cls) -> List[DBUser]:
        """Get all users"""
        db = cls.get_db()
        try:
            users = db.query(DBUser).all()
            return users
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
        finally:
            db.close()
    
    @classmethod
    def update_last_login(cls, username: str) -> None:
        """Update user's last login timestamp"""
        db = cls.get_db()
        try:
            user = db.query(DBUser).filter(DBUser.username == username).first()
            if user:
                user.last_login = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Error updating last login for {username}: {e}")
        finally:
            db.close()


class APIKeyService:
    """Service class for API key database operations"""
    
    @staticmethod
    def get_db() -> Session:
        """Get database session"""
        return SessionLocal()
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @classmethod
    def get_api_key(cls, api_key: str) -> Optional[DBAPIKey]:
        """Get API key by the actual key value"""
        db = cls.get_db()
        try:
            # For now, we're storing the actual key as key_hash (legacy)
            # In production, you'd hash the key and store the hash
            key_record = db.query(DBAPIKey).filter(
                DBAPIKey.key_hash == api_key,
                DBAPIKey.is_active == True
            ).first()
            
            if key_record:
                # Update last used timestamp
                key_record.last_used = datetime.utcnow()
                key_record.usage_count += 1
                db.commit()
            
            return key_record
            
        except Exception as e:
            logger.error(f"Error getting API key: {e}")
            return None
        finally:
            db.close()
    
    @classmethod
    def create_api_key(cls, api_key: str, client_name: str, created_by: str, 
                      access_level: str = "service") -> Optional[DBAPIKey]:
        """Create a new API key"""
        db = cls.get_db()
        try:
            # Create new API key record
            key_record = DBAPIKey(
                key_hash=api_key,  # Store actual key for now (legacy)
                key_prefix=api_key[:8],
                client_name=client_name,
                access_level=access_level,
                created_by_username=created_by,
                is_active=True,
                usage_count=0
            )
            
            db.add(key_record)
            db.commit()
            db.refresh(key_record)
            
            logger.info(f"Created API key for: {client_name}")
            return key_record
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating API key: {e}")
            return None
        finally:
            db.close()
    
    @classmethod
    def list_api_keys(cls) -> List[DBAPIKey]:
        """Get all API keys"""
        db = cls.get_db()
        try:
            keys = db.query(DBAPIKey).filter(DBAPIKey.is_active == True).all()
            return keys
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return []
        finally:
            db.close()
    
    @classmethod
    def deactivate_api_key(cls, api_key: str) -> bool:
        """Deactivate an API key"""
        db = cls.get_db()
        try:
            key_record = db.query(DBAPIKey).filter(DBAPIKey.key_hash == api_key).first()
            if key_record:
                key_record.is_active = False
                key_record.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"Deactivated API key: {api_key[:8]}...")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deactivating API key: {e}")
            return False
        finally:
            db.close()


# Legacy compatibility functions (to be removed)
def load_users() -> Dict[str, DBUser]:
    """Legacy function - load all users as dictionary"""
    users = UserService.list_users()
    return {user.username: user for user in users}


def get_user(username: str) -> Optional[DBUser]:
    """Legacy function - get user by username"""
    return UserService.get_user(username)


def load_api_keys() -> Dict[str, DBAPIKey]:
    """Legacy function - load all API keys as dictionary"""
    keys = APIKeyService.list_api_keys()
    return {key.key_hash: key for key in keys}


def save_users(users_dict: Dict[str, DBUser]) -> bool:
    """Legacy function - this is now a no-op since we use database"""
    logger.warning("save_users called - this is now handled by database automatically")
    return True


def save_api_keys(keys_dict: Dict[str, DBAPIKey]) -> bool:
    """Legacy function - this is now a no-op since we use database"""
    logger.warning("save_api_keys called - this is now handled by database automatically")
    return True