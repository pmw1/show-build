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


# EXIF tags worth surfacing on a card, mapped to friendly keys.
# Values come from PIL.ExifTags.TAGS names.
_EXIF_FIELDS = {
    "Make": "camera_make",
    "Model": "camera_model",
    "LensModel": "lens",
    "DateTimeOriginal": "taken_at",
    "ISOSpeedRatings": "iso",
    "FNumber": "aperture",
    "ExposureTime": "shutter",
    "FocalLength": "focal_length",
    "Orientation": "orientation",
    "Software": "software",
}


def _rational_to_str(value) -> str:
    """
    Render an EXIF rational in human terms.

    Values arrive either as PIL IFDRational (float-able) or as a raw
    (numerator, denominator) tuple, depending on how the file was written —
    so handle both.
    """
    try:
        if isinstance(value, tuple) and len(value) == 2:
            num, den = value
            f = float(num) / float(den) if den else float(num)
        else:
            f = float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return str(value)
    if f <= 0:
        return str(value)
    # Shutter speeds below 1s read better as 1/N
    if f < 1:
        return f"1/{round(1 / f)}"
    return f"{f:g}"


def extract_image_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract displayable metadata from an image on disk.

    Always returns intrinsic properties (format, width, height, file size).
    Adds EXIF fields only when the file actually carries them — web-sourced
    images (WebP/PNG screenshots) typically carry none, which is expected and
    not an error.

    Never raises: metadata is decorative, so a failure here must not break a save.
    """
    meta: Dict[str, Any] = {}
    try:
        meta["file_size"] = file_path.stat().st_size
    except OSError:
        pass

    try:
        from PIL import Image, ExifTags
    except ImportError:
        logger.debug("Pillow unavailable; skipping image metadata extraction")
        return meta

    try:
        with Image.open(file_path) as im:
            meta["format"] = im.format
            meta["width"], meta["height"] = im.size
            meta["mode"] = im.mode

            try:
                raw_exif = im.getexif()
            except Exception:
                raw_exif = None

            if raw_exif:
                names = {v: k for k, v in ExifTags.TAGS.items()}
                exif: Dict[str, Any] = {}
                for tag_name, friendly in _EXIF_FIELDS.items():
                    tag_id = names.get(tag_name)
                    if tag_id is None:
                        continue
                    value = raw_exif.get(tag_id)
                    if value in (None, ""):
                        continue
                    if friendly == "aperture":
                        exif[friendly] = f"f/{_rational_to_str(value)}"
                    elif friendly == "shutter":
                        exif[friendly] = f"{_rational_to_str(value)}s"
                    elif friendly == "focal_length":
                        exif[friendly] = f"{_rational_to_str(value)}mm"
                    elif isinstance(value, bytes):
                        exif[friendly] = value.decode("utf-8", "replace").strip("\x00").strip()
                    else:
                        exif[friendly] = str(value).strip()

                # GPS, when the camera recorded it
                gps_id = names.get("GPSInfo")
                if gps_id and raw_exif.get(gps_id):
                    try:
                        gps = raw_exif.get_ifd(gps_id)
                        coords = _gps_to_decimal(gps)
                        if coords:
                            exif["gps_lat"], exif["gps_lon"] = coords
                    except Exception:
                        pass

                if exif:
                    meta["exif"] = exif
    except Exception as e:
        logger.debug(f"Could not read image metadata from {file_path.name}: {e}")

    return meta


def _gps_to_decimal(gps: Dict[Any, Any]):
    """Convert EXIF GPS IFD to (lat, lon) decimal degrees, or None."""
    def to_deg(dms, ref, negative_ref):
        d, m, s = (float(x) for x in dms)
        val = d + m / 60.0 + s / 3600.0
        return -val if str(ref).upper() == negative_ref else val

    # GPS IFD keys: 1=LatRef 2=Lat 3=LonRef 4=Lon
    if 2 in gps and 4 in gps:
        lat = to_deg(gps[2], gps.get(1, "N"), "S")
        lon = to_deg(gps[4], gps.get(3, "E"), "W")
        return round(lat, 6), round(lon, 6)
    return None


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
    media_metadata: Optional[Dict[str, Any]] = None  # Extracted image metadata
    comments: Optional[List[Dict[str, Any]]] = None  # Per-node user comments


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
    media_metadata: Optional[Dict[str, Any]] = None  # Extracted image metadata
    comments: Optional[List[Dict[str, Any]]] = None  # Per-node user comments
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
