"""
FSQ Asset Generation Router
Automatically generates PNG graphics for Full Screen Quote cues
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
import subprocess
import json
import tempfile
from datetime import datetime

from auth.router import get_current_user_or_key
from core.paths import ShowBuildPaths
from services.asset_processing import generate_fsq_png
from models_assetid import generate_assetid

router = APIRouter()
path_manager = ShowBuildPaths()


class FSQAssetRequest(BaseModel):
    episode_id: str
    quote: str
    source: str
    style: str = "centered"
    slug: str
    asset_id: str
    duration: str = "00:00:05:00"
    timestamp: Optional[str] = None
    description: Optional[str] = None


class FSQAssetResponse(BaseModel):
    success: bool
    asset_path: str
    asset_url: str
    message: str


class FSQAssetAsyncRequest(BaseModel):
    episode_id: str
    quote: str
    attribution: str
    slug: str
    asset_id: str
    alignment: str = "center"
    font_family: str = "serif"
    font_size: int = 70
    duration: str = "00:00:05:00"


class FSQAssetTaskResponse(BaseModel):
    success: bool
    task_id: str
    status: str
    message: str


class QuickQuoteRequest(BaseModel):
    quote: str
    attribution: str
    episode_id: str = "0247"


@router.post("/quick-quote", response_model=FSQAssetResponse)
async def generate_quick_quote(
    request: QuickQuoteRequest,
    current_user=Depends(get_current_user_or_key)
):
    """
    Generate a one-off FSQ quote with minimal input.
    Auto-generates: slug, AssetID
    Uses: render_fsq_quotes.py with 75% height, 80% opacity settings

    Perfect for quick quote generation without manual slug/ID management.
    """
    try:
        print(f"🚀 Quick Quote Generation")
        print(f"   Quote: {request.quote[:50]}...")
        print(f"   Attribution: {request.attribution}")

        # Auto-generate slug from first 3 words
        words = request.quote.split()[:3]
        slug = '-'.join(w.lower().strip('",.:;!?') for w in words)

        # Auto-generate AssetID
        asset_id = generate_assetid('FSQ')

        print(f"   Generated Slug: {slug}")
        print(f"   Generated AssetID: {asset_id}")

        # Create FSQAssetRequest using auto-generated values
        fsq_request = FSQAssetRequest(
            episode_id=request.episode_id,
            quote=request.quote,
            source=request.attribution,
            slug=slug,
            asset_id=asset_id,
            style="centered",
            duration="00:00:05:00"
        )

        # Call existing generate endpoint
        return await generate_fsq_asset(fsq_request, current_user)

    except Exception as e:
        print(f"   ❌ Quick quote generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Quick quote generation failed: {str(e)}"
        )


@router.post("/generate", response_model=FSQAssetResponse)
async def generate_fsq_asset(
    request: FSQAssetRequest,
    current_user=Depends(get_current_user_or_key)
):
    """
    Generate FSQ PNG asset automatically

    Process:
    1. Create temporary JSON with quote data
    2. Call render_fsq_png.py tool
    3. Move generated PNG to episode assets
    4. Return asset path/URL
    """
    try:
        print(f"📝 Generating FSQ asset for episode {request.episode_id}")
        print(f"   Quote: {request.quote[:50]}...")
        print(f"   Source: {request.source}")
        print(f"   Asset ID: {request.asset_id}")

        # Normalize episode ID
        episode_id = request.episode_id.zfill(4) if len(request.episode_id) < 4 else request.episode_id

        # Setup paths using ShowBuildPaths
        episode_dir = path_manager.get_episode_dir(episode_id)
        assets_dir = path_manager.get_asset_type_dir(episode_id, 'quotes')
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Create temporary JSON file with quote data
        quote_data = {
            "metadata": {
                "episode": episode_id,
                "generated_at": datetime.now().isoformat(),
                "asset_id": request.asset_id
            },
            "quotes": [
                {
                    "slug": request.slug,
                    "text": request.quote,
                    "attribution": request.source,
                    "duration": request.duration,
                    "metadata": {
                        "align": request.style,
                        "timestamp": request.timestamp or "",
                        "description": request.description or ""
                    }
                }
            ]
        }

        # Create temp JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            json.dump(quote_data, temp_file, indent=2, ensure_ascii=False)
            temp_json_path = temp_file.name

        print(f"   📄 Created temp JSON: {temp_json_path}")

        # Call render_fsq_png.py tool
        render_script = Path(__file__).parent.parent / "tools" / "render_fsq_png.py"

        if not render_script.exists():
            raise HTTPException(
                status_code=500,
                detail=f"FSQ render script not found: {render_script}"
            )

        # Execute rendering
        print(f"   🎨 Executing FSQ renderer...")
        result = subprocess.run(
            [
                "python3",
                str(render_script),
                "--json", temp_json_path,
                "--output", str(assets_dir),
                "--width", "1920",
                "--height", "1080"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Clean up temp file
        Path(temp_json_path).unlink(missing_ok=True)

        if result.returncode != 0:
            print(f"   ❌ Render failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"FSQ rendering failed: {result.stderr}"
            )

        print(f"   ✅ Render output: {result.stdout}")

        # Find generated PNG
        clean_slug = request.slug.lower().replace(' ', '-').replace('_', '-')
        expected_filename = f"fsq_{clean_slug}.png"
        asset_path = assets_dir / expected_filename

        if not asset_path.exists():
            # Try to find any PNG that was just created
            png_files = sorted(assets_dir.glob("fsq_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            if png_files:
                asset_path = png_files[0]
                print(f"   📁 Found generated PNG: {asset_path.name}")
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Generated PNG not found. Expected: {expected_filename}"
                )

        # Generate asset URL
        asset_relative_path = asset_path.relative_to(path_manager.episodes_root)
        asset_url = f"/episodes/{asset_relative_path}"

        print(f"   ✅ Asset generated successfully")
        print(f"   📁 Path: {asset_path}")
        print(f"   🔗 URL: {asset_url}")

        return FSQAssetResponse(
            success=True,
            asset_path=str(asset_path),
            asset_url=asset_url,
            message=f"FSQ asset generated successfully: {asset_path.name}"
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="FSQ rendering timed out after 30 seconds"
        )
    except Exception as e:
        print(f"   ❌ Error generating FSQ asset: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate FSQ asset: {str(e)}"
        )


@router.post("/regenerate/{asset_id}", response_model=FSQAssetResponse)
async def regenerate_fsq_asset(
    asset_id: str,
    request: FSQAssetRequest,
    current_user=Depends(get_current_user_or_key)
):
    """Regenerate an existing FSQ asset with updated data"""
    return await generate_fsq_asset(request, current_user)


@router.post("/generate-async", response_model=FSQAssetTaskResponse)
async def generate_fsq_asset_async(
    request: FSQAssetAsyncRequest,
    current_user=Depends(get_current_user_or_key)
):
    """
    Generate FSQ PNG asset asynchronously using Celery.

    This endpoint queues the FSQ PNG generation to a Celery worker,
    which can run on the local server or a remote Windows worker.

    Benefits:
    - Non-blocking: UI doesn't freeze during generation
    - Scalable: Can offload to dedicated worker machines
    - Retry logic: Automatic retries on failure
    - Progress tracking: Can monitor task status

    Returns:
        Task ID for monitoring progress via /tasks/{task_id} endpoint
    """
    try:
        print(f"📝 Queuing FSQ PNG generation for episode {request.episode_id}")
        print(f"   Quote: {request.quote[:50]}...")
        print(f"   Attribution: {request.attribution}")
        print(f"   Asset ID: {request.asset_id}")

        # Queue Celery task
        task = generate_fsq_png.apply_async(
            kwargs={
                'episode_id': request.episode_id,
                'quote': request.quote,
                'attribution': request.attribution,
                'slug': request.slug,
                'asset_id': request.asset_id,
                'alignment': request.alignment,
                'font_family': request.font_family,
                'font_size': request.font_size,
                'duration': request.duration
            },
            queue='assets'  # Use assets queue for FSQ generation
        )

        print(f"   ✅ Task queued: {task.id}")
        print(f"   📊 Queue: assets")
        print(f"   🔍 Monitor at: /api/tasks/{task.id}")

        return FSQAssetTaskResponse(
            success=True,
            task_id=task.id,
            status="QUEUED",
            message=f"FSQ PNG generation task queued: {task.id}"
        )

    except Exception as e:
        print(f"   ❌ Error queuing FSQ generation task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue FSQ generation task: {str(e)}"
        )


@router.get("/task/{task_id}")
async def get_fsq_task_status(
    task_id: str,
    current_user=Depends(get_current_user_or_key)
):
    """
    Get status of an FSQ PNG generation task.

    Returns task state and result if completed.
    """
    try:
        task_result = generate_fsq_png.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "state": task_result.state,
            "ready": task_result.ready(),
            "successful": task_result.successful() if task_result.ready() else None
        }

        if task_result.ready():
            if task_result.successful():
                response["result"] = task_result.result
            else:
                response["error"] = str(task_result.info)
        elif task_result.state == 'PROGRESS':
            response["progress"] = task_result.info

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )
