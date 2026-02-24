"""
MP3 Encoding Profiles API Router
Manages user-defined MP3 encoding profiles for episode audio export.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import get_db
from auth.utils import get_current_user_or_key
from models_episode import (
    Mp3EncodingProfile,
    Mp3EncodingProfileCreate,
    Mp3EncodingProfileUpdate,
    Mp3EncodingProfileResponse,
)
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mp3-profiles"])


@router.get("/", response_model=List[Mp3EncodingProfileResponse])
async def list_mp3_profiles(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """List all MP3 encoding profiles with optional filtering."""
    try:
        query = db.query(Mp3EncodingProfile)

        if is_active is not None:
            query = query.filter(Mp3EncodingProfile.is_active == is_active)

        profiles = query.order_by(
            Mp3EncodingProfile.sort_order,
            Mp3EncodingProfile.name
        ).all()
        return profiles

    except Exception as e:
        logger.error(f"Error listing MP3 profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/default", response_model=Mp3EncodingProfileResponse)
async def get_default_mp3_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get the default MP3 encoding profile."""
    try:
        profile = db.query(Mp3EncodingProfile).filter(
            and_(
                Mp3EncodingProfile.is_default == True,
                Mp3EncodingProfile.is_active == True
            )
        ).first()

        if not profile:
            # Fall back to first active profile
            profile = db.query(Mp3EncodingProfile).filter(
                Mp3EncodingProfile.is_active == True
            ).order_by(Mp3EncodingProfile.sort_order).first()

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="No MP3 encoding profiles configured"
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting default MP3 profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profile_id}", response_model=Mp3EncodingProfileResponse)
async def get_mp3_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get a specific MP3 encoding profile."""
    try:
        profile = db.query(Mp3EncodingProfile).filter(
            Mp3EncodingProfile.id == profile_id
        ).first()

        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"MP3 profile {profile_id} not found"
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MP3 profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Mp3EncodingProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_mp3_profile(
    profile_data: Mp3EncodingProfileCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Create a new MP3 encoding profile."""
    try:
        # Check for duplicate name
        existing = db.query(Mp3EncodingProfile).filter(
            Mp3EncodingProfile.name == profile_data.name
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Profile '{profile_data.name}' already exists"
            )

        # If this is set as default, unset other defaults
        if profile_data.is_default:
            db.query(Mp3EncodingProfile).filter(
                Mp3EncodingProfile.is_default == True
            ).update({"is_default": False})

        profile = Mp3EncodingProfile(**profile_data.model_dump())
        db.add(profile)
        db.commit()
        db.refresh(profile)

        logger.info(f"Created MP3 profile: {profile.name} (ID: {profile.id})")
        return profile

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating MP3 profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{profile_id}", response_model=Mp3EncodingProfileResponse)
async def update_mp3_profile(
    profile_id: int,
    profile_data: Mp3EncodingProfileUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Update an existing MP3 encoding profile."""
    try:
        profile = db.query(Mp3EncodingProfile).filter(
            Mp3EncodingProfile.id == profile_id
        ).first()

        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"MP3 profile {profile_id} not found"
            )

        # Check for name conflict if name is changing
        if profile_data.name and profile_data.name != profile.name:
            existing = db.query(Mp3EncodingProfile).filter(
                and_(
                    Mp3EncodingProfile.name == profile_data.name,
                    Mp3EncodingProfile.id != profile_id
                )
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Profile '{profile_data.name}' already exists"
                )

        # If setting as default, unset other defaults
        if profile_data.is_default:
            db.query(Mp3EncodingProfile).filter(
                and_(
                    Mp3EncodingProfile.is_default == True,
                    Mp3EncodingProfile.id != profile_id
                )
            ).update({"is_default": False})

        for field, value in profile_data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)

        db.commit()
        db.refresh(profile)

        logger.info(f"Updated MP3 profile: {profile.name} (ID: {profile.id})")
        return profile

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating MP3 profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mp3_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Delete an MP3 encoding profile."""
    try:
        profile = db.query(Mp3EncodingProfile).filter(
            Mp3EncodingProfile.id == profile_id
        ).first()

        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"MP3 profile {profile_id} not found"
            )

        profile_name = profile.name
        db.delete(profile)
        db.commit()

        logger.info(f"Deleted MP3 profile: {profile_name} (ID: {profile_id})")
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting MP3 profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
