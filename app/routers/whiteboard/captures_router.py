"""
Capture inbox endpoints: external contributions to an episode's whiteboard.

Clients (capture-extension/, later a phone PWA share-target) POST one small
JSON capture; the server enriches it in the background (link preview, social
media download via yt-dlp / X API, remote media fetch into the pool) and the
whiteboard UI drains pending captures into real cards (see
docs/CAPTURE_INBOX_HANDOFF.md). Captures never touch whiteboard_items — the
full-replace board save makes direct external inserts unsafe.

Mounted standalone from main.py (NOT via routers/whiteboard/__init__.py) so it
shares the /api/whiteboard prefix without editing the package wiring.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import asyncio
import logging
import mimetypes
import re
import shutil
import uuid

from database import get_db, SessionLocal
from auth.utils import get_current_user_or_key
from models_capture import WhiteboardCapture
from models_whiteboard import AssetPoolFile, AssetTag
from services.asset_id import AssetIDService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whiteboard", tags=["whiteboard-captures"])

VALID_KINDS = {"selection", "link", "image", "video", "page", "screenshot"}
VALID_CUE_TYPES = {"sot", "vo", "nat"}
VALID_STATUSES = {"processing", "pending", "placed", "dismissed", "failed"}

# Local copy of the analyze-url service patterns (plus facebook, which yt-dlp
# also handles) — kept here so we never import route internals from the
# whiteboard package's actively-edited modules.
SOCIAL_PATTERNS = {
    "twitter": r"(twitter\.com|x\.com)",
    "youtube": r"(youtube\.com|youtu\.be)",
    "tiktok": r"tiktok\.com",
    "instagram": r"instagram\.com",
    "facebook": r"(facebook\.com|fb\.watch)",
    "rumble": r"rumble\.com",
    "soundcloud": r"soundcloud\.com",
}

REMOTE_FETCH_MAX_BYTES = 200 * 1024 * 1024  # direct image/video URL fetch cap


def _detect_social_service(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    domain = urlparse(url).netloc.lower()
    for service, pattern in SOCIAL_PATTERNS.items():
        if re.search(pattern, domain):
            return service
    return None


# ── Schemas ─────────────────────────────────────────────────────────────────

class CaptureCreate(BaseModel):
    capture_kind: str
    url: Optional[str] = None
    text_content: Optional[str] = None
    title: Optional[str] = None
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    intended_cue_type: Optional[str] = None
    # Set when the client already uploaded media (e.g. screenshots via
    # /upload-media) and the capture just references it.
    media_asset_id: Optional[str] = None
    media_path: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    client_capture_id: Optional[str] = None
    source: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


def _capture_to_dict(c: WhiteboardCapture) -> Dict[str, Any]:
    return {
        "id": c.id,
        "episode_number": c.episode_number,
        "client_capture_id": c.client_capture_id,
        "capture_kind": c.capture_kind,
        "item_type": c.item_type,
        "intended_cue_type": c.intended_cue_type,
        "title": c.title,
        "text_content": c.text_content,
        "url": c.url,
        "notes": c.notes,
        "caption": c.caption,
        "preview_title": c.preview_title,
        "preview_description": c.preview_description,
        "preview_image": c.preview_image,
        "preview_domain": c.preview_domain,
        "preview_favicon": c.preview_favicon,
        "social_metadata": c.social_metadata,
        "media_asset_id": c.media_asset_id,
        "media_path": c.media_path,
        "media_url": f"/pool/{c.media_path}" if c.media_path else None,
        "mime_type": c.mime_type,
        "file_size": c.file_size,
        "thumbnail_url": c.thumbnail_url,
        "media_metadata": c.media_metadata,
        "extra_assets": c.extra_assets,
        "status": c.status,
        "error": c.error,
        "processing_job_id": c.processing_job_id,
        "source": c.source,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "created_by": c.created_by,
        "placed_at": c.placed_at.isoformat() if c.placed_at else None,
    }


def _require_episode(identifier: str) -> str:
    if not (identifier.isdigit() and len(identifier) == 4):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Captures target episode whiteboards; identifier must be a 4-digit episode number"
        )
    return identifier


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/{identifier}/captures")
async def create_capture(
    identifier: str,
    payload: CaptureCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Accept a capture. Returns 202 while server-side enrichment runs, 200
    with the existing row when client_capture_id was already seen (idempotent
    retry), or 202/pending immediately when no enrichment is needed."""
    episode = _require_episode(identifier)

    if payload.capture_kind not in VALID_KINDS:
        raise HTTPException(status_code=400, detail=f"capture_kind must be one of {sorted(VALID_KINDS)}")
    if payload.intended_cue_type and payload.intended_cue_type not in VALID_CUE_TYPES:
        raise HTTPException(status_code=400, detail=f"intended_cue_type must be one of {sorted(VALID_CUE_TYPES)}")
    if payload.capture_kind == "selection" and not (payload.text_content or "").strip():
        raise HTTPException(status_code=400, detail="selection capture requires text_content")
    if payload.capture_kind in ("link", "page", "image", "video") and not payload.url and not payload.media_asset_id:
        raise HTTPException(status_code=400, detail=f"{payload.capture_kind} capture requires url")

    if payload.client_capture_id:
        existing = db.query(WhiteboardCapture).filter_by(client_capture_id=payload.client_capture_id).first()
        if existing:
            return JSONResponse(status_code=200, content={"capture": _capture_to_dict(existing), "duplicate": True})

    source = dict(payload.source or {})
    if payload.page_url:
        source["page_url"] = payload.page_url
    if payload.page_title:
        source["page_title"] = payload.page_title

    item_type = _initial_item_type(payload)
    has_media = bool(payload.media_asset_id)
    needs_enrichment = not has_media and payload.capture_kind != "selection"
    # A pre-uploaded video typed as SOT/VO still needs the processing dispatch.
    if has_media and payload.intended_cue_type in ("sot", "vo") and (payload.mime_type or "").startswith("video/"):
        needs_enrichment = True

    capture = WhiteboardCapture(
        episode_number=episode,
        client_capture_id=payload.client_capture_id,
        capture_kind=payload.capture_kind,
        item_type=item_type,
        intended_cue_type=payload.intended_cue_type,
        title=(payload.title or payload.page_title or None),
        text_content=payload.text_content,
        url=payload.url,
        media_asset_id=payload.media_asset_id,
        media_path=payload.media_path,
        mime_type=payload.mime_type,
        file_size=payload.file_size,
        source=source or None,
        status="processing" if needs_enrichment else "pending",
        created_by=current_user.get("username", "unknown"),
    )
    db.add(capture)
    db.commit()
    db.refresh(capture)

    if needs_enrichment:
        tags = ",".join(payload.tags) if payload.tags else None
        background_tasks.add_task(_process_capture, capture.id, tags)

    return JSONResponse(status_code=202, content={"capture": _capture_to_dict(capture)})


