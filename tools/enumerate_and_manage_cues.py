#!/usr/bin/env python3
"""
Cue Enumeration and Media Management Script

This script:
1. Iterates through rundown files and enumerates cue blocks by multiples of 10
2. Updates cue slugs with enumerated prefixes (e.g., {GFX/10 tyler-robinson})
3. Renames associated media files to match enumerated slugs
4. Copies media files to scripts/list directory for production workflow

Usage:
    python enumerate_and_manage_cues.py --episode=0241
    python enumerate_and_manage_cues.py --file=path/to/file.md
"""

import argparse
import sys
import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Add paths for imports
tools_dir = Path(__file__).parent
sys.path.insert(0, str(tools_dir))
sys.path.insert(0, str(tools_dir.parent / 'app'))

try:
    from core.paths import ShowBuildPaths
    path_manager = ShowBuildPaths()
    EPISODES_ROOT = path_manager.episodes_root
except ImportError:
    EPISODES_ROOT = Path("/mnt/sync/disaffected/episodes")


class CueEnumerator:
    """Handles cue enumeration and media file management."""

    def __init__(self):
        self.episodes_root = EPISODES_ROOT
        self.processed_files = 0
        self.updated_cues = 0
        self.renamed_files = 0
        self.copied_files = 0
        self.errors = 0

    def extract_cue_blocks(self, content: str) -> List[Tuple[str, Dict[str, str]]]:
        """Extract cue blocks and their fields from markdown content."""
        cue_pattern = r'<!-- Begin Cue -->(.*?)<!-- End Cue -->'
        cues = []

        for match in re.finditer(cue_pattern, content, re.DOTALL):
            cue_content = match.group(1).strip()
            cue_fields = {}

            # Parse cue fields like [Type: GFX], [Slug: name], etc.
            field_pattern = r'\[([^:]+):\s*([^\]]*)\]'
            for field_match in re.finditer(field_pattern, cue_content):
                key = field_match.group(1).strip()
                value = field_match.group(2).strip()
                cue_fields[key] = value

            cues.append((cue_content, cue_fields))

        return cues

    def clean_slug_for_filename(self, slug: str) -> str:
        """Clean slug for use in filename."""
        if not slug:
            return "unknown"

        # Remove enumeration prefix if present (e.g., "GFX/10 " -> "")
        clean_slug = re.sub(r'^[A-Z]+/\d+\s*', '', slug)

        # Convert to lowercase and replace problematic characters
        clean_slug = clean_slug.lower()
        clean_slug = re.sub(r'[^\w\s-]', '', clean_slug)  # Remove special chars
        clean_slug = re.sub(r'[-\s]+', '-', clean_slug)   # Replace spaces with dashes
        clean_slug = clean_slug.strip('-')                # Remove leading/trailing dashes

        return clean_slug if clean_slug else "unknown"

    def generate_enumerated_slug(self, cue_type: str, original_slug: str, index: int) -> str:
        """Generate enumerated slug with prefix."""
        enumeration = index * 10
        clean_slug = self.clean_slug_for_filename(original_slug)
        return f"{cue_type.upper()}/{enumeration:02d} {clean_slug}"

    def generate_media_filename(self, cue_type: str, enumerated_slug: str, original_media_url: str) -> str:
        """Generate new media filename based on enumerated slug."""
        if not original_media_url:
            return ""

        # Extract file extension from original
        original_path = Path(original_media_url)
        extension = original_path.suffix

        # Extract clean slug part (after enumeration prefix)
        slug_part = re.sub(r'^[A-Z]+/\d+\s*', '', enumerated_slug)
        clean_slug = self.clean_slug_for_filename(slug_part)

        # Generate new filename with enumeration
        enumeration_match = re.search(r'(\d+)', enumerated_slug)
        if enumeration_match:
            enum_num = enumeration_match.group(1)
            return f"{enum_num}-{clean_slug}{extension}"

        return f"{clean_slug}{extension}"

    def update_cue_in_content(self, content: str, old_cue: str, new_cue: str) -> str:
        """Replace old cue block with updated one in content."""
        return content.replace(f"<!-- Begin Cue -->{old_cue}<!-- End Cue -->",
                              f"<!-- Begin Cue -->{new_cue}<!-- End Cue -->")

    def rename_and_copy_media_file(self, episode_dir: Path, old_filename: str, new_filename: str) -> bool:
        """Rename media file and copy to scripts/list directory."""
        try:
            # Find the media file in assets
            old_path = None
            for assets_subdir in ['graphics', 'video', 'audio']:
                potential_path = episode_dir / "assets" / assets_subdir / old_filename
                if potential_path.exists():
                    old_path = potential_path
                    break

            if not old_path:
                print(f"   ⚠️  Media file not found: {old_filename}")
                return False

            # Rename in assets directory
            new_path = old_path.parent / new_filename
            if old_path != new_path:
                old_path.rename(new_path)
                print(f"   📄 Renamed: {old_filename} → {new_filename}")
                self.renamed_files += 1

            # Copy to scripts/list directory
            scripts_list_dir = episode_dir / "scripts" / "list"
            scripts_list_dir.mkdir(parents=True, exist_ok=True)

            dest_path = scripts_list_dir / new_filename
            shutil.copy2(new_path, dest_path)
            print(f"   📋 Copied to scripts/list: {new_filename}")
            self.copied_files += 1

            return True

        except Exception as e:
            print(f"   ❌ Error managing media file {old_filename}: {e}")
            self.errors += 1
            return False

    def process_file(self, file_path: Path) -> bool:
        """Process a single rundown file."""
        print(f"\n📄 Processing: {file_path.name}")

        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract cue blocks
            cue_blocks = self.extract_cue_blocks(content)

            if not cue_blocks:
                print("   ⏭️  No cue blocks found")
                return True

            print(f"   📝 Found {len(cue_blocks)} cue block(s)")

            # Process each cue block
            updated_content = content
            cue_index = 1  # Start at 1 for enumeration (10, 20, 30, etc.)

            for original_cue, cue_fields in cue_blocks:
                cue_type = cue_fields.get('Type', '').upper()
                original_slug = cue_fields.get('Slug', '')
                media_url = cue_fields.get('MediaURL', '')

                if cue_type in ['GFX', 'SOT']:
                    # Generate enumerated slug
                    enumerated_slug = self.generate_enumerated_slug(cue_type, original_slug, cue_index)

                    # Create updated cue block with enumerated slug
                    updated_cue = re.sub(
                        r'\[Slug:\s*' + re.escape(original_slug) + r'\]',
                        f'[Slug: {enumerated_slug}]',
                        original_cue
                    )

                    # Handle media file if present
                    if media_url and not media_url.startswith('http'):
                        # Extract filename from MediaURL
                        old_filename = Path(media_url).name
                        new_filename = self.generate_media_filename(cue_type, enumerated_slug, media_url)

                        # Update MediaURL in cue
                        old_media_path = f"../assets/{Path(media_url).parts[-2]}/{old_filename}"
                        new_media_path = f"../assets/{Path(media_url).parts[-2]}/{new_filename}"
                        updated_cue = updated_cue.replace(
                            f'[MediaURL: {media_url}]',
                            f'[MediaURL: {new_media_path}]'
                        )

                        # Rename and copy media file
                        episode_dir = file_path.parent.parent
                        self.rename_and_copy_media_file(episode_dir, old_filename, new_filename)

                    # Update content
                    updated_content = self.update_cue_in_content(updated_content, original_cue, updated_cue)

                    print(f"   🔄 Cue {cue_index}: {original_slug} → {enumerated_slug}")
                    self.updated_cues += 1
                    cue_index += 1
                else:
                    print(f"   ⏭️  Skipping cue type: {cue_type}")

            # Write updated content back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            self.processed_files += 1
            return True

        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
            self.errors += 1
            return False

    def process_episode(self, episode_number: str) -> bool:
        """Process all rundown files for an episode."""
        # Normalize episode number
        if len(episode_number) < 4:
            episode_number = episode_number.zfill(4)

        episode_path = self.episodes_root / episode_number
        rundown_dir = episode_path / "rundown"

        if not rundown_dir.exists():
            print(f"❌ Rundown directory not found: {rundown_dir}")
            return False

        print(f"🎬 Processing Episode {episode_number}")
        print(f"📁 Rundown directory: {rundown_dir}")

        # Get all markdown files in order
        markdown_files = sorted(rundown_dir.glob("*.md"))

        if not markdown_files:
            print("❌ No markdown files found")
            return False

        print(f"📝 Found {len(markdown_files)} rundown file(s)")

        # Process each file
        success = True
        for file_path in markdown_files:
            if not self.process_file(file_path):
                success = False

        return success

    def print_summary(self):
        """Print processing summary."""
        print(f"\n📊 Processing Summary:")
        print(f"   Files processed: {self.processed_files}")
        print(f"   Cues updated: {self.updated_cues}")
        print(f"   Media files renamed: {self.renamed_files}")
        print(f"   Files copied to scripts/list: {self.copied_files}")
        print(f"   Errors: {self.errors}")


