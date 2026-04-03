"""
Whiteboard media endpoints: upload media, fetch link preview, analyze URL.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import os
import shutil
import mimetypes
from pathlib import Path
import re
from urllib.parse import urlparse
import logging

from database import get_db
from auth.utils import get_current_user_or_key
from models_whiteboard import AssetPoolFile, AssetTag
from services.asset_id import AssetIDService
from link_preview_service import fetch_link_preview

logger = logging.getLogger(__name__)

router = APIRouter(tags=["whiteboard"])


@router.post("/fetch-link-preview")
async def fetch_link_preview_endpoint(
    url: str,
    bypass_cache: bool = False,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Fetch OpenGraph metadata for a URL (for rich link previews).
    Uses Twitter API if configured for enhanced Twitter/X metadata.

    Args:
        url: The URL to fetch preview for
        bypass_cache: If True, skip cache and fetch fresh from source
    """
    try:
        if bypass_cache:
            # Skip cache lookup, delete existing cache entry if present
            from sqlalchemy import text
            import hashlib
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            db.execute(text("DELETE FROM link_preview_cache WHERE url_hash = :url_hash"), {"url_hash": url_hash})
            db.commit()
            logger.info(f"🔄 Cache bypassed for {url}")

        preview_data = fetch_link_preview(url, db=db)
        return preview_data
    except Exception as e:
        logger.error(f"Error fetching link preview for {url}: {e}")
        return {"error": str(e)}


@router.get("/analyze-url")
async def analyze_url(
    url: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Analyze a URL to detect service type and determine what child nodes should be spawned.
    Must be defined before /{identifier} route to avoid path collision.
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    service_patterns = {
        'twitter': r'(twitter\.com|x\.com)',
        'youtube': r'(youtube\.com|youtu\.be)',
        'tiktok': r'tiktok\.com',
        'instagram': r'instagram\.com',
        'rumble': r'rumble\.com',
        'soundcloud': r'soundcloud\.com'
    }

    detected_service = None
    for service, pattern in service_patterns.items():
        if re.search(pattern, domain):
            detected_service = service
            break

    if not detected_service:
        return {
            "service": "generic",
            "has_media": False,
            "spawn_children": False,
            "message": "URL does not match known media services"
        }

    service_metadata = {
        'twitter': {'has_media': True, 'spawn_children': True, 'media_types': ['image', 'video'], 'description': 'Twitter/X post'},
        'youtube': {'has_media': True, 'spawn_children': True, 'media_types': ['video'], 'description': 'YouTube video'},
        'tiktok': {'has_media': True, 'spawn_children': True, 'media_types': ['video'], 'description': 'TikTok video'},
        'instagram': {'has_media': True, 'spawn_children': True, 'media_types': ['image', 'video'], 'description': 'Instagram post'},
        'rumble': {'has_media': True, 'spawn_children': True, 'media_types': ['video'], 'description': 'Rumble video'},
        'soundcloud': {'has_media': True, 'spawn_children': True, 'media_types': ['audio'], 'description': 'SoundCloud audio'},
    }

    metadata = service_metadata.get(detected_service, {})

    return {
        "service": detected_service,
        "url": url,
        "has_media": metadata.get('has_media', False),
        "spawn_children": metadata.get('spawn_children', False),
        "media_types": metadata.get('media_types', []),
        "description": metadata.get('description', ''),
        "needs_download": True
    }


@router.post("/{identifier}/upload-media")
async def upload_media(
    identifier: str,
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),  # Comma-separated tags
    source: Optional[str] = Form("manual_upload"),
    source_url: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Upload media file to asset pool.
    Stores file in /mnt/sync/asset-pool/ with AssetID naming.
    Returns file URL and AssetID for whiteboard card creation.
    """
    user_id = current_user.get("user_id")

    # Validate file type
    allowed_types = {
        'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
        'video': ['video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo'],
        'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp3'],
        'document': ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    }

    mime_type = file.content_type
    media_category = None

    for category, types in allowed_types.items():
        if mime_type in types:
            media_category = category
            break

    if not media_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {mime_type}"
        )

    # Generate AssetID
    asset_type = f"whiteboard_{media_category}"
    asset_id = AssetIDService.generate(asset_type)

    # Get file extension
    file_ext = os.path.splitext(file.filename)[1]
    if not file_ext:
        file_ext = mimetypes.guess_extension(mime_type) or ''

    # Save file with AssetID name
    file_name = f"{asset_id}{file_ext}"

    # Save to whiteboard media directory if episode, otherwise asset-pool
    is_episode = identifier.isdigit() and len(identifier) == 4
    if is_episode:
        from core.paths import paths as path_manager
        media_dir = path_manager.get_whiteboard_media_dir(identifier)
        media_dir.mkdir(parents=True, exist_ok=True)
        file_path_dest = media_dir / file_name
        relative_path = f"whiteboard/{identifier}/{file_name}"
        file_url = f"/repo/{relative_path}"
    else:
        asset_pool_dir = Path("/mnt/sync/asset-pool")
        asset_pool_dir.mkdir(parents=True, exist_ok=True)
        file_path_dest = asset_pool_dir / file_name
        relative_path = str(file_path_dest)
        file_url = f"/asset-pool/{file_name}"

    # Save uploaded file
    with open(file_path_dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get file size
    file_size = os.path.getsize(file_path_dest)

    # Create asset pool record
    asset_pool_file = AssetPoolFile(
        asset_id=asset_id,
        file_path=str(file_path_dest),
        original_filename=file.filename,
        mime_type=mime_type,
        file_size=file_size,
        source=source,
        source_url=source_url
    )
    db.add(asset_pool_file)

    # Add tags if provided
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        username = current_user.get("username", "unknown")

        for tag in tag_list:
            asset_tag = AssetTag(
                asset_id=asset_id,
                tag=tag,
                created_by=username
            )
            db.add(asset_tag)

    db.commit()

    logger.info(f"Uploaded {media_category} file {file.filename} as {asset_id} -> {file_path_dest}")

    return {
        "success": True,
        "asset_id": asset_id,
        "file_url": file_url,
        "media_path": relative_path if is_episode else None,
        "file_path": str(file_path_dest),
        "mime_type": mime_type,
        "file_size": file_size,
        "media_category": media_category,
        "original_filename": file.filename
    }
