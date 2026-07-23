"""
GFX Asset Generation Router
Generates PNG/video graphics for Full Screen Text and other GFX cues.

Architecture:
- All GFX generation routes to Celery by default (non-blocking)
- Priority queues: assets_high, assets, assets_low
- Files stored in: {episode}/assets/graphics/

Endpoints:
- POST /generate: Default async with 30s wait (high priority)
- POST /generate-async: Fire-and-forget with task ID (configurable priority)
- GET /task/{task_id}: Poll task status
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from auth.router import get_current_user_or_key
from services.asset_processing import generate_gfx_png
from services.xpost_renderer import generate_xpost_png
from models.settings import GfxXpostCue
from database import get_db
from sqlalchemy.orm import Session
from celery_jobs_router import register_celery_job

router = APIRouter()


class GFXAssetRequest(BaseModel):
    episode_id: str
    gfx_type: str = "fullscreen-text"
    body: str
    slug: str
    asset_id: str
    title: Optional[str] = None
    alignment: str = "center"
    font_family: str = "sans-serif"
    font_size: int = 25
    # Title font size in modal-pixel units (scaled 2.5x at render time, like
    # font_size). Frontend slider default 36; None means "auto = 1.3 * body".
    title_font_size: Optional[int] = None
    # Inter-line gap as a percent of the body font size (10-60). 30 ≈ the
    # current renderer default (`int(scaled_font_size * 0.3)`).
    line_spacing: int = 30
    # Black-bar overlay sizing/opacity. Defaults match the previous fixed
    # values: 80% canvas height, 75% opacity (renderer alpha=191).
    box_height: int = 80
    box_opacity: int = 75
    # Vertical shift of the title+body text block, as a percent of the
    # black-bar height. Range -40..+40; 0 = vertically centered (default).
    vertical_offset: int = 0
    render_mode: str = "png"
    priority: str = "normal"


class GFXAssetResponse(BaseModel):
    success: bool
    asset_path: str
    asset_url: str
    message: str


class GFXAssetTaskResponse(BaseModel):
    success: bool
    task_id: str
    status: str
    message: str


@router.post("/generate", response_model=GFXAssetResponse)
async def generate_gfx_asset(
    request: GFXAssetRequest,
    current_user=Depends(get_current_user_or_key)
):
    """
    Generate GFX PNG asset - routes to Celery and waits for completion.

    Args:
        request: GFX asset generation request

    Process:
    1. Queue task to Celery worker with high priority
    2. Wait for task completion (up to 30s)
    3. Return asset path/URL
    """
    try:
        print(f"🎨 Generating GFX asset for episode {request.episode_id}")
        print(f"   GFX Type: {request.gfx_type}")
        print(f"   Body: {request.body[:50]}...")
        print(f"   Asset ID: {request.asset_id}")

        # Normalize episode ID
        episode_id = request.episode_id.zfill(4) if len(request.episode_id) < 4 else request.episode_id

        print(f"   📤 Queuing to Celery worker (high priority)...")

        task = generate_gfx_png.apply_async(
            kwargs={
                'episode_id': episode_id,
                'gfx_type': request.gfx_type,
                'body': request.body,
                'slug': request.slug,
                'asset_id': request.asset_id,
                'title': request.title,
                'alignment': request.alignment,
                'font_family': request.font_family,
                'font_size': request.font_size,
                'title_font_size': request.title_font_size,
                'line_spacing': request.line_spacing,
                'box_height': request.box_height,
                'box_opacity': request.box_opacity,
                'vertical_offset': request.vertical_offset,
                'render_mode': request.render_mode,
                'priority': 'high'
            },
            queue='assets_high'
        )

        print(f"   ⏳ Waiting for task {task.id} to complete...")

        # Wait for result with timeout
        try:
            result = task.get(timeout=30)

            if result.get('success'):
                print(f"   ✅ Asset generated successfully (Celery)")
                print(f"   📁 Path: {result.get('asset_path')}")
                print(f"   🔗 URL: {result.get('asset_url')}")

                return GFXAssetResponse(
                    success=True,
                    asset_path=result.get('asset_path', ''),
                    asset_url=result.get('asset_url', ''),
                    message=result.get('message', 'GFX asset generated successfully')
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"GFX generation failed: {result.get('message', 'Unknown error')}"
                )

        except TimeoutError:
            print(f"   ⏱️ Task {task.id} still running after 30s")
            raise HTTPException(
                status_code=202,
                detail=f"GFX generation queued but not yet complete. Task ID: {task.id}. Poll /api/gfx/task/{task.id} for status."
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ Error generating GFX asset: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate GFX asset: {str(e)}"
        )


@router.post("/generate-async", response_model=GFXAssetTaskResponse)
async def generate_gfx_asset_async(
    request: GFXAssetRequest,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Generate GFX PNG asset asynchronously using Celery.

    Returns task ID for monitoring progress via /api/gfx/task/{task_id} endpoint.
    """
    try:
        priority = request.priority.lower()
        if priority not in ('high', 'normal', 'low'):
            priority = 'normal'

        queue_map = {
            'high': 'assets_high',
            'normal': 'assets',
            'low': 'assets_low'
        }
        queue_name = queue_map[priority]

        print(f"🎨 Queuing GFX PNG generation for episode {request.episode_id}")
        print(f"   GFX Type: {request.gfx_type}")
        print(f"   Body: {request.body[:50]}...")
        print(f"   Asset ID: {request.asset_id}")
        print(f"   Priority: {priority} → Queue: {queue_name}")

        # Normalize episode ID
        episode_id = request.episode_id.zfill(4) if len(request.episode_id) < 4 else request.episode_id

        task = generate_gfx_png.apply_async(
            kwargs={
                'episode_id': episode_id,
                'gfx_type': request.gfx_type,
                'body': request.body,
                'slug': request.slug,
                'asset_id': request.asset_id,
                'title': request.title,
                'alignment': request.alignment,
                'font_family': request.font_family,
                'font_size': request.font_size,
                'title_font_size': request.title_font_size,
                'line_spacing': request.line_spacing,
                'box_height': request.box_height,
                'box_opacity': request.box_opacity,
                'vertical_offset': request.vertical_offset,
                'render_mode': request.render_mode,
                'priority': priority
            },
            queue=queue_name
        )

        print(f"   ✅ Task queued: {task.id}")

        register_celery_job(db, task.id, "services.asset_processing.generate_gfx_png", "Generate GFX", "assets", episode_id, queue_name)

        return GFXAssetTaskResponse(
            success=True,
            task_id=task.id,
            status="QUEUED",
            message=f"GFX PNG generation task queued ({priority} priority): {task.id}"
        )

    except Exception as e:
        print(f"   ❌ Error queuing GFX generation task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue GFX generation task: {str(e)}"
        )


