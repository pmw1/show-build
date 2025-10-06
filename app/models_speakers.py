"""
Speaker Models
Manages speaker profiles including WPM (words per minute) for script timing
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


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
