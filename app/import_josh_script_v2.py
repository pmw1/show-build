#!/usr/bin/env python3
"""
Import Josh's manually created script into Show-Build database format.
Converts {TYPE/slug} cue blocks into proper rundown items.
Uses direct SQL to avoid model dependency issues.
"""

import re
import sys
import random
import string
from datetime import timedelta
from database import SessionLocal
from sqlalchemy import text

def generate_simple_asset_id(prefix="ITM"):
    """Generate a simple asset ID."""
    timestamp = str(int(1000000000))[-6:]
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}{timestamp}{random_suffix}"

def parse_script_file(filepath):
    """Parse Josh's script format and extract structure."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()

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

        # Detect segment titles
        elif current_block and current_segment and not current_segment.get('segment_title') and line and not line.startswith('['):
            if len(line) < 80 and line and (line[0].isupper() or line.startswith('{')):
                if not line.startswith('{'):
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
    """Import parsed blocks into database as rundown items using raw SQL."""
    db = SessionLocal()

    try:
        # Get episode ID and rundown ID
        result = db.execute(
            text("SELECT e.id, r.id FROM episodes e LEFT JOIN rundowns r ON r.episode_id = e.id WHERE e.episode_number = :ep"),
            {"ep": episode_number}
        ).fetchone()

        if not result:
            print(f"❌ Episode {episode_number} not found!")
            return False

        episode_id = result[0]
        rundown_id = result[1]

        if not rundown_id:
            print(f"❌ No rundown found for episode {episode_number}!")
            return False

        print(f"📺 Importing into Episode {episode_number} (Episode ID: {episode_id}, Rundown ID: {rundown_id})")

        # Clear existing rundown items
        result = db.execute(
            text("DELETE FROM rundown_items WHERE rundown_id = :id"),
            {"id": rundown_id}
        )
        deleted_count = result.rowcount
        print(f"🗑️  Cleared {deleted_count} existing rundown items")
        db.commit()

        order_index = 10

        for block in blocks:
            item_type = block['type']
            title = block.get('title', 'Untitled')
            slug = block.get('slug', re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-'))
            content = block.get('content', '')

            print(f"  📝 Creating {item_type}: {title}")

            # Insert main item
            asset_id = generate_simple_asset_id("SEG" if item_type == 'segment' else "PRO")
            result = db.execute(text("""
                INSERT INTO rundown_items
                (rundown_id, item_type, title, slug, order_in_rundown, script_content,
                 duration, status, asset_id, created_at, updated_at)
                VALUES (:rundown_id, :item_type, :title, :slug, :order_in_rundown,
                        :script_content, :duration, :status, :asset_id, NOW(), NOW())
                RETURNING id
            """), {
                "rundown_id": rundown_id,
                "item_type": item_type,
                "title": title,
                "slug": slug,
                "order_in_rundown": order_index,
                "script_content": content,
                "duration": timedelta(minutes=5) if item_type == 'segment' else timedelta(seconds=30),
                "status": "draft",
                "asset_id": asset_id
            })

            parent_id = result.fetchone()[0]
            db.commit()

            order_index += 10

            # Add cues as child items
            for cue in block.get('cues', []):
                cue_order = order_index
                cue_slug = cue['slug']
                cue_title = cue['title']
                cue_type = cue['type']

                print(f"    🎬 Adding {cue['original_type']}: {cue_title}")

                cue_asset_id = generate_simple_asset_id(cue_type.upper()[:3])
                # Note: segment_id references segments table, not rundown_items
                # For now, we'll set it to NULL and just nest by order
                db.execute(text("""
                    INSERT INTO rundown_items
                    (rundown_id, item_type, title, slug, order_in_rundown,
                     script_content, duration, status, asset_id, created_at, updated_at)
                    VALUES (:rundown_id, :item_type, :title, :slug,
                            :order_in_rundown, :script_content, :duration, :status, :asset_id, NOW(), NOW())
                """), {
                    "rundown_id": rundown_id,
                    "item_type": cue_type,
                    "title": cue_title,
                    "slug": cue_slug,
                    "order_in_rundown": cue_order,
                    "script_content": cue['content'],
                    "duration": timedelta(seconds=10),
                    "status": "draft",
                    "asset_id": cue_asset_id
                })

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
    script_file = '/home/episodes/0245/preshow/SCRIPT 244.txt'
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
