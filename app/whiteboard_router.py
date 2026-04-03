"""
Whiteboard router — backward-compatibility shim.
Actual implementation lives in routers/whiteboard/ package.
"""
from routers.whiteboard import router  # noqa: F401

# Re-export shared utilities that other modules may import
from routers.whiteboard import (  # noqa: F401
    _save_media_to_filesystem,
    WhiteboardItemCreate,
    WhiteboardItemResponse,
    WhiteboardResponse,
    WhiteboardSaveRequest,
    NodeLinkSave,
    NodeLinkCreate,
    NodeLinkResponse,
)
