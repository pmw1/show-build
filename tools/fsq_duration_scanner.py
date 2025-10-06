#!/usr/bin/env python3
"""
FSQ Duration Scanner - Check all FSQ cue blocks for duration fields

Scans all rundown .md files and reports FSQ cues that are missing duration fields.
Optionally fixes missing durations by calculating them from word count.
"""

import argparse
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

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


class FSQCueBlock:
    """Represents an FSQ cue block with its data and location."""
    
    def __init__(self, episode: str, segment: str, file_path: Path, start_line: int, end_line: int):
        self.episode = episode
        self.segment = segment
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.fields = {}
        self.has_duration = False
        self.calculated_duration = None
        self.word_count = 0
    
    def __str__(self):
        status = "✅ HAS" if self.has_duration else "❌ MISSING"
        return f"{self.episode}/{self.segment} [{self.fields.get('Slug', 'no-slug')}] - {status} duration"


class FSQDurationScanner:
    """Scans all rundown files for FSQ cue blocks and checks duration fields."""
    
    def __init__(self):
        self.episodes_root = EPISODES_ROOT
        self.fsq_wpm = 120  # Words per minute for FSQ calculations
        self.total_fsqs = 0
        self.fsqs_with_duration = 0
        self.fsqs_missing_duration = 0
        self.all_fsq_blocks = []
    
    def scan_all_episodes(self) -> List[FSQCueBlock]:
        """Scan all episodes for FSQ cue blocks."""
        print(f"🔍 Scanning episodes directory: {self.episodes_root}")
        
        if not self.episodes_root.exists():
            print(f"❌ Episodes directory not found: {self.episodes_root}")
            return []
        
        episode_count = 0
        for episode_dir in self.episodes_root.iterdir():
            if not episode_dir.is_dir() or not episode_dir.name.isdigit():
                continue
            
            episode_count += 1
            episode_number = episode_dir.name
            self._scan_episode(episode_number)
        
        print(f"📁 Scanned {episode_count} episodes")
        return self.all_fsq_blocks
    
    def _scan_episode(self, episode_number: str):
        """Scan a specific episode for FSQ cue blocks."""
        episode_path = self.episodes_root / episode_number
        rundown_path = episode_path / "rundown"
        
        if not rundown_path.exists():
            return
        
        for segment_file in rundown_path.glob("*.md"):
            self._scan_segment_file(episode_number, segment_file)
    
    def _scan_segment_file(self, episode_number: str, segment_file: Path):
        """Scan a segment file for FSQ cue blocks."""
        try:
            content = segment_file.read_text(encoding='utf-8')
            segment_name = segment_file.stem
            
            # Find all FSQ cue blocks
            fsq_blocks = self._extract_fsq_blocks(content, episode_number, segment_name, segment_file)
            self.all_fsq_blocks.extend(fsq_blocks)
            
        except Exception as e:
            print(f"⚠️  Error reading {segment_file}: {e}")
    
    def _extract_fsq_blocks(self, content: str, episode: str, segment: str, file_path: Path) -> List[FSQCueBlock]:
        """Extract all FSQ cue blocks from file content."""
        fsq_blocks = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for cue block start
            if '<!-- Begin Cue -->' in line:
                start_line = i
                cue_lines = []
                i += 1
                
                # Collect cue block lines
                while i < len(lines) and '<!-- End Cue -->' not in lines[i]:
                    cue_lines.append(lines[i])
                    i += 1
                
                if i < len(lines):
                    end_line = i
                    
                    # Parse cue block fields
                    cue_data = self._parse_cue_block(cue_lines)
                    
                    # Check if this is an FSQ cue
                    if cue_data.get('Type') == 'FSQ':
                        fsq_block = FSQCueBlock(episode, segment, file_path, start_line, end_line)
                        fsq_block.fields = cue_data
                        
                        # Check for duration field
                        fsq_block.has_duration = 'Duration' in cue_data and cue_data['Duration'].strip()
                        
                        # Calculate word count and duration
                        quote_text = cue_data.get('Quote', '')
                        fsq_block.word_count = self._count_words(quote_text)
                        fsq_block.calculated_duration = self._calculate_duration(fsq_block.word_count)
                        
                        fsq_blocks.append(fsq_block)
                        self.total_fsqs += 1
                        
                        if fsq_block.has_duration:
                            self.fsqs_with_duration += 1
                        else:
                            self.fsqs_missing_duration += 1
            
            i += 1
        
        return fsq_blocks
    
    def _parse_cue_block(self, cue_lines: List[str]) -> Dict[str, str]:
        """Parse cue block fields."""
        cue_data = {}
        
        for line in cue_lines:
            line = line.strip()
            # Match [Field: Value] pattern
            field_match = re.match(r'^\[([^:]+):\s*(.*)\]$', line)
            if field_match:
                field_name = field_match.group(1).strip()
                field_value = field_match.group(2).strip()
                cue_data[field_name] = field_value
        
        return cue_data
    
    def _count_words(self, text: str) -> int:
        """Count words in text, excluding markdown formatting."""
        if not text:
            return 0
        
        # Remove markdown formatting
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # headers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)        # *italic*
        text = re.sub(r'__([^_]+)__', r'\1', text)          # __bold__
        text = re.sub(r'_([^_]+)_', r'\1', text)            # _italic_
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text) # links
        text = re.sub(r'<[^>]+>', '', text)  # HTML tags
        
        words = text.split()
        return len(words)
    
    def _calculate_duration(self, word_count: int) -> str:
        """Calculate duration from word count using FSQ WPM."""
        if word_count == 0:
            return '00:00'
        
        duration_seconds = round((word_count / self.fsq_wpm) * 60)
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        
        return f"{minutes:02d}:{seconds:02d}"
    
    def print_summary(self):
        """Print scan summary."""
        print("\n" + "=" * 60)
        print("📊 FSQ Duration Scan Summary")
        print("=" * 60)
        print(f"Total FSQ cue blocks found: {self.total_fsqs}")
        print(f"✅ FSQs with duration fields: {self.fsqs_with_duration}")
        print(f"❌ FSQs missing duration fields: {self.fsqs_missing_duration}")
        
        if self.total_fsqs > 0:
            percentage = (self.fsqs_with_duration / self.total_fsqs) * 100
            print(f"📈 Coverage: {percentage:.1f}%")
        
        print()
    
    def print_missing_durations(self):
        """Print details of FSQ blocks missing durations."""
        missing_blocks = [block for block in self.all_fsq_blocks if not block.has_duration]
        
        if not missing_blocks:
            print("🎉 All FSQ cue blocks have duration fields!")
            return
        
        print(f"❌ {len(missing_blocks)} FSQ cue blocks missing duration fields:")
        print("-" * 60)
        
        for block in missing_blocks:
            slug = block.fields.get('Slug', 'no-slug')
            quote_preview = block.fields.get('Quote', '')[:50] + "..." if len(block.fields.get('Quote', '')) > 50 else block.fields.get('Quote', '')
            
            print(f"📁 {block.episode}/{block.segment}")
            print(f"   Slug: {slug}")
            print(f"   Quote: {quote_preview}")
            print(f"   Words: {block.word_count}")
            print(f"   Calculated duration: {block.calculated_duration}")
            print(f"   File: {block.file_path}")
            print(f"   Lines: {block.start_line}-{block.end_line}")
            print()
    
    def fix_missing_durations(self) -> int:
        """Fix FSQ blocks that are missing duration fields."""
        missing_blocks = [block for block in self.all_fsq_blocks if not block.has_duration]
        
        if not missing_blocks:
            print("🎉 No FSQ duration fields need fixing!")
            return 0
        
        print(f"🔧 Fixing {len(missing_blocks)} FSQ cue blocks...")
        fixed_count = 0
        
        for block in missing_blocks:
            try:
                self._fix_fsq_duration(block)
                fixed_count += 1
                print(f"✅ Fixed {block.episode}/{block.segment} [{block.fields.get('Slug', 'no-slug')}]")
            except Exception as e:
                print(f"❌ Failed to fix {block.episode}/{block.segment}: {e}")
        
        print(f"\n🎉 Fixed {fixed_count} FSQ duration fields!")
        return fixed_count
    
    def _fix_fsq_duration(self, block: FSQCueBlock):
        """Fix a single FSQ block by adding the duration field."""
        # Read current file content
        content = block.file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Find the line with <!-- End Cue --> and insert before it
        end_cue_line = None
        for i in range(block.start_line, len(lines)):
            if '<!-- End Cue -->' in lines[i]:
                end_cue_line = i
                break
        
        if end_cue_line is None:
            raise Exception(f"Could not find <!-- End Cue --> after line {block.start_line}")
        
        # Insert the duration field before <!-- End Cue -->
        duration_line = f"[Duration: {block.calculated_duration}]"
        lines.insert(end_cue_line, duration_line)
        
        # Write back to file
        updated_content = '\n'.join(lines)
        block.file_path.write_text(updated_content, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(
        description="Scan rundown files for FSQ cue blocks and check duration fields",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fsq_duration_scanner.py --scan           # Scan only, report results
  python fsq_duration_scanner.py --scan --fix     # Scan and fix missing durations
  python fsq_duration_scanner.py --fix            # Fix without detailed scan output

The scanner will:
1. Find all FSQ cue blocks in all rundown directories
2. Check which ones have duration fields
3. Calculate what the duration should be (based on 120 WPM)
4. Optionally fix missing duration fields
        """
    )
    
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Scan and report FSQ duration status'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Fix FSQ blocks missing duration fields'
    )
    parser.add_argument(
        '--list-missing',
        action='store_true',
        help='List detailed information about missing durations'
    )
    
    args = parser.parse_args()
    
    if not (args.scan or args.fix or args.list_missing):
        parser.print_help()
        sys.exit(1)
    
    print("🎬 FSQ Duration Scanner")
    print("=" * 60)
    print(f"📁 Episodes path: {EPISODES_ROOT}")
    print()
    
    scanner = FSQDurationScanner()
    
    try:
        # Always scan first
        scanner.scan_all_episodes()
        
        if args.scan or args.list_missing:
            scanner.print_summary()
            
        if args.list_missing:
            scanner.print_missing_durations()
        
        if args.fix:
            if scanner.fsqs_missing_duration > 0:
                print(f"🔧 Found {scanner.fsqs_missing_duration} FSQ blocks missing durations")
                print("🔧 Auto-fixing missing duration fields...")
                fixed_count = scanner.fix_missing_durations()
                if fixed_count > 0:
                    print(f"\n✅ Successfully fixed {fixed_count} FSQ duration fields!")
            else:
                print("🎉 All FSQ cue blocks already have duration fields!")
        
        print(f"\n🎉 FSQ duration scan completed!")
        sys.exit(0)
        
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