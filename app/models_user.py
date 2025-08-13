"""
User and Authentication Models for Show-Build Database
Integrates with existing auth system and provides migration path from JSON storage
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from typing import Optional
from datetime import datetime


class User(Base):
    """User authentication and profile model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    access_level = Column(String(20), nullable=False, default="user")  # user, admin, service
    
    # Profile fields
    first_name = Column(String(100), nullable=True, default="")
    last_name = Column(String(100), nullable=True, default="")
    email = Column(String(255), nullable=True, default="")
    phone = Column(String(20), nullable=True, default="")
    profile_picture = Column(String(500), nullable=True, default="")
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Organization relationship
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True)
    
    # Additional settings and preferences
    preferences = Column(JSON, default=dict)  # User-specific preferences (renamed from settings to avoid conflict)
    
    # Relationships (Settings model is in models.py)
    # settings = relationship("Settings", back_populates="user", cascade="all, delete-orphan")  # Commented out to avoid circular import
    
    def __repr__(self):
        return f"<User(username='{self.username}', access_level='{self.access_level}')>"


class APIKey(Base):
    """API Key model for service authentication"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Key identification
    key_hash = Column(String(255), unique=True, nullable=False, index=True)  # Store hash of key for security
    key_prefix = Column(String(8), nullable=False, index=True)  # First 8 chars for identification
    client_name = Column(String(100), nullable=False)
    
    # Permissions
    access_level = Column(String(20), nullable=False, default="service")  # service, admin
    
    # Relationship to user who created it
    created_by_username = Column(String(50), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiry
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<APIKey(client_name='{self.client_name}', prefix='{self.key_prefix}')>"


class UserSession(Base):
    """Track active user sessions"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Session identification
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), nullable=False, index=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Status
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<UserSession(username='{self.username}', active='{self.is_active}')>"