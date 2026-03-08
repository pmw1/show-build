"""
Whiteboard Router
API endpoints for brainstorm whiteboard
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

router = APIRouter(prefix="/api/whiteboard", tags=["whiteboard"])


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

    # Relative path within repo/whiteboard/{episode}/
    relative_path = f"whiteboard/{episode_number}/{filename}"

    # Serving URL via the /repo static mount
    media_url = f"/repo/{relative_path}"

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


@router.post("/generate-workspace-id")
async def generate_workspace_id(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Generate a new workspace ID (AssetID format).
    """
    workspace_id = f"WORKSPACE-{uuid.uuid4().hex[:8].upper()}"

    return {
        "workspace_id": workspace_id,
        "message": "Workspace ID generated"
    }


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


@router.get("/list")
async def list_whiteboards(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    List all whiteboards for the current user.
    """
    user_id = current_user.get("user_id")

    whiteboards = db.query(Whiteboard).filter(
        Whiteboard.created_by == user_id
    ).order_by(Whiteboard.updated_at.desc()).all()

    return {
        "whiteboards": [
            {
                "id": s.id,
                "episode_number": s.episode_number,
                "workspace_id": s.workspace_id,
                "name": s.name,
                "item_count": len(s.items),
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in whiteboards
        ]
    }


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
    import re
    from urllib.parse import urlparse

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


@router.get("/{identifier}")
async def get_whiteboard(
    identifier: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get whiteboard by episode number or workspace ID.
    Creates new whiteboard if it doesn't exist.
    Whiteboards are shared per-episode (no user filter).
    """
    user_id = current_user.get("user_id")

    # Check if identifier is episode number (4 digits) or workspace ID
    is_episode = identifier.isdigit() and len(identifier) == 4

    if is_episode:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.episode_number == identifier
        ).first()
    else:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.workspace_id == identifier
        ).first()

    # Create new whiteboard if doesn't exist
    if not whiteboard:
        whiteboard = Whiteboard(
            episode_number=identifier if is_episode else None,
            workspace_id=identifier if not is_episode else None,
            created_by=user_id
        )
        db.add(whiteboard)
        db.commit()
        db.refresh(whiteboard)
        logger.info(f"Created new whiteboard for {'episode ' if is_episode else 'workspace '}{identifier}")

    # Load node links for this whiteboard
    links = db.query(WhiteboardNodeLink).filter(
        WhiteboardNodeLink.whiteboard_id == whiteboard.id
    ).all()

    # Build item ID-to-index map for frontend mapping
    item_id_to_index = {}
    for idx, item in enumerate(whiteboard.items):
        item_id_to_index[item.id] = idx

    link_data = []
    for link in links:
        source_idx = item_id_to_index.get(link.source_item_id)
        target_idx = item_id_to_index.get(link.target_item_id)
        if source_idx is not None and target_idx is not None:
            link_data.append({
                "id": link.id,
                "source_index": source_idx,
                "target_index": target_idx,
                "relationship_type": link.relationship_type,
                "label": link.label,
                "color": link.color
            })

    # Build response with media URLs resolved from media_path
    items_data = []
    for item in whiteboard.items:
        item_dict = WhiteboardItemResponse.from_orm(item).dict()
        # Build serving URL from media_path
        if item.media_path:
            item_dict["media_url"] = f"/repo/{item.media_path}"
        items_data.append(item_dict)

    response_dict = {
        "id": whiteboard.id,
        "episode_number": whiteboard.episode_number,
        "workspace_id": whiteboard.workspace_id,
        "name": whiteboard.name,
        "items": items_data,
        "node_links": link_data
    }
    return response_dict


