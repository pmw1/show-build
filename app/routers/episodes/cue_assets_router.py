"""
Cue-asset disposition router.

When a cue block is deleted from a script, its linked media files (video,
audio, thumbnails, generated graphics) need a disposition. This router
provides two episode-scoped, additive endpoints:

  POST /{episode_number}/cue-assets/delete         -> permanently delete files
  POST /{episode_number}/cue-assets/move-to-pool   -> release files to the
                                                      unbound show media pool

Deletion is ALWAYS driven by the specific cue's own URL fields (MediaURL,
AudioURL, ThumbnailURL, thumbnailOptions). It is NEVER driven by globbing the
AssetID, because a single AssetID can be shared by multiple cues pointing at
different files — globbing would delete another cue's media.

Pool layout (host: media_assets/pool, container /home/pool). Cue-released media
goes under episodes/ FLAT (no assets/{video,audio,...} subdirs):
  /home/pool/episodes/{episode}/{file}
Sibling pool trees (managed elsewhere): ads/{advertiserID}/, repo/ (reusables),
  whiteboard/{episode}/ (whiteboard media).
"""
import mimetypes
import os
import shutil
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.utils import get_current_user_or_key
from database import get_db
from services.asset_id import AssetIDService

from ._shared import EPISODES_ROOT, logger

router = APIRouter()

POOL_ROOT = Path(os.getenv("POOL_ROOT", "/home/pool"))

# Subdirectories within an episode that legitimately hold cue media. A resolved
# file path must live under one of these (relative to the episode root) or the
# request is rejected as a traversal attempt.
ALLOWED_MEDIA_SUBDIRS = ("assets", "thumbnails")


class CueAssetDeleteRequest(BaseModel):
    media_urls: List[str] = Field(default_factory=list)


class CueAssetMoveRequest(BaseModel):
    media_urls: List[str] = Field(default_factory=list)
    slug: Optional[str] = None
    cue_type: Optional[str] = None
    asset_id: Optional[str] = None  # the (possibly shared) cue AssetID, for provenance


def _resolve_within_episode(episode_number: str, media_url: str) -> Path:
    """
    Resolve a cue's relative media URL (e.g. '../assets/video/x.mp4') against
    the episode root and assert the result stays inside an allowed media subdir.

    Raises HTTPException(403) on traversal outside the episode's media dirs.
    """
    episode_root = (EPISODES_ROOT / episode_number).resolve()

    # Cue MediaURLs come in three shapes; normalize all to a path relative to
    # the episode root (e.g. 'assets/video/x.mp4'):
    #   1. relative:        '../assets/video/x.mp4'      (from scripts/ or rundown/)
    #   2. absolute served: '/episodes/0276/assets/...'  (the /episodes static mount)
    #   3. bare:            'assets/video/x.mp4'
    cleaned = media_url.strip().lstrip("/")
    while cleaned.startswith("../"):
        cleaned = cleaned[3:]
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    # Strip a leading 'episodes/{ep}/' prefix (the absolute served-URL form), so
    # '/episodes/0276/assets/video/x.mp4' -> 'assets/video/x.mp4' instead of
    # doubling up to '<root>/episodes/0276/assets/...' (which fails the subdir check).
    # Only strip THIS episode's prefix; a different episode number is left intact so
    # the inside-episode-root safety check below rejects it (no cross-episode delete).
    ep_prefix = f"episodes/{episode_number}/"
    if cleaned.startswith(ep_prefix):
        cleaned = cleaned[len(ep_prefix):]

    candidate = (episode_root / cleaned).resolve()

    # Safety: must be inside episode_root AND under an allowed subdir.
    if episode_root not in candidate.parents:
        raise HTTPException(
            status_code=403,
            detail=f"Refusing path outside episode {episode_number}: {media_url}",
        )
    rel = candidate.relative_to(episode_root)
    if not rel.parts or rel.parts[0] not in ALLOWED_MEDIA_SUBDIRS:
        raise HTTPException(
            status_code=403,
            detail=f"Refusing path outside allowed media dirs: {media_url}",
        )
    return candidate


def _dedupe(urls: List[str]) -> List[str]:
    seen = set()
    out = []
    for u in urls:
        if not u or not str(u).strip():
            continue
        s = str(u).strip()
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


