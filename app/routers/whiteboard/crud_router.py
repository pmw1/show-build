"""
Whiteboard CRUD endpoints: generate workspace ID, list, get, save, delete.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import uuid
import logging

from database import get_db
from auth.utils import get_current_user_or_key
from models_whiteboard import Whiteboard, WhiteboardItem, WhiteboardNodeLink
from services.asset_id import AssetIDService
from ._shared import (
    WhiteboardItemCreate, WhiteboardItemResponse, WhiteboardResponse,
    WhiteboardSaveRequest, _save_media_to_filesystem,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["whiteboard"])


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
                media_asset_id = AssetIDService.generate("whiteboard_media")

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
        elif media_asset_id and episode_num and not item_data.image_data:
            # Re-saving existing media card — reconstruct media_path from asset ID
            # The file already exists on disk, we just need to find it
            from core.paths import paths as path_manager
            media_dir = path_manager.get_whiteboard_media_dir(episode_num)
            if media_dir.exists():
                import glob as glob_mod
                matches = glob_mod.glob(str(media_dir / f"{media_asset_id}.*"))
                if matches:
                    from pathlib import Path
                    filename = Path(matches[0]).name
                    media_path = f"whiteboard/{episode_num}/{filename}"

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
            collapsed=item_data.collapsed,
            code_language=item_data.code_language
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