def main():
    parser = argparse.ArgumentParser(
        description="Enumerate cue blocks and manage associated media files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enumerate_and_manage_cues.py --episode=0241
  python enumerate_and_manage_cues.py --file=/path/to/rundown/file.md

Features:
  - Enumerates cue blocks by multiples of 10
  - Updates slugs with type prefixes (GFX/10, SOT/20, etc.)
  - Renames media files to match enumerated slugs
  - Copies media files to scripts/list directory
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--episode',
        type=str,
        help='Process all rundown files for an episode (e.g., 0241 or 241)'
    )
    group.add_argument(
        '--file',
        type=str,
        help='Process a specific rundown file'
    )

    args = parser.parse_args()

    print("🎯 Cue Enumerator and Media Manager - Show-Build Tools")
    print("=" * 70)
    print(f"📁 Episodes path: {EPISODES_ROOT}")
    print()

    enumerator = CueEnumerator()

    try:
        if args.episode:
            success = enumerator.process_episode(args.episode)
        elif args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                sys.exit(1)
            success = enumerator.process_file(file_path)
        else:
            print("❌ No episode or file specified")
            sys.exit(1)

        enumerator.print_summary()

        if success and enumerator.errors == 0:
            print(f"\n🎉 Cue enumeration and media management completed successfully!")
            sys.exit(0)
        else:
            print(f"\n⚠️  Completed with errors or warnings")
            sys.exit(1 if enumerator.errors > 0 else 0)

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