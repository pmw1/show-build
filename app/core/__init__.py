"""
Core application configuration and utilities
"""
from .config import settings
from .media_paths import media_paths, MediaType, MediaCategory
from .paths import paths  # Keep existing paths for compatibility

__all__ = ['settings', 'media_paths', 'MediaType', 'MediaCategory', 'paths']