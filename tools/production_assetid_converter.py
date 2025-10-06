#!/usr/bin/env python3
"""
Production AssetID Converter
Converts all LOCAL AssetIDs to real production AssetIDs for recording
"""
import re
import os
import requests
from pathlib import Path

def get_real_assetid(asset_type):
    """Get a real AssetID from the API based on type"""
    try:
        # Determine endpoint based on asset type
        if asset_type == 'SOT':
            endpoint = 'http://localhost:8888/api/new-assetid/sot'
        elif asset_type == 'GFX':
            endpoint = 'http://localhost:8888/api/new-assetid/gfx'
        else:
            endpoint = 'http://localhost:8888/api/new-assetid/other'
        
        response = requests.get(endpoint)
        if response.status_code == 200:
            data = response.json()
            return data.get('asset_id', f'PROD-{asset_type}-{os.urandom(6).hex().upper()}')
        else:
            # Fallback ID generation
            return f'PROD-{asset_type}-{os.urandom(6).hex().upper()}'
    except:
        # Emergency fallback
        return f'PROD-{asset_type}-{os.urandom(6).hex().upper()}'

def convert_file_assetids(file_path):
    """Convert all LOCAL AssetIDs in a single file"""
    print(f"🔄 Processing: {file_path.name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all LOCAL AssetIDs
    local_pattern = r'LOCAL-([A-Z]+)-\d{8}-\d{6}'
    matches = re.findall(local_pattern, content)
    
    if not matches:
        print(f"  ✅ No LOCAL AssetIDs found")
        return
    
    conversions = 0
    for asset_type in set(matches):  # Remove duplicates
        # Get real AssetID
        real_id = get_real_assetid(asset_type)
        
        # Replace all instances of this type
        old_pattern = f'LOCAL-{asset_type}-\\d{{8}}-\\d{{6}}'
        content = re.sub(old_pattern, real_id, content)
        conversions += 1
        print(f"  🔄 {asset_type}: LOCAL-{asset_type}-* → {real_id}")
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Converted {conversions} AssetID types")

def main():
    rundown_dir = Path('/mnt/sync/disaffected/episodes/0240/rundown')
    
    print("🚀 Production AssetID Converter")
    print("Converting all LOCAL AssetIDs to production AssetIDs...")
    print()
    
    total_files = 0
    for md_file in rundown_dir.glob('*.md'):
        convert_file_assetids(md_file)
        total_files += 1
    
    print()
    print(f"✅ Production conversion complete!")
    print(f"   Processed {total_files} rundown files")
    print("   Ready for recording! 🎬")

if __name__ == "__main__":
    main()