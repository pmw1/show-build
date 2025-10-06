#!/usr/bin/env python3
"""
AssetID Generator Script
Iterates through rundown items and generates real AssetIDs for items and cue blocks.
"""
import requests
import json
import os
import re
import yaml
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8888"
API_KEY = "nSudN-zXynaRm04RXTJJBeZi0OZNGMf9dtxlm1fKLNY"
EPISODES_ROOT = Path("/home/episodes")

class AssetIDGenerator:
    def __init__(self):
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        }
        
    def get_rundown_items(self, episode_number):
        """Get all rundown items for an episode."""
        response = requests.get(f"{API_BASE}/api/episodes/{episode_number}/rundown")
        if response.status_code == 200:
            return response.json().get('items', [])
        else:
            print(f"Error getting rundown items: {response.status_code}")
            return []
    
    def generate_assetid(self, asset_type, slug=None, episode_number=None, cue_type=None):
        """Generate a new AssetID via API."""
        payload = {
            "asset_type": asset_type,
            "episode_number": int(episode_number) if episode_number else None
        }
        
        if slug:
            payload["slug"] = slug
        if cue_type:
            payload["cue_type"] = cue_type
            
        response = requests.post(f"{API_BASE}/newAssetID", 
                               headers=self.headers, 
                               json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('asset_id')
        else:
            print(f"Error generating AssetID: {response.status_code} - {response.text}")
            return None
    
    def parse_frontmatter_and_content(self, file_path):
        """Parse markdown file and extract frontmatter and content."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split frontmatter and content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1].strip()
                body_content = parts[2].strip()
                frontmatter = yaml.safe_load(frontmatter_text)
                return frontmatter, body_content
        
        return {}, content
    
    def find_cue_blocks(self, content):
        """Find all cue blocks in content like {GFX/filename}, {SOT/filename}, etc."""
        # Pattern to match cue blocks: {TYPE/filename}
        cue_pattern = r'\{(GFX|SOT|FSQ|VO|NET|MUS|LIVE|PKG|VOX|NAT)\/([^}]+)\}'
        matches = re.findall(cue_pattern, content, re.IGNORECASE)
        
        cues = []
        for cue_type, filename in matches:
            cues.append({
                'type': cue_type.upper(),
                'filename': filename,
                'full_match': f"{{{cue_type}/{filename}}}"
            })
        
        return cues
    
    def update_file_with_assetid(self, file_path, frontmatter, content, new_assetid):
        """Update markdown file with new AssetID in frontmatter."""
        frontmatter['AssetID'] = new_assetid
        
        # Reconstruct file content
        yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        new_content = f"---\n{yaml_content}---\n\n{content}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Updated {file_path} with AssetID: {new_assetid}")
    
    def process_episode(self, episode_number):
        """Process all rundown items in an episode."""
        print(f"\n🔍 Processing Episode {episode_number}")
        
        # Get rundown items from API
        items = self.get_rundown_items(episode_number)
        if not items:
            print(f"No rundown items found for episode {episode_number}")
            return
        
        episode_dir = EPISODES_ROOT / episode_number / "rundown"
        if not episode_dir.exists():
            print(f"Episode directory not found: {episode_dir}")
            return
        
        for item in items:
            filename = item.get('filename')
            asset_id = item.get('AssetID') or item.get('asset_id')
            item_type = item.get('type', 'unknown')
            slug = item.get('slug', '')
            
            if not filename:
                continue
                
            file_path = episode_dir / filename
            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                continue
            
            print(f"\n📄 Processing: {filename}")
            print(f"   Current AssetID: {asset_id or 'MISSING'}")
            print(f"   Type: {item_type}")
            
            # Parse file content
            frontmatter, content = self.parse_frontmatter_and_content(file_path)
            
            # Check if item needs AssetID
            needs_assetid = not asset_id or asset_id == "null"
            
            if needs_assetid:
                print(f"   🔄 Generating AssetID for {item_type}...")
                new_assetid = self.generate_assetid(
                    asset_type=item_type,
                    slug=slug,
                    episode_number=episode_number
                )
                
                if new_assetid:
                    self.update_file_with_assetid(file_path, frontmatter, content, new_assetid)
                else:
                    print(f"   ❌ Failed to generate AssetID for {filename}")
            else:
                print(f"   ✅ AssetID already exists: {asset_id}")
            
            # Check for cue blocks in content
            cues = self.find_cue_blocks(content)
            if cues:
                print(f"   📋 Found {len(cues)} cue blocks:")
                for cue in cues:
                    print(f"      - {cue['type']}: {cue['filename']}")
                    
                    # Generate AssetID for cue block
                    cue_assetid = self.generate_assetid(
                        asset_type="cue",
                        slug=cue['filename'],
                        episode_number=episode_number,
                        cue_type=cue['type']
                    )
                    
                    if cue_assetid:
                        print(f"        ✅ Generated cue AssetID: {cue_assetid}")
                        # Note: You might want to store cue AssetIDs in a database
                        # rather than modifying the markdown content
                    else:
                        print(f"        ❌ Failed to generate cue AssetID")
    
    def run(self, episode_number):
        """Main execution function."""
        print("🚀 Starting AssetID Generator")
        print(f"Episode: {episode_number}")
        print(f"API Base: {API_BASE}")
        print(f"Episodes Root: {EPISODES_ROOT}")
        
        self.process_episode(episode_number)
        
        print("\n✅ AssetID generation complete!")

def main():
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python assetid_generator.py <episode_number>")
        print("Example: python assetid_generator.py 0240")
        sys.exit(1)
    
    episode_number = sys.argv[1]
    generator = AssetIDGenerator()
    generator.run(episode_number)

if __name__ == "__main__":
    main()