"""
Path configurations for the show-build project.
Centralized path management for all Python scripts.
"""
from pathlib import Path

# Base directories
PROJECT_ROOT = Path(__file__).parent.parent  # show-build/
TOOLS_DIR = PROJECT_ROOT / "tools"

# Episode and content paths  
EPISODE_ROOT = PROJECT_ROOT / "episodes"  # episodes directory under show-build
BLUEPRINTS = TOOLS_DIR / "blueprints" / "printing"

# Template paths
HEADER_PATH = BLUEPRINTS / "script-cover.html"

# Valid configuration values
VALID_CUE_TYPES = ("FSQ", "SOT", "GFX")
DEFAULT_STATUS = "draft"
DEFAULT_VERSION = 1
