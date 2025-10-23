"""
Twitter OAuth Models
Database models for Twitter OAuth 2.0 tokens and user associations
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class TwitterOAuthToken(Base):
    """Twitter OAuth 2.0 access and refresh tokens for users"""
    __tablename__ = "twitter_oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # OAuth tokens
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String(50), nullable=False, default='Bearer')
    expires_at = Column(DateTime(timezone=True), nullable=True)
    scope = Column(Text, nullable=True)

    # Twitter user info
    twitter_user_id = Column(String(100), nullable=True)
    twitter_username = Column(String(100), nullable=True)
    twitter_name = Column(String(200), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
