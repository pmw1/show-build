#!/usr/bin/env python3
"""
FSQ Quote Extractor - Show-Build Tools Suite

Extracts FSQ (Full Screen Quote) cue blocks from rundown markdown files and saves them as JSON
in the episode's assets/quotes directory for further processing.

Usage:
    python extract_fsq_quotes.py --episode=0241
    python extract_fsq_quotes.py --file="path/to/segment.md"
    python extract_fsq_quotes.py --episode=0241 --dry-run
"""

import argparse
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

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


class FSQQuoteExtractor:
    """Extracts FSQ quotes from rundown files and saves as JSON."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.episodes_root = EPISODES_ROOT
        self.extracted_count = 0
        self.files_processed = 0
        self.error_count = 0

    def extract_fsq_cues_from_content(self, content: str, source_file: str) -> List[Dict]:
        """Extract FSQ cue blocks from markdown content."""
        fsq_cues = []

        # Find all cue blocks
        cue_pattern = re.compile(r'<!-- Begin Cue -->(.*?)<!-- End Cue -->', re.DOTALL)
        cue_blocks = cue_pattern.findall(content)

        for i, block in enumerate(cue_blocks):
            # Check if this is an FSQ cue
            type_match = re.search(r'\[Type:\s*(.*?)\]', block, re.IGNORECASE)
            if not type_match or type_match.group(1).strip().upper() != 'FSQ':
                continue

            # Extract all FSQ fields
            fsq_data = self.parse_fsq_fields(block)

            if fsq_data:
                # Add metadata
                fsq_data['source_file'] = source_file
                fsq_data['extraction_date'] = datetime.now().isoformat()
                fsq_data['cue_index'] = i + 1

                fsq_cues.append(fsq_data)

        return fsq_cues

    def parse_fsq_fields(self, block: str) -> Optional[Dict]:
        """Parse FSQ cue block and extract all fields."""
        fsq_data = {}

        # Extract common FSQ fields
        field_patterns = {
            'asset_id': r'\[AssetID:\s*(.*?)\]',
            'slug': r'\[Slug:\s*(.*?)\]',
            'quote': r'\[Quote:\s*(.*?)\]',
            'attribution': r'\[Attribution:\s*(.*?)\]',
            'align': r'\[Align:\s*(.*?)\]',
            'part': r'\[Part:\s*(.*?)\]',
            'word_count': r'\[WordCount:\s*(.*?)\]',
            'duration': r'\[Duration:\s*(.*?)\]',
            'font_size': r'\[FontSize:\s*(.*?)\]',
            'background_color': r'\[BackgroundColor:\s*(.*?)\]',
            'text_color': r'\[TextColor:\s*(.*?)\]',
            'position': r'\[Position:\s*(.*?)\]',
            'animation': r'\[Animation:\s*(.*?)\]',
            'style': r'\[Style:\s*(.*?)\]'
        }

        for field_name, pattern in field_patterns.items():
            match = re.search(pattern, block, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()

                # Clean up quote text (remove escaped quotes)
                if field_name == 'quote':
                    value = value.replace('\\"', '"').replace("\\'", "'")
                    # Remove surrounding quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]

                # Convert numeric fields
                if field_name == 'word_count':
                    try:
                        value = int(value)
                    except ValueError:
                        pass

                fsq_data[field_name] = value

        # Validate required fields
        if not fsq_data.get('quote'):
            return None

        # Generate fallback values for missing fields
        if not fsq_data.get('slug'):
            # Generate slug from quote text
            quote_words = fsq_data['quote'].split()[:5]
            fsq_data['slug'] = '-'.join(word.lower().strip('.,!?";:') for word in quote_words)

        if not fsq_data.get('asset_id'):
            # Generate asset ID from slug and timestamp
            timestamp = int(datetime.now().timestamp())
            fsq_data['asset_id'] = f"fsq_{timestamp}_{fsq_data['slug'][:10]}"

        # Set defaults for common fields
        fsq_data.setdefault('align', 'center')
        fsq_data.setdefault('part', '1x1')
        fsq_data.setdefault('attribution', 'Unknown')

        # Calculate word count if not provided
        if 'word_count' not in fsq_data:
            fsq_data['word_count'] = len(fsq_data['quote'].split())

        # Estimate duration if not provided (based on reading speed)
        if 'duration' not in fsq_data:
            # Assume 120 words per minute reading speed
            words = fsq_data.get('word_count', 0)
            duration_seconds = max(3, int((words / 120) * 60))  # Minimum 3 seconds
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            fsq_data['duration'] = f"{minutes:02d}:{seconds:02d}"

        return fsq_data

    def process_file(self, file_path: Path) -> List[Dict]:
        """Process a single file and extract FSQ quotes."""
        print(f"\n📄 Processing: {file_path.name}")

        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract FSQ cues
            fsq_cues = self.extract_fsq_cues_from_content(content, str(file_path))

            if fsq_cues:
                print(f"   📝 Found {len(fsq_cues)} FSQ quote(s)")
                for i, cue in enumerate(fsq_cues, 1):
                    print(f"      {i}. \"{cue['quote'][:50]}...\" - {cue['attribution']}")
                    print(f"         Slug: {cue['slug']}, Duration: {cue['duration']}")
            else:
                print(f"   ⏭️  No FSQ quotes found")

            self.files_processed += 1
            self.extracted_count += len(fsq_cues)
            return fsq_cues

        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
            self.error_count += 1
            return []

    def save_quotes_json(self, quotes: List[Dict], episode_number: str) -> bool:
        """Save extracted quotes as JSON in assets/quotes directory."""
        if not quotes:
            print("   ⏭️  No quotes to save")
            return True

        episode_path = self.episodes_root / episode_number
        quotes_dir = episode_path / "assets" / "quotes"

        # Create quotes directory if it doesn't exist
        if not self.dry_run:
            quotes_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        quotes_filename = f"fsq_quotes_{episode_number}_{timestamp}.json"
        quotes_file_path = quotes_dir / quotes_filename

        # Prepare JSON structure
        json_data = {
            "metadata": {
                "episode_number": episode_number,
                "extraction_date": datetime.now().isoformat(),
                "total_quotes": len(quotes),
                "content_type": "fsq_quotes",
                "version": "1.0",
                "extractor": "extract_fsq_quotes.py"
            },
            "quotes": []
        }

        # Process each quote for JSON output
        for quote_data in quotes:
            json_quote = {
                "id": quote_data.get('asset_id', ''),
                "slug": quote_data.get('slug', ''),
                "text": quote_data.get('quote', ''),
                "attribution": quote_data.get('attribution', ''),
                "category": f"episode_{episode_number}/fsq",
                "tags": ["fsq", "full_screen_quote", f"episode_{episode_number}"],
                "source_type": "rundown_markdown",
                "priority": "normal",
                "metadata": {
                    "source_file": quote_data.get('source_file', ''),
                    "cue_index": quote_data.get('cue_index', 0),
                    "align": quote_data.get('align', 'center'),
                    "part": quote_data.get('part', '1x1'),
                    "word_count": quote_data.get('word_count', 0),
                    "duration": quote_data.get('duration', '00:05'),
                    "extraction_date": quote_data.get('extraction_date', ''),
                    "style": {
                        "font_size": quote_data.get('font_size'),
                        "background_color": quote_data.get('background_color'),
                        "text_color": quote_data.get('text_color'),
                        "position": quote_data.get('position'),
                        "animation": quote_data.get('animation')
                    }
                }
            }
            json_data["quotes"].append(json_quote)

        # Save JSON file
        if not self.dry_run:
            with open(quotes_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print(f"   💾 Saved quotes to: {quotes_file_path}")
        else:
            print(f"   🔍 [DRY RUN] Would save quotes to: {quotes_file_path}")

        return True

    def process_episode(self, episode_number: str) -> bool:
        """Process all files in an episode and extract FSQ quotes."""
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

        # Process each file and collect all quotes
        all_quotes = []
        for file_path in sorted(markdown_files):
            file_quotes = self.process_file(file_path)
            all_quotes.extend(file_quotes)

        # Save all quotes to JSON
        if all_quotes:
            self.save_quotes_json(all_quotes, episode_number)

        # Print summary
        print(f"\n📊 Episode {episode_number} FSQ Extraction Summary:")
        print(f"   Files processed: {self.files_processed}")
        print(f"   Total FSQ quotes extracted: {self.extracted_count}")
        print(f"   Errors: {self.error_count}")

        return self.extracted_count > 0 or self.files_processed > 0


def main():
    parser = argparse.ArgumentParser(
        description="Extract FSQ quotes from rundown files and save as JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_fsq_quotes.py --episode=0241
  python extract_fsq_quotes.py --file="path/to/segment.md"
  python extract_fsq_quotes.py --episode=0241 --dry-run

The script will:
1. Scan rundown files for FSQ cue blocks
2. Extract quote text, attribution, and metadata
3. Generate JSON file in assets/quotes directory
4. Include all formatting and display parameters
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
        help='Show what would be done without creating files'
    )

    args = parser.parse_args()

    print("📝 FSQ Quote Extractor - Show-Build Tools")
    print("=" * 60)
    print(f"📁 Episodes path: {EPISODES_ROOT}")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be created")
    print()

    extractor = FSQQuoteExtractor(dry_run=args.dry_run)

    try:
        if args.episode:
            success = extractor.process_episode(args.episode)
        elif args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                sys.exit(1)

            quotes = extractor.process_file(file_path)
            # For single file, save with episode number from path
            episode_match = re.search(r'/(\d{4})/', str(file_path))
            if episode_match:
                episode_num = episode_match.group(1)
                extractor.save_quotes_json(quotes, episode_num)
            success = len(quotes) > 0
        else:
            print("❌ No episode or file specified")
            sys.exit(1)

        if success:
            print(f"\n🎉 FSQ quote extraction completed!")
            if args.dry_run:
                print("🔍 This was a dry run - no files were created")
            sys.exit(0)
        else:
            print(f"\n💡 No FSQ quotes found to extract")
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