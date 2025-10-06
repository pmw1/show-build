#!/usr/bin/env python3
"""
Quote PNG Renderer
Renders processed quotes as PNG images using Pillow for broadcast graphics
"""
import json
import os
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

class QuotePNGRenderer:
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        self.background_color = (26, 26, 26)  # Dark background
        self.text_color = (255, 255, 255)     # White text
        self.attribution_color = (200, 200, 200)  # Light gray attribution
        
        # Try to load fonts
        self.quote_font = self._load_font(48)
        self.attribution_font = self._load_font(36)
        self.metadata_font = self._load_font(24)
        
    def _load_font(self, size):
        """Try to load a system font."""
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/System/Library/Fonts/Arial.ttf',
            'arial.ttf'
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except OSError:
                continue
        
        # Fallback to default font
        try:
            return ImageFont.load_default()
        except:
            return None
    
    def _wrap_text(self, text, font, max_width):
        """Wrap text to fit within max_width."""
        if not font:
            # Estimate characters per line if no font available
            chars_per_line = max_width // 20
            return textwrap.fill(text, width=chars_per_line).split('\n')
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # Single word is too long, force it
                    lines.append(word)
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _get_text_height(self, text, font):
        """Get the height of text."""
        if not font:
            return 30  # Fallback height
        bbox = font.getbbox(text)
        return bbox[3] - bbox[1]
    
    def render_quote_png(self, quote_data, output_path):
        """Render a single quote as a PNG."""
        # Create image
        img = Image.new('RGB', (self.width, self.height), self.background_color)
        draw = ImageDraw.Draw(img)

        # Calculate layout - 10% margins on each side
        margin = int(self.width * 0.1)  # 10% of width for each margin
        content_width = self.width - (2 * margin)

        # Quote text with quotes - left aligned and vertically centered
        # Process escape characters
        raw_text = quote_data["text"]
        # Handle newline escape sequences
        processed_text = raw_text.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'")
        quote_text = f'"{processed_text}"'
        quote_lines = self._wrap_text(quote_text, self.quote_font, content_width)

        # Calculate total height of quote text - increased line spacing
        line_height = self._get_text_height("Sample", self.quote_font) + 20 if self.quote_font else 60
        total_quote_height = len(quote_lines) * line_height

        # Add attribution height
        attribution_text = f"—{quote_data['attribution']}"
        attribution_height = self._get_text_height(attribution_text, self.attribution_font) if self.attribution_font else 40

        # Calculate starting Y to center vertically
        total_content_height = total_quote_height + 40 + attribution_height
        start_y = (self.height - total_content_height) // 2

        current_y = start_y

        # Render quote lines - left aligned
        for line in quote_lines:
            if self.quote_font:
                draw.text((margin, current_y), line,
                         fill=self.text_color, font=self.quote_font)
                current_y += self._get_text_height(line, self.quote_font) + 20
            else:
                # Fallback without font
                draw.text((margin, current_y), line, fill=self.text_color)
                current_y += 60

        current_y += 40

        # Attribution - left aligned
        if self.attribution_font:
            draw.text((margin, current_y), attribution_text,
                     fill=self.attribution_color, font=self.attribution_font)

        # Save PNG
        img.save(output_path, 'PNG', optimize=True)
        print(f"✅ Generated PNG: {output_path}")
    
    def process_quote_json(self, json_file_path, output_directory):
        """Process quotes from JSON file and render as PNGs."""
        # Read JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        quotes = data.get('quotes', [])
        if not quotes:
            print(f"No quotes found in {json_file_path}")
            return
        
        # Create output directory if it doesn't exist
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Render each quote
        for quote in quotes:
            quote_id = quote['id']
            filename = f"{quote_id}.png"
            output_path = output_dir / filename
            
            print(f"🖼️ Rendering quote PNG: {quote_id}")
            self.render_quote_png(quote, output_path)
    
    def render_quotes_from_files(self, json_files, output_directory):
        """Render quotes from multiple JSON files."""
        print(f"🎨 Quote PNG Renderer")
        print(f"Output Directory: {output_directory}")
        print(f"Resolution: {self.width}x{self.height}")
        
        for json_file in json_files:
            if not Path(json_file).exists():
                print(f"❌ File not found: {json_file}")
                continue
            
            print(f"\n📖 Processing: {json_file}")
            self.process_quote_json(json_file, output_directory)
        
        print(f"\n✅ Quote PNG rendering complete!")

def main():
    if len(sys.argv) < 3:
        print("Usage: python render_quotes_png.py <output_directory> <json_file1> [json_file2] ...")
        print("Example: python render_quotes_png.py /path/to/quotes/assets quote1.json quote2.json")
        sys.exit(1)
    
    output_directory = sys.argv[1]
    json_files = sys.argv[2:]
    
    try:
        renderer = QuotePNGRenderer()
        renderer.render_quotes_from_files(json_files, output_directory)
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install Pillow")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()