@router.post("/{identifier}/save")
async def save_whiteboard(
    identifier: str,
    data: WhiteboardSaveRequest,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Save whiteboard items (bulk save - replaces all items).
    Auto-creates whiteboard if it doesn't exist.
    Whiteboards are shared per-episode (no user filter).
    """
    user_id = current_user.get("user_id")

    # Check if identifier is episode number or workspace ID
    is_episode = identifier.isdigit() and len(identifier) == 4

    if is_episode:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.episode_number == identifier
        ).first()
    else:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.workspace_id == identifier
        ).first()

    # Create new whiteboard if doesn't exist
    if not whiteboard:
        whiteboard = Whiteboard(
            episode_number=identifier if is_episode else None,
            workspace_id=identifier if not is_episode else None,
            name=data.name,
            created_by=user_id
        )
        db.add(whiteboard)
        db.flush()
    else:
        # Update name if provided
        if data.name:
            whiteboard.name = data.name

    # Delete existing links first (FK references items)
    db.query(WhiteboardNodeLink).filter(
        WhiteboardNodeLink.whiteboard_id == whiteboard.id
    ).delete()

    # Delete existing items
    db.query(WhiteboardItem).filter(
        WhiteboardItem.whiteboard_id == whiteboard.id
    ).delete()

    # Determine episode number for media storage
    episode_num = identifier if is_episode else None

    # Add new items and build client-ID-to-DB-ID map
    client_id_to_db_id = {}
    for idx, item_data in enumerate(data.items):
        media_asset_id = item_data.media_asset_id
        media_path = None
        saved_image_data = None

        # If base64 image_data is provided, extract to filesystem
        if item_data.image_data and episode_num:
            # Generate AssetID for this media if not already assigned
            if not media_asset_id:
                media_asset_id = AssetIDService.generate_asset_id("whiteboard_media", db)

            try:
                media_info = _save_media_to_filesystem(
                    item_data.image_data, episode_num, media_asset_id
                )
                media_path = media_info["media_path"]
                # Don't store base64 in database
                saved_image_data = None
            except Exception as e:
                logger.warning(f"Failed to save media to filesystem, falling back to base64: {e}")
                saved_image_data = item_data.image_data
                media_asset_id = None
                media_path = None
        elif item_data.image_data and not episode_num:
            # Standalone workspace - keep base64 for now (no episode directory)
            saved_image_data = item_data.image_data

        item = WhiteboardItem(
            whiteboard_id=whiteboard.id,
            item_type=item_data.item_type,
            title=item_data.title,
            x_position=item_data.x_position,
            y_position=item_data.y_position,
            text_content=item_data.text_content,
            url=item_data.url,
            notes=item_data.notes,
            image_data=saved_image_data,
            media_asset_id=media_asset_id,
            media_path=media_path,
            caption=item_data.caption,
            width=item_data.width,
            z_index=item_data.z_index,
            preview_title=item_data.preview_title,
            preview_description=item_data.preview_description,
            preview_image=item_data.preview_image,
            preview_domain=item_data.preview_domain,
            preview_favicon=item_data.preview_favicon,
            social_metadata=item_data.social_metadata,
            collapsed=item_data.collapsed
        )
        db.add(item)
        db.flush()  # Get the DB-assigned ID
        # Store mapping: use array index as the client reference key
        client_id_to_db_id[idx] = item.id

    # Save node links using client-ID-to-DB-ID mapping
    link_count = 0
    if data.node_links:
        for link_data in data.node_links:
            source_db_id = client_id_to_db_id.get(link_data.source_client_id)
            target_db_id = client_id_to_db_id.get(link_data.target_client_id)
            if source_db_id and target_db_id:
                node_link = WhiteboardNodeLink(
                    whiteboard_id=whiteboard.id,
                    source_item_id=source_db_id,
                    target_item_id=target_db_id,
                    relationship_type=link_data.relationship_type,
                    label=link_data.label,
                    color=link_data.color or "#1976d2"
                )
                db.add(node_link)
                link_count += 1

    db.commit()
    db.refresh(whiteboard)

    logger.info(f"Saved {len(data.items)} items and {link_count} links to whiteboard {identifier}")

    return {
        "success": True,
        "whiteboard_id": whiteboard.id,
        "item_count": len(data.items),
        "link_count": link_count
    }


@router.delete("/{identifier}")
async def delete_whiteboard(
    identifier: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Delete whiteboard and all its items.
    """

    # Check if identifier is episode number or workspace ID
    is_episode = identifier.isdigit() and len(identifier) == 4

    if is_episode:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.episode_number == identifier
        ).first()
    else:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.workspace_id == identifier
        ).first()

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found"
        )

    db.delete(whiteboard)
    db.commit()

    logger.info(f"Deleted whiteboard {identifier}")

    return {
        "success": True,
        "message": "Whiteboard deleted"
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
    asset_id = AssetIDService.generate_asset_id(asset_type, db)

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



@router.post("/{identifier}/download-social-media")
async def download_social_media(
    identifier: str,
    url: str,
    tags: Optional[str] = None,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Download media from social media URLs (Twitter, YouTube, TikTok, etc.)
    For Twitter/X: Uses Twitter API v2 directly to get media URLs and download them.
    For other services: Falls back to yt-dlp if installed.
    Returns list of downloaded media files with AssetIDs.
    """
    import re
    from urllib.parse import urlparse

    username = current_user.get("username", "unknown")
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    is_twitter = bool(re.search(r'(twitter\.com|x\.com)', domain))

    if is_twitter:
        return await _download_twitter_media(identifier, url, tags, username, db)
    else:
        return await _download_via_ytdlp(identifier, url, tags, username, db)


async def _download_twitter_media(
    identifier: str, url: str, tags: Optional[str],
    username: str, db: Session
):
    """Download media from Twitter/X using API v2 directly."""
    import re
    import requests as http_requests

    # Extract tweet ID from URL
    url_match = re.match(
        r'https?://(?:www\.)?(twitter\.com|x\.com)/([^/]+)/status/(\d+)',
        url
    )
    if not url_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract tweet ID from URL"
        )

    tweet_id = url_match.group(3)

    # Fetch tweet data - try v2 API first, syndication as fallback
    from services.social_media import fetch_tweet_via_syndication, fetch_tweet_from_api, get_twitter_oauth_credentials
    from link_preview_service import get_twitter_bearer_token

    oauth_creds = get_twitter_oauth_credentials(db)
    bearer_token = get_twitter_bearer_token(db) if not oauth_creds else None

    tweet_data = None
    if oauth_creds or bearer_token:
        tweet_data = fetch_tweet_from_api(tweet_id, bearer_token=bearer_token, oauth_creds=oauth_creds)

    # If v2 API failed or returned error, try syndication as fallback
    if not tweet_data or (isinstance(tweet_data, dict) and tweet_data.get('_error')):
        v2_error = tweet_data  # preserve error info
        logger.info(f"v2 API failed for tweet {tweet_id}, trying syndication fallback")
        tweet_data = fetch_tweet_via_syndication(tweet_id)
        if tweet_data:
            logger.info(f"Syndication fallback succeeded for tweet {tweet_id}")

    # Handle total failure
    if not tweet_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch tweet {tweet_id} from any source"
        )

    if isinstance(tweet_data, dict) and tweet_data.get('_error'):
        # API returned an error - return it with partial status so frontend can show warning
        error_info = {k: v for k, v in tweet_data.items() if k != '_error'}
        error_info['fallback_used'] = False
        return {
            "success": False,
            "status": "error",
            "url": url,
            "tweet_id": tweet_id,
            "files_downloaded": 0,
            "assets": [],
            "error": error_info,
            "tweet_data": None,
        }

    media_objects = tweet_data.get('media_objects', [])
    if not media_objects:
        # No structured media objects, try media_urls as image fallback
        media_urls = tweet_data.get('media_urls', [])
        if media_urls:
            media_objects = [{'type': 'photo', 'url': u} for u in media_urls]

    if not media_objects:
        return {
            "success": True,
            "url": url,
            "files_downloaded": 0,
            "assets": [],
            "message": "Tweet has no downloadable media"
        }

    # Determine destination
    is_episode_wb = identifier.isdigit() and len(identifier) == 4
    if is_episode_wb:
        from core.paths import paths as path_manager
        media_dir = path_manager.get_whiteboard_media_dir(identifier)
    else:
        media_dir = Path("/mnt/sync/asset-pool")
    media_dir.mkdir(parents=True, exist_ok=True)

    asset_records = []

    for media_obj in media_objects:
        media_url = media_obj.get('url')
        if not media_url:
            continue

        media_type = media_obj.get('type', 'photo')

        # Download the file
        try:
            resp = http_requests.get(media_url, timeout=30, stream=True)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to download media from {media_url}: {e}")
            continue

        # Determine extension from content-type or URL
        content_type = resp.headers.get('content-type', '')
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'png' in content_type:
            ext = '.png'
        elif 'webp' in content_type:
            ext = '.webp'
        elif 'mp4' in content_type or 'video' in content_type:
            ext = '.mp4'
        elif 'gif' in content_type:
            ext = '.gif'
        else:
            # Try from URL path
            from urllib.parse import urlparse as parse_url
            path = parse_url(media_url).path
            ext = Path(path).suffix or '.jpg'

        # Determine category
        if media_type in ('video', 'animated_gif'):
            media_category = 'video'
            mime = 'video/mp4'
        else:
            media_category = 'image'
            mime = content_type or f'image/{ext.lstrip(".")}'

        # Generate AssetID and save
        asset_type = f"whiteboard_{media_category}"
        asset_id = AssetIDService.generate_asset_id(asset_type, db)
        file_name = f"{asset_id}{ext}"
        dest_path = media_dir / file_name

        with open(dest_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = os.path.getsize(dest_path)

        if is_episode_wb:
            relative_path = f"whiteboard/{identifier}/{file_name}"
            file_url = f"/repo/{relative_path}"
        else:
            relative_path = str(dest_path)
            file_url = f"/asset-pool/{file_name}"

        source_context = {
            'tweet_id': tweet_id,
            'author': tweet_data.get('author_handle'),
            'author_name': tweet_data.get('author_name'),
            'tweet_text': tweet_data.get('tweet_text', '')[:500],
            'title': f"@{tweet_data.get('author_handle', 'unknown')} - {media_type}",
            'width': media_obj.get('width'),
            'height': media_obj.get('height'),
            'duration_ms': media_obj.get('duration_ms'),
        }

        asset_pool_file = AssetPoolFile(
            asset_id=asset_id,
            file_path=str(dest_path),
            original_filename=file_name,
            mime_type=mime,
            file_size=file_size,
            source='twitter',
            source_url=url,
            source_context=source_context
        )
        db.add(asset_pool_file)

        # Add tags
        if tags:
            tag_list = [t.strip() for t in tags.split(',') if t.strip()]
            for tag in tag_list:
                db.add(AssetTag(asset_id=asset_id, tag=tag, created_by=username))

        if is_episode_wb:
            db.add(AssetTag(asset_id=asset_id, tag=f"episode:{identifier}", created_by=username))

        db.add(AssetTag(asset_id=asset_id, tag="twitter", created_by=username))
        db.commit()

        asset_records.append({
            "asset_id": asset_id,
            "file_url": file_url,
            "media_path": relative_path if is_episode_wb else None,
            "file_path": str(dest_path),
            "mime_type": mime,
            "file_size": file_size,
            "media_category": media_category,
            "original_filename": file_name,
            "source_context": source_context
        })

        logger.info(f"Downloaded Twitter {media_category} from tweet {tweet_id} as {asset_id} -> {dest_path}")

    # Also download author avatar to local cache
    local_avatar_url = None
    avatar_url = tweet_data.get('author_avatar')
    if avatar_url:
        try:
            # Get higher-res avatar (replace _normal with _400x400)
            hires_avatar = avatar_url.replace('_normal', '_400x400')
            resp = http_requests.get(hires_avatar, timeout=10)
            resp.raise_for_status()
            avatar_ext = '.jpg'
            if 'png' in resp.headers.get('content-type', ''):
                avatar_ext = '.png'
            avatar_filename = f"avatar_{tweet_data.get('author_handle', 'unknown')}{avatar_ext}"
            avatar_dest = media_dir / avatar_filename
            with open(avatar_dest, 'wb') as f:
                f.write(resp.content)
            if is_episode_wb:
                local_avatar_url = f"/repo/whiteboard/{identifier}/{avatar_filename}"
            else:
                local_avatar_url = f"/asset-pool/{avatar_filename}"
            logger.info(f"Cached author avatar for @{tweet_data.get('author_handle')} -> {avatar_dest}")
        except Exception as e:
            logger.warning(f"Failed to cache author avatar: {e}")

    # Build local media URL mapping (CDN URL -> local URL)
    local_media_urls = [a["file_url"] for a in asset_records]

    return {
        "success": True,
        "url": url,
        "tweet_id": tweet_id,
        "files_downloaded": len(asset_records),
        "assets": asset_records,
        "tweet_data": tweet_data,
        "local_avatar_url": local_avatar_url,
        "local_media_urls": local_media_urls
    }


async def _download_via_ytdlp(
    identifier: str, url: str, tags: Optional[str],
    username: str, db: Session
):
    """Download media via yt-dlp for non-Twitter services (TikTok, YouTube, etc.).
    Returns rich metadata for local caching, matching Twitter download pattern."""
    import re
    import subprocess
    import tempfile
    import json
    import requests as http_requests
    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Detect service for metadata enrichment
    service = 'generic'
    if 'tiktok.com' in domain:
        service = 'tiktok'
    elif 'youtube.com' in domain or 'youtu.be' in domain:
        service = 'youtube'
    elif 'instagram.com' in domain:
        service = 'instagram'
    elif 'rumble.com' in domain:
        service = 'rumble'
    elif 'soundcloud.com' in domain:
        service = 'soundcloud'

    # For TikTok: fetch oEmbed metadata first (fast, no auth, no rate limits)
    oembed_data = None
    if service == 'tiktok':
        try:
            oembed_resp = http_requests.get(
                f'https://www.tiktok.com/oembed?url={url}',
                timeout=10
            )
            if oembed_resp.status_code == 200:
                oembed_data = oembed_resp.json()
                logger.info(f"TikTok oEmbed: '{oembed_data.get('title', '')[:50]}' by {oembed_data.get('author_name')}")
        except Exception as e:
            logger.warning(f"TikTok oEmbed fetch failed: {e}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_template = str(temp_path / "%(id)s.%(ext)s")

        yt_dlp_cmd = [
            "python", "-m", "yt_dlp",
            "--write-info-json",
            "--write-thumbnail",
            "-o", output_template,
            url
        ]

        try:
            result = subprocess.run(
                yt_dlp_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                logger.error(f"yt-dlp failed: {result.stderr}")
                return {
                    "success": False,
                    "url": url,
                    "service": service,
                    "error": {
                        "service": service,
                        "status_code": 500,
                        "message": "Download failed",
                        "endpoint": "yt-dlp",
                        "detail": result.stderr[:300] if result.stderr else "Unknown yt-dlp error",
                        "fallback_used": False
                    }
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "url": url,
                "service": service,
                "error": {
                    "service": service,
                    "status_code": 408,
                    "message": "Download timed out",
                    "endpoint": "yt-dlp",
                    "detail": "Download timed out after 120 seconds",
                    "fallback_used": False
                }
            }
        except FileNotFoundError:
            return {
                "success": False,
                "url": url,
                "service": service,
                "error": {
                    "service": service,
                    "status_code": 500,
                    "message": "yt-dlp not installed",
                    "endpoint": "yt-dlp",
                    "detail": "yt-dlp is not installed on the server",
                    "fallback_used": False
                }
            }

        downloaded_files = []
        info_json = None

        for file_path in temp_path.iterdir():
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    info_json = json.load(f)
            elif file_path.suffix not in ['.json', '.part']:
                downloaded_files.append(file_path)

        if not downloaded_files:
            return {
                "success": False,
                "url": url,
                "service": service,
                "error": {
                    "service": service,
                    "status_code": 404,
                    "message": "No media files found",
                    "endpoint": "yt-dlp",
                    "detail": "yt-dlp completed but no media files were downloaded",
                    "fallback_used": False
                }
            }

        # Determine destination directory
        is_episode_wb = identifier.isdigit() and len(identifier) == 4
        if is_episode_wb:
            from core.paths import paths as path_manager
            media_dir = path_manager.get_whiteboard_media_dir(identifier)
        else:
            media_dir = Path("/mnt/sync/asset-pool")
        media_dir.mkdir(parents=True, exist_ok=True)

        asset_records = []

        for file_path in downloaded_files:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = 'application/octet-stream'

            if mime_type.startswith('video/'):
                media_category = 'video'
            elif mime_type.startswith('audio/'):
                media_category = 'audio'
            elif mime_type.startswith('image/'):
                media_category = 'image'
            else:
                media_category = 'document'

            asset_type = f"whiteboard_{media_category}"
            asset_id = AssetIDService.generate_asset_id(asset_type, db)

            file_ext = file_path.suffix
            file_name = f"{asset_id}{file_ext}"
            dest_path = media_dir / file_name

            if is_episode_wb:
                relative_path = f"whiteboard/{identifier}/{file_name}"
                file_url = f"/repo/{relative_path}"
            else:
                relative_path = str(dest_path)
                file_url = f"/asset-pool/{file_name}"

            shutil.copy2(file_path, dest_path)
            file_size = os.path.getsize(dest_path)

            source_context = {}
            if info_json:
                source_context = {
                    'title': info_json.get('title'),
                    'uploader': info_json.get('uploader'),
                    'upload_date': info_json.get('upload_date'),
                    'description': info_json.get('description'),
                    'duration': info_json.get('duration'),
                    'view_count': info_json.get('view_count')
                }

            asset_pool_file = AssetPoolFile(
                asset_id=asset_id,
                file_path=str(dest_path),
                original_filename=file_path.name,
                mime_type=mime_type,
                file_size=file_size,
                source=service,
                source_url=url,
                source_context=source_context
            )
            db.add(asset_pool_file)

            if tags:
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]
                for tag in tag_list:
                    db.add(AssetTag(asset_id=asset_id, tag=tag, created_by=username))

            if is_episode_wb:
                db.add(AssetTag(asset_id=asset_id, tag=f"episode:{identifier}", created_by=username))

            db.add(AssetTag(asset_id=asset_id, tag=service, created_by=username))
            db.commit()

            asset_records.append({
                "asset_id": asset_id,
                "file_url": file_url,
                "media_path": relative_path if is_episode_wb else None,
                "file_path": str(dest_path),
                "mime_type": mime_type,
                "file_size": file_size,
                "media_category": media_category,
                "original_filename": file_path.name,
                "source_context": source_context
            })

            logger.info(f"Downloaded {media_category} from {url} as {asset_id} -> {dest_path}")

        # Build rich content_data from yt-dlp info.json (mirrors tweet_data structure)
        content_data = None
        local_avatar_url = None
        local_thumbnail_url = None

        if info_json:
            content_data = {
                'platform': service,
                'post_id': info_json.get('id'),
                'post_text': info_json.get('description') or info_json.get('title', ''),
                'author_name': info_json.get('uploader') or info_json.get('creator'),
                'author_handle': info_json.get('uploader_id') or info_json.get('channel_id'),
                'author_url': info_json.get('uploader_url') or info_json.get('channel_url'),
                'published_time': info_json.get('upload_date'),
                'duration': info_json.get('duration'),
                'duration_string': info_json.get('duration_string'),
                'title': info_json.get('title'),
                'webpage_url': info_json.get('webpage_url'),
            }

            # Engagement metrics (varies by platform)
            if info_json.get('view_count') is not None:
                content_data['views'] = info_json.get('view_count')
            if info_json.get('like_count') is not None:
                content_data['likes'] = info_json.get('like_count')
            if info_json.get('comment_count') is not None:
                content_data['comments'] = info_json.get('comment_count')
            if info_json.get('repost_count') is not None:
                content_data['reposts'] = info_json.get('repost_count')

            # TikTok-specific fields
            if service == 'tiktok':
                content_data['track'] = info_json.get('track')
                content_data['artist'] = info_json.get('artist')
                # TikTok hashtags from description
                desc = info_json.get('description', '')
                hashtags = re.findall(r'#(\w+)', desc)
                if hashtags:
                    content_data['hashtags'] = hashtags

                # Enrich with oEmbed data (more reliable author info)
                if oembed_data:
                    content_data['author_name'] = oembed_data.get('author_name') or content_data.get('author_name')
                    content_data['author_url'] = oembed_data.get('author_url') or content_data.get('author_url')
                    # Extract handle from author_url (https://www.tiktok.com/@handle)
                    author_url = oembed_data.get('author_url', '')
                    if '/@' in author_url:
                        content_data['author_handle'] = author_url.split('/@')[-1].rstrip('/')
                    content_data['oembed_title'] = oembed_data.get('title')
                    content_data['embed_html'] = oembed_data.get('html')

            # Download and cache avatar/thumbnail locally
            thumbnail_url = info_json.get('thumbnail')
            # TikTok oEmbed thumbnail is often better quality
            if oembed_data and oembed_data.get('thumbnail_url'):
                thumbnail_url = oembed_data.get('thumbnail_url')

            # Cache thumbnail
            if thumbnail_url:
                try:
                    resp = http_requests.get(thumbnail_url, timeout=10)
                    resp.raise_for_status()
                    thumb_ext = '.jpg'
                    if 'png' in resp.headers.get('content-type', ''):
                        thumb_ext = '.png'
                    elif 'webp' in resp.headers.get('content-type', ''):
                        thumb_ext = '.webp'
                    post_id = info_json.get('id', 'unknown')
                    thumb_filename = f"thumb_{service}_{post_id}{thumb_ext}"
                    thumb_dest = media_dir / thumb_filename
                    with open(thumb_dest, 'wb') as f:
                        f.write(resp.content)
                    if is_episode_wb:
                        local_thumbnail_url = f"/repo/whiteboard/{identifier}/{thumb_filename}"
                    else:
                        local_thumbnail_url = f"/asset-pool/{thumb_filename}"
                    content_data['thumbnail_url'] = local_thumbnail_url
                    logger.info(f"Cached {service} thumbnail -> {thumb_dest}")
                except Exception as e:
                    logger.warning(f"Failed to cache thumbnail: {e}")
                    content_data['thumbnail_url'] = thumbnail_url

        local_media_urls = [a["file_url"] for a in asset_records]

        return {
            "success": True,
            "url": url,
            "service": service,
            "files_downloaded": len(asset_records),
            "assets": asset_records,
            "content_data": content_data,
            "local_avatar_url": local_avatar_url,
            "local_thumbnail_url": local_thumbnail_url,
            "local_media_urls": local_media_urls
        }


# Node Linking Endpoints

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


@router.post("/{identifier}/link-nodes")
async def create_node_link(
    identifier: str,
    link_data: NodeLinkCreate,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Create a visual connection between two whiteboard nodes.
    """
    user_id = current_user.get("user_id")

    # Get whiteboard
    is_episode = identifier.isdigit() and len(identifier) == 4
    if is_episode:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.episode_number == identifier,
            Whiteboard.created_by == user_id
        ).first()
    else:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.workspace_id == identifier,
            Whiteboard.created_by == user_id
        ).first()

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found"
        )

    # Verify both items exist and belong to this whiteboard
    source_item = db.query(WhiteboardItem).filter(
        WhiteboardItem.id == link_data.source_item_id,
        WhiteboardItem.whiteboard_id == whiteboard.id
    ).first()

    target_item = db.query(WhiteboardItem).filter(
        WhiteboardItem.id == link_data.target_item_id,
        WhiteboardItem.whiteboard_id == whiteboard.id
    ).first()

    if not source_item or not target_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both items not found in whiteboard"
        )

    # Create link
    node_link = WhiteboardNodeLink(
        whiteboard_id=whiteboard.id,
        source_item_id=link_data.source_item_id,
        target_item_id=link_data.target_item_id,
        relationship_type=link_data.relationship_type,
        label=link_data.label,
        color=link_data.color
    )
    db.add(node_link)
    db.commit()
    db.refresh(node_link)

    logger.info(f"Created node link from item {link_data.source_item_id} to {link_data.target_item_id}")

    return NodeLinkResponse.from_orm(node_link)


