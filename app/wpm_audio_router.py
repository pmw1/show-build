"""
WPM Audio Analysis Router
Upload MP3 audio to automatically calculate Words Per Minute (WPM) for speakers
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from auth.utils import get_current_user_or_key
from models_speakers import Speaker
from models_user import User
import logging
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wpm-audio", tags=["WPM Audio Analysis"])


@router.post("/analyze")
async def analyze_audio_wpm(
    audio_file: UploadFile = File(...),
    speaker_id: Optional[int] = Form(None),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Analyze an MP3 audio file to calculate WPM

    Process:
    1. Accept MP3 upload
    2. Transcribe audio using Whisper (via Ollama or local)
    3. Count words in transcript
    4. Calculate duration from audio file
    5. Calculate WPM = words / (duration_seconds / 60)
    6. Update speaker profile with new WPM measurement

    Returns:
        {
            "success": true,
            "wpm": 165,
            "word_count": 450,
            "duration_seconds": 163.5,
            "transcript": "Full transcript text...",
            "speaker_updated": true
        }
    """

    # Validate file is MP3
    if not audio_file.filename.endswith(('.mp3', '.wav', '.m4a')):
        raise HTTPException(
            status_code=400,
            detail="Only MP3, WAV, and M4A audio files are supported"
        )

    temp_audio_path = None

    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio_file.filename).suffix) as temp_file:
            temp_audio_path = temp_file.name
            content = await audio_file.read()
            temp_file.write(content)

        logger.info(f"Audio file saved to temporary path: {temp_audio_path}")

        # Step 1: Get audio duration
        duration_seconds = await get_audio_duration(temp_audio_path)
        logger.info(f"Audio duration: {duration_seconds} seconds")

        # Step 2: Transcribe audio
        transcript = await transcribe_audio(temp_audio_path)
        logger.info(f"Transcription complete: {len(transcript)} characters")

        # Step 3: Count words
        word_count = count_words(transcript)
        logger.info(f"Word count: {word_count}")

        # Step 4: Calculate WPM
        minutes = duration_seconds / 60
        if minutes == 0:
            raise HTTPException(status_code=400, detail="Audio file is too short")

        calculated_wpm = round(word_count / minutes)
        wpm_min = max(100, round(calculated_wpm * 0.85))
        wpm_max = min(250, round(calculated_wpm * 1.15))

        logger.info(f"Calculated WPM: {calculated_wpm} (range: {wpm_min}-{wpm_max})")

        # Step 5: Update speaker profile if speaker_id provided
        speaker_updated = False
        if speaker_id:
            speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()
            if speaker:
                speaker.wpm = calculated_wpm
                speaker.wpm_min = wpm_min
                speaker.wpm_max = wpm_max
                db.commit()
                speaker_updated = True
                logger.info(f"Updated speaker {speaker.name} with WPM: {calculated_wpm}")
            else:
                logger.warning(f"Speaker ID {speaker_id} not found")

        return {
            "success": True,
            "wpm": calculated_wpm,
            "wpm_min": wpm_min,
            "wpm_max": wpm_max,
            "word_count": word_count,
            "duration_seconds": round(duration_seconds, 1),
            "transcript": transcript[:500] + "..." if len(transcript) > 500 else transcript,  # Truncate for response
            "full_transcript_length": len(transcript),
            "speaker_updated": speaker_updated
        }

    except Exception as e:
        logger.error(f"Error analyzing audio WPM: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze audio: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
                logger.info(f"Cleaned up temporary file: {temp_audio_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


async def get_audio_duration(audio_path: str) -> float:
    """
    Get duration of audio file in seconds

    TODO: Implement using ffprobe or pydub
    Example with ffprobe:
        ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 audio.mp3
    """
    import subprocess

    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        duration = float(result.stdout.strip())
        return duration

    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="ffprobe not installed. Install ffmpeg: apt-get install ffmpeg"
        )
    except Exception as e:
        logger.error(f"Failed to get audio duration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get audio duration: {str(e)}")


async def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file to text using Whisper server

    Primary: whisper-medium on port 8887 (faster)
    Fallback: openwebui-whisper-api on port 8886 (slower but reliable)

    Uses OpenAI Whisper API format
    Loads configuration from database (ai_services.whisper) if available
    """
    import httpx
    from api_config import api_config_manager

    # Try to load Whisper config from database
    whisper_config = api_config_manager.get_service_config(
        workflow="preproduction",
        category="ai_services",
        service="whisper"
    )

    # Default Whisper servers (Kairo)
    whisper_servers = []

    # If config exists in database and is enabled, use it as primary
    if whisper_config and whisper_config.get("enabled"):
        db_host = whisper_config.get("host")
        db_endpoint = whisper_config.get("endpoint", "/v1/audio/transcriptions")
        if db_host:
            whisper_servers.append({
                "name": "whisper-database-config",
                "host": db_host,
                "endpoint": db_endpoint,
                "timeout": 120.0
            })
            logger.info(f"Using Whisper config from database: {db_host}")

    # Add hardcoded fallbacks (Kairo servers)
    whisper_servers.extend([
        {
            "name": "whisper-medium",
            "host": "http://192.168.51.197:8887",
            "endpoint": "/v1/audio/transcriptions",
            "timeout": 120.0
        },
        {
            "name": "openwebui-whisper-api",
            "host": "http://192.168.51.197:8886",
            "endpoint": "/v1/audio/transcriptions",
            "timeout": 180.0  # Slower, needs more time
        }
    ])

    last_error = None

    # Try each server in order
    for server in whisper_servers:
        try:
            logger.info(f"Attempting transcription with {server['name']} ({server['host']})")

            async with httpx.AsyncClient(timeout=server['timeout']) as client:
                # Open audio file
                with open(audio_path, 'rb') as audio_file:
                    files = {
                        'file': (os.path.basename(audio_path), audio_file, 'audio/mpeg')
                    }
                    data = {
                        'model': 'whisper-1',  # Required by OpenAI API format
                        'language': 'en'  # English language
                    }

                    response = await client.post(
                        f"{server['host']}{server['endpoint']}",
                        files=files,
                        data=data
                    )

                    if response.status_code == 200:
                        result = response.json()
                        transcript = result.get('text', '')

                        if transcript:
                            logger.info(f"✅ Transcription successful using {server['name']} ({len(transcript)} chars)")
                            return transcript.strip()
                        else:
                            logger.warning(f"Empty transcript from {server['name']}")
                            last_error = "Empty transcript returned"
                    else:
                        logger.warning(f"Whisper server {server['name']} returned HTTP {response.status_code}")
                        last_error = f"HTTP {response.status_code}: {response.text[:200]}"

        except httpx.TimeoutException:
            logger.warning(f"Timeout connecting to {server['name']} - trying fallback")
            last_error = f"Timeout after {server['timeout']}s"
        except httpx.ConnectError:
            logger.warning(f"Connection refused to {server['name']} - trying fallback")
            last_error = f"Connection refused to {server['host']}"
        except Exception as e:
            logger.error(f"Error with {server['name']}: {e}")
            last_error = str(e)

    # All servers failed
    raise HTTPException(
        status_code=503,
        detail=f"All Whisper servers unavailable. Last error: {last_error}"
    )


def count_words(text: str) -> int:
    """
    Count words in transcript text
    Handles contractions and hyphenated words correctly
    """
    # Simple word count - split on whitespace
    words = text.split()

    # Filter out empty strings and punctuation-only tokens
    words = [w for w in words if w.strip() and not all(c in '.,!?;:' for c in w)]

    return len(words)


@router.get("/speaker/{speaker_id}/measurements")
async def get_speaker_measurements(
    speaker_id: int,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get WPM measurement history for a speaker

    TODO: Implement measurement history table to track multiple measurements over time
    For now, just returns current speaker WPM settings
    """

    speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()

    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")

    return {
        "success": True,
        "speaker": speaker.name,
        "current_wpm": speaker.wpm,
        "wpm_range": {
            "min": speaker.wpm_min,
            "max": speaker.wpm_max
        },
        "measurements": []  # TODO: Add historical measurements
    }
