"""
Media Repository Router - API endpoints for managing the media repository (bumpers, stingers, ads, promos, etc.)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import shutil
from database import get_db, Base

router = APIRouter()

# ===========================
# Database Model
# ===========================
class RepoItem(Base):
    """Media repository items (bumpers, stingers, ads, promos, etc.)"""
    __tablename__ = "repo_items"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False, index=True)  # 'bump', 'sting', 'ad', 'promo', etc.
    asset_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    media_url = Column(String, nullable=True)
    alpha = Column(Boolean, default=False)
    audio = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# ===========================
# Pydantic Models
# ===========================
class RepoItemCreate(BaseModel):
    type: str
    assetId: str
    name: str
    duration: str
    mediaUrl: Optional[str] = None
    alpha: bool = False
    audio: bool = True

class RepoItemResponse(BaseModel):
    id: int
    type: str
    assetId: str
    name: str
    duration: str
    mediaUrl: Optional[str]
    alpha: bool
    audio: bool
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# ===========================
# API Endpoints
# ===========================
@router.get("/api/repo")
async def get_repo_items(
    type: Optional[str] = Query(None, description="Filter by type (bump, sting, ad, promo, etc.)"),
    db: Session = Depends(get_db)
):
    """
    Get all media repository items, optionally filtered by type
    """
    try:
        query = db.query(RepoItem)

        if type:
            query = query.filter(RepoItem.type == type)

        items_db = query.order_by(RepoItem.name).all()

        items = []
        for item in items_db:
            items.append({
                "id": item.id,
                "type": item.type,
                "assetId": item.asset_id,
                "name": item.name,
                "duration": item.duration,
                "mediaUrl": item.media_url,
                "alpha": item.alpha,
                "audio": item.audio,
                "createdAt": item.created_at.isoformat() if item.created_at else None,
                "updatedAt": item.updated_at.isoformat() if item.updated_at else None
            })

        return {
            "success": True,
            "items": items,
            "count": len(items)
        }
    except Exception as e:
        print(f"❌ Error fetching repo items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/repo")
async def create_repo_item(
    item_data: RepoItemCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new item in the media repository
    """
    try:
        # Check if AssetID already exists
        existing = db.query(RepoItem).filter(
            RepoItem.asset_id == item_data.assetId
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"AssetID {item_data.assetId} already exists in repository"
            )

        # Create new item
        new_item = RepoItem(
            type=item_data.type,
            asset_id=item_data.assetId,
            name=item_data.name,
            duration=item_data.duration,
            media_url=item_data.mediaUrl,
            alpha=item_data.alpha,
            audio=item_data.audio
        )

        db.add(new_item)
        db.commit()
        db.refresh(new_item)

        return {
            "success": True,
            "message": f"{item_data.type.upper()} saved to repository",
            "item": {
                "id": new_item.id,
                "type": new_item.type,
                "assetId": new_item.asset_id,
                "name": new_item.name,
                "duration": new_item.duration,
                "mediaUrl": new_item.media_url,
                "alpha": new_item.alpha,
                "audio": new_item.audio
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating repo item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/repo/{item_id}")
async def delete_repo_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an item from the media repository
    """
    try:
        item = db.query(RepoItem).filter(RepoItem.id == item_id).first()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        db.delete(item)
        db.commit()

        return {
            "success": True,
            "message": f"{item.type.upper()} deleted from repository"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting repo item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/repo/{item_id}")
async def update_repo_item(
    item_id: int,
    item_data: RepoItemCreate,
    db: Session = Depends(get_db)
):
    """
    Update an item in the media repository
    """
    try:
        item = db.query(RepoItem).filter(RepoItem.id == item_id).first()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Update fields
        item.type = item_data.type
        item.asset_id = item_data.assetId
        item.name = item_data.name
        item.duration = item_data.duration
        item.media_url = item_data.mediaUrl
        item.alpha = item_data.alpha
        item.audio = item_data.audio
        item.updated_at = datetime.now()

        db.commit()
        db.refresh(item)

        return {
            "success": True,
            "message": f"{item.type.upper()} updated in repository",
            "item": {
                "id": item.id,
                "type": item.type,
                "assetId": item.asset_id,
                "name": item.name,
                "duration": item.duration,
                "mediaUrl": item.media_url,
                "alpha": item.alpha,
                "audio": item.audio
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating repo item: {e}")
        raise HTTPException(status_code=500, detail=str(e))
