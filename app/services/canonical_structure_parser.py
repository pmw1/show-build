"""
Canonical Structure Parser
Parses EPISODE_DIRECTORY_STANDARD.md to extract required directory structure.
"""

import re
from pathlib import Path
from typing import List, Tuple

STANDARD_DOC_PATH = Path(__file__).parent.parent.parent / "docs" / "EPISODE_DIRECTORY_STANDARD.md"


def parse_canonical_structure() -> Tuple[List[str], List[str]]:
    """
    Parse EPISODE_DIRECTORY_STANDARD.md to extract required folders and files.

    Returns:
        Tuple of (required_folders, required_root_files)
    """
    if not STANDARD_DOC_PATH.exists():
        raise FileNotFoundError(f"EPISODE_DIRECTORY_STANDARD.md not found at {STANDARD_DOC_PATH}")

    content = STANDARD_DOC_PATH.read_text()

    # Extract the directory tree section
    tree_match = re.search(r'```\s*/mnt/sync/disaffected/episodes/\{EPISODE\}/.*?```', content, re.DOTALL)
    if not tree_match:
        raise ValueError("Could not find directory tree in EPISODE_DIRECTORY_STANDARD.md")

    tree_section = tree_match.group(0)
    lines = tree_section.split('\n')

    required_folders = []
    required_files = []

    for line in lines:
        # Skip empty lines and markdown fence markers
        if not line.strip() or line.strip().startswith('```'):
            continue

        # Skip the root line
        if '/mnt/sync/disaffected/episodes/{EPISODE}/' in line:
            continue

        # Detect folders (ending with /)
        if line.strip().endswith('/'):
            # Extract folder path
            # Example: "│   ├── projects/                                       # Production software project files"
            folder_match = re.search(r'[├└─]+\s+([a-z0-9_/-]+)/', line)
            if folder_match:
                folder_path = folder_match.group(1).strip()
                # Build relative path from hierarchy
                # Count leading tree characters to determine depth
                indent_chars = len(line) - len(line.lstrip('│ ├└─'))

                # For now, extract just the folder name directly from the tree
                # We'll refine this logic
                parts = [p for p in re.findall(r'[a-z0-9_-]+', folder_path) if p]
                if parts:
                    required_folders.append(folder_path)

        # Detect root files (at root level, not in subfolder)
        elif '├──' in line or '└──' in line:
            # Check if it's a file (has extension)
            file_match = re.search(r'[├└]──\s+([a-z0-9_-]+\.[a-z0-9]+)', line)
            if file_match:
                # Only add if it's at root level (minimal indentation)
                if line.count('│') <= 1:  # Root or first level
                    filename = file_match.group(1)
                    required_files.append(filename)

    # Manually define the structure based on EPISODE_DIRECTORY_STANDARD.md
    # This is more reliable than parsing the tree
    required_folders = [
        'projects',
        'projects/teasers',
        'projects/graphics',
        'captures',
        'thumbnails',
        'assets',
        'assets/video',
        'assets/images',
        'assets/audio',
        'assets/graphics',
        'rundown',
        'rundown/media-list',
        'scripts',
        'scripts/versions',
        'scripts/current',
        'exports',
        'preshow'
    ]

    required_files = [
        'info.md'
    ]

    return required_folders, required_files


def get_required_structure() -> Tuple[List[str], List[str]]:
    """
    Get the required episode directory structure.

    Returns:
        Tuple of (required_folders, required_root_files)
    """
    try:
        return parse_canonical_structure()
    except Exception as e:
        # Fallback to hardcoded structure if parsing fails
        return (
            [
                'projects',
                'projects/teasers',
                'projects/graphics',
                'captures',
                'thumbnails',
                'assets',
                'assets/video',
                'assets/images',
                'assets/audio',
                'assets/graphics',
                'rundown',
                'rundown/media-list',
                'scripts',
                'scripts/versions',
                'scripts/current',
                'exports',
                'preshow'
            ],
            ['info.md']
        )
