"""
Segment LLM Data Models - Pre-extracted AI data for segments
Part of the LLM Preprocessing Layer for efficient downstream AI operations.

This module provides database models for storing "prechewed" LLM data extracted
from segment content. This extracted data (entities, summaries, quotes) can then
be efficiently reused for episode descriptions, social posts, and other AI tasks.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class SegmentLLMData(Base):
    """
    Stores pre-extracted LLM data per segment for efficient downstream operations.

    This is the core table for the LLM Preprocessing Layer. When a segment's content
    is analyzed by an LLM, the extracted entities, summaries, and quotes are stored
    here for reuse without re-analyzing the content.

    Multi-tier architecture:
    - Tier 1: Basic entity extraction (people, orgs, topics, quotes)
    - Tier 2: Derived analysis (sentiment, relationships) - stored in derived_data
    - Tier 3: Cross-segment intelligence (trends, similarity) - stored in derived_data
    """
    __tablename__ = "segment_llm_data"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)

    # Parent relationship - links to the segment via rundown_items
    # Note: We link to rundown_items because that's where script_content lives
    rundown_item_id = Column(Integer, ForeignKey("rundown_items.id", ondelete="CASCADE"), nullable=False, index=True)

    # ========== Tier 1: Core Extracted Data ==========

    # LLM-generated summaries
    llm_description = Column(Text, nullable=True)  # LLM-optimized description for AI context
    llm_summary = Column(Text, nullable=True)  # 1-2 sentence summary

    # Extracted entities - JSON arrays
    key_quotes = Column(JSON, default=list)  # ["Notable quote 1", "Notable quote 2"]
    extracted_people = Column(JSON, default=list)  # [{name, role, context}]
    extracted_organizations = Column(JSON, default=list)  # [{name, type, context}]
    extracted_institutions = Column(JSON, default=list)  # [{name, type}]
    extracted_topics = Column(JSON, default=list)  # ["topic1", "topic2"]

    # ========== Processing Metadata ==========

    # Content hash for stale detection
    source_content_hash = Column(String(64), nullable=True, index=True)  # SHA256 of source content

    # Extraction metadata
    extraction_model = Column(String(100), nullable=True)  # Model used (e.g., "claude-sonnet")
    extraction_timestamp = Column(DateTime(timezone=True), nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0.0-1.0 confidence
    token_count = Column(Integer, nullable=True)  # Approximate tokens processed

    # Processing status
    processing_status = Column(String(20), default="pending", index=True)
    # Values: pending, processing, completed, failed, stale

    # Multi-tier processing support
    processing_tier = Column(Integer, default=0, index=True)  # Highest completed tier (1, 2, 3...)

    # ========== Extensible Data Storage ==========

    # Tier 2+ derived analysis (schema-free for flexibility)
    derived_data = Column(JSON, default=dict)
    # Example structure:
    # {
    #   "tier_2": {"sentiment": {...}, "relationships": [...]},
    #   "tier_3": {"similar_segments": [...], "topic_cluster": "..."}
    # }

    # Per-tier processing metadata
    tier_metadata = Column(JSON, default=dict)
    # Example structure:
    # {
    #   "tier_1": {"model": "claude-sonnet", "timestamp": "...", "confidence": 0.92},
    #   "tier_2": {"model": "gpt-4o", "timestamp": "...", "depends_on_tier_1_hash": "abc123"}
    # }

    # Error tracking
    error_message = Column(Text, nullable=True)

    # ========== Review Workflow ==========

    # Human review support
    needs_review = Column(Boolean, default=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # ========== Standard Fields ==========

    # Test data flag
    is_test_data = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ========== Relationships ==========

    rundown_item = relationship("RundownItem", backref="llm_data")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<SegmentLLMData(id={self.id}, asset_id='{self.asset_id}', status='{self.processing_status}')>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "rundown_item_id": self.rundown_item_id,
            "llm_description": self.llm_description,
            "llm_summary": self.llm_summary,
            "key_quotes": self.key_quotes or [],
            "extracted_people": self.extracted_people or [],
            "extracted_organizations": self.extracted_organizations or [],
            "extracted_institutions": self.extracted_institutions or [],
            "extracted_topics": self.extracted_topics or [],
            "source_content_hash": self.source_content_hash,
            "extraction_model": self.extraction_model,
            "extraction_timestamp": self.extraction_timestamp.isoformat() if self.extraction_timestamp else None,
            "confidence_score": self.confidence_score,
            "token_count": self.token_count,
            "processing_status": self.processing_status,
            "processing_tier": self.processing_tier,
            "derived_data": self.derived_data or {},
            "tier_metadata": self.tier_metadata or {},
            "error_message": self.error_message,
            "needs_review": self.needs_review,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "is_test_data": self.is_test_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def is_stale(self, current_hash: str) -> bool:
        """Check if the extracted data is stale compared to current content."""
        if not self.source_content_hash:
            return True
        return self.source_content_hash != current_hash

    def get_all_entities(self) -> dict:
        """Get all extracted entities in a unified format."""
        return {
            "people": self.extracted_people or [],
            "organizations": self.extracted_organizations or [],
            "institutions": self.extracted_institutions or [],
            "topics": self.extracted_topics or [],
            "quotes": self.key_quotes or []
        }
