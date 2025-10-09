"""
Voice Model Training Router
Weekly voice sample ingestion and progressive model building
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from auth.utils import get_current_user_or_key
from models_speakers import Speaker
import logging
import tempfile
import os
import shutil
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice-model", tags=["Voice Model Training"])


# Voice sample storage paths
VOICE_SAMPLES_ROOT = Path("/shared_media/voice_samples")
VOICE_MODELS_ROOT = Path("/shared_media/voice_models")


@router.post("/ingest-sample")
async def ingest_voice_sample(
    audio_file: UploadFile = File(...),
    speaker_id: int = Form(...),
    week_number: Optional[str] = Form(None),
    episode_number: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Ingest a voice sample for progressive model training

    Weekly workflow:
    1. Upload raw audio (dry recording, no music/effects)
    2. Transcribe with Whisper
    3. Extract clean voice segments (5-10 seconds each)
    4. Store with metadata (week, episode, transcript)
    5. Add to training dataset

    Over time, accumulate samples to build robust voice model
    """

    # Validate speaker exists
    speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")

    # Create speaker's sample directory
    speaker_dir = VOICE_SAMPLES_ROOT / speaker.slug
    speaker_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp and metadata
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    week_str = f"_week{week_number}" if week_number else ""
    episode_str = f"_ep{episode_number}" if episode_number else ""
    filename = f"{timestamp}{week_str}{episode_str}{Path(audio_file.filename).suffix}"

    sample_path = speaker_dir / filename

    try:
        # Save uploaded audio file
        with open(sample_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)

        logger.info(f"Saved voice sample for {speaker.name}: {sample_path}")

        # TODO: Transcribe audio (use Whisper from wpm_audio_router)
        # transcript = await transcribe_audio(str(sample_path))

        # TODO: Extract clean voice segments (5-10 sec chunks)
        # segments = await extract_voice_segments(str(sample_path))

        # TODO: Store metadata in database (new table: voice_samples)
        # - sample_id
        # - speaker_id
        # - file_path
        # - transcript
        # - duration
        # - week_number
        # - episode_number
        # - quality_score
        # - is_training_ready

        # For now, just return basic info
        file_size = os.path.getsize(sample_path)

        return {
            "success": True,
            "speaker": speaker.name,
            "sample_path": str(sample_path),
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "week": week_number,
            "episode": episode_number,
            "message": "Voice sample ingested. Transcription and segmentation pending."
        }

    except Exception as e:
        logger.error(f"Failed to ingest voice sample: {e}")
        # Clean up on error
        if sample_path.exists():
            sample_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to ingest sample: {str(e)}")


