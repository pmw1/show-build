"""
Voice Sample Router
Handles voice print recording, WPM calculation, and XTTS integration
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
from datetime import datetime
import logging

from database import get_db
from auth.utils import get_current_user
from models_speakers import Speaker
from models_user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/voice-samples",
    tags=["voice-samples"]
)

# Voice sample storage path
VOICE_SAMPLES_ROOT = os.getenv("VOICE_SAMPLES_ROOT", "/shared_media/voice_samples")


@router.post("/upload")
async def upload_voice_sample(
    audio_file: UploadFile = File(...),
    reading_text: str = Form(...),
    reading_duration_seconds: float = Form(...),
    word_count: int = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload voice sample with reading metrics

    Args:
        audio_file: Audio recording (WAV/MP3/OGG)
        reading_text: Text that was read
        reading_duration_seconds: Time taken to read
        word_count: Number of words in the text

    Returns:
        Speaker profile with calculated WPM
    """
    try:
        username = current_user.get("username")

        # Get user from database
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Calculate WPM: (words / seconds) * 60
        calculated_wpm = (word_count / reading_duration_seconds) * 60 if reading_duration_seconds > 0 else 150.0

        logger.info(f"Voice sample upload: {word_count} words in {reading_duration_seconds}s = {calculated_wpm:.1f} WPM")

        # Create user voice sample directory
        user_voice_dir = os.path.join(VOICE_SAMPLES_ROOT, f"user_{user.id}")
        os.makedirs(user_voice_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio_file.filename)[1] or ".wav"
        filename = f"sample_{timestamp}{file_extension}"
        file_path = os.path.join(user_voice_dir, filename)

        # Save audio file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        logger.info(f"Voice sample saved to: {file_path}")

        # Get or create speaker profile for this user
        speaker = user.speaker_profile
        if not speaker:
            # Create new speaker profile
            speaker = Speaker(
                name=f"{user.first_name} {user.last_name}".strip() or user.username,
                slug=f"{user.username}-voice",
                user_id=user.id,
                wpm=calculated_wpm,
                wpm_min=max(calculated_wpm * 0.85, 100),  # 85% of calculated
                wpm_max=min(calculated_wpm * 1.15, 250),  # 115% of calculated
                voice_sample_path=file_path,
                role="user",
                is_active=True
            )
            db.add(speaker)
        else:
            # Update existing speaker profile with new WPM and sample
            speaker.wpm = calculated_wpm
            speaker.wpm_min = max(calculated_wpm * 0.85, 100)
            speaker.wpm_max = min(calculated_wpm * 1.15, 250)
            speaker.voice_sample_path = file_path

        db.commit()
        db.refresh(speaker)

        return {
            "success": True,
            "message": "Voice sample uploaded successfully",
            "speaker": speaker.to_dict(),
            "calculated_wpm": round(calculated_wpm, 1),
            "file_path": file_path,
            "xtts_ready": False  # Will be true after XTTS processing
        }

    except Exception as e:
        logger.error(f"Error uploading voice sample: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-profile")
async def get_my_voice_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's speaker/voice profile"""
    try:
        username = current_user.get("username")
        user = db.query(User).filter(User.username == username).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        speaker = user.speaker_profile

        if not speaker:
            return {
                "has_profile": False,
                "message": "No voice profile found. Complete a voice recording to create one."
            }

        return {
            "has_profile": True,
            "speaker": speaker.to_dict()
        }

    except Exception as e:
        logger.error(f"Error fetching voice profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-xtts")
async def process_voice_for_xtts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Process user's voice sample through XTTS for voice cloning
    This creates a speaker embedding for TTS generation
    """
    try:
        username = current_user.get("username")
        user = db.query(User).filter(User.username == username).first()

        if not user or not user.speaker_profile:
            raise HTTPException(status_code=404, detail="No voice profile found")

        speaker = user.speaker_profile

        if not speaker.voice_sample_path or not os.path.exists(speaker.voice_sample_path):
            raise HTTPException(status_code=404, detail="No voice sample file found")

        # TODO: Integrate with XTTS service
        # This would send the voice sample to XTTS API
        # and receive back a speaker ID/embedding

        # For now, just set a placeholder speaker name
        speaker.xtts_speaker_name = f"{username}_voice_clone"
        db.commit()

        return {
            "success": True,
            "message": "Voice processed for XTTS (placeholder)",
            "xtts_speaker_name": speaker.xtts_speaker_name,
            "note": "XTTS integration pending"
        }

    except Exception as e:
        logger.error(f"Error processing XTTS: {e}")
        raise HTTPException(status_code=500, detail=str(e))
