"""
Scratchpad Router
API endpoints for brainstorm scratchpad
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid

from database import get_db
from auth.utils import get_current_user_or_key
from models_scratchpad import Scratchpad, ScratchpadItem
from link_preview_service import fetch_link_preview
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scratchpad", tags=["scratchpad"])


# Pydantic models
class ScratchpadItemCreate(BaseModel):
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
    # Link preview fields
    preview_title: Optional[str] = None
    preview_description: Optional[str] = None
    preview_image: Optional[str] = None
    preview_domain: Optional[str] = None
    preview_favicon: Optional[str] = None
    # Social media metadata (X/Twitter, etc.)
    social_metadata: Optional[Dict[str, Any]] = None


class ScratchpadItemResponse(BaseModel):
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


class ScratchpadResponse(BaseModel):
    id: int
    episode_number: Optional[str] = None
    workspace_id: Optional[str] = None
    name: Optional[str] = None
    items: List[ScratchpadItemResponse]

    class Config:
        from_attributes = True


class ScratchpadSaveRequest(BaseModel):
    episode_number: Optional[str] = None
    workspace_id: Optional[str] = None
    name: Optional[str] = None
    items: List[ScratchpadItemCreate]


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
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Fetch OpenGraph metadata for a URL (for rich link previews).
    Uses Twitter API if configured for enhanced Twitter/X metadata.
    """
    try:
        preview_data = fetch_link_preview(url, db=db)
        return preview_data
    except Exception as e:
        logger.error(f"Error fetching link preview for {url}: {e}")
        return {"error": str(e)}


@router.get("/list")
async def list_scratchpads(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    List all scratchpads for the current user.
    """
    user_id = current_user.get("user_id")

    scratchpads = db.query(Scratchpad).filter(
        Scratchpad.created_by == user_id
    ).order_by(Scratchpad.updated_at.desc()).all()

    return {
        "scratchpads": [
            {
                "id": s.id,
                "episode_number": s.episode_number,
                "workspace_id": s.workspace_id,
                "name": s.name,
                "item_count": len(s.items),
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in scratchpads
        ]
    }


@router.get("/{identifier}")
async def get_scratchpad(
    identifier: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get scratchpad by episode number or workspace ID.
    Creates new scratchpad if it doesn't exist.
    """
    user_id = current_user.get("user_id")

    # Check if identifier is episode number (4 digits) or workspace ID
    is_episode = identifier.isdigit() and len(identifier) == 4

    if is_episode:
        scratchpad = db.query(Scratchpad).filter(
            Scratchpad.episode_number == identifier,
            Scratchpad.created_by == user_id
        ).first()
    else:
        scratchpad = db.query(Scratchpad).filter(
            Scratchpad.workspace_id == identifier,
            Scratchpad.created_by == user_id
        ).first()

    # Create new scratchpad if doesn't exist
    if not scratchpad:
        scratchpad = Scratchpad(
            episode_number=identifier if is_episode else None,
            workspace_id=identifier if not is_episode else None,
            created_by=user_id
        )
        db.add(scratchpad)
        db.commit()
        db.refresh(scratchpad)
        logger.info(f"Created new scratchpad for {'episode ' if is_episode else 'workspace '}{identifier}")

    return ScratchpadResponse.from_orm(scratchpad)


@router.post("/{identifier}/save")
async def save_scratchpad(
    identifier: str,
    data: ScratchpadSaveRequest,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Save scratchpad items (bulk save - replaces all items).
    Auto-creates scratchpad if it doesn't exist.
    """
    user_id = current_user.get("user_id")

    # Check if identifier is episode number or workspace ID
    is_episode = identifier.isdigit() and len(identifier) == 4

    if is_episode:
        scratchpad = db.query(Scratchpad).filter(
            Scratchpad.episode_number == identifier,
            Scratchpad.created_by == user_id
        ).first()
    else:
        scratchpad = db.query(Scratchpad).filter(
            Scratchpad.workspace_id == identifier,
            Scratchpad.created_by == user_id
        ).first()

    # Create new scratchpad if doesn't exist
    if not scratchpad:
        scratchpad = Scratchpad(
            episode_number=identifier if is_episode else None,
            workspace_id=identifier if not is_episode else None,
            name=data.name,
            created_by=user_id
        )
        db.add(scratchpad)
        db.flush()
    else:
        # Update name if provided
        if data.name:
            scratchpad.name = data.name

    # Delete existing items
    db.query(ScratchpadItem).filter(
        ScratchpadItem.scratchpad_id == scratchpad.id
    ).delete()

    # Add new items
    for item_data in data.items:
        item = ScratchpadItem(
            scratchpad_id=scratchpad.id,
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
            social_metadata=item_data.social_metadata
        )
        db.add(item)

    db.commit()
    db.refresh(scratchpad)

    logger.info(f"Saved {len(data.items)} items to scratchpad {identifier}")

    return {
        "success": True,
        "scratchpad_id": scratchpad.id,
        "item_count": len(data.items)
    }


@router.delete("/{identifier}")
async def delete_scratchpad(
    identifier: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Delete scratchpad and all its items.
    """
    user_id = current_user.get("user_id")

    # Check if identifier is episode number or workspace ID
    is_episode = identifier.isdigit() and len(identifier) == 4

    if is_episode:
        scratchpad = db.query(Scratchpad).filter(
            Scratchpad.episode_number == identifier,
            Scratchpad.created_by == user_id
        ).first()
    else:
        scratchpad = db.query(Scratchpad).filter(
            Scratchpad.workspace_id == identifier,
            Scratchpad.created_by == user_id
        ).first()

    if not scratchpad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scratchpad not found"
        )

    db.delete(scratchpad)
    db.commit()

    logger.info(f"Deleted scratchpad {identifier}")

    return {
        "success": True,
        "message": "Scratchpad deleted"
    }
