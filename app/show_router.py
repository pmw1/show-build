"""
Show management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy import text
from auth.utils import get_current_user_or_key
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from utils.json_helpers import serialize_json_fields, ensure_json_fields, SHOW_JSON_FIELDS
from core import settings
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shows", tags=["shows"])

# Pydantic models for API
class ShowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    format: Optional[str] = None
    logo: Optional[str] = None
    poster: Optional[str] = None
    host: Optional[str] = None
    schedule: Optional[str] = None
    category: Optional[str] = None
    trailer: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[dict] = None
    api_keys: Optional[dict] = None
    settings: Optional[dict] = None

class ShowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    format: Optional[str] = None
    logo: Optional[str] = None
    poster: Optional[str] = None
    host: Optional[str] = None
    schedule: Optional[str] = None
    category: Optional[str] = None
    trailer: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[dict] = None
    api_keys: Optional[dict] = None
    settings: Optional[dict] = None

class ShowResponse(BaseModel):
    id: int
    asset_id: str
    organization_id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    settings: Optional[dict]

    class Config:
        from_attributes = True

@router.get("/", response_model=List[dict])
async def list_shows(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get shows - admins see all, users see only their organization's shows"""
    
    if current_user.get("access_level") == "admin":
        # Admins can see all shows
        sql_query = """
            SELECT s.id, s.asset_id, s.organization_id, s.name, s.slug, s.description, 
                   s.format, s.logo, s.poster, s.host, s.schedule, s.category, s.trailer, 
                   s.website, s.contact_name, s.contact_phone, s.contact_email,
                   s.social_links, s.api_keys, s.created_at, s.updated_at, s.settings, 
                   o.name as organization_name
            FROM shows s
            LEFT JOIN organizations o ON s.organization_id = o.id
            ORDER BY s.created_at DESC
        """
        result = db.execute(text(sql_query))
    else:
        # Regular users can only see their organization's shows
        user_result = db.execute(text("SELECT organization_id FROM users WHERE username = :username"), 
                                {"username": current_user.get("username")})
        user_row = user_result.first()
        
        if not user_row or not user_row.organization_id:
            return []  # User has no organization assigned
            
        sql_query = """
            SELECT s.id, s.asset_id, s.organization_id, s.name, s.slug, s.description, 
                   s.format, s.logo, s.poster, s.host, s.schedule, s.category, s.trailer, 
                   s.website, s.contact_name, s.contact_phone, s.contact_email,
                   s.social_links, s.api_keys, s.created_at, s.updated_at, s.settings, 
                   o.name as organization_name
            FROM shows s
            LEFT JOIN organizations o ON s.organization_id = o.id
            WHERE s.organization_id = :org_id
            ORDER BY s.created_at DESC
        """
        result = db.execute(text(sql_query), {"org_id": user_row.organization_id})
    
    shows = []
    for row in result:
        show = dict(row._mapping)
        # Convert date objects to strings for JSON serialization
        if show.get('created_at'):
            show['created_at'] = show['created_at'].isoformat()
        if show.get('updated_at'):
            show['updated_at'] = show['updated_at'].isoformat()
        shows.append(show)
    
    return shows

