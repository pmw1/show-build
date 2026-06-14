"""
Enhanced path management system for Show-Build project.
Handles Obsidian integration, Docker environments, and CLI tool migration.
"""
from pathlib import Path
from typing import Optional, Dict, List, Union
import os
import logging

logger = logging.getLogger(__name__)

class ShowBuildPaths:
    """
    Centralized path management for Show-Build project.
    Automatically detects environment and provides consistent paths.
    """
    
    def __init__(self):
        # Detect if we're running in Docker container or development
        self.is_docker = Path('/app').exists()

        # Base paths with fallback detection for different mount configurations
        if self.is_docker:
            # Production/Docker paths
            self.app_root = Path('/app')
            self.project_root = Path('/app').parent

            # Try standard Docker mounts first, then Kairo/worker mounts
            if Path('/home/episodes').exists():
                # Standard show-build-server container
                self.episodes_root = Path('/home/episodes')
                self.shared_media = Path('/shared_media')
                self.repo_root = Path('/home/repo')
                self.media_assets_root = Path('/home/media_assets')
                # Unbound media pool — mounted at /home/pool (host:
                # media_assets/pool). Holds episodes/, ads/, repo/, whiteboard/.
                self.pool_root = Path('/home/pool')
            elif Path('/mnt/sync/disaffected/episodes').exists():
                # Kairo worker with /mnt/sync mount
                self.episodes_root = Path('/mnt/sync/disaffected/episodes')
                self.shared_media = Path('/mnt/sync/shared_media')
                self.repo_root = Path('/mnt/sync/disaffected/repo')
                self.media_assets_root = Path('/mnt/sync/media_assets')
                self.pool_root = Path('/mnt/sync/media_assets/pool')
            else:
                # Fallback to standard paths (will warn if not found)
                self.episodes_root = Path('/home/episodes')
                self.shared_media = Path('/shared_media')
                self.repo_root = Path('/home/repo')
                self.media_assets_root = Path('/home/media_assets')
                self.pool_root = Path('/home/pool')
        else:
            # Development paths
            self.app_root = Path(__file__).parent.parent
            self.project_root = self.app_root.parent
            # In development, episodes might be relative or absolute
            self.episodes_root = Path('/mnt/sync/disaffected/episodes')
            self.shared_media = Path('/mnt/sync/shared_media')
            self.repo_root = Path('/data/sync/disaffected/repo')
            self.media_assets_root = Path('/data/sync/media_assets')
            self.pool_root = Path('/data/sync/media_assets/pool')

        # Verify critical paths
        self._verify_paths()

        logger.info(f"ShowBuildPaths initialized - Docker: {self.is_docker}")
        logger.info(f"Episodes root: {self.episodes_root}")
        logger.info(f"App root: {self.app_root}")

    def _verify_paths(self):
        """Verify that critical paths exist and are accessible."""
        if not self.episodes_root.exists():
            logger.warning(f"Episodes directory not found: {self.episodes_root}")
        if not self.app_root.exists():
            logger.error(f"App directory not found: {self.app_root}")
            
    # Episode Management
    def get_episode_dir(self, episode_id: str) -> Path:
        """Get the root directory for a specific episode."""
        episode_num = self._normalize_episode_id(episode_id)
        return self.episodes_root / episode_num
    
    def get_episode_info_path(self, episode_id: str) -> Path:
        """Get path to episode info.md file."""
        return self.get_episode_dir(episode_id) / 'info.md'
    
    def get_rundown_dir(self, episode_id: str) -> Path:
        """Get the rundown directory for an episode."""
        return self.get_episode_dir(episode_id) / 'rundown'
    
    def get_assets_dir(self, episode_id: str) -> Path:
        """Get the assets directory for an episode."""
        return self.get_episode_dir(episode_id) / 'assets'
    
    def get_asset_type_dir(self, episode_id: str, asset_type: str) -> Path:
        """Get specific asset type directory (audio, video, graphics, etc.)."""
        valid_types = ['audio', 'video', 'graphics', 'images', 'quotes', 
                      'generated_quotes', 'thumbnails']
        if asset_type not in valid_types:
            raise ValueError(f"Invalid asset type: {asset_type}. Valid: {valid_types}")
        return self.get_assets_dir(episode_id) / asset_type
    
    def get_preshow_dir(self, episode_id: str) -> Path:
        """Get the preshow directory for an episode."""
        return self.get_episode_dir(episode_id) / 'preshow'
    
    def get_captures_dir(self, episode_id: str) -> Path:
        """Get the captures directory for an episode.""" 
        return self.get_episode_dir(episode_id) / 'captures'
    
    def get_exports_dir(self, episode_id: str) -> Path:
        """Get the exports directory for an episode."""
        return self.get_episode_dir(episode_id) / 'exports'
    
    def get_publish_dir(self, episode_id: str) -> Path:
        """Get the publish directory for an episode."""
        return self.get_episode_dir(episode_id) / 'publish'

    def get_whiteboard_media_dir(self, episode_id: str) -> Path:
        """Get the whiteboard media directory for an episode.

        RELOCATED into the unbound media pool:
          /home/pool/whiteboard/{episode}/ (container)
          /data/sync/media_assets/pool/whiteboard/{episode}/ (host)
        Served via the /pool static mount (was /repo/whiteboard).
        """
        return self.get_pool_whiteboard_dir(episode_id)

    # ---- Unbound media pool (media_assets/pool) ----------------------------
    # Single bag of reusable / released media, mounted at /home/pool. Layout:
    #   episodes/{ep}/{file}          cue-released media + loose per-episode uploads (FLAT)
    #   ads/{advertiserID}/{file}     reusable ad media (scaffold)
    #   repo/{file}                   other reusables: promos, CTAs, etc. (scaffold)
    #   whiteboard/{ep}/{file}        whiteboard media
    def get_pool_root(self) -> Path:
        """Root of the unbound media pool."""
        return self.pool_root

    def get_pool_episodes_dir(self, episode_id: str) -> Path:
        """Per-episode pool dir for cue-released / loose media (FLAT, no subdirs)."""
        episode_num = self._normalize_episode_id(episode_id)
        return self.pool_root / 'episodes' / episode_num

    def get_pool_whiteboard_dir(self, episode_id: str) -> Path:
        """Per-episode whiteboard media dir within the pool."""
        episode_num = self._normalize_episode_id(episode_id)
        return self.pool_root / 'whiteboard' / episode_num

    def get_pool_ads_dir(self, advertiser_id: str) -> Path:
        """Per-advertiser reusable ad-media dir (SCAFFOLD: not yet wired to uploads)."""
        return self.pool_root / 'ads' / str(advertiser_id)

    def get_pool_repo_dir(self) -> Path:
        """Flat repo of other reusables — promos, CTAs, etc. (SCAFFOLD; layout TBD)."""
        return self.pool_root / 'repo'
    
    # CLI Tool Integration Paths
    def get_compiled_script_path(self, episode_id: str) -> Path:
        """Get path to compiled script HTML file."""
        return self.get_rundown_dir(episode_id) / 'compiled_script.html'
    
    def get_quotes_json_path(self, episode_id: str) -> Path:
        """Get path to quotes.json file."""
        return self.get_asset_type_dir(episode_id, 'quotes') / 'quotes.json'
    
    def get_vmix_config_path(self, episode_id: str) -> Path:
        """Get path to vMix configuration file."""
        episode_dir = self.get_episode_dir(episode_id)
        # Look for various vMix file patterns
        patterns = [f'{episode_id}.vmix', '*.vmix']
        for pattern in patterns:
            matches = list(episode_dir.glob(pattern))
            if matches:
                return matches[0]
        # Return expected path even if file doesn't exist
        return episode_dir / f'{episode_id}.vmix'
    
    # Application Paths
    def get_tools_dir(self) -> Path:
        """Get the tools directory."""
        return self.project_root / 'tools'
    
    def get_templates_dir(self) -> Path:
        """Get the templates directory."""
        return self.get_tools_dir() / 'blueprints'
    
    def get_storage_dir(self) -> Path:
        """Get the app storage directory."""
        return self.app_root / 'storage'
    
    def get_logs_dir(self) -> Path:
        """Get the logs directory."""
        if self.is_docker:
            return Path('/home/logs')
        else:
            return self.app_root / 'logs'
    
    # Utility Methods
    def _normalize_episode_id(self, episode_id: str) -> str:
        """Normalize episode ID to standard format (e.g., '225' -> '0225')."""
        # Remove any leading zeros, then pad to 4 digits
        episode_num = str(int(episode_id))
        return episode_num.zfill(4)
    
    def list_episodes(self) -> List[str]:
        """List all available episodes."""
        if not self.episodes_root.exists():
            return []
        
        episodes = []
        for item in self.episodes_root.iterdir():
            if item.is_dir() and item.name.isdigit():
                episodes.append(item.name)
        
        return sorted(episodes)
    
    def episode_exists(self, episode_id: str) -> bool:
        """Check if an episode directory exists."""
        return self.get_episode_dir(episode_id).exists()
    
    def get_rundown_files(self, episode_id: str) -> List[Path]:
        """Get all markdown files in the rundown directory."""
        rundown_dir = self.get_rundown_dir(episode_id)
        if not rundown_dir.exists():
            return []
        
        md_files = []
        for file in rundown_dir.glob('*.md'):
            # Skip compiled script and other generated files
            if not file.name.startswith('compiled_'):
                md_files.append(file)
        
        return sorted(md_files)
    
    def create_episode_scaffold(self, episode_id: str) -> Dict[str, Path]:
        """Create the complete directory structure for a new episode."""
        episode_dir = self.get_episode_dir(episode_id)
        
        # Standard episode directory structure
        directories = {
            'root': episode_dir,
            'assets': episode_dir / 'assets',
            'assets_audio': episode_dir / 'assets' / 'audio',
            'assets_video': episode_dir / 'assets' / 'video', 
            'assets_graphics': episode_dir / 'assets' / 'graphics',
            'assets_images': episode_dir / 'assets' / 'images',
            'assets_quotes': episode_dir / 'assets' / 'quotes',
            'assets_generated_quotes': episode_dir / 'assets' / 'generated_quotes',
            'assets_thumbnails': episode_dir / 'assets' / 'thumbnails',
            'rundown': episode_dir / 'rundown',
            'preshow': episode_dir / 'preshow',
            'captures': episode_dir / 'captures',
            'exports': episode_dir / 'exports',
            'publish': episode_dir / 'publish'
        }
        
        # Create directories
        for name, path in directories.items():
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path}")
            except Exception as e:
                logger.error(f"Failed to create directory {path}: {e}")
        
        # Create default info.md file
        info_path = episode_dir / 'info.md'
        if not info_path.exists():
            self._create_default_info_file(episode_id, info_path)
        
        return directories
    
    def _create_default_info_file(self, episode_id: str, info_path: Path):
        """Create a default info.md file with YAML frontmatter."""
        from datetime import datetime, timedelta
        
        # Calculate next Saturday (typical air date)
        today = datetime.now()
        days_until_saturday = (5 - today.weekday()) % 7  # Saturday is 5
        if days_until_saturday == 0:  # If today is Saturday
            days_until_saturday = 7
        air_date = today + timedelta(days=days_until_saturday)
        
        default_content = f"""---
type: full_show
airdate: {air_date.strftime('%Y-%m-%d')}
episode_number: {int(episode_id)}
title: "Episode {episode_id}"
subtitle: "TBD"
duration: "01:00:00"
guest: ""
tags: []
slug: "episode-{episode_id}"
status: draft
---

# Episode {episode_id}

## Overview
Episode overview and notes go here.

## Segments
- TBD

## Notes
- Production notes
"""
        
        try:
            with open(info_path, 'w', encoding='utf-8') as f:
                f.write(default_content)
            logger.info(f"Created default info.md: {info_path}")
        except Exception as e:
            logger.error(f"Failed to create info.md: {e}")

# Global instance
paths = ShowBuildPaths()

# Convenience functions for backward compatibility  
def get_episode_dir(episode_id: str) -> Path:
    return paths.get_episode_dir(episode_id)

def get_rundown_dir(episode_id: str) -> Path:
    return paths.get_rundown_dir(episode_id)

def get_assets_dir(episode_id: str) -> Path:
    return paths.get_assets_dir(episode_id)