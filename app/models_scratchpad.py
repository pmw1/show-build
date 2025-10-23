"""
Scratchpad Models
Database models for brainstorm scratchpad items
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Scratchpad(Base):
    """Scratchpad workspace - can be linked to episode or standalone"""
    __tablename__ = "scratchpads"

    id = Column(Integer, primary_key=True, index=True)

    # Link to episode (optional)
    episode_number = Column(String(10), nullable=True, index=True)

    # Or standalone workspace with AssetID
    workspace_id = Column(String(50), nullable=True, index=True)

    # Metadata
    name = Column(String(200), nullable=True)  # Optional name for workspace
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    items = relationship("ScratchpadItem", back_populates="scratchpad", cascade="all, delete-orphan")


class ScratchpadItem(Base):
    """Individual items on the scratchpad (text, link, image)"""
    __tablename__ = "scratchpad_items"

    id = Column(Integer, primary_key=True, index=True)
    scratchpad_id = Column(Integer, ForeignKey("scratchpads.id", ondelete="CASCADE"), nullable=False)

    # Item type
    item_type = Column(String(20), nullable=False)  # 'text', 'link', 'image'

    # Custom title for card header
    title = Column(String(200), nullable=True)

    # Position on canvas
    x_position = Column(Float, nullable=False)
    y_position = Column(Float, nullable=False)

    # Content based on type
    text_content = Column(Text, nullable=True)  # For text cards
    url = Column(Text, nullable=True)  # For link cards
    notes = Column(Text, nullable=True)  # For link cards
    image_data = Column(Text, nullable=True)  # Base64 image data
    caption = Column(Text, nullable=True)  # For image cards

    # Link preview metadata (for link cards)
    preview_title = Column(Text, nullable=True)
    preview_description = Column(Text, nullable=True)
    preview_image = Column(Text, nullable=True)
    preview_domain = Column(String(255), nullable=True)
    preview_favicon = Column(Text, nullable=True)

    # Social media metadata (X/Twitter, Facebook, etc.) for rich recreation
    # Stores: author_handle, author_name, author_avatar, tweet_text,
    # published_time, media_urls, tweet_id, platform, etc.
    social_metadata = Column(JSON, nullable=True)

    # Dimensions
    width = Column(Integer, nullable=True)

    # Order/z-index
    z_index = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scratchpad = relationship("Scratchpad", back_populates="items")
