"""
Episodes management router for Show-Build application — backward compatibility shim.

The actual implementation has been split into the routers/episodes/ package.
This file re-exports for backward compatibility with existing imports.
"""
from routers.episodes import router
from routers.episodes.crud_router import get_next_episode_number
from routers.episodes._shared import create_content_version
