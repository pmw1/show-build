"""
Enhanced AssetID Router - Replaces legacy /next-id endpoint
Provides complete AssetID management with tracking, relationships, and history
"""
from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from database import get_db
from services.asset_id import AssetIDService
from auth.utils import get_current_user_or_key
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/assetid", tags=["AssetID Management"])


class AssetIDRequest(BaseModel):
    """Request model for new AssetID generation."""
    entity_type: str
    reason: str
    requested_by: Optional[str] = None
    linked_to: Optional[List[Dict[str, str]]] = None
    context: Optional[Dict[str, Any]] = None


class PendingMessageRequest(BaseModel):
    """Request model for pending messages."""
    asset_id: str
    message: str
    message_type: str = "note"
    priority: int = 5
    expires_at: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None


@router.post("/generate")
async def generate_asset_id(
    request: AssetIDRequest,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Generate new AssetID with full tracking and history.
    Replaces legacy /next-id endpoint with enhanced functionality.
    
    **Enhanced Features:**
    - Complete request tracking (who, when, why, context)
    - Relationship mapping between AssetIDs  
    - Pending message delivery
    - Full audit history
    """
    try:
        # Use current user as default requester
        if not request.requested_by:
            request.requested_by = current_user.get("username", current_user.get("client_name", "unknown"))
        
        # Generate AssetID with full tracking
        asset_id = AssetIDService.request_asset_id(
            db=db,
            entity_type=request.entity_type,
            reason=request.reason,
            requested_by=request.requested_by,
            linked_to=request.linked_to or [],
            context=request.context or {}
        )
        
        return {
            "asset_id": asset_id,
            "entity_type": request.entity_type,
            "requested_by": request.requested_by,
            "created_at": datetime.utcnow(),
            "status": "generated"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate AssetID: {str(e)}")


@router.post("/generate-legacy")
async def generate_legacy_format(
    slug: str = Form(...),
    type: str = Form(...),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Legacy compatibility endpoint - maintains same interface as /next-id
    but uses enhanced AssetID service underneath.
    
    **Migration Path:**
    - Same request format as old /next-id
    - Returns enhanced AssetID with tracking
    - Gradually migrate clients to /generate endpoint
    """
    try:
        # Convert legacy request to new format
        asset_id = AssetIDService.request_asset_id(
            db=db,
            entity_type=type.lower(),
            reason="create",
            requested_by=current_user.get("username", current_user.get("client_name", "legacy_client")),
            context={
                "slug": slug,
                "legacy_compatibility": True,
                "original_endpoint": "/next-id"
            }
        )
        
        # Return in legacy format for compatibility
        return {"id": asset_id}
        
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{asset_id}")
async def get_asset_history(
    asset_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get complete history and metadata for an AssetID.
    
    **Returns:**
    - Creation details (who, when, why, context)
    - All relationships to other AssetIDs
    - Complete message history
    - Processing history and metadata
    """
    try:
        history = AssetIDService.get_asset_history(db, asset_id)
        
        if not history:
            raise HTTPException(status_code=404, detail=f"AssetID {asset_id} not found")
        
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get asset history: {str(e)}")


@router.post("/{asset_id}/message")
async def add_message_to_asset(
    asset_id: str,
    message: str = Form(...),
    message_type: str = Form("note"),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Attach a message to an AssetID.
    If AssetID doesn't exist yet, stores as pending message for future delivery.
    
    **Use Cases:**
    - Production notes: "Add B-roll footage here"
    - Warnings: "Audio levels too low"
    - Instructions: "Use alternative angle for this segment"
    """
    try:
        user_id = current_user.get("username", current_user.get("client_name", "unknown"))
        
        AssetIDService.add_message(
            db=db,
            asset_id=asset_id,
            message=message,
            message_type=message_type,
            user_id=user_id
        )
        
        return {
            "asset_id": asset_id,
            "message": "Message added successfully",
            "message_type": message_type,
            "created_by": user_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


@router.post("/pending-message")
async def create_pending_message(
    request: PendingMessageRequest,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Create a message for an AssetID that will be created in the future.
    Message will be automatically delivered when the AssetID is generated.
    
    **Use Cases:**
    - Pre-production planning: "Remember to get interview B-roll"
    - Workflow coordination: "This segment needs legal review"
    - Resource allocation: "Reserve studio time for this"
    """
    try:
        user_id = current_user.get("username", current_user.get("client_name", "unknown"))
        
        pending_msg = AssetIDService.add_pending_message(
            db=db,
            future_asset_id=request.asset_id,
            message=request.message,
            message_type=request.message_type,
            priority=request.priority,
            expires_at=request.expires_at,
            user_id=user_id,
            context=request.context or {}
        )
        
        return {
            "pending_message_id": pending_msg.id,
            "asset_id": request.asset_id,
            "message": "Pending message created successfully",
            "priority": request.priority,
            "expires_at": request.expires_at
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create pending message: {str(e)}")


@router.get("/{asset_id}/relationships")
async def get_asset_relationships(
    asset_id: str,
    direction: str = "both",  # source, target, both
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get all relationships for an AssetID.
    
    **Direction options:**
    - "source": AssetIDs this one links TO
    - "target": AssetIDs that link TO this one  
    - "both": All relationships in both directions
    """
    try:
        relationships = AssetIDService.get_links(db, asset_id, direction)
        
        return {
            "asset_id": asset_id,
            "direction": direction,
            "relationships": [
                {
                    "source": r.source_asset_id,
                    "target": r.target_asset_id,
                    "type": r.relationship_type,
                    "created_at": r.created_at,
                    "created_by": r.created_by,
                    "is_active": r.is_active
                } for r in relationships
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get relationships: {str(e)}")


@router.post("/{source_id}/link/{target_id}")
async def link_assets(
    source_id: str,
    target_id: str,
    link_type: str = Form("related_to"),
    metadata: Optional[str] = Form(None),  # JSON string
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Create a relationship link between two AssetIDs.
    
    **Standard Link Types:**
    - parent_child, belongs_to, contains
    - derived_from, references, replaces  
    - extracted_from, related_to, duplicate_of
    - version_of
    """
    try:
        import json
        metadata_dict = {}
        if metadata:
            metadata_dict = json.loads(metadata)
        
        link = AssetIDService.link_assets(
            db=db,
            source_id=source_id,
            target_id=target_id,
            link_type=link_type,
            metadata=metadata_dict
        )
        
        return {
            "source_id": source_id,
            "target_id": target_id,
            "link_type": link_type,
            "link_id": link.id,
            "message": "Assets linked successfully"
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON in metadata field")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to link assets: {str(e)}")


@router.get("/type/{entity_type}")
async def list_assets_by_type(
    entity_type: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    List all AssetIDs of a specific entity type.
    
    **Entity Types:**
    - segment, episode, element, cue, script, etc.
    - Useful for reports and bulk operations
    """
    try:
        from models_assetid import AssetIDRegistry
        
        assets = db.query(AssetIDRegistry).filter(
            AssetIDRegistry.entity_type == entity_type,
            AssetIDRegistry.is_active == "active"
        ).order_by(AssetIDRegistry.created_at.desc()).limit(limit).all()
        
        return {
            "entity_type": entity_type,
            "count": len(assets),
            "assets": [
                {
                    "asset_id": a.asset_id,
                    "created_at": a.created_at,
                    "requested_by": a.requested_by,
                    "request_reason": a.request_reason
                } for a in assets
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list assets: {str(e)}")


@router.get("/stats/summary")
async def get_assetid_stats(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get AssetID system statistics and summary.
    
    **Returns:**
    - Total AssetIDs by entity type
    - Recent activity
    - Most active requesters
    - System health metrics
    """
    try:
        from models_assetid import AssetIDRegistry
        from sqlalchemy import func as sql_func
        
        # Count by entity type
        type_counts = db.query(
            AssetIDRegistry.entity_type,
            sql_func.count(AssetIDRegistry.id).label('count')
        ).group_by(AssetIDRegistry.entity_type).all()
        
        # Total count
        total_count = db.query(AssetIDRegistry).count()
        
        # Recent activity (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_count = db.query(AssetIDRegistry).filter(
            AssetIDRegistry.created_at >= yesterday
        ).count()
        
        return {
            "total_asset_ids": total_count,
            "recent_24h": recent_count,
            "by_entity_type": {
                row.entity_type: row.count for row in type_counts
            },
            "system_status": "operational",
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")