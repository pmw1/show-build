"""
Episodes router package.

This package splits the monolithic episodes_router.py into focused sub-routers.
The parent router owns the /episodes prefix; sub-routers use relative paths.
"""
from fastapi import APIRouter

from .crud_router import router as crud_router
from .metadata_router import router as metadata_router
from .rundown_router import router as rundown_router
from .versioning_router import router as versioning_router
from .history_router import router as history_router
from .thumbnails_router import router as thumbnails_router
from .cues_router import router as cues_router
from .media_router import router as media_router
from .cue_assets_router import router as cue_assets_router

# Re-export shared utilities for backward compatibility
from ._shared import create_content_version, create_episode_directory, create_info_file
from .crud_router import get_next_episode_number

router = APIRouter(prefix="/episodes", tags=["episodes"])

router.include_router(crud_router)
router.include_router(metadata_router)
router.include_router(rundown_router)
router.include_router(versioning_router)
router.include_router(history_router)
router.include_router(thumbnails_router)
router.include_router(cues_router)
router.include_router(media_router)
router.include_router(cue_assets_router)
