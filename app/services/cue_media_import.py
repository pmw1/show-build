"""
Cue Media Import — path-based entry points for the Legacy Cue Convert module.

Background
----------
Each cue type's manual modal already has a working pipeline that takes a
multipart upload and runs the appropriate move/rename/process work. The
Legacy Cue Convert module's conversion path is different: the file is
already on disk in the episode's preshow/ folder when the user clicks
"Convert to Cue". Re-uploading via multipart would be wasteful and would
require the conversion code to read the file into memory just to POST it
back.

This module exposes path-based wrappers that mirror what each manual
upload handler does, but accept a server-side filesystem path instead
of an UploadFile. The existing modal route handlers are NOT modified —
they keep working exactly as before for manual entry.

Coverage
--------
- start_sot_processing_from_path  — full FFmpeg multi-phase pipeline (SOT)
- start_vo_processing_from_path   — VO pipeline
- save_image_from_path            — IMG simple copy/rename
- save_audio_from_path            — BUMP/STING/MUS/LIVE/VOX (new path; the
                                    manual modals for these are library-
                                    backed and don't have an upload flow)

Not covered (intentional, per plan):
- NAT, PKG: their existing manual modal endpoints point at the
  defunct whisperbox host (192.168.51.210). The conversion module
  produces NAT/PKG cues with [MediaURL: ...] linking directly to the
  preshow file (no copy, no processing) until the manual flow is fixed.
  See ACTIVE_WORK_QUEUE.md.
- GFX, FSQ: these are GENERATORS, not uploaders. The conversion
  module produces media-less GFX/FSQ cues; the user finishes via the
  modal's generation flow.
- NOTE, RIF: text-only cues, no media.
"""
from pathlib import Path
import shutil
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# SOT
# ---------------------------------------------------------------------------

