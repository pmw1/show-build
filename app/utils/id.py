import os
import logging

# File path for tracking last issued ID
LAST_ID_FILE = "/home/logs/last.id"
MAX_ID_LENGTH = 5

# Ensure the logs directory exists
os.makedirs("/home/logs", exist_ok=True)

# Initialize the file if it doesn't exist
if not os.path.exists(LAST_ID_FILE):
    with open(LAST_ID_FILE, "w") as f:
        f.write("0")

def read_last_id() -> int:
    with open(LAST_ID_FILE, "r") as f:
        return int(f.read().strip())

def write_last_id(new_id: int):
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(new_id))

def get_next_id(slug: str, type_: str) -> str:
    logging.info(f"Generating ID for type={type_}, slug={slug}")
    if not slug.strip():
        raise ValueError("Slug cannot be empty")
    last_id = read_last_id()
    new_id = last_id + 1
    write_last_id(new_id)
    return f"{new_id:0{MAX_ID_LENGTH}d}"

