"""
Consolidation Router
Handles episode file consolidation between Syncthing and Google Drive.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth.utils import get_current_user_or_key
from services.google_drive_service import get_drive_service_from_config
from services.canonical_structure_parser import get_required_structure
from api_config import APIConfigManager

logger = logging.getLogger(__name__)

router = APIRouter()

SYNCTHING_BASE = "/home/episodes"


def validate_canonical_structure(episode_path: Path) -> Dict[str, Any]:
    """
    Validate episode directory against EPISODE_DIRECTORY_STANDARD.md.

    Args:
        episode_path: Path to episode directory

    Returns:
        Dictionary with validation results:
        - compliant: bool
        - missing_folders: list
        - missing_files: list
        - extra_folders: list (non-standard directories)
    """
    # Get required structure from EPISODE_DIRECTORY_STANDARD.md
    required_folders, required_root_files = get_required_structure()

    if not episode_path.exists():
        return {
            'compliant': False,
            'missing_folders': required_folders,
            'missing_files': required_root_files,
            'extra_folders': [],
            'error': 'Episode directory does not exist'
        }

    missing_folders = []
    missing_files = []
    extra_folders = []

    # Check required folders
    for folder in required_folders:
        folder_path = episode_path / folder
        if not folder_path.exists():
            missing_folders.append(folder)

    # Check required root files
    for file in required_root_files:
        file_path = episode_path / file
        if not file_path.exists():
            missing_files.append(file)

    # Identify extra/non-standard folders at root level
    standard_root_folders = set([f.split('/')[0] for f in required_folders])
    try:
        for item in episode_path.iterdir():
            if item.is_dir() and item.name not in standard_root_folders:
                # Ignore hidden folders
                if not item.name.startswith('.'):
                    extra_folders.append(item.name)
    except PermissionError:
        logger.warning(f"Permission denied reading {episode_path}")

    compliant = len(missing_folders) == 0 and len(missing_files) == 0

    return {
        'compliant': compliant,
        'missing_folders': missing_folders,
        'missing_files': missing_files,
        'extra_folders': extra_folders
    }


def build_syncthing_tree(episode_path: Path) -> tuple[List[Dict[str, Any]], int, int]:
    """
    Build directory tree structure for Syncthing episode directory.

    Args:
        episode_path: Path to episode directory

    Returns:
        Tuple of (tree structure, total size in bytes, file count)
    """
    if not episode_path.exists():
        logger.warning(f"Episode path does not exist: {episode_path}")
        return [], 0, 0

    total_size = 0
    file_count = 0

    def _build_tree_recursive(path: Path, relative_to: Path) -> Dict[str, Any]:
        """Recursively build tree structure."""
        nonlocal total_size, file_count

        rel_path = path.relative_to(relative_to)
        node = {
            'title': path.name,
            'path': str(rel_path),
            'type': 'folder' if path.is_dir() else 'file'
        }

        if path.is_file():
            try:
                size = path.stat().st_size
                node['size'] = size
                total_size += size
                file_count += 1
            except Exception as e:
                logger.warning(f"Could not stat file {path}: {e}")
                node['size'] = 0

        if path.is_dir():
            children = []
            try:
                # Sort directories first, then files, alphabetically
                entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
                for entry in entries:
                    # Skip hidden files and system files
                    if entry.name.startswith('.'):
                        continue
                    children.append(_build_tree_recursive(entry, relative_to))
                node['children'] = children
            except PermissionError:
                logger.warning(f"Permission denied reading directory: {path}")
                node['children'] = []

        return node

    # Build tree starting from episode root
    try:
        tree_list = []
        entries = sorted(episode_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for entry in entries:
            if entry.name.startswith('.'):
                continue
            tree_list.append(_build_tree_recursive(entry, episode_path))

        return tree_list, total_size, file_count
    except Exception as e:
        logger.error(f"Error building Syncthing tree: {e}")
        return [], 0, 0


def validate_drive_structure(drive_service, folder_id: str) -> Dict[str, Any]:
    """
    Validate Google Drive folder structure against EPISODE_DIRECTORY_STANDARD.md.

    Args:
        drive_service: Authenticated GoogleDriveService instance
        folder_id: Google Drive folder ID to validate

    Returns:
        Dictionary with validation results (same format as validate_canonical_structure)
    """
    # Get required structure from EPISODE_DIRECTORY_STANDARD.md
    required_folders, required_root_files = get_required_structure()

    missing_folders = []
    missing_files = []
    extra_folders = []

    try:
        # Build a map of all folders and files in the Drive folder
        drive_items = {}

        def _map_drive_items(parent_id: str, parent_path: str = ""):
            """Recursively map all items in Drive."""
            try:
                items = drive_service.list_files(folder_id=parent_id, order_by="folder,name")
                for item in items:
                    is_folder = item.get('mimeType') == 'application/vnd.google-apps.folder'
                    item_name = item['name']
                    item_path = f"{parent_path}/{item_name}" if parent_path else item_name

                    drive_items[item_path] = {
                        'type': 'folder' if is_folder else 'file',
                        'id': item['id'],
                        'name': item_name
                    }

                    # Recurse into folders
                    if is_folder:
                        _map_drive_items(item['id'], item_path)
            except Exception as e:
                logger.warning(f"Error mapping Drive items in {parent_id}: {e}")

        # Map all Drive items
        _map_drive_items(folder_id)

        # Check required folders
        for folder in required_folders:
            if folder not in drive_items or drive_items[folder]['type'] != 'folder':
                missing_folders.append(folder)

        # Check required root files
        for file in required_root_files:
            if file not in drive_items or drive_items[file]['type'] != 'file':
                missing_files.append(file)

        # Identify extra/non-standard folders at root level
        standard_root_folders = set([f.split('/')[0] for f in required_folders])
        for path, item in drive_items.items():
            # Only check root-level folders
            if '/' not in path and item['type'] == 'folder':
                if item['name'] not in standard_root_folders:
                    extra_folders.append(item['name'])

        compliant = len(missing_folders) == 0 and len(missing_files) == 0

        return {
            'compliant': compliant,
            'missing_folders': missing_folders,
            'missing_files': missing_files,
            'extra_folders': extra_folders
        }

    except Exception as e:
        logger.error(f"Error validating Drive structure: {e}")
        return {
            'compliant': False,
            'missing_folders': required_folders,
            'missing_files': required_root_files,
            'extra_folders': [],
            'error': str(e)
        }


def build_drive_tree(drive_service, folder_id: str) -> tuple[List[Dict[str, Any]], int, int]:
    """
    Build directory tree structure for Google Drive folder.

    Args:
        drive_service: Authenticated GoogleDriveService instance
        folder_id: Google Drive folder ID to start from

    Returns:
        Tuple of (tree structure, total size in bytes, file count)
    """
    total_size = 0
    file_count = 0

    def _build_tree_recursive(parent_id: str) -> List[Dict[str, Any]]:
        """Recursively build tree structure."""
        nonlocal total_size, file_count

        try:
            # Get all items in this folder
            items = drive_service.list_files(folder_id=parent_id, order_by="folder,name")

            tree_nodes = []
            for item in items:
                is_folder = item.get('mimeType') == 'application/vnd.google-apps.folder'

                node = {
                    'title': item['name'],
                    'id': item['id'],
                    'type': 'folder' if is_folder else 'file'
                }

                if not is_folder:
                    # Regular file - get size
                    size = int(item.get('size', 0))
                    node['size'] = size
                    total_size += size
                    file_count += 1
                else:
                    # Folder - recurse into children
                    node['children'] = _build_tree_recursive(item['id'])

                tree_nodes.append(node)

            return tree_nodes

        except Exception as e:
            logger.error(f"Error listing Google Drive folder {parent_id}: {e}")
            return []

    try:
        tree = _build_tree_recursive(folder_id)
        return tree, total_size, file_count
    except Exception as e:
        logger.error(f"Error building Drive tree: {e}")
        return [], 0, 0


@router.get("/consolidation/compare/{episode_number}")
async def compare_episode_directories(
    episode_number: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_or_key)
):
    """
    Compare episode directories between Syncthing and Google Drive.

    Returns directory trees, file counts, and total sizes for both systems.
    """
    try:
        # Build Syncthing tree
        syncthing_path = Path(SYNCTHING_BASE) / episode_number
        syncthing_tree, syncthing_size, syncthing_count = build_syncthing_tree(syncthing_path)

        # Validate canonical structure
        validation = validate_canonical_structure(syncthing_path)

        # Initialize Drive variables
        drive_tree = []
        drive_size = 0
        drive_count = 0
        drive_folder_id = None
        drive_validation = None

        # Try to build Google Drive tree
        try:
            api_config_manager = APIConfigManager()
            drive_service = get_drive_service_from_config(api_config_manager)

            # Get episodes root folder ID from config
            episodes_root_id = drive_service.get_episodes_folder_id()

            if episodes_root_id:
                # Look for episode folder within episodes root
                episode_folders = drive_service.search_files(name_contains=episode_number)

                # Filter to exact match within episodes root
                matching_folder = None
                for folder in episode_folders:
                    if folder['name'] == episode_number and folder.get('mimeType') == 'application/vnd.google-apps.folder':
                        # Check if parent is episodes root
                        parents = folder.get('parents', [])
                        if episodes_root_id in parents:
                            matching_folder = folder
                            break

                if matching_folder:
                    drive_folder_id = matching_folder['id']
                    drive_tree, drive_size, drive_count = build_drive_tree(drive_service, drive_folder_id)

                    # Validate Drive structure
                    drive_validation = validate_drive_structure(drive_service, drive_folder_id)

                    logger.info(f"✅ Found Google Drive folder for episode {episode_number}")
                else:
                    logger.warning(f"⚠️  Episode folder {episode_number} not found in Google Drive")
            else:
                logger.warning("⚠️  Episodes root folder ID not configured")

        except ValueError as e:
            logger.warning(f"⚠️  Google Drive not configured: {e}")
        except Exception as e:
            logger.error(f"❌ Error accessing Google Drive: {e}")

        return {
            "episode": episode_number,
            "syncthing_path": str(syncthing_path),
            "syncthing_tree": syncthing_tree,
            "syncthing_total_size": syncthing_size,
            "syncthing_file_count": syncthing_count,
            "syncthing_validation": validation,
            "drive_tree": drive_tree,
            "drive_total_size": drive_size,
            "drive_file_count": drive_count,
            "drive_folder_id": drive_folder_id or "Not found",
            "drive_validation": drive_validation
        }

    except Exception as e:
        logger.error(f"❌ Consolidation comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare directories: {str(e)}"
        )


@router.post("/consolidation/normalize-episode-names")
async def normalize_episode_names(
    dry_run: bool = True,
    min_episode: Optional[str] = None,
    max_episode: Optional[str] = None,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """
    Normalize episode folder names in Google Drive (remove date suffixes, extra text).

    Args:
        dry_run: Preview changes without applying
        min_episode: Minimum episode number (e.g., "0200")
        max_episode: Maximum episode number (e.g., "0300")

    Returns:
        Report with valid, renamed, flagged, and error folders
    """
    from normalize_episode_names import normalize_episode_folders

    try:
        logger.info(f"🔧 Starting episode name normalization (dry_run={dry_run})")

        report = normalize_episode_folders(
            dry_run=dry_run,
            min_episode=min_episode,
            max_episode=max_episode
        )

        return {
            "success": True,
            "dry_run": dry_run,
            "report": report,
            "summary": {
                "valid": len(report['valid']),
                "renamed": len(report['renamed']),
                "flagged": len(report['flagged']),
                "errors": len(report['errors'])
            }
        }

    except Exception as e:
        logger.error(f"❌ Episode normalization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to normalize episode names: {str(e)}"
        )
