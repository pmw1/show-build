"""
Whiteboard Models
Database models for brainstorm whiteboard items and asset pool
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Boolean, BigInteger
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Whiteboard(Base):
    """Whiteboard workspace - can be linked to episode or standalone"""
    __tablename__ = "whiteboards"

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
    items = relationship("WhiteboardItem", back_populates="whiteboard", cascade="all, delete-orphan")


class WhiteboardItem(Base):
    """Individual items on the whiteboard (text, link, image)"""
    __tablename__ = "whiteboard_items"

    id = Column(Integer, primary_key=True, index=True)
    whiteboard_id = Column(Integer, ForeignKey("whiteboards.id", ondelete="CASCADE"), nullable=False)

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

    # Asset pool integration (new columns from migration)
    asset_id = Column(String(50), ForeignKey("asset_id_registry.asset_id", ondelete="SET NULL"), nullable=True)
    parent_item_id = Column(Integer, ForeignKey("whiteboard_items.id", ondelete="CASCADE"), nullable=True)
    is_child = Column(Boolean, default=False)

    # Additional media types (new columns)
    video_url = Column(Text, nullable=True)
    audio_url = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    html_content = Column(Text, nullable=True)
    code_content = Column(Text, nullable=True)
    code_language = Column(String(50), nullable=True)
    markdown_content = Column(Text, nullable=True)
    file_url = Column(Text, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    collapsed = Column(Boolean, default=False)

    # Relationships
    whiteboard = relationship("Whiteboard", back_populates="items")
    children = relationship("WhiteboardItem", backref="parent", remote_side=[id])


class AssetPoolFile(Base):
    """Files in the asset pool with AssetID tracking"""
    __tablename__ = "asset_pool_files"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), ForeignKey("asset_id_registry.asset_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    original_filename = Column(Text, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    thumbnail_path = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)  # 'whiteboard', 'manual_upload', 'twitter', 'youtube'
    source_url = Column(Text, nullable=True)
    source_context = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AssetTag(Base):
    """Tags for organizing asset pool"""
    __tablename__ = "asset_tags"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), ForeignKey("asset_id_registry.asset_id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String(100), nullable=False, index=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WhiteboardNodeLink(Base):
    """Visual connections between whiteboard nodes"""
    __tablename__ = "whiteboard_node_links"

    id = Column(Integer, primary_key=True, index=True)
    whiteboard_id = Column(Integer, ForeignKey("whiteboards.id", ondelete="CASCADE"), nullable=False)
    source_item_id = Column(Integer, ForeignKey("whiteboard_items.id", ondelete="CASCADE"), nullable=False, index=True)
    target_item_id = Column(Integer, ForeignKey("whiteboard_items.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=True)
    label = Column(Text, nullable=True)
    color = Column(String(20), default="#1976d2", nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
