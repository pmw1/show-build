#!/usr/bin/env python3
"""
Mirror all remaining episodes and rundown data to database
"""
import os
import sys
import re
import yaml
from pathlib import Path
from datetime import datetime
sys.path.append('/mnt/process/show-build/app')

from database import SessionLocal
from models_v2 import Episode, Rundown, RundownItem
from services.asset_id import AssetIDService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_info_md(episode_dir):
    """Parse episode info.md file"""
    info_file = episode_dir / "info.md"
    if not info_file.exists():
        return {}

    try:
        with open(info_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1]) or {}
                return metadata
    except Exception as e:
        logger.warning(f"Could not parse info.md for {episode_dir}: {e}")

    return {}

def parse_segment_file(file_path):
    """Parse a segment markdown file and extract metadata"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1]) or {}
                return metadata
    except Exception as e:
        logger.warning(f"Could not parse {file_path}: {e}")

    return {}

def extract_order_from_filename(filename):
    """Extract order number from filename like '010-coldopen-show-intro.md'"""
    match = re.match(r'^(\d+)-', filename)
    if match:
        return int(match.group(1))
    return 0

def safe_date_parse(date_str):
    """Safely parse date string to datetime"""
    if not date_str or date_str == '':
        return None

    try:
        if isinstance(date_str, str):
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
    except:
        pass

    return None

def clean_duration(duration_str):
    """Clean duration format (convert 00:00:00:00 to 00:00:00)"""
    if not duration_str:
        return '00:05:00'

    if isinstance(duration_str, str) and duration_str.count(':') == 3:
        # Convert 00:00:00:00 to 00:00:00 (remove frames)
        return ':'.join(duration_str.split(':')[:3])

    return str(duration_str)

def mirror_episode(db, episode_number_str):
    """Mirror a single episode to database"""

    episode_number_int = int(episode_number_str)

    # Check if episode already exists
    existing = db.query(Episode).filter(Episode.episode_number == episode_number_int).first()
    if existing:
        logger.info(f"Episode {episode_number_str} already exists in database")
        return existing

    # Parse episode metadata
    episode_dir = Path(f"/home/episodes/{episode_number_str}")
    if not episode_dir.exists():
        logger.warning(f"Episode directory not found: {episode_dir}")
        return None

    metadata = parse_info_md(episode_dir)

    # Generate AssetID
    asset_id = metadata.get('asset_id') or metadata.get('id')
    if not asset_id:
        asset_id = AssetIDService.request_asset_id(
            db=db,
            entity_type="episode",
            reason="filesystem_mirror",
            requested_by="mirror_all_script",
            context={
                "episode_number": episode_number_str,
                "title": metadata.get('title', f'Episode {episode_number_str}'),
                "source": "filesystem_migration"
            }
        )

    # Create episode record
    episode = Episode(
        asset_id=asset_id,
        season_id=1,  # Default season
        episode_number=episode_number_int,
        title=metadata.get('title', f'Episode {episode_number_str}'),
        slug=metadata.get('slug', f'episode-{episode_number_str}'),
        status=metadata.get('status', 'draft'),
        air_date=safe_date_parse(metadata.get('airdate')),
        publish_date=safe_date_parse(metadata.get('airdate')),
        duration_formatted=clean_duration(metadata.get('duration')),
        guest_name=metadata.get('guest', ''),
        template_type=metadata.get('type', metadata.get('template_type', '')),
        template_name=metadata.get('template_name', ''),
        is_test_data=False
    )

    db.add(episode)
    db.flush()  # Get the ID

    logger.info(f"Created episode {episode_number_str}: {episode.title}")
    return episode

def mirror_episode_rundown(db, episode):
    """Mirror rundown data for an episode"""

    episode_number_str = f"{episode.episode_number:04d}"

    # Check if rundown already exists
    existing_rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
    if existing_rundown:
        logger.info(f"Rundown already exists for episode {episode_number_str}")
        return True

    # Create rundown record
    rundown_asset_id = AssetIDService.request_asset_id(
        db=db,
        entity_type="rundown",
        reason="segment_mirror",
        requested_by="mirror_all_script",
        context={
            "episode_number": episode_number_str,
            "episode_title": episode.title,
            "source": "filesystem_migration"
        }
    )

    rundown = Rundown(
        asset_id=rundown_asset_id,
        episode_id=episode.id,
        name="Main Rundown",
        description=f"Rundown for {episode.title}",
        order_in_episode=1,
        status="draft"
    )

    db.add(rundown)
    db.flush()

    # Scan segments directory
    segments_dir = Path(f"/home/episodes/{episode_number_str}/rundown")
    if not segments_dir.exists():
        logger.info(f"No rundown directory found for episode {episode_number_str}")
        return True

    segment_files = [f for f in segments_dir.glob("*.md") if f.is_file()]
    if not segment_files:
        logger.info(f"No segment files found for episode {episode_number_str}")
        return True

    segment_files.sort()

    segments_created = 0
    for segment_file in segment_files:
        try:
            # Parse segment metadata
            metadata = parse_segment_file(segment_file)

            # Extract or generate AssetID
            asset_id = metadata.get('AssetID') or metadata.get('asset_id')
            if not asset_id:
                asset_id = AssetIDService.request_asset_id(
                    db=db,
                    entity_type="rundown_item",
                    reason="segment_mirror",
                    requested_by="mirror_all_script",
                    context={
                        "filename": segment_file.name,
                        "episode_number": episode_number_str,
                        "title": metadata.get('title', segment_file.stem)
                    }
                )

            # Extract order
            order = metadata.get('order', extract_order_from_filename(segment_file.name))

            # Map item types
            item_type = metadata.get('type', 'segment')
            if item_type == 'coldopen':
                item_type = 'coldopen'
            elif 'break' in segment_file.name.lower() or 'promo' in segment_file.name.lower():
                item_type = 'break'
            elif item_type not in ['segment', 'advertisement', 'promo', 'interview', 'package', 'transition', 'break', 'coldopen']:
                item_type = 'segment'

            # Handle empty airdate
            airdate = metadata.get('airdate')
            if airdate == '' or airdate is None:
                airdate = None

            # Create rundown item
            rundown_item = RundownItem(
                asset_id=asset_id,
                rundown_id=rundown.id,
                item_type=item_type,
                title=metadata.get('title', segment_file.stem),
                slug=metadata.get('slug', segment_file.stem.lower().replace(' ', '-')),
                order_in_rundown=order,
                duration=clean_duration(metadata.get('duration')),
                subtitle=metadata.get('subtitle', ''),
                description=metadata.get('description', ''),
                airdate=airdate,
                guests=metadata.get('guests', ''),
                resources=metadata.get('resources', ''),
                tags=metadata.get('tags', ''),
                server_message=metadata.get('server_message', ''),
                priority=metadata.get('priority', ''),
                status=metadata.get('status', 'draft'),
                is_test_data=False
            )

            db.add(rundown_item)
            segments_created += 1

        except Exception as e:
            logger.error(f"Failed to process segment {segment_file.name}: {e}")
            continue

    if segments_created > 0:
        logger.info(f"Created rundown with {segments_created} items for episode {episode_number_str}")

    return True

def main():
    """Mirror all remaining episodes and rundown data"""
    db = SessionLocal()

    try:
        # Get list of filesystem episodes
        episodes_dir = Path("/home/episodes")
        filesystem_episodes = []

        for episode_dir in episodes_dir.iterdir():
            if episode_dir.is_dir() and episode_dir.name.isdigit() and len(episode_dir.name) == 4:
                filesystem_episodes.append(episode_dir.name)

        filesystem_episodes.sort()
        logger.info(f"Found {len(filesystem_episodes)} episodes in filesystem: {filesystem_episodes}")

        # Get list of database episodes
        db_episodes = db.query(Episode).all()
        db_episode_numbers = {f"{ep.episode_number:04d}" for ep in db_episodes}
        logger.info(f"Found {len(db_episodes)} episodes in database: {sorted(db_episode_numbers)}")

        total_episodes = 0
        total_rundowns = 0

        # Process all filesystem episodes
        for episode_number_str in filesystem_episodes:
            logger.info(f"\n=== Processing Episode {episode_number_str} ===")

            # Mirror episode if not exists
            episode = mirror_episode(db, episode_number_str)
            if episode:
                total_episodes += 1

                # Mirror rundown data
                if mirror_episode_rundown(db, episode):
                    total_rundowns += 1

        # Commit all changes
        db.commit()
        logger.info(f"\n✅ Successfully mirrored {total_episodes} episodes and {total_rundowns} rundowns!")

        # Show final status
        final_db_episodes = db.query(Episode).count()
        final_rundowns = db.query(Rundown).count()
        final_items = db.query(RundownItem).count()

        logger.info(f"\n📊 Final Database Status:")
        logger.info(f"  Episodes: {final_db_episodes}")
        logger.info(f"  Rundowns: {final_rundowns}")
        logger.info(f"  Rundown Items: {final_items}")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to mirror episodes: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()