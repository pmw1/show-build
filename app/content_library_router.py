"""
Content Library Router - API endpoints for reusable content management.
Handles library CRUD, placements, and type settings.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from database import get_db
from auth.utils import get_current_user_or_key
from services.asset_id import AssetIDService


router = APIRouter(prefix="/api/content-library", tags=["content-library"])


# =====================
# Pydantic Models
# =====================

class ContentLibraryCreate(BaseModel):
    """Schema for creating a new library item."""
    item_type: str = Field(..., description="Content type (advertisement, promo, cta, etc.)")
    title: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = None
    script_content: Optional[str] = None
    duration: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    customer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    priority: str = "normal"
    extra_data: Optional[Dict[str, Any]] = None
    is_test_data: bool = False


class ContentLibraryUpdate(BaseModel):
    """Schema for updating a library item."""
    title: Optional[str] = None
    slug: Optional[str] = None
    script_content: Optional[str] = None
    scratch_content: Optional[str] = None  # Per-item scratch/notes (Reusables Studio)
    duration: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    customer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    priority: Optional[str] = None
    is_active: Optional[bool] = None
    extra_data: Optional[Dict[str, Any]] = None


class ContentPlacementCreate(BaseModel):
    """Schema for placing a library item in a rundown."""
    library_asset_id: str = Field(..., description="Asset ID of the library item to place")
    order_in_rundown: int = Field(..., description="Position in rundown")
    airdate: Optional[datetime] = None
    placement_notes: Optional[str] = None


class ContentTypeSettingsUpdate(BaseModel):
    """Schema for updating content type settings."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_reusable: Optional[bool] = None
    default_duration: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CustomTypeCreate(BaseModel):
    """Schema for creating a custom rundown item type."""
    type_name: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z][a-z0-9_]*$',
                           description="Unique type identifier (lowercase, underscores allowed)")
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: str = Field(default="grey", description="Color name or hex value")
    icon: str = Field(default="mdi-shape", description="MDI icon name")
    is_reusable: bool = Field(default=False, description="Routes to library picker when true")
    default_duration: Optional[str] = Field(default="00:00:30", description="Default duration for new items")


# =====================
# Library CRUD Endpoints
# =====================

