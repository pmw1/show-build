"""
Production Roles Router
API endpoints for managing production roles (Host, Director, Teleprompter, etc.)
Used by NOTE cue "Note For" dropdown.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from database import get_db
from models_v2 import ProductionRole
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Production Roles"])


class ProductionRoleCreate(BaseModel):
    name: str
    display_order: Optional[int] = 0


class ProductionRoleUpdate(BaseModel):
    name: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_production_roles(db: Session = Depends(get_db)):
    """List all active production roles ordered by display_order."""
    try:
        roles = (
            db.query(ProductionRole)
            .filter(ProductionRole.is_active == True)
            .order_by(ProductionRole.display_order, ProductionRole.name)
            .all()
        )
        return {
            "success": True,
            "data": [
                {
                    "id": r.id,
                    "name": r.name,
                    "display_order": r.display_order,
                    "is_active": r.is_active,
                }
                for r in roles
            ],
        }
    except Exception as e:
        logger.error(f"Error listing production roles: {e}")
        raise HTTPException(status_code=500, detail="Failed to list production roles")


@router.post("/")
async def create_production_role(
    role_data: ProductionRoleCreate,
    db: Session = Depends(get_db),
):
    """Create a new production role."""
    try:
        existing = (
            db.query(ProductionRole)
            .filter(ProductionRole.name == role_data.name)
            .first()
        )
        if existing:
            if not existing.is_active:
                existing.is_active = True
                existing.display_order = role_data.display_order
                db.commit()
                db.refresh(existing)
                return {
                    "success": True,
                    "message": "Production role reactivated",
                    "data": {
                        "id": existing.id,
                        "name": existing.name,
                        "display_order": existing.display_order,
                        "is_active": existing.is_active,
                    },
                }
            raise HTTPException(
                status_code=400, detail="Production role with this name already exists"
            )

        new_role = ProductionRole(
            name=role_data.name,
            display_order=role_data.display_order,
        )
        db.add(new_role)
        db.commit()
        db.refresh(new_role)

        return {
            "success": True,
            "message": "Production role created",
            "data": {
                "id": new_role.id,
                "name": new_role.name,
                "display_order": new_role.display_order,
                "is_active": new_role.is_active,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating production role: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create production role")


@router.put("/{role_id}")
async def update_production_role(
    role_id: int,
    role_data: ProductionRoleUpdate,
    db: Session = Depends(get_db),
):
    """Update a production role."""
    try:
        role = db.query(ProductionRole).filter(ProductionRole.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Production role not found")

        for key, value in role_data.dict(exclude_unset=True).items():
            setattr(role, key, value)

        db.commit()
        db.refresh(role)

        return {
            "success": True,
            "message": "Production role updated",
            "data": {
                "id": role.id,
                "name": role.name,
                "display_order": role.display_order,
                "is_active": role.is_active,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating production role: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update production role")


@router.delete("/{role_id}")
async def delete_production_role(
    role_id: int,
    db: Session = Depends(get_db),
):
    """Soft-delete a production role (set is_active=False)."""
    try:
        role = db.query(ProductionRole).filter(ProductionRole.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Production role not found")

        role.is_active = False
        db.commit()

        return {"success": True, "message": "Production role deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting production role: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete production role")
