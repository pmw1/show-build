"""
Episodes management router for Show-Build application
Handles episode creation, listing, and metadata management
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from pathlib import Path
import os
import re
import yaml
import json
import frontmatter
from datetime import datetime
from auth.utils import get_current_user_or_key
from database import get_db
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/episodes", tags=["episodes"])

# Content versioning configuration
MAX_VERSIONS_PER_ITEM = 20  # Keep last 20 versions per rundown item

def create_content_version(db: Session, rundown_item, change_type: str = "manual_save", username: str = None):
    """
    Create a version snapshot of rundown item content.

    Args:
        db: Database session
        rundown_item: RundownItem object
        change_type: Type of change ('manual_save', 'autosave', 'api_update', 'restore')
        username: Username making the change

    Returns:
        ContentVersion object or None if content unchanged
    """
    import hashlib
    import re
    from models_v2 import ContentVersion

    # Get content and calculate hash
    content = rundown_item.script_content or ''
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

    # Check if content changed from last version
    last_version = db.query(ContentVersion).filter(
        ContentVersion.rundown_item_id == rundown_item.id
    ).order_by(ContentVersion.version_number.desc()).first()

    if last_version and last_version.content_hash == content_hash:
        logger.info(f"Content unchanged for {rundown_item.asset_id}, skipping version creation")
        return None

    # Get next version number
    version_number = (last_version.version_number + 1) if last_version else 1

    # Calculate content length (strip HTML tags for accurate count)
    content_length = len(re.sub(r'<[^>]+>', '', content).strip())

    # Create new version
    new_version = ContentVersion(
        rundown_item_id=rundown_item.id,
        asset_id=rundown_item.asset_id,
        version_number=version_number,
        script_content=content,
        content_hash=content_hash,
        content_length=content_length,
        change_type=change_type,
        created_by=username
    )

    db.add(new_version)
    db.flush()  # Get the ID

    # Clean up old versions (keep only last MAX_VERSIONS_PER_ITEM)
    old_versions = db.query(ContentVersion).filter(
        ContentVersion.rundown_item_id == rundown_item.id
    ).order_by(ContentVersion.version_number.desc()).offset(MAX_VERSIONS_PER_ITEM).all()

    for old_version in old_versions:
        db.delete(old_version)

    logger.info(f"📸 Created version {version_number} for {rundown_item.asset_id} ({content_length} chars, {change_type})")
    return new_version

def check_episode_conflicts(episode_number: str, db: Session) -> Dict[str, Any]:
    """Check for episode conflicts across all tables and filesystem"""
    from models_v2 import Episode
    from models_episode import Blueprint

    conflicts = []

    # Check episodes table (models_v2)
    episode_v2 = db.query(Episode).filter(
        Episode.episode_number == episode_number
    ).first()
    if episode_v2:
        conflicts.append(f"episodes database table (id: {episode_v2.id})")

    # Check episode_templates table (models_episode)
    episode_template = db.query(Blueprint).filter(
        Blueprint.episode_number == episode_number
    ).first()
    if episode_template:
        conflicts.append(f"blueprints database table (id: {episode_template.id})")

    # Check filesystem
    episode_dir = EPISODES_ROOT / episode_number
    if episode_dir.exists():
        conflicts.append(f"filesystem directory: {episode_dir}")
    
    return {
        "has_conflicts": len(conflicts) > 0,
        "conflicts": conflicts,
        "episode_number": episode_number
    }

# Base path for episodes - use Docker mount path which maps to host /mnt/sync/disaffected/episodes
EPISODES_ROOT = Path("/home/episodes")
EPISODE_ROOT = EPISODES_ROOT  # Alias for compatibility

class RundownMetadata(BaseModel):
    """Rundown metadata model with bidirectional linking"""
    assetid: int = Field(..., description="Asset identifier for this rundown")
    show_id: int = Field(..., description="Asset ID of the show this rundown belongs to (required)")
    episode_id: int = Field(..., description="Asset ID of the episode using this rundown")
    template_name: Optional[str] = Field(None, description="Template name if this is a reusable rundown")
    created_date: Optional[str] = Field(None, description="Date rundown was created")
    modified_date: Optional[str] = Field(None, description="Date rundown was last modified")
    segment_count: int = Field(0, description="Number of segments in this rundown")
    total_duration: str = Field("00:00:00", description="Total duration of all segments")

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

@router.get("")
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
                "subtitle": "", # TODO: Add subtitle field if needed
                "airdate": ep.air_date.isoformat() if ep.air_date else None,
                "status": ep.status or "draft",
                "duration": ep.duration_formatted or "01:00:00",
                "description": "", # TODO: Add description field if needed
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

class ReorderRequest(BaseModel):
    """Request model for reordering rundown segments"""
    segments: List[Dict[str, Any]] = Field(..., description="List of segments with filename and new order")

@router.post("/rundown/{episode_number}/reorder")
async def reorder_rundown(
    episode_number: str,
    payload: ReorderRequest,
    current_user: Optional[dict] = None
) -> Dict[str, str]:
    """Update the order field in frontmatter for each rundown segment."""
    episode_dir = EPISODES_ROOT / episode_number
    rundown_dir = episode_dir / "rundown"
    
    if not rundown_dir.exists():
        raise HTTPException(status_code=404, detail=f"Episode {episode_number} rundown not found")
    
    try:
        for segment in payload.segments:
            filename = segment.get("filename")
            new_order = segment.get("order")
            
            if not filename or new_order is None:
                continue
                
            file_path = rundown_dir / filename
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue
            
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter and body
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = yaml.safe_load(parts[1])
                    body = parts[2]
                    
                    # Update the order field
                    front_matter['order'] = new_order
                    
                    # Rebuild the file content
                    new_content = '---\n'
                    new_content += yaml.dump(front_matter, default_flow_style=False, sort_keys=False)
                    new_content += '---'
                    new_content += body
                    
                    # Write back to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
        
        return {"status": "success", "message": "Rundown order updated"}
        
    except Exception as e:
        logger.error(f"Failed to reorder rundown: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reorder rundown: {str(e)}")

class EpisodeMetadata(BaseModel):
    """Episode-specific metadata model (show-level fields are in ShowConfig)"""
    # Core episode identifiers
    assetid: int = Field(0, description="Asset identifier for this episode")
    show_id: int = Field(..., description="Asset ID of the show this episode belongs to (required)")
    rundown_id: int = Field(..., description="Asset ID of the rundown linked to this episode (required)")
    episode_number: str = Field(..., description="Episode number (4 digits)")
    type: str = Field("full_show", description="Episode type (full_show, sunday_show, etc.)")
    
    # Episode information
    airdate: Optional[str] = Field(None, description="Air date in YYYY-MM-DD format")
    title: str = Field(..., description="Episode title")
    subtitle: Optional[str] = Field(None, description="Episode subtitle")
    slug: str = Field(..., description="URL-friendly slug")
    description: Optional[str] = Field(None, description="Full description of episode")
    duration: str = Field("01:00:00", description="Episode duration in HH:MM:SS format")
    guest: Optional[str] = Field(None, description="Guest names")
    tags: List[str] = Field(default_factory=list, description="Episode tags")
    
    # Episode-specific publishing settings
    omnystudio_visibility: Optional[str] = Field("public", description="Omnystudio visibility for this episode")
    omnystudio_publish_status: Optional[str] = Field("draft", description="Omnystudio publish status")
    omnystudio_publish_datetime: Optional[str] = Field(None, description="Omnystudio publish datetime")
    
    youtube_privacy_status: Optional[str] = Field("private", description="YouTube privacy status")
    youtube_title: Optional[str] = Field(None, description="YouTube specific title (overrides episode title)")
    youtube_description: Optional[str] = Field(None, description="YouTube specific description")
    youtube_tags: Optional[str] = Field(None, description="YouTube tags for this episode")
    
    # Social media settings
    social_hashtags: Optional[str] = Field(None, description="Social media hashtags for this episode")
    twitter_thread: bool = Field(False, description="Create Twitter thread")
    instagram_reel: bool = Field(False, description="Create Instagram reel")
    facebook_post: bool = Field(False, description="Create Facebook post")
    
    # Content ratings
    explicit: bool = Field(False, description="Explicit content flag")
    content_warnings: Optional[str] = Field(None, description="Content warnings")
    
    # Publishing control
    publish_status: str = Field("draft", description="Overall publish status")
    schedule_datetime: Optional[str] = Field(None, description="Scheduled publish datetime")
    visibility: str = Field("public", description="Overall visibility")
    
    # Production info
    recording_date: Optional[str] = Field(None, description="Recording date")
    producer: Optional[str] = Field(None, description="Producer names")
    editor: Optional[str] = Field(None, description="Editor names")
    
    # Internal
    notes: Optional[str] = Field(None, description="Internal notes")
    server_messages: Optional[str] = Field(None, description="Server messages")

def create_episode_directory(episode_number: str) -> Path:
    """Create the complete directory structure for a new episode"""
    episode_dir = EPISODES_ROOT / episode_number
    
    # Standard episode directory structure
    directories = [
        episode_dir,
        episode_dir / "assets",
        episode_dir / "assets" / "audio",
        episode_dir / "assets" / "video",
        episode_dir / "assets" / "graphics",
        episode_dir / "assets" / "images",
        episode_dir / "assets" / "quotes",
        episode_dir / "assets" / "generated_quotes",
        episode_dir / "assets" / "thumbnails",
        episode_dir / "rundown",
        episode_dir / "rundown" / "ordered_media",
        episode_dir / "preshow",
        episode_dir / "captures",
        episode_dir / "exports",
        episode_dir / "publish"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    return episode_dir

def create_info_file(episode_dir: Path, metadata: EpisodeMetadata, script_content: Optional[str] = None) -> Path:
    """Create the info.md file with YAML frontmatter"""
    info_path = episode_dir / "info.md"
    
    # Convert metadata to dict and clean up None values
    metadata_dict = metadata.dict(exclude_none=True)
    
    # Create YAML frontmatter
    yaml_content = yaml.dump(metadata_dict, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    # Create the full content with script section
    content = f"""---
{yaml_content}---

