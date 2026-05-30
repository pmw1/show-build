#!/usr/bin/env python3
"""
Import Episode 0241 from filesystem to database
"""
import sys
import yaml
from pathlib import Path
from datetime import datetime

# Add app directory to path
sys.path.insert(0, '/app')

from database import SessionLocal
from models_v2 import Episode, Rundown, RundownItem

def parse_frontmatter(file_path):
    """Parse YAML frontmatter from markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_text = parts[1].strip()
    body_content = parts[2]

    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        frontmatter = {}

    return frontmatter, body_content

def import_episode_0241():
    """Import episode 0241 from filesystem to database."""
    db = SessionLocal()

    try:
        # Check if episode already exists
        existing_episode = db.query(Episode).filter(Episode.episode_number == 241).first()
        if existing_episode:
            print("Episode 0241 already exists in database. Deleting first...")
            # Delete existing rundown items and rundown
            existing_rundowns = db.query(Rundown).filter(Rundown.episode_id == existing_episode.id).all()
            for rundown in existing_rundowns:
                db.query(RundownItem).filter(RundownItem.rundown_id == rundown.id).delete()
                db.delete(rundown)
            db.delete(existing_episode)
            db.commit()
            print("Existing episode 0241 deleted.")

        # Parse episode info.md
        episode_dir = Path("/home/episodes/0241")
        info_path = episode_dir / "info.md"

        if not info_path.exists():
            print(f"Error: {info_path} not found")
            return False

        episode_data, _ = parse_frontmatter(info_path)

        # Create episode - need to check Episode model structure
        episode = Episode(
            episode_number=241,
            title=episode_data.get('title', 'Manson Family Values'),
            slug="manson-family-values",
            asset_id="EP0241",
            season_id=1,  # Default season
            status=episode_data.get('status', 'draft')
        )

        db.add(episode)
        db.flush()  # Get the episode ID
        episode_id = episode.id
        print(f"Created episode 0241 with ID: {episode_id}")

        # Create a rundown for this episode
        rundown = Rundown(
            episode_id=episode_id,
            asset_id=f"RUN{episode_id}",
            name="Main Rundown",
            description="Main rundown for episode 0241"
        )
        db.add(rundown)
        db.flush()  # Get the rundown ID
        rundown_id = rundown.id
        print(f"Created rundown with ID: {rundown_id}")

        # Import rundown items
        rundown_dir = episode_dir / "rundown"
        markdown_files = sorted(rundown_dir.glob("*.md"))

        for file_path in markdown_files:
            print(f"Importing: {file_path.name}")

            item_data, content = parse_frontmatter(file_path)

            # Create rundown item
            rundown_item = RundownItem(
                rundown_id=rundown_id,
                asset_id=item_data.get('id') or item_data.get('asset_id'),
                item_type=item_data.get('type', 'segment'),
                title=item_data.get('title', file_path.stem),
                slug=item_data.get('slug', file_path.stem),
                description=item_data.get('description'),
                script_content=content.strip() if content else "",
                order_in_rundown=int(item_data.get('order', 0)),
                duration=item_data.get('duration', "00:00:00"),
                status=item_data.get('status', 'draft'),
                subtitle=item_data.get('subtitle'),
                guests=item_data.get('guests'),
                resources=item_data.get('resources'),
                tags=item_data.get('tags'),
                server_message=item_data.get('server_message'),
                airdate=item_data.get('airdate'),
                priority=item_data.get('priority'),
                metadata={
                    'filename': file_path.name,
                    'index': item_data.get('index', 0)
                }
            )

            db.add(rundown_item)
            print(f"  Added rundown item: {rundown_item.title}")

        # Commit all changes
        db.commit()
        print(f"\n✅ Successfully imported episode 0241 with {len(markdown_files)} rundown items!")
        return True

    except Exception as e:
        import traceback
        print(f"Error importing episode: {e}")
        print("Full traceback:")
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import_episode_0241()