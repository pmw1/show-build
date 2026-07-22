"""
Capture inbox model.

Captures are content contributions sent from outside the main UI (the Chrome
capture extension today; a phone PWA share-target later). They are NOT
whiteboard items: the board save is a full delete-and-reinsert, so an external
client can never safely append a card directly. Instead a capture sits in this
inbox until the whiteboard UI drains it into a real card and acks it after a
successful board save (see docs/CAPTURE_INBOX_HANDOFF.md).
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class WhiteboardCapture(Base):
    __tablename__ = "whiteboard_captures"

    id = Column(Integer, primary_key=True, index=True)
    # 4-digit episode number. Deliberately no FK to whiteboards: a capture may
    # arrive before the board row exists (boards are created lazily on GET).
    episode_number = Column(String(4), nullable=False, index=True)
    # Client-supplied idempotency key (UUID) so offline retries never duplicate.
    client_capture_id = Column(String(64), unique=True, nullable=True)

    # What gesture produced this (drives server-side enrichment) and what
    # whiteboard node type it resolves to.
    capture_kind = Column(String(20), nullable=False)  # selection|link|image|video|page|screenshot
    item_type = Column(String(20), nullable=False)     # text|link|image|video|audio
    intended_cue_type = Column(String(10), nullable=True)  # sot|vo|nat

    # Content payload — mirrors WhiteboardItem columns so the whiteboard UI can
    # copy fields straight into a card.
    title = Column(String(200), nullable=True)
    text_content = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    caption = Column(Text, nullable=True)
    preview_title = Column(Text, nullable=True)
    preview_description = Column(Text, nullable=True)
    preview_image = Column(Text, nullable=True)
    preview_domain = Column(String(255), nullable=True)
    preview_favicon = Column(Text, nullable=True)
    social_metadata = Column(JSONB, nullable=True)  # tweet_data / content_data from download
    media_asset_id = Column(String(50), nullable=True, index=True)
    media_path = Column(Text, nullable=True)  # "whiteboard/{ep}/{file}" -> served at /pool/{media_path}
    mime_type = Column(String(100), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    media_metadata = Column(JSONB, nullable=True)
    extra_assets = Column(JSONB, nullable=True)  # secondary assets from multi-media posts

    # Lifecycle: processing -> pending -> placed | dismissed. 'failed' only when
    # there is no usable payload at all; enrichment failures degrade the row to
    # a pending link card with the failure recorded in `error`.
    status = Column(String(20), nullable=False, default="processing", index=True)
    error = Column(JSONB, nullable=True)
    # SOT/VO temp_job_id when typed processing was dispatched for this capture.
    processing_job_id = Column(String(50), nullable=True)
    source = Column(JSONB, nullable=True)  # {agent, version, hostname, page_url, page_title}

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True)
    placed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_wb_captures_ep_status", "episode_number", "status"),
    )