@router.get("/")
async def list_library_items(
    item_type: Optional[str] = Query(None, description="Filter by content type"),
    valid_on: Optional[datetime] = Query(None, description="Filter items valid on this date"),
    is_active: bool = Query(True, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in title/customer_name"),
    include_test_data: bool = Query(False, description="Include test data"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """List library items with optional filters."""
    from models_content_library import ContentLibrary

    query = db.query(ContentLibrary)

    # Filter by active status
    if is_active is not None:
        query = query.filter(ContentLibrary.is_active == is_active)

    # Filter by item type
    if item_type:
        query = query.filter(ContentLibrary.item_type == item_type)

    # Filter by validity date
    if valid_on:
        query = query.filter(
            and_(
                or_(ContentLibrary.valid_from == None, ContentLibrary.valid_from <= valid_on),
                or_(ContentLibrary.valid_until == None, ContentLibrary.valid_until >= valid_on)
            )
        )

    # Search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                ContentLibrary.title.ilike(search_pattern),
                ContentLibrary.customer_name.ilike(search_pattern)
            )
        )

    # Test data filter
    if not include_test_data:
        query = query.filter(ContentLibrary.is_test_data == False)

    # Get total count before pagination
    total = query.count()

    # Apply pagination and ordering
    items = query.order_by(ContentLibrary.title).offset(offset).limit(limit).all()

    return {
        "items": [
            {
                "id": item.id,
                "asset_id": item.asset_id,
                "item_type": item.item_type,
                "title": item.title,
                "slug": item.slug,
                "duration": item.duration,
                "valid_from": item.valid_from.isoformat() if item.valid_from else None,
                "valid_until": item.valid_until.isoformat() if item.valid_until else None,
                "customer_name": item.customer_name,
                "priority": item.priority,
                "is_active": item.is_active,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "placement_count": len([p for p in item.placements if p.removed_at is None])
            }
            for item in items
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/{asset_id}")
async def get_library_item(
    asset_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Get a single library item by asset_id."""
    from models_content_library import ContentLibrary

    item = db.query(ContentLibrary).filter(ContentLibrary.asset_id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Library item {asset_id} not found")

    return {
        "id": item.id,
        "asset_id": item.asset_id,
        "organization_id": item.organization_id,
        "item_type": item.item_type,
        "title": item.title,
        "slug": item.slug,
        "script_content": item.script_content,
        "scratch_content": item.scratch_content,
        "duration": item.duration,
        "valid_from": item.valid_from.isoformat() if item.valid_from else None,
        "valid_until": item.valid_until.isoformat() if item.valid_until else None,
        "customer_name": item.customer_name,
        "customer_contact": item.customer_contact,
        "priority": item.priority,
        "is_active": item.is_active,
        "extra_data": item.extra_data,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None
    }


@router.post("/")
async def create_library_item(
    item_data: ContentLibraryCreate,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Create a new library item."""
    from models_content_library import ContentLibrary
    from models_v2 import Organization

    # Get default organization (for now, use first active org)
    # TODO: Get from user context when multi-org support is added
    org = db.query(Organization).filter(Organization.status == "active").first()
    if not org:
        # Fallback to any organization if none marked active
        org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No organization found")

    # Generate asset ID
    asset_id = AssetIDService.generate("LIB")  # LIB prefix for library items

    # Generate slug if not provided
    slug = item_data.slug
    if not slug:
        slug = item_data.title.lower().replace(" ", "-")[:100]

    # Create the library item
    library_item = ContentLibrary(
        asset_id=asset_id,
        organization_id=org.id,
        item_type=item_data.item_type,
        title=item_data.title,
        slug=slug,
        script_content=item_data.script_content,
        duration=item_data.duration,
        valid_from=item_data.valid_from,
        valid_until=item_data.valid_until,
        customer_name=item_data.customer_name,
        customer_contact=item_data.customer_contact,
        priority=item_data.priority,
        extra_data=item_data.extra_data,
        is_test_data=item_data.is_test_data,
        is_active=True
    )

    db.add(library_item)
    db.commit()
    db.refresh(library_item)

    return {
        "success": True,
        "asset_id": library_item.asset_id,
        "id": library_item.id,
        "message": f"Created library item: {library_item.title}"
    }


@router.patch("/{asset_id}")
async def update_library_item(
    asset_id: str,
    item_data: ContentLibraryUpdate,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Update a library item."""
    from models_content_library import ContentLibrary

    item = db.query(ContentLibrary).filter(ContentLibrary.asset_id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Library item {asset_id} not found")

    # Update fields that were provided
    update_data = item_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    return {
        "success": True,
        "asset_id": item.asset_id,
        "message": f"Updated library item: {item.title}"
    }


@router.delete("/{asset_id}")
async def delete_library_item(
    asset_id: str,
    hard_delete: bool = Query(False, description="Permanently delete instead of soft delete"),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Delete a library item (soft delete by default)."""
    from models_content_library import ContentLibrary

    item = db.query(ContentLibrary).filter(ContentLibrary.asset_id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Library item {asset_id} not found")

    if hard_delete:
        db.delete(item)
        db.commit()
        return {"success": True, "message": f"Permanently deleted library item: {asset_id}"}
    else:
        item.is_active = False
        db.commit()
        return {"success": True, "message": f"Deactivated library item: {asset_id}"}


# =====================
# Usage History Endpoint
# =====================

@router.get("/{asset_id}/usage")
async def get_library_item_usage(
    asset_id: str,
    include_removed: bool = Query(True, description="Include removed placements"),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Get usage history for a library item."""
    from models_content_library import ContentLibrary, ContentPlacement

    item = db.query(ContentLibrary).filter(ContentLibrary.asset_id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Library item {asset_id} not found")

    query = db.query(ContentPlacement).filter(ContentPlacement.library_item_id == item.id)

    if not include_removed:
        query = query.filter(ContentPlacement.removed_at == None)

    placements = query.order_by(ContentPlacement.placed_at.desc()).all()

    return {
        "asset_id": asset_id,
        "title": item.title,
        "total_placements": len(placements),
        "active_placements": len([p for p in placements if p.removed_at is None]),
        "placements": [
            {
                "id": p.id,
                "episode_number": p.episode_number,
                "airdate": p.airdate.isoformat() if p.airdate else None,
                "order_in_rundown": p.order_in_rundown,
                "placed_at": p.placed_at.isoformat() if p.placed_at else None,
                "removed_at": p.removed_at.isoformat() if p.removed_at else None,
                "removed_before_air": p.removed_before_air,
                "placement_notes": p.placement_notes
            }
            for p in placements
        ]
    }


# =====================
# Placement Endpoints (Episode-specific)
# =====================

@router.post("/place/{episode_number}")
async def place_library_content(
    episode_number: str,
    placement_data: ContentPlacementCreate,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Place a library item in an episode's rundown."""
    from models_content_library import ContentLibrary, ContentPlacement
    from models_v2 import Episode, Rundown

    # Find the library item
    library_item = db.query(ContentLibrary).filter(
        ContentLibrary.asset_id == placement_data.library_asset_id,
        ContentLibrary.is_active == True
    ).first()
    if not library_item:
        raise HTTPException(status_code=404, detail=f"Library item {placement_data.library_asset_id} not found or inactive")

    # Find the episode and rundown
    episode = db.query(Episode).filter(Episode.episode_number == episode_number).first()
    if not episode:
        raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

    rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
    if not rundown:
        raise HTTPException(status_code=404, detail=f"Rundown for episode {episode_number} not found")

    # Create content snapshot
    content_snapshot = {
        "title": library_item.title,
        "slug": library_item.slug,
        "script_content": library_item.script_content,
        "duration": library_item.duration,
        "customer_name": library_item.customer_name,
        "priority": library_item.priority,
        "extra_data": library_item.extra_data,
        "snapshot_at": datetime.utcnow().isoformat()
    }

    # Create the placement
    placement = ContentPlacement(
        library_item_id=library_item.id,
        rundown_id=rundown.id,
        show_id=episode.show_id,
        episode_number=episode_number,
        order_in_rundown=placement_data.order_in_rundown,
        content_snapshot=content_snapshot,
        airdate=placement_data.airdate or episode.airdate,
        placement_notes=placement_data.placement_notes
    )

    db.add(placement)
    db.commit()
    db.refresh(placement)

    return {
        "success": True,
        "placement_id": placement.id,
        "library_asset_id": library_item.asset_id,
        "episode_number": episode_number,
        "order_in_rundown": placement.order_in_rundown,
        "message": f"Placed '{library_item.title}' in episode {episode_number}"
    }


@router.delete("/placement/{placement_id}")
async def remove_placement(
    placement_id: int,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Remove a library item from a rundown (soft delete - preserves history)."""
    from models_content_library import ContentPlacement

    placement = db.query(ContentPlacement).filter(ContentPlacement.id == placement_id).first()
    if not placement:
        raise HTTPException(status_code=404, detail=f"Placement {placement_id} not found")

    if placement.removed_at:
        raise HTTPException(status_code=400, detail="Placement already removed")

    # Determine if removed before airdate
    now = datetime.utcnow()
    removed_before_air = placement.airdate is None or now < placement.airdate

    # Soft delete
    placement.removed_at = now
    placement.removed_before_air = removed_before_air

    db.commit()

    return {
        "success": True,
        "placement_id": placement_id,
        "removed_at": placement.removed_at.isoformat(),
        "removed_before_air": removed_before_air,
        "message": "Placement removed from rundown"
    }


# =====================
# Content Type Settings Endpoints
# =====================

@router.get("/type-settings/")
async def list_type_settings(
    include_core: bool = Query(True, description="Include core type settings"),
    include_custom: bool = Query(True, description="Include custom types"),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """List all content type settings."""
    from models_content_library import ContentTypeSettings

    query = db.query(ContentTypeSettings).filter(ContentTypeSettings.is_active == True)

    # Filter by core/custom
    if include_core and not include_custom:
        query = query.filter(ContentTypeSettings.is_core == True)
    elif include_custom and not include_core:
        query = query.filter(ContentTypeSettings.is_core == False)

    settings = query.order_by(ContentTypeSettings.sort_order).all()

    return {
        "settings": [
            {
                "id": s.id,
                "type_name": s.type_name,
                "display_name": s.display_name,
                "description": getattr(s, 'description', None),
                "color": s.color,
                "icon": s.icon,
                "is_core": getattr(s, 'is_core', True),
                "is_reusable": s.is_reusable,
                "default_duration": s.default_duration,
                "sort_order": s.sort_order,
                "is_active": s.is_active
            }
            for s in settings
        ]
    }


@router.get("/custom-types/")
async def list_custom_types(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """List only custom rundown item types (for merging with core types in frontend)."""
    from models_content_library import ContentTypeSettings

    custom_types = db.query(ContentTypeSettings).filter(
        ContentTypeSettings.is_core == False,
        ContentTypeSettings.is_active == True
    ).order_by(ContentTypeSettings.sort_order).all()

    return {
        "custom_types": [
            {
                "type_name": ct.type_name,
                "display_name": ct.display_name,
                "description": getattr(ct, 'description', None),
                "color": ct.color,
                "icon": ct.icon,
                "is_reusable": ct.is_reusable,
                "default_duration": ct.default_duration,
                "sort_order": ct.sort_order
            }
            for ct in custom_types
        ]
    }


@router.post("/custom-types/")
async def create_custom_type(
    type_data: CustomTypeCreate,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Create a new custom rundown item type."""
    from models_content_library import ContentTypeSettings

    # Core type values (hardcoded - matches frontend CORE_ITEM_TYPES)
    CORE_TYPE_VALUES = [
        'segment', 'ad', 'promo', 'cta', 'trans', 'coldopen',
        'pkg', 'vo', 'sot', 'interview', 'live', 'tease', 'tag',
        'music', 'gfx', 'fsq', 'nat', 'vox', 'credits',
        'weather', 'sports', 'brief', 'reader'
    ]

    # Check if type_name conflicts with core types
    if type_data.type_name in CORE_TYPE_VALUES:
        raise HTTPException(status_code=400, detail=f"Type '{type_data.type_name}' is a reserved core type")

    # Also check database for existing type
    existing = db.query(ContentTypeSettings).filter(
        ContentTypeSettings.type_name == type_data.type_name
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail=f"Type '{type_data.type_name}' already exists")

    # Get max sort_order for custom types
    max_order = db.query(func.max(ContentTypeSettings.sort_order)).filter(
        ContentTypeSettings.is_core == False
    ).scalar() or 100

    # Create custom type
    custom_type = ContentTypeSettings(
        type_name=type_data.type_name,
        display_name=type_data.display_name,
        description=type_data.description,
        color=type_data.color,
        icon=type_data.icon,
        is_core=False,  # Always false for custom types
        is_reusable=type_data.is_reusable,
        default_duration=type_data.default_duration,
        sort_order=max_order + 1,
        is_active=True
    )

    db.add(custom_type)
    db.commit()
    db.refresh(custom_type)

    return {
        "success": True,
        "type_name": custom_type.type_name,
        "message": f"Created custom type: {custom_type.display_name}"
    }


@router.delete("/custom-types/{type_name}")
async def delete_custom_type(
    type_name: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Delete a custom rundown item type (cannot delete core types)."""
    from models_content_library import ContentTypeSettings

    type_setting = db.query(ContentTypeSettings).filter(
        ContentTypeSettings.type_name == type_name
    ).first()

    if not type_setting:
        raise HTTPException(status_code=404, detail=f"Type '{type_name}' not found")

    if getattr(type_setting, 'is_core', True):
        raise HTTPException(status_code=403, detail="Cannot delete core rundown item types")

    # Soft delete
    type_setting.is_active = False
    db.commit()

    return {
        "success": True,
        "type_name": type_name,
        "message": f"Deleted custom type: {type_name}"
    }


@router.patch("/type-settings/{type_name}")
async def update_type_settings(
    type_name: str,
    settings_data: ContentTypeSettingsUpdate,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Update content type settings."""
    from models_content_library import ContentTypeSettings

    settings = db.query(ContentTypeSettings).filter(ContentTypeSettings.type_name == type_name).first()
    if not settings:
        raise HTTPException(status_code=404, detail=f"Type settings for '{type_name}' not found")

    update_data = settings_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)

    return {
        "success": True,
        "type_name": type_name,
        "is_reusable": settings.is_reusable,
        "message": f"Updated settings for {type_name}"
    }


@router.post("/type-settings/seed")
async def seed_type_settings(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Seed default content type settings for CORE types (run once during setup).
    These are behavior flags (is_reusable) for core types, not type definitions.
    Custom types are added separately via POST /custom-types/
    """
    from models_content_library import ContentTypeSettings

    # Core type settings - behavior flags for core rundown item types
    # is_core=True means these are settings for Core Rundown Items
    core_type_settings = [
        {"type_name": "segment", "display_name": "Segment", "is_reusable": False, "sort_order": 1},
        {"type_name": "coldopen", "display_name": "Cold Open", "is_reusable": False, "sort_order": 2},
        {"type_name": "interview", "display_name": "Interview", "is_reusable": False, "sort_order": 4},
        {"type_name": "advertisement", "display_name": "Advertisement", "is_reusable": True, "sort_order": 5},
        {"type_name": "promo", "display_name": "Promo", "is_reusable": True, "sort_order": 6},
        {"type_name": "cta", "display_name": "Call to Action", "is_reusable": True, "sort_order": 7},
        {"type_name": "trans", "display_name": "Transition", "is_reusable": False, "sort_order": 8},
        {"type_name": "reader", "display_name": "Reader", "is_reusable": False, "sort_order": 11},
        {"type_name": "tease", "display_name": "Tease", "is_reusable": False, "sort_order": 12},
    ]

    created = 0
    skipped = 0
    updated = 0

    for type_data in core_type_settings:
        existing = db.query(ContentTypeSettings).filter(
            ContentTypeSettings.type_name == type_data["type_name"]
        ).first()

        if existing:
            # Update existing to ensure is_core is set
            if not getattr(existing, 'is_core', False):
                existing.is_core = True
                updated += 1
            skipped += 1
            continue

        settings = ContentTypeSettings(
            type_name=type_data["type_name"],
            display_name=type_data["display_name"],
            is_core=True,  # Mark as Core Rundown Item setting
            is_reusable=type_data["is_reusable"],
            sort_order=type_data["sort_order"],
            is_active=True
        )
        db.add(settings)
        created += 1

    db.commit()

    return {
        "success": True,
        "created": created,
        "skipped": skipped,
        "updated": updated,
        "message": f"Seeded {created} core type settings ({skipped} already existed, {updated} updated to is_core=True)"
    }
