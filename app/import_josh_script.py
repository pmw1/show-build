#!/usr/bin/env python3
"""
Import Josh's manually created script into Show-Build database format.
Converts {TYPE/slug} cue blocks into proper rundown items.
"""

import re
import sys
from datetime import timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
from models_v2 import Episode, RundownItem
from services.asset_id import AssetIDService

def parse_script_file(filepath):
    """Parse Josh's script format and extract structure."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    # Split into blocks
    blocks = []
    current_block = None
    current_segment = None
    current_content = []

    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Detect block markers
        if line.startswith('BLOCK '):
            if current_segment and current_content:
                current_segment['content'] = '\n'.join(current_content).strip()
                blocks.append(current_segment)
            current_block = line
            current_content = []
            current_segment = {
                'type': 'segment',
                'title': line,
                'block': line,
                'content': '',
                'cues': []
            }

        # Detect PROMO markers
        elif line.startswith('PROMO-'):
            if current_segment and current_content:
                current_segment['content'] = '\n'.join(current_content).strip()
                blocks.append(current_segment)
            promo_name = line.replace('PROMO-', '').strip()
            blocks.append({
                'type': 'promo',
                'title': promo_name,
                'slug': promo_name.lower().replace(' ', '-'),
                'content': '',
                'cues': []
            })
            current_content = []
            current_segment = None

        # Detect segment titles (lines after BLOCK that look like titles)
        elif current_block and current_segment and not current_segment.get('segment_title') and line and not line.startswith('['):
            # Check if this looks like a segment title (not too long, no lowercase start)
            if len(line) < 80 and line and (line[0].isupper() or line.startswith('{')):
                if not line.startswith('{'):  # Not a cue block
                    current_segment['segment_title'] = line
                    current_segment['title'] = line

        # Detect cue blocks like {GFX/slug}, {IMG/slug}, {SOT/slug}, {FS Quote/slug}
        cue_match = re.search(r'\{([A-Z\s]+)/([^}]+)\}', line)
        if cue_match:
            cue_type = cue_match.group(1).strip()
            cue_slug = cue_match.group(2).strip()

            # Map Josh's types to Show-Build types
            type_map = {
                'GFX': 'gfx',
                'IMG': 'image',
                'SOT': 'video',
                'FS Quote': 'gfx',
                'FS quote': 'gfx'
            }

            show_build_type = type_map.get(cue_type, 'cue')

            # Create slug from the text
            slug = re.sub(r'[^a-z0-9]+', '-', cue_slug.lower()).strip('-')

            cue = {
                'type': show_build_type,
                'title': cue_slug,
                'slug': slug,
                'original_type': cue_type,
                'content': f"**{cue_type}**: {cue_slug}"
            }

            if current_segment:
                current_segment['cues'].append(cue)

        # Accumulate content
        if line and current_segment:
            current_content.append(line)

        i += 1

    # Add final segment
    if current_segment and current_content:
        current_segment['content'] = '\n'.join(current_content).strip()
        blocks.append(current_segment)

    return blocks


def import_to_database(episode_number: str, blocks: list):
    """Import parsed blocks into database as rundown items."""
    db: Session = SessionLocal()
    asset_service = AssetIDService()

    try:
        # Get episode
        episode = db.query(Episode).filter(Episode.episode_number == episode_number).first()
        if not episode:
            print(f"❌ Episode {episode_number} not found!")
            return False

        print(f"📺 Importing into Episode {episode_number}: {episode.title}")

        # Clear existing rundown items for this episode
        deleted = db.query(RundownItem).filter(RundownItem.rundown_id == episode.id).delete()
        print(f"🗑️  Cleared {deleted} existing rundown items")
        db.commit()

        order_index = 10

        for block in blocks:
            item_type = block['type']
            title = block.get('title', 'Untitled')
            slug = block.get('slug', re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-'))
            content = block.get('content', '')

            # Create main item (segment or promo)
            print(f"  📝 Creating {item_type}: {title}")

            rundown_item = RundownItem(
                rundown_id=episode.id,
                item_type=item_type,
                title=title,
                slug=slug,
                order_in_rundown=order_index,
                script_content=content,
                duration=timedelta(minutes=5) if item_type == 'segment' else timedelta(seconds=30),
                status='draft',
                asset_id=asset_service.generate(item_type)
            )

            db.add(rundown_item)
            db.flush()  # Get the ID

            order_index += 10

            # Add cues as child items
            for cue in block.get('cues', []):
                cue_order = order_index
                cue_slug = cue['slug']
                cue_title = cue['title']
                cue_type = cue['type']

                print(f"    🎬 Adding {cue['original_type']}: {cue_title}")

                cue_item = RundownItem(
                    rundown_id=episode.id,
                    segment_id=rundown_item.id,  # Link to parent segment
                    item_type=cue_type,
                    title=cue_title,
                    slug=cue_slug,
                    order_in_rundown=cue_order,
                    script_content=cue['content'],
                    duration=timedelta(seconds=10),
                    status='draft',
                    asset_id=asset_service.generate(cue_type)
                )

                db.add(cue_item)
                order_index += 10

        db.commit()
        print(f"✅ Successfully imported {len(blocks)} items into episode {episode_number}")
        return True

    except Exception as e:
        print(f"❌ Error importing: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == '__main__':
    script_file = '/mnt/sync/disaffected/episodes/0245/preshow/SCRIPT 244.txt'
    episode_num = '0245'

    if len(sys.argv) > 1:
        episode_num = sys.argv[1]
    if len(sys.argv) > 2:
        script_file = sys.argv[2]

    print(f"📖 Parsing script file: {script_file}")
    blocks = parse_script_file(script_file)

    print(f"\n📊 Found {len(blocks)} blocks:")
    for block in blocks:
        print(f"  - {block['type']}: {block['title']} ({len(block.get('cues', []))} cues)")

    print(f"\n💾 Importing into database...")
    success = import_to_database(episode_num, blocks)

    sys.exit(0 if success else 1)
