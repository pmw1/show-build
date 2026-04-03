"""
Episode CRUD operations router.
Handles episode creation, listing, deletion, duplication, and conflict checking.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional, Dict, Any
from pathlib import Path
import yaml
import logging
from auth.utils import get_current_user_or_key
from database import get_db
from sqlalchemy.orm import Session
from datetime import datetime

from ._shared import (
    EPISODES_ROOT, EpisodeMetadata, check_episode_conflicts,
    create_episode_directory, create_info_file, logger
)

router = APIRouter()


@router.get("/upcoming")
async def get_upcoming_episodes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Get all upcoming episodes that haven't passed 10pm NY time of their airdate."""
    from models_v2 import Episode, Rundown, RundownItem
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    try:
        # Get current time in NY timezone
        ny_tz = ZoneInfo('America/New_York')
        now_ny = datetime.now(ny_tz)

        # Find episodes that either:
        # 1. Have air_date in the future, OR
        # 2. Have air_date today but current NY time < 10pm
        episodes = db.query(Episode).filter(
            Episode.air_date.isnot(None)
        ).order_by(Episode.air_date.asc()).all()

        upcoming_episodes = []
        for episode in episodes:
            if episode.air_date:
                # Convert episode air_date to NY timezone
                episode_date_ny = episode.air_date.astimezone(ny_tz)
                # Create 10pm cutoff for that date
                cutoff_time = episode_date_ny.replace(hour=22, minute=0, second=0, microsecond=0)

                # If current time hasn't passed the 10pm cutoff, this is an upcoming episode
                if now_ny < cutoff_time:
                    upcoming_episodes.append(episode)

        if not upcoming_episodes:
            return {"error": "No upcoming episodes found", "episodes": []}

        # Process each upcoming episode to calculate statistics
        episodes_data = []

        for episode in upcoming_episodes:
            # Format episode number as 4-digit string
            episode_number_str = f"{episode.episode_number:04d}" if episode.episode_number else "0000"

            # Get rundown statistics for this episode
            rundowns = db.query(Rundown).filter(Rundown.episode_id == episode.id).all()

            total_items = 0
            items_by_status = {"draft": 0, "approved": 0, "production": 0, "completed": 0}
            items_by_type = {"segment": 0, "advertisement": 0, "promo": 0, "transition": 0, "other": 0}
            total_duration_seconds = 0

            for rundown in rundowns:
                items = db.query(RundownItem).filter(RundownItem.rundown_id == rundown.id).all()
                total_items += len(items)

                for item in items:
                    # Count by status
                    status = item.status or "draft"
                    if status in items_by_status:
                        items_by_status[status] += 1

                    # Count by type
                    item_type = item.item_type or "segment"
                    if item_type in items_by_type:
                        items_by_type[item_type] += 1
                    else:
                        items_by_type["other"] += 1

                    # Sum duration (convert HH:MM:SS to seconds)
                    if item.duration:
                        try:
                            time_parts = item.duration.split(':')
                            if len(time_parts) == 3:
                                hours, minutes, seconds = map(int, time_parts)
                                total_duration_seconds += hours * 3600 + minutes * 60 + seconds
                        except:
                            pass

            # Convert total duration back to HH:MM:SS
            hours = total_duration_seconds // 3600
            minutes = (total_duration_seconds % 3600) // 60
            seconds = total_duration_seconds % 60
            estimated_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            # Calculate progress percentage
            completed_items = items_by_status["completed"] + items_by_status["approved"]
            progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0

            episode_data = {
                "episode": {
                    "number": episode_number_str,
                    "title": episode.title or "Untitled",
                    "air_date": episode.air_date.isoformat() if episode.air_date else None,
                    "status": episode.status or "draft",
                    "target_duration": episode.duration_formatted or "01:00:00",
                    "guest": {
                        "name": episode.guest_name or "",
                        "bio": episode.guest_bio or "",
                        "website": episode.guest_website or ""
                    },
                    "asset_id": episode.asset_id,
                    "created_at": episode.created_at.isoformat() if episode.created_at else None,
                    "is_dummy": episode.is_dummy or False
                },
                "statistics": {
                    "total_items": total_items,
                    "by_status": items_by_status,
                    "by_type": items_by_type,
                    "duration": {
                        "estimated": estimated_duration,
                        "target": episode.duration_formatted or "01:00:00"
                    },
                    "progress_percentage": round(progress_percentage, 1)
                }
            }

            episodes_data.append(episode_data)

        logger.info(f"Retrieved {len(episodes_data)} upcoming episodes")
        return {"episodes": episodes_data}

    except Exception as e:
        logger.error(f"Error retrieving upcoming episodes: {e}")
        return {"error": str(e)}


