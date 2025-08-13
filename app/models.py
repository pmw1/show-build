"""
SQLAlchemy models for Show-Build episode management system.
Server-heavy architecture storing rich metadata beyond markdown frontmatter.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from typing import Optional, Dict, Any
import enum

class EpisodeStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    READY = "ready"
    LIVE = "live"
    ARCHIVED = "archived"

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class CueType(str, enum.Enum):
    FSQ = "FSQ"  # Full Screen Quote
    SOT = "SOT"  # Sound on Tape (video)
    GFX = "GFX"  # Graphics

class EpisodeLegacy(Base):
    """Legacy episode metadata - to be migrated to new Episode model."""
    __tablename__ = "episodes_legacy"
    
    id = Column(Integer, primary_key=True, index=True)
    episode_number = Column(String(4), unique=True, index=True, nullable=False)  # "0225"
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255), nullable=True)
    airdate = Column(DateTime, nullable=True)
    status = Column(String(20), default=EpisodeStatus.DRAFT, nullable=False)
    duration = Column(String(10), nullable=True)  # "01:30:00"
    guest = Column(String(255), nullable=True)
    tags = Column(JSON, default=list, nullable=True)  # JSON array of tags
    slug = Column(String(100), nullable=True)
    
    # Server processing metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_compiled = Column(DateTime, nullable=True)
    last_quote_extraction = Column(DateTime, nullable=True)
    
    # File system paths (for Docker/development compatibility)
    episode_path = Column(String(500), nullable=False)  # Absolute path to episode directory
    
    # Relationships
    rundown_items = relationship("RundownItemLegacy", back_populates="episode", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="episode", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="episode", cascade="all, delete-orphan")
    
class RundownItemLegacy(Base):
    """Legacy rundown segments - to be migrated to new RundownItem model."""
    __tablename__ = "rundown_items_legacy"
    
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes_legacy.id"), nullable=False)
    
    # Basic metadata
    asset_id = Column(String(50), nullable=False, index=True)  # "12345"
    slug = Column(String(100), nullable=False, index=True)
    type = Column(String(20), nullable=False)  # segment, promo, advert, etc.
    order = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Timing and production
    duration = Column(String(10), nullable=True)  # "00:05:30"
    priority = Column(String(20), nullable=True)
    status = Column(String(20), default="draft", nullable=False)
    
    # Content storage (beyond simple markdown)
    script_content = Column(Text, nullable=True)  # Full script text
    notes = Column(Text, nullable=True)  # Production notes
    resources = Column(Text, nullable=True)  # Links, references
    guests = Column(String(255), nullable=True)
    tags = Column(JSON, default=list, nullable=True)
    
    # Server processing metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    file_path = Column(String(500), nullable=False)  # Path to source markdown file
    
    # Relationships
    episode = relationship("EpisodeLegacy", back_populates="rundown_items")
    cue_blocks = relationship("CueBlock", back_populates="rundown_item", cascade="all, delete-orphan")

class Asset(Base):
    """Episode assets with rich metadata for server management."""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes_legacy.id"), nullable=False)
    
    # Asset identification
    asset_id = Column(String(50), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    asset_type = Column(String(20), nullable=False)  # video, audio, graphics, quotes, etc.
    
    # File metadata
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Media metadata (for videos/images)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)  # Duration in seconds
    
    # Server processing metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed = Column(Boolean, default=False)
    meta_data = Column(JSON, default=dict, nullable=True)  # Flexible metadata storage
    
    # Relationships
    episode = relationship("EpisodeLegacy", back_populates="assets")

class CueBlock(Base):
    """Cue blocks with detailed metadata beyond markdown limitations."""
    __tablename__ = "cue_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    rundown_item_id = Column(Integer, ForeignKey("rundown_items_legacy.id"), nullable=False)
    
    # Cue identification
    asset_id = Column(String(50), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    cue_type = Column(String(10), nullable=False)  # FSQ, SOT, GFX
    order = Column(Integer, nullable=False)
    
    # Cue content
    quote_text = Column(Text, nullable=True)  # For FSQ blocks
    attribution = Column(String(255), nullable=True)  # For FSQ blocks
    media_url = Column(String(500), nullable=True)  # For GFX/SOT blocks
    transcription = Column(Text, nullable=True)  # For SOT blocks
    duration = Column(String(10), nullable=True)  # For SOT blocks
    
    # Server processing metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    validated = Column(Boolean, default=False)
    validation_errors = Column(JSON, default=list, nullable=True)
    
    # Rich metadata storage
    meta_data = Column(JSON, default=dict, nullable=True)  # Additional cue-specific data
    
    # Relationships
    rundown_item = relationship("RundownItemLegacy", back_populates="cue_blocks")

class ProcessingJob(Base):
    """Background processing jobs with server-side status tracking."""
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes_legacy.id"), nullable=False)
    
    # Job identification
    job_type = Column(String(50), nullable=False)  # script_compilation, quote_extraction, etc.
    job_id = Column(String(100), nullable=False, index=True)  # Celery task ID
    status = Column(String(20), default=ProcessingStatus.PENDING, nullable=False)
    
    # Job details
    parameters = Column(JSON, default=dict, nullable=True)  # Job input parameters
    result = Column(JSON, default=dict, nullable=True)  # Job output/results
    error_message = Column(Text, nullable=True)
    progress = Column(Integer, default=0, nullable=False)  # 0-100 percentage
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    episode = relationship("EpisodeLegacy", back_populates="processing_jobs")

class ExtractedQuote(Base):
    """Extracted quotes with rich metadata for server-side processing."""
    __tablename__ = "extracted_quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes_legacy.id"), nullable=False)
    
    # Quote identification
    quote_id = Column(String(50), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    
    # Quote content
    text = Column(Text, nullable=False)
    attribution = Column(String(255), nullable=True)
    context = Column(Text, nullable=True)  # Surrounding context
    
    # Processing metadata
    generated_image_path = Column(String(500), nullable=True)
    image_generated = Column(Boolean, default=False)
    word_count = Column(Integer, nullable=True)
    character_count = Column(Integer, nullable=True)
    
    # Server processing metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Source information
    source_file = Column(String(500), nullable=True)
    source_line = Column(Integer, nullable=True)


class Settings(Base):
    """Application and user settings storage."""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=False)
    category = Column(String(50), nullable=True)  # 'colors', 'interface', 'api', etc.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for global settings
    description = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships (User model is in models_user.py)
    # user = relationship("User", back_populates="settings")  # Commented out to avoid circular import