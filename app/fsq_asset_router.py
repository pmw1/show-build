"""
FSQ Asset Generation Router
Automatically generates PNG graphics for Full Screen Quote cues.

Architecture:
- All FSQ generation routes to Celery by default (non-blocking)
- Direct module import for rendering (no subprocess overhead)
- Priority queues: assets_high, assets, assets_low
- Files stored in: {episode}/assets/quotes/

Endpoints:
- POST /generate: Default async with 30s wait (high priority)
- POST /generate-async: Fire-and-forget with task ID (configurable priority)
- POST /regenerate-all/{episode_id}: Batch regeneration (low priority)
- GET /task/{task_id}: Poll task status
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from auth.router import get_current_user_or_key
from core.paths import ShowBuildPaths
from services.asset_processing import generate_fsq_png
from services.asset_id import AssetIDService
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter()
path_manager = ShowBuildPaths()


class FSQAssetRequest(BaseModel):
    episode_id: str
    quote: str
    source: str
    style: str = "center"  # Text alignment: left, center, right
    slug: str
    asset_id: str
    duration: str = "00:00:05:00"
    timestamp: Optional[str] = None
    description: Optional[str] = None
    enumerator: Optional[str] = None  # e.g., "10_05" for rundown position
    # Style parameters (new)
    font_family: str = "sans-serif"  # sans-serif or serif
    box_height: int = 80  # Black overlay height as % of canvas
    box_opacity: int = 75  # Black overlay opacity as %
    line_spacing: int = 30  # Line spacing as % of font size
    attribution_size: Optional[int] = None  # Fixed size in px, or None for auto


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
    alignment: str = "center"  # Text alignment: left, center, right
    font_family: str = "sans-serif"  # sans-serif or serif
    max_font_size: Optional[int] = None  # Maximum font size in px for auto-fitting (None = full auto)
    box_height: int = 80  # Black overlay height as % of canvas
    box_opacity: int = 75  # Black overlay opacity as %
    line_spacing: int = 30  # Line spacing as % of font size
    attribution_size: Optional[int] = None  # Fixed size in px, or None for auto
    duration: str = "00:00:05:00"
    enumerator: Optional[str] = None  # e.g., "10_05" for rundown position
    priority: str = "normal"  # Queue priority: high, normal, low


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
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
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

        # Auto-generate AssetID using AssetIDService
        asset_id = AssetIDService.request_asset_id(
            db=db,
            entity_type='fsq',
            reason='create',
            requested_by=current_user.get("username", current_user.get("client_name", "quick_quote")),
            context={"slug": slug, "quote": request.quote[:50]}
        )

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
    current_user=Depends(get_current_user_or_key),
    sync: bool = False
):
    """
    Generate FSQ PNG asset - routes to Celery by default for non-blocking operation.

    By default, this endpoint queues the generation to Celery and waits for completion
    (up to 30 seconds). For truly async operation, use /generate-async instead.

    Args:
        request: FSQ asset generation request
        sync: If True, uses direct rendering (blocks the API thread). Default: False

    Process (Celery - default):
    1. Queue task to Celery worker with high priority
    2. Wait for task completion (up to 30s)
    3. Return asset path/URL

    Process (sync=True):
    1. Import renderer module directly
    2. Render PNG synchronously
    3. Return asset path/URL
    """
    import re

    try:
        print(f"📝 Generating FSQ asset for episode {request.episode_id}")
        print(f"   Quote: {request.quote[:50]}...")
        print(f"   Source: {request.source}")
        print(f"   Asset ID: {request.asset_id}")
        print(f"   Mode: {'sync (direct)' if sync else 'async (Celery)'}")

        # Normalize episode ID
        episode_id = request.episode_id.zfill(4) if len(request.episode_id) < 4 else request.episode_id

        if sync:
            # SYNCHRONOUS MODE: Direct rendering (blocks API thread)
            # Use this only when immediate response is critical and Celery is unavailable
            import sys
            tools_dir = Path(__file__).parent.parent / "tools"
            if str(tools_dir) not in sys.path:
                sys.path.insert(0, str(tools_dir))

            from render_fsq_png import FSQPNGRenderer

            assets_dir = path_manager.get_asset_type_dir(episode_id, 'quotes')
            assets_dir.mkdir(parents=True, exist_ok=True)

            # Create renderer instance
            renderer = FSQPNGRenderer(
                width=1920,
                height=1080,
                font_family=request.font_family,
                box_height=request.box_height,
                box_opacity=request.box_opacity,
                line_spacing=request.line_spacing,
                attribution_size=request.attribution_size
            )

            # Build output filename
            clean_slug = request.slug.lower().replace(' ', '-').replace('_', '-')
            clean_slug = re.sub(r'[^\w\-]', '', clean_slug)

            if request.enumerator:
                output_filename = f"{request.enumerator}-{clean_slug}.png"
            else:
                output_filename = f"fsq_{clean_slug}.png"

            output_path = assets_dir / output_filename

            print(f"   🎨 Rendering FSQ PNG directly...")

            success = renderer.render_single(
                quote_text=request.quote,
                attribution=request.source,
                output_path=output_path,
                slug=request.slug,
                alignment=request.style
            )

            if not success:
                raise HTTPException(
                    status_code=500,
                    detail=f"FSQ rendering failed for slug: {request.slug}"
                )

            asset_relative_path = output_path.relative_to(path_manager.episodes_root)
            asset_url = f"/episodes/{asset_relative_path}"

            print(f"   ✅ Asset generated successfully (sync)")
            print(f"   📁 Path: {output_path}")
            print(f"   🔗 URL: {asset_url}")

            return FSQAssetResponse(
                success=True,
                asset_path=str(output_path),
                asset_url=asset_url,
                message=f"FSQ asset generated successfully (sync): {output_path.name}"
            )

        else:
            # ASYNCHRONOUS MODE: Queue to Celery and wait for result
            # This is the default - doesn't block the API thread during rendering
            print(f"   📤 Queuing to Celery worker (high priority)...")

            task = generate_fsq_png.apply_async(
                kwargs={
                    'episode_id': episode_id,
                    'quote': request.quote,
                    'attribution': request.source,
                    'slug': request.slug,
                    'asset_id': request.asset_id,
                    'alignment': request.style,
                    'font_family': request.font_family,
                    'box_height': request.box_height,
                    'box_opacity': request.box_opacity,
                    'line_spacing': request.line_spacing,
                    'attribution_size': request.attribution_size,
                    'duration': request.duration,
                    'enumerator': request.enumerator,
                    'priority': 'high'  # User-initiated = high priority
                },
                queue='assets_high'  # Explicitly use high priority queue
            )

            print(f"   ⏳ Waiting for task {task.id} to complete...")

            # Wait for result with timeout
            try:
                result = task.get(timeout=30)

                if result.get('success'):
                    print(f"   ✅ Asset generated successfully (Celery)")
                    print(f"   📁 Path: {result.get('asset_path')}")
                    print(f"   🔗 URL: {result.get('asset_url')}")

                    return FSQAssetResponse(
                        success=True,
                        asset_path=result.get('asset_path', ''),
                        asset_url=result.get('asset_url', ''),
                        message=result.get('message', 'FSQ asset generated successfully')
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"FSQ generation failed: {result.get('message', 'Unknown error')}"
                    )

            except TimeoutError:
                # Task is still running - return task ID for polling
                print(f"   ⏱️ Task {task.id} still running after 30s")
                raise HTTPException(
                    status_code=202,
                    detail=f"FSQ generation queued but not yet complete. Task ID: {task.id}. Poll /api/fsq/task/{task.id} for status."
                )

    except HTTPException:
        raise
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

    Priority Levels:
    - high: User-initiated single quote generation (immediate feedback needed)
    - normal: Standard batch operations (default)
    - low: Background regeneration, bulk updates

    Benefits:
    - Non-blocking: UI doesn't freeze during generation
    - Scalable: Can offload to dedicated worker machines
    - Retry logic: Automatic retries on failure
    - Progress tracking: Can monitor task status
    - Priority queues: High-priority tasks processed first

    Returns:
        Task ID for monitoring progress via /api/fsq/task/{task_id} endpoint
    """
    try:
        # Validate priority
        priority = request.priority.lower()
        if priority not in ('high', 'normal', 'low'):
            priority = 'normal'

        # FSQ tasks go to dedicated 'fsq' queue where Kairo worker listens
        # (Kairo has Pillow + render_fsq_png.py, Windows worker doesn't)
        queue_name = 'fsq'

        print(f"📝 Queuing FSQ PNG generation for episode {request.episode_id}")
        print(f"   Quote: {request.quote[:50]}...")
        print(f"   Attribution: {request.attribution}")
        print(f"   Asset ID: {request.asset_id}")
        print(f"   Priority: {priority} → Queue: {queue_name}")

        # Queue Celery task to FSQ queue
        task = generate_fsq_png.apply_async(
            kwargs={
                'episode_id': request.episode_id,
                'quote': request.quote,
                'attribution': request.attribution,
                'slug': request.slug,
                'asset_id': request.asset_id,
                'alignment': request.alignment,
                'font_family': request.font_family,
                'max_font_size': request.max_font_size,
                'box_height': request.box_height,
                'box_opacity': request.box_opacity,
                'line_spacing': request.line_spacing,
                'attribution_size': request.attribution_size,
                'duration': request.duration,
                'enumerator': request.enumerator,
                'priority': priority
            },
            queue=queue_name  # Route to FSQ queue (Kairo worker)
        )

        print(f"   ✅ Task queued: {task.id}")
        print(f"   📊 Queue: {queue_name}")
        print(f"   🔍 Monitor at: /api/fsq/task/{task.id}")

        return FSQAssetTaskResponse(
            success=True,
            task_id=task.id,
            status="QUEUED",
            message=f"FSQ PNG generation task queued ({priority} priority): {task.id}"
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


class FSQBatchRequest(BaseModel):
    regenerate_existing: bool = False  # If True, regenerate even if PNG exists


class FSQBatchResponse(BaseModel):
    success: bool
    episode_id: str
    total_fsqs: int
    generated: int
    skipped: int
    failed: int
    task_ids: list
    message: str


@router.post("/regenerate-all/{episode_id}", response_model=FSQBatchResponse)
async def regenerate_all_fsq_assets(
    episode_id: str,
    request: FSQBatchRequest = None,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Regenerate all FSQ PNG assets for an episode.

    This endpoint scans the episode's rundown for FSQ cue blocks and
    generates/regenerates PNG assets for each one.

    Args:
        episode_id: Episode identifier
        regenerate_existing: If True, regenerate even if PNG already exists

    Returns:
        Summary of batch generation with task IDs for monitoring
    """
    from models_v2 import RundownItem, Rundown, Episode
    import re

    # Extract regenerate_existing from request body (default False)
    regenerate_existing = request.regenerate_existing if request else False

    try:
        print(f"📦 Starting batch FSQ regeneration for episode {episode_id}")
        print(f"   Regenerate existing: {regenerate_existing}")

        # Normalize episode ID
        episode_id_normalized = episode_id.zfill(4) if len(episode_id) < 4 else episode_id

        # Get episode by episode_number string
        episode = db.query(Episode).filter(
            Episode.episode_number == int(episode_id_normalized)
        ).first()

        if not episode:
            print(f"   ⚠️ No episode found for number {episode_id_normalized}")
            return FSQBatchResponse(
                success=True,
                episode_id=episode_id,
                total_fsqs=0,
                generated=0,
                skipped=0,
                failed=0,
                task_ids=[],
                message="No episode found"
            )

        # Get rundown for this episode
        rundown = db.query(Rundown).filter(
            Rundown.episode_id == episode.id
        ).first()

        if not rundown:
            print(f"   ⚠️ No rundown found for episode {episode_id_normalized}")
            return FSQBatchResponse(
                success=True,
                episode_id=episode_id,
                total_fsqs=0,
                generated=0,
                skipped=0,
                failed=0,
                task_ids=[],
                message="No rundown found for this episode"
            )

        # Get all rundown items for this rundown
        rundown_items = db.query(RundownItem).filter(
            RundownItem.rundown_id == rundown.id
        ).order_by(RundownItem.order_in_rundown).all()

        if not rundown_items:
            print(f"   ⚠️ No rundown items found for episode {episode_id}")
            return FSQBatchResponse(
                success=True,
                episode_id=episode_id,
                total_fsqs=0,
                generated=0,
                skipped=0,
                failed=0,
                task_ids=[],
                message="No rundown items found for this episode"
            )

        # Parse FSQ cue blocks from script content
        fsq_cues = []
        fsq_pattern = re.compile(
            r'<!-- Begin Cue -->.*?'
            r'\[Type:\s*FSQ\].*?'
            r'<!-- End Cue -->',
            re.DOTALL | re.IGNORECASE
        )

        for item in rundown_items:
            if not item.script_content:
                continue

            matches = fsq_pattern.findall(item.script_content)
            for match in matches:
                # Extract cue data from match
                cue_data = _parse_cue_block(match)
                if cue_data and cue_data.get('quote'):
                    cue_data['rundown_order'] = item.order_in_rundown
                    cue_data['rundown_item_id'] = item.id
                    fsq_cues.append(cue_data)

        print(f"   📝 Found {len(fsq_cues)} FSQ cues")

        if not fsq_cues:
            return FSQBatchResponse(
                success=True,
                episode_id=episode_id,
                total_fsqs=0,
                generated=0,
                skipped=0,
                failed=0,
                task_ids=[],
                message="No FSQ cue blocks found in episode rundown"
            )

        # Check existing files and queue generation tasks
        generated = 0
        skipped = 0
        failed = 0
        task_ids = []
        cleaned = 0

        assets_dir = path_manager.get_asset_type_dir(episode_id, 'quotes')
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Clean up old quote files before regenerating
        # This ensures enumerated files don't conflict with old non-enumerated files
        if regenerate_existing:
            print(f"   🧹 Cleaning old quote files from {assets_dir}")
            for old_file in assets_dir.glob("*.png"):
                try:
                    old_file.unlink()
                    cleaned += 1
                    print(f"      Removed: {old_file.name}")
                except Exception as e:
                    print(f"      Failed to remove {old_file.name}: {e}")
            print(f"   🧹 Cleaned {cleaned} old files")

        for cue in fsq_cues:
            try:
                slug = cue.get('slug', 'quote')
                clean_slug = slug.lower().replace(' ', '-').replace('_', '-')
                enumerator = cue.get('enumerator')

                # Build expected filename
                if enumerator:
                    expected_filename = f"{enumerator}-{clean_slug}.png"
                else:
                    expected_filename = f"fsq_{clean_slug}.png"

                asset_path = assets_dir / expected_filename

                # Check if file exists
                if asset_path.exists() and not regenerate_existing:
                    print(f"   ⏭️ Skipping existing: {expected_filename}")
                    skipped += 1
                    continue

                # Scale the stored fontsize for readable output at 1920x1080
                # The modal slider (10-40px) represents "preview scale" values.
                # Quote text: 3x scaling as MAX (auto-fit will find optimal size)
                # Attribution: 2x scaling as MAX
                fontsize_raw = cue.get('fontsize', cue.get('fontSize', ''))
                max_fontsize = None
                if fontsize_raw:
                    try:
                        # Parse the stored value (e.g., "23px" -> 23)
                        raw_value = float(str(fontsize_raw).replace('px', '').strip())
                        # Apply 3x scaling as upper limit for auto-fitting
                        max_fontsize = int(raw_value * 3)
                    except (ValueError, AttributeError):
                        pass  # Fall back to default max (200px)

                # Scale attribution size at 2x (smaller than quote text)
                attribution_raw = cue.get('attributionSize', cue.get('attributionsize', ''))
                max_attribution_size = None
                if attribution_raw:
                    try:
                        raw_attr = float(str(attribution_raw).replace('px', '').strip())
                        max_attribution_size = int(raw_attr * 2)
                    except (ValueError, AttributeError):
                        pass  # Fall back to auto-sizing

                # Queue Celery task with low priority (batch operation)
                # Use max_font_size for auto-fitting (finds largest size that fits with 10% padding)
                task = generate_fsq_png.apply_async(
                    kwargs={
                        'episode_id': episode_id,
                        'quote': cue.get('quote', ''),
                        'attribution': cue.get('attribution', cue.get('source', '')),
                        'slug': slug,
                        'asset_id': cue.get('assetId', cue.get('asset_id', '')),
                        'alignment': cue.get('alignment', cue.get('style', 'center')),
                        'font_family': cue.get('fontFamily', cue.get('fontfamily', 'sans-serif')),
                        'max_font_size': max_fontsize,  # Upper limit for auto-fit (3x scaled)
                        'box_height': int(cue.get('boxHeight', cue.get('boxheight', 80))),
                        'box_opacity': int(cue.get('boxOpacity', cue.get('boxopacity', 75))),
                        'line_spacing': int(cue.get('lineSpacing', cue.get('linespacing', 30))),
                        'max_attribution_size': max_attribution_size,  # Upper limit (2x scaled)
                        'duration': cue.get('duration', '00:00:05:00'),
                        'enumerator': enumerator,
                        'priority': 'low'  # Batch regeneration uses low priority
                    },
                    queue='fsq'  # FSQ queue - Kairo worker handles this
                )

                task_ids.append(task.id)
                generated += 1
                print(f"   ✅ Queued: {expected_filename} (task: {task.id})")

            except Exception as e:
                print(f"   ❌ Failed to queue {cue.get('slug', 'unknown')}: {e}")
                failed += 1

        if cleaned > 0:
            message = f"Batch FSQ generation: {cleaned} old files cleaned, {generated} queued, {skipped} skipped, {failed} failed"
        else:
            message = f"Batch FSQ generation: {generated} queued, {skipped} skipped, {failed} failed"
        print(f"   📊 {message}")

        return FSQBatchResponse(
            success=True,
            episode_id=episode_id,
            total_fsqs=len(fsq_cues),
            generated=generated,
            skipped=skipped,
            failed=failed,
            task_ids=task_ids,
            message=message
        )

    except Exception as e:
        print(f"   ❌ Batch FSQ generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Batch FSQ generation failed: {str(e)}"
        )


def _parse_cue_block(cue_content: str) -> Dict[str, Any]:
    """
    Parse FSQ cue block content into a dictionary.

    Args:
        cue_content: Raw cue block content between Begin/End Cue markers

    Returns:
        dict: Parsed cue data
    """
    import re

    cue_data = {}

    # Parse field lines [Field: Value]
    field_pattern = re.compile(r'\[([^:]+):\s*([^\]]*)\]')

    for match in field_pattern.finditer(cue_content):
        field_name = match.group(1).strip()
        field_value = match.group(2).strip()

        # Convert field names to camelCase
        camel_field = _to_camel_case(field_name)

        # Strip quotes from quote field
        if camel_field.lower() == 'quote' and field_value:
            if field_value.startswith('"') or field_value.startswith("'"):
                field_value = field_value[1:]
            if field_value.endswith('"') or field_value.endswith("'"):
                field_value = field_value[:-1]

        cue_data[camel_field] = field_value

    return cue_data


def _to_camel_case(field_name: str) -> str:
    """Convert field name to camelCase."""
    words = field_name.replace('-', ' ').replace('_', ' ').split()
    if not words:
        return field_name
    result = words[0].lower()
    for word in words[1:]:
        result += word.capitalize()
    return result
