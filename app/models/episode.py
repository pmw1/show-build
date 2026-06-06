"""
Episode, Break, Rundown, Region, and RundownItem models.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


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
    air_time = Column(String(50), nullable=True)  # Time of day for airing (HH:MM format)
    air_timezone = Column(String(50), nullable=True, default='America/New_York')  # Timezone for air time

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

    # --- Core Episode Description ---
    subtitle = Column(String(500), nullable=True)  # Short tagline
    description = Column(Text, nullable=True)  # Master description — root for all platform descriptions
    tags = Column(String(1000), nullable=True)  # Comma-separated tags/keywords
    notes = Column(Text, nullable=True)  # Internal production notes (not published)

    # --- Content Rating ---
    explicit = Column(Boolean, default=False, nullable=False)  # Explicit content flag (podcast RSS)
    content_warnings = Column(String(500), nullable=True)  # Free-text content warnings

    # --- Production Crew ---
    recording_date = Column(DateTime, nullable=True)  # When episode was recorded
    producer = Column(String(255), nullable=True)  # Producer name(s)
    editor = Column(String(255), nullable=True)  # Editor name(s)

    # --- Master Publishing Control ---
    publish_status = Column(String(20), default="draft")  # draft, scheduled, published, unpublished
    schedule_datetime = Column(DateTime(timezone=True), nullable=True)  # Master scheduled publish time
    visibility = Column(String(20), default="public")  # public, unlisted, private

    # --- OmnyStudio (Podcast Distribution) ---
    omny_description = Column(Text, nullable=True)  # Override description for podcast feeds (NULL = use master)
    omny_visibility = Column(String(20), default="public")  # public, unlisted, private
    omny_publish_status = Column(String(20), default="draft")  # draft, scheduled, published
    omny_schedule_datetime = Column(DateTime(timezone=True), nullable=True)  # Override schedule (NULL = use master)

    # --- YouTube ---
    yt_title = Column(String(100), nullable=True)  # Override title for YouTube (NULL = use episode title)
    yt_description = Column(Text, nullable=True)  # Override description for YouTube (NULL = use master)
    yt_tags = Column(String(500), nullable=True)  # YouTube-specific tags (comma-separated, 500 char limit)
    yt_privacy_status = Column(String(20), default="private")  # public, unlisted, private (default private for safety)
    yt_schedule_datetime = Column(DateTime(timezone=True), nullable=True)  # Override schedule (NULL = use master)

    # --- Social Media Promotion ---
    social_hashtags = Column(String(500), nullable=True)  # Hashtags shared across platforms
    twitter_post_text = Column(Text, nullable=True)  # Pre-composed tweet/thread text
    twitter_schedule_datetime = Column(DateTime(timezone=True), nullable=True)  # Override schedule (NULL = use master)
    instagram_caption = Column(Text, nullable=True)  # Instagram post/reel caption
    instagram_schedule_datetime = Column(DateTime(timezone=True), nullable=True)  # Override schedule (NULL = use master)
    facebook_post_text = Column(Text, nullable=True)  # Facebook post text
    facebook_schedule_datetime = Column(DateTime(timezone=True), nullable=True)  # Override schedule (NULL = use master)
    tiktok_caption = Column(Text, nullable=True)  # TikTok video caption
    tiktok_schedule_datetime = Column(DateTime(timezone=True), nullable=True)  # Override schedule (NULL = use master)

    # --- Auto-generation ---
    auto_generate_enabled = Column(Boolean, default=True, nullable=False, server_default="true")  # Kill switch for background description/tone sweeper

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

    # Block grouping for downstream consumers (showtime cue runner,
    # vmix-promoter filename grammar). Nullable: editor populates when
    # the segment belongs to a labeled block (A/B/C/D); unset for
    # interstitials and uncategorized items. See
    # docs/SHOWTIME_INTEGRATION_ANALYSIS.md Gap B.
    block_letter = Column(String(2), nullable=True)

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

    # --- Tone classification (LLM first-pass) ---
    tone = Column(String(32), nullable=True)  # e.g. 'sarcastic', 'serious' — from tone palette
    tone_rationale = Column(Text, nullable=True)  # One-sentence explanation from classifier
    tone_confidence = Column(Float, nullable=True)  # 0.0-1.0

    # --- Auto-generation bookkeeping ---
    llm_generated_fields = Column(JSON, nullable=True, default=list)  # ['description','tone',...] — drives purple highlight in sidebar
    auto_generate_attempts = Column(Integer, nullable=False, default=0, server_default="0")  # Bounded retries; reset on human edit
    description_gen_history = Column(JSON, nullable=True, default=list)  # [{role:'llm'|'user', text:str, ts:str}, ...] — full regen conversation
    auto_description_enabled = Column(Boolean, default=True, nullable=False, server_default="true")  # Per-segment opt-in/out for auto-description sweeper
    description_model = Column(String(100), nullable=True)  # LLM model name used to generate the description
    slug_gen_history = Column(JSON, nullable=True, default=list)  # [{role:'llm'|'user', text:str, ts:str}, ...] — LLM slug generation conversation

    # Relationships
    rundown = relationship("Rundown", back_populates="rundown_items")
    # region = relationship("Region", back_populates="rundown_items")  # DISABLED: regions calculated dynamically on frontend
    segment = relationship("Segment", back_populates="rundown_items")
    speaker = relationship("Speaker")
    content_versions = relationship("ContentVersion", back_populates="rundown_item", cascade="all, delete-orphan", order_by="ContentVersion.version_number.desc()")
