#!/usr/bin/env python3
"""
Quote PDF Renderer
Renders processed quotes as PDFs for the quotes asset directory
"""
import json
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import textwrap

class QuotePDFRenderer:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        # Create custom styles
        self.quote_style = ParagraphStyle(
            'QuoteStyle',
            parent=self.styles['Normal'],
            fontSize=16,
            leading=24,
            spaceBefore=12,
            spaceAfter=12,
            fontName='Times-Roman',
            leftIndent=0.5*inch,
            rightIndent=0.5*inch
        )
        
        self.attribution_style = ParagraphStyle(
            'AttributionStyle',
            parent=self.styles['Normal'],
            fontSize=14,
            leading=18,
            spaceBefore=6,
            spaceAfter=6,
            fontName='Times-Italic',
            alignment=TA_CENTER
        )
        
        self.title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Heading1'],
            fontSize=20,
            leading=24,
            spaceBefore=12,
            spaceAfter=18,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )
    
    def render_quote_pdf(self, quote_data, output_path):
        """Render a single quote as a PDF."""
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=1*inch,
            leftMargin=1*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )
        
        story = []
        
        # Title
        title = f"Full Screen Quote: {quote_data['category'].split('/')[-1]}"
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 0.25*inch))
        
        # Quote text with smart quotes
        quote_text = quote_data['text']
        quote_text = f'"{quote_text}"'
        story.append(Paragraph(quote_text, self.quote_style))
        story.append(Spacer(1, 0.25*inch))
        
        # Attribution
        attribution = f"—{quote_data['attribution']}"
        story.append(Paragraph(attribution, self.attribution_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Metadata section
        metadata_style = ParagraphStyle(
            'MetadataStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            fontName='Helvetica',
            textColor='gray'
        )
        
        story.append(Paragraph("<b>Quote Metadata:</b>", metadata_style))
        story.append(Spacer(1, 0.1*inch))
        
        metadata_items = [
            f"<b>ID:</b> {quote_data['id']}",
            f"<b>Category:</b> {quote_data['category']}",
            f"<b>Source Type:</b> {quote_data['source_type']}",
            f"<b>Word Count:</b> {len(quote_data['text'].split())} words",
            f"<b>Character Count:</b> {len(quote_data['text'])} characters",
        ]
        
        if quote_data.get('tags'):
            metadata_items.append(f"<b>Tags:</b> {', '.join(quote_data['tags'])}")
            
        if quote_data.get('content_warning'):
            metadata_items.append(f"<b>Content Warning:</b> {quote_data['content_warning']}")
        
        for item in metadata_items:
            story.append(Paragraph(item, metadata_style))
            story.append(Spacer(1, 0.05*inch))
        
        # Build PDF
        doc.build(story)
        print(f"✅ Generated PDF: {output_path}")
    
    def process_quote_json(self, json_file_path, output_directory):
        """Process quotes from JSON file and render as PDFs."""
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
            filename = f"{quote_id}.pdf"
            output_path = output_dir / filename
            
            print(f"📄 Rendering quote: {quote_id}")
            self.render_quote_pdf(quote, output_path)
    
    def render_quotes_from_files(self, json_files, output_directory):
        """Render quotes from multiple JSON files."""
        print(f"🎨 Quote PDF Renderer")
        print(f"Output Directory: {output_directory}")
        
        for json_file in json_files:
            if not Path(json_file).exists():
                print(f"❌ File not found: {json_file}")
                continue
            
            print(f"\n📖 Processing: {json_file}")
            self.process_quote_json(json_file, output_directory)
        
        print(f"\n✅ Quote PDF rendering complete!")

def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python render_quotes_pdf.py <output_directory> <json_file1> [json_file2] ...")
        print("Example: python render_quotes_pdf.py /path/to/quotes/assets quote1.json quote2.json")
        sys.exit(1)
    
    output_directory = sys.argv[1]
    json_files = sys.argv[2:]
    
    try:
        renderer = QuotePDFRenderer()
        renderer.render_quotes_from_files(json_files, output_directory)
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install reportlab")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()