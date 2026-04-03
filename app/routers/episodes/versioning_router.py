"""
Content versioning and autosave router.
Handles content versions and autosave operations for rundown items.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
from auth.utils import get_current_user_or_key
from database import get_db
from sqlalchemy.orm import Session
from datetime import datetime

from ._shared import EPISODES_ROOT, create_content_version, logger

router = APIRouter()


@router.post("/{episode_number}/rundown/{item_filename}/autosave")
async def autosave_rundown_item(
    episode_number: str,
    item_filename: str,
    content_data: dict,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Autosave rundown item content to autosave directory"""
    try:
        episode_path = EPISODES_ROOT / episode_number
        autosave_dir = episode_path / "rundown" / "autosave"

        # Create autosave directory if it doesn't exist
        if not autosave_dir.exists():
            autosave_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created autosave directory: {autosave_dir}")

        # Generate autosave filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = item_filename.replace('.md', '')
        autosave_filename = f"{base_name}_autosave_{timestamp}.md"
        autosave_path = autosave_dir / autosave_filename

        # Write autosave content
        with open(autosave_path, 'w', encoding='utf-8') as f:
            f.write(content_data.get('content', ''))

        return {
            "success": True,
            "message": f"Autosaved {item_filename}",
            "autosave_path": str(autosave_path),
            "timestamp": timestamp
        }

    except Exception as e:
        logging.error(f"Autosave failed for {episode_number}/{item_filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Autosave failed: {str(e)}"
        )


@router.put("/{episode_number}/rundown/{item_filename}/autosave")
async def update_autosave_current(
    episode_number: str,
    item_filename: str,
    content_data: dict,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Update current autosave version (overwrites existing autosave)"""
    try:
        episode_path = EPISODES_ROOT / episode_number
        autosave_dir = episode_path / "rundown" / "autosave"

        # Create autosave directory if it doesn't exist
        if not autosave_dir.exists():
            autosave_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created autosave directory: {autosave_dir}")

        # Use simple autosave filename (current version)
        base_name = item_filename.replace('.md', '')
        autosave_filename = f"{base_name}_autosave.md"
        autosave_path = autosave_dir / autosave_filename

        # Write autosave content (overwrite if exists)
        with open(autosave_path, 'w', encoding='utf-8') as f:
            f.write(content_data.get('content', ''))

        return {
            "success": True,
            "message": f"Autosave updated for {item_filename}",
            "autosave_path": str(autosave_path)
        }

    except Exception as e:
        logging.error(f"Autosave update failed for {episode_number}/{item_filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Autosave update failed: {str(e)}"
        )


# ============================================================================
# CONTENT VERSIONING ENDPOINTS
# ============================================================================

@router.get("/rundown-item/{asset_id}/versions")
async def get_content_versions(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Get version history for a rundown item."""
    from models_v2 import RundownItem, ContentVersion

    # Find the rundown item
    item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Rundown item {asset_id} not found")

    # Get all versions
    versions = db.query(ContentVersion).filter(
        ContentVersion.rundown_item_id == item.id
    ).order_by(ContentVersion.version_number.desc()).all()

    return {
        "asset_id": asset_id,
        "total_versions": len(versions),
        "versions": [
            {
                "id": v.id,
                "version_number": v.version_number,
                "content_length": v.content_length,
                "change_type": v.change_type,
                "change_summary": v.change_summary,
                "created_by": v.created_by,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "content_hash": v.content_hash
            }
            for v in versions
        ]
    }


@router.get("/rundown-item/{asset_id}/versions/{version_number}")
async def get_content_version_detail(
    asset_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Get full content of a specific version."""
    from models_v2 import RundownItem, ContentVersion

    # Find the rundown item
    item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Rundown item {asset_id} not found")

    # Get specific version
    version = db.query(ContentVersion).filter(
        ContentVersion.rundown_item_id == item.id,
        ContentVersion.version_number == version_number
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail=f"Version {version_number} not found")

    return {
        "id": version.id,
        "asset_id": asset_id,
        "version_number": version.version_number,
        "script_content": version.script_content,
        "content_length": version.content_length,
        "content_hash": version.content_hash,
        "change_type": version.change_type,
        "change_summary": version.change_summary,
        "created_by": version.created_by,
        "created_at": version.created_at.isoformat() if version.created_at else None
    }


@router.post("/rundown-item/{asset_id}/versions/{version_number}/restore")
async def restore_content_version(
    asset_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Restore a rundown item to a previous version."""
    from models_v2 import RundownItem, ContentVersion
    from datetime import datetime

    # Find the rundown item
    item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Rundown item {asset_id} not found")

    # Get version to restore
    version = db.query(ContentVersion).filter(
        ContentVersion.rundown_item_id == item.id,
        ContentVersion.version_number == version_number
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail=f"Version {version_number} not found")

    # Create a new version of the current content before restoring (safety snapshot)
    create_content_version(db, item, change_type="pre_restore", username=current_user.get('username') if isinstance(current_user, dict) else None)

    # Restore the old content
    item.script_content = version.script_content
    item.updated_at = datetime.now()

    # Create a version entry for the restore action
    username = current_user.get('username') if isinstance(current_user, dict) else None
    create_content_version(db, item, change_type="restore", username=username)

    db.commit()

    logger.info(f"Restored {asset_id} to version {version_number} by {username}")

    return {
        "success": True,
        "message": f"Restored to version {version_number}",
        "asset_id": asset_id,
        "restored_version": version_number,
        "content_length": version.content_length
    }