# Episode {metadata.episode_number}: {metadata.title}

## Overview
{metadata.description or 'Episode overview and notes go here.'}

## Script
{script_content or '<!-- Episode script will be compiled from rundown segments -->'}

## Segments
- TBD

## Notes
{metadata.notes or '- Production notes'}
"""
    
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return info_path

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
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Delete an episode and all its content from both filesystem and database"""
    
    episode_dir = EPISODES_ROOT / episode_number
    
    if not episode_dir.exists():
        raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found in filesystem")
    
    try:
        import shutil
        from datetime import datetime
        from models_v2 import Episode, RundownItem, Segment, Break, Rundown
        # from models import Asset, ProcessingJob, ExtractedQuote  # REMOVED - models.py deleted
        from models_episode import Blueprint
        
        # First, delete from database to ensure data consistency
        logger.info(f"Starting deletion of episode {episode_number} from database")

        # Initialize counters for response
        rundown_item_count = 0
        segment_count = 0
        
        # Find episode record from episodes table (models_v2) - don't delete yet
        # Convert episode_number string to int for database query
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
        
        # Now delete from filesystem - create backup first
        backup_dir = EPISODES_ROOT / ".trash" / f"{episode_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.parent.mkdir(exist_ok=True)
        shutil.move(str(episode_dir), str(backup_dir))
        
        logger.info(f"Episode {episode_number} deleted successfully (filesystem moved to {backup_dir})")
        
        return {
            "success": True,
            "message": f"Episode {episode_number} deleted successfully from filesystem and database",
            "backup_path": str(backup_dir),
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

# Script Management Endpoints
# The script is stored in two ways:
# 1. Individual segments in rundown/*.md files (source of truth)
# 2. Compiled script in info.md or separate script.md file (generated)

@router.get("/{episode_number}/script")
async def get_episode_script(
    episode_number: str,
    format: str = "markdown",  # markdown, html, text
    current_user: Optional[dict] = None
) -> Dict[str, Any]:
    """
    Get the compiled script for an episode.
    
    Script Storage Strategy:
    - Individual segments are stored in rundown/*.md files
    - Each segment has its own script section
    - The full script is compiled from all segments in order
    - Can be cached in info.md or a separate compiled_script.md
    """
    
    episode_dir = EPISODES_ROOT / episode_number
    if not episode_dir.exists():
        raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")
    
    rundown_dir = episode_dir / "rundown"
    if not rundown_dir.exists():
        return {
            "episode_number": episode_number,
            "script": "",
            "segments": [],
            "format": format
        }
    
    # Compile script from rundown segments
    segments = []
    compiled_script = []
    
    # Get all markdown files in rundown directory
    rundown_files = sorted(rundown_dir.glob("*.md"))
    
    for file_path in rundown_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter and content
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1].strip()
                    body = parts[2].strip()
                    
                    frontmatter = yaml.safe_load(frontmatter_text) or {}
                    
                    # Extract script section from body
                    script_text = ""
                    if "## Script" in body:
                        script_start = body.find("## Script")
                        script_section = body[script_start:]
                        # Find the next section or end of file
                        next_section = script_section.find("\n## ", 1)
                        if next_section > 0:
                            script_text = script_section[10:next_section].strip()
                        else:
                            script_text = script_section[10:].strip()
                    
                    segment_info = {
                        "file": file_path.name,
                        "order": frontmatter.get("order", 999),
                        "type": frontmatter.get("type", "segment"),
                        "title": frontmatter.get("title", "Untitled"),
                        "duration": frontmatter.get("duration", "00:00:00"),
                        "script": script_text
                    }
                    segments.append(segment_info)
                    
                    if script_text:
                        compiled_script.append(f"### {segment_info['title']}\n\n{script_text}")
                        
        except Exception as e:
            logger.warning(f"Could not process rundown file {file_path}: {e}")
    
    # Sort segments by order
    segments.sort(key=lambda x: x["order"])
    
    # Join all scripts
    full_script = "\n\n---\n\n".join(compiled_script)
    
    # Convert format if needed
    if format == "html":
        import markdown
        full_script = markdown.markdown(full_script)
    elif format == "text":
        # Strip markdown formatting for plain text
        import re
        full_script = re.sub(r'#{1,6}\s+', '', full_script)  # Remove headers
        full_script = re.sub(r'\*\*(.+?)\*\*', r'\1', full_script)  # Remove bold
        full_script = re.sub(r'\*(.+?)\*', r'\1', full_script)  # Remove italic
        full_script = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', full_script)  # Remove links
    
    return {
        "episode_number": episode_number,
        "script": full_script,
        "segments": segments,
        "format": format,
        "total_segments": len(segments),
        "word_count": len(full_script.split())
    }

