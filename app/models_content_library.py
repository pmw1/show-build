"""
Content Library Models - Reusable Content System
Enables ads, promos, CTAs, and other recurring content to appear in multiple rundowns.
Uses junction table pattern for many-to-many relationship between library items and rundowns.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class ContentLibrary(Base):
    """
    Master repository for reusable content (ads, promos, CTAs, etc.).
    Organization-wide scope - shared across all shows in the organization.
    Same asset_id appears in multiple rundowns via ContentPlacement junction table.
    """
    __tablename__ = "content_library"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)

    # Organization scope
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Content type (matches RundownItemType enum values)
    item_type = Column(String(50), nullable=False, index=True)  # advertisement, promo, cta, etc.

    # Core content fields
    title = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    script_content = Column(Text, nullable=True)  # Master script content
    scratch_content = Column(Text, nullable=True)  # Per-item scratch/notes (Reusables Studio)
    duration = Column(String(20), nullable=True)  # "00:00:30" format

    # Availability window
    valid_from = Column(DateTime(timezone=True), nullable=True)  # When this content becomes available
    valid_until = Column(DateTime(timezone=True), nullable=True)  # When this content expires

    # Advertiser/sponsor info (for ads)
    customer_name = Column(String(255), nullable=True)  # Sponsor or advertiser name
    customer_contact = Column(String(255), nullable=True)  # Contact email/phone

    # Priority and status
    priority = Column(String(50), default="normal")  # high, normal, low
    is_active = Column(Boolean, default=True, nullable=False)  # Soft delete flag

    # Extensible metadata (note: can't use 'metadata' - reserved by SQLAlchemy)
    extra_data = Column(JSON, nullable=True)  # Additional type-specific fields

    # Test data flag (matches other models)
    is_test_data = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    placements = relationship("ContentPlacement", back_populates="library_item", cascade="all, delete-orphan")


class ContentPlacement(Base):
    """
    Junction table linking library items to rundowns.
    Enables same content to appear in multiple rundowns.
    Also serves as permanent usage history (removed_at tracks removals).
    """
    __tablename__ = "content_placements"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    library_item_id = Column(Integer, ForeignKey("content_library.id"), nullable=False, index=True)
    rundown_id = Column(Integer, ForeignKey("rundowns.id"), nullable=False, index=True)
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=True, index=True)

    # Denormalized fields for fast queries
    episode_number = Column(String(20), nullable=True)  # "0100", "0101", etc.

    # Position in rundown
    order_in_rundown = Column(Integer, nullable=False)

    # Content snapshot - frozen at placement time (independent copies requirement)
    content_snapshot = Column(JSON, nullable=True)  # {title, script_content, duration, etc.}

    # Scheduling
    airdate = Column(DateTime(timezone=True), nullable=True)

    # Placement lifecycle
    placed_at = Column(DateTime(timezone=True), server_default=func.now())
    removed_at = Column(DateTime(timezone=True), nullable=True)  # NULL = active
    removed_before_air = Column(Boolean, nullable=True)  # TRUE if removed before airdate

    # Optional per-placement notes
    placement_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    library_item = relationship("ContentLibrary", back_populates="placements")
    rundown = relationship("Rundown")
    show = relationship("Show")


class ContentTypeSettings(Base):
    """
    Admin-configurable settings for each content type.
    Supports both Core Rundown Items (is_core=True) and Custom Rundown Items (is_core=False).
    Controls which types route to the library picker (is_reusable flag).
    """
    __tablename__ = "content_type_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Type identifier
    type_name = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "advertisement", "my_custom_type"

    # Display properties
    display_name = Column(String(100), nullable=False)  # "Advertisement", "My Custom Type"
    description = Column(Text, nullable=True)  # Description of what this type is for
    color = Column(String(20), nullable=True)  # Hex color or theme color name
    icon = Column(String(50), nullable=True)  # mdi-icon name

    # Core vs Custom flag - KEY FIELD
    is_core = Column(Boolean, default=False, nullable=False)  # True = Core Rundown Items, False = Custom Rundown Items

    # Reusability flag - Routes to library picker when TRUE
    is_reusable = Column(Boolean, default=False, nullable=False)

    # Default values for new items
    default_duration = Column(String(20), nullable=True)  # "00:00:30"

    # Ordering and status
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)

    # Organization scope (NULL = global defaults)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    organization = relationship("Organization")
