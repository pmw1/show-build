import os
import logging
from datetime import datetime

# File path for tracking last issued ID - use relative path
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LAST_ID_FILE = os.path.join(LOGS_DIR, "last.id")

# Ensure the logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Initialize the file if it doesn't exist
if not os.path.exists(LAST_ID_FILE):
    with open(LAST_ID_FILE, "w") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d')}:0")

def read_last_id() -> tuple[str, int]:
    """Reads the last used date and ID from the tracking file."""
    try:
        with open(LAST_ID_FILE, "r") as f:
            content = f.read().strip()
            if ':' in content:
                date_str, last_id_str = content.split(':')
                return date_str, int(last_id_str)
            else:
                # Handle legacy format by assuming today and the read number
                return datetime.now().strftime('%Y-%m-%d'), int(content)
    except (IOError, ValueError):
        # If file is empty, corrupt, or doesn't exist, start fresh
        return datetime.now().strftime('%Y-%m-%d'), 0

def write_last_id(date_str: str, new_id: int):
    """Writes the new date and ID to the tracking file."""
    with open(LAST_ID_FILE, "w") as f:
        f.write(f"{date_str}:{new_id}")

def get_next_id(slug: str, type_: str) -> str:
    """
    Generates a new unique ID based on the format: {type}_{YYYYMMDD}_{###}.
    The sequential number resets daily.
    """
    logging.info(f"Generating ID for type={type_}, slug={slug}")
    if not slug or not slug.strip():
        raise ValueError("Slug cannot be empty")
    if not type_ or not type_.strip():
        raise ValueError("Type cannot be empty")

    today_str = datetime.now().strftime('%Y-%m-%d')
    date_from_file, last_id = read_last_id()

    if date_from_file == today_str:
        new_id_num = last_id + 1
    else:
        new_id_num = 1  # Reset for the new day

    write_last_id(today_str, new_id_num)

    date_for_id = datetime.now().strftime('%Y%m%d')
    
    # Format: {type}_{YYYYMMDD}_{###}
    return f"{type_.lower()}_{date_for_id}_{new_id_num:03d}"

