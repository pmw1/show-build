"""
Show-Build v2 Database Models - Segment-Centric Architecture
Episodes as flagship units, Segments as portable value units.
Every entity has an AssetID from central service.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float, Enum, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from typing import Optional
import enum


class RundownItemType(str, enum.Enum):
    """Types of items that can appear in a rundown."""
    SEGMENT = "segment"
    OPENING = "opening"
    TEASER = "teaser"
    ADVERTISEMENT = "advertisement"
    PROMO = "promo"
    INTERVIEW = "interview"
    PACKAGE = "package"
    TRANSITION = "transition"
    STINGER = "stinger"
    REJOIN = "rejoin"
    READER = "reader"
    CLOSE = "close"
    BREAK = "break"


class ElementType(str, enum.Enum):
    """Types of media elements."""
    VIDEO = "video"
    AUDIO = "audio"
    GRAPHIC = "graphic"
    ANIMATION = "animation"
    LOWER_THIRD = "lower_third"
    QUOTE = "quote"


class CueType(str, enum.Enum):
    """Types of production cues."""
    MEDIA = "media"  # Play media element
    CAMERA = "camera"  # Camera switch
    AUDIO_MIC = "audio_mic"  # Microphone control
    LIGHTING = "lighting"  # Lighting change
    DIRECTOR = "director"  # Director note
    TALENT = "talent"  # Talent instruction


class Organization(Base):
    """Comprehensive organization model with complete business information."""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Name fields
    name = Column(String(255), nullable=True)  # Display name or primary name
    legal_name = Column(String(255), nullable=False)  # Official legal name
    trade_name = Column(String(255), nullable=True)  # DBA, trade name, alias
    
    # Organization classification
    organization_type = Column(String(50), nullable=True)  # LLC, Corporation, Nonprofit, etc.
    industry = Column(String(100), nullable=True)  # Broadcasting, Technology, etc.
    sector = Column(String(100), nullable=True)  # Media, Healthcare, etc.
    
    # Identification
    registration_number = Column(String(100), nullable=True)  # Business registration number
    tax_id = Column(String(50), nullable=True)  # EIN, VAT number, etc.
    
    # Contact information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=False, default="United States")
    
    phone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Operational data
    founded_date = Column(DateTime(timezone=True), nullable=True)
    number_of_employees = Column(Integer, nullable=True)
    annual_revenue = Column(BigInteger, nullable=True)  # Store in cents for precision
    status = Column(String(20), nullable=False, default="active")  # active, inactive, suspended
    
    # System metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Legacy settings field (deprecated, use specific fields above)
    settings = Column(JSON, default=dict)
    
    # Relationships
    shows = relationship("Show", back_populates="organization", cascade="all, delete-orphan")


class Show(Base):
    """A show/program under an organization."""
    __tablename__ = "shows"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    settings = Column(JSON, default=dict)  # Show-specific settings
    
    # Relationships
    organization = relationship("Organization", back_populates="shows")
    seasons = relationship("Season", back_populates="show", cascade="all, delete-orphan")


class Season(Base):
    """Season/Series - flexible grouping of episodes."""
    __tablename__ = "seasons"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=False)
    
    # Flexible identification
    name = Column(String(255), nullable=False)  # "Series 1" or "Election 2024"
    number = Column(Integer, nullable=True)  # Optional enumeration
    slug = Column(String(100), nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    show = relationship("Show", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan")


class Episode(Base):
    """The flagship broadcast unit - organizes segments into a complete show."""
    __tablename__ = "episodes"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False)
    
    # Flexible identification
    episode_number = Column(Integer, nullable=True)  # Optional numbering
    title = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    
    # Scheduling
    publish_date = Column(DateTime, nullable=True)
    air_date = Column(DateTime, nullable=True)
    
    # Timing
    target_duration = Column(Integer, nullable=True)  # Target duration in seconds
    actual_duration = Column(Integer, nullable=True)  # Actual duration after production
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    status = Column(String(50), default="draft")  # draft, scheduled, live, archived
    
    # Relationships
    season = relationship("Season", back_populates="episodes")
    breaks = relationship("Break", back_populates="episode", cascade="all, delete-orphan")
    rundowns = relationship("Rundown", back_populates="episode", cascade="all, delete-orphan")
    segments = relationship("Segment", back_populates="episode")


class Break(Base):
    """Break periods between content blocks (commercials, news, station ID, etc.)."""
    __tablename__ = "breaks"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=False)
    
    # Break identification
    name = Column(String(50), nullable=False)  # "Break 1", "Break 2", "Cold Open Break"
    break_type = Column(String(50), default="commercial")  # commercial, news, station_id, technical, weather
    
    # Positioning
    order_in_episode = Column(Integer, nullable=False)  # 1, 2, 3...
    
    # Timing
    estimated_duration = Column(String(20), nullable=True)  # "00:02:30"
    actual_duration = Column(String(20), nullable=True)     # "00:02:45"
    
    # Content metadata
    description = Column(Text, nullable=True)
    sponsor = Column(String(255), nullable=True)  # For sponsored breaks
    
    # Status and workflow
    status = Column(String(50), default="scheduled")  # scheduled, live, completed, skipped
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    episode = relationship("Episode", back_populates="breaks")


class Rundown(Base):
    """Ordered sequence of rundown items within a block or episode."""
    __tablename__ = "rundowns"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Parent relationship 
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=False)
    
    # Rundown metadata
    name = Column(String(100), nullable=False)  # "Main Rundown", "Block A Rundown", etc.
    description = Column(Text, nullable=True)
    
    # Ordering and timing
    order_in_episode = Column(Integer, default=0)
    estimated_duration = Column(String(20), nullable=True)  # "00:15:30"
    
    # Status and workflow
    status = Column(String(50), default="draft")  # draft, approved, live, archived
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    episode = relationship("Episode", back_populates="rundowns") 
    rundown_items = relationship("RundownItem", back_populates="rundown")


class RundownItem(Base):
    """Individual items within a rundown (segments, promos, adverts, etc.)."""
    __tablename__ = "rundown_items" 
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Parent relationships
    rundown_id = Column(Integer, ForeignKey("rundowns.id"), nullable=False)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=True)  # Links to segment if this item represents one
    
    # Item metadata
    item_type = Column(String(50), nullable=False)  # segment, promo, advert
    title = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    
    # Timing and ordering
    order_in_rundown = Column(Integer, nullable=False)  # From "order" field
    duration = Column(String(20), nullable=True)  # "00:03:45" - from "duration" field
    
    # Segment-specific fields (nullable for other types)
    subtitle = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)  
    airdate = Column(DateTime, nullable=True)
    guests = Column(String(500), nullable=True)
    resources = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)
    server_message = Column(Text, nullable=True)
    
    # Promo/Advert fields (nullable for segments)
    link = Column(String(500), nullable=True)
    priority = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    
    # Status and workflow
    status = Column(String(50), default="draft")  # draft, ready, live, completed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    rundown = relationship("Rundown", back_populates="rundown_items")
    segment = relationship("Segment", back_populates="rundown_items")


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


class AssetLink(Base):
    """Links between AssetIDs for relationship tracking."""
    __tablename__ = "asset_links"
    
    id = Column(Integer, primary_key=True, index=True)
    source_asset_id = Column(String(50), nullable=False, index=True)
    target_asset_id = Column(String(50), nullable=False, index=True)
    link_type = Column(String(50), nullable=False)  # "references", "derived_from", "related_to"
    meta_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AssetMessage(Base):
    """Messages attached to AssetIDs."""
    __tablename__ = "asset_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), nullable=False, index=True)
    message_type = Column(String(50), nullable=False)  # "note", "warning", "production"
    content = Column(Text, nullable=False)
    user_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())