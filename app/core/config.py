"""
Configuration management for Show-Build application
Handles environment variables and dynamic path configuration
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with configurable paths"""
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://showbuild:showbuild@show-build-postgres/showbuild"
    )
    
    # Authentication
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 2880  # 48 hours
    
    # Media Storage Paths (configurable)
    media_root: str = os.getenv("MEDIA_ROOT", "/mnt/sync/disaffected")
    episodes_path: str = os.getenv("EPISODES_PATH", "episodes")
    show_path: str = os.getenv("SHOW_PATH", "show")
    library_path: str = os.getenv("LIBRARY_PATH", "lib")
    
    # Specific media subdirectories
    show_logos_subdir: str = "logos"
    show_branding_subdir: str = "branding"
    episode_assets_subdir: str = "assets"
    episode_rundown_subdir: str = "rundown"
    episode_exports_subdir: str = "exports"
    episode_preshow_subdir: str = "preshow"
    
    # Upload settings
    max_upload_size: int = 100 * 1024 * 1024  # 100MB default
    allowed_image_extensions: set = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
    allowed_video_extensions: set = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    allowed_audio_extensions: set = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
    
    # API settings
    api_prefix: str = "/api"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_episodes_root(self) -> Path:
        """Get the full path to episodes directory"""
        return Path(self.media_root) / self.episodes_path
    
    def get_episode_path(self, episode_number: str) -> Path:
        """Get the full path to a specific episode"""
        return self.get_episodes_root() / episode_number
    
    def get_show_root(self) -> Path:
        """Get the full path to show directory"""
        return Path(self.media_root) / self.show_path
    
    def get_show_logos_path(self) -> Path:
        """Get the full path to show logos directory"""
        return self.get_show_root() / self.show_logos_subdir
    
    def get_library_root(self) -> Path:
        """Get the full path to library directory"""
        return Path(self.media_root) / self.library_path
    
    def get_episode_assets_path(self, episode_number: str) -> Path:
        """Get the full path to episode assets"""
        return self.get_episode_path(episode_number) / self.episode_assets_subdir
    
    def get_episode_rundown_path(self, episode_number: str) -> Path:
        """Get the full path to episode rundown"""
        return self.get_episode_path(episode_number) / self.episode_rundown_subdir
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        dirs_to_create = [
            self.get_show_root(),
            self.get_show_logos_path(),
            self.get_show_root() / self.show_branding_subdir,
            self.get_library_root(),
        ]
        
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)


# Singleton instance
settings = Settings()

# Don't create directories on import - will be done on startup if needed
# settings.ensure_directories()