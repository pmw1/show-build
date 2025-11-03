#!/usr/bin/env python3
"""
Render FSQ quotes as PNG files with transparent backgrounds.
Specs:
- Transparent background
- Black box: 100% width x 75% height at 50% opacity
- 10% padding inside black box = text box
- Quote text: left/top aligned in text box, dynamic font size
- Attribution: bottom left outside text box but inside black box, smaller consistent font
- Font: Helvetica
"""

import json
import sys
from PIL import Image, ImageDraw, ImageFont
import os


# Canvas dimensions (1920x1080 for HD)
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

# Black box dimensions (75% height, vertically centered)
BOX_WIDTH = CANVAS_WIDTH  # 100% width
BOX_HEIGHT = int(CANVAS_HEIGHT * 0.75)  # 75% height
BOX_OPACITY = 204  # 80% opacity (0-255 scale)
BOX_Y = int((CANVAS_HEIGHT - BOX_HEIGHT) / 2)  # Vertically centered

# Padding inside black box (10%)
PADDING = int(BOX_WIDTH * 0.10)

# Text box dimensions (inside padding)
TEXT_BOX_X = PADDING
TEXT_BOX_Y = BOX_Y + PADDING
TEXT_BOX_WIDTH = BOX_WIDTH - (PADDING * 2)
TEXT_BOX_HEIGHT = BOX_HEIGHT - (PADDING * 2)

# Attribution font size (consistent)
ATTRIBUTION_FONT_SIZE = 37  # Increased from 32 by 5pt


def find_serif_font():
    """Find serif font on system."""
    font_paths = [
        # Linux serif fonts
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
    ]

    for path in font_paths:
        if os.path.exists(path):
            return path

    raise RuntimeError("No suitable serif font found. Install liberation-fonts or dejavu-fonts.")


def calculate_optimal_font_size(text, max_width, max_height, font_path, min_size=20, max_size=100):
    """Calculate optimal font size to fit text in available space."""

    # Binary search for optimal font size
    best_size = min_size

    for size in range(max_size, min_size - 1, -2):
        try:
            font = ImageFont.truetype(font_path, size)

            # Create temporary draw context to measure text
            temp_img = Image.new('RGBA', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)

            # Wrap text and measure
            wrapped_lines = wrap_text(text, max_width, font, temp_draw)

            # Calculate total height
            total_height = 0
            line_spacing = size * 0.25  # 25% line spacing (increased from 15%)

            for line in wrapped_lines:
                bbox = temp_draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                total_height += line_height + line_spacing

            total_height -= line_spacing  # Remove last line spacing

            # Check if it fits
            if total_height <= max_height:
                best_size = size
                break

        except Exception as e:
            print(f"Warning: Error testing font size {size}: {e}")
            continue

    return best_size


def wrap_text(text, max_width, font, draw):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        # Test with this word added
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line.append(word)
        else:
            # Line is full, start new line
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    # Add last line
    if current_line:
        lines.append(' '.join(current_line))

    return lines


def render_quote(quote_data, output_path, font_path):
    """Render a single quote as PNG."""

    # Create canvas with transparent background
    img = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw black box with 85% opacity, vertically centered
    black_box = Image.new('RGBA', (BOX_WIDTH, BOX_HEIGHT), (0, 0, 0, BOX_OPACITY))
    img.paste(black_box, (0, BOX_Y), black_box)

    # Calculate optimal font size for quote text
    quote_text = quote_data['quote']

    # Reserve space for attribution (bottom of text box area)
    # Need: minimal spacing + attribution line
    attribution_reserve = ATTRIBUTION_FONT_SIZE * 2.0  # Minimal: Reserve 2 lines for spacing + attribution
    available_height = TEXT_BOX_HEIGHT - attribution_reserve

    optimal_size = calculate_optimal_font_size(
        quote_text,
        TEXT_BOX_WIDTH,
        available_height,
        font_path,
        min_size=40,   # Increased minimum to make all quotes larger
        max_size=150   # Maximum possible quote font size
    )

    print(f"  Font size: {optimal_size}px")

    # Load fonts
    quote_font = ImageFont.truetype(font_path, optimal_size)
    attribution_font = ImageFont.truetype(font_path, ATTRIBUTION_FONT_SIZE)

    # Wrap quote text
    wrapped_lines = wrap_text(quote_text, TEXT_BOX_WIDTH, quote_font, draw)

    # Calculate total height of wrapped text
    line_spacing = optimal_size * 0.25  # 25% line spacing (increased from 15%)
    total_text_height = 0
    for line in wrapped_lines:
        bbox = draw.textbbox((0, 0), line, font=quote_font)
        line_height = bbox[3] - bbox[1]
        total_text_height += line_height + line_spacing
    total_text_height -= line_spacing  # Remove last line spacing

    # Calculate vertical center position
    y_position = TEXT_BOX_Y + (available_height - total_text_height) / 2

    # Draw quote text (left-aligned, vertically centered)
    for line in wrapped_lines:
        draw.text(
            (TEXT_BOX_X, y_position),
            line,
            font=quote_font,
            fill=(255, 255, 255, 255)  # White text
        )
        bbox = draw.textbbox((0, 0), line, font=quote_font)
        line_height = bbox[3] - bbox[1]
        y_position += line_height + line_spacing

    # Draw attribution (bottom-left inside black box with 10% margin)
    attribution_text = f"—{quote_data['attribution']}"
    attribution_margin = int(BOX_WIDTH * 0.10)  # 10% margin from edges
    attribution_x = attribution_margin  # 10% from left edge of black box
    attribution_y = BOX_Y + BOX_HEIGHT - attribution_margin - ATTRIBUTION_FONT_SIZE  # 10% from bottom

    draw.text(
        (attribution_x, attribution_y),
        attribution_text,
        font=attribution_font,
        fill=(200, 200, 200, 255)  # Light gray text
    )

    # Save PNG
    img.save(output_path, 'PNG')
    print(f"  ✅ Saved: {output_path}")


def main():
    """Render all quotes from JSON file."""

    json_path = '/mnt/sync/disaffected/episodes/0247/fs_quotes_extracted.json'
    output_dir = '/mnt/sync/disaffected/episodes/0247/assets/graphics'

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Find font
    try:
        font_path = find_serif_font()
        print(f"📝 Using font: {font_path}")
    except RuntimeError as e:
        print(f"❌ {e}")
        return False

    # Load quotes
    print(f"📖 Loading quotes from: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        quotes = json.load(f)

    print(f"✅ Found {len(quotes)} quotes to render\n")

    # Render each quote
    for i, quote in enumerate(quotes, 1):
        slug = quote['slug']
        output_path = os.path.join(output_dir, f"{slug}.png")

        print(f"{i}/{len(quotes)}: Rendering '{slug}'")
        print(f"  Words: {quote['wordCount']} | Attribution: {quote['attribution']}")

        try:
            render_quote(quote, output_path, font_path)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            continue

        print()

    print(f"🎉 Done! Rendered {len(quotes)} quote PNGs to {output_dir}")
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
