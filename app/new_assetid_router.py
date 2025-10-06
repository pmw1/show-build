"""
Unified AssetID Generation Router
Creates AssetIDs for any asset type with proper database storage and parent-child linkage.
"""
from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from database import get_db
from services.asset_id import AssetIDService
from auth.utils import get_current_user_or_key
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import logging

# Import all models for database record creation
from models_v2 import (
    Organization, Show, Season, Episode, Break, Rundown, RundownItem, 
    Segment, Script, Element, Cue, AssetLink
)

router = APIRouter(tags=["Unified AssetID Generation"])


class NewAssetIDRequest(BaseModel):
    """Request model for unified AssetID generation."""
    asset_type: str  # episode, segment, cue, ad, promo, cta
    slug: Optional[str] = None  # Descriptive name/slug
    parent_asset_id: Optional[str] = None  # Parent AssetID for linkage
    cue_type: Optional[str] = None  # For cues: SOT, GFX, FSQ, VO, NET
    episode_number: Optional[int] = None  # For episodes
    context: Optional[dict] = None  # Additional metadata


class RemoveAssetIDRequest(BaseModel):
    """Request model for AssetID removal."""
    asset_id: Optional[str] = None  # AssetID to remove from database
    # Alternative lookup methods when AssetID is not available
    episode_number: Optional[int] = None  # For episode context
    context_type: Optional[str] = None  # episode, segment, cue
    file_path: Optional[str] = None  # For context-based lookup


