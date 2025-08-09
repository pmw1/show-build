# app/assets_router.py

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import JSONResponse, FileResponse
from auth.utils import get_current_user_or_key
import os
import shutil
from pathlib import Path
import logging
from typing import List

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use an environment variable for the base path, with a fallback for development
ASSETS_BASE_PATH = Path(os.getenv("ASSETS_ROOT", "/home/episodes/assets"))

def get_sanitized_path(path_str: str) -> Path:
    """Sanitizes a path to prevent directory traversal attacks."""
    if not path_str:
        return ASSETS_BASE_PATH

    # Resolve the path and ensure it's within the base directory
    full_path = (ASSETS_BASE_PATH / path_str).resolve()
    if ASSETS_BASE_PATH not in full_path.parents and full_path != ASSETS_BASE_PATH:
        raise HTTPException(status_code=403, detail="Forbidden: Access outside of asset directory is not allowed.")
    
    return full_path

@router.get("/assets", dependencies=[Depends(get_current_user_or_key)])
async def list_assets(path: str = ""):
    """
    List files and folders at a given path.
    """
    try:
        target_path = get_sanitized_path(path)
        if not target_path.exists() or not target_path.is_dir():
            raise HTTPException(status_code=404, detail="Path not found or is not a directory.")

        items = []
        for item in sorted(target_path.iterdir()):
            items.append({
                "name": item.name,
                "path": str(item.relative_to(ASSETS_BASE_PATH)),
                "type": "folder" if item.is_dir() else "file",
                "size": item.stat().st_size,
                "modified": item.stat().st_mtime,
            })
        return JSONResponse(content={"items": items})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error listing assets at path '{path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while listing assets.")

@router.post("/assets/folder", dependencies=[Depends(get_current_user_or_key)])
async def create_folder(path: str = Form(...)):
    """
    Create a new folder at the specified path.
    """
    try:
        target_path = get_sanitized_path(path)
        if target_path.exists():
            raise HTTPException(status_code=409, detail="Folder or file with this name already exists.")
        
        target_path.mkdir(parents=True)
        logger.info(f"Folder created: {target_path}")
        return JSONResponse(content={"message": "Folder created successfully", "path": path}, status_code=201)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error creating folder at path '{path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create folder.")

@router.post("/assets/upload", dependencies=[Depends(get_current_user_or_key)])
async def upload_files(path: str = Form(""), files: List[UploadFile] = File(...)):
    """
    Upload one or more files to the specified path.
    """
    try:
        upload_dir = get_sanitized_path(path)
        if not upload_dir.is_dir():
            raise HTTPException(status_code=400, detail="The specified path is not a directory.")

        uploaded_files = []
        for file in files:
            file_path = upload_dir / file.filename
            if file_path.exists():
                # Simple conflict resolution: append a number
                i = 1
                while file_path.exists():
                    name, ext = os.path.splitext(file.filename)
                    file_path = upload_dir / f"{name}_{i}{ext}"
                    i += 1
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_files.append({"filename": file_path.name, "path": str(file_path.relative_to(ASSETS_BASE_PATH))})
            logger.info(f"File uploaded: {file_path}")

        return JSONResponse(content={"message": "Files uploaded successfully", "uploaded_files": uploaded_files})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error uploading files to path '{path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred during file upload.")

@router.put("/assets/rename", dependencies=[Depends(get_current_user_or_key)])
async def rename_asset(old_path: str = Form(...), new_name: str = Form(...)):
    """
    Rename a file or folder.
    """
    try:
        old_target_path = get_sanitized_path(old_path)
        if not old_target_path.exists():
            raise HTTPException(status_code=404, detail="Source file or folder not found.")

        new_target_path = old_target_path.parent / new_name
        if new_target_path.exists():
            raise HTTPException(status_code=409, detail="Destination name already exists.")

        old_target_path.rename(new_target_path)
        logger.info(f"Renamed '{old_target_path}' to '{new_target_path}'")
        return JSONResponse(content={"message": "Renamed successfully"})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error renaming '{old_path}' to '{new_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to rename asset.")

@router.delete("/assets", dependencies=[Depends(get_current_user_or_key)])
async def delete_asset(path: str):
    """
    Delete a file or folder.
    """
    try:
        target_path = get_sanitized_path(path)
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="File or folder not found.")

        if target_path.is_dir():
            shutil.rmtree(target_path)
            logger.info(f"Deleted folder: {target_path}")
        else:
            target_path.unlink()
            logger.info(f"Deleted file: {target_path}")
            
        return JSONResponse(content={"message": "Deleted successfully"})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting asset at path '{path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete asset.")

@router.get("/assets/{file_path:path}", dependencies=[Depends(get_current_user_or_key)])
async def get_asset(file_path: str):
    """
    Serve an asset file.
    """
    try:
        target_path = get_sanitized_path(file_path)
        if not target_path.exists() or not target_path.is_file():
            raise HTTPException(status_code=404, detail="File not found.")
        return FileResponse(str(target_path))
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error serving asset at path '{file_path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while serving asset.")