@router.get("/")
async def list_episodes(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """List all episodes from database."""
    from models_v2 import Episode

    try:
        # Query all episodes from database, ordered by episode number
        db_episodes = db.query(Episode).order_by(Episode.episode_number.desc()).all()

        episodes = []
        for ep in db_episodes:
            # Format episode number as 4-digit string (e.g., 236 -> "0236")
            episode_number_str = f"{ep.episode_number:04d}" if ep.episode_number else "0000"

            episodes.append({
                "id": episode_number_str,
                "episode_number": episode_number_str,
                "title": ep.title or "Untitled",
                "subtitle": ep.subtitle or "",
                "airdate": ep.air_date.isoformat() if ep.air_date else None,
                "status": ep.status or "draft",
                "duration": ep.duration_formatted or "01:00:00",
                "description": ep.description or "",
                "guest": ep.guest_name or "",
                "guest_bio": ep.guest_bio or "",
                "guest_website": ep.guest_website or "",
                "template_type": ep.template_type or "",
                "template_name": ep.template_name or "",
                "asset_id": ep.asset_id,
                "created_at": ep.created_at.isoformat() if ep.created_at else None,
                "updated_at": ep.updated_at.isoformat() if ep.updated_at else None,
                "is_dummy": ep.is_dummy or False
            })

        logger.info(f"Retrieved {len(episodes)} episodes from database")
        return {"episodes": episodes}

    except Exception as e:
        logger.error(f"Error retrieving episodes from database: {e}")
        # Fallback: return empty list rather than crash
        return {"episodes": []}


@router.post("/{episode_number}/create")
async def create_episode(
    episode_number: str,
    metadata: EpisodeMetadata = Body(...),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new episode with full directory structure and metadata"""

    # Validate episode number format
    if not episode_number.isdigit() or len(episode_number) != 4:
        raise HTTPException(status_code=400, detail="Episode number must be 4 digits")

    # Check for conflicts with detailed reporting
    conflict_info = check_episode_conflicts(episode_number, db)
    if conflict_info["has_conflicts"]:
        conflicts_text = ", ".join(conflict_info["conflicts"])
        raise HTTPException(
            status_code=409,
            detail=f"Episode {episode_number} already exists in: {conflicts_text}"
        )

    try:
        # Ensure episode_number in metadata matches the path parameter
        metadata.episode_number = episode_number

        # Set default slug if not provided
        if not metadata.slug:
            metadata.slug = f"episode-{episode_number}"

        # Generate rundown_id if not provided (episode number + 000)
        if not metadata.rundown_id:
            metadata.rundown_id = int(episode_number + "000")

        # Create directory structure
        episode_dir = create_episode_directory(episode_number)
        logger.info(f"Created directory structure for episode {episode_number}")

        # Create info.md file
        info_path = create_info_file(episode_dir, metadata)
        logger.info(f"Created info.md for episode {episode_number}")

        # Create a default rundown item
        rundown_dir = episode_dir / "rundown"
        default_rundown = rundown_dir / "10 Opening.md"
        default_rundown_content = f"""---
id: '{episode_number}001'
slug: opening
type: segment
order: 10
duration: 00:05:00
status: draft
title: Opening
subtitle: null
description: Show opening and introduction
airdate: {metadata.airdate}
priority: ''
guests: null
resources: ''
tags: null
server_message: ''
---

## Notes
Welcome to episode {episode_number}

## Description
Show opening and introduction

## Script
[Opening script goes here]
"""

        with open(default_rundown, 'w', encoding='utf-8') as f:
            f.write(default_rundown_content)

        # Create database record in episodes table
        from services.asset_id import AssetIDService
        from models_v2 import Episode

        # Generate AssetID for the episode
        episode_asset_id = AssetIDService.request_asset_id(
            db=db,
            entity_type="episode",
            reason="create",
            requested_by=current_user.get("username", current_user.get("client_name", "system")),
            context={
                "source": "episode_creation",
                "episode_number": episode_number,
                "title": metadata.title
            }
        )

        # Create episode record
        episode = Episode(
            asset_id=episode_asset_id,
            season_id=1,  # Default season
            episode_number=int(episode_number),
            title=metadata.title,
            slug=metadata.slug,
            status="draft",
            publish_date=metadata.airdate,
            air_date=metadata.airdate
        )

        db.add(episode)
        db.commit()
        db.refresh(episode)

        logger.info(f"Created database record for episode {episode_number} with AssetID {episode_asset_id}")

        return {
            "success": True,
            "message": f"Episode {episode_number} created successfully",
            "episode_number": episode_number,
            "asset_id": episode_asset_id,
            "database_id": episode.id,
            "path": str(episode_dir),
            "info_file": str(info_path),
            "metadata": metadata.dict(exclude_none=True)
        }

    except Exception as e:
        logger.error(f"Failed to create episode {episode_number}: {e}")
        # Clean up if partial creation occurred
        db.rollback()  # Rollback any database changes
        if episode_dir.exists():
            import shutil
            shutil.rmtree(episode_dir)
        raise HTTPException(status_code=500, detail=f"Failed to create episode: {str(e)}")


@router.delete("/{episode_number}")
async def delete_episode(
    episode_number: str,
    force: bool = False,
    break_locks: bool = False,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Delete an episode and all its content from both filesystem and database.

    If the filesystem directory doesn't exist but database records do (phantom record),
    use force=true to confirm database-only deletion.

    If there are active segment locks, use break_locks=true to force-remove them.
    """
    from models_v2 import Episode, Rundown, RundownItem, SegmentLock

    episode_dir = EPISODES_ROOT / episode_number
    filesystem_exists = episode_dir.exists()

    # Check for database record
    try:
        episode_num_int = int(episode_number)
        episode_record = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
        db_record_exists = episode_record is not None
    except ValueError:
        episode_record = None
        db_record_exists = False

    # Check for segment locks BEFORE attempting any deletion
    if episode_record:
        # Get all rundown item asset_ids for this episode
        rundown_ids = db.query(Rundown.id).filter(Rundown.episode_id == episode_record.id).all()
        rundown_ids = [r[0] for r in rundown_ids]

        if rundown_ids:
            rundown_item_asset_ids = db.query(RundownItem.asset_id).filter(
                RundownItem.rundown_id.in_(rundown_ids)
            ).all()
            rundown_item_asset_ids = [r[0] for r in rundown_item_asset_ids if r[0]]

            if rundown_item_asset_ids:
                # Check for segment locks on these items
                segment_locks = db.query(SegmentLock).filter(
                    SegmentLock.rundown_item_asset_id.in_(rundown_item_asset_ids)
                ).all()

                if segment_locks and not break_locks:
                    # Return information about the locks
                    lock_info = []
                    for lock in segment_locks:
                        lock_info.append({
                            "lock_id": lock.id,
                            "asset_id": lock.asset_id,
                            "rundown_item_asset_id": lock.rundown_item_asset_id,
                            "user_id": lock.user_id,
                            "locked_at": lock.locked_at.isoformat() if lock.locked_at else None,
                            "expires_at": lock.expires_at.isoformat() if lock.expires_at else None
                        })

                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": "segment_locks_exist",
                            "message": f"Episode {episode_number} has {len(segment_locks)} active segment lock(s). Use break_locks=true to force-remove them and delete the episode.",
                            "episode_number": episode_number,
                            "lock_count": len(segment_locks),
                            "locks": lock_info,
                            "action_required": "confirm_break_locks"
                        }
                    )
                elif segment_locks and break_locks:
                    # User confirmed - delete the segment locks
                    for lock in segment_locks:
                        db.delete(lock)
                    logger.info(f"Force-deleted {len(segment_locks)} segment locks for episode {episode_number}")

    # Handle phantom records (database exists but no filesystem)
    if not filesystem_exists:
        if not db_record_exists:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found in filesystem or database")

        # Database record exists but no filesystem - require force confirmation
        if not force:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "phantom_record",
                    "message": f"Episode {episode_number} exists in database but has no filesystem directory. Use force=true to confirm deletion of database records only.",
                    "episode_number": episode_number,
                    "filesystem_exists": False,
                    "database_exists": True,
                    "action_required": "confirm_force_delete"
                }
            )
        # force=true, proceed with database-only deletion
        logger.info(f"Force deleting phantom episode {episode_number} (database only, no filesystem)")

    try:
        import shutil
        from datetime import datetime
        from models_v2 import Segment, Break
        from models_episode import Blueprint

        # First, delete from database to ensure data consistency
        logger.info(f"Starting deletion of episode {episode_number} from database")

        # Initialize counters for response
        rundown_item_count = 0
        segment_count = 0

        # episode_record already fetched above, reuse it
        if not episode_record:
            # Try again in case it wasn't fetched earlier
            try:
                episode_num_int = int(episode_number)
                episode_record = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
            except ValueError:
                logger.error(f"Invalid episode number format: {episode_number}")
                episode_record = None

        if not episode_record:
            logger.warning(f"No episode record found for {episode_number} in episodes table")

        # Delete from blueprints table (scaffolded episodes)
        blueprint_episode = db.query(Blueprint).filter(Blueprint.episode_number == episode_number).first()
        if blueprint_episode:
            db.delete(blueprint_episode)
            logger.info(f"Deleted blueprint episode record {episode_number} from blueprints table")
        else:
            logger.warning(f"No blueprint episode record found for {episode_number} in blueprints table")

        # Delete associated rundown items (via rundown relationship)
        if episode_record:
            # Get all rundowns for this episode
            episode_rundowns = db.query(Rundown).filter(Rundown.episode_id == episode_record.id).all()
            rundown_item_count = 0
            for rundown in episode_rundowns:
                # Get all rundown items for each rundown
                rundown_items = db.query(RundownItem).filter(RundownItem.rundown_id == rundown.id).all()
                for item in rundown_items:
                    db.delete(item)
                    rundown_item_count += 1
                # Delete the rundown itself
                db.delete(rundown)
            if rundown_item_count > 0:
                logger.info(f"Deleted {rundown_item_count} rundown items and {len(episode_rundowns)} rundowns for episode {episode_number}")

        # Delete segments associated with this episode
        if episode_record:
            segments = db.query(Segment).filter(Segment.episode_id == episode_record.id).all()
            segment_count = len(segments)
            for segment in segments:
                db.delete(segment)
            if segment_count > 0:
                logger.info(f"Deleted {segment_count} segments for episode {episode_number}")

        # Now delete the episode record itself (after using it to find related records)
        if episode_record:
            db.delete(episode_record)
            logger.info(f"Deleted episode record {episode_number} from episodes table")

        # Clean up any assets that might be referenced by episode_number string
        # Note: The cascade relationships should handle most of this, but we're being thorough

        # Commit database changes
        db.commit()
        logger.info(f"Database deletion completed for episode {episode_number}")

        # Calculate total deletions for response
        total_deleted = ((1 if episode_record else 0) +
                        (1 if blueprint_episode else 0))

        # Delete from filesystem if it exists - create backup first
        backup_path = None
        if filesystem_exists:
            backup_dir = EPISODES_ROOT / ".trash" / f"{episode_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.parent.mkdir(exist_ok=True)
            shutil.move(str(episode_dir), str(backup_dir))
            backup_path = str(backup_dir)
            logger.info(f"Episode {episode_number} filesystem moved to {backup_dir}")

        # Build appropriate response message
        if filesystem_exists:
            message = f"Episode {episode_number} deleted successfully from filesystem and database"
        else:
            message = f"Episode {episode_number} database records deleted (no filesystem directory existed)"

        logger.info(f"Episode {episode_number} deletion completed: filesystem={'yes' if filesystem_exists else 'no'}, db_records={total_deleted}")

        return {
            "success": True,
            "message": message,
            "backup_path": backup_path,
            "filesystem_deleted": filesystem_exists,
            "database_records_deleted": {
                "episodes": 1 if episode_record else 0,
                "blueprints": 1 if blueprint_episode else 0,
                "rundown_items": rundown_item_count,
                "additional_rundown_items": 0,  # No longer used after architecture cleanup
                "segments": segment_count,
                "total_records": total_deleted
            }
        }

    except Exception as e:
        # Rollback database changes if filesystem deletion fails
        db.rollback()
        logger.error(f"Failed to delete episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete episode: {str(e)}")


