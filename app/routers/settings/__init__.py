"""
Settings router package.

This package splits the monolithic settings_router.py into focused sub-routers.
The parent router owns the /settings prefix; sub-routers use relative paths.
"""
from fastapi import APIRouter

from .general_router import router as general_router
from .media_paths_router import router as media_paths_router
from .interface_router import router as interface_router
from .system_router import router as system_router
from .llm_identity_router import router as llm_identity_router

# Re-export shared utilities for backward compatibility
from ._shared import (
    load_settings, save_settings, derive_paths, format_bytes,
    camel_to_snake, SETTINGS_FILE,
    MediaPathSettings, InterfaceSettings, RundownSettings,
    SystemSettings, GenerationSettings, AutosaveHistorySettings,
    SettingsUpdate,
)

router = APIRouter(prefix="/settings", tags=["settings"])

router.include_router(general_router)
router.include_router(media_paths_router)
router.include_router(interface_router)
router.include_router(system_router)
router.include_router(llm_identity_router)
