#!/usr/bin/env python3
"""
Extract all FSQ (Full Screen Quote) cues from episode 0245 script content.
Outputs a JSON file with quote metadata for PNG generation.
"""

import re
import json
import sys
from database import SessionLocal
from sqlalchemy import text


def extract_fsq_cues(script_content):
    """Extract all FSQ cue blocks from script content."""
    quotes = []

    # Pattern to match FSQ cue blocks
    # Matches: <!-- Begin Cue --> ... [Type: FSQ] ... <!-- End Cue -->
    cue_pattern = r'<!-- Begin Cue -->(.*?)<!-- End Cue -->'

    cue_matches = re.finditer(cue_pattern, script_content, re.DOTALL)

    for match in cue_matches:
        cue_block = match.group(1)

        # Check if this is an FSQ type
        type_match = re.search(r'\[Type:\s*FSQ\]', cue_block, re.IGNORECASE)
        if not type_match:
            continue

        # Extract fields
        quote_data = {
            'type': 'FSQ',
            'slug': '',
            'assetId': '',
            'quote': '',
            'attribution': '',
            'style': 'left',
            'fontFamily': 'sans-serif',
            'fontSize': '24px',
            'duration': '00:00:10:00',
            'wordCount': 0,
            'part': '1x1',
            'renderMode': 'png'
        }

        # Extract each field
        slug_match = re.search(r'\[Slug:\s*([^\]]+)\]', cue_block)
        if slug_match:
            quote_data['slug'] = slug_match.group(1).strip()

        assetid_match = re.search(r'\[Assetid:\s*([^\]]+)\]', cue_block, re.IGNORECASE)
        if assetid_match:
            quote_data['assetId'] = assetid_match.group(1).strip()

        quote_match = re.search(r'\[Quote:\s*([^\]]+)\]', cue_block)
        if quote_match:
            quote_data['quote'] = quote_match.group(1).strip()

        attribution_match = re.search(r'\[Attribution:\s*([^\]]+)\]', cue_block)
        if attribution_match:
            quote_data['attribution'] = attribution_match.group(1).strip()

        style_match = re.search(r'\[Style:\s*([^\]]+)\]', cue_block)
        if style_match:
            quote_data['style'] = style_match.group(1).strip()

        font_family_match = re.search(r'\[Fontfamily:\s*([^\]]+)\]', cue_block, re.IGNORECASE)
        if font_family_match:
            quote_data['fontFamily'] = font_family_match.group(1).strip()

        font_size_match = re.search(r'\[Fontsize:\s*([^\]]+)\]', cue_block, re.IGNORECASE)
        if font_size_match:
            quote_data['fontSize'] = font_size_match.group(1).strip()

        duration_match = re.search(r'\[Duration:\s*([^\]]+)\]', cue_block)
        if duration_match:
            quote_data['duration'] = duration_match.group(1).strip()

        wordcount_match = re.search(r'\[Wordcount:\s*([^\]]+)\]', cue_block, re.IGNORECASE)
        if wordcount_match:
            quote_data['wordCount'] = int(wordcount_match.group(1).strip())

        part_match = re.search(r'\[Part:\s*([^\]]+)\]', cue_block)
        if part_match:
            quote_data['part'] = part_match.group(1).strip()

        rendermode_match = re.search(r'\[Rendermode:\s*([^\]]+)\]', cue_block, re.IGNORECASE)
        if rendermode_match:
            quote_data['renderMode'] = rendermode_match.group(1).strip()

        # Only add if we have a quote
        if quote_data['quote']:
            quotes.append(quote_data)

    return quotes


def main():
    """Extract FSQ quotes from episode 0245 and save to JSON."""
    db = SessionLocal()

    try:
        # Get script content from rundown item
        result = db.execute(
            text("SELECT script_content FROM rundown_items WHERE rundown_id = 28 AND id = 370")
        ).fetchone()

        if not result:
            print("❌ No script content found for episode 0245")
            return False

        script_content = result[0]
        print(f"📖 Loaded script content ({len(script_content)} characters)")

        # Extract FSQ cues
        quotes = extract_fsq_cues(script_content)
        print(f"✅ Found {len(quotes)} FSQ quotes")

        # Display summary
        for i, quote in enumerate(quotes, 1):
            print(f"  {i}. [{quote['slug']}] - {quote['wordCount']} words - Part {quote['part']}")

        # Save to JSON file (use container path)
        output_file = '/home/episodes/0245/fsq_quotes.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved to: {output_file}")
        print(f"📊 Total quotes: {len(quotes)}")

        # Calculate total parts vs individual quotes
        multipart = [q for q in quotes if 'x' in q['part'] and q['part'] != '1x1']
        single = [q for q in quotes if q['part'] == '1x1']
        print(f"   Single-part quotes: {len(single)}")
        print(f"   Multi-part quotes: {len(multipart)}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
