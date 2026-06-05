"""
Shared helpers, models, and constants for the whiteboard router package.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid
import os
import shutil
import mimetypes
from pathlib import Path

from database import get_db
from auth.utils import get_current_user_or_key
from models_whiteboard import Whiteboard, WhiteboardItem, AssetPoolFile, AssetTag, WhiteboardNodeLink
from models_assetid import AssetIDRegistry
from services.asset_id import AssetIDService
from link_preview_service import fetch_link_preview
import logging

logger = logging.getLogger(__name__)


def _save_media_to_filesystem(base64_data: str, episode_number: str, asset_id: str) -> Dict[str, str]:
    """
    Extract base64 media data to the whiteboard media directory.

    Args:
        base64_data: Base64-encoded media (may include data URI prefix)
        episode_number: Episode number for directory path
        asset_id: AssetID to use as filename stem

    Returns:
        Dict with media_path (relative) and media_url (serving URL)
    """
    import base64
    import re
    from core.paths import paths as path_manager

    # Parse data URI to get mime type and raw data
    # Format: data:image/png;base64,iVBOR...
    mime_type = 'image/png'
    raw_data = base64_data

    data_uri_match = re.match(r'^data:([^;]+);base64,(.+)$', base64_data)
    if data_uri_match:
        mime_type = data_uri_match.group(1)
        raw_data = data_uri_match.group(2)

    # Determine file extension from mime type
    ext_map = {
        'image/png': '.png', 'image/jpeg': '.jpg', 'image/jpg': '.jpg',
        'image/gif': '.gif', 'image/webp': '.webp', 'image/svg+xml': '.svg',
        'video/mp4': '.mp4', 'video/webm': '.webm',
        'audio/mpeg': '.mp3', 'audio/wav': '.wav', 'audio/ogg': '.ogg',
    }
    ext = ext_map.get(mime_type, '.bin')

    # Get whiteboard media directory and ensure it exists
    media_dir = path_manager.get_whiteboard_media_dir(episode_number)
    media_dir.mkdir(parents=True, exist_ok=True)

    # Write file with AssetID as stem
    filename = f"{asset_id}{ext}"
    file_path = media_dir / filename
    file_path.write_bytes(base64.b64decode(raw_data))

    # Relative path within the pool (pool/whiteboard/{episode}/). Stored relative
    # so only the serving prefix changes if the pool ever moves again.
    relative_path = f"whiteboard/{episode_number}/{filename}"

    # Serving URL via the /pool static mount (whiteboard media relocated from /repo)
    media_url = f"/pool/{relative_path}"

    logger.info(f"Saved whiteboard media: {filename} ({file_path.stat().st_size:,} bytes)")

    return {
        "media_path": relative_path,
        "media_url": media_url,
        "mime_type": mime_type,
        "file_size": file_path.stat().st_size
    }


# Pydantic models
class WhiteboardItemCreate(BaseModel):
    item_type: str  # 'text', 'link', 'image'
    title: Optional[str] = None  # Custom card header title
    x_position: float
    y_position: float
    text_content: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    image_data: Optional[str] = None  # Base64 from frontend - extracted to filesystem on save
    caption: Optional[str] = None
    width: Optional[int] = None
    z_index: int = 1
    collapsed: bool = False
    # Link preview fields
    preview_title: Optional[str] = None
    preview_description: Optional[str] = None
    preview_image: Optional[str] = None
    preview_domain: Optional[str] = None
    preview_favicon: Optional[str] = None
    # Social media metadata (X/Twitter, etc.)
    social_metadata: Optional[Dict[str, Any]] = None
    # Code card language
    code_language: Optional[str] = None
    # Filesystem media fields (returned on load, optional on create)
    media_asset_id: Optional[str] = None
    media_url: Optional[str] = None  # Serving URL built from media_path


class WhiteboardItemResponse(BaseModel):
    id: int
    item_type: str
    title: Optional[str] = None  # Custom card header title
    x_position: float
    y_position: float
    text_content: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    image_data: Optional[str] = None  # Deprecated - will be None for new items
    media_asset_id: Optional[str] = None
    media_url: Optional[str] = None  # Serving URL for media file
    media_fallback_url: Optional[str] = None
    caption: Optional[str] = None
    width: Optional[int] = None
    z_index: int
    collapsed: bool = False
    # Link preview fields
    preview_title: Optional[str] = None
    preview_description: Optional[str] = None
    preview_image: Optional[str] = None
    preview_domain: Optional[str] = None
    preview_favicon: Optional[str] = None
    # Social media metadata
    social_metadata: Optional[Dict[str, Any]] = None
    # Code card language
    code_language: Optional[str] = None

    class Config:
        from_attributes = True


class WhiteboardResponse(BaseModel):
    id: int
    episode_number: Optional[str] = None
    workspace_id: Optional[str] = None
    name: Optional[str] = None
    items: List[WhiteboardItemResponse]

    class Config:
        from_attributes = True


class NodeLinkSave(BaseModel):
    source_client_id: int  # Client-side card ID for source
    target_client_id: int  # Client-side card ID for target
    relationship_type: Optional[str] = None
    label: Optional[str] = None
    color: Optional[str] = "#1976d2"


class WhiteboardSaveRequest(BaseModel):
    episode_number: Optional[str] = None
    workspace_id: Optional[str] = None
    name: Optional[str] = None
    items: List[WhiteboardItemCreate]
    node_links: Optional[List[NodeLinkSave]] = None


class NodeLinkCreate(BaseModel):
    source_item_id: int
    target_item_id: int
    relationship_type: Optional[str] = None
    label: Optional[str] = None
    color: Optional[str] = "#1976d2"


class NodeLinkResponse(BaseModel):
    id: int
    whiteboard_id: int
    source_item_id: int
    target_item_id: int
    relationship_type: Optional[str] = None
    label: Optional[str] = None
    color: str

    class Config:
        from_attributes = True
