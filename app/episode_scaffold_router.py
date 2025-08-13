"""
Episode scaffolding API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from auth.utils import get_current_user
from models_user import User
from models_episode import (
    EpisodeTemplateCreate, EpisodeTemplateResponse, 
    BlueprintTemplateResponse
)
from services.episode_scaffold import EpisodeScaffoldService
from core.media_paths import media_paths
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/episodes", tags=["episodes"])

def get_episode_service(db: Session = Depends(get_db)) -> EpisodeScaffoldService:
    """Get episode scaffolding service"""
    return EpisodeScaffoldService(db, media_paths)

@router.get("/next-number")
async def get_next_episode_number(
    service: EpisodeScaffoldService = Depends(get_episode_service),
    current_user: User = Depends(get_current_user)
):
    """Get the next available episode number"""
    try:
        next_number = await service.get_next_episode_number()
        return {"next_episode_number": next_number}
    except Exception as e:
        logger.error(f"Error getting next episode number: {e}")
        raise HTTPException(status_code=500, detail="Failed to get next episode number")

@router.get("/templates")
async def get_blueprint_templates(
    service: EpisodeScaffoldService = Depends(get_episode_service),
    current_user: User = Depends(get_current_user)
) -> List[BlueprintTemplateResponse]:
    """Get available blueprint templates for episode creation"""
    try:
        templates = await service.get_available_templates()
        return templates
    except Exception as e:
        logger.error(f"Error getting blueprint templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get blueprint templates")

@router.post("/create", response_model=EpisodeTemplateResponse)
async def create_episode(
    request: EpisodeTemplateCreate,
    service: EpisodeScaffoldService = Depends(get_episode_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new episode from blueprint template"""
    try:
        # Use user's organization if available  
        organization_id = current_user.get('organization_id', None)
        
        episode = await service.create_episode(
            request=request,
            user_id=current_user['id'],
            organization_id=organization_id
        )
        
        return episode
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating episode: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create episode: {str(e)}")

@router.get("/validate-number/{episode_number}")
async def validate_episode_number(
    episode_number: str,
    service: EpisodeScaffoldService = Depends(get_episode_service),
    current_user: User = Depends(get_current_user)
):
    """Validate if an episode number is available"""
    try:
        is_available = await service.validate_episode_number(episode_number)
        return {"episode_number": episode_number, "is_available": is_available}
    except Exception as e:
        logger.error(f"Error validating episode number: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate episode number")

@router.get("/{episode_number}")
async def get_episode(
    episode_number: str,
    service: EpisodeScaffoldService = Depends(get_episode_service),
    current_user: User = Depends(get_current_user)
):
    """Get episode information by number"""
    try:
        episode = await service.get_episode_by_number(episode_number)
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")
        return episode
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting episode: {e}")
        raise HTTPException(status_code=500, detail="Failed to get episode")

@router.get("/")
async def list_episodes(
    skip: int = 0,
    limit: int = 100,
    service: EpisodeScaffoldService = Depends(get_episode_service),
    current_user: User = Depends(get_current_user)
) -> List[EpisodeTemplateResponse]:
    """List all episodes"""
    try:
        episodes = await service.list_episodes(skip=skip, limit=limit)
        return episodes
    except Exception as e:
        logger.error(f"Error listing episodes: {e}")
        raise HTTPException(status_code=500, detail="Failed to list episodes")