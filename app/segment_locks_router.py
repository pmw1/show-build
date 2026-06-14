"""
Segment Locks Router - Pessimistic locking for rundown item segments
Prevents concurrent editing conflicts by locking segments during editing.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta, timezone
import logging

from database import get_db
from auth.utils import get_current_user_or_key
from models_v2 import RundownItem, SegmentLock
from models_user import User
from services.asset_id import AssetIDService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/locks", tags=["segment-locks"])

# Lock TTL settings. The client heartbeats every 15s (HEARTBEAT_INTERVAL_MS in
# useSegmentLock.js), so a 30s TTL keeps a live editor's lock alive (2 missed
# beats of slack) while ensuring an ABANDONED lock (tab closed without a clean
# release) auto-clears within ~30s instead of lingering a full minute and
# greying the row on other users (todo #41). cleanup_expired_locks runs on every
# lock query incl. the /active poll, so expiry is enforced promptly.
LOCK_TTL_SECONDS = 30  # Lock expires after 30 seconds without heartbeat
HEARTBEAT_EXTENSION_SECONDS = 30  # Heartbeat extends lock by 30 seconds


def get_user_display_name(user: User) -> str:
    """Get a display name for the user."""
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    return user.username


def cleanup_expired_locks(db: Session) -> int:
    """Remove all expired locks. Returns count of deleted locks."""
    now = datetime.now(timezone.utc)
    expired = db.query(SegmentLock).filter(SegmentLock.expires_at < now).all()
    count = len(expired)
    for lock in expired:
        db.delete(lock)
    if count > 0:
        db.commit()
        logger.info(f"Cleaned up {count} expired segment locks")
    return count


# IMPORTANT: Static routes (/my-locks, /active) must be defined BEFORE dynamic
# routes (/{asset_id}) or FastAPI interprets them as an asset_id.

@router.get("/active")
async def get_active_locks(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Snapshot of all currently-LIVE locks (todo #41). The rundown panel polls this
    on a short interval to render which segments are locked by other users. This
    is a cheap single query — NO streaming / long-held connection (an SSE design
    starved the gunicorn worker pool; polling keeps workers free).
    """
    cleanup_expired_locks(db)
    current_user_id = current_user.get("user_id") or current_user.get("id")
    locks = db.query(SegmentLock).all()
    out = []
    for lock in locks:
        holder = db.query(User).filter(User.id == lock.user_id).first()
        out.append({
            "rundown_item_asset_id": lock.rundown_item_asset_id,
            "holder_user_id": lock.user_id,
            "holder_username": get_user_display_name(holder) if holder else "Unknown",
            "held_by_me": lock.user_id == current_user_id,
            "expires_at": lock.expires_at.isoformat() if lock.expires_at else None,
        })
    return {"locks": out}


