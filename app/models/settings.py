"""
Settings, PromptOverride, and GfxXpostCue models.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


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


class GfxXpostCue(Base):
    """GFX-XPOST cue — a full-screen graphic of an X/Twitter post.

    Stores all structured metadata for an X post cue so it can be queried,
    rendered, and regenerated independently of the markdown script_content.
    The cue block in script_content is the editorial source of truth;
    this table is the structured mirror for tooling and rendering.
    """
    __tablename__ = "gfx_xpost_cues"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)

    # Episode + rundown item linkage
    episode_number = Column(String(20), nullable=False, index=True)
    rundown_item_id = Column(Integer, ForeignKey("rundown_items.id"), nullable=True)

    # Slug (unique per episode for filesystem naming)
    slug = Column(String(255), nullable=False)

    # ── Author fields ──
    xpost_name = Column(String(255), nullable=True)          # Display name (e.g. "John Smith")
    xpost_username = Column(String(255), nullable=True)       # @handle (without @)
    xpost_profile_photo = Column(Text, nullable=True)         # URL to avatar image
    xpost_verified = Column(Boolean, default=False)           # Blue check / verified badge
    xpost_bio = Column(Text, nullable=True)                   # Author bio text
    xpost_followers = Column(Integer, nullable=True)          # Follower count
    xpost_following = Column(Integer, nullable=True)          # Following count

    # ── Post content ──
    xpost_post_text = Column(Text, nullable=True)             # Full tweet text
    xpost_tweet_id = Column(String(50), nullable=True, index=True)  # Twitter tweet ID
    xpost_conversation_id = Column(String(50), nullable=True) # Thread conversation ID

    # ── Media ──
    xpost_media_urls = Column(JSON, nullable=True)            # Array of media URLs (images/video)
    xpost_media_objects = Column(JSON, nullable=True)         # Structured media objects [{type, url, width, height}]
    xpost_media_local_paths = Column(JSON, nullable=True)     # Local filesystem paths for downloaded media

    # ── Timing ──
    xpost_datetime = Column(DateTime(timezone=True), nullable=True)  # When the post was published

    # ── Engagement metrics ──
    xpost_view_count = Column(Integer, nullable=True)         # Impressions / views
    xpost_likes = Column(Integer, nullable=True)
    xpost_retweets = Column(Integer, nullable=True)
    xpost_replies = Column(Integer, nullable=True)
    xpost_quotes = Column(Integer, nullable=True)
    xpost_bookmarks = Column(Integer, nullable=True)

    # ── Source ──
    xpost_source_url = Column(Text, nullable=True)            # Original tweet URL
    xpost_platform = Column(String(20), default='x')          # Always 'x' for now

    # ── Entities and referenced tweets (complex JSON) ──
    xpost_entities = Column(JSON, nullable=True)              # Hashtags, mentions, URLs from tweet
    xpost_referenced_tweets = Column(JSON, nullable=True)     # Quoted/replied tweet refs

    # ── Rendering ──
    aspect_ratio = Column(String(20), nullable=True)          # e.g. "16:9", "1:1"
    render_mode = Column(String(20), default='png')           # png or video
    generated_asset_path = Column(Text, nullable=True)        # Path to rendered PNG/video
    generated_asset_url = Column(Text, nullable=True)         # URL to rendered asset
    status = Column(String(20), default='pending')            # pending, generating, complete, failed
    duration = Column(String(20), default='00:00:15:00')      # Timecode duration
    enumerator = Column(String(10), nullable=True)            # Rundown cue number (e.g. "03")

    # ── Full archival metadata ──
    full_metadata = Column(JSON, nullable=True)               # Complete original API response for archival

    # ── Whiteboard origin (no FK constraint — whiteboard_items in separate model file) ──
    whiteboard_item_id = Column(Integer, nullable=True)

    # ── Timestamps ──
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    rundown_item = relationship("RundownItem", foreign_keys=[rundown_item_id])
