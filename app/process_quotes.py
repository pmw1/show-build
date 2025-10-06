#!/usr/bin/env python3
"""
Quote Processing Tool for Show-Build
Processes JSON quote files and inserts them into the extracted_quotes database table
"""

import json
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add app directory to path for Show-Build imports
sys.path.insert(0, str(Path(__file__).parent / 'app'))

from database import get_db
# from models import ExtractedQuote
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_word_count(text: str) -> int:
    """Calculate word count for quote text"""
    return len(text.split())

def calculate_character_count(text: str) -> int:
    """Calculate character count for quote text"""
    return len(text)

def generate_slug(category: str, quote_id: str) -> str:
    """Generate a slug from category and quote ID"""
    # Extract the part after the slash from category
    if '/' in category:
        category_part = category.split('/')[-1]
    else:
        category_part = category
    
    # Create slug from category and ID
    slug = f"{category_part.lower().replace(' ', '-')}-{quote_id.lower()}"
    return slug[:100]  # Limit to 100 characters

def process_quotes_json(json_file_path: str, episode_id: int = None) -> bool:
    """
    Process quotes from JSON file and insert into database
    
    Args:
        json_file_path: Path to the JSON file containing quotes
        episode_id: Episode ID to associate quotes with (optional)
    
    Returns:
        bool: True if processing was successful
    """
    try:
        # Read JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        quotes = data.get('quotes', [])
        metadata = data.get('metadata', {})
        
        logger.info(f"Processing {len(quotes)} quotes from {json_file_path}")
        
        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        try:
            processed_count = 0
            
            for quote_data in quotes:
                try:
                    # Extract quote fields
                    quote_id = quote_data.get('id', 'unknown')
                    category = quote_data.get('category', 'uncategorized')
                    text = quote_data.get('text', '')
                    attribution = quote_data.get('attribution', '')
                    
                    # Generate slug
                    slug = generate_slug(category, quote_id)
                    
                    # Calculate counts
                    word_count = calculate_word_count(text)
                    character_count = calculate_character_count(text)
                    
                    # Create context from additional metadata
                    context_data = {
                        'category': category,
                        'tags': quote_data.get('tags', []),
                        'content_warning': quote_data.get('content_warning'),
                        'priority': quote_data.get('priority'),
                        'source_type': quote_data.get('source_type'),
                        'metadata': metadata
                    }
                    context = json.dumps(context_data)
                    
                    # Check if quote already exists
                    existing_quote = db.query(ExtractedQuote).filter(
                        ExtractedQuote.quote_id == quote_id
                    ).first()
                    
                    if existing_quote:
                        logger.info(f"Quote {quote_id} already exists, updating...")
                        # Update existing quote
                        existing_quote.text = text
                        existing_quote.attribution = attribution
                        existing_quote.context = context
                        existing_quote.word_count = word_count
                        existing_quote.character_count = character_count
                        existing_quote.updated_at = datetime.utcnow()
                        existing_quote.source_file = json_file_path
                    else:
                        # Create new quote record
                        new_quote = ExtractedQuote(
                            episode_id=episode_id or 1,  # Default to episode 1 if not specified
                            quote_id=quote_id,
                            slug=slug,
                            text=text,
                            attribution=attribution,
                            context=context,
                            word_count=word_count,
                            character_count=character_count,
                            source_file=json_file_path,
                            is_test_data=metadata.get('content_type') == 'sensitive' or episode_id is None
                        )
                        
                        db.add(new_quote)
                        logger.info(f"Added new quote: {quote_id}")
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing quote {quote_data.get('id', 'unknown')}: {e}")
                    continue
            
            # Commit all changes
            db.commit()
            logger.info(f"Successfully processed {processed_count} quotes")
            
            # Display summary
            print(f"\n=== Quote Processing Summary ===")
            print(f"File: {json_file_path}")
            print(f"Quotes processed: {processed_count}/{len(quotes)}")
            print(f"Episode ID: {episode_id or 'Default (1)'}")
            print(f"Content type: {metadata.get('content_type', 'normal')}")
            print(f"Requires review: {metadata.get('requires_review', False)}")
            
            return True
            
        except Exception as db_error:
            db.rollback()
            logger.error(f"Database error: {db_error}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error processing quotes JSON: {e}")
        return False

def main():
    """Main function for command-line usage"""
    if len(sys.argv) < 2:
        print("Usage: python process_quotes.py <json_file> [episode_id]")
        print("Example: python process_quotes.py quotes_input.json 238")
        sys.exit(1)
    
    json_file = sys.argv[1]
    episode_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not Path(json_file).exists():
        print(f"Error: JSON file not found: {json_file}")
        sys.exit(1)
    
    success = process_quotes_json(json_file, episode_id)
    
    if success:
        print("\n✅ Quote processing completed successfully")
    else:
        print("\n❌ Quote processing failed")
        sys.exit(1)

if __name__ == '__main__':
    main()