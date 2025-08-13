"""
AssetID Registry Models - Track all AssetID generation and relationships
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class AssetIDRequestReason(str, enum.Enum):
    """Reasons for requesting an AssetID."""
    CREATE = "create"  # Creating new entity
    IMPORT = "import"  # Importing existing content
    DUPLICATE = "duplicate"  # Duplicating existing entity
    MIGRATION = "migration"  # Migrating from old system
    REPLACEMENT = "replacement"  # Replacing damaged/lost ID
    TEST = "test"  # Testing purposes


class AssetIDLinkType(str, enum.Enum):
    """Types of relationships between AssetIDs."""
    PARENT_CHILD = "parent_child"  # Hierarchical relationship
    DERIVED_FROM = "derived_from"  # Created from another asset
    REFERENCES = "references"  # References another asset
    REPLACES = "replaces"  # Replaces deprecated asset
    RELATED_TO = "related_to"  # General relationship
    CONTAINS = "contains"  # Container relationship
    BELONGS_TO = "belongs_to"  # Membership relationship
    DUPLICATE_OF = "duplicate_of"  # Duplicate content
    VERSION_OF = "version_of"  # Different version
    EXTRACTED_FROM = "extracted_from"  # Extracted segment/clip


class AssetIDRegistry(Base):
    """
    Master registry of all AssetIDs issued by the system.
    Tracks complete history and metadata for every ID.
    """
    __tablename__ = "asset_id_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # The AssetID itself
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Entity information
    entity_type = Column(String(50), nullable=False, index=True)  # segment, episode, etc.
    entity_table = Column(String(100), nullable=True)  # Database table name
    entity_id = Column(Integer, nullable=True)  # Primary key in entity table
    
    # Request metadata
    request_reason = Column(String(50), nullable=False)  # Why ID was requested
    request_context = Column(JSON, default=dict)  # Additional context about request
    requested_by = Column(String(255), nullable=True)  # User/system that requested
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Initial relationships (set at creation time)
    initial_links = Column(JSON, default=list)  # [{"asset_id": "...", "link_type": "..."}]
    
    # Status
    is_active = Column(String(20), default="active")  # active, deprecated, deleted
    
    # Additional metadata
    meta_data = Column(JSON, default=dict)  # Flexible metadata storage
    notes = Column(Text, nullable=True)  # Human-readable notes


class AssetIDRelationship(Base):
    """
    Tracks all relationships between AssetIDs.
    Separate from AssetLink to provide richer relationship tracking.
    """
    __tablename__ = "asset_id_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relationship
    source_asset_id = Column(String(50), nullable=False, index=True)
    target_asset_id = Column(String(50), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False, index=True)
    
    # Relationship metadata
    is_bidirectional = Column(String(5), default="false")  # Whether relationship goes both ways
    strength = Column(Integer, default=1)  # Relationship strength (1-10)
    
    # Context
    created_by = Column(String(255), nullable=True)  # User/system that created link
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    context = Column(JSON, default=dict)  # Additional context
    
    # Status
    is_active = Column(String(20), default="active")  # active, broken, deprecated
    
    # Notes
    notes = Column(Text, nullable=True)


class AssetIDPendingMessage(Base):
    """
    Messages that are pending for AssetIDs that don't exist yet.
    When the AssetID is created, these messages are delivered.
    """
    __tablename__ = "asset_id_pending_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Target AssetID (that doesn't exist yet)
    pending_asset_id = Column(String(50), nullable=False, index=True)
    
    # Message details
    message_type = Column(String(50), nullable=False)  # note, warning, production, instruction
    content = Column(Text, nullable=False)
    priority = Column(Integer, default=5)  # 1-10, higher is more important
    
    # Sender information
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Delivery status
    delivered = Column(String(5), default="false")
    delivered_at = Column(DateTime, nullable=True)
    
    # Expiration
    expires_at = Column(DateTime, nullable=True)  # Optional expiration date
    
    # Context
    context = Column(JSON, default=dict)  # Additional context about the message