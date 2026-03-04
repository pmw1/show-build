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


# Pydantic models
class WhiteboardItemCreate(BaseModel):
    item_type: str  # 'text', 'link', 'image'
    title: Optional[str] = None  # Custom card header title
    x_position: float
    y_position: float
    text_content: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    image_data: Optional[str] = None
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


class WhiteboardItemResponse(BaseModel):
    id: int
    item_type: str
    title: Optional[str] = None  # Custom card header title
    x_position: float
    y_position: float
    text_content: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    image_data: Optional[str] = None
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

    response = WhiteboardResponse.from_orm(whiteboard)
    # Add links to response dict
    response_dict = response.dict()
    response_dict["node_links"] = link_data
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

    # Add new items and build client-ID-to-DB-ID map
    client_id_to_db_id = {}
    for idx, item_data in enumerate(data.items):
        item = WhiteboardItem(
            whiteboard_id=whiteboard.id,
            item_type=item_data.item_type,
            title=item_data.title,
            x_position=item_data.x_position,
            y_position=item_data.y_position,
            text_content=item_data.text_content,
            url=item_data.url,
            notes=item_data.notes,
            image_data=item_data.image_data,
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

    # Create asset pool directory path
    asset_pool_dir = Path("/mnt/sync/asset-pool")
    asset_pool_dir.mkdir(parents=True, exist_ok=True)

    # Get file extension
    file_ext = os.path.splitext(file.filename)[1]
    if not file_ext:
        file_ext = mimetypes.guess_extension(mime_type) or ''

    # Save file with AssetID name
    file_name = f"{asset_id}{file_ext}"
    file_path = asset_pool_dir / file_name

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get file size
    file_size = os.path.getsize(file_path)

    # Create asset pool record
    asset_pool_file = AssetPoolFile(
        asset_id=asset_id,
        file_path=str(file_path),
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

    logger.info(f"Uploaded {media_category} file {file.filename} as {asset_id} to asset pool")

    # Return file URL (relative to asset-pool directory)
    file_url = f"/asset-pool/{file_name}"

    return {
        "success": True,
        "asset_id": asset_id,
        "file_url": file_url,
        "file_path": str(file_path),
        "mime_type": mime_type,
        "file_size": file_size,
        "media_category": media_category,
        "original_filename": file.filename
    }


@router.post("/analyze-url")
async def analyze_url(
    url: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Analyze a URL to detect service type and determine what child nodes should be spawned.
    Returns metadata about detected service and media types.

    Supported services:
    - Twitter/X: Extracts tweet with media
    - YouTube: Extracts video
    - TikTok: Extracts video
    - Instagram: Extracts images/video
    - Rumble: Extracts video
    - SoundCloud: Extracts audio
    """
    import re
    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Service detection patterns
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

    # Service-specific metadata
    service_metadata = {
        'twitter': {
            'has_media': True,
            'spawn_children': True,
            'media_types': ['image', 'video'],
            'description': 'Twitter/X post - may contain images or video'
        },
        'youtube': {
            'has_media': True,
            'spawn_children': True,
            'media_types': ['video'],
            'description': 'YouTube video'
        },
        'tiktok': {
            'has_media': True,
            'spawn_children': True,
            'media_types': ['video'],
            'description': 'TikTok video'
        },
        'instagram': {
            'has_media': True,
            'spawn_children': True,
            'media_types': ['image', 'video'],
            'description': 'Instagram post - may contain images or video'
        },
        'rumble': {
            'has_media': True,
            'spawn_children': True,
            'media_types': ['video'],
            'description': 'Rumble video'
        },
        'soundcloud': {
            'has_media': True,
            'spawn_children': True,
            'media_types': ['audio'],
            'description': 'SoundCloud audio'
        }
    }

    metadata = service_metadata.get(detected_service, {})

    return {
        "service": detected_service,
        "url": url,
        "has_media": metadata.get('has_media', False),
        "spawn_children": metadata.get('spawn_children', False),
        "media_types": metadata.get('media_types', []),
        "description": metadata.get('description', ''),
        "needs_download": True  # All detected services require download
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
    Uses yt-dlp to extract media and stores in asset pool.
    Returns list of downloaded media files with AssetIDs.
    """
    import subprocess
    import tempfile
    import json

    username = current_user.get("username", "unknown")

    # Create temporary directory for download
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Use yt-dlp to download media with metadata
        output_template = str(temp_path / "%(id)s.%(ext)s")

        yt_dlp_cmd = [
            "yt-dlp",
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
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"yt-dlp failed: {result.stderr}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to download media: {result.stderr}"
                )

        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Download timed out after 60 seconds"
            )
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="yt-dlp not installed on server"
            )

        # Find downloaded files
        downloaded_files = []
        info_json = None

        for file_path in temp_path.iterdir():
            if file_path.suffix == '.json':
                # Load metadata
                with open(file_path, 'r') as f:
                    info_json = json.load(f)
            elif file_path.suffix not in ['.json', '.part']:
                downloaded_files.append(file_path)

        if not downloaded_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No media files downloaded"
            )

        # Process each downloaded file
        asset_records = []

        for file_path in downloaded_files:
            # Determine media type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = 'application/octet-stream'

            # Determine category
            if mime_type.startswith('video/'):
                media_category = 'video'
            elif mime_type.startswith('audio/'):
                media_category = 'audio'
            elif mime_type.startswith('image/'):
                media_category = 'image'
            else:
                media_category = 'document'

            # Generate AssetID
            asset_type = f"whiteboard_{media_category}"
            asset_id = AssetIDService.generate_asset_id(asset_type, db)

            # Move to asset pool
            asset_pool_dir = Path("/mnt/sync/asset-pool")
            asset_pool_dir.mkdir(parents=True, exist_ok=True)

            file_ext = file_path.suffix
            file_name = f"{asset_id}{file_ext}"
            dest_path = asset_pool_dir / file_name

            shutil.copy2(file_path, dest_path)
            file_size = os.path.getsize(dest_path)

            # Create asset pool record
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
                source='social_media',
                source_url=url,
                source_context=source_context
            )
            db.add(asset_pool_file)

            # Add tags
            if tags:
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]
                for tag in tag_list:
                    asset_tag = AssetTag(
                        asset_id=asset_id,
                        tag=tag,
                        created_by=username
                    )
                    db.add(asset_tag)

            # Auto-tag with episode if episode whiteboard
            if identifier.isdigit() and len(identifier) == 4:
                asset_tag = AssetTag(
                    asset_id=asset_id,
                    tag=f"episode:{identifier}",
                    created_by=username
                )
                db.add(asset_tag)

            db.commit()

            asset_records.append({
                "asset_id": asset_id,
                "file_url": f"/asset-pool/{file_name}",
                "file_path": str(dest_path),
                "mime_type": mime_type,
                "file_size": file_size,
                "media_category": media_category,
                "original_filename": file_path.name,
                "source_context": source_context
            })

            logger.info(f"Downloaded {media_category} from {url} as {asset_id}")

        return {
            "success": True,
            "url": url,
            "files_downloaded": len(asset_records),
            "assets": asset_records
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