@router.get("/{episode_number}/info")
async def get_episode_info(episode_number: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get episode metadata from database."""
    from models_v2 import Episode

    try:
        # Convert episode number to int
        episode_num_int = int(episode_number)

        # Get episode from database
        episode = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        # Convert database record to info format
        info = {
            "episode_number": f"{episode.episode_number:04d}",
            "title": episode.title or "Untitled",
            "slug": episode.slug or f"episode-{episode_number}",
            "status": episode.status or "draft",
            "airdate": episode.air_date.isoformat() if episode.air_date else None,
            "publish_date": episode.publish_date.isoformat() if episode.publish_date else None,
            "duration": episode.duration_formatted or "01:00:00",
            "guest": episode.guest_name or "",
            "guest_bio": episode.guest_bio or "",
            "guest_website": episode.guest_website or "",
            "template_type": episode.template_type or "",
            "template_id": episode.template_id or "",
            "template_name": episode.template_name or "",
            "asset_id": episode.asset_id,
            "season_id": episode.season_id,
            "created_at": episode.created_at.isoformat() if episode.created_at else None,
            "updated_at": episode.updated_at.isoformat() if episode.updated_at else None,
            "is_test_data": episode.is_test_data or False,
            "is_dummy": episode.is_dummy or False
        }

        logger.info(f"Retrieved episode info from database for episode {episode_number}")
        return {"info": info}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode number format")
    except Exception as e:
        logger.error(f"Error reading episode info from database: {e}")
        raise HTTPException(status_code=500, detail="Error reading episode info from database")

@router.get("/{episode_number}/rundown")
async def get_episode_rundown(episode_number: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get all rundown items for an episode from database."""
    from models_v2 import Episode, Rundown, RundownItem

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
            items = db.query(RundownItem).filter(RundownItem.rundown_id == rundown.id).order_by(RundownItem.order_in_rundown).all()

            for item in items:
                order_value = item.order_in_rundown or 0
                rundown_item_dict = {
                    "id": item.asset_id,
                    "type": item.item_type or 'segment',
                    "slug": item.slug or '',
                    "duration": item.duration or '00:00:00',
                    "script": item.script_content or '',  # Script content from new field
                    "order": order_value,
                    "order_in_rundown": order_value,  # Explicit field for frontend
                    "index": order_value,  # Explicit field for frontend
                    "status": item.status or 'draft',
                    "title": item.title or item.slug or 'Untitled',
                    "subtitle": item.subtitle or '',
                    "description": item.description or '',  # Metadata description
                    "filename": f"{order_value:03d}-{item.slug}.md",  # Generate filename for compatibility
                    "asset_id": item.asset_id,
                    "airdate": item.airdate.isoformat() if item.airdate else '',
                    "guests": item.guests or '',
                    "resources": item.resources or '',
                    "tags": item.tags or '',
                    "priority": item.priority or '',
                    "server_message": item.server_message or '',
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                }
                rundown_items.append(rundown_item_dict)

        # Sort by order field
        rundown_items.sort(key=lambda x: x.get('order', 999))

        logger.info(f"Retrieved {len(rundown_items)} rundown items from database for episode {episode_number}")
        return {"items": rundown_items}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode number format")
    except Exception as e:
        logger.error(f"Error retrieving rundown from database for episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving rundown from database")

@router.get("/{episode_number}/statistics")
async def get_episode_statistics(episode_number: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get statistics for an episode's rundown items."""
    from models_v2 import Episode, Rundown, RundownItem
    from sqlalchemy import func

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
            # Return empty statistics if no rundowns exist yet
            return {
                "total_items": 0,
                "by_status": {},
                "by_type": {},
                "progress_percentage": 0
            }

        # Get all rundown items for this episode
        rundown_ids = [r.id for r in rundowns]
        items = db.query(RundownItem).filter(RundownItem.rundown_id.in_(rundown_ids)).all()

        # Calculate statistics
        total_items = len(items)
        by_status = {}
        by_type = {}

        for item in items:
            # Count by status
            status = item.status or 'draft'
            by_status[status] = by_status.get(status, 0) + 1

            # Count by type
            item_type = item.item_type or 'segment'
            by_type[item_type] = by_type.get(item_type, 0) + 1

        # Calculate progress percentage
        # Items that are 'approved' or 'completed' count as done
        completed_count = by_status.get('approved', 0) + by_status.get('completed', 0)
        progress_percentage = round((completed_count / total_items * 100) if total_items > 0 else 0)

        logger.info(f"Retrieved statistics for episode {episode_number}: {total_items} items")
        return {
            "total_items": total_items,
            "by_status": by_status,
            "by_type": by_type,
            "progress_percentage": progress_percentage
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode number format")
    except Exception as e:
        logger.error(f"Error retrieving statistics for episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving episode statistics")

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


@router.post("/{episode_number}/enumerate-cues")
async def enumerate_cue_blocks(
    episode_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """
    Enumerate all cue blocks in an episode with sequential numbering.

    Process:
    1. Iterate through all rundown items in chronological order
    2. Find all cue blocks (<!-- Begin Cue --> ... <!-- End Cue -->)
    3. Strip any existing enumeration prefix from slugs
    4. Add new enumeration prefix (10, 20, 30, ...)
    5. Add/update [Enumerator: XX] field for display
    6. Rename associated media files
    7. Update MediaUrl fields
    8. Save changes to database

    This is idempotent - running again will re-enumerate cleanly.
    """
    from models_v2 import RundownItem, Rundown, Episode
    import shutil

    try:
        logger.info(f"Starting cue block enumeration for episode {episode_number}")

        # Normalize episode number
        episode_id_normalized = episode_number.zfill(4) if len(episode_number) < 4 else episode_number

        # Get episode
        episode = db.query(Episode).filter(
            Episode.episode_number == int(episode_id_normalized)
        ).first()

        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        # Get rundown
        rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
        if not rundown:
            raise HTTPException(status_code=404, detail=f"Rundown not found for episode {episode_number}")

        # Get all rundown items in order
        rundown_items = db.query(RundownItem).filter(
            RundownItem.rundown_id == rundown.id
        ).order_by(RundownItem.order_in_rundown).all()

        # Episode assets directory - use ShowBuildPaths for correct Docker/host path
        from core.paths import ShowBuildPaths
        path_manager = ShowBuildPaths()
        episodes_root = path_manager.episodes_root
        episode_assets_dir = episodes_root / episode_id_normalized / "assets"

        # Patterns
        slug_pattern = re.compile(r'\[Slug:\s*([^\]]+)\]', re.IGNORECASE)
        mediaurl_pattern = re.compile(r'\[Mediaurl:\s*([^\]]+)\]', re.IGNORECASE)
        enumerator_pattern = re.compile(r'\[Enumerator:\s*[^\]]*\]\n?', re.IGNORECASE)
        enum_prefix_pattern = re.compile(r'^(\d+)[-_](.+)$')

        # Track statistics
        total_cues = 0
        updated_cues = 0
        renamed_files = 0

        # First pass: collect all cue blocks across all items to enumerate globally
        all_cue_data = []

        for item in rundown_items:
            if not item.script_content:
                continue

            # Find all cue blocks in this item
            cue_block_pattern = re.compile(
                r'<!-- Begin Cue -->(.*?)<!-- End Cue -->',
                re.DOTALL
            )
            matches = list(cue_block_pattern.finditer(item.script_content))

            for match in matches:
                total_cues += 1
                cue_body = match.group(1)

                # Extract current slug
                slug_match = slug_pattern.search(cue_body)
                if not slug_match:
                    continue

                all_cue_data.append({
                    'item': item,
                    'match_start': match.start(),
                    'match_end': match.end(),
                    'cue_body': cue_body,
                    'current_slug': slug_match.group(1).strip()
                })

        # Second pass: enumerate and update
        enumeration_counter = 10

        # Group by item for batch updates
        items_to_update = {}

        for cue_info in all_cue_data:
            item = cue_info['item']
            cue_body = cue_info['cue_body']
            current_slug = cue_info['current_slug']

            # Strip existing enumeration prefix
            base_slug = current_slug
            enum_match = enum_prefix_pattern.match(current_slug)
            if enum_match:
                base_slug = enum_match.group(2)

            # Normalize slug: lowercase, replace spaces with hyphens
            normalized_slug = base_slug.lower().replace(' ', '-').replace('_', '-')
            normalized_slug = re.sub(r'-+', '-', normalized_slug)
            normalized_slug = re.sub(r'[^\w-]', '', normalized_slug)

            # Create new enumerated slug
            new_slug = f"{enumeration_counter:02d}-{normalized_slug}"
            enumerator_value = f"{enumeration_counter:02d}"

            # Extract current mediaurl
            mediaurl_match = mediaurl_pattern.search(cue_body)
            old_mediaurl = mediaurl_match.group(1).strip() if mediaurl_match else None

            # Extract cue type to determine correct asset directory
            type_match = re.search(r'\[Type:\s*([^\]]+)\]', cue_body, re.IGNORECASE)
            cue_type = type_match.group(1).strip().upper() if type_match else None

            # Determine new mediaurl and rename file
            new_mediaurl = None
            if old_mediaurl:
                old_filename = Path(old_mediaurl).name
                ext = Path(old_filename).suffix

                # Determine asset type directory based on CUE TYPE first, then path
                # SOT cues should ALWAYS go to video directory
                if cue_type == 'SOT':
                    asset_type = "video"
                    # SOT files are mp4, ensure correct extension
                    if not ext or ext.lower() not in ['.mp4', '.mov', '.mp3']:
                        ext = '.mp4'
                elif cue_type == 'IMG':
                    asset_type = "images"
                elif cue_type == 'FSQ':
                    asset_type = "quotes"
                elif cue_type == 'AUDIO':
                    asset_type = "audio"
                elif "/video/" in old_mediaurl:
                    asset_type = "video"
                elif "/images/" in old_mediaurl:
                    asset_type = "images"
                elif "/audio/" in old_mediaurl:
                    asset_type = "audio"
                elif "/sot/" in old_mediaurl:
                    asset_type = "video"  # sot goes to video
                else:
                    asset_type = "quotes"  # fallback for FSQ and unknown

                new_filename = f"{new_slug}{ext}"
                new_mediaurl = f"/episodes/{episode_id_normalized}/assets/{asset_type}/{new_filename}"

                # Try to rename the actual file
                old_file_path = episodes_root / old_mediaurl.lstrip('/').replace('episodes/', '')
                new_file_path = episode_assets_dir / asset_type / new_filename

                if old_file_path.exists() and str(old_file_path) != str(new_file_path):
                    try:
                        new_file_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(old_file_path), str(new_file_path))
                        renamed_files += 1
                        logger.info(f"Renamed: {old_file_path.name} -> {new_file_path.name}")
                    except Exception as e:
                        logger.warning(f"Could not rename file {old_file_path}: {e}")

            # Store update info for this item
            if item.id not in items_to_update:
                items_to_update[item.id] = {
                    'item': item,
                    'replacements': []
                }

            items_to_update[item.id]['replacements'].append({
                'old_slug': current_slug,
                'new_slug': new_slug,
                'enumerator': enumerator_value,
                'old_mediaurl': old_mediaurl,
                'new_mediaurl': new_mediaurl
            })

            updated_cues += 1
            enumeration_counter += 10

        # Third pass: apply all replacements to each item's content
        for item_id, update_info in items_to_update.items():
            item = update_info['item']
            content = item.script_content

            for repl in update_info['replacements']:
                # Find and update each cue block
                def update_cue_block(match):
                    cue_body = match.group(0)

                    # Check if this is the cue block we're looking for
                    slug_m = slug_pattern.search(cue_body)
                    if not slug_m or slug_m.group(1).strip() != repl['old_slug']:
                        return cue_body

                    # Remove existing Enumerator field if present
                    updated_body = enumerator_pattern.sub('', cue_body)

                    # Update slug
                    updated_body = slug_pattern.sub(f"[Slug: {repl['new_slug']}]", updated_body)

                    # Update mediaurl if applicable
                    if repl['new_mediaurl'] and repl['old_mediaurl']:
                        updated_body = mediaurl_pattern.sub(f"[Mediaurl: {repl['new_mediaurl']}]", updated_body)

                    # Add Enumerator field after [Type: XXX] line
                    type_pattern = re.compile(r'(\[Type:\s*[^\]]+\]\n)', re.IGNORECASE)
                    type_match = type_pattern.search(updated_body)
                    if type_match:
                        insert_pos = type_match.end()
                        updated_body = (
                            updated_body[:insert_pos] +
                            f"[Enumerator: {repl['enumerator']}]\n" +
                            updated_body[insert_pos:]
                        )

                    return updated_body

                # Apply update - process ALL cue blocks (not just count=1)
                # The update_cue_block function only modifies the matching slug
                cue_pattern = re.compile(
                    r'<!-- Begin Cue -->.*?<!-- End Cue -->',
                    re.DOTALL
                )
                content = cue_pattern.sub(update_cue_block, content)
                # Update old_slug for subsequent iterations within same item
                repl['old_slug'] = repl['new_slug']

            item.script_content = content
            db.add(item)

        # Commit all changes
        db.commit()

        logger.info(f"Cue enumeration completed: {updated_cues}/{total_cues} cues updated, {renamed_files} files renamed")

        return {
            "success": True,
            "total": total_cues,
            "updated": updated_cues,
            "renamed": renamed_files,
            "message": f"Enumerated {updated_cues} cue blocks, renamed {renamed_files} files"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enumerate cue blocks for episode {episode_number}: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to enumerate cue blocks: {str(e)}")


def load_rundown_settings() -> dict:
    """Load rundown settings from database"""
    try:
        # from models import Settings  # REMOVED - models.py deleted
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Load rundown-related settings from database
            settings = {}
            
            # Get enumerate_rundown_markdown_files setting
            enumerate_setting = db.query(Settings).filter(
                Settings.key == "enumerate_rundown_markdown_files"
            ).first()
            
            if enumerate_setting:
                settings['enumerate_rundown_markdown_files'] = enumerate_setting.value
            else:
                settings['enumerate_rundown_markdown_files'] = True  # Default
            
            # Get auto_number_rundown_items setting
            auto_number_setting = db.query(Settings).filter(
                Settings.key == "auto_number_rundown_items"
            ).first()
            
            if auto_number_setting:
                settings['auto_number_rundown_items'] = auto_number_setting.value
            else:
                settings['auto_number_rundown_items'] = True  # Default
                
            return settings
            
        finally:
            db.close()
            
    except Exception as e:
        logger.warning(f"Could not load rundown settings from database: {e}")
    
    # Return defaults if loading fails
    return {
        'enumerate_rundown_markdown_files': True,
        'auto_number_rundown_items': True
    }

async def normalize_rundown_items(rundown_dir: Path, episode_number: str) -> dict:
    """
    Core normalization logic for rundown items.
    
    Process:
    1. Scan all .md files and extract current index/order
    2. Build normalization map with conflict resolution
    3. Update files with new indexes and order fields
    4. Return summary of changes
    """
    changes = []
    errors = []
    
    try:
        # Step 1: Scan existing rundown items
        items_data = scan_rundown_items(rundown_dir)
        logger.info(f"Scanned {len(items_data)} rundown items")
        
        # Step 2: Calculate normalized indexes with conflict resolution
        normalized_items = calculate_normalized_indexes(items_data)
        logger.info(f"Calculated normalized indexes for {len(normalized_items)} items")
        
        # Load settings to determine filename format
        rundown_settings = load_rundown_settings()
        
        # Step 3: Apply changes (rename files and update frontmatter)
        changes, errors = await apply_normalization_changes(rundown_dir, items_data, normalized_items, rundown_settings)
        
        return {
            "success": True,
            "episode_number": episode_number,
            "items_processed": len(items_data),
            "changes_applied": len(changes),
            "errors": len(errors),
            "changes": changes,
            "error_details": errors
        }
        
    except Exception as e:
        logger.error(f"Error in normalize_rundown_items: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "changes": changes,
            "error_details": errors
        }

def scan_rundown_items(rundown_dir: Path) -> list:
    """
    Scan rundown directory and extract current index/order data.
    
    Returns list of dicts with:
    - filename: original filename
    - filepath: full path to file
    - current_index: index from filename (or None)
    - current_order: order from frontmatter (or None)
    - frontmatter: parsed frontmatter dict
    """
    items = []
    
    for file_path in rundown_dir.glob("*.md"):
        try:
            # Extract index from filename (support both formats: "123 Title.md" and "123-Title.md")
            filename = file_path.name
            filename_match = re.match(r'^(\d+)[-\s]', filename)
            current_index = int(filename_match.group(1)) if filename_match else None
            
            # Read and parse frontmatter
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                
            current_order = post.metadata.get('order')
            if isinstance(current_order, str):
                try:
                    current_order = int(current_order)
                except ValueError:
                    current_order = None
            
            items.append({
                'filename': filename,
                'filepath': file_path,
                'current_index': current_index,
                'current_order': current_order,
                'frontmatter': post.metadata,
                'content': post.content,
                'title': post.metadata.get('title', ''),
                'type': post.metadata.get('type', 'segment'),
                'slug': post.metadata.get('slug', '')
            })
            
            logger.debug(f"Scanned {filename}: index={current_index}, order={current_order}")
            
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {str(e)}")
            continue
    
    # Sort by current index (or order as fallback, or filename)
    def sort_key(item):
        if item['current_index'] is not None:
            return item['current_index']
        elif item['current_order'] is not None:
            return item['current_order']
        else:
            return 9999  # Push items without index/order to end
    
    items.sort(key=sort_key)
    return items

def calculate_normalized_indexes(items_data: list) -> list:
    """
    Calculate normalized index values with conflict resolution.
    
    Rules:
    1. Round non-multiple-of-10 indexes up to next multiple of 10
    2. Handle conflicts by cascading bumps
    3. Maintain relative ordering
    
    Returns list of dicts with:
    - original_item: reference to original item data
    - new_index: calculated normalized index
    - needs_rename: whether filename needs to change
    - needs_order_update: whether frontmatter order needs update
    """
    normalized = []
    used_indexes = set()
    
    for item in items_data:
        current_index = item['current_index']
        
        # Use current index, or assign based on position if no index
        if current_index is not None:
            target_index = current_index
        else:
            # Assign index based on position (start at 10, increment by 10)
            target_index = (len(normalized) + 1) * 10
        
        # Round up to next multiple of 10
        normalized_index = ((target_index + 9) // 10) * 10
        
        # Handle conflicts by finding next available multiple of 10
        while normalized_index in used_indexes:
            normalized_index += 10
            
        used_indexes.add(normalized_index)
        
        # Determine what changes are needed
        needs_rename = (current_index != normalized_index) or (current_index is None)
        needs_order_update = (item['current_order'] != normalized_index)
        
        normalized.append({
            'original_item': item,
            'new_index': normalized_index,
            'needs_rename': needs_rename,
            'needs_order_update': needs_order_update
        })
        
        logger.debug(f"Item '{item['filename']}': {current_index} -> {normalized_index} "
                    f"(rename: {needs_rename}, order_update: {needs_order_update})")
    
    return normalized

async def apply_normalization_changes(rundown_dir: Path, items_data: list, normalized_items: list, rundown_settings: dict) -> tuple:
    """
    Apply the calculated normalization changes to files.
    
    Args:
        rundown_dir: Directory containing rundown files
        items_data: Original item data
        normalized_items: Calculated normalization data
        rundown_settings: Settings dict containing enumerate_rundown_markdown_files flag
    
    Returns tuple of (changes, errors)
    """
    changes = []
    errors = []
    
    for norm_item in normalized_items:
        item = norm_item['original_item']
        new_index = norm_item['new_index']
        
        try:
            change_record = {
                'original_filename': item['filename'],
                'original_index': item['current_index'],
                'original_order': item['current_order'],
                'new_index': new_index,
                'actions': []
            }
            
            # Generate new filename based on settings
            enumerate_files = rundown_settings.get('enumerate_rundown_markdown_files', True)
            
            if enumerate_files:
                # Use format: "{enumeration}-{type}-{slug}.md" for file system organization
                item_type = item['type'] or 'segment'
                slug = item['slug'] or item['title'] or item_type
                
                # Clean type and slug for filename
                clean_type = re.sub(r'[^\w-]', '', item_type).strip().lower()
                clean_slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
                clean_slug = re.sub(r'[-\s]+', '-', clean_slug)[:40]  # Use dashes, limit length
                
                new_filename = f"{new_index:03d}-{clean_type}-{clean_slug}.md"
            else:
                # Use plain format: "{type}-{slug}.md" (no enumeration prefix)
                item_type = item['type'] or 'segment'
                slug = item['slug'] or item['title'] or item_type
                
                # Clean type and slug for filename
                clean_type = re.sub(r'[^\w-]', '', item_type).strip().lower()
                clean_slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
                clean_slug = re.sub(r'[-\s]+', '-', clean_slug)[:50]  # Allow longer names without prefix
                
                new_filename = f"{clean_type}-{clean_slug}.md"
            
            # Update frontmatter order field
            updated_frontmatter = item['frontmatter'].copy()
            updated_frontmatter['order'] = new_index
            
            # Create new file with updated frontmatter
            new_filepath = rundown_dir / new_filename
            post = frontmatter.Post(item['content'], **updated_frontmatter)
            
            with open(new_filepath, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
                
            change_record['actions'].append('created_new_file')
            change_record['new_filename'] = new_filename
            
            # Remove old file if filename changed (always remove if it's different)
            if item['filename'] != new_filename:
                old_filepath = item['filepath']
                if old_filepath.exists():
                    old_filepath.unlink()
                    change_record['actions'].append('removed_old_file')
                    logger.info(f"Removed old file: {item['filename']}")
            
            if norm_item['needs_order_update']:
                change_record['actions'].append('updated_order_field')
            
            changes.append(change_record)
            logger.info(f"Normalized {item['filename']} -> {new_filename} (index: {new_index})")
            
        except Exception as e:
            error_record = {
                'filename': item['filename'],
                'error': str(e),
                'new_index': new_index
            }
            errors.append(error_record)
            logger.error(f"Error normalizing {item['filename']}: {str(e)}")
    
    return changes, errors

@router.put("/{episode_number}/script")
async def update_episode_script(
    episode_number: str,
    segment_file: str = Body(..., description="Rundown file name (e.g., '10 Opening.md')"),
    script_content: str = Body(..., description="New script content for the segment"),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """
    Update the script content for a specific segment.
    
    Note: Scripts are stored in individual rundown segment files,
    not as a single monolithic script file.
    """
    
    episode_dir = EPISODES_ROOT / episode_number
    if not episode_dir.exists():
        raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")
    
    rundown_file = episode_dir / "rundown" / segment_file
    if not rundown_file.exists():
        raise HTTPException(status_code=404, detail=f"Segment file {segment_file} not found")
    
    try:
        # Read existing file
        with open(rundown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse frontmatter and body
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                body = parts[2]
                
                # Find and replace script section
                if "## Script" in body:
                    script_start = body.find("## Script")
                    before_script = body[:script_start]
                    
                    # Find the next section
                    remaining = body[script_start:]
                    next_section = remaining.find("\n## ", 1)
                    if next_section > 0:
                        after_script = remaining[next_section:]
                    else:
                        after_script = ""
                    
                    # Rebuild body with new script
                    new_body = f"{before_script}## Script\n\n{script_content}\n{after_script}"
                else:
                    # Add script section if it doesn't exist
                    new_body = f"{body}\n\n## Script\n\n{script_content}"
                
                # Rebuild complete file
                new_content = f"---{frontmatter}---{new_body}"
                
                # Write back
                with open(rundown_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                return {
                    "success": True,
                    "message": f"Script updated for segment {segment_file}",
                    "episode_number": episode_number,
                    "segment_file": segment_file
                }
        else:
            raise HTTPException(status_code=400, detail="Invalid file format - missing frontmatter")
            
    except Exception as e:
        logger.error(f"Failed to update script: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update script: {str(e)}")

@router.put("/{episode_number}/info")
async def update_episode_info(episode_number: str, info_data: dict, current_user: dict = Depends(get_current_user_or_key)):
    """Update episode information in both info.md file and database"""
    from sqlalchemy.orm import Session
    from database import get_db
    from models_v2 import Episode
    from fastapi import Depends
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        info_path = EPISODES_ROOT / episode_number / "info.md"
        
        # Update the info.md file first
        existing_body = ""
        if info_path.exists():
            with open(info_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    existing_body = parts[2].strip()
        
        # Create new content with updated frontmatter
        import yaml
        frontmatter_yaml = yaml.dump(info_data, default_flow_style=False, allow_unicode=True)
        new_content = f"---\n{frontmatter_yaml}---\n{existing_body}"
        
        # Write back to file
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Update database record if it exists
        try:
            episode_num = int(episode_number)
            db_episode = db.query(Episode).filter(Episode.episode_number == episode_num).first()
            
            if db_episode:
                # Update database fields from info_data
                if 'title' in info_data:
                    db_episode.title = info_data['title']
                if 'status' in info_data:
                    db_episode.status = info_data['status']
                if 'airdate' in info_data and info_data['airdate']:
                    from datetime import datetime
                    try:
                        db_episode.air_date = datetime.fromisoformat(info_data['airdate'])
                    except (ValueError, TypeError):
                        logging.warning(f"Could not parse airdate: {info_data['airdate']}")
                if 'duration' in info_data and info_data['duration']:
                    # Convert duration from HH:MM:SS to seconds
                    try:
                        duration_parts = info_data['duration'].split(':')
                        if len(duration_parts) == 3:
                            hours, minutes, seconds = map(int, duration_parts)
                            total_seconds = hours * 3600 + minutes * 60 + seconds
                            db_episode.actual_duration = total_seconds
                    except (ValueError, IndexError):
                        logging.warning(f"Could not parse duration: {info_data['duration']}")
                
                db.commit()
                logging.info(f"Updated database record for episode {episode_number}")
            else:
                logging.info(f"No database record found for episode {episode_number}")
                
        except (ValueError, TypeError) as e:
            logging.warning(f"Could not update database for episode {episode_number}: {e}")
        except Exception as db_error:
            logging.error(f"Database update failed for episode {episode_number}: {db_error}")
            db.rollback()
            # Don't fail the entire request if database update fails
        
        return {
            "message": f"Episode {episode_number} info updated successfully",
            "episode_number": episode_number,
            "info": info_data
        }
        
    except Exception as e:
        logging.error(f"Failed to update episode info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update episode info: {str(e)}")
    finally:
        db.close()

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
            guests=item_data.get('guests'),
            resources=item_data.get('resources'),
            created_at=creation_timestamp,
            updated_at=creation_timestamp
        )
        db.add(db_item)
        db.commit()
        logger.info(f"Created database record for rundown item: {asset_id}")

        # OPTIONAL: Create filesystem file for compatibility (secondary)
        try:
            episode_dir = EPISODES_ROOT / episode_number
            if episode_dir.exists():
                rundown_dir = episode_dir / "rundown"
                rundown_dir.mkdir(exist_ok=True)

                # Generate filename
                clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
                clean_title = re.sub(r'[-\s]+', ' ', clean_title)[:30]
                filename = f"{item_index:03d} {clean_title}.md"

                # Create markdown file from database record
                markdown_content = f"""---
asset_id: {asset_id}
slug: {slug}
type: {item_type}
title: {title}
subtitle: {item_data.get('subtitle', '')}
description: {item_data.get('description', '')}
duration: {item_data.get('duration', '00:00:00')}
status: draft
order: {item_index}
guests: {item_data.get('guests', '')}
resources: {item_data.get('resources', '')}
created_at: "{creation_timestamp.isoformat()}"
---
## Notes

## Description

## Script
"""

                file_path = rundown_dir / filename
                with open(file_path, 'w') as f:
                    f.write(markdown_content)
                logger.info(f"Created filesystem file: {filename}")
        except Exception as file_error:
            logger.warning(f"Database record created but filesystem file failed: {file_error}")
            # Don't fail the request - database is source of truth

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

            # Calculate content lengths (strip HTML tags)
            import re
            new_content_length = len(re.sub(r'<[^>]+>', '', new_script or '').strip())
            existing_content_length = len(re.sub(r'<[^>]+>', '', existing_script).strip())

            # 🛡️ PROTECTION: Prevent destructive saves
            if existing_content_length > 50 and new_content_length < 30:
                logger.error(f"🚨 BLOCKED DESTRUCTIVE SAVE for {item_id}!")
                logger.error(f"   Existing: {existing_content_length} chars, New: {new_content_length} chars")
                raise HTTPException(
                    status_code=400,
                    detail=f"Blocked destructive save: would delete {existing_content_length} characters"
                )

            item.script_content = new_script
            logger.info(f"Updated script_content: {existing_content_length} -> {new_content_length} chars")

            # 📸 Create version snapshot
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


@router.post("/{episode_number}/rundown/{item_filename}/autosave")
async def autosave_rundown_item(
    episode_number: str,
    item_filename: str,
    content_data: dict,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Autosave rundown item content to autosave directory"""
    try:
        episode_path = EPISODES_ROOT / episode_number
        autosave_dir = episode_path / "rundown" / "autosave"
        
        # Create autosave directory if it doesn't exist
        if not autosave_dir.exists():
            autosave_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created autosave directory: {autosave_dir}")
        
        # Generate autosave filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = item_filename.replace('.md', '')
        autosave_filename = f"{base_name}_autosave_{timestamp}.md"
        autosave_path = autosave_dir / autosave_filename
        
        # Write autosave content
        with open(autosave_path, 'w', encoding='utf-8') as f:
            f.write(content_data.get('content', ''))
        
        return {
            "success": True,
            "message": f"Autosaved {item_filename}",
            "autosave_path": str(autosave_path),
            "timestamp": timestamp
        }
        
    except Exception as e:
        logging.error(f"Autosave failed for {episode_number}/{item_filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Autosave failed: {str(e)}"
        )

@router.put("/{episode_number}/rundown/{item_filename}/autosave")
async def update_autosave_current(
    episode_number: str, 
    item_filename: str,
    content_data: dict,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Update current autosave version (overwrites existing autosave)"""
    try:
        episode_path = EPISODES_ROOT / episode_number
        autosave_dir = episode_path / "rundown" / "autosave"
        
        # Create autosave directory if it doesn't exist
        if not autosave_dir.exists():
            autosave_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created autosave directory: {autosave_dir}")
        
        # Use simple autosave filename (current version)
        base_name = item_filename.replace('.md', '')
        autosave_filename = f"{base_name}_autosave.md"
        autosave_path = autosave_dir / autosave_filename
        
        # Write autosave content (overwrite if exists)
        with open(autosave_path, 'w', encoding='utf-8') as f:
            f.write(content_data.get('content', ''))
        
        return {
            "success": True,
            "message": f"Autosave updated for {item_filename}",
            "autosave_path": str(autosave_path)
        }
        
    except Exception as e:
        logging.error(f"Autosave update failed for {episode_number}/{item_filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Autosave update failed: {str(e)}"
        )

@router.put("/{episode_number}/items/{item_id}")
async def save_rundown_item_by_id(
    episode_number: str,
    item_id: str,
    payload: Dict[str, Any],
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Save rundown item using item ID - matches frontend expectation"""
    try:
        # Find the item by AssetID (which is the item_id from frontend)
        episode_dir = Path(f"/home/episodes/{episode_number}")
        if not episode_dir.exists():
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")
        
        rundown_dir = episode_dir / "rundown"
        if not rundown_dir.exists():
            raise HTTPException(status_code=404, detail=f"Rundown directory not found for episode {episode_number}")
        
        # Find the markdown file with matching AssetID
        target_file = None
        for md_file in rundown_dir.glob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                        file_asset_id = frontmatter.get('AssetID') or frontmatter.get('asset_id', '')
                        
                        if file_asset_id == item_id:
                            target_file = md_file
                            break
                            
            except Exception as e:
                logger.warning(f"Could not read file {md_file}: {e}")
                continue
        
        if not target_file:
            raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
        
        # Now call the existing save function with the found filename
        return await save_rundown_item(
            episode_number=episode_number,
            item_filename=target_file.name,
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


@router.put("/{episode_number}/save-episode")
async def save_episode_metadata(
    episode_number: str,
    episode_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Database-first episode metadata save - replaces filesystem approach"""
    from models_v2 import Episode

    try:
        # Convert episode number to int
        episode_num_int = int(episode_number)

        # Get episode from database
        episode = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        # Update episode fields
        for field, value in episode_data.items():
            if hasattr(episode, field) and value is not None:
                if field in ['air_date', 'publish_date']:
                    # Handle date fields - convert empty strings to None
                    if value == '' or value is None:
                        setattr(episode, field, None)
                    else:
                        from datetime import datetime
                        setattr(episode, field, datetime.fromisoformat(value) if isinstance(value, str) else value)
                else:
                    setattr(episode, field, value)

        # Always update the updated_at timestamp
        from datetime import datetime
        episode.updated_at = datetime.now()

        db.commit()
        db.refresh(episode)

        logger.info(f"Episode {episode_number} metadata saved to database")
        return {"status": "success", "message": f"Episode {episode_number} metadata saved"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode number format")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving episode metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save episode metadata: {str(e)}")

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

                    # 🔥 CRITICAL: Only update script_content if explicitly provided
                    # Frontend sends script only for currently edited item
                    if 'script' in item_data:
                        new_script = item_data['script']
                        existing_script = rundown_item.script_content or ''

                        # 🛡️ CRITICAL FIX: Strip frontmatter from script_content
                        # script_content should NEVER contain YAML frontmatter - only the body
                        # Frontmatter is stored in separate database fields (title, type, status, etc.)
                        import re
                        if new_script and new_script.strip().startswith('---'):
                            logger.warning(f"🚨 STRIPPING FRONTMATTER from script_content for {asset_id}")
                            logger.warning(f"   Original content preview: {new_script[:200]}...")

                            # Find the closing --- and extract only the body
                            lines = new_script.split('\n')
                            dash_count = 0
                            body_start_index = 0

                            for i, line in enumerate(lines):
                                if line.strip() == '---':
                                    dash_count += 1
                                    if dash_count == 2:
                                        body_start_index = i + 1
                                        break

                            if dash_count >= 2:
                                # Take content after the closing frontmatter
                                body_content = '\n'.join(lines[body_start_index:]).strip()

                                # ADDITIONAL CHECK: If body still contains another frontmatter block,
                                # this is duplicated content - strip it again
                                while body_content.strip().startswith('---'):
                                    logger.warning(f"🚨 DOUBLE FRONTMATTER DETECTED! Stripping again...")
                                    body_lines = body_content.split('\n')
                                    inner_dash_count = 0
                                    inner_body_start = 0

                                    for j, bline in enumerate(body_lines):
                                        if bline.strip() == '---':
                                            inner_dash_count += 1
                                            if inner_dash_count == 2:
                                                inner_body_start = j + 1
                                                break

                                    if inner_dash_count >= 2:
                                        body_content = '\n'.join(body_lines[inner_body_start:]).strip()
                                    else:
                                        break  # No more complete frontmatter blocks

                                new_script = body_content
                                logger.warning(f"✅ Stripped frontmatter, body length: {len(new_script)} chars")
                            else:
                                logger.warning(f"⚠️ Found opening --- but no closing ---, keeping original")

                        # Calculate content lengths (strip HTML tags for accurate word count)
                        new_content_length = len(re.sub(r'<[^>]+>', '', new_script or '').strip())
                        existing_content_length = len(re.sub(r'<[^>]+>', '', existing_script).strip())

                        # 🛡️ PROTECTION: Prevent destructive saves
                        # If existing content has >50 characters and new content is nearly empty (< 30 chars)
                        if existing_content_length > 50 and new_content_length < 30:
                            logger.error(f"🚨 BLOCKED DESTRUCTIVE SAVE for {asset_id}!")
                            logger.error(f"   Existing content: {existing_content_length} chars")
                            logger.error(f"   New content: {new_content_length} chars ({new_script[:100]})")
                            logger.error(f"   This would delete {existing_content_length} characters!")
                            logger.error(f"   Save operation BLOCKED to prevent data loss")
                            # Skip this update but don't fail the whole operation
                            continue

                        logger.info(f"💾 Saving script content for {asset_id}: {new_script[:100] if new_script else 'EMPTY'}")
                        logger.info(f"   Content length: {existing_content_length} -> {new_content_length} chars")
                        rundown_item.script_content = new_script

                        # 📸 Create version snapshot after successful save
                        try:
                            username = current_user.get('username') if isinstance(current_user, dict) else None
                            create_content_version(db, rundown_item, change_type="manual_save", username=username)
                        except Exception as e:
                            logger.error(f"Failed to create content version for {asset_id}: {e}")
                    else:
                        logger.info(f"⚠️ No 'script' key in item_data for {asset_id}, not updating script_content")

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

        db.commit()

        logger.info(f"Saved {saved_count} rundown items for episode {episode_number} with order synchronization")
        return {
            "status": "success",
            "message": f"Saved {saved_count} rundown items with order synchronization",
            "items_saved": saved_count
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
                from models_v2 import RundownItem, Segment

                # Find and delete the rundown item by AssetID
                db_item = db.query(RundownItem).filter(RundownItem.asset_id == str(asset_id)).first()
                if db_item:
                    db.delete(db_item)
                    logger.info(f"Deleted database rundown item for AssetID: {asset_id}")

                # Also try to delete segment record
                segment = db.query(Segment).filter(Segment.asset_id == str(asset_id)).first()
                if segment:
                    db.delete(segment)
                    logger.info(f"Deleted database segment for AssetID: {asset_id}")

                db.commit()
                logger.info(f"Successfully deleted database entries for AssetID: {asset_id}")

        except Exception as e:
            logger.warning(f"Could not delete from database: {str(e)}")
            db.rollback()
            # Continue even if database deletion fails - file deletion is more important
        
        return {"status": "success", "message": "Rundown item deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting rundown item: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete rundown item: {str(e)}")


# ============================================================================
# CONTENT VERSIONING ENDPOINTS
# ============================================================================

@router.get("/rundown-item/{asset_id}/versions")
async def get_content_versions(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Get version history for a rundown item."""
    from models_v2 import RundownItem, ContentVersion

    # Find the rundown item
    item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Rundown item {asset_id} not found")

    # Get all versions
    versions = db.query(ContentVersion).filter(
        ContentVersion.rundown_item_id == item.id
    ).order_by(ContentVersion.version_number.desc()).all()

    return {
        "asset_id": asset_id,
        "total_versions": len(versions),
        "versions": [
            {
                "id": v.id,
                "version_number": v.version_number,
                "content_length": v.content_length,
                "change_type": v.change_type,
                "change_summary": v.change_summary,
                "created_by": v.created_by,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "content_hash": v.content_hash
            }
            for v in versions
        ]
    }


@router.get("/rundown-item/{asset_id}/versions/{version_number}")
async def get_content_version_detail(
    asset_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Get full content of a specific version."""
    from models_v2 import RundownItem, ContentVersion

    # Find the rundown item
    item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Rundown item {asset_id} not found")

    # Get specific version
    version = db.query(ContentVersion).filter(
        ContentVersion.rundown_item_id == item.id,
        ContentVersion.version_number == version_number
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail=f"Version {version_number} not found")

    return {
        "id": version.id,
        "asset_id": asset_id,
        "version_number": version.version_number,
        "script_content": version.script_content,
        "content_length": version.content_length,
        "content_hash": version.content_hash,
        "change_type": version.change_type,
        "change_summary": version.change_summary,
        "created_by": version.created_by,
        "created_at": version.created_at.isoformat() if version.created_at else None
    }


@router.post("/rundown-item/{asset_id}/versions/{version_number}/restore")
async def restore_content_version(
    asset_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Restore a rundown item to a previous version."""
    from models_v2 import RundownItem, ContentVersion
    from datetime import datetime

    # Find the rundown item
    item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Rundown item {asset_id} not found")

    # Get version to restore
    version = db.query(ContentVersion).filter(
        ContentVersion.rundown_item_id == item.id,
        ContentVersion.version_number == version_number
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail=f"Version {version_number} not found")

    # Create a new version of the current content before restoring (safety snapshot)
    create_content_version(db, item, change_type="pre_restore", username=current_user.get('username') if isinstance(current_user, dict) else None)

    # Restore the old content
    item.script_content = version.script_content
    item.updated_at = datetime.now()

    # Create a version entry for the restore action
    username = current_user.get('username') if isinstance(current_user, dict) else None
    create_content_version(db, item, change_type="restore", username=username)

    db.commit()

    logger.info(f"✨ Restored {asset_id} to version {version_number} by {username}")

    return {
        "success": True,
        "message": f"Restored to version {version_number}",
        "asset_id": asset_id,
        "restored_version": version_number,
        "content_length": version.content_length
    }


@router.post("/{episode_number}/gather-media")
async def gather_media_for_show(
    episode_number: str,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Gather all media files referenced in cue blocks and copy them to media-list directory.

    Creates: {episode}/rundown/media-list/
    Copies each cue's MediaURL source file with enumerated filename.

    Returns:
        Summary of gathered files with counts
    """
    import shutil
    from models_v2 import RundownItem, Rundown, Episode
    from core.paths import ShowBuildPaths

    path_manager = ShowBuildPaths()

    try:
        print(f"📁 Starting media gather for episode {episode_number}")

        # Normalize episode number
        episode_id = episode_number.zfill(4) if len(episode_number) < 4 else episode_number

        # Get episode
        episode = db.query(Episode).filter(
            Episode.episode_number == int(episode_id)
        ).first()

        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")

        # Get rundown
        rundown = db.query(Rundown).filter(
            Rundown.episode_id == episode.id
        ).first()

        if not rundown:
            raise HTTPException(status_code=404, detail=f"No rundown found for episode {episode_id}")

        # Create media-list directory
        episode_path = path_manager.episodes_root / episode_id
        media_list_dir = episode_path / "rundown" / "media-list"
        media_list_dir.mkdir(parents=True, exist_ok=True)
        print(f"   📁 Media-list directory: {media_list_dir}")

        # Get all rundown items with script content
        items = db.query(RundownItem).filter(
            RundownItem.rundown_id == rundown.id
        ).order_by(RundownItem.order_in_rundown).all()

        # Cue block patterns
        cue_pattern = re.compile(r'<!-- Begin Cue -->([\s\S]*?)<!-- End Cue -->', re.IGNORECASE)
        mediaurl_pattern = re.compile(r'\[Mediaurl:\s*([^\]]+)\]', re.IGNORECASE)
        enumerator_pattern = re.compile(r'\[Enumerator:\s*([^\]]+)\]', re.IGNORECASE)
        slug_pattern = re.compile(r'\[Slug:\s*([^\]]+)\]', re.IGNORECASE)
        type_pattern = re.compile(r'\[Type:\s*([^\]]+)\]', re.IGNORECASE)

        copied = 0
        skipped = 0
        failed = 0
        total = 0
        gathered_files = []
        failures = []
        skipped_cues = []

        # Process each rundown item
        for item in items:
            if not item.script_content:
                continue

            # Find all cue blocks
            cue_matches = cue_pattern.findall(item.script_content)

            for cue_content in cue_matches:
                total += 1

                # Extract cue type, slug, and enumerator
                type_match_local = type_pattern.search(cue_content)
                slug_match_local = slug_pattern.search(cue_content)
                enumerator_match_local = enumerator_pattern.search(cue_content)

                cue_type_local = type_match_local.group(1).strip().upper() if type_match_local else 'UNKNOWN'
                slug_local = slug_match_local.group(1).strip() if slug_match_local else None
                enumerator_local = enumerator_match_local.group(1).strip() if enumerator_match_local else None

                # Extract MediaURL
                mediaurl_match = mediaurl_pattern.search(cue_content)
                media_url = mediaurl_match.group(1).strip() if mediaurl_match else None

                # For FSQ cues without MediaURL, construct path from enumerator + slug
                if not media_url and cue_type_local == 'FSQ' and slug_local:
                    # Normalize slug for filename
                    clean_slug = slug_local.lower().replace(' ', '-').replace('_', '-')
                    clean_slug = re.sub(r'[^\w\-]', '', clean_slug)
                    # Strip existing enum prefix from slug if present
                    enum_prefix_match = re.match(r'^(\d+)[-_](.+)$', clean_slug)
                    if enum_prefix_match:
                        clean_slug = enum_prefix_match.group(2)

                    if enumerator_local:
                        fsq_filename = f"{enumerator_local}-{clean_slug}.png"
                    else:
                        fsq_filename = f"fsq_{clean_slug}.png"
                    media_url = f"episodes/{episode_id}/assets/quotes/{fsq_filename}"
                    print(f"   🔧 FSQ path constructed: {media_url}")

                # Skip if still no media URL (non-FSQ cues without MediaURL)
                if not media_url:
                    skipped += 1
                    skipped_cues.append({
                        'type': cue_type_local,
                        'slug': slug_local
                    })
                    continue

                # Use already extracted values
                enumerator = enumerator_local
                slug = slug_local if slug_local else 'media'
                cue_type = cue_type_local

                # Convert MediaURL to actual file path
                # MediaURL formats:
                #   - /episodes/XXXX/assets/... (absolute URL path with leading /)
                #   - episodes/XXXX/assets/... (relative to episodes root, no leading /)
                #   - assets/... (relative to episode directory)
                #   - http://... (external URL - skip)
                if media_url.startswith('http'):
                    # Skip external URLs
                    print(f"   ⏭️ Skipping external URL: {media_url[:50]}...")
                    skipped += 1
                    continue
                elif media_url.startswith('/episodes/') or media_url.startswith('episodes/'):
                    # Path relative to episodes root
                    relative_path = media_url.lstrip('/').replace('episodes/', '', 1)
                    source_path = path_manager.episodes_root / relative_path
                else:
                    # Try as relative to episode directory
                    source_path = episode_path / media_url.lstrip('/')

                if not source_path.exists():
                    # Try fallback: look for file without enumeration prefix
                    # e.g., if looking for "20-bomb-mausoleum.mp4", try "bomb-mausoleum.mp4"
                    fallback_found = False
                    original_source = source_path

                    # Extract base slug without enumeration prefix
                    filename = source_path.name
                    enum_prefix_match = re.match(r'^(\d+)[-_](.+)$', filename)
                    if enum_prefix_match:
                        base_filename = enum_prefix_match.group(2)
                        fallback_path = source_path.parent / base_filename
                        if fallback_path.exists():
                            source_path = fallback_path
                            fallback_found = True
                            print(f"   🔄 Fallback found: {fallback_path.name}")

                    # Also try with fsq_ prefix for quotes
                    if not fallback_found and cue_type == 'FSQ':
                        # Try fsq_{slug}.png format
                        slug_part = re.sub(r'^\d+[-_]', '', filename)
                        slug_part = re.sub(r'\.png$', '', slug_part, flags=re.IGNORECASE)
                        fsq_fallback = source_path.parent / f"fsq_{slug_part}.png"
                        if fsq_fallback.exists():
                            source_path = fsq_fallback
                            fallback_found = True
                            print(f"   🔄 FSQ fallback found: {fsq_fallback.name}")

                    if not fallback_found:
                        print(f"   ❌ Source not found: {original_source}")
                        failed += 1
                        failures.append({
                            'type': cue_type,
                            'slug': slug,
                            'mediaUrl': media_url,
                            'expectedPath': str(original_source)
                        })
                        continue

                # Build destination filename
                # Format: {enumerator}-{type}-{slug}.{ext}
                ext = source_path.suffix
                clean_slug = re.sub(r'[^\w\-]', '', slug.lower().replace(' ', '-'))

                if enumerator:
                    dest_filename = f"{enumerator}-{cue_type}-{clean_slug}{ext}"
                else:
                    dest_filename = f"{cue_type}-{clean_slug}{ext}"

                dest_path = media_list_dir / dest_filename

                # Copy file to media-list directory
                try:
                    # Remove existing file if present
                    if dest_path.exists() or dest_path.is_symlink():
                        dest_path.unlink()

                    # Copy file (preserves metadata)
                    shutil.copy2(source_path, dest_path)

                    gathered_files.append({
                        'source': str(source_path),
                        'dest': dest_filename,
                        'type': cue_type,
                        'enumerator': enumerator
                    })
                    copied += 1
                    print(f"   ✅ Copied: {dest_filename}")

                except Exception as e:
                    print(f"   ❌ Failed to copy {dest_filename}: {e}")
                    failed += 1

        message = f"Media gather complete: {copied} copied, {skipped} skipped (no MediaURL), {failed} failed"
        print(f"   📊 {message}")

        return {
            "success": True,
            "episode_id": episode_id,
            "media_list_path": str(media_list_dir),
            "total": total,
            "copied": copied,
            "skipped": skipped,
            "failed": failed,
            "files": gathered_files,
            "failures": failures,
            "skippedCues": skipped_cues,
            "message": message
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error gathering media for episode {episode_number}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))