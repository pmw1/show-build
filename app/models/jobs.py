"""
CeleryJobLog and SOTProcessingJob models.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from database import Base


class CeleryJobLog(Base):
    """Lightweight log of all celery tasks dispatched from show-build."""
    __tablename__ = "celery_job_log"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    task_name = Column(String(255), nullable=False)  # e.g. services.ffmpeg_tasks.generate_episode_mp3
    display_name = Column(String(255), nullable=True)  # Human-friendly name e.g. "Generate MP3"
    category = Column(String(50), nullable=False, server_default='general')  # sot, tools, fsq, gfx, vo, compilation
    episode = Column(String(10), nullable=True)
    status = Column(String(20), nullable=False, server_default='pending')  # pending, running, completed, failed
    progress = Column(Integer, nullable=True)
    result_summary = Column(Text, nullable=True)  # Brief result or error message
    worker = Column(String(100), nullable=True)  # Which worker picked it up
    queue = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


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
    job_category = Column(String(20), nullable=False, server_default='sot')  # sot, vo - distinguishes SOT vs VO processing
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
    transcription = Column(Text, nullable=True)  # Whisper transcription from phase 0.5

    # Parent/child asset tracking (added 2025-10-26)
    source_asset_id = Column(String(50), nullable=True)  # Source (original upload) AssetID
    final_asset_id = Column(String(50), nullable=True)  # Final (processed) AssetID

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
