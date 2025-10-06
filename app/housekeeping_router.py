"""
API endpoints for housekeeping and integrity checking
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any
from database import get_db
from auth.utils import get_current_user_or_key
from housekeeping_service import HousekeepingService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/housekeeping", tags=["housekeeping"])


@router.post("/active-edit/register")
async def register_active_edit(
    asset_id: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Register that an item is currently being edited"""
    try:
        HousekeepingService.register_active_edit(asset_id)
        return {
            'status': 'success',
            'asset_id': asset_id,
            'message': f'Registered active edit for {asset_id}'
        }
    except Exception as e:
        logger.error(f"Error registering active edit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/active-edit/unregister")
async def unregister_active_edit(
    asset_id: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Unregister that an item is no longer being edited"""
    try:
        HousekeepingService.unregister_active_edit(asset_id)
        return {
            'status': 'success',
            'asset_id': asset_id,
            'message': f'Unregistered active edit for {asset_id}'
        }
    except Exception as e:
        logger.error(f"Error unregistering active edit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active-edit/list")
async def list_active_edits(
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Get list of currently active edit sessions"""
    try:
        active_assets = HousekeepingService.get_actively_edited_assets()
        return {
            'count': len(active_assets),
            'asset_ids': list(active_assets)
        }
    except Exception as e:
        logger.error(f"Error listing active edits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrity-check")
async def run_integrity_check(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """
    Run all integrity checks and return detailed report.

    Checks for:
    - Duplicate slugs within same episode
    - Identical script content (likely corruption)
    - Orphaned rundown items
    - Order conflicts
    - Missing asset IDs
    """
    try:
        report = await HousekeepingService.run_all_checks(db)
        return report
    except Exception as e:
        logger.error(f"Error running integrity checks: {e}")
        raise HTTPException(status_code=500, detail=f"Integrity check failed: {str(e)}")


@router.get("/integrity-check/duplicates")
async def check_duplicates_only(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Check for duplicate slugs only"""
    try:
        issues = HousekeepingService.check_duplicate_slugs(db)
        return {
            'timestamp': HousekeepingService.check_duplicate_slugs.__name__,
            'count': len(issues),
            'issues': [issue.to_dict() for issue in issues]
        }
    except Exception as e:
        logger.error(f"Error checking duplicates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrity-check/script-corruption")
async def check_script_corruption(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Check for identical script content across multiple items"""
    try:
        issues = HousekeepingService.check_identical_script_content(db)
        return {
            'timestamp': HousekeepingService.check_identical_script_content.__name__,
            'count': len(issues),
            'issues': [issue.to_dict() for issue in issues]
        }
    except Exception as e:
        logger.error(f"Error checking script corruption: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrity-check/orphans")
async def check_orphans(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Check for orphaned rundown items"""
    try:
        issues = HousekeepingService.check_orphaned_rundown_items(db)
        return {
            'timestamp': HousekeepingService.check_orphaned_rundown_items.__name__,
            'count': len(issues),
            'issues': [issue.to_dict() for issue in issues]
        }
    except Exception as e:
        logger.error(f"Error checking orphans: {e}")
        raise HTTPException(status_code=500, detail=str(e))
