# validator.py
import logging
from utils.id import get_next_id

def validate_front_matter(front_matter: dict, filename: str = None) -> dict:
    """
    Validates and normalizes front matter fields, passing all other fields through.
    - Normalizes all keys to lowercase.
    - Ensures 'slug' is present.
    - Validates or generates 'id'.
    - Ensures 'order' is an integer if present.
    - Passes through all other fields without validation.
    """
    if not isinstance(front_matter, dict):
        logging.error(f"Invalid front_matter input for {filename}: expected dict, got {type(front_matter)}")
        return {"id": filename, "type": "error", "slug": "invalid-frontmatter", "title": f"Invalid Frontmatter in {filename}"}

    system_messages = []
    
    # Normalize all keys to lowercase and create the base metadata object
    metadata = {k.strip().lower(): v for k, v in front_matter.items()}

    # Ensure 'slug' is present, as it's critical for routing and ID generation
    if "slug" not in metadata or not metadata["slug"]:
        # If no slug, we can't generate a proper ID, this is a critical error
        raise ValueError(f"Missing or invalid 'slug' in {filename or 'front matter'}")

    # Validate 'id' or generate a new one if missing/invalid
    if "id" not in metadata or not str(metadata.get("id")).strip():
        try:
            # Use a default 'unknown' if type is missing, as per documentation
            item_type = metadata.get("type", "unknown")
            if not item_type:
                item_type = "unknown"
            
            new_id = get_next_id(metadata["slug"], item_type)
            metadata["id"] = new_id
            system_messages.append(f"ID was missing or invalid and has been automatically generated: {new_id}")
        except Exception as e:
            raise ValueError(f"Could not generate ID for {filename}: {e}")

    # Ensure 'order' is an integer if it exists
    if "order" in metadata:
        try:
            if metadata["order"] is not None:
                metadata["order"] = int(metadata["order"])
        except (ValueError, TypeError):
            system_messages.append(f"Value for 'order' in {filename} ('{metadata['order']}') is not a valid integer and will be ignored.")
            metadata.pop("order")

    # Add any system messages to the metadata
    if system_messages:
        # Use a more descriptive key for system-generated messages
        metadata["system_warnings"] = system_messages

    return metadata

