#!/usr/bin/env python3
"""
Extract FS Quote blocks from Josh's script file format.
Format: {FS Quote/slug}
        Quote text here
        —Attribution
"""

import re
import json
import sys


def extract_fs_quotes(script_path):
    """Extract all {FS Quote/...} blocks from script file."""

    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    quotes = []

    # Pattern to match {FS Quote/slug} followed by text until attribution line
    # Look for lines starting with {FS Quote or {FS quote (case insensitive)
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check if this line is an FS Quote marker
        if re.match(r'\{FS\s+[Qq]uote[/\s]', line):
            # Extract slug from the marker
            slug_match = re.search(r'\{FS\s+[Qq]uote[/\s]([^}]*)\}', line)
            if not slug_match:
                i += 1
                continue

            slug = slug_match.group(1).strip()
            if not slug:
                slug = "untitled-quote"

            # Collect quote lines until we hit attribution (line starting with — or --)
            quote_lines = []
            attribution = ""
            i += 1

            # Skip blank lines immediately after marker
            while i < len(lines) and not lines[i].strip():
                i += 1

            # Collect quote text
            while i < len(lines):
                current = lines[i].strip()

                # Check if this is the attribution line
                if current.startswith('—') or current.startswith('--'):
                    attribution = current.lstrip('—').lstrip('-').strip()
                    break

                # Check if we hit another cue marker (stop collecting)
                if current.startswith('{'):
                    break

                # Empty line might signal end of quote
                if not current:
                    # Check if next non-empty line is attribution
                    peek = i + 1
                    while peek < len(lines) and not lines[peek].strip():
                        peek += 1
                    if peek < len(lines):
                        next_line = lines[peek].strip()
                        if next_line.startswith('—') or next_line.startswith('--'):
                            i = peek
                            attribution = next_line.lstrip('—').lstrip('-').strip()
                            break
                    # Otherwise stop here
                    break

                # Add to quote
                if current:
                    quote_lines.append(current)

                i += 1

            # Join quote lines
            quote_text = ' '.join(quote_lines).strip()

            if quote_text:
                # Clean up slug for filename
                clean_slug = re.sub(r'[^a-z0-9\s-]', '', slug.lower())
                clean_slug = re.sub(r'\s+', '-', clean_slug).strip('-')
                if not clean_slug:
                    clean_slug = f"quote-{len(quotes) + 1}"

                # Count words
                word_count = len(quote_text.split())

                quotes.append({
                    'type': 'FSQ',
                    'slug': clean_slug,
                    'quote': quote_text,
                    'attribution': attribution if attribution else 'Unknown',
                    'style': 'left',
                    'fontFamily': 'sans-serif',
                    'fontSize': '24px',
                    'duration': '00:00:10:00',
                    'wordCount': word_count,
                    'part': '1x1',
                    'renderMode': 'png'
                })

        i += 1

    return quotes


def main():
    """Extract FS quotes and save to JSON."""

    script_path = '/mnt/sync/disaffected/episodes/.trash/0245_20251018_201219/preshow/SCRIPT 244.txt'
    output_path = '/mnt/sync/disaffected/episodes/0245/fs_quotes_extracted.json'

    print(f"📖 Reading script: {script_path}")

    try:
        quotes = extract_fs_quotes(script_path)

        print(f"\n✅ Found {len(quotes)} FS Quote blocks:\n")

        for i, quote in enumerate(quotes, 1):
            preview = quote['quote'][:60] + '...' if len(quote['quote']) > 60 else quote['quote']
            print(f"  {i}. [{quote['slug']}]")
            print(f"     Words: {quote['wordCount']} | Attribution: {quote['attribution']}")
            print(f"     Preview: {preview}\n")

        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved to: {output_path}")
        print(f"📊 Total quotes: {len(quotes)}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