@router.post("/{episode_number}/cue-assets/delete")
async def delete_cue_assets(
    episode_number: str,
    payload: CueAssetDeleteRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
):
    """
    Permanently delete the media files linked to a cue.

    Returns 200 even on partial failure; the caller inspects `errors` and
    decides what to surface to the user.
    """
    deleted: List[str] = []
    skipped: List[str] = []
    errors: List[dict] = []

    for url in _dedupe(payload.media_urls):
        try:
            path = _resolve_within_episode(episode_number, url)
        except HTTPException as e:
            errors.append({"path": url, "reason": e.detail})
            continue

        try:
            if not path.exists():
                skipped.append(url)
                continue
            path.unlink()
            deleted.append(url)
            logger.info(f"Deleted cue asset: {path}")
        except Exception as exc:  # noqa: BLE001 - report every failure to the UI
            errors.append({"path": url, "reason": str(exc)})
            logger.error(f"Failed to delete cue asset {path}: {exc}")

    return {"deleted": deleted, "skipped": skipped, "errors": errors}


@router.post("/{episode_number}/cue-assets/move-to-pool")
async def move_cue_assets_to_pool(
    episode_number: str,
    payload: CueAssetMoveRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
):
    """
    Release a cue's media files to the unbound show media pool.

    Each file is MOVED (not copied) out of the episode into
    /home/pool/episodes/{episode}/{file} (flat) and recorded as an AssetPoolFile
    row so a future pool-browser can surface it for reuse.
    """
    # Imported here to avoid a hard import dependency at module load.
    from models_whiteboard import AssetPoolFile, AssetTag

    username = (current_user or {}).get("username", "unknown")

    moved: List[dict] = []
    errors: List[dict] = []

    for url in _dedupe(payload.media_urls):
        try:
            src = _resolve_within_episode(episode_number, url)
        except HTTPException as e:
            errors.append({"path": url, "reason": e.detail})
            continue

        if not src.exists():
            # Nothing to move; not an error worth blocking on.
            errors.append({"path": url, "reason": "file not found on disk"})
            continue

        try:
            # FLAT pool layout: every released file lands directly in the
            # episode's pool folder — /home/pool/episodes/{episode}/{file} —
            # regardless of its original assets/{video,audio,images,graphics}
            # subdir. The pool is an unbound bag of reusable media; the per-type
            # subdirs the live episode tree uses add no value here (provenance is
            # captured in the AssetPoolFile row's source_context + tags below).
            dest_dir = POOL_ROOT / "episodes" / episode_number
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name

            # Avoid clobbering an existing pooled file of the same name.
            if dest.exists():
                stem, ext = os.path.splitext(src.name)
                i = 1
                while (dest_dir / f"{stem}-{i}{ext}").exists():
                    i += 1
                dest = dest_dir / f"{stem}-{i}{ext}"

            shutil.move(str(src), str(dest))
            logger.info(f"Released cue asset to pool: {src} -> {dest}")

            mime_type = mimetypes.guess_type(str(dest))[0]
            file_size = dest.stat().st_size

            pool_asset_id = AssetIDService.request_asset_id(
                db,
                entity_type="pool",
                reason="cue_release",
                requested_by=username,
                context={
                    "episode": episode_number,
                    "origin_cue_assetid": payload.asset_id,
                    "slug": payload.slug,
                    "cue_type": payload.cue_type,
                    "original_path": url,
                },
            )

            db.add(
                AssetPoolFile(
                    asset_id=pool_asset_id,
                    file_path=str(dest),
                    original_filename=src.name,
                    mime_type=mime_type,
                    file_size=file_size,
                    source="cue_release",
                    source_url=url,
                    source_context={
                        "episode": episode_number,
                        "origin_cue_assetid": payload.asset_id,
                        "slug": payload.slug,
                        "cue_type": payload.cue_type,
                        "original_path": url,
                    },
                )
            )

            # Tag for future browse/filter (cue type + slug).
            for tag in filter(None, [payload.cue_type, payload.slug, f"episode:{episode_number}"]):
                db.add(AssetTag(asset_id=pool_asset_id, tag=str(tag), created_by=username))

            db.commit()

            moved.append(
                {
                    "asset_id": pool_asset_id,
                    "new_path": str(dest),
                    "original_path": url,
                }
            )
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            errors.append({"path": url, "reason": str(exc)})
            logger.error(f"Failed to move cue asset {src} to pool: {exc}", exc_info=True)

    return {"moved": moved, "errors": errors}