def start_sot_processing_from_path(
    db: Session,
    source_path: Path,
    episode: str,
    slug: str,
    asset_id: Optional[str] = None,
) -> dict:
    """
    Mirror of /api/sot/upload/background + /api/sot/process/multi-phase
    for a file that already exists at `source_path` (typically in
    episodes/{episode}/preshow/).

    Steps:
      1. Generate temp_job_id and create working directory
         (/shared_media/preproc/working/{temp_job_id}/).
      2. Copy source_path → working_dir/{temp_job_id}_upload.mp4.
      3. Create SOTProcessingJob row with status='uploaded'.
      4. Dispatch process_sot_video_multi_phase Celery task.

    Returns:
      {
        "temp_job_id": "...",
        "celery_task_id": "...",
        "working_dir": "/shared_media/preproc/working/...",
      }

    Raises:
      FileNotFoundError if source_path doesn't exist.
      RuntimeError if SOTProcessingJob creation fails.
    """
    from models_v2 import SOTProcessingJob
    from services.ffmpeg_tasks import process_sot_video_multi_phase

    if not source_path.exists():
        raise FileNotFoundError(f"Source media not found: {source_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    temp_job_id = f"sot_{timestamp}_{unique_id}"

    working_dir = Path("/shared_media") / "preproc" / "working" / temp_job_id
    working_dir.mkdir(parents=True, exist_ok=True)

    upload_path = working_dir / f"{temp_job_id}_upload.mp4"
    # Use copy (not move) so the source file in preshow/ is preserved.
    shutil.copy2(str(source_path), str(upload_path))

    job = SOTProcessingJob(
        temp_job_id=temp_job_id,
        episode=episode,
        slug=slug,
        asset_id=asset_id,
        current_phase='phase1',
        status='processing',
        working_directory=str(working_dir),
        job_type='full_process',
    )
    db.add(job)
    db.commit()

    # Mirror sot_router.py:493 — process_sot_video_multi_phase.apply_async with
    # positional args: (temp_job_id, episode, slug, trim_start, trim_end,
    # job_type, clips, asset_id, devel_mode)
    task = process_sot_video_multi_phase.apply_async(
        args=[
            temp_job_id,
            episode,
            slug,
            "00:00:00",  # trim_start
            "00:00:00",  # trim_end
            "full_process",
            None,        # clips
            asset_id,
            False,       # devel_mode
        ],
        queue='media',
        routing_key='media',
        exchange='media',
    )

    job.celery_task_id = task.id
    db.commit()

    return {
        "temp_job_id": temp_job_id,
        "celery_task_id": task.id,
        "working_dir": str(working_dir),
    }


# ---------------------------------------------------------------------------
# VO
# ---------------------------------------------------------------------------

def start_vo_processing_from_path(
    db: Session,
    source_path: Path,
    episode: str,
    slug: str,
    asset_id: Optional[str] = None,
) -> dict:
    """
    Mirror of /api/vo/upload/background + /api/vo/process for a file
    that already exists at `source_path`. Same shape as
    start_sot_processing_from_path but routes to the VO pipeline (no
    audio normalization, video-only).

    Returns the same shape: {temp_job_id, celery_task_id, working_dir}.
    """
    from models_v2 import SOTProcessingJob  # VO reuses the same job table
    from services.ffmpeg_tasks import process_vo_video

    if not source_path.exists():
        raise FileNotFoundError(f"Source media not found: {source_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    temp_job_id = f"vo_{timestamp}_{unique_id}"

    working_dir = Path("/shared_media") / "preproc" / "working" / temp_job_id
    working_dir.mkdir(parents=True, exist_ok=True)

    upload_path = working_dir / f"{temp_job_id}_upload.mp4"
    shutil.copy2(str(source_path), str(upload_path))

    job = SOTProcessingJob(
        temp_job_id=temp_job_id,
        episode=episode,
        slug=slug,
        asset_id=asset_id,
        current_phase='phase0',
        status='processing',
        working_directory=str(working_dir),
        job_category='vo',
    )
    db.add(job)
    db.commit()

    # Mirror vo_router.py:229 — process_vo_video.apply_async with positional args.
    # Signature: (temp_job_id, episode, slug, trim_start, trim_end, asset_id)
    task = process_vo_video.apply_async(
        args=[temp_job_id, episode, slug, "00:00:00", "00:00:00", asset_id],
        queue='media',
        routing_key='media',
        exchange='media',
    )

    job.celery_task_id = task.id
    db.commit()

    return {
        "temp_job_id": temp_job_id,
        "celery_task_id": task.id,
        "working_dir": str(working_dir),
    }


# ---------------------------------------------------------------------------
# IMG
# ---------------------------------------------------------------------------

def save_image_from_path(
    source_path: Path,
    episode: str,
    slug: str,
    media_root: Optional[Path] = None,
) -> dict:
    """
    Mirror of /api/upload/image for a file that already exists at
    `source_path`. Synchronous — no Celery, no processing. Just
    copy + rename to the canonical path:
        episodes/{episode}/assets/images/{slug}.{ext}

    Returns:
      {"target_path": "...", "media_url": "/episodes/.../assets/images/..."}
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source media not found: {source_path}")

    if media_root is None:
        # Match the running server's path resolution. Inside the docker
        # container, episodes are at /home/episodes (per app/main.py).
        media_root = Path("/home")

    ext = source_path.suffix.lower().lstrip(".") or "png"
    target_dir = media_root / "episodes" / episode / "assets" / "images"
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / f"{slug}.{ext}"
    shutil.copy2(str(source_path), str(target_path))

    media_url = f"/episodes/{episode}/assets/images/{slug}.{ext}"
    return {"target_path": str(target_path), "media_url": media_url}


# ---------------------------------------------------------------------------
# Audio (BUMP / STING / MUS / LIVE / VOX)
# ---------------------------------------------------------------------------

def save_audio_from_path(
    source_path: Path,
    episode: str,
    slug: str,
    asset_id: Optional[str] = None,
    media_root: Optional[Path] = None,
) -> dict:
    """
    Copy an audio file from preshow/ into the canonical location:
        episodes/{episode}/assets/audio/{slug}.{ext}

    Used by the Legacy Cue Convert module for BUMP/STING/MUS/LIVE/VOX
    cues — these types have no manual upload flow (their modals are
    library-backed). For converted cues, we still need to land the
    file in a canonical place so the cue's MediaURL resolves.

    No Celery / no audio normalization at this stage. The cue lands
    with [ProcessingStatus: pending] and the user can use the existing
    audio reprocess flow if they want normalization.

    Returns:
      {"target_path": "...", "media_url": "/episodes/.../assets/audio/..."}
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source media not found: {source_path}")

    if media_root is None:
        media_root = Path("/home")

    ext = source_path.suffix.lower().lstrip(".") or "mp3"
    target_dir = media_root / "episodes" / episode / "assets" / "audio"
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / f"{slug}.{ext}"
    shutil.copy2(str(source_path), str(target_path))

    media_url = f"/episodes/{episode}/assets/audio/{slug}.{ext}"
    return {"target_path": str(target_path), "media_url": media_url}
