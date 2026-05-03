"""
Thumbnail management router.
Handles thumbnail listing, conversion, take, and confirmed status.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import re
from auth.utils import get_current_user_or_key
from database import get_db
from sqlalchemy.orm import Session
import logging

from ._shared import ConvertThumbnailRequest, TakeThumbnailRequest, logger

router = APIRouter()


@router.get("/{episode_number}/thumbnails")
async def get_episode_thumbnails(episode_number: str) -> Dict[str, Any]:
    """Get candidate thumbnail images for an episode.

    Scans {episode_dir}/exports/thumbnails/ and one level of its subdirectories
    for any .jpg or .png file. The feature image (poster) is chosen by the
    user in the interface and persisted in the database; it is not inferred
    from the filename.
    """
    from core.paths import paths as path_manager

    try:
        episode_num = path_manager._normalize_episode_id(episode_number)
        episode_dir = path_manager.get_episode_dir(episode_number)
        thumbnails_dir = episode_dir / "exports" / "thumbnails"

        image_pattern = re.compile(r'\.(jpg|png)$', re.IGNORECASE)

        thumbnails = []
        seen_paths = set()

        def scan_directory(directory, url_prefix):
            if not directory.exists():
                return
            for file in directory.iterdir():
                if file.is_file() and image_pattern.search(file.name):
                    real_path = file.resolve()
                    if real_path in seen_paths:
                        continue
                    seen_paths.add(real_path)
                    thumbnails.append({
                        "filename": file.name,
                        "url": f"{url_prefix}/{file.name}",
                        "modified": file.stat().st_mtime,
                        "size": file.stat().st_size
                    })

        if thumbnails_dir.exists():
            scan_directory(thumbnails_dir, f"/episodes/{episode_num}/exports/thumbnails")
            for subdir in thumbnails_dir.iterdir():
                if subdir.is_dir():
                    scan_directory(subdir, f"/episodes/{episode_num}/exports/thumbnails/{subdir.name}")

        thumbnails.sort(key=lambda x: -x["modified"])

        selected = thumbnails[0]["url"] if thumbnails else None

        logger.info(f"Found {len(thumbnails)} thumbnail(s) for episode {episode_number}")
        return {
            "thumbnails": thumbnails,
            "selected": selected,
            "count": len(thumbnails)
        }

    except Exception as e:
        logger.error(f"Error finding thumbnails for episode {episode_number}: {e}")
        return {"thumbnails": [], "selected": None, "error": str(e)}


@router.post("/{episode_number}/thumbnail/convert-to-png")
async def convert_thumbnail_to_png(
    episode_number: str,
    request: ConvertThumbnailRequest
) -> Dict[str, Any]:
    """Dispatch a Celery task to convert a non-PNG thumbnail to PNG format.

    Returns the task_id for polling completion status.
    """
    from core.paths import paths as path_manager
    from celery_app import celery_app

    try:
        episode_num = path_manager._normalize_episode_id(episode_number)
        episode_dir = path_manager.get_episode_dir(episode_number)

        # Resolve URL to filesystem path
        # URL format: /episodes/0257/thumbnails/subdir/file.jpg or /episodes/0257/exports/file.jpg
        url_path = request.url
        if url_path.startswith('/episodes/'):
            relative = url_path[len('/episodes/'):]  # e.g. "0257/thumbnails/poster.jpg"
            source_path = path_manager.episodes_root / relative
        else:
            return {"success": False, "error": "Invalid thumbnail URL format"}

        if not source_path.exists():
            return {"success": False, "error": f"File not found: {source_path.name}"}

        if source_path.suffix.lower() == '.png':
            return {"success": False, "error": "File is already PNG"}

        # Dispatch Celery task on assets queue
        task = celery_app.send_task(
            'services.asset_processing.convert_thumbnail_to_png',
            args=[str(source_path), episode_num],
            queue='assets'
        )

        logger.info(f"Dispatched thumbnail PNG conversion: {source_path.name} -> task {task.id}")

        return {
            "success": True,
            "task_id": task.id,
            "source_url": request.url,
            "message": f"Conversion started for {source_path.name}"
        }

    except Exception as e:
        logger.error(f"Error dispatching thumbnail conversion: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{episode_number}/thumbnail/convert-status/{task_id}")
async def get_thumbnail_convert_status(episode_number: str, task_id: str) -> Dict[str, Any]:
    """Poll the status of a thumbnail PNG conversion task."""
    from celery_app import celery_app

    try:
        result = celery_app.AsyncResult(task_id)
        response = {
            "task_id": task_id,
            "state": result.state,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None
        }

        if result.ready():
            if result.successful():
                response["result"] = result.result
            else:
                response["error"] = str(result.info)
        elif result.state == 'PROGRESS':
            response["progress"] = result.info

        return response

    except Exception as e:
        return {"task_id": task_id, "state": "ERROR", "error": str(e)}


@router.post("/{episode_number}/thumbnail/take")
async def take_episode_thumbnail(
    episode_number: str,
    request: TakeThumbnailRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    'Take' a thumbnail - copy it to a protected location with an AssetID filename.

    This protects the selected thumbnail from user filesystem changes by:
    1. Copying it to assets/thumbnails/ with an AssetID-based filename
    2. Storing the protected path in the database

    The original file in exports/ remains untouched.
    """
    from core.paths import paths as path_manager
    from models_v2 import Episode
    import shutil
    import uuid

    try:
        episode_num = path_manager._normalize_episode_id(episode_number)

        # Get episode from database
        episode = db.query(Episode).filter(Episode.episode_number == int(episode_number)).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found in database")

        # Parse source URL to get the actual file path
        # URL format: /episodes/0257/exports/poster16x9.jpg
        source_url = request.source_url
        if not source_url.startswith('/episodes/'):
            raise HTTPException(status_code=400, detail="Invalid source URL format")

        # Convert URL to filesystem path
        relative_path = source_url.replace('/episodes/', '')
        source_path = path_manager.episodes_root / relative_path

        if not source_path.exists():
            raise HTTPException(status_code=404, detail=f"Source file not found: {source_url}")

        # Get file extension
        ext = source_path.suffix.lower()

        # Generate a unique protected filename using episode asset_id or generate new
        if episode.asset_id:
            protected_filename = f"{episode.asset_id}_poster{ext}"
        else:
            # Fallback: use episode number + UUID
            unique_id = uuid.uuid4().hex[:8].upper()
            protected_filename = f"EP{episode_num}_{unique_id}_poster{ext}"

        # Destination: assets/thumbnails/protected/ directory
        thumbnails_dir = path_manager.get_asset_type_dir(episode_number, 'thumbnails')
        protected_dir = thumbnails_dir / 'protected'
        protected_dir.mkdir(parents=True, exist_ok=True)

        dest_path = protected_dir / protected_filename

        # Copy the file to protected location
        shutil.copy2(source_path, dest_path)
        logger.info(f"Copied thumbnail from {source_path} to {dest_path}")

        # Build the protected URL path
        protected_url = f"/episodes/{episode_num}/assets/thumbnails/protected/{protected_filename}"

        # Update database with protected thumbnail path
        episode.poster_16x9 = protected_url
        db.commit()

        logger.info(f"Saved protected thumbnail for episode {episode_number}: {protected_url}")

        return {
            "success": True,
            "message": "Thumbnail confirmed and protected",
            "original_url": source_url,
            "protected_url": protected_url,
            "protected_filename": protected_filename
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error taking thumbnail for episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to take thumbnail: {str(e)}")


@router.get("/{episode_number}/thumbnail/confirmed")
async def get_confirmed_thumbnail(
    episode_number: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get the confirmed/protected thumbnail for an episode from the database.

    Also attempts to find the original source URL by scanning the exports directory.
    """
    from models_v2 import Episode
    from core.paths import paths as path_manager

    try:
        episode = db.query(Episode).filter(Episode.episode_number == int(episode_number)).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        if episode.poster_16x9:
            # Verify the file still exists
            episode_num = path_manager._normalize_episode_id(episode_number)
            relative_path = episode.poster_16x9.replace('/episodes/', '')
            file_path = path_manager.episodes_root / relative_path

            # Try to find the original source URL by matching file content/size
            source_url = None
            if file_path.exists():
                protected_size = file_path.stat().st_size
                exports_dir = path_manager.get_exports_dir(episode_number)

                if exports_dir.exists():
                    # Pattern to match poster files
                    poster_pattern = re.compile(
                        r'^poster[_-]?(16x9)?[_-]?.*\.(jpg|jpeg|png|webp)$',
                        re.IGNORECASE
                    )

                    for export_file in exports_dir.iterdir():
                        if export_file.is_file() and poster_pattern.match(export_file.name):
                            # Match by file size (quick check)
                            if export_file.stat().st_size == protected_size:
                                source_url = f"/episodes/{episode_num}/exports/{export_file.name}"
                                break

            return {
                "confirmed": True,
                "url": episode.poster_16x9,
                "source_url": source_url,
                "exists": file_path.exists()
            }
        else:
            return {
                "confirmed": False,
                "url": None,
                "source_url": None,
                "exists": False
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting confirmed thumbnail for episode {episode_number}: {e}")
        return {"confirmed": False, "url": None, "source_url": None, "error": str(e)}
