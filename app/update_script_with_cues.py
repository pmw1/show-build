#!/usr/bin/env python3
"""
Update SCRIPT 245 with enumerated cues based on shot list.
"""

import re

# Load shot list mapping
shot_list = {
    10: ('IMG', 'i-love-hitler'),
    20: ('FSQ', 'leaders-of-young'),
    30: ('FSQ', 'they-referred'),
    40: ('FSQ', 'the-exchange-is'),
    50: ('FSQ', 'since-politico'),
    60: ('FSQ', 'the-more-the'),
    70: ('GFX', 'text-graphic'),
    80: ('IMG', 'unlikely-buddha'),
    90: ('IMG', 'lauren-ashley'),
    95: ('FSQ', 'luv-my-gov'),
    96: ('FSQ', 'keep-family-safe'),
    100: ('GFX', 'great-feminizaton'),
    110: ('FSQ', 'this-cancellation'),
    120: ('FSQ', 'the-field-that'),
    130: ('IMG', 'new-england-schools'),
    140: ('FSQ', 'in-new-england'),
    150: ('FSQ', 'i-have-to-tell'),
    160: ('FSQ', 'he-stared-at'),
    170: ('FSQ', 'i-looked-at'),
    180: ('IMG', 'secretary-sean'),
    190: ('GFX', 'i-grieved-through'),
    200: ('GFX', 'i-felt-sad'),
    210: ('SOT', '11-times-covid'),
    220: ('SOT', 'kung-fu-butterball'),
    230: ('IMG', 'miley-cyrus'),
    240: ('SOT', 'independent-woman'),
    250: ('GFX', 'right-angle-news'),
    260: ('GFX', 'kevin-this-is-where-your-orphan-movie-poster-goes'),
    270: ('SOT', 'naked-portland'),
    280: ('SOT', 'not-for-nothing'),
    290: ('GFX', 'youtube-bell'),
}

# Reverse lookup: slug to shot number
slug_to_shot = {slug: num for num, (type_, slug) in shot_list.items()}

# New quotes to add (Sam Douglass quotes)
new_quotes = {
    95: {
        'slug': 'luv-my-gov',
        'quote': '"if my Governor asks me to do something, I will act, because I believe in what he\'s trying to do."',
        'attribution': '—Sen. Sam Douglass'
    },
    96: {
        'slug': 'keep-family-safe',
        'quote': '"I know that this decision will upset many, and delight others, but in this political climate I must keep my family safe, Douglass said, adding that his resignation will be effective Monday at noon. Since the story broke, I have reached out to the majority of my Jewish and BIPOC friends and colleagues to ensure that they can be honest and upfront with me, and I know that as a young person I have a duty to set a good example for others."',
        'attribution': '—Sen. Sam Douglass'
    }
}

script_input = '/mnt/sync/disaffected/episodes/.trash/0245_20251018_201219/preshow/SCRIPT 244.txt'
script_output = '/mnt/sync/disaffected/episodes/0245/SCRIPT 245.txt'

with open(script_input, 'r', encoding='utf-8') as f:
    lines = f.readlines()

output_lines = []
i = 0

while i < len(lines):
    line = lines[i]

    # Check for cue markers
    cue_match = re.match(r'\{(FS Quote|IMG|GFX|SOT)[/\s]([^}]+)\}', line, re.IGNORECASE)

    if cue_match:
        cue_type = cue_match.group(1).upper().replace(' ', '')
        if cue_type == 'FSQUOTE':
            cue_type = 'FSQ'

        original_slug = cue_match.group(2).strip()
        clean_slug = re.sub(r'[^a-z0-9\s-]', '', original_slug.lower())
        clean_slug = re.sub(r'\s+', '-', clean_slug).strip('-')

        # Find shot number
        shot_num = slug_to_shot.get(clean_slug)

        if shot_num:
            # Replace with enumerated version
            output_lines.append(f'{{{shot_num:03d}  [{cue_type}] {clean_slug}}}\n')
        else:
            # Keep original
            output_lines.append(line)

        # Skip blank lines immediately after cue marker
        i += 1
        while i < len(lines) and lines[i].strip() == '':
            i += 1
        continue
    else:
        output_lines.append(line)

    i += 1

# Insert new Sam Douglass quotes after the "since-politico" quote
# Find the location
insert_after_slug = 'since-politico'
insert_index = None

for idx, line in enumerate(output_lines):
    if insert_after_slug in line and '{050' in line:
        # Find the end of this quote block (skip attribution)
        search_idx = idx + 1
        while search_idx < len(output_lines):
            if output_lines[search_idx].strip().startswith('—'):
                insert_index = search_idx + 1
                break
            search_idx += 1
        break

# Insert the new quotes
if insert_index:
    new_content = []
    new_content.append('\n\n')

    # Quote 095
    new_content.append('{095  [FSQ] luv-my-gov}\n')
    new_content.append(new_quotes[95]['quote'] + '\n')
    new_content.append(new_quotes[95]['attribution'] + '\n')
    new_content.append('\n\n')

    # Quote 096
    new_content.append('{096  [FSQ] keep-family-safe}\n')
    new_content.append(new_quotes[96]['quote'] + '\n')
    new_content.append(new_quotes[96]['attribution'] + '\n')

    output_lines[insert_index:insert_index] = new_content

# Write output
with open(script_output, 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print(f"✅ Updated script saved to: {script_output}")
print(f"   - Enumerated all cues with shot numbers")
print(f"   - Added 2 new Sam Douglass quotes (095, 096)")