@router.post("/newAssetID")
async def create_new_asset_id(
    request: NewAssetIDRequest,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Unified AssetID generation endpoint for all asset types.
    
    **Supported Asset Types:**
    - `episode`: Creates episode record with episode_number
    - `segment`: Creates segment record with slug, links to parent show/episode
    - `cue`: Creates cue record with slug and cue_type, links to parent segment
    - `ad`: Creates rundown_item record for advertisement
    - `promo`: Creates rundown_item record for promotion  
    - `cta`: Creates rundown_item record for call-to-action
    
    **Parent Linkage:**
    - Episodes: No parent needed (top-level)
    - Segments: parent_asset_id should be episode AssetID
    - Cues: parent_asset_id should be segment AssetID
    - Ads/Promos/CTAs: parent_asset_id should be episode or segment AssetID
    """
    try:
        user_id = current_user.get("username", current_user.get("client_name", "api_user"))
        asset_type = request.asset_type.lower()
        
        # Generate AssetID with tracking
        asset_id = AssetIDService.request_asset_id(
            db=db,
            entity_type=asset_type,
            reason="create",
            requested_by=user_id,
            linked_to=_build_parent_links(request.parent_asset_id) if request.parent_asset_id else [],
            context={
                "slug": request.slug,
                "cue_type": request.cue_type,
                "episode_number": request.episode_number,
                "source": "unified_newAssetID_endpoint",
                **(request.context or {})
            }
        )
        
        # Create database record based on asset type
        db_record = _create_database_record(
            db=db,
            asset_type=asset_type,
            asset_id=asset_id,
            request=request,
            user_id=user_id
        )
        
        # Create parent-child relationship if specified
        if request.parent_asset_id:
            _create_parent_child_link(db, request.parent_asset_id, asset_id, asset_type)
        
        db.commit()
        
        return {
            "asset_id": asset_id,
            "asset_type": asset_type,
            "database_record_id": db_record.id if db_record else None,
            "parent_asset_id": request.parent_asset_id,
            "slug": request.slug,
            "cue_type": request.cue_type,
            "episode_number": request.episode_number,
            "created_by": user_id,
            "created_at": datetime.utcnow(),
            "status": "created"
        }
        
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to create AssetID for {request.asset_type}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create AssetID: {str(e)}")


def _create_database_record(
    db: Session, 
    asset_type: str, 
    asset_id: str, 
    request: NewAssetIDRequest,
    user_id: str
):
    """Create appropriate database record based on asset type."""
    
    if asset_type == "episode":
        return _create_episode_record(db, asset_id, request)
    
    elif asset_type == "segment":
        return _create_segment_record(db, asset_id, request)
    
    elif asset_type == "cue":
        return _create_cue_record(db, asset_id, request)
    
    elif asset_type in ["ad", "advertisement", "promo", "cta"]:
        return _create_rundown_item_record(db, asset_id, request, asset_type)
    
    else:
        # For unsupported types, log but don't fail
        logging.warning(f"No database record creation for asset type: {asset_type}")
        return None


def _create_episode_record(db: Session, asset_id: str, request: NewAssetIDRequest):
    """Create episode database record."""
    from models_v2 import Episode, Season, Show, Organization
    
    # Check if episode number already exists
    if request.episode_number:
        existing_episode = db.query(Episode).filter(
            Episode.episode_number == request.episode_number
        ).first()
        if existing_episode:
            raise HTTPException(status_code=409, detail=f"Episode number {request.episode_number} is already an asset")
    
    # Find or create a default season
    # For now, we'll create/use a default season structure
    # You may want to enhance this logic based on your needs
    
    # Find or create default organization
    default_org = db.query(Organization).filter(Organization.name == "Default Organization").first()
    if not default_org:
        default_org = Organization(
            asset_id=f"ORG{asset_id[-10:]}",
            legal_name="Default Organization",
            name="Default Organization",
            is_test_data=False
        )
        db.add(default_org)
        db.flush()
    
    # Find or create default show
    default_show = db.query(Show).filter(Show.name == "Default Show").first()
    if not default_show:
        default_show = Show(
            asset_id=f"SHW{asset_id[-10:]}",
            organization_id=default_org.id,
            name="Default Show",
            is_test_data=False
        )
        db.add(default_show)
        db.flush()
    
    # Find or create default season
    default_season = db.query(Season).filter(Season.show_id == default_show.id).first()
    if not default_season:
        default_season = Season(
            asset_id=f"SSN{asset_id[-10:]}",
            show_id=default_show.id,
            name="Default Season",
            number=1,
            slug="default-season"
        )
        db.add(default_season)
        db.flush()
    
    episode = Episode(
        asset_id=asset_id,
        season_id=default_season.id,
        episode_number=request.episode_number,
        title=request.slug or f"Episode {request.episode_number or 'Untitled'}",
        slug=request.slug or f"episode-{request.episode_number or asset_id[-8:]}",
        is_test_data=False
    )
    
    db.add(episode)
    db.flush()
    return episode


def _create_segment_record(db: Session, asset_id: str, request: NewAssetIDRequest):
    """Create segment database record."""
    from models_v2 import Segment, RundownItemType
    
    # Find parent episode if parent_asset_id provided
    parent_episode_id = None
    if request.parent_asset_id:
        parent_episode = db.query(Episode).filter(
            Episode.asset_id == request.parent_asset_id
        ).first()
        if parent_episode:
            parent_episode_id = parent_episode.id
    
    segment = Segment(
        asset_id=asset_id,
        episode_id=parent_episode_id,
        rundown_type=RundownItemType.SEGMENT,
        title=request.slug or "Untitled Segment",
        slug=request.slug or f"segment-{asset_id[-8:]}",
        order=1,  # Default order - you may want to calculate this
        estimated_duration=180  # Default 3 minutes in seconds
    )
    
    db.add(segment)
    db.flush()
    return segment


def _create_cue_record(db: Session, asset_id: str, request: NewAssetIDRequest):
    """Create cue database record."""
    from models_v2 import Cue, CueType
    
    # Find parent segment/rundown item if parent_asset_id provided
    parent_segment_id = None
    if request.parent_asset_id:
        # Check RundownItem table for segment-type rundown items (segments ARE rundown items)
        from models_v2 import RundownItem
        parent_rundown_item = db.query(RundownItem).filter(
            RundownItem.asset_id == request.parent_asset_id,
            RundownItem.item_type == 'segment'
        ).first()
        if parent_rundown_item:
            parent_segment_id = parent_rundown_item.id

    if not parent_segment_id:
        raise HTTPException(status_code=400, detail="Cues require a parent segment AssetID from RundownItem table")
    
    # Map cue_type from request to database enum
    cue_type_mapping = {
        "SOT": CueType.MEDIA,
        "GFX": CueType.MEDIA,
        "FSQ": CueType.MEDIA,
        "VO": CueType.AUDIO_MIC,
        "NET": CueType.MEDIA
    }
    
    db_cue_type = cue_type_mapping.get(request.cue_type, CueType.MEDIA)
    
    cue = Cue(
        asset_id=asset_id,
        segment_id=parent_segment_id,
        cue_type=db_cue_type,
        name=request.slug or f"{request.cue_type or 'CUE'} Cue",
        time_offset=0.0,  # Default start time
        parameters={
            "original_cue_type": request.cue_type,
            "slug": request.slug
        }
    )
    
    db.add(cue)
    db.flush()
    return cue


def _create_rundown_item_record(db: Session, asset_id: str, request: NewAssetIDRequest, item_type: str):
    """Create rundown_item database record for ads, promos, CTAs."""
    from models_v2 import RundownItem, Rundown, Episode
    
    # Map item types
    type_mapping = {
        "ad": "advertisement",
        "advertisement": "advertisement", 
        "promo": "promo",
        "cta": "cta"
    }
    
    mapped_type = type_mapping.get(item_type, item_type)
    
    # Find or create a default rundown
    default_rundown = db.query(Rundown).first()
    if not default_rundown:
        # Create a default episode first if none exists
        default_episode = db.query(Episode).first()
        if not default_episode:
            # Create minimal episode structure
            default_episode = _create_episode_record(db, f"EPS{asset_id[-10:]}", 
                NewAssetIDRequest(asset_type="episode", slug="Default Episode"))
        
        default_rundown = Rundown(
            asset_id=f"RUN{asset_id[-10:]}",
            episode_id=default_episode.id,
            name="Default Rundown",
            description="Auto-created rundown for standalone items"
        )
        db.add(default_rundown)
        db.flush()
    
    rundown_item = RundownItem(
        asset_id=asset_id,
        rundown_id=default_rundown.id,
        item_type=mapped_type,
        title=request.slug or f"{mapped_type.title()} Item",
        slug=request.slug or f"{mapped_type}-{asset_id[-8:]}",
        order_in_rundown=1,  # Default - calculate proper order
        duration="00:00:30",  # Default 30 seconds
        status="draft",
        is_test_data=False
    )
    
    db.add(rundown_item)
    db.flush()
    return rundown_item


def _build_parent_links(parent_asset_id: str) -> list:
    """Build parent link structure for AssetID service."""
    return [{"asset_id": parent_asset_id, "link_type": "parent_child"}]


def _create_parent_child_link(db: Session, parent_asset_id: str, child_asset_id: str, child_type: str):
    """Create parent-child relationship link."""
    link = AssetLink(
        source_asset_id=parent_asset_id,
        target_asset_id=child_asset_id,
        link_type="parent_child",
        meta_data={
            "child_type": child_type,
            "relationship": "parent_to_child"
        }
    )
    db.add(link)


@router.post("/removeAssetID")
async def remove_asset_id(
    request: RemoveAssetIDRequest,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Remove AssetID from database.
    
    **Removes:**
    - AssetID registry entry
    - Associated database records (Episode, Segment, Cue, etc.)
    - Asset links (parent-child relationships)
    
    **Note:** This operation cannot be undone.
    """
    try:
        user_id = current_user.get("username", current_user.get("client_name", "api_user"))
        
        # Find the AssetID registry entry using different lookup methods
        from models_assetid import AssetIDRegistry
        registry_entry = None
        asset_id = None
        
        if request.asset_id:
            # Direct AssetID lookup
            asset_id = request.asset_id
            registry_entry = db.query(AssetIDRegistry).filter(
                AssetIDRegistry.asset_id == asset_id
            ).first()
        elif request.episode_number and request.context_type == "episode":
            # Episode number lookup
            registry_entry = db.query(AssetIDRegistry).filter(
                AssetIDRegistry.entity_type == "episode"
            ).join(Episode, AssetIDRegistry.asset_id == Episode.asset_id).filter(
                Episode.episode_number == request.episode_number
            ).first()
            if registry_entry:
                asset_id = registry_entry.asset_id
        
        if not registry_entry:
            if request.asset_id:
                raise HTTPException(status_code=404, detail=f"AssetID {request.asset_id} not found in registry")
            elif request.episode_number:
                raise HTTPException(status_code=404, detail=f"Episode {request.episode_number} not found in registry")
            else:
                raise HTTPException(status_code=400, detail="Must provide either asset_id or context information")
        
        # Remove associated database records based on entity type
        removed_records = _remove_database_records(db, asset_id, registry_entry.entity_type)
        
        # Remove asset links
        removed_links = _remove_asset_links(db, asset_id)
        
        # Remove registry entry
        db.delete(registry_entry)
        
        db.commit()
        
        return {
            "asset_id": asset_id,
            "entity_type": registry_entry.entity_type,
            "removed_records": removed_records,
            "removed_links": removed_links,
            "removed_by": user_id,
            "removed_at": datetime.utcnow(),
            "status": "removed"
        }
        
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to remove AssetID {request.asset_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to remove AssetID: {str(e)}")


def _remove_database_records(db: Session, asset_id: str, entity_type: str) -> list:
    """Remove associated database records for the AssetID."""
    removed_records = []
    
    try:
        if entity_type == "episode":
            episodes = db.query(Episode).filter(Episode.asset_id == asset_id).all()
            for episode in episodes:
                removed_records.append(f"Episode(id={episode.id}, number={episode.episode_number})")
                db.delete(episode)
        
        elif entity_type == "segment":
            from models_v2 import Segment
            segments = db.query(Segment).filter(Segment.asset_id == asset_id).all()
            for segment in segments:
                removed_records.append(f"Segment(id={segment.id}, title={segment.title})")
                db.delete(segment)
        
        elif entity_type == "cue":
            from models_v2 import Cue
            cues = db.query(Cue).filter(Cue.asset_id == asset_id).all()
            for cue in cues:
                removed_records.append(f"Cue(id={cue.id}, name={cue.name})")
                db.delete(cue)
        
        elif entity_type in ["ad", "advertisement", "promo", "cta"]:
            from models_v2 import RundownItem
            items = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).all()
            for item in items:
                removed_records.append(f"RundownItem(id={item.id}, title={item.title})")
                db.delete(item)
        
        else:
            logging.warning(f"No database record removal logic for entity type: {entity_type}")
            
    except Exception as e:
        logging.error(f"Error removing database records for {asset_id}: {e}")
        
    return removed_records


def _remove_asset_links(db: Session, asset_id: str) -> list:
    """Remove asset links where this AssetID is source or target."""
    removed_links = []
    
    try:
        # Remove links where this asset is the source
        source_links = db.query(AssetLink).filter(AssetLink.source_asset_id == asset_id).all()
        for link in source_links:
            removed_links.append(f"Link({link.source_asset_id} -> {link.target_asset_id})")
            db.delete(link)
        
        # Remove links where this asset is the target  
        target_links = db.query(AssetLink).filter(AssetLink.target_asset_id == asset_id).all()
        for link in target_links:
            removed_links.append(f"Link({link.source_asset_id} -> {link.target_asset_id})")
            db.delete(link)
            
    except Exception as e:
        logging.error(f"Error removing asset links for {asset_id}: {e}")
        
    return removed_links


# Legacy compatibility endpoints that redirect to the new unified endpoint
@router.post("/generate_asset_id/episode")
async def generate_episode_asset_id_legacy(
    episode_number: int = Form(...),
    slug: str = Form(None),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Legacy endpoint for episode AssetID generation."""
    request = NewAssetIDRequest(
        asset_type="episode",
        episode_number=episode_number,
        slug=slug
    )
    result = await create_new_asset_id(request, current_user, db)
    return {"asset_id": result["asset_id"]}


@router.post("/generate_asset_id/segment")  
async def generate_segment_asset_id_legacy(
    slug: str = Form(...),
    parent_asset_id: str = Form(None),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Legacy endpoint for segment AssetID generation."""
    request = NewAssetIDRequest(
        asset_type="segment",
        slug=slug,
        parent_asset_id=parent_asset_id
    )
    result = await create_new_asset_id(request, current_user, db)
    return {"asset_id": result["asset_id"]}


@router.post("/generate_asset_id/cue")
async def generate_cue_asset_id_legacy(
    type: str = Form(...),  # SOT, GFX, FSQ, VO, NET
    slug: str = Form(None),
    parent_asset_id: str = Form(None),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Legacy endpoint for cue AssetID generation."""
    request = NewAssetIDRequest(
        asset_type="cue",
        slug=slug,
        parent_asset_id=parent_asset_id,
        cue_type=type
    )
    result = await create_new_asset_id(request, current_user, db)
    return {"asset_id": result["asset_id"]}