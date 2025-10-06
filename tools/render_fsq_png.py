#!/usr/bin/env python3
"""
FSQ PNG Renderer - Show-Build Tools Suite

Renders FSQ quotes from JSON as PNG images with transparent backgrounds for video compositing.

Usage:
    python render_fsq_png.py --json="path/to/fsq_quotes.json"
    python render_fsq_png.py --episode=0241
    python render_fsq_png.py --json="file.json" --output="custom_dir"
"""

import argparse
import sys
import json
import textwrap
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import re

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


class FSQPNGRenderer:
    """Renders FSQ quotes as PNG images with transparent backgrounds."""

    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height

        # Design specifications
        self.black_region_height = int(height * 0.8)  # 80% of screen height
        self.black_region_width = width  # 100% of width
        self.black_region_y = (height - self.black_region_height) // 2  # Centered vertically
        self.black_region_x = 0

        # Colors (RGBA for transparency support)
        self.black_overlay = (0, 0, 0, int(255 * 0.75))  # 75% opacity black
        self.text_color = (255, 255, 255, 255)  # White text
        self.attribution_color = (200, 200, 200, 255)  # Light gray attribution

        # Padding (10% of black region dimensions)
        self.padding_x = int(self.black_region_width * 0.1)
        self.padding_y = int(self.black_region_height * 0.1)

        # Content area (inside padding)
        self.content_x = self.black_region_x + self.padding_x
        self.content_y = self.black_region_y + self.padding_y
        self.content_width = self.black_region_width - (2 * self.padding_x)
        self.content_height = self.black_region_height - (2 * self.padding_y)

        # Load fonts
        self.helvetica_font_paths = [
            '/System/Library/Fonts/Helvetica.ttc',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/TTF/arial.ttf',
            'arial.ttf'
        ]

        self.rendered_count = 0
        self.error_count = 0

    def load_font(self, size: int) -> ImageFont.ImageFont:
        """Load Helvetica or fallback font."""
        for font_path in self.helvetica_font_paths:
            try:
                if Path(font_path).exists():
                    return ImageFont.truetype(font_path, size)
            except OSError:
                continue

        # Fallback to default font
        try:
            return ImageFont.load_default()
        except:
            # Ultimate fallback
            return ImageFont.load_default()

    def get_text_dimensions(self, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
        """Get text dimensions using textbbox."""
        # Create temporary draw object for measurement
        temp_img = Image.new('RGBA', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)

        bbox = temp_draw.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height

    def wrap_text_to_fit(self, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
        """Wrap text to fit within max_width, respecting explicit line breaks."""
        # First split by explicit line breaks
        paragraphs = text.split('\n')
        lines = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                # Empty line - add blank line
                lines.append('')
                continue

            # Wrap each paragraph normally
            words = paragraph.split()
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                line_width, _ = self.get_text_dimensions(test_line, font)

                if line_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        # Single word is too long, force it
                        lines.append(word)

            if current_line:
                lines.append(' '.join(current_line))

        return lines

    def calculate_optimal_font_size(self, quote_text: str, attribution: str,
                                  target_width: int, target_height: int) -> Tuple[int, int]:
        """Calculate optimal font sizes for quote and attribution."""
        # Attribution is now fixed at bottom, so quote gets most of the space
        # Reserve space for attribution (about 10% of height) plus some padding
        attribution_space = int(target_height * 0.12)  # Space for attribution + padding
        quote_space = target_height - attribution_space

        # Binary search for optimal quote font size
        min_size, max_size = 12, 200
        best_quote_size = min_size

        while min_size <= max_size:
            mid_size = (min_size + max_size) // 2
            font = self.load_font(mid_size)

            lines = self.wrap_text_to_fit(quote_text, font, target_width)
            line_height = self.get_text_dimensions("Wy", font)[1]  # Height with descenders
            # Calculate total height with mixed line spacing
            total_height = 0
            for line in lines:
                if line.strip():  # Non-empty line
                    total_height += line_height * 1.3  # Slightly increased line spacing
                else:  # Empty line (paragraph break)
                    total_height += line_height * 1.3 * 0.6  # Reduced paragraph spacing

            if total_height <= quote_space:
                best_quote_size = mid_size
                min_size = mid_size + 1
            else:
                max_size = mid_size - 1

        # Attribution font size (smaller)
        attribution_size = max(12, int(best_quote_size * 0.6))

        return best_quote_size, attribution_size

    def render_quote_png(self, quote_data: Dict, output_path: Path) -> bool:
        """Render a single quote as PNG."""
        try:
            print(f"   🎨 Rendering: {quote_data['slug']}")

            # Extract quote data and decode escape characters
            quote_text = quote_data['text'].encode().decode('unicode_escape')
            attribution = quote_data['attribution']
            alignment = quote_data.get('metadata', {}).get('align', 'center').lower()

            print(f"      Text: \"{quote_text[:50]}...\"")
            print(f"      Attribution: {attribution}")
            print(f"      Alignment: {alignment}")

            # Create image with transparent background
            img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Draw black overlay region
            overlay_coords = [
                self.black_region_x,
                self.black_region_y,
                self.black_region_x + self.black_region_width,
                self.black_region_y + self.black_region_height
            ]
            draw.rectangle(overlay_coords, fill=self.black_overlay)

            # Calculate optimal font sizes
            quote_font_size, attribution_font_size = self.calculate_optimal_font_size(
                quote_text, attribution, self.content_width, self.content_height
            )

            quote_font = self.load_font(quote_font_size)
            attribution_font = self.load_font(attribution_font_size)

            print(f"      Quote font size: {quote_font_size}")
            print(f"      Attribution font size: {attribution_font_size}")

            # Wrap quote text
            quote_lines = self.wrap_text_to_fit(quote_text, quote_font, self.content_width)
            line_height = int(self.get_text_dimensions("Wy", quote_font)[1] * 1.3)  # 1.3 for slightly increased line spacing
            paragraph_break_height = int(line_height * 0.6)  # 40% reduction for paragraph breaks

            # Calculate attribution dimensions
            attribution_width, attribution_height = self.get_text_dimensions(attribution, attribution_font)

            # Calculate total content height
            total_quote_height = len(quote_lines) * line_height
            total_content_height = total_quote_height + attribution_height + int(self.content_height * 0.1)

            # Center content vertically in available space
            start_y = self.content_y + (self.content_height - total_content_height) // 2

            # Render quote text
            current_y = start_y
            for line in quote_lines:
                if line.strip():  # Non-empty line
                    line_width, _ = self.get_text_dimensions(line, quote_font)

                    if alignment == 'center':
                        x = self.content_x + (self.content_width - line_width) // 2
                    elif alignment == 'right':
                        x = self.content_x + self.content_width - line_width
                    else:  # left alignment
                        x = self.content_x

                    draw.text((x, current_y), line, font=quote_font, fill=self.text_color)
                    current_y += line_height  # Normal line spacing for text
                else:  # Empty line (paragraph break)
                    current_y += paragraph_break_height  # Reduced spacing for paragraph breaks

            # Render attribution at bottom of black bar with 10% margin
            attribution_text = f"— {attribution}"
            attribution_width, attribution_height = self.get_text_dimensions(attribution_text, attribution_font)

            # Position at bottom of black region with 10% margin from bottom
            attribution_y = (self.black_region_y + self.black_region_height) - self.padding_y - attribution_height

            if alignment == 'center':
                # Attribution bottom right
                attribution_x = self.content_x + self.content_width - attribution_width
            else:
                # Attribution bottom left (for left alignment)
                attribution_x = self.content_x

            draw.text((attribution_x, attribution_y), attribution_text,
                     font=attribution_font, fill=self.attribution_color)

            # Save PNG with transparency
            img.save(output_path, 'PNG', optimize=True)

            print(f"      ✅ Saved: {output_path.name}")
            self.rendered_count += 1
            return True

        except Exception as e:
            print(f"      ❌ Error rendering quote: {e}")
            self.error_count += 1
            return False

    def process_json_file(self, json_path: Path, output_dir: Path) -> bool:
        """Process FSQ JSON file and render all quotes as PNGs."""
        try:
            print(f"📖 Loading JSON: {json_path}")

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            quotes = data.get('quotes', [])
            metadata = data.get('metadata', {})

            print(f"📊 Found {len(quotes)} quotes to render")
            print(f"📁 Output directory: {output_dir}")

            if not quotes:
                print("⚠️  No quotes found in JSON file")
                return True

            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)

            # Render each quote
            for i, quote_data in enumerate(quotes, 1):
                print(f"\n🎨 Rendering quote {i}/{len(quotes)}")

                # Generate output filename
                slug = quote_data.get('slug', f'quote_{i}')
                clean_slug = re.sub(r'[^\w\-]', '', slug.replace(' ', '-'))
                output_filename = f"fsq_{clean_slug}.png"
                output_path = output_dir / output_filename

                self.render_quote_png(quote_data, output_path)

            # Print summary
            print(f"\n📊 Rendering Summary:")
            print(f"   Quotes processed: {len(quotes)}")
            print(f"   Successfully rendered: {self.rendered_count}")
            print(f"   Errors: {self.error_count}")

            return self.error_count == 0

        except Exception as e:
            print(f"❌ Error processing JSON file: {e}")
            return False

    def process_episode(self, episode_number: str, output_dir: Optional[Path] = None) -> bool:
        """Find and process FSQ JSON files for an episode."""
        # Normalize episode number
        if len(episode_number) < 4:
            episode_number = episode_number.zfill(4)

        episode_path = self.episodes_root / episode_number
        quotes_dir = episode_path / "assets" / "quotes"

        if not quotes_dir.exists():
            print(f"❌ Quotes directory not found: {quotes_dir}")
            return False

        # Find FSQ JSON files
        json_files = list(quotes_dir.glob("fsq_quotes_*.json"))

        if not json_files:
            print(f"❌ No FSQ quote JSON files found in {quotes_dir}")
            return False

        print(f"🎬 Processing Episode {episode_number}")
        print(f"📁 Quotes directory: {quotes_dir}")
        print(f"📝 Found {len(json_files)} JSON file(s)")

        # Use default output directory if not specified
        if output_dir is None:
            output_dir = episode_path / "assets" / "quotes"

        success = True
        for json_file in json_files:
            print(f"\n📄 Processing: {json_file.name}")
            if not self.process_json_file(json_file, output_dir):
                success = False

        return success


def main():
    parser = argparse.ArgumentParser(
        description="Render FSQ quotes from JSON as PNG images with transparent backgrounds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python render_fsq_png.py --episode=0241
  python render_fsq_png.py --json="fsq_quotes_0241.json"
  python render_fsq_png.py --json="file.json" --output="custom_output_dir"

Features:
  - Transparent background for video compositing
  - 80% height black overlay with 75% opacity
  - Helvetica font with automatic sizing
  - User-specified text alignment
  - Smart attribution placement
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--episode',
        type=str,
        help='Process episode FSQ quotes (e.g., 0241 or 241)'
    )
    group.add_argument(
        '--json',
        type=str,
        help='Process specific JSON file'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output directory for PNG files (optional)'
    )

    parser.add_argument(
        '--width',
        type=int,
        default=1920,
        help='Image width in pixels (default: 1920)'
    )

    parser.add_argument(
        '--height',
        type=int,
        default=1080,
        help='Image height in pixels (default: 1080)'
    )

    args = parser.parse_args()

    print("🎨 FSQ PNG Renderer - Show-Build Tools")
    print("=" * 60)
    print(f"📐 Output resolution: {args.width}x{args.height}")
    print(f"📁 Episodes path: {EPISODES_ROOT}")
    print()

    renderer = FSQPNGRenderer(width=args.width, height=args.height)
    renderer.episodes_root = EPISODES_ROOT

    try:
        if args.episode:
            output_dir = Path(args.output) if args.output else None
            success = renderer.process_episode(args.episode, output_dir)
        elif args.json:
            json_path = Path(args.json)
            if not json_path.exists():
                print(f"❌ JSON file not found: {json_path}")
                sys.exit(1)

            if args.output:
                output_dir = Path(args.output)
            else:
                output_dir = json_path.parent / "rendered_pngs"

            success = renderer.process_json_file(json_path, output_dir)
        else:
            print("❌ No episode or JSON file specified")
            sys.exit(1)

        if success:
            print(f"\n🎉 FSQ PNG rendering completed!")
            sys.exit(0)
        else:
            print(f"\n💥 FSQ PNG rendering failed")
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