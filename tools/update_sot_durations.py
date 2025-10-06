#!/usr/bin/env python3
"""
SOT Duration Updater - Show-Build Tools Suite

Scans rundown segments for SOT cue blocks, uses ffprobe to get actual media durations,
and updates the duration fields in both the cue blocks and frontmatter.

Usage:
    python update_sot_durations.py --episode=0241
    python update_sot_durations.py --file="path/to/segment.md"
    python update_sot_durations.py --episode=0241 --dry-run
"""

import argparse
import sys
import re
import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple

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


class SOTDurationUpdater:
    """Updates SOT durations using ffprobe and updates frontmatter."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.episodes_root = EPISODES_ROOT
        self.updated_count = 0
        self.error_count = 0
        self.skipped_count = 0

    def get_media_duration_ffprobe(self, media_path: Path) -> Optional[str]:
        """Use ffprobe to get actual media duration."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(media_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            duration_seconds = float(data['format']['duration'])

            # Convert to HH:MM:SS format
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            seconds = int(duration_seconds % 60)

            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        except subprocess.CalledProcessError as e:
            print(f"   ❌ ffprobe error: {e}")
            return None
        except FileNotFoundError:
            print(f"   ❌ ffprobe not found. Please install FFmpeg.")
            return None
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"   ❌ Error parsing ffprobe output: {e}")
            return None

    def resolve_media_path(self, media_url: str, markdown_file_path: Path) -> Optional[Path]:
        """Resolve media URL to absolute file path."""
        # If it's already an absolute path, return it
        if Path(media_url).is_absolute():
            return Path(media_url)

        # Handle relative paths (like ../assets/video/filename.mp4)
        if media_url.startswith('../'):
            # Resolve relative to the markdown file's directory
            base_dir = markdown_file_path.parent
            resolved_path = (base_dir / media_url).resolve()
            return resolved_path

        # Handle paths that start with assets/ (relative to episode root)
        if media_url.startswith('assets/'):
            episode_dir = markdown_file_path.parent.parent  # rundown -> episode
            return episode_dir / media_url

        # Handle URLs or other formats - for now just return as-is
        return Path(media_url)

    def extract_sot_cues_from_content(self, content: str) -> List[Dict]:
        """Extract SOT cue blocks from markdown content."""
        sot_cues = []

        # Find all cue blocks
        cue_pattern = re.compile(r'<!-- Begin Cue -->(.*?)<!-- End Cue -->', re.DOTALL)
        cue_blocks = cue_pattern.findall(content)

        for i, block in enumerate(cue_blocks):
            # Check if this is an SOT cue
            type_match = re.search(r'\[Type:\s*(.*?)\]', block, re.IGNORECASE)
            if not type_match or type_match.group(1).strip().upper() != 'SOT':
                continue

            # Extract fields
            slug_match = re.search(r'\[Slug:\s*(.*?)\]', block, re.IGNORECASE)
            asset_id_match = re.search(r'\[AssetID:\s*(.*?)\]', block, re.IGNORECASE)
            media_url_match = re.search(r'\[MediaURL:\s*(.*?)\]', block, re.IGNORECASE)
            duration_match = re.search(r'\[Duration:\s*(.*?)\]', block, re.IGNORECASE)

            slug = slug_match.group(1).strip() if slug_match else f"sot-{i+1}"
            asset_id = asset_id_match.group(1).strip() if asset_id_match else ""
            media_url = media_url_match.group(1).strip() if media_url_match else ""
            current_duration = duration_match.group(1).strip() if duration_match else ""

            sot_cues.append({
                'index': i,
                'slug': slug,
                'asset_id': asset_id,
                'media_url': media_url,
                'current_duration': current_duration,
                'block_text': block,
                'full_block': f"<!-- Begin Cue -->{block}<!-- End Cue -->"
            })

        return sot_cues

    def update_sot_cue_duration(self, content: str, sot_cue: Dict, new_duration: str) -> str:
        """Update duration in a specific SOT cue block."""
        old_block = sot_cue['full_block']

        # Update duration field in the block
        block_text = sot_cue['block_text']

        if re.search(r'\[Duration:\s*.*?\]', block_text, re.IGNORECASE):
            # Replace existing duration
            updated_block = re.sub(
                r'\[Duration:\s*.*?\]',
                f'[Duration: {new_duration}]',
                block_text,
                flags=re.IGNORECASE
            )
        else:
            # Add duration field before the end comment
            updated_block = block_text.strip() + f'\n[Duration: {new_duration}]'

        new_full_block = f"<!-- Begin Cue -->{updated_block}<!-- End Cue -->"

        # Replace in content
        updated_content = content.replace(old_block, new_full_block)
        return updated_content

    def update_frontmatter_duration(self, content: str, new_duration: str) -> str:
        """Update duration field in YAML frontmatter."""
        lines = content.split('\n')
        updated_lines = []
        in_frontmatter = False
        frontmatter_end_found = False
        duration_updated = False

        for i, line in enumerate(lines):
            # Detect frontmatter boundaries
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                elif in_frontmatter and not frontmatter_end_found:
                    frontmatter_end_found = True
                    in_frontmatter = False

            # Update duration field if we're in frontmatter
            if in_frontmatter and not frontmatter_end_found:
                duration_match = re.match(r'^(\s*duration:\s*)(.*?)(\s*)$', line)
                if duration_match:
                    indent = duration_match.group(1)
                    trailing_space = duration_match.group(3)
                    new_line = f'{indent}{new_duration}{trailing_space}'
                    updated_lines.append(new_line)
                    duration_updated = True
                    continue

            updated_lines.append(line)

        # If no duration field was found but we have frontmatter, add it
        if not duration_updated and frontmatter_end_found:
            # Find the end of frontmatter and insert duration field before it
            for i, line in enumerate(updated_lines):
                if line.strip() == '---' and i > 0:  # This is the closing ---
                    updated_lines.insert(i, f'duration: {new_duration}')
                    break

        return '\n'.join(updated_lines)

    def process_segment_file(self, segment_file: Path) -> bool:
        """Process a single segment file for SOT duration updates."""
        print(f"\n📄 Processing: {segment_file.name}")

        try:
            # Read file content
            with open(segment_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract SOT cues
            sot_cues = self.extract_sot_cues_from_content(content)

            if not sot_cues:
                print(f"   ⏭️  No SOT cues found")
                self.skipped_count += 1
                return True

            print(f"   🎬 Found {len(sot_cues)} SOT cue(s)")

            updated_content = content
            segment_updated = False
            total_duration_seconds = 0.0

            # Process each SOT cue
            for sot_cue in sot_cues:
                print(f"   📹 SOT: {sot_cue['slug']}")
                print(f"      Media: {sot_cue['media_url']}")
                print(f"      Current duration: {sot_cue['current_duration'] or 'None'}")

                if not sot_cue['media_url']:
                    print(f"      ⏭️  No media URL specified")
                    continue

                # Resolve media path
                media_path = self.resolve_media_path(sot_cue['media_url'], segment_file)

                if not media_path or not media_path.exists():
                    print(f"      ❌ Media file not found: {media_path}")
                    self.error_count += 1
                    continue

                # Get duration using ffprobe
                actual_duration = self.get_media_duration_ffprobe(media_path)

                if not actual_duration:
                    print(f"      ❌ Could not determine duration")
                    self.error_count += 1
                    continue

                print(f"      ✅ Actual duration: {actual_duration}")

                # Update cue block duration if different
                if sot_cue['current_duration'] != actual_duration:
                    if not self.dry_run:
                        updated_content = self.update_sot_cue_duration(
                            updated_content, sot_cue, actual_duration
                        )
                    segment_updated = True
                    print(f"      📝 Updated cue duration: {sot_cue['current_duration']} → {actual_duration}")
                else:
                    print(f"      ✅ Duration already correct")

                # Add to total for frontmatter
                duration_parts = actual_duration.split(':')
                if len(duration_parts) == 3:
                    hours, minutes, seconds = map(int, duration_parts)
                    total_duration_seconds += hours * 3600 + minutes * 60 + seconds

            # Update frontmatter duration with total SOT duration
            if segment_updated and total_duration_seconds > 0:
                hours = int(total_duration_seconds // 3600)
                minutes = int((total_duration_seconds % 3600) // 60)
                seconds = int(total_duration_seconds % 60)
                total_duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                if not self.dry_run:
                    updated_content = self.update_frontmatter_duration(
                        updated_content, total_duration_formatted
                    )
                print(f"   📝 Updated frontmatter duration: {total_duration_formatted}")

            # Write updated content back to file
            if segment_updated and not self.dry_run:
                with open(segment_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                print(f"   ✅ File updated")
                self.updated_count += 1
            elif segment_updated and self.dry_run:
                print(f"   🔍 [DRY RUN] Would update file")
                self.updated_count += 1
            else:
                print(f"   ⏭️  No changes needed")
                self.skipped_count += 1

            return True

        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
            self.error_count += 1
            return False

    def process_episode(self, episode_number: str) -> bool:
        """Process all segments in an episode."""
        # Normalize episode number to 4 digits
        if len(episode_number) < 4:
            episode_number = episode_number.zfill(4)

        episode_path = self.episodes_root / episode_number
        rundown_path = episode_path / "rundown"

        if not episode_path.exists():
            print(f"❌ Episode {episode_number} not found at {episode_path}")
            return False

        if not rundown_path.exists():
            print(f"❌ Rundown directory not found at {rundown_path}")
            return False

        print(f"🎬 Processing Episode {episode_number}")
        print(f"📁 Rundown: {rundown_path}")

        segment_files = list(rundown_path.glob("*.md"))
        if not segment_files:
            print(f"❌ No segment files found")
            return False

        print(f"📝 Found {len(segment_files)} segment files")

        # Process each segment file
        success_count = 0
        for segment_file in sorted(segment_files):
            if self.process_segment_file(segment_file):
                success_count += 1

        # Print summary
        print(f"\n📊 Episode {episode_number} Summary:")
        print(f"   Files processed: {success_count}/{len(segment_files)}")
        print(f"   Files updated: {self.updated_count}")
        print(f"   Files skipped: {self.skipped_count}")
        print(f"   Errors: {self.error_count}")

        return success_count > 0


def main():
    parser = argparse.ArgumentParser(
        description="Update SOT durations using ffprobe and update frontmatter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_sot_durations.py --episode=0241
  python update_sot_durations.py --file="path/to/segment.md"
  python update_sot_durations.py --episode=0241 --dry-run

The script will:
1. Scan rundown segments for SOT cue blocks
2. Use ffprobe to get actual media durations
3. Update duration fields in cue blocks
4. Update frontmatter duration with total SOT time
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--episode',
        type=str,
        help='Process all segments in episode (e.g., 0241 or 241)'
    )
    group.add_argument(
        '--file',
        type=str,
        help='Process single segment file'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    print("🎬 SOT Duration Updater - Show-Build Tools")
    print("=" * 60)
    print(f"📁 Episodes path: {EPISODES_ROOT}")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
    print()

    updater = SOTDurationUpdater(dry_run=args.dry_run)

    try:
        if args.episode:
            success = updater.process_episode(args.episode)
        elif args.file:
            segment_file = Path(args.file)
            if not segment_file.exists():
                print(f"❌ File not found: {segment_file}")
                sys.exit(1)
            success = updater.process_segment_file(segment_file)
        else:
            print("❌ No episode or file specified")
            sys.exit(1)

        if success:
            print(f"\n🎉 SOT duration update completed!")
            if args.dry_run:
                print("🔍 This was a dry run - no files were actually modified")
            sys.exit(0)
        else:
            print(f"\n💥 SOT duration update failed")
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