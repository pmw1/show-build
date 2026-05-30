"""Recording session storage — showtime writeback target.

Tables created in migration g016_recording_sessions. Showtime (vMix
show-control on Win11 VM) PUTs recording manifests after a session;
this module is where those land. See
`docs/SHOWTIME_INTEGRATION_ANALYSIS.md` for the full rationale.

Multiple sessions per episode are supported (rehearsals + retakes +
real take). Each session is append-only.
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Float, ForeignKey,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class RecordingSession(Base):
    __tablename__ = "recording_sessions"

    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(
        Integer,
        ForeignKey("episodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_uuid = Column(String(64), nullable=False, unique=True)
    session_kind = Column(String(32), nullable=False, default="live")
    status = Column(String(20), nullable=False, default="in_progress")
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))
    operator = Column(String(120))
    host_machine = Column(String(120))
    vmix_version = Column(String(60))
    showtime_version = Column(String(40))
    take_count = Column(Integer, nullable=False, default=0)
    total_duration_seconds = Column(Float)
    recording_root_path = Column(String(500))
    notes = Column(Text)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    takes = relationship(
        "RecordingTake",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "idx_recording_sessions_episode_started",
            "episode_id", "started_at",
        ),
    )


class RecordingTake(Base):
    __tablename__ = "recording_takes"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("recording_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rundown_item_id = Column(
        Integer,
        ForeignKey("rundown_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename = Column(String(255), nullable=False)
    category = Column(String(40))
    block_letter = Column(String(2))
    segment_number = Column(Integer)
    take_number = Column(Integer)
    pickup_number = Column(Integer)
    status = Column(String(30), nullable=False, default="pending_review")
    started_at_wallclock = Column(DateTime(timezone=True), nullable=False)
    ended_at_wallclock = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)
    disk_band = Column(String(20))
    pickup_replaces_from_seconds = Column(Float)
    pickup_back_seconds = Column(Integer)
    pickup_splices_into_filename = Column(String(255))
    operator_note = Column(Text)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session = relationship("RecordingSession", back_populates="takes")
    markers = relationship(
        "TakeMarker",
        back_populates="take",
        cascade="all, delete-orphan",
    )
    cue_fires = relationship(
        "TakeCueFire",
        back_populates="take",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "session_id", "filename",
            name="uq_recording_takes_session_filename",
        ),
    )


class TakeMarker(Base):
    __tablename__ = "take_markers"

    id = Column(Integer, primary_key=True, index=True)
    take_id = Column(
        Integer,
        ForeignKey("recording_takes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind = Column(String(20), nullable=False)
    offset_seconds = Column(Float, nullable=False)
    wallclock = Column(DateTime(timezone=True), nullable=False)
    note = Column(Text)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    take = relationship("RecordingTake", back_populates="markers")


class TakeCueFire(Base):
    __tablename__ = "take_cue_fires"

    id = Column(Integer, primary_key=True, index=True)
    take_id = Column(
        Integer,
        ForeignKey("recording_takes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rundown_item_id = Column(
        Integer,
        ForeignKey("rundown_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cue_uuid = Column(String(64))
    cue_type = Column(String(40))
    cue_title = Column(String(255))
    trigger = Column(String(20))
    offset_seconds = Column(Float)
    fired_at_wallclock = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="fired")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    take = relationship("RecordingTake", back_populates="cue_fires")