@router.post("/{episode_number}/force-cleanup")
async def force_cleanup_phantom_records(
    episode_number: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Force cleanup any phantom database records for an episode.
    Use this if episode recreation fails due to leftover database records.
    """
    from models_v2 import Episode, Segment
    # from models import RundownItem  # REMOVED - models.py deleted
    from models_episode import Blueprint
    from models_v2 import RundownItem

    cleaned_records = []

    try:
        # Clean up all possible database records
        tables_to_clean = [
            (Episode, "episodes"),
            (Blueprint, "blueprints"),
            (RundownItem, "rundown_items"),
            (Segment, "segments")
        ]

        for model_class, table_name in tables_to_clean:
            records = db.query(model_class).filter(
                model_class.episode_number == episode_number
            ).all()

            if records:
                for record in records:
                    db.delete(record)
                cleaned_records.append(f"{table_name}: {len(records)} records")
                logger.info(f"Force cleaned {len(records)} records from {table_name} for episode {episode_number}")

        # Commit all cleanup
        db.commit()

        return {
            "success": True,
            "message": f"Force cleanup completed for episode {episode_number}",
            "cleaned_records": cleaned_records,
            "total_cleaned": len(cleaned_records)
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to force cleanup episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to force cleanup: {str(e)}")


@router.get("/{episode_number}/conflicts")
async def check_episode_conflicts_endpoint(
    episode_number: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check what conflicts prevent episode creation without attempting to create it.
    Useful for diagnosing phantom record issues.
    """
    return check_episode_conflicts(episode_number, db)


@router.post("/{episode_number}/duplicate")
async def duplicate_episode(
    episode_number: str,
    new_episode_number: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Duplicate an existing episode to a new episode number"""

    # Validate episode numbers
    if not new_episode_number.isdigit() or len(new_episode_number) != 4:
        raise HTTPException(status_code=400, detail="New episode number must be 4 digits")

    source_dir = EPISODES_ROOT / episode_number
    if not source_dir.exists():
        raise HTTPException(status_code=404, detail=f"Source episode {episode_number} not found")

    target_dir = EPISODES_ROOT / new_episode_number
    if target_dir.exists():
        raise HTTPException(status_code=409, detail=f"Target episode {new_episode_number} already exists")

    try:
        import shutil

        # Copy entire directory structure
        shutil.copytree(source_dir, target_dir)

        # Update info.md with new episode number
        info_path = target_dir / "info.md"
        if info_path.exists():
            with open(info_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse and update frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1].strip()
                    body = parts[2]

                    frontmatter = yaml.safe_load(frontmatter_text) or {}
                    frontmatter['episode_number'] = new_episode_number
                    frontmatter['title'] = f"{frontmatter.get('title', '')} (Copy)"
                    frontmatter['status'] = 'draft'
                    frontmatter['publish_status'] = 'draft'
                    frontmatter['airdate'] = None  # Clear air date

                    new_yaml = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
                    new_content = f"---\n{new_yaml}---{body}"

                    with open(info_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

        logger.info(f"Duplicated episode {episode_number} to {new_episode_number}")

        return {
            "success": True,
            "message": f"Episode {episode_number} duplicated to {new_episode_number}",
            "source": episode_number,
            "target": new_episode_number,
            "path": str(target_dir)
        }

    except Exception as e:
        logger.error(f"Failed to duplicate episode: {e}")
        # Clean up if partial copy occurred
        if target_dir.exists():
            shutil.rmtree(target_dir)
        raise HTTPException(status_code=500, detail=f"Failed to duplicate episode: {str(e)}")


@router.get("/next-number")
async def get_next_episode_number(
    current_user: Optional[dict] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get the next available episode number from database"""
    from models_v2 import Episode

    try:
        # Get all existing episode numbers from database
        existing_episodes = db.query(Episode.episode_number).filter(Episode.episode_number.isnot(None)).all()

        if not existing_episodes:
            next_number = 1
        else:
            # Extract episode numbers and find max
            episode_numbers = [ep[0] for ep in existing_episodes if ep[0] is not None]
            next_number = max(episode_numbers) + 1 if episode_numbers else 1

        logger.info(f"Next available episode number: {next_number:04d}")
        return {
            "next_number": str(next_number).zfill(4),
            "existing_count": len(existing_episodes)
        }

    except Exception as e:
        logger.error(f"Error getting next episode number from database: {e}")
        # Fallback to a reasonable default
        return {"next_number": "0001", "existing_count": 0}
