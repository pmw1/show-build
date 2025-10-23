"""
Google Drive Router
API endpoints for Google Drive file operations.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from auth.utils import get_current_user_or_key
from services.google_drive_service import GoogleDriveService, get_drive_service_from_config, is_folder_allowed
from api_config import api_config_manager

router = APIRouter()
logger = logging.getLogger(__name__)


class FileSearchRequest(BaseModel):
    """Request model for file search."""
    name_contains: Optional[str] = None
    mime_type: Optional[str] = None
    modified_after: Optional[str] = None


class FolderCreateRequest(BaseModel):
    """Request model for folder creation."""
    folder_name: str
    parent_id: Optional[str] = None


class FileUploadRequest(BaseModel):
    """Request model for file upload."""
    file_path: str
    folder_id: Optional[str] = None
    file_name: Optional[str] = None


class FileDownloadRequest(BaseModel):
    """Request model for file download."""
    file_id: str
    destination_path: str


@router.get("/drive/status")
async def get_drive_status(token_data=Depends(get_current_user_or_key)):
    """
    Check Google Drive integration status.
    """
    try:
        config = api_config_manager.load_config()
        google_config = (
            config.get('preproduction', {})
            .get('storage', {})
            .get('google', {})
        )

        drive_enabled = google_config.get('driveEnabled', False)
        has_service_account = bool(google_config.get('serviceAccount'))

        return {
            "success": True,
            "enabled": drive_enabled,
            "configured": has_service_account,
            "message": "Google Drive ready" if (drive_enabled and has_service_account) else "Google Drive not configured"
        }
    except Exception as e:
        logger.error(f"Failed to check Drive status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drive/test")
async def test_drive_connection(token_data=Depends(get_current_user_or_key)):
    """
    Test Google Drive connection by listing root files and folders.
    """
    try:
        drive_service = get_drive_service_from_config(api_config_manager)

        # List both files and folders
        all_items = drive_service.list_files(page_size=100)

        # Separate folders and files
        all_folders = [f for f in all_items if f.get('mimeType') == 'application/vnd.google-apps.folder']
        all_files = [f for f in all_items if f.get('mimeType') != 'application/vnd.google-apps.folder']

        # Apply folder filtering
        config = getattr(drive_service, 'config', {})
        filtered_folders = [f for f in all_folders if is_folder_allowed(f.get('name'), config)]

        return {
            "success": True,
            "message": f"✅ Connected to Google Drive (found {len(filtered_folders)} allowed folders, {len(all_files)} files)",
            "folders": [
                {
                    "name": f.get('name'),
                    "id": f.get('id'),
                    "type": f.get('mimeType')
                }
                for f in filtered_folders[:20]
            ],
            "sample_files": [
                {
                    "name": f.get('name'),
                    "id": f.get('id'),
                    "type": f.get('mimeType')
                }
                for f in all_files[:5]
            ],
            "filtering_active": bool(config.get('allowedFolders') or config.get('excludedFolders')),
            "total_folders": len(all_folders),
            "filtered_folders": len(filtered_folders)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Drive connection test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


@router.get("/drive/files")
async def list_files(
    folder_id: Optional[str] = Query(None, description="Folder ID to list files from"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of results"),
    order_by: str = Query("modifiedTime desc", description="Sort order"),
    token_data=Depends(get_current_user_or_key)
):
    """
    List files from Google Drive.
    """
    try:
        drive_service = get_drive_service_from_config(api_config_manager)
        files = drive_service.list_files(
            folder_id=folder_id,
            page_size=page_size,
            order_by=order_by
        )

        return {
            "success": True,
            "count": len(files),
            "files": files
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drive/search")
async def search_files(
    search: FileSearchRequest,
    token_data=Depends(get_current_user_or_key)
):
    """
    Search for files in Google Drive.
    """
    try:
        drive_service = get_drive_service_from_config(api_config_manager)
        files = drive_service.search_files(
            name_contains=search.name_contains,
            mime_type=search.mime_type,
            modified_after=search.modified_after
        )

        return {
            "success": True,
            "count": len(files),
            "files": files
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drive/file/{file_id}")
async def get_file_metadata(
    file_id: str,
    token_data=Depends(get_current_user_or_key)
):
    """
    Get metadata for a specific file.
    """
    try:
        drive_service = get_drive_service_from_config(api_config_manager)
        metadata = drive_service.get_file_metadata(file_id)

        return {
            "success": True,
            "file": metadata
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get file metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drive/download")
async def download_file(
    download: FileDownloadRequest,
    token_data=Depends(get_current_user_or_key)
):
    """
    Download a file from Google Drive to local storage.
    """
    try:
        drive_service = get_drive_service_from_config(api_config_manager)
        local_path = drive_service.download_file(
            file_id=download.file_id,
            destination_path=download.destination_path
        )

        return {
            "success": True,
            "message": "File downloaded successfully",
            "local_path": local_path
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drive/upload")
async def upload_file(
    upload: FileUploadRequest,
    token_data=Depends(get_current_user_or_key)
):
    """
    Upload a local file to Google Drive.
    """
    try:
        drive_service = get_drive_service_from_config(api_config_manager)
        file_metadata = drive_service.upload_file(
            file_path=upload.file_path,
            folder_id=upload.folder_id,
            file_name=upload.file_name
        )

        return {
            "success": True,
            "message": "File uploaded successfully",
            "file": file_metadata
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drive/folders")
async def list_folders(
    parent_id: Optional[str] = Query(None, description="Parent folder ID"),
    token_data=Depends(get_current_user_or_key)
):
    """
    List folders in Google Drive.
    """
    try:
        drive_service = get_drive_service_from_config(api_config_manager)
        folders = drive_service.list_folders(parent_id=parent_id)

        return {
            "success": True,
            "count": len(folders),
            "folders": folders
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drive/folder-tree")
async def get_folder_tree(
    root_folder_id: Optional[str] = Query(None, description="Root folder ID"),
    max_depth: int = Query(5, ge=1, le=10, description="Maximum depth to traverse"),
    token_data=Depends(get_current_user_or_key)
):
    """
    Get hierarchical folder structure from Google Drive.
    """
    try:
        drive_service = get_drive_service_from_config(api_config_manager)
        tree = drive_service.get_folder_tree(
            root_folder_id=root_folder_id,
            max_depth=max_depth
        )

        return {
            "success": True,
            "tree": tree
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get folder tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drive/folder")
async def create_folder(
    folder: FolderCreateRequest,
    token_data=Depends(get_current_user_or_key)
):
    """
    Create a new folder in Google Drive.
    """
    try:
        drive_service = get_drive_service_from_config(api_config_manager)
        folder_metadata = drive_service.create_folder(
            folder_name=folder.folder_name,
            parent_id=folder.parent_id
        )

        return {
            "success": True,
            "message": "Folder created successfully",
            "folder": folder_metadata
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))
