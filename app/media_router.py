"""
Media serving and upload API endpoints using dynamic path routing
"""
from fastapi import APIRouter, HTTPException, status, File, UploadFile, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from auth.utils import get_current_user_or_key
from core.media_paths import media_paths, MediaType, MediaCategory
from typing import Optional
import shutil
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{path:path}")
async def serve_media(path: str):
    """
    Serve media files from the media root
    Path is relative to media root and dynamically resolved
    """
    # Use media_paths to resolve and validate the request
    file_path = media_paths.resolve_media_request(path)
    
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )
    
    # Determine media type for proper content-type header
    media_type = media_paths.get_media_type_from_file(file_path)
    
    # Map media types to MIME types
    mime_types = {
        MediaType.IMAGE: "image/jpeg",  # Will be refined based on extension
        MediaType.VIDEO: "video/mp4",
        MediaType.AUDIO: "audio/mpeg",
        MediaType.DOCUMENT: "application/pdf",
    }
    
    # Refine MIME type based on actual extension
    ext = file_path.suffix.lower()
    ext_mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.pdf': 'application/pdf',
        '.json': 'application/json',
    }
    
    media_type_str = ext_mime_map.get(ext, mime_types.get(media_type, "application/octet-stream"))
    
    return FileResponse(
        path=file_path,
        media_type=media_type_str,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.post("/upload")
async def upload_media(
    category: MediaCategory,
    media_type: MediaType,
    identifier: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """
    Universal media upload endpoint with dynamic routing
    
    Args:
        category: Category of media (show, episode, library, etc.)
        media_type: Type of media (logo, video, audio, etc.)
        identifier: Context identifier (show asset_id, episode number, etc.)
        file: The uploaded file
    """
    
    # Validate file extension
    if not media_paths.validate_extension(file.filename, media_type):
        allowed = list(media_paths.extensions.get(media_type, set()))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type for {media_type}. Allowed: {', '.join(allowed)}"
        )
    
    # Route the upload to the correct location
    routing_info = media_paths.route_upload(
        category=category,
        media_type=media_type,
        identifier=identifier,
        filename=file.filename
    )
    
    # Save the file
    try:
        with routing_info["full_path"].open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Media uploaded: {routing_info['filename']} to {routing_info['directory']}")
        
        return {
            "message": "File uploaded successfully",
            "filename": routing_info["filename"],
            "path": routing_info["relative_path"],
            "url": routing_info["url"],
            "category": category.value,
            "media_type": media_type.value
        }
        
    except Exception as e:
        logger.error(f"Error uploading media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.get("/config/paths")
async def get_media_config(
    current_user: dict = Depends(get_current_user_or_key)
):
    """
    Get current media path configuration
    Admin only endpoint for debugging and configuration
    """
    if current_user.get("access_level") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return media_paths.get_config()


@router.post("/config/update")
async def update_media_config(
    updates: dict,
    current_user: dict = Depends(get_current_user_or_key)
):
    """
    Update media path configuration
    Admin only endpoint
    """
    if current_user.get("access_level") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    media_paths.update_config(updates)
    
    return {
        "message": "Configuration updated",
        "config": media_paths.get_config()
    }


@router.get("/episodes")
async def list_episodes(
    current_user: dict = Depends(get_current_user_or_key)
):
    """List all available episodes with their media information"""
    episodes = media_paths.list_episodes()
    
    episode_info = []
    for ep_num in episodes:
        info = media_paths.get_episode_info(ep_num)
        if info:
            episode_info.append(info)
    
    return {
        "count": len(episode_info),
        "episodes": episode_info
    }


@router.post("/organize/{episode_number}")
async def organize_episode_assets(
    episode_number: str,
    current_user: dict = Depends(get_current_user_or_key)
):
    """
    Organize loose files in episode directory into proper subdirectories
    Admin only endpoint
    """
    if current_user.get("access_level") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    media_paths.organize_episode_assets(episode_number)
    
    return {
        "message": f"Episode {episode_number} assets organized",
        "episode_info": media_paths.get_episode_info(episode_number)
    }