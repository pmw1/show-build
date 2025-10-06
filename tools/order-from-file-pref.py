#!/usr/bin/env python3
"""
Order From File Prefix Tool - Show-Build Tools Suite

Updates the 'order:' frontmatter field in segment files based on the numeric prefix in the filename.
Extracts the number prefix from filenames like "10 News Roundup.md" and sets order: "10".

Usage:
    python order-from-file-pref.py --episode=0236
    python order-from-file-pref.py 0236
"""

import argparse
import sys
import re
from pathlib import Path
from typing import Optional, List

# Add both tools and app directories to Python path
tools_dir = Path(__file__).parent
sys.path.insert(0, str(tools_dir))
sys.path.insert(0, str(tools_dir.parent / 'app'))

# Import from centralized paths system
try:
    from core.paths import ShowBuildPaths
    path_manager = ShowBuildPaths()
    EPISODES_ROOT = path_manager.episodes_root
except ImportError:
    # Fallback to direct path
    EPISODES_ROOT = Path("/mnt/sync/disaffected/episodes")


class SegmentOrderUpdater:
    """Updates segment order fields based on filename prefixes."""
    
    def __init__(self, episode_number: str):
        self.episode_number = episode_number
        self.episodes_root = EPISODES_ROOT
        self.updated_count = 0
        self.skipped_count = 0
        self.error_count = 0
    
    def update_episode_order_fields(self) -> bool:
        """Update order fields for all segments in the episode."""
        episode_path = self.episodes_root / self.episode_number
        rundown_path = episode_path / "rundown"
        
        if not episode_path.exists():
            print(f"❌ Episode directory not found: {episode_path}")
            return False
        
        if not rundown_path.exists():
            print(f"❌ Rundown directory not found: {rundown_path}")
            return False
        
        print(f"🔄 Processing episode {self.episode_number}")
        print(f"📁 Rundown path: {rundown_path}")
        print()
        
        # Get all markdown files in rundown directory
        segment_files = list(rundown_path.glob("*.md"))
        segment_files.sort()  # Sort for consistent processing order
        
        if not segment_files:
            print("❌ No segment files found in rundown directory")
            return False
        
        print(f"📝 Found {len(segment_files)} segment files")
        print()
        
        # Process each segment file
        for segment_file in segment_files:
            self._process_segment_file(segment_file)
        
        # Print summary
        print()
        print("=" * 60)
        print("📊 Order Update Summary")
        print("=" * 60)
        print(f"✅ Files updated: {self.updated_count}")
        print(f"⏭️  Files skipped: {self.skipped_count}")
        print(f"❌ Files with errors: {self.error_count}")
        print(f"📝 Total files processed: {len(segment_files)}")
        
        return True
    
    def _process_segment_file(self, segment_file: Path):
        """Process a single segment file to update its order field."""
        try:
            # Extract numeric prefix from filename
            filename = segment_file.stem  # Remove .md extension
            order_number = self._extract_order_number(filename)
            
            if order_number is None:
                print(f"⏭️  SKIPPED: {segment_file.name} (no numeric prefix found)")
                self.skipped_count += 1
                return
            
            # Read current file content
            content = segment_file.read_text(encoding='utf-8')
            
            # Update the order field in frontmatter
            updated_content = self._update_order_field(content, order_number)
            
            if updated_content != content:
                # Write updated content back to file
                segment_file.write_text(updated_content, encoding='utf-8')
                print(f"✅ UPDATED: {segment_file.name} -> order: \"{order_number}\"")
                self.updated_count += 1
            else:
                print(f"⏭️  SKIPPED: {segment_file.name} (order already \"{order_number}\")")
                self.skipped_count += 1
                
        except Exception as e:
            print(f"❌ ERROR: {segment_file.name} - {e}")
            self.error_count += 1
    
    def _extract_order_number(self, filename: str) -> Optional[str]:
        """Extract the numeric prefix from a filename."""
        # Match numeric prefix at the start of filename
        # Examples: "10 News Roundup" -> "10", "41 SLOCUM CONSULTING" -> "41"
        match = re.match(r'^(\d+)', filename)
        if match:
            return match.group(1)
        return None
    
    def _update_order_field(self, content: str, order_number: str) -> str:
        """Update the order field in YAML frontmatter."""
        lines = content.split('\n')
        updated_lines = []
        in_frontmatter = False
        frontmatter_end_found = False
        order_updated = False
        
        for i, line in enumerate(lines):
            # Detect frontmatter boundaries
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                elif in_frontmatter and not frontmatter_end_found:
                    frontmatter_end_found = True
                    in_frontmatter = False
            
            # Update order field if we're in frontmatter
            if in_frontmatter and not frontmatter_end_found:
                order_match = re.match(r'^(\s*order:\s*)(.*?)(\s*)$', line)
                if order_match:
                    indent = order_match.group(1)
                    trailing_space = order_match.group(3)
                    new_line = f'{indent}"{order_number}"{trailing_space}'
                    updated_lines.append(new_line)
                    order_updated = True
                    continue
            
            updated_lines.append(line)
        
        # If no order field was found but we have frontmatter, add it
        if not order_updated and frontmatter_end_found:
            # Find the end of frontmatter and insert order field before it
            for i, line in enumerate(updated_lines):
                if line.strip() == '---' and i > 0:  # This is the closing ---
                    updated_lines.insert(i, f'order: "{order_number}"')
                    break
        
        return '\n'.join(updated_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Update segment order fields based on filename numeric prefixes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python order-from-file-pref.py --episode=0236
  python order-from-file-pref.py 0236

The script will:
1. Find all .md files in the episode's rundown directory
2. Extract numeric prefixes from filenames (e.g., "10" from "10 News.md")
3. Update the 'order:' field in frontmatter to match the prefix
4. Log all changes to console
        """
    )
    
    parser.add_argument(
        'episode',
        nargs='?',
        help='Episode number (e.g., 0236)'
    )
    parser.add_argument(
        '--episode',
        dest='episode_flag',
        help='Episode number (alternative format)'
    )
    
    args = parser.parse_args()
    
    # Get episode number from either positional or named argument  
    episode_number = args.episode or args.episode_flag
    
    if not episode_number:
        parser.print_help()
        sys.exit(1)
    
    # Validate episode number format
    if not re.match(r'^\d{4}$', episode_number):
        print(f"❌ Invalid episode number format: {episode_number}")
        print("Episode number should be 4 digits (e.g., 0236)")
        sys.exit(1)
    
    print("🎬 Segment Order Field Updater")
    print("=" * 60)
    print(f"📁 Episodes path: {EPISODES_ROOT}")
    print(f"🎯 Target episode: {episode_number}")
    print()
    
    try:
        updater = SegmentOrderUpdater(episode_number)
        success = updater.update_episode_order_fields()
        
        if success:
            print(f"\n🎉 Order field update completed for episode {episode_number}!")
            sys.exit(0)
        else:
            print(f"\n💥 Failed to process episode {episode_number}")
            sys.exit(1)
            
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