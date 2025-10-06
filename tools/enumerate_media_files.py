#!/usr/bin/env python3
"""
Media File Enumerator
Enumerates cue blocks in rundown order and copies media files with enumerated names
"""
import os
import re
import shutil
from pathlib import Path

def extract_cue_blocks_from_file(file_path):
    """Extract all cue blocks from a markdown file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return []
    
    # Extract frontmatter
    frontmatter_match = re.match(r'^---\s*$(.*?)^---\s*$', content, re.DOTALL | re.MULTILINE)
    order = 999  # Default high order
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        order_match = re.search(r'^order:\s*(\d+)', frontmatter, re.MULTILINE)
        if order_match:
            order = int(order_match.group(1))
    
    # Find all cue blocks
    cue_pattern = r'<!-- Begin Cue -->(.*?)<!-- End Cue -->'
    cue_blocks = []
    
    for match in re.finditer(cue_pattern, content, re.DOTALL):
        cue_content = match.group(1).strip()
        
        # Extract cue fields
        type_match = re.search(r'\[Type:\s*([^\]]+)\]', cue_content)
        slug_match = re.search(r'\[Slug:\s*([^\]]+)\]', cue_content)
        media_match = re.search(r'\[MediaURL:\s*([^\]]+)\]', cue_content)
        asset_id_match = re.search(r'\[AssetID:\s*([^\]]+)\]', cue_content)
        
        if type_match and slug_match:
            cue_type = type_match.group(1).strip()
            slug = slug_match.group(1).strip()
            media_url = media_match.group(1).strip() if media_match else ""
            asset_id = asset_id_match.group(1).strip() if asset_id_match else ""
            
            cue_blocks.append({
                'type': cue_type,
                'slug': slug,
                'media_url': media_url,
                'asset_id': asset_id,
                'file_order': order,
                'source_file': file_path.name
            })
    
    return cue_blocks

def enumerate_and_copy_media(rundown_dir, scripts_dir):
    """Enumerate all cue blocks and copy media files"""
    
    # Create /list subdirectory
    list_dir = scripts_dir / "list"
    list_dir.mkdir(exist_ok=True)
    print(f"📁 Created directory: {list_dir}")
    
    # Get all markdown files and sort by filename
    md_files = sorted(rundown_dir.glob("*.md"))
    
    # Extract all cue blocks with their file order
    all_cues = []
    for md_file in md_files:
        cues = extract_cue_blocks_from_file(md_file)
        all_cues.extend(cues)
    
    # Sort by file order, then by appearance in file
    all_cues.sort(key=lambda x: x['file_order'])
    
    print(f"🔍 Found {len(all_cues)} cue blocks total")
    
    # Enumerate by multiples of 10 and copy files
    copied_count = 0
    manifest = []
    
    for i, cue in enumerate(all_cues):
        enum_num = (i + 1) * 10  # 10, 20, 30, 40...
        
        print(f"\n🎬 Cue {enum_num:03d}: [{cue['type']}] {cue['slug']}")
        print(f"   Source: {cue['source_file']}")
        print(f"   AssetID: {cue['asset_id']}")
        
        if cue['media_url']:
            # Parse media URL to get filename
            media_path = cue['media_url'].replace('../assets/', '/mnt/sync/disaffected/episodes/0240/assets/')
            source_media = Path(media_path)
            
            print(f"   Media: {source_media.name}")
            
            if source_media.exists():
                # Create enumerated filename
                extension = source_media.suffix
                enum_filename = f"{enum_num:03d}-{cue['slug']}{extension}"
                dest_path = list_dir / enum_filename
                
                # Copy file
                try:
                    shutil.copy2(source_media, dest_path)
                    print(f"   ✅ Copied to: {enum_filename}")
                    copied_count += 1
                    
                    manifest.append({
                        'number': enum_num,
                        'slug': cue['slug'],
                        'type': cue['type'],
                        'asset_id': cue['asset_id'],
                        'original_file': source_media.name,
                        'enumerated_file': enum_filename,
                        'source_segment': cue['source_file']
                    })
                    
                except Exception as e:
                    print(f"   ❌ Copy failed: {e}")
            else:
                print(f"   ❌ Media file not found: {source_media}")
                # Add to manifest anyway for tracking
                manifest.append({
                    'number': enum_num,
                    'slug': cue['slug'],
                    'type': cue['type'],
                    'asset_id': cue['asset_id'],
                    'original_file': source_media.name,
                    'enumerated_file': f"{enum_num:03d}-{cue['slug']}{source_media.suffix}",
                    'source_segment': cue['source_file'],
                    'status': 'MISSING'
                })
        else:
            print(f"   ⚠️  No media URL specified")
    
    # Write manifest file
    manifest_path = list_dir / "media-manifest.txt"
    with open(manifest_path, 'w') as f:
        f.write("# Media File Enumeration Manifest\n")
        f.write("# Episode 0240 - Production Media List\n\n")
        
        for item in manifest:
            status = item.get('status', 'OK')
            f.write(f"{item['number']:03d} | {item['type']:3s} | {item['slug']:30s} | {item['enumerated_file']:40s} | {status}\n")
    
    print(f"\n✅ Enumeration complete!")
    print(f"   📁 List directory: {list_dir}")
    print(f"   📄 Manifest: {manifest_path}")
    print(f"   📋 Total cues: {len(all_cues)}")
    print(f"   📁 Files copied: {copied_count}")
    
    return manifest

def main():
    rundown_dir = Path("/mnt/sync/disaffected/episodes/0240/rundown")
    scripts_dir = Path("/mnt/sync/disaffected/episodes/0240/scripts")
    
    if not rundown_dir.exists():
        print(f"❌ Rundown directory not found: {rundown_dir}")
        return
    
    if not scripts_dir.exists():
        scripts_dir.mkdir(parents=True)
        print(f"📁 Created scripts directory: {scripts_dir}")
    
    print("🎬 Media File Enumerator")
    print("=" * 50)
    
    manifest = enumerate_and_copy_media(rundown_dir, scripts_dir)
    
    print("\n🎯 Ready for production!")

if __name__ == "__main__":
    main()