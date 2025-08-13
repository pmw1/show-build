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
import yaml
from datetime import datetime
from auth.utils import get_current_user_or_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/episodes", tags=["episodes"])

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

@router.get("")
async def list_episodes() -> Dict[str, Any]:
    """List all episodes."""
    episodes = []
    
    if not EPISODES_ROOT.exists():
        return {"episodes": []}
    
    # Iterate through episode directories
    for episode_dir in sorted(EPISODES_ROOT.iterdir()):
        if not episode_dir.is_dir():
            continue
        
        # Skip non-numeric directories
        if not episode_dir.name.isdigit():
            continue
            
        info_file = episode_dir / "info.md"
        if info_file.exists():
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        metadata = yaml.safe_load(parts[1])
                        episodes.append({
                            "id": episode_dir.name,
                            "episode_number": episode_dir.name,
                            "title": metadata.get('title', 'Untitled'),
                            "subtitle": metadata.get('subtitle', ''),
                            "airdate": metadata.get('airdate'),
                            "status": metadata.get('status', 'draft'),
                            "duration": metadata.get('duration', '01:00:00'),
                            "description": metadata.get('description', ''),
                            "guest": metadata.get('guest')
                        })
            except Exception as e:
                logger.warning(f"Could not parse episode {episode_dir.name}: {e}")
                # Add basic info even if parsing fails
                episodes.append({
                    "id": episode_dir.name,
                    "episode_number": episode_dir.name,
                    "title": f"Episode {episode_dir.name}",
                    "status": "unknown"
                })
    
    return {"episodes": episodes}

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
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Create a new episode with full directory structure and metadata"""
    
    # Validate episode number format
    if not episode_number.isdigit() or len(episode_number) != 4:
        raise HTTPException(status_code=400, detail="Episode number must be 4 digits")
    
    # Check if episode already exists
    episode_dir = EPISODES_ROOT / episode_number
    if episode_dir.exists():
        raise HTTPException(status_code=409, detail=f"Episode {episode_number} already exists")
    
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
        
        return {
            "success": True,
            "message": f"Episode {episode_number} created successfully",
            "episode_number": episode_number,
            "path": str(episode_dir),
            "info_file": str(info_path),
            "metadata": metadata.dict(exclude_none=True)
        }
        
    except Exception as e:
        logger.error(f"Failed to create episode {episode_number}: {e}")
        # Clean up if partial creation occurred
        if episode_dir.exists():
            import shutil
            shutil.rmtree(episode_dir)
        raise HTTPException(status_code=500, detail=f"Failed to create episode: {str(e)}")

@router.delete("/{episode_number}")
async def delete_episode(
    episode_number: str,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Delete an episode and all its content"""
    
    episode_dir = EPISODES_ROOT / episode_number
    
    if not episode_dir.exists():
        raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")
    
    try:
        # Create a backup first (optional - could move to trash instead)
        import shutil
        from datetime import datetime
        
        backup_dir = EPISODES_ROOT / ".trash" / f"{episode_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.parent.mkdir(exist_ok=True)
        shutil.move(str(episode_dir), str(backup_dir))
        
        logger.info(f"Deleted episode {episode_number} (moved to {backup_dir})")
        
        return {
            "success": True,
            "message": f"Episode {episode_number} deleted successfully",
            "backup_path": str(backup_dir)
        }
        
    except Exception as e:
        logger.error(f"Failed to delete episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete episode: {str(e)}")

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
    current_user: Optional[dict] = None
) -> Dict[str, Any]:
    """Get the next available episode number"""
    
    if not EPISODES_ROOT.exists():
        return {"next_number": "0001"}
    
    existing_episodes = []
    for item in EPISODES_ROOT.iterdir():
        if item.is_dir() and item.name.isdigit():
            existing_episodes.append(int(item.name))
    
    if not existing_episodes:
        next_number = 1
    else:
        next_number = max(existing_episodes) + 1
    
    return {
        "next_number": str(next_number).zfill(4),
        "existing_count": len(existing_episodes)
    }

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
async def get_episode_info(episode_number: str) -> Dict[str, Any]:
    """Get episode metadata from info.md file."""
    episode_dir = EPISODES_ROOT / episode_number
    info_file = episode_dir / "info.md"
    
    if not info_file.exists():
        raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")
    
    try:
        with open(info_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1])
                return {"info": metadata}
        
        return {"info": {}}
    except Exception as e:
        logger.error(f"Error reading episode info: {e}")
        raise HTTPException(status_code=500, detail="Error reading episode info")

@router.get("/{episode_number}/rundown")
async def get_episode_rundown(episode_number: str) -> Dict[str, Any]:
    """Get all rundown items for an episode."""
    episode_dir = EPISODES_ROOT / episode_number
    rundown_dir = episode_dir / "rundown"
    
    if not rundown_dir.exists():
        raise HTTPException(status_code=404, detail=f"Rundown not found for episode {episode_number}")
    
    rundown_items = []
    for file_path in sorted(rundown_dir.glob("*.md")):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter and content
            parts = content.split('---', 2)
            if len(parts) >= 3:
                front_matter = yaml.safe_load(parts[1])
                script_content = parts[2].strip()
            else:
                continue
            
            # Get order value and ensure it's an integer
            order_value = front_matter.get('order', 0)
            if isinstance(order_value, str):
                try:
                    order_value = int(order_value)
                except (ValueError, TypeError):
                    order_value = 0
            elif not isinstance(order_value, int):
                order_value = 0
            
            # Create rundown item
            item = {
                "id": front_matter.get('id', file_path.stem),
                "type": front_matter.get('type', 'segment'),
                "slug": front_matter.get('slug', ''),
                "duration": front_matter.get('duration', '00:00:00'),
                "script": script_content,
                "order": order_value,  # Use the converted integer value
                "status": front_matter.get('status', 'draft'),
                "title": front_matter.get('title', file_path.stem),
                "subtitle": front_matter.get('subtitle', ''),
                "description": front_matter.get('description', ''),
                "filename": file_path.name,  # Add the filename
                **{k: v for k, v in front_matter.items() if k not in ['id', 'type', 'slug', 'duration', 'script', 'order', 'status', 'title', 'subtitle', 'description', 'filename']}
            }
            rundown_items.append(item)
        except Exception as e:
            logger.warning(f"Could not process rundown file {file_path}: {e}")
            continue
    
    # Sort by order field (handle both string and int values)
    def get_order_value(item):
        order = item.get('order', 999)
        # Convert string to int if needed
        if isinstance(order, str):
            try:
                return int(order)
            except (ValueError, TypeError):
                return 999
        return order if isinstance(order, int) else 999
    
    rundown_items.sort(key=get_order_value)
    
    return {"items": rundown_items}

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