"""
Sibling-tool configuration endpoints (showtime / media-prep / media-distribute).

v1: per-tool base URL + enabled toggle + a live reachability probe. Stored in the
existing api_configs table (workflow='integrations', category='sibling_tool',
service=<tool>, config_key in {base_url, enabled}). Mirrors the established
api_configs pattern so it shows up alongside other service config.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import logging

from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from auth.utils import get_current_user_or_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["settings", "tools"])

# The sibling tools show-build coordinates with. Extend as the ecosystem grows.
KNOWN_TOOLS = ("showtime", "media-prep", "media-distribute")
WORKFLOW = "integrations"
CATEGORY = "sibling_tool"


class ToolConfigIn(BaseModel):
    base_url: Optional[str] = None
    enabled: bool = True


def _read_tool(db: Session, tool: str) -> Dict[str, Any]:
    rows = db.execute(text(
        "SELECT config_key, config_value FROM api_configs "
        "WHERE workflow=:w AND category=:c AND service=:s"
    ), {"w": WORKFLOW, "c": CATEGORY, "s": tool}).fetchall()
    cfg = {k: v for k, v in rows}
    return {
        "tool": tool,
        "base_url": cfg.get("base_url"),
        "enabled": (cfg.get("enabled", "true") == "true"),
    }


def _write_kv(db: Session, tool: str, key: str, value: str) -> None:
    """Upsert one api_configs row for a tool."""
    existing = db.execute(text(
        "SELECT id FROM api_configs WHERE workflow=:w AND category=:c "
        "AND service=:s AND config_key=:k"
    ), {"w": WORKFLOW, "c": CATEGORY, "s": tool, "k": key}).fetchone()
    if existing:
        db.execute(text(
            "UPDATE api_configs SET config_value=:v WHERE id=:id"
        ), {"v": value, "id": existing[0]})
    else:
        db.execute(text(
            "INSERT INTO api_configs (workflow, category, service, config_key, config_value) "
            "VALUES (:w, :c, :s, :k, :v)"
        ), {"w": WORKFLOW, "c": CATEGORY, "s": tool, "k": key, "v": value})


@router.get("/tools")
async def list_tools(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Config for all known sibling tools."""
    return [_read_tool(db, t) for t in KNOWN_TOOLS]


@router.put("/tools/{tool}")
async def save_tool(
    tool: str,
    body: ToolConfigIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_or_key),
) -> Dict[str, Any]:
    """Save a sibling tool's base URL + enabled flag."""
    if tool not in KNOWN_TOOLS:
        raise HTTPException(status_code=400, detail=f"Unknown tool '{tool}'")
    if body.base_url is not None:
        _write_kv(db, tool, "base_url", body.base_url)
    _write_kv(db, tool, "enabled", "true" if body.enabled else "false")
    db.commit()
    return _read_tool(db, tool)


@router.get("/tools/{tool}/health")
async def tool_health(tool: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Probe a tool's base URL for reachability (best-effort, short timeout)."""
    if tool not in KNOWN_TOOLS:
        raise HTTPException(status_code=400, detail=f"Unknown tool '{tool}'")
    cfg = _read_tool(db, tool)
    url = cfg.get("base_url")
    if not url:
        return {"tool": tool, "reachable": False, "detail": "no base_url configured"}
    import httpx
    # Track an auth failure separately: a node that answers but rejects login
    # (401/403) is "reachable but not authorized" — a distinct state from
    # plain unreachable, surfaced to the UI as its own (throbbing) status.
    auth_failed = None
    for path in ("/health", "/api/health", "/"):
        try:
            with httpx.Client(timeout=3.0, verify=False) as client:
                r = client.get(url.rstrip("/") + path)
                if r.status_code in (401, 403):
                    auth_failed = {"tool": tool, "reachable": True,
                                   "auth_failed": True, "status_code": r.status_code,
                                   "probe": path,
                                   "detail": f"login rejected ({r.status_code})"}
                    continue
                if r.status_code < 500:
                    return {"tool": tool, "reachable": True, "auth_failed": False,
                            "status_code": r.status_code, "probe": path}
        except Exception:  # noqa: BLE001
            continue
    if auth_failed is not None:
        return auth_failed
    return {"tool": tool, "reachable": False, "auth_failed": False,
            "detail": "no successful probe"}
