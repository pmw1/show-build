#!/usr/bin/env python3
"""
Rename Files by Slug - Show-Build Tools Suite

Renames rundown markdown files to use their slug while preserving enumeration.
Format: {index:03d}-{type}-{slug}.md

Usage:
    python rename_files_by_slug.py --episode=0241
    python rename_files_by_slug.py --file="path/to/segment.md"
    python rename_files_by_slug.py --episode=0241 --dry-run
"""

import argparse
import sys
import re
from pathlib import Path
from typing import Optional, Dict, List

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


class FileRenamer:
    """Renames files based on their slug while preserving enumeration."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.episodes_root = EPISODES_ROOT
        self.renamed_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def extract_frontmatter_field(self, content: str, field_name: str) -> Optional[str]:
        """Extract a field value from YAML frontmatter."""
        lines = content.split('\n')
        in_frontmatter = False

        for line in lines:
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    break  # End of frontmatter

            if in_frontmatter:
                # Match field: value pattern
                match = re.match(f'^{field_name}:\\s*(.*)$', line, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    return value if value else None

        return None

    def extract_index_from_filename(self, filename: str) -> Optional[int]:
        """Extract numeric index from filename."""
        match = re.match(r'^(\d+)', filename)
        return int(match.group(1)) if match else None

    def clean_slug_for_filename(self, slug: str) -> str:
        """Clean slug for use in filename."""
        if not slug:
            return "untitled"

        # Convert to lowercase and replace problematic characters
        clean_slug = slug.lower()
        clean_slug = re.sub(r'[^\w\s-]', '', clean_slug)  # Remove special chars except spaces and dashes
        clean_slug = re.sub(r'[-\s]+', '-', clean_slug)   # Replace spaces and multiple dashes with single dash
        clean_slug = clean_slug.strip('-')                # Remove leading/trailing dashes

        # Limit length
        if len(clean_slug) > 40:
            clean_slug = clean_slug[:40].rstrip('-')

        return clean_slug if clean_slug else "untitled"

    def generate_new_filename(self, index: int, item_type: str, slug: str) -> str:
        """Generate new filename based on index, type, and slug."""
        clean_slug = self.clean_slug_for_filename(slug)

        # Only include type prefix for special types, skip for regular segments
        if item_type and item_type.lower() not in ['segment', 'unknown']:
            clean_type = self.clean_slug_for_filename(item_type)
            return f"{index:03d}-{clean_type}-{clean_slug}.md"
        else:
            return f"{index:03d}-{clean_slug}.md"

    def process_file(self, file_path: Path) -> bool:
        """Process a single file for renaming."""
        print(f"\n📄 Processing: {file_path.name}")

        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract metadata
            slug = self.extract_frontmatter_field(content, 'slug')
            item_type = self.extract_frontmatter_field(content, 'type')
            index = self.extract_index_from_filename(file_path.name)

            print(f"   📊 Index: {index}")
            print(f"   🏷️  Type: {item_type}")
            print(f"   🔗 Slug: {slug}")

            if not index:
                print(f"   ⚠️  Could not extract index from filename")
                self.error_count += 1
                return False

            if not slug:
                print(f"   ⚠️  No slug found in frontmatter")
                self.error_count += 1
                return False

            # Generate new filename
            new_filename = self.generate_new_filename(index, item_type, slug)
            new_file_path = file_path.parent / new_filename

            print(f"   ➡️  New filename: {new_filename}")

            # Check if rename is needed
            if file_path.name == new_filename:
                print(f"   ✅ Filename already correct")
                self.skipped_count += 1
                return True

            # Check if target file already exists
            if new_file_path.exists():
                print(f"   ❌ Target file already exists: {new_filename}")
                self.error_count += 1
                return False

            # Perform rename
            if not self.dry_run:
                file_path.rename(new_file_path)
                print(f"   ✅ Renamed to: {new_filename}")
            else:
                print(f"   🔍 [DRY RUN] Would rename to: {new_filename}")

            self.renamed_count += 1
            return True

        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
            self.error_count += 1
            return False

    def process_episode(self, episode_number: str) -> bool:
        """Process all files in an episode."""
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

        # Get all markdown files
        markdown_files = list(rundown_path.glob("*.md"))
        if not markdown_files:
            print(f"❌ No markdown files found")
            return False

        print(f"📝 Found {len(markdown_files)} markdown files")

        # Sort by filename to process in order
        markdown_files.sort()

        # Process each file
        success_count = 0
        for file_path in markdown_files:
            if self.process_file(file_path):
                success_count += 1

        # Print summary
        print(f"\n📊 Episode {episode_number} Summary:")
        print(f"   Files processed: {success_count}/{len(markdown_files)}")
        print(f"   Files renamed: {self.renamed_count}")
        print(f"   Files skipped: {self.skipped_count}")
        print(f"   Errors: {self.error_count}")

        return success_count > 0


def main():
    parser = argparse.ArgumentParser(
        description="Rename rundown files based on their slug while preserving enumeration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rename_files_by_slug.py --episode=0241
  python rename_files_by_slug.py --file="path/to/segment.md"
  python rename_files_by_slug.py --episode=0241 --dry-run

The script will:
1. Extract slug, type, and index from each file
2. Generate new filename: {index:03d}-{type}-{slug}.md
3. Rename files to match their content
4. Preserve enumeration order
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--episode',
        type=str,
        help='Process all files in episode (e.g., 0241 or 241)'
    )
    group.add_argument(
        '--file',
        type=str,
        help='Process single file'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    print("📁 File Renamer by Slug - Show-Build Tools")
    print("=" * 60)
    print(f"📁 Episodes path: {EPISODES_ROOT}")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be renamed")
    print()

    renamer = FileRenamer(dry_run=args.dry_run)

    try:
        if args.episode:
            success = renamer.process_episode(args.episode)
        elif args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                sys.exit(1)
            success = renamer.process_file(file_path)
        else:
            print("❌ No episode or file specified")
            sys.exit(1)

        if success:
            print(f"\n🎉 File renaming completed!")
            if args.dry_run:
                print("🔍 This was a dry run - no files were actually renamed")
            sys.exit(0)
        else:
            print(f"\n💥 File renaming failed")
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