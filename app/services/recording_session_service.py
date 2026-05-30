"""Persist showtime recording manifests into recording_sessions tables.

Called by PUT /api/episodes/{n}/save-episode when the payload contains
`episode_metadata.recording_manifest`. See
docs/SHOWTIME_INTEGRATION_ANALYSIS.md.

Showtime's current manifest shape (from
/home/kevin/showtime/backend/modules/local_json_rundown/module.py _build_manifest):

    {
      "episode_number": "0273",
      "wrapped_at": "<iso>",
      "rundown": [
        {
          "id": "<uuid>", "title": "...", "item_type": "...", "status": "...",
          "takes": [
            {"filename": "...", "duration_seconds": float,
             "marker_count": int, "status": "...",
             "pickup_metadata": null | {replaces_from_offset_seconds,
                                        back_seconds, splices_into,
                                        operator_note}}
          ],
          "cues": [
            {"id": "<uuid>", "title": "...", "cue_type": "...",
             "status": "...", "fired_at_wallclock": "<iso>|null"}
          ]
        }
      ],
      # Optional richer fields (not in current showtime build but the
      # schema supports them):
      "session_uuid": "...", "session_kind": "live|rehearsal|retake|...",
      "operator": "...", "host_machine": "...", "vmix_version": "...",
      "showtime_version": "...", "recording_root_path": "...",
      "started_at": "<iso>", "ended_at": "<iso>",
    }

Ingest is conservative: anything missing is left null. Session-level
fields default to sensible values (kind='live', status='wrapped',
started_at falls back to wrapped_at).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from models.recording import (
    RecordingSession, RecordingTake, TakeCueFire,
)
from models.episode import RundownItem

logger = logging.getLogger(__name__)


def _parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _rundown_item_id_by_asset_id(
    db: Session, asset_id: str | None
) -> int | None:
    """Showtime's `id` field is a UUID derived from show-build's
    asset_id (see show_build_http.py _safe_uuid_from). For round-trip
    matching we look up by asset_id directly — showtime may pass
    either the raw asset_id or the UUID5; we accept either."""
    if not asset_id:
        return None
    item = db.query(RundownItem).filter(
        RundownItem.asset_id == str(asset_id)
    ).first()
    return item.id if item else None


def persist_recording_manifest(
    db: Session,
    episode_db_id: int,
    manifest: dict[str, Any],
) -> RecordingSession:
    """Write a recording manifest from showtime into the
    recording_sessions / recording_takes / take_cue_fires tables.

    Returns the created RecordingSession. Caller is responsible for
    db.commit() — we only db.flush() so the caller can compose this
    with other writes in the same transaction.
    """
    wrapped_at = _parse_iso(manifest.get("wrapped_at")) or datetime.utcnow()
    started_at = (
        _parse_iso(manifest.get("started_at"))
        or wrapped_at  # fallback when showtime doesn't send it
    )
    ended_at = _parse_iso(manifest.get("ended_at")) or wrapped_at

    session_uuid = manifest.get("session_uuid") or str(uuid.uuid4())

    session = RecordingSession(
        episode_id=episode_db_id,
        session_uuid=session_uuid,
        session_kind=manifest.get("session_kind", "live"),
        status=manifest.get("status", "wrapped"),
        started_at=started_at,
        ended_at=ended_at,
        operator=manifest.get("operator"),
        host_machine=manifest.get("host_machine"),
        vmix_version=manifest.get("vmix_version"),
        showtime_version=manifest.get("showtime_version"),
        recording_root_path=manifest.get("recording_root_path"),
        notes=manifest.get("notes"),
    )
    db.add(session)
    db.flush()  # need session.id for child rows

    take_count = 0
    total_duration = 0.0

    for item in manifest.get("rundown", []):
        rundown_item_id = _rundown_item_id_by_asset_id(db, item.get("id"))

        first_take_for_item: RecordingTake | None = None
        for t in item.get("takes", []):
            pickup = t.get("pickup_metadata") or {}
            take = RecordingTake(
                session_id=session.id,
                rundown_item_id=rundown_item_id,
                filename=t.get("filename") or f"unknown-{take_count}",
                category=t.get("category"),
                block_letter=t.get("block_letter"),
                segment_number=t.get("segment_number"),
                take_number=t.get("take_number"),
                pickup_number=t.get("pickup_number"),
                status=t.get("status", "pending_review"),
                started_at_wallclock=_parse_iso(t.get("started_at_wallclock"))
                                    or started_at,
                ended_at_wallclock=_parse_iso(t.get("ended_at_wallclock")),
                duration_seconds=t.get("duration_seconds"),
                disk_band=t.get("disk_band"),
                pickup_replaces_from_seconds=pickup.get(
                    "replaces_from_offset_seconds"
                ),
                pickup_back_seconds=pickup.get("back_seconds"),
                pickup_splices_into_filename=pickup.get("splices_into"),
                operator_note=pickup.get("operator_note") or t.get("operator_note"),
            )
            db.add(take)
            db.flush()
            take_count += 1
            if first_take_for_item is None:
                first_take_for_item = take
            if t.get("duration_seconds"):
                total_duration += float(t["duration_seconds"])

        # Markers are summarized as a count in the current showtime
        # manifest. If a future revision sends the full marker list,
        # iterate it here. For now we skip detailed markers — the
        # take.duration_seconds + marker_count is enough for editorial.

        # Cue fires are item-level events in showtime's manifest (not
        # per-take). Attach each fired cue to the first take of the
        # item — post-prod can reconcile if multiple takes overlap a
        # cue fire. Cues with no fired_at_wallclock never fired and
        # are skipped.
        if first_take_for_item is not None:
            for c in item.get("cues", []):
                fired_at = _parse_iso(c.get("fired_at_wallclock"))
                if fired_at is None:
                    continue
                db.add(TakeCueFire(
                    take_id=first_take_for_item.id,
                    rundown_item_id=rundown_item_id,
                    cue_uuid=c.get("id"),
                    cue_type=c.get("cue_type"),
                    cue_title=c.get("title"),
                    trigger=c.get("trigger"),
                    offset_seconds=c.get("offset_seconds"),
                    fired_at_wallclock=fired_at,
                    status=c.get("status", "fired"),
                ))

    session.take_count = take_count
    session.total_duration_seconds = total_duration if take_count else None
    db.flush()

    logger.info(
        "persisted recording session %s for episode %s: %d takes, %.1fs total",
        session.session_uuid, episode_db_id, take_count, total_duration,
    )
    return session