class GFXBatchRequest(BaseModel):
    regenerate_existing: bool = False


class GFXBatchResponse(BaseModel):
    success: bool
    episode_id: str
    total_gfxs: int
    generated: int
    skipped: int
    failed: int
    task_ids: list
    message: str


@router.post("/regenerate-all/{episode_id}", response_model=GFXBatchResponse)
async def regenerate_all_gfx_assets(
    episode_id: str,
    request: GFXBatchRequest = None,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Regenerate all GFX PNG assets for an episode.

    Scans the episode's rundown for GFX cue blocks and queues PNG
    generation for each. Mirrors the FSQ batch regeneration endpoint.
    """
    from models_v2 import RundownItem, Rundown, Episode
    from core.paths import ShowBuildPaths
    import re

    path_manager = ShowBuildPaths()
    regenerate_existing = request.regenerate_existing if request else False

    try:
        print(f"📦 Starting batch GFX regeneration for episode {episode_id}")
        print(f"   Regenerate existing: {regenerate_existing}")

        episode_id_normalized = episode_id.zfill(4) if len(episode_id) < 4 else episode_id

        episode = db.query(Episode).filter(
            Episode.episode_number == int(episode_id_normalized)
        ).first()

        if not episode:
            return GFXBatchResponse(
                success=True, episode_id=episode_id, total_gfxs=0,
                generated=0, skipped=0, failed=0, task_ids=[],
                message="No episode found"
            )

        rundown = db.query(Rundown).filter(
            Rundown.episode_id == episode.id
        ).first()

        if not rundown:
            return GFXBatchResponse(
                success=True, episode_id=episode_id, total_gfxs=0,
                generated=0, skipped=0, failed=0, task_ids=[],
                message="No rundown found for this episode"
            )

        rundown_items = db.query(RundownItem).filter(
            RundownItem.rundown_id == rundown.id
        ).order_by(RundownItem.order_in_rundown).all()

        if not rundown_items:
            return GFXBatchResponse(
                success=True, episode_id=episode_id, total_gfxs=0,
                generated=0, skipped=0, failed=0, task_ids=[],
                message="No rundown items found"
            )

        gfx_pattern = re.compile(
            r'<!-- Begin Cue(?: collapsed)? -->.*?'
            r'\[Type:\s*GFX\].*?'
            r'<!-- End Cue -->',
            re.DOTALL | re.IGNORECASE
        )

        gfx_cues = []
        for item in rundown_items:
            if not item.script_content:
                continue
            for match in gfx_pattern.findall(item.script_content):
                cue_data = _parse_gfx_cue_block(match)
                if not cue_data:
                    continue
                # NB: _to_camel_case lowercases single-word field names, so
                # [GfxType:] parses to 'gfxtype' and [AssetID:] to 'assetid'.
                # Read both spellings defensively.
                is_xpost = (cue_data.get('gfxtype') or cue_data.get('gfxType') or '').lower() == 'xpost'
                if is_xpost:
                    # xpost renders from its gfx_xpost_cues row, keyed by AssetID.
                    # It MUST NOT fall through to the fullscreen-text renderer —
                    # that would overwrite the tweet PNG with a blank text frame.
                    if not (cue_data.get('assetid') or cue_data.get('assetId')):
                        continue
                    cue_data['_isXpost'] = True
                elif not (cue_data.get('body') or cue_data.get('title') or cue_data.get('listItems')):
                    # Need a body (or title/list) to render — match frontend rule
                    continue
                cue_data['rundown_item_id'] = item.id
                gfx_cues.append(cue_data)

        print(f"   📝 Found {len(gfx_cues)} GFX cues")

        if not gfx_cues:
            return GFXBatchResponse(
                success=True, episode_id=episode_id, total_gfxs=0,
                generated=0, skipped=0, failed=0, task_ids=[],
                message="No GFX cue blocks found in episode rundown"
            )

        generated = 0
        skipped = 0
        failed = 0
        task_ids = []
        cleaned = 0

        assets_dir = path_manager.get_asset_type_dir(episode_id_normalized, 'graphics')
        assets_dir.mkdir(parents=True, exist_ok=True)

        # When regenerating, sweep existing GFX PNGs so stale enumerated names
        # do not collide with freshly rendered files. Mirrors FSQ behavior.
        if regenerate_existing:
            print(f"   🧹 Cleaning old GFX files from {assets_dir}")
            for old_file in assets_dir.glob("*.png"):
                try:
                    old_file.unlink()
                    cleaned += 1
                except Exception as e:
                    print(f"      Failed to remove {old_file.name}: {e}")
            print(f"   🧹 Cleaned {cleaned} old files")

        for cue in gfx_cues:
            try:
                slug = cue.get('slug', 'gfx')
                clean_slug = slug.lower().replace(' ', '-').replace('_', '-')
                enumerator = cue.get('enumerator')

                if enumerator:
                    expected_filename = f"{enumerator}-{clean_slug}.png"
                else:
                    expected_filename = f"gfx_{clean_slug}.png"

                if cue.get('_isXpost'):
                    # X-post renders live in their dedicated directory.
                    asset_path = assets_dir.parent / 'gfx' / 'xpost' / expected_filename
                else:
                    asset_path = assets_dir / expected_filename

                if asset_path.exists() and not regenerate_existing:
                    print(f"   ⏭️ Skipping existing: {expected_filename}")
                    skipped += 1
                    continue

                # xpost cues render via the dedicated tweet-card task from
                # their gfx_xpost_cues row — never the fullscreen-text renderer.
                if cue.get('_isXpost'):
                    xp_asset_id = cue.get('assetid') or cue.get('assetId') or ''
                    xp_row = db.query(GfxXpostCue).filter(
                        GfxXpostCue.asset_id == xp_asset_id
                    ).first()
                    if not xp_row:
                        print(f"   ⏭️ Skipping xpost {xp_asset_id}: no captured row in gfx_xpost_cues")
                        skipped += 1
                        continue
                    task = generate_xpost_png.apply_async(
                        kwargs={
                            'asset_id': xp_asset_id,
                            'episode_id': episode_id_normalized,
                            'priority': 'low',
                        },
                        queue='xpost'
                    )
                    task_ids.append(task.id)
                    generated += 1
                    print(f"   ✅ Queued xpost: {expected_filename} (task: {task.id})")
                    continue

                font_size_raw = cue.get('fontSize', '')
                font_size = 25
                if font_size_raw:
                    try:
                        font_size = int(float(str(font_size_raw).replace('px', '').strip()))
                    except (ValueError, AttributeError):
                        pass

                vertical_offset_raw = cue.get('verticalOffset', 0)
                try:
                    vertical_offset = int(float(str(vertical_offset_raw)))
                except (ValueError, AttributeError):
                    vertical_offset = 0

                task = generate_gfx_png.apply_async(
                    kwargs={
                        'episode_id': episode_id_normalized,
                        'gfx_type': cue.get('gfxType', 'fullscreen-text'),
                        'body': (cue.get('body', '') or '').replace('\\n', '\n'),
                        'slug': slug,
                        'asset_id': cue.get('assetId', cue.get('asset_id', '')),
                        'title': cue.get('title'),
                        'alignment': cue.get('textAlign', cue.get('alignment', 'center')),
                        'font_family': cue.get('fontFamily', 'sans-serif'),
                        'font_size': font_size,
                        'vertical_offset': vertical_offset,
                        'render_mode': cue.get('renderMode', 'png'),
                        'priority': 'low'
                    },
                    queue='assets_low'
                )

                task_ids.append(task.id)
                generated += 1
                print(f"   ✅ Queued: {expected_filename} (task: {task.id})")

            except Exception as e:
                print(f"   ❌ Failed to queue {cue.get('slug', 'unknown')}: {e}")
                failed += 1

        if cleaned > 0:
            message = f"Batch GFX generation: {cleaned} old files cleaned, {generated} queued, {skipped} skipped, {failed} failed"
        else:
            message = f"Batch GFX generation: {generated} queued, {skipped} skipped, {failed} failed"
        print(f"   📊 {message}")

        return GFXBatchResponse(
            success=True,
            episode_id=episode_id,
            total_gfxs=len(gfx_cues),
            generated=generated,
            skipped=skipped,
            failed=failed,
            task_ids=task_ids,
            message=message
        )

    except Exception as e:
        print(f"   ❌ Batch GFX generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Batch GFX generation failed: {str(e)}"
        )


def _parse_gfx_cue_block(cue_content: str) -> dict:
    """Parse a GFX cue block into a dict (camelCase keys)."""
    import re
    cue_data = {}
    field_pattern = re.compile(r'^\s*\[([^:]+):\s*(.*)\]\s*$')
    for line in cue_content.split('\n'):
        match = field_pattern.match(line)
        if not match:
            continue
        field_name = match.group(1).strip()
        field_value = match.group(2).strip()
        cue_data[_to_camel_case(field_name)] = field_value
    return cue_data


def _to_camel_case(field_name: str) -> str:
    words = field_name.replace('-', ' ').replace('_', ' ').split()
    if not words:
        return field_name
    result = words[0].lower()
    for word in words[1:]:
        result += word.capitalize()
    return result


@router.get("/task/{task_id}")
async def get_gfx_task_status(
    task_id: str,
    current_user=Depends(get_current_user_or_key)
):
    """
    Get status of a GFX PNG generation task.

    Returns task state and result if completed.
    """
    try:
        task_result = generate_gfx_png.AsyncResult(task_id)

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


# ═══════════════════════════════════════════════════════════════════════════
# X-Post (tweet) GFX cues — capture + render
#
# The cue block in script_content stays the editorial source of truth; this
# table is the structured mirror + archival capture. captured_at/captured_by/
# full_metadata are set ONCE on first upsert and never updated — the "what did
# the tweet say when we saved it" record. Rendering runs on the dedicated
# 'xpost' queue (services/xpost_renderer.py).
# ═══════════════════════════════════════════════════════════════════════════

class XpostCueUpsertRequest(BaseModel):
    asset_id: str
    episode_number: str
    slug: str
    # Author
    xpost_name: Optional[str] = None
    xpost_username: Optional[str] = None
    xpost_profile_photo: Optional[str] = None
    xpost_verified: Optional[bool] = False
    xpost_bio: Optional[str] = None
    xpost_followers: Optional[int] = None
    xpost_following: Optional[int] = None
    # Post content
    xpost_post_text: Optional[str] = None
    xpost_tweet_id: Optional[str] = None
    xpost_conversation_id: Optional[str] = None
    # Media
    xpost_media_urls: Optional[List[Any]] = None
    xpost_media_objects: Optional[List[Any]] = None
    # Timing (ISO-8601 string, Z tolerated)
    xpost_datetime: Optional[str] = None
    # Engagement
    xpost_view_count: Optional[int] = None
    xpost_likes: Optional[int] = None
    xpost_retweets: Optional[int] = None
    xpost_replies: Optional[int] = None
    xpost_quotes: Optional[int] = None
    xpost_bookmarks: Optional[int] = None
    # Source
    xpost_source_url: Optional[str] = None
    xpost_platform: Optional[str] = 'x'
    xpost_entities: Optional[Dict[str, Any]] = None
    xpost_referenced_tweets: Optional[List[Any]] = None
    # Rendering / editorial
    aspect_ratio: Optional[str] = None
    title: Optional[str] = None
    notes: Optional[List[Dict[str, Any]]] = None
    display_sequence: Optional[Dict[str, Any]] = None
    enumerator: Optional[str] = None
    whiteboard_item_id: Optional[int] = None
    duration: Optional[str] = None
    # Archival + dispatch
    full_metadata: Optional[Dict[str, Any]] = None
    render: bool = True
    priority: str = 'high'


def _parse_xpost_datetime(value: Optional[str]):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None


# Fields copied verbatim from the request onto the row on every upsert.
_XPOST_MUTABLE_FIELDS = [
    'slug', 'xpost_name', 'xpost_username', 'xpost_profile_photo',
    'xpost_verified', 'xpost_bio', 'xpost_followers', 'xpost_following',
    'xpost_post_text', 'xpost_tweet_id', 'xpost_conversation_id',
    'xpost_media_urls', 'xpost_media_objects',
    'xpost_view_count', 'xpost_likes', 'xpost_retweets', 'xpost_replies',
    'xpost_quotes', 'xpost_bookmarks',
    'xpost_source_url', 'xpost_platform', 'xpost_entities',
    'xpost_referenced_tweets', 'aspect_ratio', 'title', 'notes',
    'display_sequence', 'enumerator', 'whiteboard_item_id', 'duration',
]


def _xpost_row_to_dict(row: GfxXpostCue) -> dict:
    out = {}
    for col in row.__table__.columns:
        val = getattr(row, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        out[col.name] = val
    return out


def _dispatch_xpost_render(db: Session, row: GfxXpostCue, episode_id: str, priority: str = 'high') -> str:
    task = generate_xpost_png.apply_async(
        kwargs={
            'asset_id': row.asset_id,
            'episode_id': episode_id,
            'priority': priority,
        },
        queue='xpost'
    )
    register_celery_job(
        db, task.id, "services.xpost_renderer.generate_xpost_png",
        "Render X-Post GFX", "assets", episode_id, "xpost"
    )
    row.last_render_task_id = task.id
    db.commit()
    return task.id


@router.post("/xpost")
async def upsert_xpost_cue(
    request: XpostCueUpsertRequest,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Upsert an X-post cue's structured/archival record and (by default)
    dispatch the tweet-card PNG render.

    First insert stamps the immutable capture: captured_at, captured_by,
    full_metadata. Later upserts refresh only the mutable fields.
    """
    try:
        episode_id = request.episode_number.zfill(4) if len(request.episode_number) < 4 else request.episode_number

        row = db.query(GfxXpostCue).filter(GfxXpostCue.asset_id == request.asset_id).first()
        created = row is None
        if created:
            row = GfxXpostCue(asset_id=request.asset_id)
            row.captured_at = datetime.now(timezone.utc)
            row.captured_by = (current_user or {}).get('username') if isinstance(current_user, dict) else None
            row.full_metadata = request.full_metadata
            row.status = 'pending'
            db.add(row)
        elif row.full_metadata is None and request.full_metadata is not None:
            # Capture stamp is immutable, but backfill an empty archive.
            row.full_metadata = request.full_metadata

        row.episode_number = episode_id
        for field in _XPOST_MUTABLE_FIELDS:
            value = getattr(request, field)
            if field == 'duration' and value is None:
                continue  # keep column default
            setattr(row, field, value)
        row.xpost_datetime = _parse_xpost_datetime(request.xpost_datetime)

        db.commit()
        db.refresh(row)

        task_id = None
        if request.render:
            task_id = _dispatch_xpost_render(db, row, episode_id, request.priority)

        print(f"🐦 X-post cue {'captured' if created else 'updated'}: {row.asset_id}"
              f" (captured_at={row.captured_at}, render task={task_id})")

        return {
            "success": True,
            "id": row.id,
            "asset_id": row.asset_id,
            "created": created,
            "captured_at": row.captured_at.isoformat() if row.captured_at else None,
            "task_id": task_id,
        }

    except Exception as e:
        db.rollback()
        print(f"   ❌ X-post upsert failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"X-post upsert failed: {str(e)}")


@router.post("/xpost/{asset_id}/render")
async def render_xpost_cue(
    asset_id: str,
    priority: str = 'high',
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Re-render the tweet-card PNG for an already-captured X-post cue."""
    row = db.query(GfxXpostCue).filter(GfxXpostCue.asset_id == asset_id).first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"No captured X-post data for AssetID {asset_id} — POST /api/gfx/xpost first."
        )
    try:
        task_id = _dispatch_xpost_render(db, row, row.episode_number, priority)
        return {"success": True, "task_id": task_id, "asset_id": asset_id, "status": "QUEUED"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to queue X-post render: {str(e)}")


@router.get("/xpost/{asset_id}")
async def get_xpost_cue(
    asset_id: str,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Fetch the structured/archival record for an X-post cue."""
    row = db.query(GfxXpostCue).filter(GfxXpostCue.asset_id == asset_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"No X-post cue for AssetID {asset_id}")
    return _xpost_row_to_dict(row)