@router.get("/{identifier}/node-links")
async def get_node_links(
    identifier: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get all node links for a whiteboard.
    """
    user_id = current_user.get("user_id")

    # Get whiteboard
    is_episode = identifier.isdigit() and len(identifier) == 4
    if is_episode:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.episode_number == identifier,
            Whiteboard.created_by == user_id
        ).first()
    else:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.workspace_id == identifier,
            Whiteboard.created_by == user_id
        ).first()

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found"
        )

    links = db.query(WhiteboardNodeLink).filter(
        WhiteboardNodeLink.whiteboard_id == whiteboard.id
    ).all()

    return {
        "links": [NodeLinkResponse.from_orm(link) for link in links]
    }


@router.delete("/{identifier}/link-nodes/{link_id}")
async def delete_node_link(
    identifier: str,
    link_id: int,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Delete a node link.
    """
    user_id = current_user.get("user_id")

    # Get whiteboard
    is_episode = identifier.isdigit() and len(identifier) == 4
    if is_episode:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.episode_number == identifier,
            Whiteboard.created_by == user_id
        ).first()
    else:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.workspace_id == identifier,
            Whiteboard.created_by == user_id
        ).first()

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found"
        )

    # Get and delete link
    link = db.query(WhiteboardNodeLink).filter(
        WhiteboardNodeLink.id == link_id,
        WhiteboardNodeLink.whiteboard_id == whiteboard.id
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node link not found"
        )

    db.delete(link)
    db.commit()

    logger.info(f"Deleted node link {link_id}")

    return {
        "success": True,
        "message": "Node link deleted"
    }