@router.post("/", response_model=dict)
async def create_show(
    show_data: ShowCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Create a new show - users create in their org, admins can specify org"""
    
    # Determine organization_id
    if current_user.get("access_level") == "admin":
        # For now, admins create shows in their own organization
        # Could be extended to allow specifying organization_id
        user_result = db.execute(text("SELECT organization_id FROM users WHERE username = :username"), 
                                {"username": current_user.get("username")})
        user_row = user_result.first()
        
        if not user_row or not user_row.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin user has no organization assigned"
            )
        organization_id = user_row.organization_id
    else:
        # Regular users create shows in their organization
        user_result = db.execute(text("SELECT organization_id FROM users WHERE username = :username"), 
                                {"username": current_user.get("username")})
        user_row = user_result.first()
        
        if not user_row or not user_row.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no organization assigned"
            )
        organization_id = user_row.organization_id
    
    # Generate AssetID for the show
    import random
    import string
    asset_id = 'SHOW' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=11))
    
    # Prepare data for insertion
    create_data = show_data.dict()
    create_data['organization_id'] = organization_id
    create_data['asset_id'] = asset_id
    create_data['created_at'] = datetime.utcnow()
    
    # Generate slug from name (optional)
    import re
    slug = re.sub(r'[^a-z0-9-]', '-', show_data.name.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    create_data['slug'] = slug if slug else None
    
    # Ensure JSON fields are properly serialized
    create_data = ensure_json_fields(create_data, SHOW_JSON_FIELDS)
    
    # Build insert query
    columns = list(create_data.keys())
    placeholders = [f":{col}" for col in columns]
    
    insert_sql = f"""
        INSERT INTO shows ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        RETURNING id
    """
    
    try:
        result = db.execute(text(insert_sql), create_data)
        show_id = result.scalar()
        db.commit()
        
        # Return the created show
        result = db.execute(text("""
            SELECT s.id, s.asset_id, s.organization_id, s.name, s.slug, s.description, 
                   s.format, s.logo, s.poster, s.host, s.schedule, s.category, s.trailer, 
                   s.website, s.contact_name, s.contact_phone, s.contact_email,
                   s.social_links, s.api_keys, s.created_at, s.updated_at, s.settings, 
                   o.name as organization_name
            FROM shows s
            LEFT JOIN organizations o ON s.organization_id = o.id
            WHERE s.id = :show_id
        """), {"show_id": show_id})
        
        row = result.first()
        if row:
            show = dict(row._mapping)
            # Convert date objects to strings for JSON serialization
            if show.get('created_at'):
                show['created_at'] = show['created_at'].isoformat()
            if show.get('updated_at'):
                show['updated_at'] = show['updated_at'].isoformat()
            
            logger.info(f"Show created: {show_id} by {current_user.get('username')}")
            return show
        else:
            raise HTTPException(status_code=404, detail="Show not found after creation")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating show: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create show"
        )

@router.get("/{show_id}", response_model=dict)
async def get_show(
    show_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get a specific show"""
    
    # Check if user has access to this show
    if current_user.get("access_level") != "admin":
        # Regular users can only access their organization's shows
        user_result = db.execute(text("SELECT organization_id FROM users WHERE username = :username"), 
                                {"username": current_user.get("username")})
        user_row = user_result.first()
        
        if user_row:
            # Check if show belongs to user's organization
            show_check = db.execute(text("SELECT organization_id FROM shows WHERE id = :show_id"), 
                                   {"show_id": show_id})
            show_row = show_check.first()
            
            if not show_row or show_row.organization_id != user_row.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - you can only view your organization's shows"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - no organization assigned"
            )
    
    # Get show with organization info
    result = db.execute(text("""
        SELECT s.id, s.asset_id, s.organization_id, s.name, s.slug, s.description, 
               s.format, s.logo, s.poster, s.host, s.schedule, s.category, s.trailer, 
               s.website, s.contact_name, s.contact_phone, s.contact_email,
               s.social_links, s.api_keys, s.created_at, s.updated_at, s.settings, 
               o.name as organization_name
        FROM shows s
        LEFT JOIN organizations o ON s.organization_id = o.id
        WHERE s.id = :show_id
    """), {"show_id": show_id})
    
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found"
        )
    
    show = dict(row._mapping)
    # Convert date objects to strings for JSON serialization
    if show.get('created_at'):
        show['created_at'] = show['created_at'].isoformat()
    if show.get('updated_at'):
        show['updated_at'] = show['updated_at'].isoformat()
    
    return show