@router.get("/samples/{speaker_id}")
async def list_voice_samples(
    speaker_id: int,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    List all voice samples for a speaker
    Shows progressive collection over weeks/episodes
    """

    speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")

    speaker_dir = VOICE_SAMPLES_ROOT / speaker.slug

    if not speaker_dir.exists():
        return {
            "success": True,
            "speaker": speaker.name,
            "samples": [],
            "total_count": 0,
            "total_duration_minutes": 0,
            "training_ready": False
        }

    # List all audio files in speaker's directory
    samples = []
    total_size = 0

    for sample_file in speaker_dir.glob("*.*"):
        if sample_file.suffix.lower() in ['.mp3', '.wav', '.m4a', '.flac']:
            file_size = sample_file.stat().st_size
            total_size += file_size

            samples.append({
                "filename": sample_file.name,
                "path": str(sample_file),
                "size_mb": round(file_size / (1024 * 1024), 2),
                "created": sample_file.stat().st_ctime
            })

    # Sort by creation time (newest first)
    samples.sort(key=lambda x: x['created'], reverse=True)

    # Estimate if ready for training (need ~5 minutes minimum)
    # Rough estimate: 1 MB = ~1 minute of audio
    estimated_minutes = total_size / (1024 * 1024)
    training_ready = estimated_minutes >= 5

    return {
        "success": True,
        "speaker": speaker.name,
        "samples": samples,
        "total_count": len(samples),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "estimated_duration_minutes": round(estimated_minutes, 1),
        "training_ready": training_ready,
        "minimum_required_minutes": 5,
        "recommended_minutes": 30  # For high quality model
    }


@router.post("/train/{speaker_id}")
async def train_voice_model(
    speaker_id: int,
    model_name: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Train a voice model from collected samples

    Phase 1 (Now): Quick XTTS fine-tune with available samples
    Phase 2 (Future): Robust model training with accumulated weeks of data

    Training requirements:
    - Minimum: 5 minutes of clean audio
    - Recommended: 30+ minutes for quality
    - Optimal: 2+ hours for production-grade model
    """

    speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")

    # Check if enough samples exist
    speaker_dir = VOICE_SAMPLES_ROOT / speaker.slug
    if not speaker_dir.exists():
        raise HTTPException(
            status_code=400,
            detail="No voice samples found. Ingest samples first."
        )

    # Count samples
    sample_count = len(list(speaker_dir.glob("*.mp3")) +
                       list(speaker_dir.glob("*.wav")) +
                       list(speaker_dir.glob("*.m4a")))

    if sample_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No voice samples found. Ingest samples first."
        )

    # Create model directory
    model_dir = VOICE_MODELS_ROOT / speaker.slug
    model_dir.mkdir(parents=True, exist_ok=True)

    model_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_id = model_name or f"{speaker.slug}_{model_timestamp}"

    logger.info(f"Starting voice model training for {speaker.name} with {sample_count} samples")

    # TODO: Implement training pipeline
    # Phase 1 (Quick XTTS):
    #   1. Combine all samples into training manifest
    #   2. Call XTTS fine-tuning API
    #   3. Wait for training (minutes to hours)
    #   4. Save model checkpoint
    #
    # Phase 2 (Robust training):
    #   1. Extract mel spectrograms from all samples
    #   2. Train prosody model
    #   3. Train acoustic model
    #   4. Fine-tune with speaker embedding
    #   5. Generate quality metrics

    return {
        "success": True,
        "status": "training_queued",
        "speaker": speaker.name,
        "model_id": model_id,
        "sample_count": sample_count,
        "estimated_training_time_minutes": sample_count * 2,  # Rough estimate
        "message": "Voice model training queued. This feature is under development.",
        "next_steps": [
            "Training pipeline integration with XTTS",
            "Model quality evaluation",
            "A/B testing vs original voice"
        ]
    }


@router.get("/models/{speaker_id}")
async def list_voice_models(
    speaker_id: int,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    List all trained voice models for a speaker
    Shows progression over time as more samples are added
    """

    speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")

    model_dir = VOICE_MODELS_ROOT / speaker.slug

    if not model_dir.exists():
        return {
            "success": True,
            "speaker": speaker.name,
            "models": [],
            "total_count": 0
        }

    # List model checkpoints
    models = []
    for model_path in model_dir.glob("*"):
        if model_path.is_dir():
            models.append({
                "model_id": model_path.name,
                "path": str(model_path),
                "created": model_path.stat().st_ctime,
                "size_mb": sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file()) / (1024 * 1024)
            })

    models.sort(key=lambda x: x['created'], reverse=True)

    return {
        "success": True,
        "speaker": speaker.name,
        "models": models,
        "total_count": len(models)
    }


@router.delete("/sample/{speaker_id}/{filename}")
async def delete_voice_sample(
    speaker_id: int,
    filename: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Delete a voice sample (for quality control)
    """

    speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")

    sample_path = VOICE_SAMPLES_ROOT / speaker.slug / filename

    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample not found")

    try:
        sample_path.unlink()
        logger.info(f"Deleted voice sample: {sample_path}")

        return {
            "success": True,
            "message": f"Sample {filename} deleted"
        }
    except Exception as e:
        logger.error(f"Failed to delete sample: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete sample: {str(e)}")
