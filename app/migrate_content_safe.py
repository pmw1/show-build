#!/usr/bin/env python3
"""
Safe migration script that captures both YAML frontmatter AND markdown body content
with proper character encoding and database escaping
"""
import os
import sys
import re
import yaml
import json
from pathlib import Path
from datetime import datetime
sys.path.append('/mnt/process/show-build/app')

from database import SessionLocal
from models_v2 import Episode, Rundown, RundownItem
from services.asset_id import AssetIDService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_segment_file_with_content(file_path):
    """Parse segment file and extract both metadata AND markdown body content"""
    try:
        # Read file with explicit UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Handle files with YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                # Parse YAML metadata
                metadata = yaml.safe_load(parts[1]) or {}

                # Extract markdown body content (everything after second ---)
                markdown_body = parts[2].strip() if len(parts[2].strip()) > 0 else None

                return metadata, markdown_body

        # Handle files without frontmatter (pure markdown)
        return {}, content.strip() if content.strip() else None

    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error in {file_path}: {e}")
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin1') as f:
                content = f.read()
            logger.warning(f"Used latin1 encoding for {file_path}")
            return {}, content.strip() if content.strip() else None
        except Exception as e2:
            logger.error(f"Failed to read {file_path} with any encoding: {e2}")
            return {}, None

    except yaml.YAMLError as e:
        logger.error(f"YAML parse error in {file_path}: {e}")
        # Return raw content if YAML parsing fails
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {}, content.strip() if content.strip() else None
        except:
            return {}, None

    except Exception as e:
        logger.error(f"Unexpected error parsing {file_path}: {e}")
        return {}, None

def safe_string_for_db(value, default=''):
    """Safely prepare string values for database insertion"""
    if value is None:
        return "None"
    if isinstance(value, str):
        if value.strip() == '':
            return default
        # PostgreSQL TEXT field with proper parameterization handles escaping
        # Just ensure it's valid UTF-8
        try:
            value.encode('utf-8')
            return value
        except UnicodeEncodeError:
            # If encoding fails, replace problematic chars
            return value.encode('utf-8', errors='replace').decode('utf-8')
    return str(value)

def safe_duration(duration_str):
    """Clean duration format and remove frame count"""
    if not duration_str:
        return '00:05:00'

    duration_str = str(duration_str)

    # Handle HH:MM:SS:FF format (remove frame count)
    if duration_str.count(':') == 3:
        return ':'.join(duration_str.split(':')[:3])

    # Handle numeric duration (assume seconds)
    if duration_str.isdigit():
        total_seconds = int(duration_str)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return duration_str

def extract_order_from_filename(filename):
    """Extract order number from filename"""
    match = re.search(r'(\d+)', filename)
    if match:
        return int(match.group(1))
    return 0

def safe_date_parse(date_str):
    """Safely parse date string to datetime"""
    if not date_str or date_str == '':
        return None

    try:
        if isinstance(date_str, str):
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
    except:
        pass

    return None

def update_rundown_item_with_content(db, rundown_item_id, markdown_content):
    """Update existing rundown item with markdown content"""
    try:
        rundown_item = db.query(RundownItem).filter(RundownItem.id == rundown_item_id).first()
        if rundown_item:
            # Use safe string preparation and let SQLAlchemy handle parameterization
            rundown_item.description = safe_string_for_db(markdown_content, default='')
            db.flush()
            return True
    except Exception as e:
        logger.error(f"Failed to update rundown item {rundown_item_id}: {e}")
        return False
    return False

def migrate_episode_content(db, episode_number_str):
    """Migrate markdown content for all rundown items in an episode"""
    logger.info(f"\n=== Migrating Content for Episode {episode_number_str} ===")

    episode_number_int = int(episode_number_str)
    episode = db.query(Episode).filter(Episode.episode_number == episode_number_int).first()

    if not episode:
        logger.warning(f"Episode {episode_number_str} not found in database")
        return False

    # Get rundown for this episode
    rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
    if not rundown:
        logger.warning(f"No rundown found for episode {episode_number_str}")
        return False

    # Get all rundown items
    rundown_items = db.query(RundownItem).filter(RundownItem.rundown_id == rundown.id).all()
    logger.info(f"Found {len(rundown_items)} rundown items to update")

    # Process segment files from filesystem
    segments_dir = Path(f"/home/episodes/{episode_number_str}/rundown")
    if not segments_dir.exists():
        logger.warning(f"Rundown directory not found: {segments_dir}")
        return False

    segment_files = [f for f in segments_dir.glob("*.md") if f.is_file()]
    logger.info(f"Found {len(segment_files)} markdown files")

    updates_count = 0
    for segment_file in segment_files:
        try:
            # Parse file with content
            metadata, markdown_content = parse_segment_file_with_content(segment_file)

            if markdown_content:
                # Find matching rundown item by AssetID or title
                asset_id = metadata.get('AssetID') or metadata.get('asset_id')
                title = metadata.get('title') or segment_file.stem.replace('-', ' ').replace('_', ' ').title()

                matching_item = None
                if asset_id:
                    matching_item = db.query(RundownItem).filter(
                        RundownItem.rundown_id == rundown.id,
                        RundownItem.asset_id == asset_id
                    ).first()

                if not matching_item and title:
                    matching_item = db.query(RundownItem).filter(
                        RundownItem.rundown_id == rundown.id,
                        RundownItem.title == title
                    ).first()

                if matching_item:
                    if update_rundown_item_with_content(db, matching_item.id, markdown_content):
                        content_preview = markdown_content[:100].replace('\n', ' ') + "..." if len(markdown_content) > 100 else markdown_content
                        logger.info(f"  ✅ Updated {matching_item.title}: {content_preview}")
                        updates_count += 1
                    else:
                        logger.error(f"  ❌ Failed to update {matching_item.title}")
                else:
                    logger.warning(f"  ⚠️  No matching rundown item found for {segment_file.name}")
            else:
                logger.info(f"  ℹ️  No content to migrate from {segment_file.name}")

        except Exception as e:
            logger.error(f"  ❌ Error processing {segment_file.name}: {e}")
            continue

    logger.info(f"✅ Updated {updates_count} rundown items with content for episode {episode_number_str}")
    return updates_count > 0

def main():
    """Migrate markdown content for all episodes"""
    db = SessionLocal()

    try:
        # Get all episodes that need content migration
        episodes_to_migrate = ['0236', '0238', '0239', '0240']

        total_updated = 0
        for episode_number_str in episodes_to_migrate:
            try:
                if migrate_episode_content(db, episode_number_str):
                    db.commit()
                    total_updated += 1
                    logger.info(f"✅ Committed content updates for episode {episode_number_str}")
                else:
                    logger.warning(f"⚠️  No updates made for episode {episode_number_str}")

            except Exception as e:
                logger.error(f"❌ Failed to migrate episode {episode_number_str}: {e}")
                db.rollback()

        logger.info(f"\n📊 Migration Complete: {total_updated} episodes updated with content")

        # Show sample of updated content
        sample_item = db.query(RundownItem).filter(
            RundownItem.description != '',
            RundownItem.description != 'None',
            RundownItem.description.isnot(None)
        ).first()

        if sample_item:
            preview = sample_item.description[:200] + "..." if len(sample_item.description) > 200 else sample_item.description
            logger.info(f"\n📝 Sample Content Preview ({sample_item.title}):")
            logger.info(f"{preview}")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()