"""
vMix Integration Router
Sends rundown media to vMix list inputs via the vMix Web Controller API.

Endpoints:
- POST /vmix/build-list/{episode_number}: Build LIST1RAW from assets/rundown directory
"""

import re
import httpx
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from auth.router import get_current_user_or_key
from database import get_db

router = APIRouter(prefix="/vmix", tags=["vmix"])


def _get_vmix_config():
    """Load vMix config from api_configs table."""
    from api_config import APIConfigManager
    mgr = APIConfigManager()
    cfg = mgr.get_service_config("production", "control", "vmix") or {}
    return cfg


@router.post("/build-list/{episode_number}")
async def build_vmix_list(
    episode_number: str,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Build a vMix list input (LIST1RAW) from the assets/rundown directory.

    1. Reads all files from {episode}/assets/rundown/ sorted by filename
    2. Clears LIST1RAW via ListRemoveAll
    3. Adds each file via ListAdd with remapped Windows paths

    Requires: Run 'Gather for Show' first to populate assets/rundown/.
    """
    from models_v2 import Episode
    from core.paths import ShowBuildPaths

    # Load vMix config
    cfg = _get_vmix_config()
    host = cfg.get("host")
    port = cfg.get("port", "8088")
    enabled = cfg.get("enabled", False)
    remote_media_path = cfg.get("remoteMediaPath", "")

    if not enabled:
        raise HTTPException(status_code=400, detail="vMix integration is not enabled. Enable it in Settings > API Access.")
    if not host:
        raise HTTPException(status_code=400, detail="vMix host not configured. Set it in Settings > API Access.")
    if not remote_media_path:
        raise HTTPException(status_code=400, detail="Remote Media Path not configured. Set it in Settings > API Access > vMix.")

    vmix_api = f"http://{host}:{port}/api"

    # Normalize episode number
    episode_id = episode_number.zfill(4) if len(episode_number) < 4 else episode_number

    episode = db.query(Episode).filter(
        Episode.episode_number == int(episode_id)
    ).first()
    if not episode:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")

    # Scan assets/rundown directory
    path_manager = ShowBuildPaths()
    rundown_dir = path_manager.episodes_root / episode_id / "assets" / "rundown"

    if not rundown_dir.exists():
        raise HTTPException(
            status_code=404,
            detail="No assets/rundown directory found. Run 'Gather for Show' first."
        )

    # Get all media files with natural numeric sort (10, 20, 30... not 10, 100, 1000...)
    media_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mov', '.avi', '.mkv', '.webm', '.mp3', '.wav'}

    def natural_sort_key(path: Path):
        """Split filename into text and numeric parts for natural ordering."""
        return [int(part) if part.isdigit() else part.lower()
                for part in re.split(r'(\d+)', path.name)]

    files = sorted(
        [f for f in rundown_dir.iterdir()
         if f.is_file() and f.suffix.lower() in media_extensions],
        key=natural_sort_key
    )

    if not files:
        return {
            "success": True,
            "total": 0,
            "added": 0,
            "failed": 0,
            "items": [],
            "message": "No media files found in assets/rundown. Run 'Gather for Show' first."
        }

    # Build remote path prefix
    resolved_prefix = remote_media_path.replace('{episode_number}', episode_id)
    resolved_prefix = resolved_prefix.rstrip('\\').rstrip('/')

    # Build media items list
    media_items = []
    for f in files:
        remote_path = f"{resolved_prefix}\\{f.name}"
        media_items.append({
            "filename": f.name,
            "localPath": str(f),
            "remotePath": remote_path,
        })

    results = []
    added = 0
    failed = 0

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Step 1: Clear the list
        try:
            print(f"📺 vMix: Clearing LIST1RAW on {host}:{port}")
            resp = await client.get(vmix_api, params={
                "Function": "ListRemoveAll",
                "Input": "LIST1RAW"
            })
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"vMix ListRemoveAll failed with HTTP {resp.status_code}"
                )
            print(f"   ✅ LIST1RAW cleared")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail=f"Cannot connect to vMix at {host}:{port}")
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail=f"vMix connection timed out at {host}:{port}")

        # Step 2: Add each media file
        for item in media_items:
            try:
                resp = await client.get(vmix_api, params={
                    "Function": "ListAdd",
                    "Input": "LIST1RAW",
                    "Value": item["remotePath"]
                })
                if resp.status_code == 200:
                    item["status"] = "ok"
                    added += 1
                    print(f"   ✅ Added {item['filename']}: {item['remotePath']}")
                else:
                    item["status"] = "error"
                    item["error"] = f"HTTP {resp.status_code}"
                    failed += 1
                    print(f"   ❌ Failed {item['filename']}: HTTP {resp.status_code}")
            except Exception as e:
                item["status"] = "error"
                item["error"] = str(e)
                failed += 1
                print(f"   ❌ Failed {item['filename']}: {e}")

            results.append(item)

    print(f"📺 vMix build complete: {added} added, {failed} failed out of {len(media_items)} items")

    return {
        "success": failed == 0,
        "total": len(media_items),
        "added": added,
        "failed": failed,
        "items": results
    }
