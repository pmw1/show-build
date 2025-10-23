#!/usr/bin/env python3
"""
Render a single FSQ quote as PNG.
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont

# Canvas dimensions (1920x1080 for HD)
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

# Black box dimensions (80% height, vertically centered)
BOX_WIDTH = CANVAS_WIDTH
BOX_HEIGHT = int(CANVAS_HEIGHT * 0.80)  # 80% height
BOX_OPACITY = 217  # 85% opacity
BOX_Y = int((CANVAS_HEIGHT - BOX_HEIGHT) / 2)  # Vertically centered

# Padding inside black box (10%)
PADDING = int(BOX_WIDTH * 0.10)

# Text box dimensions
TEXT_BOX_X = PADDING
TEXT_BOX_Y = BOX_Y + PADDING
TEXT_BOX_WIDTH = BOX_WIDTH - (PADDING * 2)
TEXT_BOX_HEIGHT = BOX_HEIGHT - (PADDING * 2)

# Attribution font size
ATTRIBUTION_FONT_SIZE = 32


def find_serif_font():
    """Find serif font on system."""
    font_paths = [
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf',
    ]
    for path in font_paths:
        if os.path.exists(path):
            return path
    raise RuntimeError("No suitable serif font found.")


def calculate_optimal_font_size(text, max_width, max_height, font_path, min_size=28, max_size=90):
    """Calculate optimal font size to fit text in available space."""
    best_size = min_size

    for size in range(max_size, min_size - 1, -2):
        try:
            font = ImageFont.truetype(font_path, size)
            temp_img = Image.new('RGBA', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            wrapped_lines = wrap_text(text, max_width, font, temp_draw)

            total_height = 0
            line_spacing = size * 0.4  # 40% line spacing

            for line in wrapped_lines:
                bbox = temp_draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                total_height += line_height + line_spacing

            total_height -= line_spacing

            if total_height <= max_height:
                best_size = size
                break
        except Exception:
            continue

    return best_size


def wrap_text(text, max_width, font, draw):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines


def render_quote(quote_text, attribution, output_path, font_path):
    """Render a single quote as PNG."""

    # Create canvas with transparent background
    img = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw black box with 85% opacity, vertically centered
    black_box = Image.new('RGBA', (BOX_WIDTH, BOX_HEIGHT), (0, 0, 0, BOX_OPACITY))
    img.paste(black_box, (0, BOX_Y), black_box)

    # Reserve space for attribution
    attribution_reserve = ATTRIBUTION_FONT_SIZE * 3
    available_height = TEXT_BOX_HEIGHT - attribution_reserve

    # Calculate optimal font size
    optimal_size = calculate_optimal_font_size(
        quote_text,
        TEXT_BOX_WIDTH,
        available_height,
        font_path,
        min_size=28,
        max_size=90
    )

    print(f"  Font size: {optimal_size}px")

    # Load fonts
    quote_font = ImageFont.truetype(font_path, optimal_size)
    attribution_font = ImageFont.truetype(font_path, ATTRIBUTION_FONT_SIZE)

    # Wrap quote text
    wrapped_lines = wrap_text(quote_text, TEXT_BOX_WIDTH, quote_font, draw)

    # Calculate total height of wrapped text
    line_spacing = optimal_size * 0.4
    total_text_height = 0
    for line in wrapped_lines:
        bbox = draw.textbbox((0, 0), line, font=quote_font)
        line_height = bbox[3] - bbox[1]
        total_text_height += line_height + line_spacing
    total_text_height -= line_spacing

    # Calculate vertical center position
    y_position = TEXT_BOX_Y + (available_height - total_text_height) / 2

    # Draw quote text (vertically centered)
    for line in wrapped_lines:
        draw.text(
            (TEXT_BOX_X, y_position),
            line,
            font=quote_font,
            fill=(255, 255, 255, 255)
        )
        bbox = draw.textbbox((0, 0), line, font=quote_font)
        line_height = bbox[3] - bbox[1]
        y_position += line_height + line_spacing

    # Draw attribution
    attribution_text = f"—{attribution}"
    attribution_y = BOX_Y + BOX_HEIGHT - PADDING - ATTRIBUTION_FONT_SIZE - 10

    draw.text(
        (TEXT_BOX_X, attribution_y),
        attribution_text,
        font=attribution_font,
        fill=(200, 200, 200, 255)
    )

    # Save PNG
    img.save(output_path, 'PNG')
    print(f"  ✅ Saved: {output_path}")


def main():
    """Render the quote."""

    quote_text = '''William Hendrix, the Kansas Young Republicans' vice chair, used the words "n--ga" and "n--guh," variations of a racial slur, more than a dozen times in the chat. Bobby Walker, the vice chair of the New York State Young Republicans at the time, referred to rape as "epic." Peter Giunta, who at the time was chair of the same organization, wrote in a message sent in June that "everyone that votes no is going to the gas chamber."'''
    attribution = "Politico"
    slug = "william-hendrix"
    output_dir = '/home/episodes/0245/assets/graphics'
    output_path = os.path.join(output_dir, f"{slug}.png")

    print(f"📝 Rendering quote: {slug}")
    print(f"   Attribution: {attribution}")

    try:
        font_path = find_serif_font()
        print(f"   Using font: {font_path}")

        render_quote(quote_text, attribution, output_path, font_path)

        print(f"\n🎉 Done!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
