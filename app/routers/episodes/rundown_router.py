"""
Rundown item CRUD and management router.
Handles rundown listing, item creation/update/delete, reordering, and normalization.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional, List, Dict, Any
from pathlib import Path
import yaml
import re
import logging
from auth.utils import get_current_user_or_key
from database import get_db
from sqlalchemy.orm import Session
from datetime import datetime

from ._shared import (
    EPISODES_ROOT, ReorderRequest, create_content_version,
    normalize_rundown_items, logger
)

router = APIRouter()


@router.post("/regenerate-description")
async def regenerate_description(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Regenerate a segment description with user feedback about what to change.
    Calls the LLM with the original prompt + previous description + feedback.
    """
    asset_id = payload.get('asset_id')
    previous_description = payload.get('previous_description', '')
    feedback = payload.get('feedback', '')

    if not asset_id:
        raise HTTPException(status_code=400, detail="asset_id is required")

    try:
        from services.auto_description_service import regenerate_segment_description
        result = regenerate_segment_description(asset_id, previous_description, feedback)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Regeneration failed for {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


@router.post("/rundown/{episode_number}/reorder")
async def reorder_rundown(
    episode_number: str,
    payload: ReorderRequest,
    current_user: Optional[dict] = None,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Update order_in_rundown in database for each rundown segment.

    Accepts segments with either 'asset_id' or 'filename' to identify items.
    """
    from models_v2 import Episode, Rundown, RundownItem

    try:
        episode_num_int = int(episode_number)
        episode = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
        if not rundown:
            raise HTTPException(status_code=404, detail=f"No rundown found for episode {episode_number}")

        updated_count = 0
        for segment in payload.segments:
            new_order = segment.get("order")
            if new_order is None:
                continue

            asset_id = segment.get("asset_id")
            filename = segment.get("filename")

            item = None
            if asset_id:
                item = db.query(RundownItem).filter(
                    RundownItem.asset_id == asset_id,
                    RundownItem.rundown_id == rundown.id
                ).first()

            if not item and filename:
                # Try to match by filename pattern — items have generated filenames
                # like "010-slug.md" based on order + slug
                items = db.query(RundownItem).filter(
                    RundownItem.rundown_id == rundown.id
                ).all()
                for candidate in items:
                    candidate_filename = f"{(candidate.order_in_rundown or 0):03d}-{candidate.slug}.md"
                    if candidate_filename == filename:
                        item = candidate
                        break

            if item:
                item.order_in_rundown = new_order
                item.updated_at = datetime.now()
                updated_count += 1

        db.commit()
        logger.info(f"Reordered {updated_count} items for episode {episode_number}")

        return {"status": "success", "message": f"Rundown order updated ({updated_count} items)"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reorder rundown: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reorder rundown: {str(e)}")


@router.get("/rundown-item/{asset_id}")
async def get_rundown_item_by_asset_id(asset_id: str, db: Session = Depends(get_db)):
    """Get a single rundown item by asset_id (used for live refresh after LLM updates)."""
    from models.episode import RundownItem
    item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Rundown item {asset_id} not found")
    return {
        "asset_id": item.asset_id,
        "description": item.description or '',
        "description_model": getattr(item, 'description_model', None) or '',
        "tone": item.tone or '',
        "tone_rationale": item.tone_rationale or '',
        "tone_confidence": item.tone_confidence,
        "llm_generated_fields": item.llm_generated_fields or [],
    }


@router.get("/{episode_number}/rundown")
async def get_episode_rundown(episode_number: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get all rundown items for an episode from database.

    Returns unified list of:
    - Regular rundown_items (source: 'rundown_item')
    - Content library placements (source: 'library')
    """
    from models_v2 import Episode, Rundown, RundownItem
    from services.cue_extractor import extract_cues

    try:
        # Convert episode number to int
        episode_num_int = int(episode_number)

        # Get episode from database
        episode = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        # Get rundowns for this episode
        rundowns = db.query(Rundown).filter(Rundown.episode_id == episode.id).all()
        if not rundowns:
            # Return empty rundown if no rundowns exist yet
            return {"items": []}

        # Get all rundown items for all rundowns of this episode
        rundown_items = []
        for rundown in rundowns:
            # Get regular rundown items
            items = db.query(RundownItem).filter(RundownItem.rundown_id == rundown.id).order_by(RundownItem.order_in_rundown).all()

            for item in items:
                order_value = item.order_in_rundown or 0
                script_content = item.script_content or ''
                rundown_item_dict = {
                    "id": item.asset_id,  # Legacy: asset_id as primary identifier for frontend
                    "db_id": item.id,     # Database integer ID for API operations
                    "type": item.item_type or 'segment',
                    "slug": item.slug or '',
                    "duration": item.duration or '00:00:00',
                    "script": script_content,  # Script content from new field
                    "cues": extract_cues(script_content),  # Structured cues parsed server-side
                    "order": order_value,
                    "order_in_rundown": order_value,  # Explicit field for frontend
                    "index": order_value,  # Explicit field for frontend
                    "status": item.status or 'draft',
                    "title": item.title or item.slug or 'Untitled',
                    "subtitle": item.subtitle or '',
                    "description": item.description or '',  # Metadata description
                    "filename": f"{order_value:03d}-{item.slug}.md",  # Generate filename for compatibility
                    "asset_id": item.asset_id,
                    "block_letter": item.block_letter or '',
                    "airdate": item.airdate.isoformat() if item.airdate else '',
                    "guests": item.guests or '',
                    "resources": item.resources or '',
                    "tags": item.tags or '',
                    "priority": item.priority or '',
                    "server_message": item.server_message or '',
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                    "tone": item.tone or '',
                    "tone_rationale": item.tone_rationale or '',
                    "tone_confidence": item.tone_confidence,
                    "llm_generated_fields": item.llm_generated_fields or [],
                    "auto_description_enabled": getattr(item, 'auto_description_enabled', True),
                    "description_model": getattr(item, 'description_model', None) or '',
                    "source": "rundown_item"  # Distinguish from library placements
                }
                rundown_items.append(rundown_item_dict)

            # Get content library placements (active only - removed_at is NULL)
            try:
                from models_content_library import ContentPlacement, ContentLibrary
                placements = db.query(ContentPlacement, ContentLibrary).join(
                    ContentLibrary, ContentPlacement.library_item_id == ContentLibrary.id
                ).filter(
                    ContentPlacement.rundown_id == rundown.id,
                    ContentPlacement.removed_at == None  # Only active placements
                ).all()

                for placement, library_item in placements:
                    order_value = placement.order_in_rundown or 0
                    # Use snapshot if available, otherwise use current library item data
                    snapshot = placement.content_snapshot or {}

                    placement_dict = {
                        "id": library_item.asset_id,  # Library item's asset_id
                        "db_id": placement.id,        # Placement ID for operations
                        "placement_id": placement.id, # Explicit placement ID
                        "library_item_id": library_item.id,
                        "type": library_item.item_type or 'advertisement',
                        "slug": snapshot.get('slug', library_item.slug) or '',
                        "duration": snapshot.get('duration', library_item.duration) or '00:00:00',
                        "script": snapshot.get('script_content', library_item.script_content) or '',
                        "order": order_value,
                        "order_in_rundown": order_value,
                        "index": order_value,
                        "status": 'library',  # Special status for library items
                        "title": snapshot.get('title', library_item.title) or 'Untitled',
                        "subtitle": '',
                        "description": '',
                        "filename": f"{order_value:03d}-{library_item.slug}.md",
                        "asset_id": library_item.asset_id,
                        "airdate": placement.airdate.isoformat() if placement.airdate else '',
                        "guests": '',
                        "resources": '',
                        "tags": '',
                        "priority": snapshot.get('priority', library_item.priority) or '',
                        "server_message": '',
                        "customer_name": snapshot.get('customer_name', library_item.customer_name) or '',
                        "placement_notes": placement.placement_notes or '',
                        "created_at": placement.created_at.isoformat() if placement.created_at else None,
                        "updated_at": placement.updated_at.isoformat() if placement.updated_at else None,
                        "source": "library",  # Distinguish from regular items
                        "is_library_item": True  # Flag for frontend handling
                    }
                    rundown_items.append(placement_dict)
            except ImportError:
                # Content library tables don't exist yet - skip
                pass
            except Exception as e:
                # Log but don't fail - content library is optional enhancement
                logger.warning(f"Could not load content placements: {e}")

        # Sort by order field
        rundown_items.sort(key=lambda x: x.get('order', 999))

        logger.info(f"Retrieved {len(rundown_items)} rundown items from database for episode {episode_number}")
        return {"items": rundown_items}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode number format")
    except Exception as e:
        logger.error(f"Error retrieving rundown from database for episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving rundown from database")


@router.post("/{episode_number}/rundown/normalize")
async def normalize_rundown_order(
    episode_number: str,
    current_user: dict = Depends(get_current_user_or_key)
):
    """
    Normalize rundown item order and index numbers.

    Rules:
    1. Index numbers from filenames take precedence
    2. Round non-multiple-of-10 indexes up to next multiple of 10
    3. Handle conflicts by cascading bumps
    4. Sync order fields in frontmatter to match index numbers
    5. Rename files to match new index numbers
    """
    try:
        logger.info(f"Starting rundown normalization for episode {episode_number}")

        # Get episode directory
        episode_dir = Path(f"/home/episodes/{episode_number}")
        rundown_dir = episode_dir / "rundown"

        if not rundown_dir.exists():
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} rundown directory not found")

        # Execute normalization
        result = await normalize_rundown_items(rundown_dir, episode_number)

        logger.info(f"Rundown normalization completed for episode {episode_number}")
        return result

    except Exception as e:
        logger.error(f"Failed to normalize rundown for episode {episode_number}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to normalize rundown: {str(e)}")


@router.post("/{episode_number}/rundown/item")
async def create_rundown_item(
    episode_number: str,
    item_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Create a new rundown item - DATABASE FIRST approach"""
    try:
        from models_v2 import Episode, Rundown, RundownItem
        from services.asset_id import AssetIDService

        # Get episode from database
        episode_num_int = int(episode_number)
        episode = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found in database")

        # Extract item data first
        item_type = item_data.get('type', 'segment')
        title = item_data.get('title', 'Untitled Item')

        # Generate AssetID and timestamp with proper backend registration
        user_id = current_user.get("username", current_user.get("client_name", "api_user"))
        creation_timestamp = datetime.now()

        # Use request_asset_id() instead of generate() to register in AssetID tracking system
        asset_id = AssetIDService.request_asset_id(
            db=db,
            entity_type="segment",
            reason="rundown_item_creation",
            requested_by=user_id,
            context={
                "episode_number": episode_number,
                "item_type": item_type,
                "title": title,
                "creation_method": "create_rundown_item_endpoint"
            }
        )
        slug = item_data.get('slug', '')
        item_index = item_data.get('index', 10)

        # Debug logging
        logger.info(f"Creating rundown item - received data: {item_data}")
        logger.info(f"Extracted index: {item_index} (type: {type(item_index)})")
        logger.info(f"Raw index from request: {item_data.get('index')} (type: {type(item_data.get('index'))})")

        # Don't auto-generate slug - let user fill it in
        # Frontend will highlight the slug field yellow for user attention
        if not slug:
            slug = ''  # Keep empty, don't generate from title

        # Get or create rundown for this episode
        rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
        if not rundown:
            rundown = Rundown(
                asset_id=f"RUN{asset_id[3:]}",
                episode_id=episode.id,
                name=f"Episode {episode_number} Rundown",
                created_at=creation_timestamp
            )
            db.add(rundown)
            db.flush()  # Get rundown.id

        # CREATE DATABASE RECORD FIRST (source of truth)
        db_item = RundownItem(
            asset_id=asset_id,
            rundown_id=rundown.id,
            item_type=item_type,
            title=title,
            slug=slug,
            order_in_rundown=item_index,
            duration=item_data.get('duration'),
            subtitle=item_data.get('subtitle'),
            description=item_data.get('description'),
            script_content=item_data.get('script_content'),
            guests=item_data.get('guests'),
            resources=item_data.get('resources'),
            block_letter=item_data.get('block_letter') or None,
            created_at=creation_timestamp,
            updated_at=creation_timestamp
        )
        db.add(db_item)
        db.commit()
        logger.info(f"Created database record for rundown item: {asset_id}")

        return {
            "success": True,
            "asset_id": asset_id,
            "created_at": creation_timestamp.isoformat(),
            "message": f"Created rundown item: {title} (AssetID: {asset_id})"
        }

    except Exception as e:
        logger.error(f"Failed to create rundown item: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create rundown item: {str(e)}")


@router.patch("/{episode_number}/item/{item_id}")
async def update_rundown_item(
    episode_number: str,
    item_id: str,
    item_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Update a rundown item's fields (for test segment generation, etc.)"""
    try:
        from models_v2 import RundownItem

        # Find the item by asset_id
        item = db.query(RundownItem).filter(RundownItem.asset_id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"Rundown item {item_id} not found")

        # Update fields that are provided
        if 'script_content' in item_data:
            new_script = item_data['script_content']
            existing_script = item.script_content or ''

            # Server-side Autoscrub: normalize the focused item as it lands
            # (strip span/div cruft, clean whitespace, flag invalid cues, etc).
            # This is the "scrub on save" slice — safe because the edit is done.
            # See docs/AUTOSCRUB_SERVER_REFACTOR_PLAN.md.
            try:
                from services.script_scrub_service import scrub_script_content, load_scrub_settings
                _scrub = scrub_script_content(new_script or '', load_scrub_settings())
                if _scrub.changed:
                    new_script = _scrub.content
                    logger.info(f"Autoscrub normalized {item_id} on save: {', '.join(_scrub.notes)}")
            except Exception as _e:
                logger.warning(f"Autoscrub skipped for {item_id}: {_e}")

            # Calculate content lengths (strip HTML tags)
            import re
            new_content_length = len(re.sub(r'<[^>]+>', '', new_script or '').strip())
            existing_content_length = len(re.sub(r'<[^>]+>', '', existing_script).strip())

            # PROTECTION: Prevent destructive saves
            if existing_content_length > 50 and new_content_length < 30:
                logger.error(f"BLOCKED DESTRUCTIVE SAVE for {item_id}!")
                logger.error(f"   Existing: {existing_content_length} chars, New: {new_content_length} chars")
                raise HTTPException(
                    status_code=400,
                    detail=f"Blocked destructive save: would delete {existing_content_length} characters"
                )

            item.script_content = new_script
            logger.info(f"Updated script_content: {existing_content_length} -> {new_content_length} chars")

            # Create version snapshot
            try:
                create_content_version(db, item, change_type="api_update")
            except Exception as e:
                logger.error(f"Failed to create content version: {e}")
        if 'title' in item_data:
            item.title = item_data['title']
        if 'slug' in item_data:
            item.slug = item_data['slug']
        if 'duration' in item_data:
            item.duration = item_data['duration']
        if 'status' in item_data:
            item.status = item_data['status']
        if 'tone' in item_data:
            item.tone = item_data['tone']
        if 'tone_rationale' in item_data:
            item.tone_rationale = item_data['tone_rationale']
        if 'tone_confidence' in item_data:
            item.tone_confidence = item_data['tone_confidence']
        if 'llm_generated_fields' in item_data:
            item.llm_generated_fields = item_data['llm_generated_fields']
        if 'auto_description_enabled' in item_data:
            item.auto_description_enabled = item_data['auto_description_enabled']

        item.updated_at = datetime.now()
        db.commit()

        logger.info(f"Updated rundown item: {item_id}")
        return {
            "success": True,
            "message": f"Updated item {item_id}",
            "asset_id": item_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update rundown item: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update rundown item: {str(e)}")


@router.put("/{episode_number}/items/{item_id}")
async def save_rundown_item_by_id(
    episode_number: str,
    item_id: str,
    payload: Dict[str, Any],
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Save rundown item using asset_id — database-first lookup.

    LEGACY: This endpoint is rarely called directly. Prefer PUT /{episode_number}/save-rundown.
    """
    from models_v2 import RundownItem

    try:
        # Find item by asset_id in database (no filesystem scan needed)
        item = db.query(RundownItem).filter(RundownItem.asset_id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"Rundown item {item_id} not found in database")

        # Generate a compatible filename from DB fields for the filesystem save path
        item_filename = f"{(item.order_in_rundown or 0):03d}-{item.slug or 'untitled'}.md"

        # Delegate to save_rundown_item which handles both DB and filesystem
        return await save_rundown_item(
            episode_number=episode_number,
            item_filename=item_filename,
            payload=payload,
            current_user=current_user,
            db=db
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving rundown item by ID: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{episode_number}/rundown/{item_filename}")
async def save_rundown_item(
    episode_number: str,
    item_filename: str,
    payload: dict,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Save rundown item to file and update database"""
    try:
        episode_path = EPISODES_ROOT / episode_number
        rundown_dir = episode_path / "rundown"
        item_path = rundown_dir / item_filename

        # Ensure rundown directory exists
        if not rundown_dir.exists():
            rundown_dir.mkdir(parents=True, exist_ok=True)

        # Extract payload data - support multiple content formats
        content = payload.get('content', '')
        script = payload.get('script', '')
        rawMarkdown = payload.get('rawMarkdown', '')
        metadata = payload.get('metadata', {})

        # Build the complete markdown file with frontmatter
        if rawMarkdown:
            # If raw markdown is provided, use it directly
            final_content = rawMarkdown
        elif script and metadata:
            # Build from script and metadata
            import yaml
            frontmatter_yaml = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
            final_content = f"---\n{frontmatter_yaml}---\n\n{script}"
        else:
            # Fallback to provided content
            final_content = content or script or ''
        # Write final content to file
        with open(item_path, 'w', encoding='utf-8') as f:
            f.write(final_content)

        # Enhanced dual-destination saving: Update database with complete field mapping
        try:
            # Use provided metadata or parse from saved file
            db_metadata = metadata if metadata else {}

            if not db_metadata:
                # Parse frontmatter from saved file as fallback
                from utils.frontmatter_parser import parse_markdown_file
                parsed_metadata, body = parse_markdown_file(str(item_path))
                db_metadata = parsed_metadata or {}

            if db_metadata:
                try:
                    from models_v2 import RundownItem
                    from datetime import datetime

                    asset_id = db_metadata.get('AssetID') or db_metadata.get('asset_id')
                    if asset_id:
                        # Find existing rundown item or create new one
                        rundown_item = db.query(RundownItem).filter(RundownItem.asset_id == str(asset_id)).first()

                        if not rundown_item:
                            # Create new rundown item
                            rundown_item = RundownItem(
                                asset_id=str(asset_id),
                                rundown_id=rundown.id,
                                item_type=db_metadata.get('type', 'segment'),
                                title=db_metadata.get('title', 'Untitled'),
                                slug=db_metadata.get('slug', ''),
                                order_in_rundown=int(db_metadata.get('order', 0)) if db_metadata.get('order') else 0,
                                is_test_data=episode_number.startswith('900')  # Mark test episodes
                            )
                            db.add(rundown_item)
                            logger.info(f"Created new database record for rundown item {asset_id}")

                        # Update all fields with comprehensive mapping
                        rundown_item.title = db_metadata.get('title', rundown_item.title or 'Untitled')
                        rundown_item.item_type = db_metadata.get('type', rundown_item.item_type or 'segment')
                        rundown_item.slug = db_metadata.get('slug', rundown_item.slug or '')
                        rundown_item.subtitle = db_metadata.get('subtitle', rundown_item.subtitle)
                        rundown_item.description = db_metadata.get('description', rundown_item.description)
                        rundown_item.duration = db_metadata.get('duration', rundown_item.duration)  # Keep as string HH:MM:SS
                        rundown_item.status = db_metadata.get('status', rundown_item.status or 'draft')
                        rundown_item.priority = db_metadata.get('priority', rundown_item.priority)
                        rundown_item.guests = db_metadata.get('guests', rundown_item.guests)
                        rundown_item.resources = db_metadata.get('resources', rundown_item.resources)
                        rundown_item.tags = db_metadata.get('tags', rundown_item.tags)
                        rundown_item.server_message = db_metadata.get('server_message', rundown_item.server_message)
                        rundown_item.order_in_rundown = int(db_metadata.get('order', rundown_item.order_in_rundown or 0)) if db_metadata.get('order') else rundown_item.order_in_rundown

                        # Tone + LLM bookkeeping
                        if 'tone' in db_metadata:
                            rundown_item.tone = db_metadata['tone']
                        if 'tone_rationale' in db_metadata:
                            rundown_item.tone_rationale = db_metadata['tone_rationale']
                        if 'tone_confidence' in db_metadata:
                            rundown_item.tone_confidence = db_metadata['tone_confidence']
                        if 'llm_generated_fields' in db_metadata:
                            rundown_item.llm_generated_fields = db_metadata['llm_generated_fields']
                        if 'auto_description_enabled' in db_metadata:
                            rundown_item.auto_description_enabled = db_metadata['auto_description_enabled']
                        if 'block_letter' in db_metadata:
                            rundown_item.block_letter = db_metadata['block_letter'] or None

                        # Handle airdate conversion
                        if 'airdate' in db_metadata and db_metadata['airdate']:
                            try:
                                if isinstance(db_metadata['airdate'], str):
                                    # Parse date string to datetime
                                    airdate = datetime.fromisoformat(db_metadata['airdate'].replace('T', ' ').replace('Z', ''))
                                    rundown_item.airdate = airdate
                                elif isinstance(db_metadata['airdate'], datetime):
                                    rundown_item.airdate = db_metadata['airdate']
                            except ValueError as date_error:
                                logger.warning(f"Could not parse airdate '{db_metadata['airdate']}': {date_error}")

                        rundown_item.updated_at = datetime.utcnow()

                        db.commit()
                        logger.info(f"Successfully updated database record for rundown item {asset_id} with all metadata fields")

                except Exception as db_error:
                    logger.error(f"Comprehensive database update failed for {item_filename}: {db_error}")
                    db.rollback()
                    # Continue with file save even if DB update fails

        except Exception as parse_error:
            logger.warning(f"Could not process metadata for database update: {parse_error}")

        return {
            "success": True,
            "message": f"Saved {item_filename} to rundown and updated database",
            "path": str(item_path)
        }

    except Exception as e:
        logging.error(f"Save failed for {episode_number}/{item_filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Save failed: {str(e)}"
        )


@router.put("/{episode_number}/save-rundown")
async def save_rundown_items(
    episode_number: str,
    rundown_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Database-first rundown save with order synchronization

    Supports two modes:
    1. Full rundown save: { "items": [...] }
    2. Single item save: { "item": {...}, "asset_id": "..." }
    """
    from models_v2 import Episode, Rundown, RundownItem

    try:
        # Convert episode number to int
        episode_num_int = int(episode_number)

        # Get episode from database
        episode = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        # Get or create the main rundown for this episode
        rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
        if not rundown:
            from services.asset_id import AssetIDService
            rundown_asset_id = AssetIDService.request_asset_id(
                db=db,
                entity_type="rundown",
                reason="episode_rundown_creation",
                requested_by=str(current_user.get('id', 'system')),
                linked_to=[{"asset_id": episode.asset_id, "link_type": "belongs_to"}],
                context={"episode_number": episode_number}
            )
            rundown = Rundown(
                asset_id=rundown_asset_id,
                episode_id=episode.id,
                name=f"Episode {episode_number} Main Rundown",
                status="draft"
            )
            db.add(rundown)
            db.flush()  # Get the rundown.id

        # Detect mode: single item or full rundown
        if 'item' in rundown_data and 'asset_id' in rundown_data:
            # SINGLE ITEM MODE
            logger.info(f"Single item save mode for asset_id: {rundown_data['asset_id']}")
            items = [rundown_data['item']]
        else:
            # FULL RUNDOWN MODE
            items = rundown_data.get('items', [])
        saved_count = 0

        for i, item_data in enumerate(items):
            logger.info(f"Processing item {i}: {type(item_data)} - {item_data}")

            # Skip if item_data is not a dictionary
            if not isinstance(item_data, dict):
                logger.warning(f"Skipping invalid item_data: {item_data}")
                continue

            # CRITICAL: Sync frontend index to database order field
            frontend_index = item_data.get('index', 0)
            item_data['order'] = frontend_index  # This is the key synchronization!

            asset_id = item_data.get('asset_id') or item_data.get('AssetID') or item_data.get('id')

            if asset_id:
                # Try to find existing item
                rundown_item = db.query(RundownItem).filter(RundownItem.asset_id == str(asset_id)).first()

                if rundown_item:
                    # Update existing item
                    # Use proper null checking - 0 is a valid order value!
                    order_value = item_data.get('order') if item_data.get('order') is not None else item_data.get('index')
                    rundown_item.order_in_rundown = order_value if order_value is not None else 0
                    rundown_item.title = item_data.get('title', rundown_item.title)
                    rundown_item.item_type = item_data.get('type', rundown_item.item_type)
                    rundown_item.duration = item_data.get('duration', rundown_item.duration)
                    rundown_item.status = item_data.get('status', rundown_item.status)
                    if 'block_letter' in item_data:
                        rundown_item.block_letter = item_data.get('block_letter') or None

                    # CRITICAL: Only update script_content if explicitly provided
                    # Frontend sends script only for currently edited item
                    if 'script' in item_data:
                        new_script = item_data['script']
                        existing_script = rundown_item.script_content or ''

                        # CRITICAL FIX: Strip frontmatter from script_content
                        # script_content should NEVER contain YAML frontmatter - only the body
                        # Frontmatter is stored in separate database fields (title, type, status, etc.)
                        import re

                        def _is_frontmatter_delimiter(line):
                            t = line.strip()
                            return t == '---' or t == '- - -'

                        def _starts_with_frontmatter(text):
                            t = text.strip()
                            return t.startswith('---') or t.startswith('- - -')

                        if new_script and _starts_with_frontmatter(new_script):
                            logger.warning(f"STRIPPING FRONTMATTER from script_content for {asset_id}")
                            logger.warning(f"   Original content preview: {new_script[:200]}...")

                            # Find the closing delimiter and extract only the body
                            lines = new_script.split('\n')
                            dash_count = 0
                            body_start_index = 0

                            for i, line in enumerate(lines):
                                if _is_frontmatter_delimiter(line):
                                    dash_count += 1
                                    if dash_count == 2:
                                        body_start_index = i + 1
                                        break

                            if dash_count >= 2:
                                # Take content after the closing frontmatter
                                body_content = '\n'.join(lines[body_start_index:]).strip()

                                # ADDITIONAL CHECK: If body still contains another frontmatter block,
                                # this is duplicated content - strip it again
                                while _starts_with_frontmatter(body_content):
                                    logger.warning(f"DOUBLE FRONTMATTER DETECTED! Stripping again...")
                                    body_lines = body_content.split('\n')
                                    inner_dash_count = 0
                                    inner_body_start = 0

                                    for j, bline in enumerate(body_lines):
                                        if _is_frontmatter_delimiter(bline):
                                            inner_dash_count += 1
                                            if inner_dash_count == 2:
                                                inner_body_start = j + 1
                                                break

                                    if inner_dash_count >= 2:
                                        body_content = '\n'.join(body_lines[inner_body_start:]).strip()
                                    else:
                                        break  # No more complete frontmatter blocks

                                new_script = body_content
                                logger.warning(f"Stripped frontmatter, body length: {len(new_script)} chars")
                            else:
                                logger.warning(f"Found opening delimiter but no closing one, keeping original")

                        logger.info(f"Saving script content for {asset_id}: {new_script[:100] if new_script else 'EMPTY'}")
                        rundown_item.script_content = new_script

                        # Create version snapshot after successful save (only for manual saves)
                        try:
                            username = current_user.get('username') if isinstance(current_user, dict) else None
                            # Use save_type from request body, default to 'manual_save'
                            save_type = rundown_data.get('save_type', 'manual_save')
                            create_content_version(db, rundown_item, change_type=save_type, username=username)
                        except Exception as e:
                            logger.error(f"Failed to create content version for {asset_id}: {e}")

                        # Write segment snapshot to filesystem
                        try:
                            from services.autosave_history import write_segment_snapshot
                            write_segment_snapshot(
                                episode_number=episode_number,
                                item_id=rundown_item.id,
                                asset_id=rundown_item.asset_id,
                                title=rundown_item.title,
                                item_type=rundown_item.item_type,
                                script_content=new_script,
                                order_in_rundown=rundown_item.order_in_rundown or 0,
                            )
                        except Exception as e:
                            logger.warning(f"Autosave history segment snapshot failed: {e}")
                    else:
                        logger.info(f"No 'script' key in item_data for {asset_id}, not updating script_content")

                    rundown_item.description = item_data.get('description', rundown_item.description)  # Metadata description
                    rundown_item.subtitle = item_data.get('subtitle', rundown_item.subtitle)
                    rundown_item.guests = item_data.get('guests', rundown_item.guests)
                    rundown_item.tags = item_data.get('tags', rundown_item.tags)
                    rundown_item.priority = item_data.get('priority', rundown_item.priority)
                    rundown_item.slug = item_data.get('slug', rundown_item.slug)  # FIXED: Missing slug field

                    # Update timestamps
                    from datetime import datetime
                    rundown_item.updated_at = datetime.now()
                    saved_count += 1
                    logger.info(f"Updated existing rundown item with asset_id: {asset_id}")
                else:
                    # Create new item with existing asset_id
                    from datetime import datetime
                    import re

                    # Generate slug from title if not provided
                    title = item_data.get('title', 'Untitled')
                    slug = item_data.get('slug') or re.sub(r'[^a-zA-Z0-9\-]', '-', title.lower()).strip('-')

                    new_item = RundownItem(
                        asset_id=str(asset_id),
                        rundown_id=rundown.id,
                        order_in_rundown=item_data.get('order') if item_data.get('order') is not None else (item_data.get('index') if item_data.get('index') is not None else 0),
                        title=title,
                        slug=slug,
                        item_type=item_data.get('type', 'segment'),
                        duration=item_data.get('duration'),
                        status=item_data.get('status', 'draft'),
                        script_content=item_data.get('script', ''),  # Script content
                        description=item_data.get('description', ''),
                        subtitle=item_data.get('subtitle'),
                        guests=item_data.get('guests'),
                        tags=item_data.get('tags'),
                        priority=item_data.get('priority', 'normal'),
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    db.add(new_item)
                    saved_count += 1
                    logger.info(f"Created new rundown item with asset_id: {asset_id}")
            else:
                # Create completely new item without asset_id
                from services.asset_id import AssetIDService
                from datetime import datetime
                import re

                new_asset_id = AssetIDService.request_asset_id(
                    db=db,
                    entity_type=item_data.get('type', 'segment'),
                    reason="rundown_item_creation_during_save",
                    requested_by=str(current_user.get('id', 'system')),
                    context={"episode_number": episode_number}
                )

                # Generate slug from title if not provided
                title = item_data.get('title', 'Untitled')
                slug = item_data.get('slug') or re.sub(r'[^a-zA-Z0-9\-]', '-', title.lower()).strip('-')

                new_item = RundownItem(
                    asset_id=str(new_asset_id),
                    rundown_id=rundown.id,
                    order_in_rundown=item_data.get('order') or item_data.get('index', 0),
                    title=title,
                    slug=slug,
                    item_type=item_data.get('type', 'segment'),
                    duration=item_data.get('duration'),
                    status=item_data.get('status', 'draft'),
                    script_content=item_data.get('script', ''),  # Script content
                    description=item_data.get('description', ''),
                    subtitle=item_data.get('subtitle'),
                    guests=item_data.get('guests'),
                    tags=item_data.get('tags'),
                    priority=item_data.get('priority', 'normal'),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(new_item)
                saved_count += 1
                logger.info(f"Created completely new rundown item with new asset_id: {new_asset_id}")

        # Calculate and store total duration on the episode
        # Includes both item-level durations AND embedded cue durations (RIF, SOT, VOX, etc.)
        import re as re_mod
        all_items = db.query(RundownItem).filter(RundownItem.rundown_id == rundown.id).all()
        total_duration_seconds = 0

        def _parse_dur(dur_str):
            """Parse HH:MM:SS:FF, HH:MM:SS, or MM:SS to seconds"""
            try:
                parts = dur_str.split(':')
                if len(parts) == 4:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                elif len(parts) == 3:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                elif len(parts) == 2:
                    return int(parts[0]) * 60 + int(parts[1])
            except (ValueError, IndexError):
                pass
            return 0

        for ri in all_items:
            # 1. Item-level duration
            if ri.duration:
                total_duration_seconds += _parse_dur(ri.duration)
            # 2. Embedded cue durations from script_content
            if ri.script_content:
                cue_blocks = re_mod.findall(
                    r'<!-- Begin Cue -->(.*?)<!-- End Cue -->',
                    ri.script_content, re_mod.DOTALL
                )
                for cue_block in cue_blocks:
                    dur_match = re_mod.search(r'\[Duration:\s*([^\]]+)\]', cue_block, re_mod.IGNORECASE)
                    if dur_match:
                        total_duration_seconds += _parse_dur(dur_match.group(1).strip())

        episode.actual_duration = total_duration_seconds
        h = total_duration_seconds // 3600
        m = (total_duration_seconds % 3600) // 60
        s = total_duration_seconds % 60
        episode.duration_formatted = f"{h:02d}:{m:02d}:{s:02d}"

        db.commit()

        # Write episode snapshot to filesystem (throttled by interval setting)
        try:
            from services.autosave_history import write_episode_snapshot
            write_episode_snapshot(
                episode_number=episode_number,
                episode_title=episode.title or "",
                rundown_items=all_items,
            )
        except Exception as e:
            logger.warning(f"Autosave history episode snapshot failed: {e}")

        logger.info(f"Saved {saved_count} rundown items for episode {episode_number} with order synchronization")
        logger.info(f"Updated episode total duration: {episode.duration_formatted} ({total_duration_seconds}s)")
        return {
            "status": "success",
            "message": f"Saved {saved_count} rundown items with order synchronization",
            "items_saved": saved_count,
            "total_duration": episode.duration_formatted,
            "total_duration_seconds": total_duration_seconds,
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode number format")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving rundown items: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to save rundown items: {str(e)}")


@router.delete("/{episode_number}/rundown/clear")
async def clear_entire_rundown(
    episode_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Clear entire rundown - delete all items and files for an episode"""
    import shutil

    try:
        # Check if episode exists
        from models_v2 import Episode, Rundown, RundownItem

        episode = db.query(Episode).filter(Episode.episode_number == episode_number).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        episode_dir = EPISODES_ROOT / episode_number
        rundown_dir = episode_dir / "rundown"

        deleted_files = 0
        deleted_items = 0
        deleted_rundowns = 0

        # Step 1: Delete all rundown files from filesystem
        if rundown_dir.exists():
            md_files = list(rundown_dir.glob("*.md"))
            for md_file in md_files:
                try:
                    md_file.unlink()
                    deleted_files += 1
                    logger.info(f"Deleted rundown file: {md_file.name}")
                except Exception as e:
                    logger.warning(f"Could not delete file {md_file}: {e}")

            # Clean up autosave directory if it exists
            autosave_dir = rundown_dir / "autosave"
            if autosave_dir.exists():
                try:
                    shutil.rmtree(autosave_dir)
                    logger.info("Deleted rundown autosave directory")
                except Exception as e:
                    logger.warning(f"Could not delete autosave directory: {e}")

        # Step 2: Delete all database records
        try:
            # Get all rundowns for this episode
            rundowns = db.query(Rundown).filter(Rundown.episode_id == episode.id).all()

            for rundown in rundowns:
                # Delete all rundown items for this rundown
                rundown_items = db.query(RundownItem).filter(RundownItem.rundown_id == rundown.id).all()
                for item in rundown_items:
                    db.delete(item)
                    deleted_items += 1

                # Delete the rundown itself
                db.delete(rundown)
                deleted_rundowns += 1

            db.commit()
            logger.info(f"Deleted {deleted_items} rundown items and {deleted_rundowns} rundowns from database")

        except Exception as e:
            logger.error(f"Database deletion failed: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to clear database records: {str(e)}")

        return {
            "status": "success",
            "message": f"Cleared entire rundown for episode {episode_number}",
            "deleted": {
                "files": deleted_files,
                "database_items": deleted_items,
                "database_rundowns": deleted_rundowns
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing entire rundown: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear rundown: {str(e)}")


@router.delete("/{episode_number}/rundown/{item_filename}")
async def delete_rundown_item(
    episode_number: str,
    item_filename: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Delete rundown item from both file system and database"""
    try:
        episode_path = EPISODES_ROOT / episode_number
        rundown_dir = episode_path / "rundown"
        item_path = rundown_dir / item_filename

        # Delete file if it exists
        if item_path.exists():
            item_path.unlink()
            logger.info(f"Deleted file: {item_path}")

        # Parse AssetID from filename or lookup for database deletion
        asset_id = None
        try:
            # Try to extract AssetID from filename (format: "order slug~assetid.md")
            if '~' in item_filename:
                asset_id_part = item_filename.split('~')[1].replace('.md', '')
                asset_id = asset_id_part
                logger.info(f"Extracted AssetID from filename: {asset_id}")
            else:
                # If no AssetID in filename, try to find by filename pattern
                logger.info(f"No AssetID in filename, attempting database lookup for: {item_filename}")

                # Remove .md extension for search
                base_filename = item_filename.replace('.md', '')

                # Import models for database lookup
                from models_v2 import RundownItem, Segment

                # Try to find by filename pattern (remove order prefix and search by slug)
                # Convert "030-show-cold-open" to "show-cold-open"
                if '-' in base_filename and base_filename[0:3].isdigit():
                    slug_part = '-'.join(base_filename.split('-')[1:])  # Remove order prefix
                    db_item = db.query(RundownItem).filter(RundownItem.slug == slug_part).first()
                    if db_item:
                        asset_id = db_item.asset_id
                        logger.info(f"Found AssetID by slug lookup: {asset_id}")

                # Also try exact filename match
                if not asset_id:
                    db_item = db.query(RundownItem).filter(RundownItem.filename == item_filename).first()
                    if db_item:
                        asset_id = db_item.asset_id
                        logger.info(f"Found AssetID by filename lookup: {asset_id}")

                if not asset_id:
                    logger.warning(f"Could not find AssetID for filename: {item_filename}")
                    raise ValueError("No AssetID found in filename or database lookup")

            # Delete from database using the found AssetID
            if asset_id:
                from models_v2 import RundownItem, Segment, SegmentLock

                db_deleted = False

                # First, delete any segment locks referencing this rundown item
                locks_deleted = db.query(SegmentLock).filter(
                    SegmentLock.rundown_item_asset_id == str(asset_id)
                ).delete(synchronize_session=False)
                if locks_deleted:
                    logger.info(f"Deleted {locks_deleted} segment lock(s) for AssetID: {asset_id}")

                # Try to find and delete by asset_id first
                db_item = db.query(RundownItem).filter(RundownItem.asset_id == str(asset_id)).first()
                if db_item:
                    db.delete(db_item)
                    db_deleted = True
                    logger.info(f"Deleted database rundown item for AssetID: {asset_id}")

                # Also try to find by id if asset_id is numeric (might be database id)
                if not db_deleted and asset_id.isdigit():
                    db_item = db.query(RundownItem).filter(RundownItem.id == int(asset_id)).first()
                    if db_item:
                        db.delete(db_item)
                        db_deleted = True
                        logger.info(f"Deleted database rundown item for ID: {asset_id}")

                # Also try to delete segment record
                segment = db.query(Segment).filter(Segment.asset_id == str(asset_id)).first()
                if segment:
                    db.delete(segment)
                    logger.info(f"Deleted database segment for AssetID: {asset_id}")

                db.commit()

                if db_deleted:
                    logger.info(f"Successfully deleted database entries for AssetID/ID: {asset_id}")
                else:
                    logger.warning(f"No database record found for AssetID/ID: {asset_id}")

        except Exception as e:
            logger.error(f"Database deletion failed: {str(e)}")
            db.rollback()
            # In database-first architecture, failing to delete from DB is a real error
            raise HTTPException(status_code=500, detail=f"Failed to delete from database: {str(e)}")

        return {"status": "success", "message": "Rundown item deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting rundown item: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete rundown item: {str(e)}")


@router.delete("/{episode_number}/rundown/by-asset-id/{asset_id}")
async def delete_rundown_item_by_asset_id(
    episode_number: str,
    asset_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Delete rundown item by asset_id - DATABASE FIRST approach.

    This is the preferred delete method. It:
    1. Looks up the item by asset_id (guaranteed unique)
    2. Validates the item belongs to the specified episode
    3. Deletes from database FIRST (source of truth)
    4. Then cleans up filesystem file (if exists)

    Args:
        episode_number: Episode number (e.g., "0101")
        asset_id: The unique asset_id of the rundown item

    Returns:
        Success status with deleted item details
    """
    from models_v2 import RundownItem, Segment, Episode, Rundown, SegmentLock

    try:
        logger.info(f"Delete by asset_id: {asset_id} for episode {episode_number}")

        # Step 1: Find the rundown item by asset_id
        db_item = db.query(RundownItem).filter(RundownItem.asset_id == str(asset_id)).first()

        if not db_item:
            logger.warning(f"Rundown item not found for asset_id: {asset_id}")
            raise HTTPException(status_code=404, detail=f"Rundown item with asset_id '{asset_id}' not found")

        # Step 2: Validate the item belongs to the correct episode
        rundown = db.query(Rundown).filter(Rundown.id == db_item.rundown_id).first()
        if rundown:
            episode = db.query(Episode).filter(Episode.id == rundown.episode_id).first()
            if episode:
                # Normalize episode numbers for comparison (handle "0101" vs 101)
                db_episode_num = str(episode.episode_number).zfill(4)
                request_episode_num = str(episode_number).zfill(4)
                if db_episode_num != request_episode_num:
                    logger.warning(f"Asset {asset_id} belongs to episode {db_episode_num}, not {request_episode_num}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Item belongs to episode {db_episode_num}, not {episode_number}"
                    )

        # Step 3: Capture item details before deletion (for file cleanup and response)
        item_slug = db_item.slug
        item_title = db_item.title
        item_order = db_item.order_in_rundown
        item_type = db_item.item_type

        # Step 4: DELETE FROM DATABASE FIRST (source of truth)
        # First delete any segment locks referencing this rundown item
        locks_deleted = db.query(SegmentLock).filter(
            SegmentLock.rundown_item_asset_id == str(asset_id)
        ).delete(synchronize_session=False)
        if locks_deleted:
            logger.info(f"Deleted {locks_deleted} segment lock(s) for asset_id: {asset_id}")

        db.delete(db_item)
        logger.info(f"Deleted rundown item from database: {asset_id} ({item_title})")

        # Also delete associated segment if exists
        segment = db.query(Segment).filter(Segment.asset_id == str(asset_id)).first()
        if segment:
            db.delete(segment)
            logger.info(f"Deleted associated segment for asset_id: {asset_id}")

        # Commit database changes
        db.commit()
        logger.info(f"Database deletion committed for asset_id: {asset_id}")

        # Step 5: Clean up filesystem file (secondary, non-critical)
        files_deleted = []
        try:
            episode_path = EPISODES_ROOT / episode_number
            rundown_dir = episode_path / "rundown"

            if rundown_dir.exists():
                # Try multiple filename patterns that might exist
                possible_filenames = [
                    f"{item_order:03d}-{item_slug}.md",           # Format: 010-slug.md
                    f"{item_order} {item_slug}~{asset_id}.md",    # Format: 10 slug~assetid.md
                    f"{item_order:03d} {item_slug}~{asset_id}.md", # Format: 010 slug~assetid.md
                ]

                for filename in possible_filenames:
                    file_path = rundown_dir / filename
                    if file_path.exists():
                        file_path.unlink()
                        files_deleted.append(filename)
                        logger.info(f"Deleted file: {file_path}")

                # Also search for any file containing the asset_id
                if not files_deleted:
                    for file_path in rundown_dir.glob(f"*{asset_id}*"):
                        if file_path.is_file():
                            file_path.unlink()
                            files_deleted.append(file_path.name)
                            logger.info(f"Deleted file by asset_id pattern: {file_path}")

                    # Search for any file containing the slug
                    for file_path in rundown_dir.glob(f"*{item_slug}*"):
                        if file_path.is_file() and file_path.name not in files_deleted:
                            file_path.unlink()
                            files_deleted.append(file_path.name)
                            logger.info(f"Deleted file by slug pattern: {file_path}")

                if not files_deleted:
                    logger.info(f"No filesystem files found for asset_id {asset_id} (may already be deleted)")

        except Exception as file_error:
            # File deletion is secondary - log but don't fail the request
            logger.warning(f"File cleanup failed (non-critical): {file_error}")

        return {
            "status": "success",
            "message": f"Deleted rundown item: {item_title}",
            "deleted": {
                "asset_id": asset_id,
                "title": item_title,
                "slug": item_slug,
                "type": item_type,
                "order": item_order
            },
            "files_deleted": files_deleted
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting rundown item by asset_id: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete rundown item: {str(e)}")


# ============================================================================
# SINGLE RUNDOWN ITEM ENDPOINT
# ============================================================================

@router.get("/rundown-item-by-id/{item_id}")
async def get_rundown_item_by_id(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Get a single rundown item by its database ID."""
    from models_v2 import RundownItem

    # Find the rundown item
    item = db.query(RundownItem).filter(RundownItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Rundown item {item_id} not found")

    return {
        "id": item.id,
        "asset_id": item.asset_id,
        "title": item.title,
        "slug": item.slug,
        "item_type": item.item_type,
        "duration": item.duration,
        "status": item.status,
        "order": item.order_in_rundown,
        "script_content": item.script_content,
        "description": item.description,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None
    }


@router.get("/rundown-item/{asset_id}")
async def get_rundown_item_by_asset_id(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """
    Get a single rundown item by its asset_id with full content.

    This endpoint is optimized for single-item fetches after SOT processing
    completes, allowing the frontend to update just the affected item
    instead of reloading the entire rundown.

    Returns the item in the same format as the rundown list endpoint
    for direct array merge compatibility.

    Args:
        asset_id: AssetID of the rundown item

    Returns:
        Dict with full item data including script_content
    """
    from models_v2 import RundownItem, Rundown, Episode

    logger.info(f"Single-item fetch requested for asset_id: {asset_id}")

    # Find the rundown item by asset_id
    item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()

    if not item:
        raise HTTPException(status_code=404, detail=f"Rundown item {asset_id} not found")

    # Get the rundown to find episode info
    rundown = db.query(Rundown).filter(Rundown.id == item.rundown_id).first()
    episode_number = None
    if rundown:
        episode = db.query(Episode).filter(Episode.id == rundown.episode_id).first()
        if episode:
            episode_number = episode.episode_number

    # Return item in same format as rundown list endpoint for direct merge
    return {
        "id": item.asset_id,  # Legacy: asset_id as primary identifier for frontend
        "db_id": item.id,     # Database integer ID for API operations
        "asset_id": item.asset_id,
        "type": item.item_type or 'segment',
        "title": item.title or '',
        "slug": item.slug or '',
        "subtitle": item.subtitle,
        "description": item.description,
        "duration": item.duration or '00:00:00',
        "status": item.status or 'draft',
        "priority": item.priority,
        "guests": item.guests,
        "resources": item.resources,
        "tags": item.tags,
        "order": item.order_in_rundown or 0,
        "script_content": item.script_content,
        "airdate": item.airdate.isoformat() if item.airdate else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        "episode_number": episode_number,
        "source": "rundown_item"  # Distinguish from library placements
    }
