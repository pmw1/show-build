"""
Voice Conference API Router

Provides endpoints for managing Asterisk-based voice conferences:
- Create/end conferences
- Track participants
- Handle recordings and transcriptions
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import logging
import httpx
from sqlalchemy import text

from database import get_db
from auth.utils import get_current_user_or_key
from asterisk_service import get_asterisk_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice/conference", tags=["voice-conference"])


# ============================================================================
# TRANSCRIPTION + DIARIZATION PIPELINE
# ============================================================================
async def trigger_transcription_pipeline(recording_path: str, conference_id: str, db: Session):
    """
    Trigger transcription and diarization for conference recording

    Pipeline:
    1. Send to Whisper for transcription
    2. Send to diarization service for speaker identification
    3. Merge transcription with speaker labels
    4. Store in database
    """
    logger.info(f"Starting transcription pipeline for {conference_id}: {recording_path}")

    try:
        # Load diarization config from database
        query = text("""
            SELECT config_key, config_value
            FROM api_configs
            WHERE service = 'diarization' AND is_enabled = TRUE
        """)
        result = db.execute(query)

        diarization_config = {}
        for row in result:
            diarization_config[row.config_key] = row.config_value

        if not diarization_config.get('enabled') == 'true':
            logger.warning("Diarization service not enabled, skipping")
            return

        diarization_url = diarization_config.get('url')
        api_key = diarization_config.get('apiKey')
        timeout = int(diarization_config.get('timeout', 600))

        if not diarization_url:
            logger.error("Diarization URL not configured")
            return

        # Call diarization service
        logger.info(f"Calling diarization service: {diarization_url}/diarize")

        async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
            response = await client.post(
                f"{diarization_url}/diarize",
                headers={"X-API-Key": api_key},
                json={
                    "audio_path": recording_path,
                    "num_speakers": None,  # Auto-detect
                    "min_speakers": 1,
                    "max_speakers": 10
                }
            )

            if response.status_code == 200:
                diarization_data = response.json()
                logger.info(f"Diarization complete: {diarization_data['num_speakers']} speakers, {len(diarization_data['segments'])} segments")

                # TODO: Store diarization results in database
                # TODO: Trigger Whisper transcription
                # TODO: Merge transcription with speaker labels

                return diarization_data
            else:
                logger.error(f"Diarization failed: {response.status_code} - {response.text}")

    except Exception as e:
        logger.error(f"Transcription pipeline error: {e}")
        raise


# ============================================================================
# CREATE CONFERENCE
# ============================================================================
@router.post("/create")
async def create_conference(
    episode_id: str = Body(...),
    title: str = Body(None),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Create a new voice conference for an episode

    Body:
    {
      "episode_id": "0245",
      "title": "Interview with Dr. Jane Doe"
    }

    Returns:
    {
      "conference_id": "ep-0245-abc123",
      "pin": "123456",
      "dial_in_number": "+1-555-0100",
      "webrtc_url": "sip:ep-0245-abc123@asterisk.local",
      "recording_enabled": true,
      "created_at": "2025-10-09T10:30:00"
    }
    """
    try:
        asterisk = await get_asterisk_service(db)

        if not asterisk:
            raise HTTPException(
                status_code=503,
                detail="Asterisk service not configured or unavailable"
            )

        user_id = current_user.get('id') or current_user.get('user_id')

        conference = await asterisk.create_conference(
            episode_id=episode_id,
            user_id=user_id,
            title=title
        )

        logger.info(f"Conference created: {conference['conference_id']} by user {user_id}")

        return {
            "success": True,
            "conference": conference
        }

    except Exception as e:
        logger.error(f"Failed to create conference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GET CONFERENCE DETAILS
# ============================================================================
@router.get("/{conference_id}")
async def get_conference(
    conference_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Get conference details including participant list"""
    try:
        asterisk = await get_asterisk_service(db)

        if not asterisk:
            raise HTTPException(status_code=503, detail="Asterisk service unavailable")

        conference = await asterisk.get_conference(conference_id)

        if not conference:
            raise HTTPException(status_code=404, detail="Conference not found")

        return {
            "success": True,
            "conference": conference
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# JOIN CONFERENCE (Browser/WebRTC)
# ============================================================================
class JoinRequest(BaseModel):
    join_method: str = 'webrtc'

@router.post("/{conference_id}/join")
async def join_conference(
    conference_id: str,
    request: JoinRequest,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Join conference from browser (WebRTC)

    Returns SIP connection details for WebRTC client
    """
    try:
        asterisk = await get_asterisk_service(db)

        if not asterisk:
            raise HTTPException(status_code=503, detail="Asterisk service unavailable")

        conference = await asterisk.get_conference(conference_id)
        if not conference:
            raise HTTPException(status_code=404, detail="Conference not found")

        # Add participant
        user_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
        if not user_name:
            user_name = current_user.get('username', 'User')

        caller_id = f"WebRTC-{current_user.get('id')}"

        participant_id = await asterisk.add_participant(
            conference_id=conference_id,
            caller_id=caller_id,
            join_method=request.join_method
        )

        # Return WebRTC connection details
        return {
            "success": True,
            "participant_id": participant_id,
            "webrtc_config": {
                "sip_uri": conference['webrtc_url'],
                "username": caller_id,
                "display_name": user_name
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to join conference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# IDENTIFY PARTICIPANT
# ============================================================================
@router.post("/{conference_id}/identify")
async def identify_participant(
    conference_id: str,
    participant_id: str = Body(...),
    name: str = Body(...),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Manually identify a participant (post-call or during call)

    Body:
    {
      "participant_id": "p-1",
      "name": "Dr. Jane Doe"
    }
    """
    try:
        asterisk = await get_asterisk_service(db)

        if not asterisk:
            raise HTTPException(status_code=503, detail="Asterisk service unavailable")

        success = await asterisk.identify_participant(
            conference_id=conference_id,
            participant_id=participant_id,
            name=name
        )

        if not success:
            raise HTTPException(status_code=404, detail="Participant not found")

        return {
            "success": True,
            "message": f"Participant {participant_id} identified as {name}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to identify participant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# END CONFERENCE
# ============================================================================
@router.post("/{conference_id}/end")
async def end_conference(
    conference_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    End conference and trigger recording/transcription pipeline

    Returns path to recording file
    """
    try:
        asterisk = await get_asterisk_service(db)

        if not asterisk:
            raise HTTPException(status_code=503, detail="Asterisk service unavailable")

        recording_path = await asterisk.end_conference(conference_id)

        if not recording_path:
            raise HTTPException(status_code=404, detail="Conference not found")

        logger.info(f"Conference ended: {conference_id}, recording: {recording_path}")

        # Trigger transcription + diarization pipeline
        try:
            await trigger_transcription_pipeline(recording_path, conference_id, db)
        except Exception as e:
            logger.error(f"Failed to trigger transcription pipeline: {e}")
            # Don't fail the endpoint - transcription is async

        return {
            "success": True,
            "conference_id": conference_id,
            "recording_path": recording_path,
            "message": "Conference ended, recording saved"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end conference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LIST ACTIVE CONFERENCES
# ============================================================================
@router.get("/")
async def list_conferences(
    episode_id: str = None,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """List all active conferences, optionally filtered by episode"""
    try:
        asterisk = await get_asterisk_service(db)

        if not asterisk:
            return {"success": True, "conferences": []}

        conferences = []
        for conf_id, conf_data in asterisk.active_conferences.items():
            if episode_id and conf_data.get('episode_id') != episode_id:
                continue

            conferences.append({
                'conference_id': conf_id,
                'episode_id': conf_data.get('episode_id'),
                'title': conf_data.get('title'),
                'created_at': conf_data.get('created_at'),
                'participant_count': len(conf_data.get('participants', []))
            })

        return {
            "success": True,
            "conferences": conferences
        }

    except Exception as e:
        logger.error(f"Failed to list conferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))
