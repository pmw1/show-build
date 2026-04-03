"""
Episode history/snapshot endpoints router.
Handles segment and episode snapshot listing, reading, restoring, and force-snapshot.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from auth.utils import get_current_user_or_key
from database import get_db
from sqlalchemy.orm import Session
import logging

from ._shared import logger

router = APIRouter()


@router.get("/{episode_number}/history/segments/{item_id}")
async def list_segment_history(
    episode_number: str,
    item_id: int,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """List available segment snapshots for a rundown item."""
    from services.autosave_history import list_segment_snapshots
    snapshots = list_segment_snapshots(episode_number, item_id)
    return {"item_id": item_id, "episode": episode_number, "snapshots": snapshots}


@router.get("/{episode_number}/history/segments/{item_id}/{filename}")
async def read_segment_history(
    episode_number: str,
    item_id: int,
    filename: str,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Read a specific segment snapshot file."""
    from services.autosave_history import read_segment_snapshot
    snapshot = read_segment_snapshot(episode_number, filename)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Snapshot {filename} not found")
    return snapshot


@router.get("/{episode_number}/history/episode")
async def list_episode_history(
    episode_number: str,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """List available episode snapshots."""
    from services.autosave_history import list_episode_snapshots
    snapshots = list_episode_snapshots(episode_number)
    return {"episode": episode_number, "snapshots": snapshots}


@router.get("/{episode_number}/history/episode/{filename}")
async def read_episode_history(
    episode_number: str,
    filename: str,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Read a specific episode snapshot file."""
    from services.autosave_history import read_episode_snapshot
    snapshot = read_episode_snapshot(episode_number, filename)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Snapshot {filename} not found")
    return snapshot


@router.post("/{episode_number}/history/segments/restore/{filename}")
async def restore_segment_history(
    episode_number: str,
    filename: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Restore a segment from a filesystem snapshot (matched by item_id, index-agnostic)."""
    from services.autosave_history import restore_segment_from_snapshot
    result = restore_segment_from_snapshot(db, episode_number, filename)
    if not result:
        raise HTTPException(status_code=404, detail="Snapshot not found or item no longer exists")
    return {"success": True, **result}


@router.post("/{episode_number}/history/episode/restore/{filename}")
async def restore_episode_history(
    episode_number: str,
    filename: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Restore all segments from an episode snapshot (restores content and order)."""
    from services.autosave_history import restore_episode_from_snapshot
    result = restore_episode_from_snapshot(db, episode_number, filename)
    if not result:
        raise HTTPException(status_code=404, detail="Snapshot not found or no items to restore")
    return {"success": True, **result}


@router.post("/{episode_number}/history/episode/force-snapshot")
async def force_episode_snapshot(
    episode_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Force an immediate episode snapshot (bypasses throttle). Used before destructive operations like join."""
    from services.autosave_history import write_episode_snapshot
    from models_v2 import Episode, Rundown, RundownItem
    from pathlib import Path

    ep_num = str(episode_number).zfill(4)

    # Get the episode
    episode = db.query(Episode).filter(Episode.episode_number == ep_num).first()
    if not episode:
        raise HTTPException(status_code=404, detail=f"Episode {ep_num} not found")

    # Get all rundown items for this episode
    rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
    if not rundown:
        raise HTTPException(status_code=404, detail=f"No rundown found for episode {ep_num}")

    all_items = db.query(RundownItem).filter(
        RundownItem.rundown_id == rundown.id
    ).order_by(RundownItem.order_in_rundown).all()

    if not all_items:
        raise HTTPException(status_code=404, detail=f"No rundown items found for episode {ep_num}")

    filepath = write_episode_snapshot(
        episode_number=ep_num,
        episode_title=episode.title or "",
        rundown_items=all_items,
        force=True
    )

    if not filepath:
        raise HTTPException(status_code=500, detail="Failed to create snapshot")

    snapshot_name = f"Pre-Join {filepath.stem.split('_', 1)[1] if '_' in filepath.stem else filepath.stem}"

    return {
        "success": True,
        "snapshot_filename": filepath.name,
        "snapshot_name": snapshot_name,
        "item_count": len(all_items)
    }
