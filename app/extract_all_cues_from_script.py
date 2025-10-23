#!/usr/bin/env python3
"""
Extract all cue elements from Josh's script file format.
Supports: {FS Quote/slug}, {IMG/slug}, {GFX/slug}, {SOT/slug}
Output chronological shot list with enumeration by multiples of 10.
"""

import re
import sys


def extract_all_cues(script_path):
    """Extract all cue markers from script file in chronological order."""

    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    cues = []
    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Check for FS Quote
        fs_quote_match = re.match(r'\{FS\s+[Qq]uote[/\s]([^}]*)\}', line)
        if fs_quote_match:
            slug = fs_quote_match.group(1).strip()
            clean_slug = re.sub(r'[^a-z0-9\s-]', '', slug.lower())
            clean_slug = re.sub(r'\s+', '-', clean_slug).strip('-')
            if not clean_slug:
                clean_slug = f"quote-{len(cues) + 1}"

            cues.append({
                'type': 'FSQ',
                'slug': clean_slug,
                'line': line_num,
                'original': slug
            })
            continue

        # Check for IMG
        img_match = re.match(r'\{IMG[/\s]([^}]+)\}', line, re.IGNORECASE)
        if img_match:
            slug = img_match.group(1).strip()
            clean_slug = re.sub(r'[^a-z0-9\s-]', '', slug.lower())
            clean_slug = re.sub(r'\s+', '-', clean_slug).strip('-')

            cues.append({
                'type': 'IMG',
                'slug': clean_slug,
                'line': line_num,
                'original': slug
            })
            continue

        # Check for GFX
        gfx_match = re.match(r'\{GFX[/\s]([^}]+)\}', line, re.IGNORECASE)
        if gfx_match:
            slug = gfx_match.group(1).strip()
            clean_slug = re.sub(r'[^a-z0-9\s-]', '', slug.lower())
            clean_slug = re.sub(r'\s+', '-', clean_slug).strip('-')

            cues.append({
                'type': 'GFX',
                'slug': clean_slug,
                'line': line_num,
                'original': slug
            })
            continue

        # Check for SOT
        sot_match = re.match(r'\{SOT[/\s]([^}]+)\}', line, re.IGNORECASE)
        if sot_match:
            slug = sot_match.group(1).strip()
            clean_slug = re.sub(r'[^a-z0-9\s-]', '', slug.lower())
            clean_slug = re.sub(r'\s+', '-', clean_slug).strip('-')

            cues.append({
                'type': 'SOT',
                'slug': clean_slug,
                'line': line_num,
                'original': slug
            })
            continue

    return cues


def generate_shot_list(cues):
    """Generate enumerated shot list by multiples of 10."""

    shot_list = []

    for i, cue in enumerate(cues):
        shot_number = (i + 1) * 10
        shot_list.append({
            'shot': shot_number,
            'type': cue['type'],
            'slug': cue['slug'],
            'original': cue['original'],
            'line': cue['line']
        })

    return shot_list


def main():
    """Extract all cues and generate shot list."""

    script_path = '/mnt/sync/disaffected/episodes/.trash/0245_20251018_201219/preshow/SCRIPT 244.txt'
    output_path = '/mnt/sync/disaffected/episodes/0245/scripts/shot_list.txt'

    print(f"📖 Reading script: {script_path}\n")

    try:
        # Extract all cues
        cues = extract_all_cues(script_path)

        print(f"✅ Found {len(cues)} cues in chronological order:\n")

        # Count by type
        type_counts = {}
        for cue in cues:
            cue_type = cue['type']
            type_counts[cue_type] = type_counts.get(cue_type, 0) + 1

        print("📊 Breakdown by type:")
        for cue_type in sorted(type_counts.keys()):
            print(f"   {cue_type}: {type_counts[cue_type]}")
        print()

        # Generate shot list
        shot_list = generate_shot_list(cues)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("EPISODE 0245 SHOT LIST\n")
            f.write("=" * 80 + "\n\n")

            for shot in shot_list:
                f.write(f"{shot['shot']:03d}  [{shot['type']:3s}]  {shot['slug']}\n")

        print(f"💾 Saved shot list to: {output_path}\n")

        # Display shot list
        print("=" * 80)
        print("EPISODE 0245 SHOT LIST")
        print("=" * 80)
        print()

        for shot in shot_list:
            print(f"{shot['shot']:03d}  [{shot['type']:3s}]  {shot['slug']}")

        print()
        print(f"📊 Total shots: {len(shot_list)}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
