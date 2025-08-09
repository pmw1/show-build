import yaml
import re
import logging

def parse_markdown_file(file_path: str):
    """Parses a markdown file with YAML frontmatter."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return None, None
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return None, None

    # Regex to find YAML frontmatter
    frontmatter_match = re.match(r'^---\s*$(.*)^---\s*$', content, re.MULTILINE | re.DOTALL)

    if not frontmatter_match:
        return None, content # No frontmatter

    frontmatter_str = frontmatter_match.group(1)
    body = content[frontmatter_match.end():].strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_str)
        return frontmatter, body
    except yaml.YAMLError as e:
        logging.error(f"Invalid YAML frontmatter in {file_path}: {e}")
        return None, body # Invalid frontmatter
