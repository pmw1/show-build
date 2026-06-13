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

Pool layout (episode-foldered for provenance, logically unbound from any cue):
  /home/pool/{episode}/assets/{video,audio,images,graphics}/{file}

TODO(future): whiteboard media may also relocate under
  /home/pool/{episode}/whiteboard/
so the whole episode's loose media lives in one place.
"""
import mimetypes
import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
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

    # Cue MediaURLs are stored relative to the episode's scripts/ or rundown/
    # dir as '../assets/...'. Strip leading '../' and any leading slash, then
    # resolve against the episode root so '../assets/video/x.mp4' -> assets/...
    cleaned = media_url.strip().lstrip("/")
    while cleaned.startswith("../"):
        cleaned = cleaned[3:]
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]

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
    /home/pool/{episode}/assets/{subdir}/ and recorded as an AssetPoolFile row
    so a future pool-browser can surface it for reuse.
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
            # Preserve the media subdir (video/audio/images/graphics/...).
            episode_root = (EPISODES_ROOT / episode_number).resolve()
            rel = src.relative_to(episode_root)
            # rel like assets/video/x.mp4 -> keep everything after the first
            # 'assets'/'thumbnails' marker so the pool mirrors the episode tree.
            sub_parts = rel.parts[1:]  # drop the top-level 'assets'/'thumbnails'
            dest_dir = POOL_ROOT / episode_number / "assets" / Path(*sub_parts[:-1]) \
                if sub_parts[:-1] else POOL_ROOT / episode_number / "assets"
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
