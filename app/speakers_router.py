"""
Speakers Router
API endpoints for managing speaker profiles and WPM measurements
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
from auth.utils import get_current_user
from models_speakers import Speaker
from models_user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/speakers", tags=["Speakers"])


class SpeakerCreate(BaseModel):
    """Model for creating a speaker profile"""
    name: str
    slug: Optional[str] = None
    wpm: float
    wpm_min: Optional[float] = None
    wpm_max: Optional[float] = None
    role: str = "host"
    voice_type: Optional[str] = None
    language: str = "en"
    accent: Optional[str] = None
    xtts_speaker_name: Optional[str] = None
    organization_id: Optional[int] = None
    show_id: Optional[int] = None


class SpeakerUpdate(BaseModel):
    """Model for updating a speaker profile"""
    name: Optional[str] = None
    wpm: Optional[float] = None
    wpm_min: Optional[float] = None
    wpm_max: Optional[float] = None
    role: Optional[str] = None
    voice_type: Optional[str] = None
    language: Optional[str] = None
    accent: Optional[str] = None
    xtts_speaker_name: Optional[str] = None
    is_active: Optional[bool] = None


class WPMMeasurementCreate(BaseModel):
    """Model for creating WPM measurement for current user"""
    word_count: int
    elapsed_seconds: int
    script_text: Optional[str] = None


@router.get("/me")
async def get_my_speaker_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the speaker profile for the currently logged-in user"""
    try:
        speaker = db.query(Speaker).filter(Speaker.user_id == current_user.id).first()

        if not speaker:
            return {
                "success": False,
                "message": "No speaker profile found. Create one by measuring your WPM.",
                "data": None
            }

        return {
            "success": True,
            "data": speaker.to_dict()
        }
    except Exception as e:
        logger.error(f"Error fetching speaker profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch speaker profile")


@router.post("/me/measure-wpm")
async def measure_my_wpm(
    measurement: WPMMeasurementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update speaker profile for current user based on WPM measurement
    """
    try:
        # Calculate WPM
        minutes = measurement.elapsed_seconds / 60
        if minutes == 0:
            raise HTTPException(status_code=400, detail="Measurement time too short")

        calculated_wpm = round(measurement.word_count / minutes)
        wpm_min = max(100, round(calculated_wpm * 0.85))
        wpm_max = round(calculated_wpm * 1.15)

        # Check if user already has a speaker profile
        speaker = db.query(Speaker).filter(Speaker.user_id == current_user.id).first()

        if speaker:
            # Update existing profile
            speaker.wpm = calculated_wpm
            speaker.wpm_min = wpm_min
            speaker.wpm_max = wpm_max
            db.commit()
            db.refresh(speaker)

            return {
                "success": True,
                "message": "Speaker profile updated successfully",
                "data": speaker.to_dict()
            }
        else:
            # Create new speaker profile
            slug = current_user.username.lower().replace(' ', '-')

            new_speaker = Speaker(
                name=current_user.full_name or current_user.username,
                slug=slug,
                wpm=calculated_wpm,
                wpm_min=wpm_min,
                wpm_max=wpm_max,
                role="host",
                user_id=current_user.id,
                organization_id=current_user.organization_id
            )

            db.add(new_speaker)
            db.commit()
            db.refresh(new_speaker)

            return {
                "success": True,
                "message": "Speaker profile created successfully",
                "data": new_speaker.to_dict()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error measuring WPM: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save WPM measurement")


@router.get("/")
async def list_speakers(
    show_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    is_active: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all speakers, optionally filtered by show or organization"""
    try:
        query = db.query(Speaker).filter(Speaker.is_test_data == False)

        if is_active:
            query = query.filter(Speaker.is_active == True)

        if show_id:
            query = query.filter(Speaker.show_id == show_id)
        elif organization_id:
            query = query.filter(Speaker.organization_id == organization_id)
        else:
            # Default to user's organization (handle both dict and User object)
            user_org_id = current_user.get('organization_id') if isinstance(current_user, dict) else getattr(current_user, 'organization_id', None)
            if user_org_id:
                query = query.filter(Speaker.organization_id == user_org_id)

        speakers = query.all()

        return {
            "success": True,
            "data": [speaker.to_dict() for speaker in speakers],
            "count": len(speakers)
        }
    except Exception as e:
        logger.error(f"Error listing speakers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list speakers")


@router.post("/")
async def create_speaker(
    speaker_data: SpeakerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new speaker profile (admin only)"""
    try:
        # Generate slug if not provided
        if not speaker_data.slug:
            speaker_data.slug = speaker_data.name.lower().replace(' ', '-').replace('_', '-')

        # Check for duplicate slug
        existing = db.query(Speaker).filter(Speaker.slug == speaker_data.slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="Speaker with this slug already exists")

        new_speaker = Speaker(**speaker_data.dict())

        db.add(new_speaker)
        db.commit()
        db.refresh(new_speaker)

        return {
            "success": True,
            "message": "Speaker created successfully",
            "data": new_speaker.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating speaker: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create speaker")


@router.patch("/{speaker_id}")
async def update_speaker(
    speaker_id: int,
    speaker_data: SpeakerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a speaker profile"""
    try:
        speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()

        if not speaker:
            raise HTTPException(status_code=404, detail="Speaker not found")

        # Update only provided fields
        for key, value in speaker_data.dict(exclude_unset=True).items():
            setattr(speaker, key, value)

        db.commit()
        db.refresh(speaker)

        return {
            "success": True,
            "message": "Speaker updated successfully",
            "data": speaker.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating speaker: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update speaker")


@router.delete("/{speaker_id}")
async def delete_speaker(
    speaker_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a speaker profile (soft delete)"""
    try:
        speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()

        if not speaker:
            raise HTTPException(status_code=404, detail="Speaker not found")

        # Soft delete
        speaker.is_active = False
        db.commit()

        return {
            "success": True,
            "message": "Speaker deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting speaker: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete speaker")
