"""
Show-Build v2 Database Models - Segment-Centric Architecture
Episodes as flagship units, Segments as portable value units.
Every entity has an AssetID from central service.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float, Enum, BigInteger
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from typing import Optional
import enum


class RundownItemType(str, enum.Enum):
    """Types of items that can appear in a rundown."""
    SEGMENT = "segment"
    OPEN = "open"
    COLDOPEN = "coldopen"
    TEASE = "tease"
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
    
    # Test data flag
    is_test_data = Column(Boolean, default=False, nullable=False)  # True for test organizations
    
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
    speakers = relationship("Speaker", back_populates="organization", cascade="all, delete-orphan")


class Show(Base):
    """A show/program under an organization."""
    __tablename__ = "shows"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Test data flag
    is_test_data = Column(Boolean, default=False, nullable=False)  # True for test shows
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
    speakers = relationship("Speaker", back_populates="show", cascade="all, delete-orphan")


class Speaker(Base):
    """Speaker model for managing show hosts, guests, and voice talent"""
    __tablename__ = "speakers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)

    # Speech metrics
    wpm = Column(Float, default=150.0, nullable=False)  # Words per minute
    wpm_min = Column(Float, default=130.0)  # Minimum comfortable WPM
    wpm_max = Column(Float, default=180.0)  # Maximum comfortable WPM

    # Speaker metadata
    role = Column(String, default="host")  # host, guest, narrator, voice_talent
    voice_type = Column(String)  # male, female, neutral
    language = Column(String, default="en")
    accent = Column(String)  # american, british, australian, etc.

    # AI/TTS integration
    xtts_speaker_name = Column(String)  # XTTS speaker ID for voice synthesis
    voice_sample_path = Column(String)  # Path to voice sample file

    # Status and metadata
    is_active = Column(Boolean, default=True)
    is_test_data = Column(Boolean, default=False)

    # Show/Organization relationship
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    show_id = Column(Integer, ForeignKey("shows.id"))
    user_id = Column(Integer, ForeignKey("users.id"))  # Link to logged-in user

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="speakers")
    show = relationship("Show", back_populates="speakers")
    user = relationship("User", back_populates="speaker_profile")

    def __repr__(self):
        return f"<Speaker(id={self.id}, name='{self.name}', wpm={self.wpm})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "wpm": self.wpm,
            "wpm_min": self.wpm_min,
            "wpm_max": self.wpm_max,
            "role": self.role,
            "voice_type": self.voice_type,
            "language": self.language,
            "accent": self.accent,
            "xtts_speaker_name": self.xtts_speaker_name,
            "voice_sample_path": self.voice_sample_path,
            "is_active": self.is_active,
            "organization_id": self.organization_id,
            "show_id": self.show_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


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
    
    # Test data flag
    is_test_data = Column(Boolean, default=False, nullable=False)  # True for test episodes
    # Dummy episode flag
    is_dummy = Column(Boolean, default=False, nullable=False)  # True for dummy/placeholder episodes
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

    # Guest information
    guest_name = Column(String(255), nullable=True)  # Primary guest name
    guest_bio = Column(Text, nullable=True)  # Guest biography/description
    guest_website = Column(String(500), nullable=True)  # Guest website URL

    # Template tracking (for episodes created from templates)
    template_type = Column(String(50), nullable=True)  # e.g., "sunday_show"
    template_id = Column(String(50), nullable=True)  # Reference to template used
    template_name = Column(String(100), nullable=True)  # Name of template used

    # Duration in original format (preserves "00:00:00" format from filesystem)
    duration_formatted = Column(String(10), nullable=True)  # "HH:MM:SS" format

    # Media - Poster images for different aspect ratios (promotional needs)
    poster_16x9 = Column(String(500), nullable=True)  # Widescreen (16:9) - YouTube, web, TV
    poster_1x1 = Column(String(500), nullable=True)   # Square (1:1) - Instagram feed, profile
    poster_9x16 = Column(String(500), nullable=True)  # Vertical (9:16) - Stories, TikTok, Reels
    poster_4x5 = Column(String(500), nullable=True)   # Portrait (4:5) - Facebook, Twitter cards

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
    regions = relationship("Region", back_populates="rundown")
    rundown_items = relationship("RundownItem", back_populates="rundown")


class Region(Base):
    """Organizational containers within rundowns (breaks, blocks, segments, etc.)."""
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)

    # Test data flag
    is_test_data = Column(Boolean, default=False, nullable=False)

    # Parent relationship
    rundown_id = Column(Integer, ForeignKey("rundowns.id"), nullable=False)

    # Region metadata
    region_type = Column(String(50), nullable=False)  # 'break', 'block', 'segment_group'
    name = Column(String(100), nullable=False)  # "Commercial Break 1", "Block A", etc.
    description = Column(Text, nullable=True)

    # Positioning and timing
    order_in_rundown = Column(Integer, nullable=False)  # Order within the rundown
    estimated_duration = Column(String(20), nullable=True)  # "00:05:30"
    actual_duration = Column(String(20), nullable=True)

    # Region behavior settings
    is_collapsible = Column(Boolean, default=True)  # Can be collapsed in UI
    is_collapsed = Column(Boolean, default=False)   # Current collapsed state
    allow_reorder = Column(Boolean, default=True)   # Allow items to be reordered within

    # Visual settings
    color_theme = Column(String(50), nullable=True)  # Theme color for UI display

    # Status and workflow
    status = Column(String(50), default="active")  # active, disabled, completed

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    rundown = relationship("Rundown", back_populates="regions")
    # rundown_items = relationship("RundownItem", back_populates="region")  # DISABLED: regions calculated dynamically on frontend


class RundownItem(Base):
    """Individual items within a rundown (segments, promos, adverts, etc.)."""
    __tablename__ = "rundown_items" 
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Test data flag
    is_test_data = Column(Boolean, default=False, nullable=False)  # True for test rundown items
    
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
    description = Column(Text, nullable=True)  # Metadata description only
    script_content = Column(Text, nullable=True)  # Actual script content (separate from description)
    airdate = Column(DateTime, nullable=True)
    guests = Column(String(500), nullable=True)
    resources = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)
    server_message = Column(Text, nullable=True)
    
    # Promo/Advert fields (nullable for segments)
    link = Column(String(500), nullable=True)
    priority = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)

    # Speaker assignment
    speaker_id = Column(Integer, ForeignKey("speakers.id"), nullable=True)

    # Status and workflow
    status = Column(String(50), default="draft")  # draft, ready, live, completed

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    rundown = relationship("Rundown", back_populates="rundown_items")
    # region = relationship("Region", back_populates="rundown_items")  # DISABLED: regions calculated dynamically on frontend
    segment = relationship("Segment", back_populates="rundown_items")
    speaker = relationship("Speaker")


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


class Settings(Base):
    """Application settings storage."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    category = Column(String(50), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SOTProcessingJob(Base):
    """Tracks multi-phase SOT video processing pipeline."""
    __tablename__ = "sot_processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    temp_job_id = Column(String(50), unique=True, nullable=False, index=True)
    episode = Column(String(10), nullable=True)
    slug = Column(String(255), nullable=True)
    asset_id = Column(String(50), nullable=True)  # AssetID for linking to cue block
    current_phase = Column(String(20), nullable=False, server_default='upload')
    status = Column(String(20), nullable=False, server_default='pending')
    job_type = Column(String(30), nullable=False, server_default='full_process')  # single_trim, individual_clips, montage, full_process
    clips_data = Column(Text, nullable=True)  # JSON string of clips array
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, server_default='0')
    celery_task_id = Column(String(50), nullable=True)
    working_directory = Column(Text, nullable=True)
    final_video_path = Column(Text, nullable=True)
    final_audio_path = Column(Text, nullable=True)
    final_thumbnail_path = Column(Text, nullable=True)

    # Enhanced processing metadata (added in migration 1013)
    thumbnail_candidates = Column(JSON, nullable=True)  # Array of thumbnail filenames for user selection
    selected_thumbnail = Column(String(255), nullable=True)  # User-selected thumbnail
    pre_analysis = Column(JSON, nullable=True)  # Technical analysis of uploaded raw file
    post_analysis = Column(JSON, nullable=True)  # Technical analysis of final processed file
    processing_report = Column(JSON, nullable=True)  # Comprehensive success/failure/warning report

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PromptOverride(Base):
    """LLM prompt overrides for customizing generation behavior."""
    __tablename__ = "prompt_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(50), nullable=False)  # generate, analyze, extract, refactor, compose, inventory
    operation_key = Column(String(100), nullable=False)  # e.g., generate-segment-script, inventory-batch-match-slots
    system_prompt = Column(Text, nullable=True)  # Override system prompt
    user_prompt_template = Column(Text, nullable=True)  # Override user prompt template with {{variable}} placeholders
    is_enabled = Column(Boolean, nullable=False, server_default='true')
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # Note: 'metadata' is reserved by SQLAlchemy Base but works in table with name='metadata' mapped to column
    prompt_metadata = Column('metadata', JSON, nullable=True)  # Maps to 'metadata' column in database
    suggested_service = Column(String(50), nullable=True)
    suggested_model = Column(String(100), nullable=True)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)