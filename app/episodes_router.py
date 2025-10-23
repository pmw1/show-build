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
            item.script_content = item_data['script_content']
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
                        logger.info(f"💾 Saving script content for {asset_id}: {item_data['script'][:100] if item_data['script'] else 'EMPTY'}")
                        rundown_item.script_content = item_data['script']
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