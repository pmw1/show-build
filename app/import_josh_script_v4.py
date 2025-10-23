#!/usr/bin/env python3
"""
Import Josh's script properly - break into NAMED segments like episode 0241.

Structure:
- Cold Open (intro)
- Named segments (e.g., "Young Republicans Chat", "Whole Language")
- Promos between blocks
- CTA at end
- Cues formatted as HTML comments within script
"""

import re
import sys
import random
import string
from datetime import timedelta
from database import SessionLocal
from sqlalchemy import text

def generate_asset_id(prefix="SEG"):
    """Generate AssetID."""
    timestamp = str(int(1000000000))[-6:]
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}{timestamp}{random_suffix}"

def format_cue_as_html_comment(cue_match):
    """Convert {TYPE/slug} to HTML comment format like episode 0241."""
    cue_type = cue_match.group(1).strip()
    cue_slug = cue_match.group(2).strip()

    # Convert "FS Quote" to "FSQ"
    if cue_type.upper() in ['FS QUOTE', 'FS-QUOTE', 'FSQUOTE']:
        cue_type = 'FSQ'

    # Clean slug
    slug = re.sub(r'[^a-z0-9]+', '-', cue_slug.lower()).strip('-')

    # Generate asset ID based on type
    type_map = {'GFX': 'GFX', 'IMG': 'IMG', 'SOT': 'SOT', 'FSQ': 'FSQ'}
    asset_prefix = type_map.get(cue_type, 'CUE')
    asset_id = generate_asset_id(asset_prefix)

    # Determine media path based on type
    if cue_type == 'FSQ':
        media_path = f"../assets/graphics/{slug}.png"
    elif cue_type == 'IMG':
        media_path = f"../assets/images/{slug}.jpg"
    elif cue_type == 'SOT':
        media_path = f"../assets/video/{slug}.mp4"
    else:
        media_path = f"../assets/graphics/{slug}.png"

    # Format as HTML comment
    return f"""<!-- Begin Cue -->
[Type: {cue_type}]
[AssetID: {asset_id}]
[Slug: {slug}]
[Description: ]
[MediaURL: {media_path}]
<!-- End Cue -->"""

