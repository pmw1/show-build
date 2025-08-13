"""
Minimal database models for rapid Show-Build coordination system.
ONLY what's needed to prevent processing conflicts and enable job queuing.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from database import Base

class Episode(Base):
    """Minimal episode tracking - just for coordination, not data storage."""
    __tablename__ = "episodes"
    
    id = Column(Integer, primary_key=True)
    episode_number = Column(String(4), unique=True, nullable=False)  # "0237"
    
    # Coordination metadata only
    is_processing = Column(Boolean, default=False)  # Lock for script compilation
    last_compiled = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProcessingJob(Base):
    """Background job tracking - essential for queue coordination."""
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True)
    episode_number = Column(String(4), nullable=False)
    
    # Job essentials
    job_type = Column(String(50), nullable=False)  # "script_compilation"
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    
    # Basic tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Results storage
    result = Column(JSON, nullable=True)

# That's it! No rundown items, assets, cues - just coordination essentials