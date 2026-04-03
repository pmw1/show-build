"""
Segment, Script, Element, Cue, ContentVersion, and SegmentLock models.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from models.enums import RundownItemType, ElementType, CueType


class SegmentLock(Base):
    """Segment-level editing locks for concurrent editing protection."""
    __tablename__ = "segment_locks"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)

    # What is locked (by rundown item asset_id, not segment_id)
    rundown_item_asset_id = Column(String(50), ForeignKey("rundown_items.asset_id", ondelete="CASCADE"), nullable=False, index=True)

    # Who holds the lock
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Lock lifecycle
    locked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_heartbeat = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    rundown_item = relationship("RundownItem", backref="lock")
    user = relationship("User")


class ContentVersion(Base):
    """Version history for rundown item script content - prevents data loss."""
    __tablename__ = "content_versions"

    id = Column(Integer, primary_key=True, index=True)
    rundown_item_id = Column(Integer, ForeignKey("rundown_items.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(String(50), nullable=False, index=True)  # Denormalized for easier lookup

    # Version tracking
    version_number = Column(Integer, nullable=False)
    script_content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)  # SHA256 for deduplication
    content_length = Column(Integer, nullable=False)  # Quick reference without loading content

    # Change metadata
    change_type = Column(String(20), nullable=False)  # 'manual_save', 'autosave', 'api_update', 'restore'
    change_summary = Column(Text, nullable=True)  # Optional: what changed
    created_by = Column(String(100), nullable=True)  # Username who made the change

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    rundown_item = relationship("RundownItem", back_populates="content_versions")

    __table_args__ = (
        # Ensure version numbers are unique per rundown item
        # Index for fast "get latest version" queries
        {"schema": None}
    )


class Segment(Base):
    """The portable value unit - individually packageable and promotable content."""
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)

    # Current placement (nullable for portability)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=True)

    # Segment identification
    rundown_type = Column(Enum(RundownItemType), nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, index=True)
    order = Column(Integer, nullable=False)  # Order within block/episode

    # Rich metadata for promotion
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    thumbnail_url = Column(String(500), nullable=True)

    # Timing
    estimated_duration = Column(Integer, nullable=False)  # Pre-production estimate in seconds
    actual_duration = Column(Integer, nullable=True)  # Actual after production

    # Production markers
    in_point = Column(Float, nullable=True)  # Start time in episode timeline
    out_point = Column(Float, nullable=True)  # End time in episode timeline
    markers = Column(JSON, default=list)  # Production markers for auto-cutting

    # Publishing
    publishable = Column(Boolean, default=True)
    published_platforms = Column(JSON, default=dict)  # {"youtube": "url", "twitter": "url"}

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    episode = relationship("Episode", back_populates="segments")
    rundown_items = relationship("RundownItem", back_populates="segment")
    scripts = relationship("Script", back_populates="segment", cascade="all, delete-orphan")
    elements = relationship("Element", back_populates="segment", cascade="all, delete-orphan")
    cues = relationship("Cue", back_populates="segment", cascade="all, delete-orphan")


class Script(Base):
    """Role-specific script content for a segment."""
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)

    # Script type
    role = Column(String(50), nullable=False)  # "host", "director", "technical", "camera"

    # Content
    content = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    segment = relationship("Segment", back_populates="scripts")


class Element(Base):
    """Media assets used in production."""
    __tablename__ = "elements"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)

    # Element identification
    element_type = Column(Enum(ElementType), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)

    # File reference
    file_path = Column(String(500), nullable=True)
    file_url = Column(String(500), nullable=True)

    # Modifications
    modifications = Column(JSON, default=dict)  # {"trim_start": 5, "trim_end": 30, "crop": {...}}

    # Media metadata
    duration = Column(Float, nullable=True)  # Duration in seconds
    resolution = Column(String(50), nullable=True)  # "1920x1080"
    file_size = Column(Integer, nullable=True)  # Bytes

    # For quote elements
    quote_text = Column(Text, nullable=True)
    attribution = Column(String(255), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    segment = relationship("Segment", back_populates="elements")
    cues = relationship("Cue", back_populates="element")


class Cue(Base):
    """Production cues - timed calls for actions or media."""
    __tablename__ = "cues"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)
    element_id = Column(Integer, ForeignKey("elements.id"), nullable=True)  # Nullable for non-media cues

    # Cue identification
    cue_type = Column(Enum(CueType), nullable=False)
    name = Column(String(255), nullable=False)

    # Timing
    time_offset = Column(Float, nullable=False)  # Seconds from segment start
    duration = Column(Float, nullable=True)  # Duration if applicable

    # Cue-specific data
    parameters = Column(JSON, default=dict)  # {"camera": 2, "transition": "fade"}
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    segment = relationship("Segment", back_populates="cues")
    element = relationship("Element", back_populates="cues")