@router.get("/{identifier}/captures")
async def list_captures(
    identifier: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = 50,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db),
):
    episode = _require_episode(identifier)
    q = db.query(WhiteboardCapture).filter(WhiteboardCapture.episode_number == episode)
    return _list_response(q, status_filter, limit)


def _list_response(q, status_filter, limit):
    status_filter = status_filter or "pending"
    if status_filter != "all":
        if status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"status must be 'all' or one of {sorted(VALID_STATUSES)}")
        q = q.filter(WhiteboardCapture.status == status_filter)
    rows = q.order_by(WhiteboardCapture.created_at.asc()).limit(min(max(limit, 1), 200)).all()
    return {"captures": [_capture_to_dict(c) for c in rows], "count": len(rows)}


@router.get("/{identifier}/captures/{capture_id}")
async def get_capture(
    identifier: str,
    capture_id: int,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    capture = _get_owned(db, identifier, capture_id)
    return {"capture": _capture_to_dict(capture)}


@router.post("/{identifier}/captures/{capture_id}/ack")
async def ack_capture(
    identifier: str,
    capture_id: int,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Mark a capture placed on the board. Idempotent. 409 while processing."""
    capture = _get_owned(db, identifier, capture_id)
    if capture.status == "processing":
        raise HTTPException(status_code=409, detail="Capture is still processing")
    if capture.status != "placed":
        capture.status = "placed"
        capture.placed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(capture)
    return {"capture": _capture_to_dict(capture)}


@router.post("/{identifier}/captures/{capture_id}/dismiss")
async def dismiss_capture(
    identifier: str,
    capture_id: int,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Dismiss a capture. Idempotent. Never deletes pool media."""
    capture = _get_owned(db, identifier, capture_id)
    if capture.status != "dismissed":
        capture.status = "dismissed"
        db.commit()
        db.refresh(capture)
    return {"capture": _capture_to_dict(capture)}


def _get_owned(db: Session, identifier: str, capture_id: int) -> WhiteboardCapture:
    episode = _require_episode(identifier)
    capture = db.query(WhiteboardCapture).filter_by(id=capture_id, episode_number=episode).first()
    if not capture:
        raise HTTPException(status_code=404, detail=f"Capture {capture_id} not found for episode {episode}")
    return capture


def _initial_item_type(payload: CaptureCreate) -> str:
    if payload.capture_kind == "selection":
        return "text"
    if payload.capture_kind in ("image", "screenshot"):
        return "image"
    if payload.capture_kind == "video":
        return "video"
    return "link"


# ── Enrichment (BackgroundTasks; sync fn → runs in Starlette's threadpool) ──

def _process_capture(capture_id: int, tags: Optional[str] = None):
    """Enrich a capture: link preview / social download / remote media fetch,
    then optional SOT/VO processing dispatch. Any failure degrades the row to
    a pending link card with the error recorded — a capture is never lost."""
    db = SessionLocal()
    try:
        capture = db.query(WhiteboardCapture).filter_by(id=capture_id).first()
        if not capture:
            return
        try:
            _enrich(db, capture, tags)
        except Exception as e:
            logger.exception(f"Capture {capture_id} enrichment failed")
            db.rollback()  # the failure may have poisoned the transaction
            capture = db.query(WhiteboardCapture).filter_by(id=capture_id).first()
            if not capture:
                return
            capture.error = {"stage": "enrichment", "message": str(e)[:500]}
            if capture.url or capture.text_content or capture.media_asset_id:
                capture.item_type = capture.item_type if capture.media_asset_id else "link"
                capture.status = "pending"
            else:
                capture.status = "failed"
            db.commit()
            return

        try:
            if capture.intended_cue_type in ("sot", "vo") and capture.media_path \
                    and (capture.mime_type or "").startswith("video/"):
                _dispatch_cue_processing(db, capture)
        except Exception as e:
            # Processing dispatch failure must not sink the capture itself.
            logger.exception(f"Capture {capture_id} cue-processing dispatch failed")
            db.rollback()
            capture = db.query(WhiteboardCapture).filter_by(id=capture_id).first()
            if not capture:
                return
            capture.error = {"stage": "cue_processing", "message": str(e)[:500]}

        capture.status = "pending"
        db.commit()
    finally:
        db.close()


def _enrich(db: Session, capture: WhiteboardCapture, tags: Optional[str]):
    from routers.whiteboard.social_media_router import _download_twitter_media, _download_via_ytdlp
    from link_preview_service import fetch_link_preview

    url = capture.url
    service = _detect_social_service(url)
    username = capture.created_by or "capture"

    # Always try a link preview when we have a URL — cheap, and gives the card
    # something to show even when a media download fails.
    if url:
        try:
            preview = fetch_link_preview(url, db=db) or {}
            if not preview.get("error"):
                capture.preview_title = preview.get("title")
                capture.preview_description = preview.get("description")
                capture.preview_image = preview.get("image")
                capture.preview_domain = preview.get("domain") or urlparse(url).netloc
                capture.preview_favicon = preview.get("favicon")
                if not capture.title:
                    capture.title = (preview.get("title") or "")[:200] or None
        except Exception as e:
            logger.warning(f"Capture {capture.id}: link preview failed for {url}: {e}")

    if capture.media_asset_id:
        return  # media already uploaded client-side; preview above is all we add

    if service and capture.capture_kind in ("link", "page", "video"):
        if service == "twitter":
            result = asyncio.run(_download_twitter_media(capture.episode_number, url, tags, username, db))
        else:
            result = asyncio.run(_download_via_ytdlp(capture.episode_number, url, tags, username, db))

        if result.get("success") and result.get("assets"):
            # yt-dlp downloads often include a thumbnail image alongside the
            # video — lead with the richest media, not download order.
            rank = {"video": 0, "audio": 1, "image": 2}
            assets = sorted(result["assets"], key=lambda a: rank.get(a.get("media_category"), 3))
            first = assets[0]
            capture.media_asset_id = first["asset_id"]
            capture.media_path = first.get("media_path")
            capture.mime_type = first.get("mime_type")
            capture.file_size = first.get("file_size")
            category = first.get("media_category", "image")
            capture.item_type = category if category in ("image", "video", "audio") else "link"
            capture.extra_assets = assets[1:] or None
            capture.social_metadata = result.get("tweet_data") or result.get("content_data")
            capture.thumbnail_url = result.get("local_thumbnail_url") or result.get("local_avatar_url")
            sm = capture.social_metadata or {}
            if not capture.title:
                author = sm.get("author_handle") or sm.get("author_name")
                capture.title = (f"@{author}" if author else service).strip()[:200]
        else:
            # Post with no media, or download failure: keep it as a link card.
            capture.item_type = "link"
            err = result.get("error")
            if err:
                capture.error = {"stage": "social_download", "detail": err}
            if result.get("tweet_data") or result.get("content_data"):
                capture.social_metadata = result.get("tweet_data") or result.get("content_data")
        return

    if capture.capture_kind in ("image", "video") and url:
        saved = _save_url_to_pool(db, capture.episode_number, url, username, tags,
                                  source_url=(capture.source or {}).get("page_url") or url)
        if saved:
            capture.media_asset_id = saved["asset_id"]
            capture.media_path = saved["media_path"]
            capture.mime_type = saved["mime_type"]
            capture.file_size = saved["file_size"]
            capture.item_type = saved["media_category"] if saved["media_category"] in ("image", "video", "audio") else "link"
        else:
            capture.item_type = "link"
            capture.error = {"stage": "media_fetch", "message": f"Could not fetch media from {url[:200]}"}
        return

    # link/page with no social service: preview-only link card (already set).
    capture.item_type = "link" if url else capture.item_type


def _save_url_to_pool(db: Session, episode: str, url: str, username: str,
                      tags: Optional[str], source_url: Optional[str]) -> Optional[Dict[str, Any]]:
    """Fetch a direct media URL server-side into pool/whiteboard/{ep}/ with an
    AssetID name + AssetPoolFile row (mirrors upload-media's episode branch).
    Server-side fetch is immune to page CORS and hotlink referer checks fail
    soft: returns None on any problem."""
    import requests as http_requests
    from core.paths import paths as path_manager

    try:
        resp = http_requests.get(url, timeout=30, stream=True)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Capture media fetch failed for {url}: {e}")
        return None

    content_type = (resp.headers.get("content-type") or "").split(";")[0].strip()
    category = content_type.split("/")[0] if "/" in content_type else ""
    if category not in ("image", "video", "audio"):
        logger.warning(f"Capture media fetch: unsupported content-type '{content_type}' for {url}")
        return None

    ext = mimetypes.guess_extension(content_type) or Path(urlparse(url).path).suffix or ""
    if ext == ".jpe":
        ext = ".jpg"

    # Registry-backed ID: asset_pool_files.asset_id FKs asset_id_registry.
    asset_id = AssetIDService.request_asset_id(
        db, entity_type=f"whiteboard_{category}", reason="create",
        requested_by=username, context={"source": "extension", "source_url": source_url}
    )
    file_name = f"{asset_id}{ext}"
    media_dir = path_manager.get_whiteboard_media_dir(episode)
    media_dir.mkdir(parents=True, exist_ok=True)
    dest_path = media_dir / file_name

    written = 0
    try:
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                written += len(chunk)
                if written > REMOTE_FETCH_MAX_BYTES:
                    raise ValueError(f"exceeds {REMOTE_FETCH_MAX_BYTES} byte cap")
                f.write(chunk)
    except Exception as e:
        logger.warning(f"Capture media fetch aborted for {url}: {e}")
        dest_path.unlink(missing_ok=True)
        return None

    relative_path = f"whiteboard/{episode}/{file_name}"
    db.add(AssetPoolFile(
        asset_id=asset_id,
        file_path=str(dest_path),
        original_filename=Path(urlparse(url).path).name or file_name,
        mime_type=content_type,
        file_size=written,
        source="extension",
        source_url=source_url,
    ))
    for tag in [t.strip() for t in (tags or "").split(",") if t.strip()]:
        db.add(AssetTag(asset_id=asset_id, tag=tag, created_by=username))
    db.add(AssetTag(asset_id=asset_id, tag=f"episode:{episode}", created_by=username))
    db.commit()

    logger.info(f"Capture saved {category} from {url} as {asset_id} -> {dest_path}")
    return {
        "asset_id": asset_id,
        "media_path": relative_path,
        "mime_type": content_type,
        "file_size": written,
        "media_category": category,
    }


def _dispatch_cue_processing(db: Session, capture: WhiteboardCapture):
    """Feed a captured video into the existing SOT/VO pipeline: mint a
    temp_job_id, copy the pool file into the preproc working dir, insert a
    SOTProcessingJob row, dispatch the existing Celery task. Cue write-back
    inside the task no-ops safely (there is no cue yet); results live on the
    job row + episode assets, keyed by processing_job_id."""
    from models.jobs import SOTProcessingJob

    pool_file = Path("/home/pool") / capture.media_path
    if not pool_file.exists():
        raise FileNotFoundError(f"pool file missing: {pool_file}")

    cue_type = capture.intended_cue_type  # 'sot' | 'vo'
    temp_job_id = f"cap{cue_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    working_dir = Path("/shared_media") / "preproc" / "working" / temp_job_id
    working_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pool_file, working_dir / f"{temp_job_id}_upload.mp4")

    slug = _slug_for(capture)
    job = SOTProcessingJob(
        temp_job_id=temp_job_id,
        episode=capture.episode_number,
        slug=slug,
        status="processing",
        current_phase="phase1" if cue_type == "sot" else "phase0",
        job_type="full_process",
        job_category=cue_type,
        working_directory=str(working_dir),
    )
    db.add(job)
    db.commit()

    if cue_type == "sot":
        from services.ffmpeg_tasks import process_sot_video_multi_phase
        task = process_sot_video_multi_phase.apply_async(
            args=[temp_job_id, capture.episode_number, slug,
                  "00:00:00", "00:00:00", "full_process", None, None, False],
            queue="media", routing_key="media", exchange="media",
        )
    else:
        from services.ffmpeg_tasks import process_vo_video
        task = process_vo_video.apply_async(
            args=[temp_job_id, capture.episode_number, slug, "00:00:00", "00:00:00", None],
            queue="media", routing_key="media", exchange="media",
        )

    job.celery_task_id = task.id
    capture.processing_job_id = temp_job_id
    db.commit()
    logger.info(f"Capture {capture.id}: dispatched {cue_type.upper()} processing as {temp_job_id} (task {task.id})")


def _slug_for(capture: WhiteboardCapture) -> str:
    sm = capture.social_metadata or {}
    base = capture.title or sm.get("author_handle") or sm.get("author_name") or f"capture-{capture.id}"
    slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")[:40]
    return f"cap-{slug}" if slug else f"cap-{capture.id}"
