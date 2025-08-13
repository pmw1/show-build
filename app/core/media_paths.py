"""
Centralized media path management for Show-Build
Handles all path operations, validation, and organization
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
import json


class MediaType(str, Enum):
    """Types of media assets"""
    LOGO = "logo"
    POSTER = "poster"
    AUDIO = "audio"
    VIDEO = "video"
    GRAPHIC = "graphic"
    IMAGE = "image"
    THUMBNAIL = "thumbnail"
    QUOTE = "quote"
    DOCUMENT = "document"
    PROJECT = "project"  # vMix, etc.


class MediaCategory(str, Enum):
    """Categories for organizing media"""
    SHOW = "show"
    EPISODE = "episode"
    LIBRARY = "library"
    RUNDOWN_ITEM = "rundown_item"
    ADVERTISEMENT = "advertisement"
    PROMO = "promo"


class MediaPathManager:
    """Manages all media paths with configurable roots and organization"""
    
    def __init__(self, media_root: str = None):
        """Initialize with media root from environment or default"""
        self.media_root = Path(media_root or os.getenv("MEDIA_ROOT", "/mnt/sync/disaffected"))
        
        # Configurable subdirectory names
        self.config = {
            "episodes": os.getenv("EPISODES_PATH", "episodes"),
            "show": os.getenv("SHOW_PATH", "show"),
            "library": os.getenv("LIBRARY_PATH", "lib"),
            "uploads": os.getenv("UPLOADS_PATH", "uploads"),
            
            # Episode subdirectories
            "assets": "assets",
            "rundown": "rundown",
            "exports": "exports",
            "preshow": "preshow",
            "captures": "captures",
            "distribute": "distribute",
            
            # Asset type subdirectories
            "audio": "audio",
            "video": "video",
            "graphics": "graphics",
            "images": "images",
            "quotes": "quotes",
            "thumbnails": "thumbnails",
            
            # Show subdirectories
            "logos": "logos",
            "branding": "branding",
            "posters": "posters",
            
            # Library subdirectories
            "ads": "ads",
            "ctas": "ctas",
            "promos": "promos",
            "music": "music",
            "sfx": "sfx",
            "templates": "templates",
        }
        
        # File extension mappings
        self.extensions = {
            MediaType.IMAGE: {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"},
            MediaType.VIDEO: {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"},
            MediaType.AUDIO: {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"},
            MediaType.GRAPHIC: {".psd", ".ai", ".svg", ".eps"},
            MediaType.DOCUMENT: {".pdf", ".doc", ".docx", ".txt", ".md"},
            MediaType.PROJECT: {".vmix", ".xml", ".json"},
        }
    
    # ========== Path Builders ==========
    
    def get_episodes_root(self) -> Path:
        """Get root path for all episodes"""
        return self.media_root / self.config["episodes"]
    
    def get_episode_path(self, episode_number: str) -> Path:
        """Get path for specific episode"""
        return self.get_episodes_root() / episode_number
    
    def get_show_root(self) -> Path:
        """Get root path for show assets"""
        return self.media_root / self.config["show"]
    
    def get_library_root(self) -> Path:
        """Get root path for library assets"""
        return self.media_root / self.config["library"]
    
    def get_uploads_root(self) -> Path:
        """Get root path for temporary uploads"""
        return self.media_root / self.config["uploads"]
    
    # ========== Episode Paths ==========
    
    def get_episode_assets(self, episode_number: str) -> Path:
        """Get episode assets directory"""
        return self.get_episode_path(episode_number) / self.config["assets"]
    
    def get_episode_rundown(self, episode_number: str) -> Path:
        """Get episode rundown directory"""
        return self.get_episode_path(episode_number) / self.config["rundown"]
    
    def get_episode_exports(self, episode_number: str) -> Path:
        """Get episode exports directory"""
        return self.get_episode_path(episode_number) / self.config["exports"]
    
    def get_episode_media_type_path(self, episode_number: str, media_type: MediaType) -> Path:
        """Get path for specific media type in episode"""
        assets_path = self.get_episode_assets(episode_number)
        
        type_map = {
            MediaType.AUDIO: self.config["audio"],
            MediaType.VIDEO: self.config["video"],
            MediaType.GRAPHIC: self.config["graphics"],
            MediaType.IMAGE: self.config["images"],
            MediaType.QUOTE: self.config["quotes"],
            MediaType.THUMBNAIL: self.config["thumbnails"],
        }
        
        subdir = type_map.get(media_type)
        if subdir:
            return assets_path / subdir
        return assets_path
    
    # ========== Show Paths ==========
    
    def get_show_logos_path(self) -> Path:
        """Get path for show logos"""
        return self.get_show_root() / self.config["logos"]
    
    def get_show_branding_path(self) -> Path:
        """Get path for show branding assets"""
        return self.get_show_root() / self.config["branding"]
    
    def get_show_posters_path(self) -> Path:
        """Get path for show posters"""
        return self.get_show_root() / self.config["posters"]
    
    # ========== Library Paths ==========
    
    def get_library_ads_path(self, advertiser: str = None) -> Path:
        """Get path for advertisement assets"""
        ads_path = self.get_library_root() / self.config["ads"]
        if advertiser:
            return ads_path / advertiser
        return ads_path
    
    def get_library_promos_path(self) -> Path:
        """Get path for promo assets"""
        return self.get_library_root() / self.config["promos"]
    
    def get_library_music_path(self) -> Path:
        """Get path for music library"""
        return self.get_library_root() / self.config["music"]
    
    # ========== Path Operations ==========
    
    def ensure_path(self, path: Path) -> Path:
        """Create directory if it doesn't exist"""
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_relative_path(self, full_path: Path) -> str:
        """Get path relative to media root"""
        try:
            return str(full_path.relative_to(self.media_root))
        except ValueError:
            return str(full_path)
    
    def resolve_path(self, relative_path: str) -> Path:
        """Resolve relative path to full path"""
        return self.media_root / relative_path
    
    # ========== File Operations ==========
    
    def validate_extension(self, filename: str, media_type: MediaType) -> bool:
        """Validate file extension for media type"""
        ext = Path(filename).suffix.lower()
        allowed = self.extensions.get(media_type, set())
        return ext in allowed
    
    def generate_filename(self, asset_id: str, media_type: MediaType, original_filename: str) -> str:
        """Generate standardized filename using asset ID"""
        ext = Path(original_filename).suffix.lower()
        return f"{asset_id}_{media_type.value}{ext}"
    
    def get_media_url(self, relative_path: str) -> str:
        """Generate URL for media file"""
        return f"/api/media/{relative_path}"
    
    # ========== Discovery ==========
    
    def list_episodes(self) -> List[str]:
        """List all episode numbers"""
        episodes_root = self.get_episodes_root()
        if not episodes_root.exists():
            return []
        
        episodes = []
        for item in episodes_root.iterdir():
            if item.is_dir() and item.name.isdigit():
                episodes.append(item.name)
        
        return sorted(episodes)
    
    def get_episode_info(self, episode_number: str) -> Dict[str, Any]:
        """Get information about an episode's file structure"""
        episode_path = self.get_episode_path(episode_number)
        if not episode_path.exists():
            return None
        
        info = {
            "number": episode_number,
            "path": str(episode_path),
            "has_rundown": self.get_episode_rundown(episode_number).exists(),
            "has_assets": self.get_episode_assets(episode_number).exists(),
            "has_exports": self.get_episode_exports(episode_number).exists(),
            "rundown_items": [],
            "asset_counts": {}
        }
        
        # Count rundown items
        rundown_path = self.get_episode_rundown(episode_number)
        if rundown_path.exists():
            info["rundown_items"] = [
                f.name for f in rundown_path.glob("*.md")
                if f.name != "info.md"
            ]
        
        # Count assets by type
        for media_type in [MediaType.AUDIO, MediaType.VIDEO, MediaType.IMAGE]:
            type_path = self.get_episode_media_type_path(episode_number, media_type)
            if type_path.exists():
                info["asset_counts"][media_type.value] = len(list(type_path.iterdir()))
        
        return info
    
    # ========== Dynamic Routing ==========
    
    def route_upload(self, category: MediaCategory, media_type: MediaType, 
                    identifier: str, filename: str) -> Dict[str, Any]:
        """
        Route an upload to the correct location based on category and type
        Returns dict with full_path, relative_path, and url
        """
        # Determine target directory based on category and type
        if category == MediaCategory.SHOW:
            if media_type == MediaType.LOGO:
                target_dir = self.get_show_logos_path()
            elif media_type == MediaType.POSTER:
                target_dir = self.get_show_posters_path()
            else:
                target_dir = self.get_show_branding_path()
                
        elif category == MediaCategory.EPISODE:
            episode_num = identifier.split('_')[0] if '_' in identifier else identifier
            target_dir = self.get_episode_media_type_path(episode_num, media_type)
            
        elif category == MediaCategory.LIBRARY:
            if media_type == MediaType.AUDIO:
                target_dir = self.get_library_music_path()
            elif identifier:  # Advertiser name
                target_dir = self.get_library_ads_path(identifier)
            else:
                target_dir = self.get_library_promos_path()
                
        elif category == MediaCategory.RUNDOWN_ITEM:
            # Rundown items go in episode rundown folder
            episode_num = identifier.split('_')[0] if '_' in identifier else identifier
            target_dir = self.get_episode_rundown(episode_num)
            
        else:
            # Default to uploads directory
            target_dir = self.get_uploads_root()
        
        # Ensure directory exists
        self.ensure_path(target_dir)
        
        # Generate standardized filename
        std_filename = self.generate_filename(identifier, media_type, filename)
        full_path = target_dir / std_filename
        relative_path = self.get_relative_path(full_path)
        
        return {
            "full_path": full_path,
            "relative_path": relative_path,
            "url": self.get_media_url(relative_path),
            "filename": std_filename,
            "directory": str(target_dir)
        }
    
    def resolve_media_request(self, url_path: str) -> Optional[Path]:
        """
        Resolve a media URL path to actual file path
        Returns None if file doesn't exist or path is invalid
        """
        # Remove leading /api/media/ if present
        if url_path.startswith("/api/media/"):
            url_path = url_path[11:]
        elif url_path.startswith("api/media/"):
            url_path = url_path[10:]
        elif url_path.startswith("/media/"):
            url_path = url_path[7:]
        elif url_path.startswith("media/"):
            url_path = url_path[6:]
        
        # Prevent directory traversal attacks
        if ".." in url_path or url_path.startswith("/"):
            return None
        
        full_path = self.media_root / url_path
        
        # Check if file exists and is within media root
        if full_path.exists() and full_path.is_file():
            try:
                # Ensure path is within media root (prevents symlink attacks)
                full_path.relative_to(self.media_root)
                return full_path
            except ValueError:
                return None
        
        return None
    
    def get_media_type_from_file(self, filepath: Path) -> Optional[MediaType]:
        """Determine media type from file extension"""
        ext = filepath.suffix.lower()
        
        for media_type, extensions in self.extensions.items():
            if ext in extensions:
                return media_type
        
        return None
    
    # ========== Batch Operations ==========
    
    def organize_episode_assets(self, episode_number: str):
        """
        Organize loose files in episode directory into proper subdirectories
        Useful for cleaning up after manual uploads
        """
        episode_path = self.get_episode_path(episode_number)
        if not episode_path.exists():
            return
        
        # Map extensions to subdirectories
        for file in episode_path.glob("*"):
            if file.is_file():
                media_type = self.get_media_type_from_file(file)
                if media_type:
                    target_dir = self.get_episode_media_type_path(episode_number, media_type)
                    self.ensure_path(target_dir)
                    target_path = target_dir / file.name
                    if not target_path.exists():
                        file.rename(target_path)
    
    # ========== Configuration ==========
    
    def update_config(self, updates: Dict[str, str]):
        """Update configuration with new paths"""
        self.config.update(updates)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            "media_root": str(self.media_root),
            "paths": self.config,
            "extensions": {k.value: list(v) for k, v in self.extensions.items()}
        }
    
    def save_config(self, filepath: str):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.get_config(), f, indent=2)
    
    def load_config(self, filepath: str):
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            config = json.load(f)
            self.media_root = Path(config["media_root"])
            self.config = config["paths"]


# Global instance
media_paths = MediaPathManager()