"""
Shared helpers, models, and constants for the episodes router package.
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

# Content versioning configuration
MAX_VERSIONS_PER_ITEM = 20  # Keep last 20 versions per rundown item

# Base path for episodes - use Docker mount path which maps to host /mnt/sync/disaffected/episodes
EPISODES_ROOT = Path("/home/episodes")
EPISODE_ROOT = EPISODES_ROOT  # Alias for compatibility


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

    # Content length = raw character count of script_content as stored.
    # Previously this stripped HTML tags before counting (intent: "human text
    # only"), which made the column disagree with LENGTH(script_content) and
    # repeatedly looked like data loss during debugging
    # (2026-05-10 incident: row showed content_length=156399 while
    # LENGTH(script_content)=158144 — same row). Use raw length now; if any
    # caller still wants text-only count for shrink guards, they compute it
    # themselves at the call site.
    content_length = len(content) if content else 0

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

    # Content rating
    explicit: bool = Field(False, description="Explicit content flag")
    content_warnings: Optional[str] = Field(None, description="Content warnings")

    # Production crew
    recording_date: Optional[str] = Field(None, description="Recording date")
    producer: Optional[str] = Field(None, description="Producer names")
    editor: Optional[str] = Field(None, description="Editor names")

    # Master publishing control
    publish_status: str = Field("draft", description="Overall publish status: draft, scheduled, published, unpublished")
    schedule_datetime: Optional[str] = Field(None, description="Master scheduled publish datetime")
    visibility: str = Field("public", description="Master visibility: public, unlisted, private")

    # OmnyStudio (podcast distribution)
    omny_description: Optional[str] = Field(None, description="Override description for podcast (NULL = use master)")
    omny_visibility: Optional[str] = Field("public", description="OmnyStudio visibility override")
    omny_publish_status: Optional[str] = Field("draft", description="OmnyStudio publish status")
    omny_schedule_datetime: Optional[str] = Field(None, description="OmnyStudio schedule override (NULL = use master)")

    # YouTube
    yt_title: Optional[str] = Field(None, description="YouTube title override (NULL = use episode title)")
    yt_description: Optional[str] = Field(None, description="YouTube description override (NULL = use master)")
    yt_tags: Optional[str] = Field(None, description="YouTube-specific tags (comma-separated)")
    yt_privacy_status: Optional[str] = Field("private", description="YouTube privacy: public, unlisted, private")
    yt_schedule_datetime: Optional[str] = Field(None, description="YouTube schedule override (NULL = use master)")

    # Social media promotion
    social_hashtags: Optional[str] = Field(None, description="Hashtags shared across platforms")
    twitter_post_text: Optional[str] = Field(None, description="Pre-composed tweet/thread text")
    twitter_schedule_datetime: Optional[str] = Field(None, description="Twitter schedule override (NULL = use master)")
    instagram_caption: Optional[str] = Field(None, description="Instagram post/reel caption")
    instagram_schedule_datetime: Optional[str] = Field(None, description="Instagram schedule override (NULL = use master)")
    facebook_post_text: Optional[str] = Field(None, description="Facebook post text")
    facebook_schedule_datetime: Optional[str] = Field(None, description="Facebook schedule override (NULL = use master)")
    tiktok_caption: Optional[str] = Field(None, description="TikTok video caption")
    tiktok_schedule_datetime: Optional[str] = Field(None, description="TikTok schedule override (NULL = use master)")

    # Internal
    notes: Optional[str] = Field(None, description="Internal production notes")


class ReorderRequest(BaseModel):
    """Request model for reordering rundown segments"""
    segments: List[Dict[str, Any]] = Field(..., description="List of segments with filename and new order")


class ConvertThumbnailRequest(BaseModel):
    """Request body for converting a thumbnail to PNG."""
    url: str = Field(..., description="The URL path of the non-PNG thumbnail (e.g., /episodes/0257/thumbnails/poster16x9.jpg)")


class TakeThumbnailRequest(BaseModel):
    """Request body for taking/confirming a thumbnail."""
    source_url: str = Field(..., description="The URL path of the thumbnail to take (e.g., /episodes/0257/exports/poster16x9.jpg)")


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
        episode_dir / "captures" / "orig",
        episode_dir / "captures" / "preview",
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