def parse_script_file(filepath):
    """Parse Josh's script into properly named rundown items."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    items = []
    lines = content.split('\n')

    # Read entire script to identify segments
    full_text = '\n'.join(lines)

    # Find segment markers and content
    # Pattern: Look for standalone lines that are segment titles

    # BLOCK A
    block_a_start = full_text.find('BLOCK A')
    block_a_end = full_text.find('PROMO-SLOCUM CONSULTING', block_a_start)
    block_a_content = full_text[block_a_start:block_a_end].strip()

    # Split BLOCK A into cold open and main segment
    young_republicans_start = block_a_content.find('Young Republicans Chat')

    if young_republicans_start > 0:
        # Cold open is everything before "Young Republicans Chat"
        cold_open_content = block_a_content[:young_republicans_start].strip()

        # Convert cue blocks to HTML comments (non-greedy multi-line match)
        cold_open_content = re.sub(r'\{([A-Z\s]+)/([^}]+?)\}', format_cue_as_html_comment, cold_open_content, flags=re.DOTALL)

        items.append({
            'type': 'coldopen',
            'title': 'Cold Open',
            'slug': 'cold-open',
            'content': cold_open_content
        })

        # Young Republicans segment
        young_rep_content = block_a_content[young_republicans_start:].strip()
        young_rep_content = re.sub(r'\{([A-Z\s]+)/([^}]+?)\}', format_cue_as_html_comment, young_rep_content, flags=re.DOTALL)

        items.append({
            'type': 'segment',
            'title': 'Young Republicans Chat',
            'slug': 'young-republicans-chat',
            'content': young_rep_content
        })

    # First promo
    promo1_start = full_text.find('PROMO-SLOCUM CONSULTING', block_a_end)
    items.append({
        'type': 'promo',
        'title': 'Slocum Consulting',
        'slug': 'slocum-consulting',
        'content': 'PROMO-SLOCUM CONSULTING'
    })

    # BLOCK B - Literacy segment
    block_b_start = full_text.find('BLOCK B', promo1_start)
    block_b_end = full_text.find('PROMO-SLOCUM CONSULTING', block_b_start + 10)
    block_b_content = full_text[block_b_start:block_b_end].strip()
    block_b_content = re.sub(r'\{([A-Z\s]+)/([^}]+?)\}', format_cue_as_html_comment, block_b_content, flags=re.DOTALL)

    items.append({
        'type': 'segment',
        'title': 'Literacy Crisis / Whole Language',
        'slug': 'literacy-crisis',
        'content': block_b_content
    })

    # Second promo
    items.append({
        'type': 'promo',
        'title': 'Slocum Consulting',
        'slug': 'slocum-consulting-2',
        'content': 'PROMO-SLOCUM CONSULTING'
    })

    # BLOCK C - Potpourri
    block_c_start = full_text.find('BLOCK C', block_b_end)
    block_c_end = full_text.find('PROMO-SUPPORT US', block_c_start)
    block_c_content = full_text[block_c_start:block_c_end].strip()
    block_c_content = re.sub(r'\{([A-Z\s]+)/([^}]+?)\}', format_cue_as_html_comment, block_c_content, flags=re.DOTALL)

    items.append({
        'type': 'segment',
        'title': 'Potpourri du Moquerie',
        'slug': 'potpourri-du-moquerie',
        'content': block_c_content
    })

    # Support promo
    items.append({
        'type': 'promo',
        'title': 'Support Us',
        'slug': 'support-us',
        'content': 'PROMO-SUPPORT US'
    })

    # Subscribe CTA
    subscribe_start = full_text.find('SUBSCRIBE', block_c_end)
    subscribe_content = full_text[subscribe_start:].strip()
    subscribe_content = re.sub(r'\{([A-Z\s]+)/([^}]+?)\}', format_cue_as_html_comment, subscribe_content, flags=re.DOTALL)

    items.append({
        'type': 'cta',
        'title': 'Subscribe CTA',
        'slug': 'subscribe-cta',
        'content': subscribe_content
    })

    return items

def import_to_database(episode_number: str, items: list):
    """Import rundown items with HTML-formatted cues."""
    db = SessionLocal()

    try:
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

        print(f"📺 Episode {episode_number} (Rundown ID: {rundown_id})")

        order_index = 10

        for item in items:
            item_type = item['type']
            title = item['title']
            slug = item['slug']
            content = item['content']

            # Duration estimates
            duration_map = {
                'coldopen': timedelta(seconds=45),
                'segment': timedelta(minutes=15),
                'promo': timedelta(seconds=30),
                'cta': timedelta(seconds=15)
            }
            duration = duration_map.get(item_type, timedelta(seconds=30))

            asset_id = generate_asset_id("SEG" if item_type in ['segment', 'coldopen'] else "PRO")

            print(f"  [{order_index:3}] {item_type:12} - {title}")

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
                "script_content": content,
                "duration": duration,
                "status": "draft",
                "asset_id": asset_id
            })

            order_index += 10
            db.commit()

        print(f"\n✅ Imported {len(items)} rundown items")
        print(f"📋 Cues formatted as HTML comments (like episode 0241)")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
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

    print(f"📖 Parsing: {script_file}\n")
    items = parse_script_file(script_file)

    print(f"📊 Rundown structure ({len(items)} items):")
    for i, item in enumerate(items, 1):
        cue_count = item['content'].count('<!-- Begin Cue -->')
        print(f"  {i}. {item['type']:12} - {item['title']} ({cue_count} cues)")

    print(f"\n💾 Importing...")
    import_to_database(episode_num, items)
