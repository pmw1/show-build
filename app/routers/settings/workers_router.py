"""
Worker fleet settings endpoints.

CRUD over worker_definitions (the DB-backed worker fleet config) plus a live
status endpoint that reports which workers are actually online via Celery's
inspect API. v1 STORES definitions + shows status — it does NOT remotely deploy.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import logging

from database import get_db
from sqlalchemy.orm import Session
from auth.utils import get_current_user_or_key
from models.settings import WorkerDefinition

logger = logging.getLogger(__name__)

router = APIRouter(tags=["settings", "workers"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class WorkerDefIn(BaseModel):
    name: str
    image: str                      # container image / repo URL
    flavor: Optional[str] = None    # base | media-cpu | media-gpu
    host: Optional[str] = None
    queues: List[str] = []
    concurrency: int = 1
    gpu: Optional[str] = None
    mounts: Optional[List[str]] = None
    enabled: bool = True
    owner_tool: Optional[str] = None
    notes: Optional[str] = None


class WorkerDefOut(WorkerDefIn):
    id: int


def _to_out(w: WorkerDefinition) -> Dict[str, Any]:
    return {
        "id": w.id,
        "name": w.name,
        "image": w.image,
        "flavor": w.flavor,
        "host": w.host,
        "queues": w.queues or [],
        "concurrency": w.concurrency,
        "gpu": w.gpu,
        "mounts": w.mounts,
        "enabled": w.enabled,
        "owner_tool": w.owner_tool,
        "notes": w.notes,
    }


# ── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("/workers")
async def list_workers(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """All defined workers, newest first."""
    rows = db.query(WorkerDefinition).order_by(WorkerDefinition.id.desc()).all()
    return [_to_out(w) for w in rows]


@router.post("/workers")
async def create_worker(
    body: WorkerDefIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_or_key),
) -> Dict[str, Any]:
    """Define a new worker (name must be unique)."""
    if db.query(WorkerDefinition).filter(WorkerDefinition.name == body.name).first():
        raise HTTPException(status_code=409, detail=f"Worker '{body.name}' already exists")
    w = WorkerDefinition(**body.model_dump())
    db.add(w)
    db.commit()
    db.refresh(w)
    return _to_out(w)


@router.patch("/workers/{worker_id}")
async def update_worker(
    worker_id: int,
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_or_key),
) -> Dict[str, Any]:
    """Update any field of a worker definition."""
    w = db.query(WorkerDefinition).filter(WorkerDefinition.id == worker_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Worker not found")
    allowed = {"name", "image", "flavor", "host", "queues", "concurrency",
               "gpu", "mounts", "enabled", "owner_tool", "notes"}
    for k, v in body.items():
        if k in allowed:
            setattr(w, k, v)
    db.commit()
    db.refresh(w)
    return _to_out(w)


@router.delete("/workers/{worker_id}")
async def delete_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_or_key),
) -> Dict[str, Any]:
    """Delete a worker definition (does not stop a running worker)."""
    w = db.query(WorkerDefinition).filter(WorkerDefinition.id == worker_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Worker not found")
    db.delete(w)
    db.commit()
    return {"success": True, "deleted": worker_id}


# ── Live status (read-only; no deploy) ───────────────────────────────────────

@router.get("/workers/status")
async def workers_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Cross-reference defined workers against Celery's live worker list.

    Returns each online worker (from `celery inspect ping/active_queues`) and,
    for each DB-defined worker, whether a matching live worker is present.
    Read-only: never starts/stops anything.
    """
    online: Dict[str, Any] = {}
    try:
        from celery_app import celery_app
        insp = celery_app.control.inspect(timeout=2.0)
        ping = insp.ping() or {}
        queues = insp.active_queues() or {}
        for node, _ in ping.items():
            online[node] = {
                "node": node,
                "queues": sorted({q.get("name") for q in queues.get(node, [])}),
            }
    except Exception as exc:  # noqa: BLE001
        logger.warning("worker status inspect failed: %s", exc)
        return {"online": [], "defined": [], "error": str(exc)}

    defined = []
    for w in db.query(WorkerDefinition).all():
        # a live node name looks like "<name>@<host>"; match on the name part
        match = next((n for n in online if n.split("@")[0] == w.name), None)
        defined.append({
            **_to_out(w),
            "online": match is not None,
            "live_node": match,
        })
    return {"online": list(online.values()), "defined": defined}