def _file_kind(mime_type: Optional[str], filename: str) -> str:
    """Coarse media kind for the UI's cue-type picker: video | image | audio | other."""
    mt = (mime_type or "").lower()
    if mt.startswith("video/"):
        return "video"
    if mt.startswith("image/"):
        return "image"
    if mt.startswith("audio/"):
        return "audio"
    # Fallback by extension when mime is missing/unknown.
    ext = os.path.splitext(filename)[1].lower()
    if ext in (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"):
        return "video"
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"):
        return "image"
    if ext in (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"):
        return "audio"
    return "other"


@router.get("/{episode_number}/cue-assets/pool")
async def list_episode_pool_assets(
    episode_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
):
    """
    List the media files preserved in the pool for this episode — i.e. media
    released from deleted cues (and, later, loose per-episode uploads). These
    live at /home/pool/episodes/{episode}/ and are served at /pool/episodes/...

    Returns rows the AssetPoolPanel 'Media' tab renders: a servable url, a coarse
    `kind` (video/image/audio) for the re-insert cue-type picker, plus name /
    size / mime / source / origin provenance.
    """
    from models_whiteboard import AssetPoolFile

    # Match this episode's pooled files. Primary key is the on-disk location
    # (file_path under episodes/{ep}/); also accept rows tagged via source_context.
    ep_dir = str(POOL_ROOT / "episodes" / episode_number)
    rows = (
        db.query(AssetPoolFile)
        .filter(AssetPoolFile.file_path.like(f"{ep_dir}/%"))
        .order_by(AssetPoolFile.created_at.desc())
        .all()
    )

    items = []
    for r in rows:
        fname = os.path.basename(r.file_path)
        # URL-encode the filename so paths with spaces/special chars are valid
        # when assigned to <video>/<img> src or used as a cue MediaURL.
        url = f"/pool/episodes/{episode_number}/{quote(fname)}"
        thumb = None
        if r.thumbnail_path:
            thumb = f"/pool/episodes/{episode_number}/{quote(os.path.basename(r.thumbnail_path))}"
        ctx = r.source_context or {}
        items.append({
            "asset_id": r.asset_id,
            "filename": fname,
            "original_filename": r.original_filename,
            "url": url,
            "thumbnail_url": thumb,
            "kind": _file_kind(r.mime_type, fname),
            "mime_type": r.mime_type,
            "file_size": r.file_size,
            "source": r.source,
            "origin_slug": ctx.get("slug"),
            "origin_cue_type": ctx.get("cue_type"),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {"episode": episode_number, "count": len(items), "items": items}


@router.post("/{episode_number}/cue-assets/pool/upload")
async def upload_to_episode_pool(
    episode_number: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key),
):
    """
    Upload a media file straight into this episode's pool (a second way media
    lands here besides cue release). Stored at /home/pool/episodes/{ep}/{name}
    and recorded as an AssetPoolFile row so it shows in the Media tab and can be
    re-inserted as a cue.
    """
    from models_whiteboard import AssetPoolFile, AssetTag

    username = (current_user or {}).get("username", "unknown")
    dest_dir = POOL_ROOT / "episodes" / episode_number
    dest_dir.mkdir(parents=True, exist_ok=True)

    safe_name = os.path.basename(file.filename or "upload.bin")
    dest = dest_dir / safe_name
    if dest.exists():
        stem, ext = os.path.splitext(safe_name)
        i = 1
        while (dest_dir / f"{stem}-{i}{ext}").exists():
            i += 1
        dest = dest_dir / f"{stem}-{i}{ext}"

    try:
        with open(dest, "wb") as out:
            shutil.copyfileobj(file.file, out)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Pool upload failed for {dest}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")

    mime_type = file.content_type or mimetypes.guess_type(str(dest))[0]
    file_size = dest.stat().st_size

    pool_asset_id = AssetIDService.request_asset_id(
        db,
        entity_type="pool",
        reason="manual_upload",
        requested_by=username,
        context={"episode": episode_number, "original_filename": safe_name},
    )
    db.add(AssetPoolFile(
        asset_id=pool_asset_id,
        file_path=str(dest),
        original_filename=safe_name,
        mime_type=mime_type,
        file_size=file_size,
        source="manual_upload",
        source_context={"episode": episode_number, "original_filename": safe_name},
    ))
    db.add(AssetTag(asset_id=pool_asset_id, tag=f"episode:{episode_number}", created_by=username))
    db.commit()

    return {
        "asset_id": pool_asset_id,
        "filename": dest.name,
        "url": f"/pool/episodes/{episode_number}/{quote(dest.name)}",
        "kind": _file_kind(mime_type, dest.name),
        "mime_type": mime_type,
        "file_size": file_size,
    }
