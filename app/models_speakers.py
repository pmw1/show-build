"""
Speaker Models - COMPATIBILITY SHIM

⚠️ DEPRECATED: This module is maintained for backwards compatibility only.
Speaker model has been moved to models_v2.py for proper architecture.

All new code should import Speaker from models_v2 directly:
    from models_v2 import Speaker  # Preferred

This shim will be removed in a future release.
"""

# Re-export Speaker from models_v2 for backwards compatibility
from models_v2 import Speaker

__all__ = ['Speaker']

# Warning for developers
import warnings
warnings.warn(
    "models_speakers.py is deprecated. Import Speaker from models_v2 instead.",
    DeprecationWarning,
    stacklevel=2
)
