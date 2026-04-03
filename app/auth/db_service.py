"""
Authentication database service.

Uses the shared database connection from database.py and models from models_user.py.
"""
from datetime import datetime
from typing import Optional, List
from database import SessionLocal
from models_user import User, APIKey
from passlib.context import CryptContext
import logging

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service using shared database connection"""

    @staticmethod
    def get_db():
        return SessionLocal()

    @classmethod
    def get_user(cls, username: str) -> Optional[dict]:
        """Get a user by username"""
        db = cls.get_db()
        try:
            user = db.query(User).filter(User.username == username).first()
            logger.info(f"Database query for user '{username}': {'Found' if user else 'Not found'}")

            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "hashed_password": user.hashed_password,
                    "access_level": user.access_level,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "phone": user.phone,
                    "profile_picture": user.profile_picture,
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
                key_record.last_used = datetime.utcnow()
                key_record.usage_count += 1
                db.commit()
                logger.info(f"API key {api_key[:8]}... found and usage updated")

                return {
                    "id": key_record.id,
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
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                logger.warning(f"User {username} already exists")
                return None

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
                preferences=kwargs.get('preferences', {}),
                organization_id=kwargs.get('organization_id', None),
                is_test_data=kwargs.get('is_test_data', False)
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
                key_hash=api_key,
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

    @classmethod
    def update_user(cls, username: str, **kwargs) -> Optional[User]:
        """Update user information"""
        db = cls.get_db()
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"User {username} not found for update")
                return None

            if 'first_name' in kwargs:
                user.first_name = kwargs['first_name']
            if 'last_name' in kwargs:
                user.last_name = kwargs['last_name']
            if 'email' in kwargs:
                user.email = kwargs['email']
            if 'phone' in kwargs:
                user.phone = kwargs['phone']
            if 'access_level' in kwargs:
                user.access_level = kwargs['access_level']
            if 'is_active' in kwargs:
                user.is_active = kwargs['is_active']
            if 'profile_picture' in kwargs:
                user.profile_picture = kwargs['profile_picture']
            if 'password' in kwargs:
                user.hashed_password = pwd_context.hash(kwargs['password'])

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
    def delete_user(cls, username: str) -> bool:
        """Delete a user"""
        db = cls.get_db()
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"User {username} not found for deletion")
                return False

            db.delete(user)
            db.commit()

            logger.info(f"Deleted user: {username}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting user {username}: {e}")
            return False
        finally:
            db.close()
