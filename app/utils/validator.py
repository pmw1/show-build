# validator.py
import logging
from utils.id import get_next_id



# Define which front matter fields we care about
KNOWN_FIELDS = [
    "slug",
    "id",
    "type",
    "duration",
    "title",
    "order"
]

def validate_front_matter(front_matter: dict, filename: str = None) -> dict:
    metadata = {}
    system_messages = []

    print(f"[DEBUG FRONT MATTER] {front_matter}")
    
    # Normalize keys (case-insensitive)
    normalized = {k.strip().lower(): v for k, v in front_matter.items()}

    for field in KNOWN_FIELDS:
        key = field.lower()
        if key in normalized:
            metadata[field] = normalized[key]

    # Validate required fields
    if "slug" not in metadata or not metadata["slug"]:
        raise ValueError(f"Missing or invalid 'slug' in {filename or 'front matter'}")

    if "id" not in metadata or not str(metadata["id"]).isdigit():
        try:
            metadata["id"] = get_next_id(metadata["slug"], metadata.get("type", "unknown"))
            system_messages.append("ID was missing or invalid and has been automatically generated.")
        except Exception as e:
            raise ValueError(f"Could not generate ID: {e}")

    # Validate optional integer field for 'order'
    if "order" in metadata:
        try:
            if metadata["order"] is not None:
                metadata["order"] = int(metadata["order"])
        except (ValueError, TypeError):
            system_messages.append("'order' must be an integer or null.")

    # Catch unexpected fields
    for field in normalized:
        if field not in KNOWN_FIELDS:
            msg = f"Unexpected front matter field: {field}. This field is not currently handled by the validator."
            logging.warning(f"{filename or 'unknown file'} — system warnings: {msg}")
            ##system_messages.append(msg)

    if system_messages:
        metadata["system_messages"] = system_messages

    return metadata

