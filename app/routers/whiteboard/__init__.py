"""
Whiteboard router package.

This package splits the monolithic whiteboard_router.py into focused sub-routers.
The parent router owns the /api/whiteboard prefix; sub-routers use relative paths.

IMPORTANT: media_router must be included BEFORE crud_router because
analyze-url and fetch-link-preview must be registered before /{identifier}
to avoid path collision.
"""
from fastapi import APIRouter

from .media_router import router as media_router
from .crud_router import router as crud_router
from .social_media_router import router as social_media_router
from .node_links_router import router as node_links_router

# Re-export shared utilities for backward compatibility
from ._shared import (
    _save_media_to_filesystem,
    WhiteboardItemCreate, WhiteboardItemResponse, WhiteboardResponse,
    WhiteboardSaveRequest, NodeLinkSave, NodeLinkCreate, NodeLinkResponse,
)

router = APIRouter(prefix="/api/whiteboard", tags=["whiteboard"])

# media_router first (has /analyze-url, /fetch-link-preview that must precede /{identifier})
router.include_router(media_router)
# crud_router has /{identifier} catch-all patterns
router.include_router(crud_router)
router.include_router(social_media_router)
router.include_router(node_links_router)
