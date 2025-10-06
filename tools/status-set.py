#!/usr/bin/env python3
"""
Status Set Tool - Show-Build Tools Suite

Updates the 'status:' frontmatter field in segment files.
Can target specific segments by order number or AssetID, or apply to entire episodes.

Usage:
    python status-set.py --episode=0236 --segment=30 --status="production"
    python status-set.py --episode=0236 --status="draft"
    python status-set.py --AssetID=SEGMEEJ44L61P9LZV --status="approved"
"""

import argparse
import sys
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

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


class SegmentInfo:
    """Information about a segment file."""
    def __init__(self, file_path: Path, episode: str, order: str, title: str, current_status: str, asset_id: str):
        self.file_path = file_path
        self.episode = episode
        self.order = order
        self.title = title
        self.current_status = current_status
        self.asset_id = asset_id
    
    def __str__(self):
        return f"{self.episode}/{self.order} - {self.title} (current: {self.current_status})"


class StatusUpdater:
    """Updates segment status fields."""
    
    def __init__(self, auto_confirm: bool = False):
        self.episodes_root = EPISODES_ROOT
        self.updated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.auto_confirm = auto_confirm
    
    def update_status_by_episode_segment(self, episode_number: str, segment_order: str, new_status: str) -> bool:
        """Update status for a specific segment by episode and order number."""
        episode_path = self.episodes_root / episode_number
        rundown_path = episode_path / "rundown"
        
        if not self._validate_episode_path(episode_path, rundown_path):
            return False
        
        # Find segment file by order number
        segment_info = self._find_segment_by_order(rundown_path, segment_order)
        if not segment_info:
            print(f"❌ Segment with order '{segment_order}' not found in episode {episode_number}")
            return False
        
        # Display info and get confirmation
        episode_title = self._get_episode_title(episode_path)
        print(f"📺 Episode: {episode_number} - {episode_title}")
        print(f"📝 Segment: {segment_info}")
        print(f"🔄 New status: '{new_status}'")
        print()
        
        if not self.auto_confirm:
            try:
                response = input("Update this segment's status? (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("❌ Status update cancelled")
                    return False
            except EOFError:
                print("❌ Status update cancelled (non-interactive mode)")
                return False
        else:
            print("✅ Auto-confirming status update")
        
        return self._update_segment_status(segment_info, new_status)
    
    def update_status_by_episode(self, episode_number: str, new_status: str) -> bool:
        """Update status for all segments in an episode."""
        episode_path = self.episodes_root / episode_number
        rundown_path = episode_path / "rundown"
        
        if not self._validate_episode_path(episode_path, rundown_path):
            return False
        
        # Get all segments
        segments = self._get_all_segments(rundown_path)
        if not segments:
            print(f"❌ No segments found in episode {episode_number}")
            return False
        
        # Display info and get confirmation
        episode_title = self._get_episode_title(episode_path)
        print(f"📺 Episode: {episode_number} - {episode_title}")
        print(f"📝 Found {len(segments)} segments:")
        for segment in segments:
            print(f"   • {segment}")
        print(f"🔄 New status: '{new_status}'")
        print()
        
        if not self.auto_confirm:
            try:
                response = input(f"Update status for all {len(segments)} segments? (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("❌ Status update cancelled")
                    return False
            except EOFError:
                print("❌ Status update cancelled (non-interactive mode)")
                return False
        else:
            print(f"✅ Auto-confirming status update for all {len(segments)} segments")
        
        # Update all segments
        print(f"\n🔄 Updating {len(segments)} segments...")
        success = True
        for segment in segments:
            if not self._update_segment_status(segment, new_status):
                success = False
        
        return success
    
    def update_status_by_asset_id(self, asset_id: str, new_status: str) -> bool:
        """Update status for a segment by AssetID."""
        segment_info = self._find_segment_by_asset_id(asset_id)
        if not segment_info:
            print(f"❌ Segment with AssetID '{asset_id}' not found")
            return False
        
        # Display info and get confirmation
        episode_title = self._get_episode_title(self.episodes_root / segment_info.episode)
        print(f"📺 Episode: {segment_info.episode} - {episode_title}")
        print(f"📝 Segment: {segment_info}")
        print(f"🔄 New status: '{new_status}'")
        print()
        
        if not self.auto_confirm:
            try:
                response = input("Update this segment's status? (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("❌ Status update cancelled")
                    return False
            except EOFError:
                print("❌ Status update cancelled (non-interactive mode)")
                return False
        else:
            print("✅ Auto-confirming status update")
        
        return self._update_segment_status(segment_info, new_status)
    
    def _validate_episode_path(self, episode_path: Path, rundown_path: Path) -> bool:
        """Validate episode and rundown paths exist."""
        if not episode_path.exists():
            print(f"❌ Episode directory not found: {episode_path}")
            return False
        
        if not rundown_path.exists():
            print(f"❌ Rundown directory not found: {rundown_path}")
            return False
        
        return True
    
    def _get_episode_title(self, episode_path: Path) -> str:
        """Get episode title from info.md file."""
        info_file = episode_path / "info.md"
        if not info_file.exists():
            return "Unknown Title"
        
        try:
            content = info_file.read_text(encoding='utf-8')
            title_match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
            if title_match:
                return title_match.group(1).strip()
        except Exception:
            pass
        
        return "Unknown Title"
    
    def _find_segment_by_order(self, rundown_path: Path, target_order: str) -> Optional[SegmentInfo]:
        """Find segment file by order number."""
        for segment_file in rundown_path.glob("*.md"):
            segment_info = self._parse_segment_file(segment_file)
            if segment_info and segment_info.order == target_order:
                return segment_info
        return None
    
    def _find_segment_by_asset_id(self, target_asset_id: str) -> Optional[SegmentInfo]:
        """Find segment file by AssetID across all episodes."""
        for episode_dir in self.episodes_root.iterdir():
            if not episode_dir.is_dir() or not episode_dir.name.isdigit():
                continue
            
            rundown_path = episode_dir / "rundown"
            if not rundown_path.exists():
                continue
            
            for segment_file in rundown_path.glob("*.md"):
                segment_info = self._parse_segment_file(segment_file)
                if segment_info and segment_info.asset_id == target_asset_id:
                    return segment_info
        
        return None
    
    def _get_all_segments(self, rundown_path: Path) -> List[SegmentInfo]:
        """Get all segments in a rundown directory."""
        segments = []
        for segment_file in rundown_path.glob("*.md"):
            segment_info = self._parse_segment_file(segment_file)
            if segment_info:
                segments.append(segment_info)
        
        # Sort by order number
        segments.sort(key=lambda s: int(s.order) if s.order.isdigit() else 999)
        return segments
    
    def _parse_segment_file(self, segment_file: Path) -> Optional[SegmentInfo]:
        """Parse segment file to extract frontmatter information."""
        try:
            content = segment_file.read_text(encoding='utf-8')
            frontmatter = self._extract_frontmatter(content)
            
            if not frontmatter:
                return None
            
            episode = segment_file.parent.parent.name
            order = frontmatter.get('order', '').strip('"')
            title = frontmatter.get('title', segment_file.stem)
            current_status = frontmatter.get('status', '')
            asset_id = frontmatter.get('AssetID', '')
            
            return SegmentInfo(segment_file, episode, order, title, current_status, asset_id)
            
        except Exception as e:
            print(f"⚠️  Error parsing {segment_file}: {e}")
            return None
    
    def _extract_frontmatter(self, content: str) -> Optional[Dict[str, str]]:
        """Extract YAML frontmatter from file content."""
        lines = content.split('\n')
        if not lines or lines[0].strip() != '---':
            return None
        
        frontmatter = {}
        in_frontmatter = False
        
        for line in lines[1:]:
            if line.strip() == '---':
                break
            
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()
        
        return frontmatter
    
    def _update_segment_status(self, segment_info: SegmentInfo, new_status: str) -> bool:
        """Update the status field in a segment file."""
        try:
            content = segment_info.file_path.read_text(encoding='utf-8')
            updated_content = self._update_status_field(content, new_status)
            
            if updated_content != content:
                segment_info.file_path.write_text(updated_content, encoding='utf-8')
                print(f"✅ UPDATED: {segment_info.file_path.name} -> status: \"{new_status}\"")
                self.updated_count += 1
            else:
                print(f"⏭️  SKIPPED: {segment_info.file_path.name} (status already \"{new_status}\")")
                self.skipped_count += 1
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR: {segment_info.file_path.name} - {e}")
            self.error_count += 1
            return False
    
    def _update_status_field(self, content: str, new_status: str) -> str:
        """Update the status field in YAML frontmatter."""
        lines = content.split('\n')
        updated_lines = []
        in_frontmatter = False
        frontmatter_end_found = False
        status_updated = False
        
        for i, line in enumerate(lines):
            # Detect frontmatter boundaries
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                elif in_frontmatter and not frontmatter_end_found:
                    frontmatter_end_found = True
                    in_frontmatter = False
            
            # Update status field if we're in frontmatter
            if in_frontmatter and not frontmatter_end_found:
                status_match = re.match(r'^(\s*status:\s*)(.*?)(\s*)$', line)
                if status_match:
                    indent = status_match.group(1)
                    trailing_space = status_match.group(3)
                    new_line = f'{indent}{new_status}{trailing_space}'
                    updated_lines.append(new_line)
                    status_updated = True
                    continue
            
            updated_lines.append(line)
        
        # If no status field was found but we have frontmatter, add it
        if not status_updated and frontmatter_end_found:
            # Find the end of frontmatter and insert status field before it
            for i, line in enumerate(updated_lines):
                if line.strip() == '---' and i > 0:  # This is the closing ---
                    updated_lines.insert(i, f'status: {new_status}')
                    break
        
        return '\n'.join(updated_lines)
    
    def print_summary(self):
        """Print update summary."""
        print()
        print("=" * 60)
        print("📊 Status Update Summary")
        print("=" * 60)
        print(f"✅ Files updated: {self.updated_count}")
        print(f"⏭️  Files skipped: {self.skipped_count}")
        print(f"❌ Files with errors: {self.error_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Update segment status fields in frontmatter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python status-set.py --episode=0236 --segment=30 --status="production"
  python status-set.py --episode=0236 --status="draft"
  python status-set.py --AssetID=SEGMEEJ44L61P9LZV --status="approved"

The script will:
1. Find the target segment(s) by episode/order or AssetID
2. Display current information and request confirmation
3. Update the 'status:' field in YAML frontmatter
4. Log all changes to console
        """
    )
    
    parser.add_argument(
        '--episode',
        help='Episode number (e.g., 0236)'
    )
    parser.add_argument(
        '--segment',
        help='Segment order number (e.g., 30)'
    )
    parser.add_argument(
        '--AssetID',
        help='Segment AssetID (e.g., SEGMEEJ44L61P9LZV)'
    )
    parser.add_argument(
        '--status',
        required=True,
        help='New status value (e.g., "production", "draft", "approved")'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Auto-confirm all prompts (non-interactive mode)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.AssetID and not args.episode:
        print("❌ Must specify either --episode or --AssetID")
        parser.print_help()
        sys.exit(1)
    
    if args.AssetID and args.episode:
        print("❌ Cannot specify both --AssetID and --episode")
        parser.print_help()
        sys.exit(1)
    
    if args.segment and not args.episode:
        print("❌ --segment requires --episode")
        parser.print_help()
        sys.exit(1)
    
    # Validate episode number format if provided
    if args.episode and not re.match(r'^\d{4}$', args.episode):
        print(f"❌ Invalid episode number format: {args.episode}")
        print("Episode number should be 4 digits (e.g., 0236)")
        sys.exit(1)
    
    print("🎬 Segment Status Updater")
    print("=" * 60)
    print(f"📁 Episodes path: {EPISODES_ROOT}")
    print()
    
    try:
        updater = StatusUpdater(auto_confirm=args.yes)
        success = False
        
        if args.AssetID:
            # Update by AssetID
            success = updater.update_status_by_asset_id(args.AssetID, args.status)
        elif args.segment:
            # Update specific segment in episode
            success = updater.update_status_by_episode_segment(args.episode, args.segment, args.status)
        else:
            # Update entire episode
            success = updater.update_status_by_episode(args.episode, args.status)
        
        updater.print_summary()
        
        if success:
            print(f"\n🎉 Status update completed!")
            sys.exit(0)
        else:
            print(f"\n💥 Status update failed")
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