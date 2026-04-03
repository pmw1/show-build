#!/usr/bin/env python3
"""
Import Josh's manually created script into Show-Build database format.
CORRECTLY interprets rundown items vs cue blocks.

Rundown items = segments, promos, ads (database records)
Cue blocks = {GFX/...}, {IMG/...}, {SOT/...} markers WITHIN script content (not separate records)
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
    """
    Parse Josh's script and extract rundown items (NOT cues as separate items).

    Rundown items:
    - BLOCK A, B, C markers define segments
    - PROMO-X markers are promos
    - Content between markers is the segment content

    Cue blocks like {GFX/...} stay IN the script content, not extracted.
    """
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    items = []
    lines = content.split('\n')

    current_item = None
    current_content_lines = []

    for line in lines:
        stripped = line.strip()

        # Detect BLOCK markers (these start new segments)
        if stripped.startswith('BLOCK '):
            # Save previous item if exists
            if current_item:
                current_item['content'] = '\n'.join(current_content_lines).strip()
                items.append(current_item)

            # Start new segment item
            current_item = {
                'type': 'segment',
                'title': stripped,  # "BLOCK A", "BLOCK B", etc.
                'slug': stripped.lower().replace(' ', '-'),
                'content': ''
            }
            current_content_lines = [line]  # Include BLOCK marker in content

        # Detect PROMO markers (these are separate promo items)
        elif stripped.startswith('PROMO-'):
            # Save previous item
            if current_item:
                current_item['content'] = '\n'.join(current_content_lines).strip()
                items.append(current_item)

            promo_name = stripped.replace('PROMO-', '').strip()
            current_item = {
                'type': 'promo',
                'title': promo_name,
                'slug': promo_name.lower().replace(' ', '-'),
                'content': stripped  # Just the PROMO marker
            }
            current_content_lines = [line]

        # Detect SUBSCRIBE markers (CTAs)
        elif 'SUBSCRIBE' in stripped and 'NOTIFICATION' in stripped:
            # Save previous item
            if current_item:
                current_item['content'] = '\n'.join(current_content_lines).strip()
                items.append(current_item)

            current_item = {
                'type': 'cta',
                'title': 'Subscribe CTA',
                'slug': 'subscribe-cta',
                'content': stripped
            }
            current_content_lines = [line]

        else:
            # Accumulate content for current item
            if current_item:
                current_content_lines.append(line)

    # Save final item
    if current_item:
        current_item['content'] = '\n'.join(current_content_lines).strip()
        items.append(current_item)

    return items

def import_to_database(episode_number: str, items: list):
    """Import rundown items into database. Cues stay as text markers in script_content."""
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

        for item in items:
            item_type = item['type']
            title = item['title']
            slug = item['slug']
            content = item['content']

            print(f"  📝 Creating {item_type}: {title}")

            # Determine duration based on type
            if item_type == 'segment':
                duration = timedelta(minutes=15)  # Estimate for segments
            elif item_type == 'promo':
                duration = timedelta(seconds=30)
            else:
                duration = timedelta(seconds=10)

            # Insert rundown item with cues as text in script_content
            asset_id = generate_simple_asset_id("SEG" if item_type == 'segment' else "PRO")
            db.execute(text("""
                INSERT INTO rundown_items
                (rundown_id, item_type, title, slug, order_in_rundown, script_content,
                 duration, status, asset_id, created_at, updated_at)
                VALUES (:rundown_id, :item_type, :title, :slug, :order_in_rundown,
                        :script_content, :duration, :status, :asset_id, NOW(), NOW())
            """), {
                "rundown_id": rundown_id,
                "item_type": item_type,
                "title": title,
                "slug": slug,
                "order_in_rundown": order_index,
                "script_content": content,  # Includes all {GFX/...} markers as text
                "duration": duration,
                "status": "draft",
                "asset_id": asset_id
            })

            order_index += 10
            db.commit()

        print(f"✅ Successfully imported {len(items)} rundown items into episode {episode_number}")
        print(f"📋 Cue blocks like {{GFX/...}} remain as text markers in script content")
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
    items = parse_script_file(script_file)

    print(f"\n📊 Found {len(items)} rundown items:")
    for item in items:
        # Count cue blocks in content
        cue_count = len(re.findall(r'\{[A-Z\s]+/[^}]+\}', item['content']))
        print(f"  - {item['type']}: {item['title'][:50]} ({cue_count} cue blocks in script)")

    print(f"\n💾 Importing into database...")
    success = import_to_database(episode_num, items)

    sys.exit(0 if success else 1)
