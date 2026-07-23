#!/usr/bin/env python3
"""
Media Collection Tool - Show-Build Edition

Scans episode rundown files for media references and collects all referenced media
files into an enumerated list directory for vMix production use.

Adapted from /mnt/sync/disaffected/tools/python/render-list.py to use
Show-Build centralized path management and enhanced validation.

Usage:
    python media-collect.py 0237
    python media-collect.py --episode 0237
"""

import argparse
import sys
import re
import shutil
import yaml
from pathlib import Path
from datetime import datetime

# Add tools directory to Python path for Show-Build imports
tools_dir = Path(__file__).parent
sys.path.insert(0, str(tools_dir))
sys.path.insert(0, str(tools_dir.parent / 'app'))

# Import Show-Build centralized paths
try:
    from core.paths import ShowBuildPaths
    path_manager = ShowBuildPaths()
    EPISODES_ROOT = path_manager.episodes_root
except ImportError:
    # Fallback to tools path system
    from paths import EPISODE_ROOT
    EPISODES_ROOT = EPISODE_ROOT

__version__ = "2.1.0-showbuild"

# API endpoint for FSQ regeneration (optional)
FSQ_API_BASE = "http://localhost:8888/api/fsq"


class MediaCollector:
    """Media collection engine for Show-Build episodes."""
    
    def __init__(self, episode_number: str, generate_fsq: bool = True, regenerate_fsq: bool = False):
        self.episode_number = episode_number
        self.episodes_root = EPISODES_ROOT
        self.episode_path = self.episodes_root / episode_number
        self.rundown_path = self.episode_path / "rundown"
        self.list_path = self.rundown_path / "list"
        self.counter = 1
        self.collected_files = []
        self.generate_fsq = generate_fsq  # Generate missing FSQ PNGs before collection
        self.regenerate_fsq = regenerate_fsq  # Regenerate all FSQ PNGs (even existing)

        # Valid cue types for media collection
        self.media_cue_types = ['GFX', 'SOT']
        self.fsq_cue_types = ['FSQ']
        
    def validate_paths(self) -> bool:
        """Validate that required paths exist."""
        if not self.episode_path.exists():
            print(f"❌ Episode folder for {self.episode_number} does not exist at {self.episode_path}")
            return False

        if not self.rundown_path.exists():
            print(f"❌ Rundown folder for episode {self.episode_number} does not exist at {self.rundown_path}")
            return False

        return True

    def trigger_fsq_generation(self) -> dict:
        """
        Trigger FSQ PNG generation via API before collecting media.

        Returns:
            dict: API response with generation status
        """
        import urllib.request
        import json as json_lib

        if not self.generate_fsq and not self.regenerate_fsq:
            return {"skipped": True, "message": "FSQ generation disabled"}

        print(f"\n🎨 Triggering FSQ PNG generation...")

        try:
            url = f"{FSQ_API_BASE}/regenerate-all/{self.episode_number}?regenerate_existing={str(self.regenerate_fsq).lower()}"

            # Create request with proper headers
            req = urllib.request.Request(
                url,
                method='POST',
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json_lib.loads(response.read().decode('utf-8'))

            print(f"   ✅ FSQ generation triggered: {result.get('message', 'No message')}")
            print(f"   📊 Total FSQs: {result.get('total_fsqs', 0)}")
            print(f"   📥 Queued: {result.get('generated', 0)}")
            print(f"   ⏭️ Skipped: {result.get('skipped', 0)}")
            print(f"   ❌ Failed: {result.get('failed', 0)}")

            if result.get('generated', 0) > 0:
                print(f"   ⏳ Waiting 5 seconds for generation to complete...")
                import time
                time.sleep(5)

            return result

        except urllib.error.URLError as e:
            print(f"   ⚠️ Could not connect to FSQ API: {e}")
            print(f"   📝 Proceeding with existing FSQ files...")
            return {"error": str(e), "generated": 0}
        except Exception as e:
            print(f"   ⚠️ FSQ generation request failed: {e}")
            return {"error": str(e), "generated": 0}
    
    def parse_yaml_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from markdown content."""
        match = re.match(r'^---\s*$(.*?)^---\s*$', content, re.DOTALL | re.MULTILINE)
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                return {}
        return {}
    
    def get_production_segments(self) -> list:
        """Get all segments with 'production' status, sorted by order field."""
        segment_files = sorted(self.rundown_path.glob("*.md"))
        
        if not segment_files:
            print(f"❌ No markdown files found in {self.rundown_path}")
            return []
            
        valid_segments = []
        segment_order_map = {}
        
        print("🔍 Filtering segments by production status...")
        
        for file_path in segment_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                frontmatter = self.parse_yaml_frontmatter(content)
                status = frontmatter.get("status", "").strip().lower()
                order = str(frontmatter.get("order", "")).strip()
                
                if status == "production":
                    valid_segments.append(file_path)
                    order_val = order if order else "9999"
                    segment_order_map[file_path] = order_val
                    print(f"✅ INCLUDED: {file_path.name} (status: 'production', order: '{order_val}')")
                else:
                    status_display = status if status else "empty"
                    print(f"⏭️  EXCLUDED: {file_path.name} (status: '{status_display}')")
                    
            except Exception as e:
                print(f"❌ ERROR: {file_path.name}: {e}")
        
        # Sort by order field (numeric) with filename as tiebreaker
        valid_segments.sort(key=lambda x: (int(segment_order_map[x]) if segment_order_map[x].isdigit() else 9999, x.name))
        
        print(f"\n📋 Sorted segments by order:")
        for seg in valid_segments:
            order_val = segment_order_map[seg]
            print(f"   {seg.name} (order: {order_val})")
            
        return valid_segments
    
    def find_fsq_media_files(self, cue_slug: str, asset_id: str) -> list:
        """Find FSQ media files in quotes/generated_quotes folders."""
        search_paths = [
            self.episode_path / "assets" / "quotes",
            self.episode_path / "assets" / "generated_quotes"
        ]
        
        media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi', '.webm', '.svg']
        matching_files = []
        
        search_patterns = [
            f"{cue_slug}.*",
            f"{asset_id}.*", 
            f".*{cue_slug}.*"
        ]
        
        for quotes_path in search_paths:
            if not quotes_path.exists():
                continue
                
            for pattern in search_patterns:
                for ext in media_extensions:
                    matches = list(quotes_path.glob(f"{pattern}{ext}"))
                    if matches:
                        matches.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                        matching_files.extend(matches)
                        break
                if matching_files:
                    break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for f in matching_files:
            if f not in seen:
                seen.add(f)
                unique_files.append(f)
        
        return unique_files
    
    def process_segment(self, file_path: Path) -> list:
        """Process a single segment file for media collection."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"\n📄 Processing {file_path.name}")
        except Exception as e:
            print(f"❌ Error reading {file_path.name}: {e}")
            return []
        
        frontmatter = self.parse_yaml_frontmatter(content)
        order = str(frontmatter.get("order", "")).strip()
        
        # Find cue blocks with both correct and malformed syntax
        correct_cue_pattern = r"(<!--\s*Begin\s*Cue\s*-->.*?<!--\s*End\s*Cue\s*-->)"
        malformed_cue_pattern = r"(<<!--\s*Begin\s*Cue\s*-->>.*?<<!--\s*End\s*Cue\s*-->>)"
        
        correct_cues = list(re.finditer(correct_cue_pattern, content, flags=re.DOTALL | re.IGNORECASE))
        malformed_cues = list(re.finditer(malformed_cue_pattern, content, flags=re.DOTALL | re.IGNORECASE))
        
        all_cues = correct_cues + malformed_cues
        
        if malformed_cues:
            print(f"⚠️  WARNING: Found {len(malformed_cues)} malformed cue blocks")
        
        print(f"   Found {len(all_cues)} total cue blocks")
        
        collected_media = []
        
        for cue_match in all_cues:
            cue_block = cue_match.group(0)
            
            # Extract cue metadata
            cue_type_match = re.search(r"\[Type:\s*(.*?)\]", cue_block, re.IGNORECASE)
            cue_slug_match = re.search(r"\[Slug:\s*(.*?)\]", cue_block, re.IGNORECASE)
            asset_id_match = re.search(r"\[AssetID:\s*(.*?)\]", cue_block, re.IGNORECASE)
            
            cue_type = cue_type_match.group(1).strip().upper() if cue_type_match else "UNKNOWN"
            cue_slug = cue_slug_match.group(1).strip() if cue_slug_match else "unknown"
            asset_id = asset_id_match.group(1).strip() if asset_id_match else "unknown"
            
            print(f"   Processing cue: {asset_id} / {cue_type} / {cue_slug}")
            
            # Process GFX and SOT cues with MediaURL
            if cue_type in self.media_cue_types:
                media_url_match = re.search(r"\[MediaURL:\s*(.*?)\]", cue_block, re.IGNORECASE)
                if media_url_match:
                    media_url = media_url_match.group(1).strip()
                    
                    # Resolve media path using Show-Build path management
                    if media_url.startswith('../'):
                        # Relative path from rundown directory
                        clean_url = media_url.lstrip('../')
                        source_path = self.episode_path / clean_url
                    else:
                        # Absolute or episode-relative path
                        source_path = Path(media_url) if media_url.startswith('/') else self.episode_path / media_url
                    
                    if source_path.exists():
                        collected_file = self.copy_media_file(source_path, order, cue_type, cue_slug)
                        if collected_file:
                            collected_media.append(collected_file)
                    else:
                        print(f"      ❌ Media file not found: {source_path}")
            
            # Process FSQ cues by searching for generated quote images
            elif cue_type in self.fsq_cue_types:
                print(f"      Processing FSQ cue - searching for generated quote media")
                
                fsq_media_files = self.find_fsq_media_files(cue_slug, asset_id)
                
                if fsq_media_files:
                    print(f"      Found {len(fsq_media_files)} FSQ media file(s)")
                    
                    for fsq_file in fsq_media_files:
                        collected_file = self.copy_media_file(fsq_file, order, cue_type, cue_slug)
                        if collected_file:
                            collected_media.append(collected_file)
                else:
                    print(f"      ⚠️  No FSQ media files found for '{cue_slug}' or '{asset_id}'")
        
        return collected_media
    
    def copy_media_file(self, source_path: Path, order: str, cue_type: str, cue_slug: str) -> str:
        """Copy media file to list directory with enumerated naming."""
        filename = source_path.name
        
        # Create enumerated filename: order_counter_original-name
        order_prefix = order.zfill(2) if order.isdigit() else "99"
        target_filename = f"{order_prefix}_{self.counter:02d}_{filename}"
        target_path = self.list_path / target_filename
        
        try:
            # Ensure list directory exists
            self.list_path.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source_path, target_path)
            print(f"      ✅ Copied to: {target_filename}")
            
            self.counter += 1
            return str(target_path.resolve())
            
        except Exception as e:
            print(f"      ❌ Copy failed: {e}")
            return ""
    
    def generate_media_list(self, collected_files: list):
        """Generate M3U playlist and text file list."""
        # Create M3U playlist
        m3u_path = self.rundown_path / "media-list.m3u"
        
        try:
            with open(m3u_path, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                f.write(f"# Generated by Show-Build Media Collector v{__version__}\n")
                f.write(f"# Episode: {self.episode_number}\n") 
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write(f"# Total files: {len(collected_files)}\n")
                f.write("\\n")
                
                for media_file in collected_files:
                    f.write(f"{media_file}\n")
            
            print(f"✅ M3U playlist saved: {m3u_path}")
            
        except Exception as e:
            print(f"❌ Error saving M3U playlist: {e}")
        
        # Create text file with just filenames
        txt_path = self.rundown_path / "media-list.txt"
        
        try:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"# Show-Build Media List - Episode {self.episode_number}\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write("\\n")
                
                for media_file in collected_files:
                    filename = Path(media_file).name
                    f.write(f"{filename}\n")
            
            print(f"✅ Text file list saved: {txt_path}")
            
        except Exception as e:
            print(f"❌ Error saving text list: {e}")
    
    def collect_media(self) -> bool:
        """Main media collection process."""
        print(f"🎬 Show-Build Media Collector v{__version__}")
        print("=" * 80)
        print(f"📺 Episode: {self.episode_number}")
        print(f"📁 Episodes root: {self.episodes_root}")
        print(f"📁 Episode path: {self.episode_path}")
        print(f"📁 List directory: {self.list_path}")
        print(f"🎨 FSQ Generation: {'Enabled' if self.generate_fsq else 'Disabled'}")
        print(f"🔄 FSQ Regenerate: {'All' if self.regenerate_fsq else 'Missing Only'}")
        print()

        # Validate paths
        if not self.validate_paths():
            return False

        # Trigger FSQ generation before collecting media
        if self.generate_fsq:
            self.trigger_fsq_generation()

        # Get production segments
        valid_segments = self.get_production_segments()
        if not valid_segments:
            print("❌ No production-ready segments found")
            return False
        
        # Process each segment
        print(f"\n🔄 Processing {len(valid_segments)} segments for media collection...")
        
        for segment in valid_segments:
            segment_media = self.process_segment(segment)
            self.collected_files.extend(segment_media)
        
        # Generate output files
        if self.collected_files:
            print(f"\n📝 Generating media lists...")
            self.generate_media_list(self.collected_files)
            
            print("\n" + "=" * 80)
            print(f"✅ SUCCESS: Media collection completed!")
            print(f"📊 Total media files collected: {len(self.collected_files)}")
            print(f"📁 Files copied to: {self.list_path}")
            print(f"📋 Media list: {self.rundown_path / 'media-list.txt'}")
            print(f"🎵 M3U playlist: {self.rundown_path / 'media-list.m3u'}")
            print("=" * 80)
            return True
        else:
            print("\n⚠️  No media files found to collect")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="Collect all media references from episode rundown into enumerated list directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python media-collect.py 0237
  python media-collect.py --episode 0237
  python media-collect.py 0237 --regenerate-fsq    # Regenerate all FSQ PNGs
  python media-collect.py 0237 --no-fsq            # Skip FSQ generation

The script will:
1. Trigger FSQ PNG generation for any missing quote graphics (via API)
2. Scan all rundown segments with 'production' status
3. Extract MediaURL references from GFX/SOT cue blocks
4. Find FSQ-generated quote images in assets/quotes/
5. Copy all media to rundown/list/ with enumerated filenames
6. Generate media-list.m3u and media-list.txt files

Path Management:
- Uses Show-Build centralized path system
- Handles relative MediaURL paths (../assets/...)
- Searches multiple quote directories for FSQ media

FSQ PNG Generation:
- Default: Generate missing FSQ PNGs only
- --regenerate-fsq: Regenerate ALL FSQ PNGs (even existing)
- --no-fsq: Skip FSQ generation entirely (use existing files only)
        """
    )

    parser.add_argument(
        "episode_number",
        nargs="?",
        help="Episode number (4 digits, e.g., 0237)"
    )
    parser.add_argument(
        "--episode",
        help="Episode number (alternative format)"
    )
    parser.add_argument(
        "--regenerate-fsq",
        action="store_true",
        help="Regenerate ALL FSQ PNG graphics (even if they already exist)"
    )
    parser.add_argument(
        "--no-fsq",
        action="store_true",
        help="Skip FSQ PNG generation (use existing files only)"
    )

    args = parser.parse_args()

    # Get episode number from either positional or --episode argument
    episode_number = args.episode_number or args.episode

    if not episode_number:
        print("❌ Episode number is required")
        parser.print_help()
        sys.exit(1)

    if not re.match(r'^\d{4}$', episode_number):
        print(f"❌ Invalid episode number format: {episode_number}")
        print("Episode number should be 4 digits (e.g., 0237)")
        sys.exit(1)

    # Determine FSQ generation settings
    generate_fsq = not args.no_fsq
    regenerate_fsq = args.regenerate_fsq

    try:
        collector = MediaCollector(
            episode_number,
            generate_fsq=generate_fsq,
            regenerate_fsq=regenerate_fsq
        )
        success = collector.collect_media()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()