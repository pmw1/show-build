"""
Google Drive Service
Handles Google Drive API operations using Service Account authentication.
Credentials sourced from api_configs database.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError
import io
from pathlib import Path

logger = logging.getLogger(__name__)

class GoogleDriveService:
    """Service for interacting with Google Drive API using Service Account."""

    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file'
    ]

    def __init__(self, service_account_json: str):
        """
        Initialize Google Drive service with Service Account credentials.

        Args:
            service_account_json: JSON string containing service account credentials
        """
        self.service = None
        self.credentials = None
        self.config = {}  # Will be set by get_drive_service_from_config
        self._authenticate(service_account_json)

    def _authenticate(self, service_account_json: str):
        """Authenticate using Service Account JSON."""
        try:
            # Parse JSON credentials
            creds_dict = json.loads(service_account_json)

            # Create credentials from service account info
            self.credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=self.SCOPES
            )

            # Build Drive API service
            self.service = build('drive', 'v3', credentials=self.credentials)
            logger.info("✅ Google Drive service authenticated successfully")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid service account JSON: {e}")
            raise ValueError("Invalid service account JSON format")
        except Exception as e:
            logger.error(f"❌ Google Drive authentication failed: {e}")
            raise

    def get_episodes_folder_id(self) -> Optional[str]:
        """
        Get the configured episodes root folder ID from config.

        Returns:
            Folder ID string, or None if not configured
        """
        return self.config.get('episodesFolderId')

    def list_files(
        self,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 100,
        order_by: str = "modifiedTime desc"
    ) -> List[Dict[str, Any]]:
        """
        List files in Google Drive.

        Args:
            folder_id: Optional folder ID to list files from
            query: Optional query string for filtering (Google Drive Query Language)
            page_size: Number of results per page (max 1000)
            order_by: Sort order (e.g., 'modifiedTime desc', 'name')

        Returns:
            List of file metadata dictionaries
        """
        try:
            # Build query
            query_parts = []
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            if query:
                query_parts.append(query)

            # Add trashed filter (exclude by default)
            query_parts.append("trashed = false")

            final_query = " and ".join(query_parts) if query_parts else None

            # Execute API call (include Shared Drives)
            results = self.service.files().list(
                q=final_query,
                pageSize=page_size,
                orderBy=order_by,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink, parents, owners)",
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                corpora='allDrives'
            ).execute()

            files = results.get('files', [])
            logger.info(f"📁 Listed {len(files)} files from Google Drive")
            return files

        except HttpError as e:
            logger.error(f"❌ Google Drive API error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to list files: {e}")
            raise

    def search_files(
        self,
        name_contains: Optional[str] = None,
        mime_type: Optional[str] = None,
        modified_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for files in Google Drive.

        Args:
            name_contains: Search for files containing this string in name
            mime_type: Filter by MIME type (e.g., 'video/mp4', 'image/jpeg')
            modified_after: ISO 8601 datetime string (e.g., '2024-01-01T00:00:00')

        Returns:
            List of matching file metadata
        """
        query_parts = []

        if name_contains:
            query_parts.append(f"name contains '{name_contains}'")
        if mime_type:
            query_parts.append(f"mimeType = '{mime_type}'")
        if modified_after:
            query_parts.append(f"modifiedTime > '{modified_after}'")

        query = " and ".join(query_parts) if query_parts else None
        return self.list_files(query=query)

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific file.

        Args:
            file_id: Google Drive file ID

        Returns:
            File metadata dictionary
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime, webViewLink, parents, owners, description"
            ).execute()

            logger.info(f"📄 Retrieved metadata for: {file.get('name')}")
            return file

        except HttpError as e:
            logger.error(f"❌ Failed to get file metadata for {file_id}: {e}")
            raise

    def download_file(self, file_id: str, destination_path: str) -> str:
        """
        Download a file from Google Drive.

        Args:
            file_id: Google Drive file ID
            destination_path: Local path to save file

        Returns:
            Path to downloaded file
        """
        try:
            # Get file metadata first
            file_metadata = self.get_file_metadata(file_id)
            file_name = file_metadata.get('name')

            # Request file content
            request = self.service.files().get_media(fileId=file_id)

            # Download to destination
            dest_path = Path(destination_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            with io.FileIO(str(dest_path), 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.debug(f"⬇️  Download progress: {progress}%")

            logger.info(f"✅ Downloaded: {file_name} → {dest_path}")
            return str(dest_path)

        except HttpError as e:
            logger.error(f"❌ Failed to download file {file_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Download error: {e}")
            raise

    def upload_file(
        self,
        file_path: str,
        folder_id: Optional[str] = None,
        file_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Google Drive.

        Args:
            file_path: Local path to file to upload
            folder_id: Optional parent folder ID
            file_name: Optional name for uploaded file (defaults to local filename)

        Returns:
            Uploaded file metadata
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Prepare metadata
            file_metadata = {
                'name': file_name or path.name
            }
            if folder_id:
                file_metadata['parents'] = [folder_id]

            # Upload file
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()

            logger.info(f"✅ Uploaded: {path.name} → Google Drive (ID: {file.get('id')})")
            return file

        except FileNotFoundError as e:
            logger.error(f"❌ {e}")
            raise
        except HttpError as e:
            logger.error(f"❌ Failed to upload file: {e}")
            raise

    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a folder in Google Drive.

        Args:
            folder_name: Name of folder to create
            parent_id: Optional parent folder ID

        Returns:
            Created folder metadata
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]

            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()

            logger.info(f"✅ Created folder: {folder_name} (ID: {folder.get('id')})")
            return folder

        except HttpError as e:
            logger.error(f"❌ Failed to create folder: {e}")
            raise

    def list_folders(self, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List folders in Google Drive.

        Args:
            parent_id: Optional parent folder ID to list subfolders from

        Returns:
            List of folder metadata
        """
        query = "mimeType = 'application/vnd.google-apps.folder'"
        return self.list_files(folder_id=parent_id, query=query)

    def get_folder_tree(self, root_folder_id: Optional[str] = None, max_depth: int = 5) -> Dict[str, Any]:
        """
        Get hierarchical folder structure.

        Args:
            root_folder_id: Starting folder ID (None for root)
            max_depth: Maximum depth to traverse

        Returns:
            Nested dictionary representing folder structure
        """
        def _build_tree(folder_id: Optional[str], depth: int) -> Dict[str, Any]:
            if depth >= max_depth:
                return {}

            folders = self.list_folders(parent_id=folder_id)
            tree = {}

            for folder in folders:
                folder_id = folder['id']
                folder_name = folder['name']
                tree[folder_name] = {
                    'id': folder_id,
                    'metadata': folder,
                    'children': _build_tree(folder_id, depth + 1)
                }

            return tree

        return _build_tree(root_folder_id, 0)


def get_drive_service_from_config(api_config_manager) -> GoogleDriveService:
    """
    Create GoogleDriveService instance from database configuration.

    Args:
        api_config_manager: APIConfigManager instance

    Returns:
        Authenticated GoogleDriveService instance

    Raises:
        ValueError: If configuration is missing or invalid
    """
    try:
        # Load config from database
        config = api_config_manager.load_config()

        # Navigate to Google config
        google_config = (
            config.get('preproduction', {})
            .get('storage', {})
            .get('google', {})
        )

        # Check if enabled
        if not google_config.get('driveEnabled'):
            raise ValueError("Google Drive integration is not enabled in settings")

        # Get service account JSON
        service_account_json = google_config.get('serviceAccount')
        if not service_account_json:
            raise ValueError("Service Account JSON not configured. Please add credentials in Settings > API Configuration > Google Services")

        # Create service
        logger.info("🔧 Initializing Google Drive service from database config")
        service = GoogleDriveService(service_account_json)

        # Store config on service for filtering
        service.config = google_config

        return service

    except Exception as e:
        logger.error(f"❌ Failed to initialize Google Drive service: {e}")
        raise


def is_folder_allowed(folder_name: str, config: Dict[str, Any]) -> bool:
    """
    Check if a folder is allowed based on whitelist/blacklist configuration.

    Args:
        folder_name: Name of the folder to check
        config: Google Drive configuration dict

    Returns:
        True if folder is allowed, False otherwise
    """
    # Check excluded folders first (blacklist takes priority)
    excluded = config.get('excludedFolders', [])
    if excluded and folder_name in excluded:
        return False

    # Check allowed folders (whitelist)
    allowed = config.get('allowedFolders', [])
    if allowed:
        # If whitelist exists, only allow listed folders
        return folder_name in allowed

    # No whitelist means all (non-excluded) folders are allowed
    return True