@router.get("/my-locks")
async def get_my_locks(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    List all locks held by the current user.
    Useful for cleanup on page unload or session end.
    """
    # First, clean up any expired locks
    cleanup_expired_locks(db)

    current_user_id = current_user.get("user_id") or current_user.get("id")
    if not current_user_id:
        raise HTTPException(status_code=401, detail="User ID not found in authentication context")

    locks = db.query(SegmentLock).filter(SegmentLock.user_id == current_user_id).all()

    return {
        "locks": [
            {
                "lock_asset_id": lock.asset_id,
                "rundown_item_asset_id": lock.rundown_item_asset_id,
                "locked_at": lock.locked_at.isoformat() if lock.locked_at else None,
                "expires_at": lock.expires_at.isoformat() if lock.expires_at else None
            }
            for lock in locks
        ]
    }


@router.delete("/my-locks")
async def release_all_my_locks(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Release all locks held by the current user.
    Useful for cleanup on logout or session end.
    """
    current_user_id = current_user.get("user_id") or current_user.get("id")
    if not current_user_id:
        raise HTTPException(status_code=401, detail="User ID not found in authentication context")

    locks = db.query(SegmentLock).filter(SegmentLock.user_id == current_user_id).all()
    count = len(locks)

    for lock in locks:
        db.delete(lock)

    db.commit()

    logger.info(f"Released {count} locks for user {current_user_id}")

    return {
        "success": True,
        "message": f"Released {count} locks"
    }


# Dynamic routes (with path parameters) must be defined AFTER static routes

@router.get("/{asset_id}")
async def get_lock_status(
    asset_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Check lock status for a rundown item.
    Returns lock info if locked, or indicates it's available.
    """
    # First, clean up any expired locks
    cleanup_expired_locks(db)

    # Check if the rundown item exists
    rundown_item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()
    if not rundown_item:
        raise HTTPException(status_code=404, detail="Rundown item not found")

    # Check for existing lock
    lock = db.query(SegmentLock).filter(SegmentLock.rundown_item_asset_id == asset_id).first()

    if not lock:
        return {
            "locked": False,
            "asset_id": asset_id,
            "available": True
        }

    # Get the user who holds the lock
    lock_holder = db.query(User).filter(User.id == lock.user_id).first()

    # Check if current user holds this lock
    current_user_id = current_user.get("user_id") or current_user.get("id")
    is_my_lock = lock.user_id == current_user_id

    return {
        "locked": True,
        "asset_id": asset_id,
        "available": False,
        "is_my_lock": is_my_lock,
        "locked_by": get_user_display_name(lock_holder) if lock_holder else "Unknown",
        "locked_by_id": lock.user_id,
        "locked_at": lock.locked_at.isoformat() if lock.locked_at else None,
        "expires_at": lock.expires_at.isoformat() if lock.expires_at else None,
        "lock_asset_id": lock.asset_id
    }


@router.post("/{asset_id}/acquire")
async def acquire_lock(
    asset_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Acquire a lock on a rundown item segment.
    Returns 423 Locked if already locked by another user.
    Returns 200 with lock info if successful or already owned by current user.
    """
    # First, clean up any expired locks
    cleanup_expired_locks(db)

    # Check if the rundown item exists
    rundown_item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()
    if not rundown_item:
        raise HTTPException(status_code=404, detail="Rundown item not found")

    current_user_id = current_user.get("user_id") or current_user.get("id")
    if not current_user_id:
        raise HTTPException(status_code=401, detail="User ID not found in authentication context")

    # Check for existing lock
    existing_lock = db.query(SegmentLock).filter(
        SegmentLock.rundown_item_asset_id == asset_id
    ).first()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=LOCK_TTL_SECONDS)

    if existing_lock:
        # If current user already holds this lock, extend it
        if existing_lock.user_id == current_user_id:
            existing_lock.expires_at = expires_at
            existing_lock.last_heartbeat = now
            db.commit()

            return {
                "success": True,
                "message": "Lock extended",
                "lock_asset_id": existing_lock.asset_id,
                "expires_at": expires_at.isoformat()
            }

        # Lock held by another user - return 423 Locked
        lock_holder = db.query(User).filter(User.id == existing_lock.user_id).first()
        raise HTTPException(
            status_code=423,  # Locked
            detail={
                "error": "Segment is locked by another user",
                "locked_by": get_user_display_name(lock_holder) if lock_holder else "Unknown",
                "locked_by_id": existing_lock.user_id,
                "locked_at": existing_lock.locked_at.isoformat() if existing_lock.locked_at else None,
                "expires_at": existing_lock.expires_at.isoformat() if existing_lock.expires_at else None
            }
        )

    # Create new lock
    lock_asset_id = AssetIDService.generate(entity_type="lock")

    new_lock = SegmentLock(
        asset_id=lock_asset_id,
        rundown_item_asset_id=asset_id,
        user_id=current_user_id,
        locked_at=now,
        expires_at=expires_at,
        last_heartbeat=now
    )

    db.add(new_lock)
    db.commit()

    logger.info(f"Lock acquired on {asset_id} by user {current_user_id}")

    return {
        "success": True,
        "message": "Lock acquired",
        "lock_asset_id": lock_asset_id,
        "expires_at": expires_at.isoformat()
    }


@router.post("/{asset_id}/take-over")
async def take_over_lock(
    asset_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Forcibly claim a segment lock, EVICTING the current holder (todo #41).
    Reassigns the lock to the requesting user. Returns the previous holder so
    the frontend can show the eviction notice; the evicted user learns of the
    eviction on their next heartbeat (which will report taken_over=True).
    """
    rundown_item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()
    if not rundown_item:
        raise HTTPException(status_code=404, detail="Rundown item not found")

    current_user_id = current_user.get("user_id") or current_user.get("id")
    if not current_user_id:
        raise HTTPException(status_code=401, detail="User ID not found in authentication context")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=LOCK_TTL_SECONDS)

    lock = db.query(SegmentLock).filter(
        SegmentLock.rundown_item_asset_id == asset_id
    ).first()

    evicted_user_id = None
    evicted_username = None
    if lock is not None:
        if lock.user_id != current_user_id:
            evicted_user_id = lock.user_id
            evicted_holder = db.query(User).filter(User.id == evicted_user_id).first()
            evicted_username = get_user_display_name(evicted_holder) if evicted_holder else "another user"
        # Reassign the existing lock row to the requester.
        lock.user_id = current_user_id
        lock.locked_at = now
        lock.expires_at = expires_at
        lock.last_heartbeat = now
    else:
        lock = SegmentLock(
            asset_id=AssetIDService.generate(entity_type="lock"),
            rundown_item_asset_id=asset_id,
            user_id=current_user_id,
            locked_at=now,
            expires_at=expires_at,
            last_heartbeat=now,
        )
        db.add(lock)

    db.commit()
    logger.info(
        f"Lock TAKEN OVER on {asset_id} by user {current_user_id} "
        f"(evicted user {evicted_user_id})"
    )

    return {
        "success": True,
        "message": "Lock taken over",
        "lock_asset_id": lock.asset_id,
        "expires_at": expires_at.isoformat(),
        "evicted_user_id": evicted_user_id,
        "evicted_username": evicted_username,
    }


@router.post("/{asset_id}/heartbeat")
async def heartbeat_lock(
    asset_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Extend lock TTL via heartbeat.
    Should be called every 15 seconds by the client.

    If the caller no longer holds the lock — because another user took it over
    (todo #41) or it expired and was reclaimed — return 409 with taken_over info
    so the client can show the eviction notice and flip to read-only.
    """
    current_user_id = current_user.get("user_id") or current_user.get("id")
    if not current_user_id:
        raise HTTPException(status_code=401, detail="User ID not found in authentication context")

    # The caller's own live lock?
    lock = db.query(SegmentLock).filter(
        and_(
            SegmentLock.rundown_item_asset_id == asset_id,
            SegmentLock.user_id == current_user_id
        )
    ).first()

    if not lock:
        # Did someone else take it over? Report that distinctly so the client
        # can render "You have been evicted from this Rundown Item by {username}".
        other = db.query(SegmentLock).filter(
            SegmentLock.rundown_item_asset_id == asset_id
        ).first()
        if other is not None:
            holder = db.query(User).filter(User.id == other.user_id).first()
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "taken_over",
                    "taken_over_by": get_user_display_name(holder) if holder else "another user",
                    "taken_over_by_id": other.user_id,
                },
            )
        raise HTTPException(status_code=404, detail="No lock found for this segment")

    # Extend the lock
    now = datetime.now(timezone.utc)
    lock.expires_at = now + timedelta(seconds=HEARTBEAT_EXTENSION_SECONDS)
    lock.last_heartbeat = now

    db.commit()

    return {
        "success": True,
        "message": "Lock extended",
        "expires_at": lock.expires_at.isoformat()
    }


@router.post("/{asset_id}/release")
async def release_lock(
    asset_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Release a lock on a rundown item segment.
    Only the lock holder can release the lock.
    """
    current_user_id = current_user.get("user_id") or current_user.get("id")
    if not current_user_id:
        raise HTTPException(status_code=401, detail="User ID not found in authentication context")

    # Find the lock
    lock = db.query(SegmentLock).filter(
        SegmentLock.rundown_item_asset_id == asset_id
    ).first()

    if not lock:
        # No lock exists - that's fine, return success
        return {
            "success": True,
            "message": "No lock to release"
        }

    # Verify ownership
    if lock.user_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot release lock owned by another user"
        )

    # Delete the lock
    db.delete(lock)
    db.commit()

    logger.info(f"Lock released on {asset_id} by user {current_user_id}")

    return {
        "success": True,
        "message": "Lock released"
    }