@router.put("/{show_id}", response_model=dict)
async def update_show(
    show_id: int,
    show_data: ShowUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Update a show - admins can update any, users can update their organization's shows"""
    
    # Check if user has access to this show
    if current_user.get("access_level") != "admin":
        user_result = db.execute(text("SELECT organization_id FROM users WHERE username = :username"), 
                                {"username": current_user.get("username")})
        user_row = user_result.first()
        
        if user_row:
            # Check if show belongs to user's organization
            show_check = db.execute(text("SELECT organization_id FROM shows WHERE id = :show_id"), 
                                   {"show_id": show_id})
            show_row = show_check.first()
            
            if not show_row or show_row.organization_id != user_row.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - you can only update your organization's shows"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - no organization assigned"
            )
    
    # Check if show exists
    result = db.execute(text("SELECT id FROM shows WHERE id = :show_id"), {"show_id": show_id})
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found"
        )
    
    # Update fields that were provided
    update_data = show_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Serialize JSON fields in update data
    update_data = serialize_json_fields(update_data, SHOW_JSON_FIELDS)
    
    # Build dynamic update query
    set_clauses = []
    params = {"show_id": show_id, "updated_at": datetime.utcnow()}
    
    for field, value in update_data.items():
        set_clauses.append(f"{field} = :{field}")
        params[field] = value
    
    set_clauses.append("updated_at = :updated_at")
    
    update_sql = f"""
        UPDATE shows 
        SET {', '.join(set_clauses)}
        WHERE id = :show_id
    """
    
    try:
        db.execute(text(update_sql), params)
        db.commit()
        
        # Return updated show
        result = db.execute(text("""
            SELECT s.id, s.asset_id, s.organization_id, s.name, s.slug, s.description, 
                   s.format, s.logo, s.poster, s.host, s.schedule, s.category, s.trailer, 
                   s.website, s.contact_name, s.contact_phone, s.contact_email,
                   s.social_links, s.api_keys, s.created_at, s.updated_at, s.settings, 
                   o.name as organization_name
            FROM shows s
            LEFT JOIN organizations o ON s.organization_id = o.id
            WHERE s.id = :show_id
        """), {"show_id": show_id})
        
        row = result.first()
        if row:
            show = dict(row._mapping)
            # Convert date objects to strings for JSON serialization
            if show.get('created_at'):
                show['created_at'] = show['created_at'].isoformat()
            if show.get('updated_at'):
                show['updated_at'] = show['updated_at'].isoformat()
            
            logger.info(f"Show {show_id} updated by {current_user.get('username')}")
            return show
        else:
            raise HTTPException(status_code=404, detail="Show not found after update")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating show {show_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update show"
        )

@router.post("/{show_id}/upload-logo")
async def upload_show_logo(
    show_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Upload a logo file for a show"""
    
    # Check if user has access to this show
    if current_user.get("access_level") != "admin":
        user_result = db.execute(text("SELECT organization_id FROM users WHERE username = :username"), 
                                {"username": current_user.get("username")})
        user_row = user_result.first()
        
        if user_row:
            show_check = db.execute(text("SELECT organization_id, asset_id FROM shows WHERE id = :show_id"), 
                                   {"show_id": show_id})
            show_row = show_check.first()
            
            if not show_row or show_row.organization_id != user_row.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    else:
        # Admin - just get the show asset_id
        show_check = db.execute(text("SELECT asset_id FROM shows WHERE id = :show_id"), 
                               {"show_id": show_id})
        show_row = show_check.first()
    
    if not show_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found"
        )
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.allowed_image_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_image_extensions)}"
        )
    
    # Create logo directory if it doesn't exist
    logo_dir = settings.get_show_logos_path()
    logo_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename using show asset_id
    filename = f"{show_row.asset_id}_logo{file_ext}"
    file_path = logo_dir / filename
    
    # Save the file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update show record with logo path (relative to media root)
        relative_path = f"{settings.show_path}/{settings.show_logos_subdir}/{filename}"
        
        update_sql = """
            UPDATE shows 
            SET logo = :logo_path, updated_at = :updated_at
            WHERE id = :show_id
        """
        
        db.execute(text(update_sql), {
            "logo_path": relative_path,
            "updated_at": datetime.utcnow(),
            "show_id": show_id
        })
        db.commit()
        
        logger.info(f"Logo uploaded for show {show_id}: {filename}")
        
        return {
            "message": "Logo uploaded successfully",
            "filename": filename,
            "path": relative_path,
            "url": f"/api/media/{relative_path}"
        }
        
    except Exception as e:
        logger.error(f"Error uploading logo for show {show_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload logo"
        )