"""
Isolated database service for authentication
Avoids SQLAlchemy relationship conflicts by defining minimal models
"""
import os
from datetime import datetime
from typing import Dict, Optional, List
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from passlib.context import CryptContext
import logging
import hashlib

# Create isolated base and connection
Base = declarative_base()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://showbuild:showbuild@postgres:5432/showbuild")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)


class User(Base):
    """Isolated User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    access_level = Column(String(20), nullable=False, default="user")
    first_name = Column(String(100), nullable=True, default="")
    last_name = Column(String(100), nullable=True, default="")
    email = Column(String(255), nullable=True, default="")
    phone = Column(String(20), nullable=True, default="")
    profile_picture = Column(String(500), nullable=True, default="")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    settings = Column(JSON, default=dict)


class APIKey(Base):
    """Isolated API Key model for authentication"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(8), nullable=False, index=True)
    client_name = Column(String(100), nullable=False)
    access_level = Column(String(20), nullable=False, default="service")
    created_by_username = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)


class AuthService:
    """Authentication service using isolated database connection"""
    
    @staticmethod
    def get_db() -> Session:
        return SessionLocal()
    
    @classmethod
    def get_user(cls, username: str) -> Optional[dict]:
        """Get a user by username"""
        db = cls.get_db()
        try:
            user = db.query(User).filter(User.username == username).first()
            logger.info(f"Database query for user '{username}': {'Found' if user else 'Not found'}")
            
            if user:
                # Return dict to avoid session issues
                return {
                    "id": user.id,
                    "username": user.username,
                    "hashed_password": user.hashed_password,
                    "access_level": user.access_level,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "created_at": user.created_at,
                    "last_login": user.last_login
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user {username}: {e}")
            return None
        finally:
            db.close()
    
    @classmethod
    def get_api_key(cls, api_key: str) -> Optional[dict]:
        """Get API key by the actual key value"""
        db = cls.get_db()
        try:
            key_record = db.query(APIKey).filter(
                APIKey.key_hash == api_key,
                APIKey.is_active == True
            ).first()
            
            if key_record:
                # Update last used timestamp
                key_record.last_used = datetime.utcnow()
                key_record.usage_count += 1
                db.commit()
                logger.info(f"API key {api_key[:8]}... found and usage updated")
                
                # Return dict to avoid session issues
                return {
                    "client_name": key_record.client_name,
                    "access_level": key_record.access_level,
                    "created_by_username": key_record.created_by_username,
                    "is_active": key_record.is_active,
                    "usage_count": key_record.usage_count
                }
            else:
                logger.warning(f"API key {api_key[:8]}... not found")
                return None
            
        except Exception as e:
            logger.error(f"Error getting API key: {e}")
            return None
        finally:
            db.close()
    
    @classmethod
    def create_user(cls, username: str, password: str, **kwargs) -> Optional[User]:
        """Create a new user"""
        db = cls.get_db()
        try:
            # Check if user already exists
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                logger.warning(f"User {username} already exists")
                return None
            
            # Create new user
            hashed_password = pwd_context.hash(password)
            user = User(
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
    def create_api_key(cls, api_key: str, client_name: str, created_by: str, 
                      access_level: str = "service") -> Optional[APIKey]:
        """Create a new API key"""
        db = cls.get_db()
        try:
            key_record = APIKey(
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
    def list_users(cls) -> List[User]:
        """Get all users"""
        db = cls.get_db()
        try:
            users = db.query(User).all()
            return users
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
        finally:
            db.close()
    
    @classmethod
    def list_api_keys(cls) -> List[APIKey]:
        """Get all API keys"""
        db = cls.get_db()
        try:
            keys = db.query(APIKey).filter(APIKey.is_active == True).all()
            return keys
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return []
        finally:
            db.close()
    
    @classmethod
    def update_last_login(cls, username: str) -> None:
        """Update user's last login timestamp"""
        db = cls.get_db()
        try:
            user = db.query(User).filter(User.username == username).first()
            if user:
                user.last_login = datetime.utcnow()
                db.commit()
                logger.info(f"Updated last login for user: {username}")
        except Exception as e:
            logger.error(f"Error updating last login for {username}: {e}")
        finally:
            db.close()