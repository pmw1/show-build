"""
Per-user preference storage backed by the `settings` table.

Reads and writes Settings rows scoped to the current user's id. A separate
"global" tier (rows with user_id=NULL) provides default values when a user
has no override; it is managed through the existing settings_colors_router
and other settings endpoints.

All endpoints require authentication. The user's id is taken from the JWT
or API-key principal returned by `get_current_user_or_key`.

Endpoints:
    GET    /api/user/prefs           -> {key: value, ...}  (current user only)
    GET    /api/user/prefs/{key}     -> {key, value, source}  (user, falls back to global)
    PUT    /api/user/prefs/{key}     -> set this user's override
    DELETE /api/user/prefs/{key}     -> remove this user's override (falls back to global on next read)

    GET    /api/user/prefs/_metadata           -> {key: {overridable, reason?}}
    PUT    /api/user/prefs/_metadata/{key}     -> admin-only: mark a key not-overridable
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any, Dict, Optional
import logging

from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from models.settings import Settings
from auth.utils import get_current_user_or_key, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user/prefs", tags=["user-prefs"])

# Single global Settings row that holds the {key: {overridable, reason?}} map.
META_KEY = "pref_overridable"
META_CATEGORY = "_meta"


class PrefValue(BaseModel):
    value: Any


def _user_id(current_user: dict) -> int:
    uid = current_user.get("id")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated principal has no user id (likely an API key)"
        )
    return int(uid)


def _get_row(db: Session, key: str, user_id: Optional[int]) -> Optional[Settings]:
    q = db.query(Settings).filter(Settings.key == key)
    if user_id is None:
        q = q.filter(Settings.user_id.is_(None))
    else:
        q = q.filter(Settings.user_id == user_id)
    return q.first()


# ---------------------------------------------------------------------------
# Metadata: which keys are overridable per-user
# ---------------------------------------------------------------------------

@router.get("/_metadata")
async def get_overridable_metadata(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user_or_key),
) -> Dict[str, Any]:
    row = _get_row(db, META_KEY, None)
    return row.value if row and isinstance(row.value, dict) else {}


@router.put("/_metadata/{key:path}")
async def set_overridable_metadata(
    key: str,
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    """Admin-only. Body: {overridable: bool, reason?: str}."""
    overridable = bool(body.get("overridable", True))
    reason = body.get("reason")
    row = _get_row(db, META_KEY, None)
    current = row.value if row and isinstance(row.value, dict) else {}
    entry: Dict[str, Any] = {"overridable": overridable}
    if reason:
        entry["reason"] = reason
    current[key] = entry
    if row:
        row.value = current
    else:
        row = Settings(key=META_KEY, category=META_CATEGORY, value=current, user_id=None)
        db.add(row)
    db.commit()
    return {"success": True, "key": key, **entry}


# ---------------------------------------------------------------------------
# Per-user preference CRUD
# ---------------------------------------------------------------------------

@router.get("")
async def list_user_prefs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
) -> Dict[str, Any]:
    """Return all preference rows owned by the current user as a flat map.

    Useful as a one-shot hydrate on login; clients should cache the result
    and call individual endpoints for subsequent writes.
    """
    uid = _user_id(current_user)
    rows = db.query(Settings).filter(Settings.user_id == uid).all()
    return {row.key: row.value for row in rows}


@router.get("/{key:path}")
async def get_user_pref(
    key: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
) -> Dict[str, Any]:
    """Return the current user's value for `key`, falling back to the
    global value if no override exists. The `source` field is "user" or
    "global" or "default" (when neither row exists)."""
    if key.startswith("_"):
        raise HTTPException(status_code=400, detail="Reserved key")
    uid = _user_id(current_user)
    row = _get_row(db, key, uid)
    if row is not None:
        return {"key": key, "value": row.value, "source": "user"}
    glob = _get_row(db, key, None)
    if glob is not None:
        return {"key": key, "value": glob.value, "source": "global"}
    return {"key": key, "value": None, "source": "default"}


def _is_admin(current_user: dict) -> bool:
    """Permissive admin check used to gate scope=global writes."""
    if current_user.get("access_level") == "admin":
        return True
    perms = current_user.get("permissions") or []
    if "admin.*" in perms or "*" in perms:
        return True
    return False


@router.put("/{key:path}")
async def set_user_pref(
    key: str,
    body: PrefValue,
    scope: str = "user",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
) -> Dict[str, Any]:
    """Write a preference for `key`.

    scope=user (default): writes the current user's override.
    scope=global: writes the GLOBAL default (admin only). Users without
    personal overrides will pick up the new value on their next hydrate.
    """
    if key.startswith("_"):
        raise HTTPException(status_code=400, detail="Reserved key")

    target_uid: Optional[int]
    if scope == "global":
        if not _is_admin(current_user):
            raise HTTPException(status_code=403, detail="Admin access required for global writes")
        target_uid = None
    else:
        target_uid = _user_id(current_user)

    row = _get_row(db, key, target_uid)
    if row:
        row.value = body.value
    else:
        category = "global_pref" if target_uid is None else "user_pref"
        row = Settings(key=key, value=body.value, user_id=target_uid, category=category)
        db.add(row)
    db.commit()
    return {"success": True, "key": key, "value": body.value, "source": "global" if target_uid is None else "user"}


@router.delete("/{key:path}")
async def delete_user_pref(
    key: str,
    scope: str = "user",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
) -> Dict[str, Any]:
    """Remove a preference row.

    scope=user (default): drop the current user's override; next reads
    fall through to global.
    scope=global: drop the GLOBAL default (admin only). Users with
    personal overrides keep their values; everyone else falls back to
    the in-code default.
    """
    if key.startswith("_"):
        raise HTTPException(status_code=400, detail="Reserved key")

    target_uid: Optional[int]
    if scope == "global":
        if not _is_admin(current_user):
            raise HTTPException(status_code=403, detail="Admin access required for global writes")
        target_uid = None
    else:
        target_uid = _user_id(current_user)

    row = _get_row(db, key, target_uid)
    if row:
        db.delete(row)
        db.commit()
    return {"success": True, "key": key, "scope": scope, "removed": row is not None}


# Re-export `text` to silence unused-import warnings if a future helper needs raw SQL.
_ = text
