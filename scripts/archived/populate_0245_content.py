#!/usr/bin/env python3
"""Populate episode 0245 rundown with Josh's script content."""

import re
import sys
from database import SessionLocal
from sqlalchemy import text

def format_cue_to_html(match):
    """Convert {TYPE/slug} to HTML comment format."""
    cue_type = match.group(1).strip()
    cue_slug = match.group(2).strip()

    # Convert FS Quote to FSQ
    if 'FS' in cue_type.upper() and 'QUOTE' in cue_type.upper():
        cue_type = 'FSQ'
    elif cue_type.upper() == 'IMG':
        cue_type = 'IMG'
    elif cue_type.upper() == 'GFX':
        cue_type = 'GFX'
    elif cue_type.upper() == 'SOT':
        cue_type = 'SOT'

    # Clean slug
    slug = re.sub(r'[^a-z0-9]+', '-', cue_slug.lower()).strip('-')

    # Generate simple AssetID
    import random, string
    asset_id = cue_type + '000000' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Determine media path
    if cue_type == 'FSQ':
        media_path = f'../assets/graphics/{slug}.png'
    elif cue_type == 'IMG':
        media_path = f'../assets/images/{slug}.jpg'
    elif cue_type == 'SOT':
        media_path = f'../assets/video/{slug}.mp4'
    elif cue_type == 'GFX':
        media_path = f'../assets/graphics/{slug}.png'
    else:
        media_path = f'../assets/{slug}'

    return f'''<!-- Begin Cue -->
[Type: {cue_type}]
[AssetID: {asset_id}]
[Slug: {slug}]
[Description: ]
[MediaURL: {media_path}]
<!-- End Cue -->'''


def main():
    # Read the script
    print("📖 Reading script file...")
    with open('/home/episodes/0245/preshow/SCRIPT 244.txt', 'r', encoding='utf-8-sig') as f:
        script = f.read()

    print(f"✅ Read {len(script)} characters")

    # Find section markers
    block_a_pos = script.find('BLOCK A')
    young_rep_pos = script.find('Young Republicans Chat')
    promo1_pos = script.find('PROMO-SLOCUM CONSULTING')
    block_b_pos = script.find('BLOCK B', promo1_pos)
    promo2_pos = script.find('PROMO-SLOCUM CONSULTING', block_b_pos)
    block_c_pos = script.find('BLOCK C', promo2_pos)
    potpourri_pos = script.find('Potpourri du Moquerie')
    promo3_pos = script.find('PROMO-SUPPORT US')
    subscribe_pos = script.find('SUBSCRIBE')

    print(f"\n📍 Section positions:")
    print(f"  BLOCK A: {block_a_pos}")
    print(f"  Young Republicans: {young_rep_pos}")
    print(f"  Promo 1: {promo1_pos}")
    print(f"  BLOCK B: {block_b_pos}")
    print(f"  Promo 2: {promo2_pos}")
    print(f"  BLOCK C: {block_c_pos}")
    print(f"  Potpourri: {potpourri_pos}")
    print(f"  Promo 3: {promo3_pos}")
    print(f"  Subscribe: {subscribe_pos}")

    # Extract sections
    cold_open = script[block_a_pos:young_rep_pos].strip()
    young_rep = script[young_rep_pos:promo1_pos].strip()
    literacy = script[block_b_pos:promo2_pos].strip()
    potpourri = script[potpourri_pos:promo3_pos].strip()
    subscribe = script[subscribe_pos:].strip()

    print(f"\n📝 Extracted sections:")
    print(f"  Cold Open: {len(cold_open)} chars")
    print(f"  Young Republicans: {len(young_rep)} chars")
    print(f"  Literacy Crisis: {len(literacy)} chars")
    print(f"  Potpourri: {len(potpourri)} chars")
    print(f"  Subscribe: {len(subscribe)} chars")

    # Convert cues to HTML (fixed regex to handle all cases including "FS Quote")
    print(f"\n🔄 Converting cue blocks to HTML...")
    # Pattern matches: {TYPE/slug} where TYPE can be "FS Quote", "GFX", "IMG", etc.
    # [^/]+ captures everything up to the first / (handles "FS Quote" with space)
    cue_pattern = r'\{([^/]+)/(.*?)\}'
    cold_open = re.sub(cue_pattern, format_cue_to_html, cold_open, flags=re.DOTALL)
    young_rep = re.sub(cue_pattern, format_cue_to_html, young_rep, flags=re.DOTALL)
    literacy = re.sub(cue_pattern, format_cue_to_html, literacy, flags=re.DOTALL)
    potpourri = re.sub(cue_pattern, format_cue_to_html, potpourri, flags=re.DOTALL)
    subscribe = re.sub(cue_pattern, format_cue_to_html, subscribe, flags=re.DOTALL)

    # Count cues
    print(f"\n🎬 Cues found:")
    print(f"  Cold Open: {cold_open.count('<!-- Begin Cue -->')}")
    print(f"  Young Republicans: {young_rep.count('<!-- Begin Cue -->')}")
    print(f"  Literacy Crisis: {literacy.count('<!-- Begin Cue -->')}")
    print(f"  Potpourri: {potpourri.count('<!-- Begin Cue -->')}")
    print(f"  Subscribe: {subscribe.count('<!-- Begin Cue -->')}")

    # Update database
    print(f"\n💾 Updating database...")
    db = SessionLocal()
    try:
        # Update each segment by title (order_in_rundown has duplicates)
        db.execute(text('UPDATE rundown_items SET script_content = :content WHERE rundown_id = 27 AND title = :title'),
                   {'content': cold_open, 'title': 'Cold Open'})
        print("  ✅ Updated Cold Open")

        db.execute(text('UPDATE rundown_items SET script_content = :content WHERE rundown_id = 27 AND title = :title'),
                   {'content': young_rep, 'title': 'Young Republicans Chat'})
        print("  ✅ Updated Young Republicans Chat")

        db.execute(text('UPDATE rundown_items SET script_content = :content WHERE rundown_id = 27 AND title = :title'),
                   {'content': literacy, 'title': 'Literacy Crisis'})
        print("  ✅ Updated Literacy Crisis")

        db.execute(text('UPDATE rundown_items SET script_content = :content WHERE rundown_id = 27 AND title = :title'),
                   {'content': potpourri, 'title': 'Potpourri du Moquerie'})
        print("  ✅ Updated Potpourri du Moquerie")

        db.execute(text('UPDATE rundown_items SET script_content = :content WHERE rundown_id = 27 AND title = :title'),
                   {'content': subscribe, 'title': 'Subscribe CTA'})
        print("  ✅ Updated Subscribe CTA")

        db.commit()
        print("\n✅ All segments updated successfully!")

        # Verify
        result = db.execute(text('SELECT order_in_rundown, title, LENGTH(script_content) as len FROM rundown_items WHERE rundown_id = 27 ORDER BY order_in_rundown')).fetchall()
        print("\n📊 Verification:")
        for row in result:
            print(f"  [{row[0]:3}] {row[1]:30} {row[2]:6} chars")

        return True

    except Exception as e:
        print(f"\n❌ Database error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
