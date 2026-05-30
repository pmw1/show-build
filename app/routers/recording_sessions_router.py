"""Read API for recording sessions written by showtime.

Write path lives in routers/episodes/metadata_router.py
(PUT /api/episodes/{n}/save-episode with episode_metadata.recording_manifest).
This router provides the read counterparts so a future "Recording
History" panel or any other consumer can browse sessions, takes,
markers, and cue-fires.

All endpoints are unauthenticated for now, mirroring the GET /rundown
pattern. Add auth in a follow-up if write-path RBAC ever extends to
read.

See docs/SHOWTIME_INTEGRATION_ANALYSIS.md.
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.recording import (
    RecordingSession, RecordingTake, TakeMarker, TakeCueFire,
)
from models.episode import Episode

router = APIRouter()


def _session_summary(s: RecordingSession) -> Dict[str, Any]:
    return {
        "id": s.id,
        "episode_id": s.episode_id,
        "session_uuid": s.session_uuid,
        "session_kind": s.session_kind,
        "status": s.status,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "ended_at": s.ended_at.isoformat() if s.ended_at else None,
        "operator": s.operator,
        "host_machine": s.host_machine,
        "vmix_version": s.vmix_version,
        "showtime_version": s.showtime_version,
        "take_count": s.take_count,
        "total_duration_seconds": s.total_duration_seconds,
        "recording_root_path": s.recording_root_path,
        "notes": s.notes,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _take_detail(t: RecordingTake) -> Dict[str, Any]:
    return {
        "id": t.id,
        "session_id": t.session_id,
        "rundown_item_id": t.rundown_item_id,
        "filename": t.filename,
        "category": t.category,
        "block_letter": t.block_letter,
        "segment_number": t.segment_number,
        "take_number": t.take_number,
        "pickup_number": t.pickup_number,
        "status": t.status,
        "started_at_wallclock": (
            t.started_at_wallclock.isoformat()
            if t.started_at_wallclock else None
        ),
        "ended_at_wallclock": (
            t.ended_at_wallclock.isoformat()
            if t.ended_at_wallclock else None
        ),
        "duration_seconds": t.duration_seconds,
        "disk_band": t.disk_band,
        "is_pickup": t.pickup_replaces_from_seconds is not None,
        "pickup_replaces_from_seconds": t.pickup_replaces_from_seconds,
        "pickup_back_seconds": t.pickup_back_seconds,
        "pickup_splices_into_filename": t.pickup_splices_into_filename,
        "operator_note": t.operator_note,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


def _marker_detail(m: TakeMarker) -> Dict[str, Any]:
    return {
        "id": m.id,
        "take_id": m.take_id,
        "kind": m.kind,
        "offset_seconds": m.offset_seconds,
        "wallclock": m.wallclock.isoformat() if m.wallclock else None,
        "note": m.note,
    }


def _cue_fire_detail(c: TakeCueFire) -> Dict[str, Any]:
    return {
        "id": c.id,
        "take_id": c.take_id,
        "rundown_item_id": c.rundown_item_id,
        "cue_uuid": c.cue_uuid,
        "cue_type": c.cue_type,
        "cue_title": c.cue_title,
        "trigger": c.trigger,
        "offset_seconds": c.offset_seconds,
        "fired_at_wallclock": (
            c.fired_at_wallclock.isoformat()
            if c.fired_at_wallclock else None
        ),
        "status": c.status,
    }


@router.get("/episodes/{episode_number}/recording-sessions")
async def list_recording_sessions_for_episode(
    episode_number: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """List all recording sessions for an episode (summary form).

    Sessions are returned newest-first by started_at so the most recent
    session is the first entry — convenient for "show me the last
    session" lookups.
    """
    try:
        episode_num_int = int(episode_number)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode number")

    episode = db.query(Episode).filter(
        Episode.episode_number == episode_num_int
    ).first()
    if not episode:
        raise HTTPException(
            status_code=404,
            detail=f"Episode {episode_number} not found",
        )

    sessions = (
        db.query(RecordingSession)
        .filter(RecordingSession.episode_id == episode.id)
        .order_by(RecordingSession.started_at.desc())
        .all()
    )
    return {
        "episode_number": episode_number,
        "session_count": len(sessions),
        "sessions": [_session_summary(s) for s in sessions],
    }


@router.get("/recording-sessions/{session_id}")
async def get_recording_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Full session detail with takes + markers + cue-fires nested."""
    session = db.query(RecordingSession).filter(
        RecordingSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Recording session {session_id} not found",
        )

    takes = (
        db.query(RecordingTake)
        .filter(RecordingTake.session_id == session.id)
        .order_by(RecordingTake.started_at_wallclock.asc())
        .all()
    )
    take_ids = [t.id for t in takes]

    markers_by_take: Dict[int, List[Dict[str, Any]]] = {tid: [] for tid in take_ids}
    cue_fires_by_take: Dict[int, List[Dict[str, Any]]] = {tid: [] for tid in take_ids}
    if take_ids:
        for m in (
            db.query(TakeMarker)
            .filter(TakeMarker.take_id.in_(take_ids))
            .order_by(TakeMarker.offset_seconds.asc())
            .all()
        ):
            markers_by_take[m.take_id].append(_marker_detail(m))
        for c in (
            db.query(TakeCueFire)
            .filter(TakeCueFire.take_id.in_(take_ids))
            .order_by(TakeCueFire.fired_at_wallclock.asc())
            .all()
        ):
            cue_fires_by_take[c.take_id].append(_cue_fire_detail(c))

    takes_out = []
    for t in takes:
        d = _take_detail(t)
        d["markers"] = markers_by_take.get(t.id, [])
        d["cue_fires"] = cue_fires_by_take.get(t.id, [])
        takes_out.append(d)

    out = _session_summary(session)
    out["takes"] = takes_out
    return out


@router.get("/recording-sessions/{session_id}/takes")
async def list_recording_session_takes(
    session_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Just the takes list for a session (no markers/cue_fires).

    Cheaper than the full detail endpoint when only take-level info is
    needed (e.g. post-prod handoff listing).
    """
    session = db.query(RecordingSession).filter(
        RecordingSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Recording session {session_id} not found",
        )
    takes = (
        db.query(RecordingTake)
        .filter(RecordingTake.session_id == session.id)
        .order_by(RecordingTake.started_at_wallclock.asc())
        .all()
    )
    return {
        "session_id": session_id,
        "take_count": len(takes),
        "takes": [_take_detail(t) for t in takes],
    }
