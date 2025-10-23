#!/usr/bin/env python3
"""
Populate media-list folder with all visual elements enumerated by shot number.
"""

import os
import shutil

# Shot list with file locations and actual filenames
shots = [
    (10, 'IMG', 'i-love-hitler', 'preshow', 'i love hitler.png'),
    (20, 'FSQ', 'leaders-of-young', 'assets/graphics', 'leaders-of-young.png'),
    (30, 'FSQ', 'they-referred', 'assets/graphics', 'they-referred.png'),
    (40, 'FSQ', 'the-exchange-is', 'assets/graphics', 'the-exchange-is.png'),
    (50, 'FSQ', 'since-politico', 'assets/graphics', 'since-politico.png'),
    (60, 'FSQ', 'the-more-the', 'assets/graphics', 'the-more-the.png'),
    (70, 'GFX', 'text-graphic', 'preshow', 'text graphic.png'),
    (80, 'IMG', 'unlikely-buddha', 'preshow', 'unlikely buddha.png'),
    (90, 'IMG', 'lauren-ashley', 'preshow', 'lauren ashley.png'),
    (95, 'FSQ', 'luv-my-gov', 'assets/graphics', 'luv-my-gov.png'),
    (96, 'FSQ', 'keep-family-safe', 'assets/graphics', 'keep-family-safe.png'),
    (100, 'GFX', 'great-feminizaton', 'preshow', 'great feminizaton.png'),
    (110, 'FSQ', 'this-cancellation', 'assets/graphics', 'this-cancellation.png'),
    (120, 'FSQ', 'the-field-that', 'assets/graphics', 'the-field-that.png'),
    (130, 'IMG', 'new-england-schools', 'preshow', 'new england schools.png'),
    (140, 'FSQ', 'in-new-england', 'assets/graphics', 'in-new-england.png'),
    (150, 'FSQ', 'i-have-to-tell', 'assets/graphics', 'i-have-to-tell.png'),
    (160, 'FSQ', 'he-stared-at', 'assets/graphics', 'he-stared-at.png'),
    (170, 'FSQ', 'i-looked-at', 'assets/graphics', 'i-looked-at.png'),
    (180, 'IMG', 'secretary-sean', 'preshow', 'secretary sean.png'),
    (190, 'GFX', 'i-grieved-through', 'preshow', 'i grieved through.png'),
    (200, 'GFX', 'i-felt-sad', 'preshow', 'i felt sad.png'),
    (210, 'SOT', '11-times-covid', 'preshow', '11 times covid.mp4'),
    (220, 'SOT', 'kung-fu-butterball', 'preshow', 'kung fu butterball.mp4'),
    (230, 'IMG', 'miley-cyrus', 'preshow', 'miley cyrus.png'),
    (240, 'SOT', 'independent-woman', 'preshow', 'independent woman.mp4'),
    (250, 'GFX', 'right-angle-news', 'preshow', 'right angle news.png'),
    (260, 'GFX', 'kevin-this-is-where-your-orphan-movie-poster-goes', 'preshow', None),  # TBD
    (270, 'SOT', 'naked-portland', 'preshow', 'naked portland.mp4'),
    (280, 'SOT', 'not-for-nothing', 'preshow', 'not for nothing.mp4'),
    (290, 'GFX', 'youtube-bell', 'preshow', 'youtube bell.png'),
]

base_path = '/mnt/sync/disaffected/episodes/0245'
media_list_path = f'{base_path}/rundown/media-list'

# Common image/video extensions
extensions = ['.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mov', '.avi', '.mkv']

copied = 0
missing = 0

for shot_data in shots:
    shot_num, media_type, slug, source_dir = shot_data[:4]
    actual_filename = shot_data[4] if len(shot_data) > 4 else None

    source_path = f'{base_path}/{source_dir}'

    if actual_filename:
        # Use the specified filename
        source_file = f'{source_path}/{actual_filename}'
        if os.path.exists(source_file):
            # Get extension from actual filename
            _, ext = os.path.splitext(actual_filename)
            dest_file = f'{media_list_path}/{shot_num:03d}-{slug}{ext}'
            shutil.copy2(source_file, dest_file)
            print(f"✅ {shot_num:03d} [{media_type}] {slug}{ext}")
            copied += 1
        else:
            print(f"❌ {shot_num:03d} [{media_type}] {actual_filename} - NOT FOUND in {source_dir}")
            missing += 1
    else:
        # Try to find the file with various extensions
        found = False
        for ext in extensions:
            source_file = f'{source_path}/{slug}{ext}'
            if os.path.exists(source_file):
                dest_file = f'{media_list_path}/{shot_num:03d}-{slug}{ext}'
                shutil.copy2(source_file, dest_file)
                print(f"✅ {shot_num:03d} [{media_type}] {slug}{ext}")
                copied += 1
                found = True
                break

        if not found:
            print(f"❌ {shot_num:03d} [{media_type}] {slug} - NOT FOUND in {source_dir}")
            missing += 1

print(f"\n📊 Summary:")
print(f"   Copied: {copied}")
print(f"   Missing: {missing}")
print(f"   Total: {len(shots)}")
print(f"\n📁 Media list: {media_list_path}")
