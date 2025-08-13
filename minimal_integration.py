"""
Minimal database integration for existing Show-Build API.
Adds only essential coordination features without breaking current endpoints.
"""
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
import os

# Minimal models - only what's needed for coordination
class MinimalEpisode:
    """Minimal episode tracking for processing coordination."""
    
    @staticmethod
    def mark_processing(episode_number: str, db: Session):
        """Mark episode as being processed to prevent conflicts."""
        # Check if episode exists on filesystem first
        base_path = os.getenv("EPISODE_ROOT", "/home/episodes")
        episode_path = os.path.join(base_path, episode_number)
        
        if not os.path.isdir(episode_path):
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")
        
        # For now, we can use a simple file-based lock
        lock_file = os.path.join(episode_path, ".processing_lock")
        
        if os.path.exists(lock_file):
            raise HTTPException(status_code=409, detail="Episode is already being processed")
        
        # Create lock file
        with open(lock_file, 'w') as f:
            f.write(f"Processing started at {os.popen('date').read().strip()}")
        
        return True
    
    @staticmethod
    def clear_processing(episode_number: str):
        """Clear processing lock for episode."""
        base_path = os.getenv("EPISODE_ROOT", "/home/episodes")
        lock_file = os.path.join(base_path, episode_number, ".processing_lock")
        
        if os.path.exists(lock_file):
            os.remove(lock_file)
    
    @staticmethod
    def is_processing(episode_number: str) -> bool:
        """Check if episode is currently being processed."""
        base_path = os.getenv("EPISODE_ROOT", "/home/episodes")
        lock_file = os.path.join(base_path, episode_number, ".processing_lock")
        
        return os.path.exists(lock_file)

def get_processing_status(episode_number: str):
    """Minimal endpoint to check processing status without database dependency."""
    return {
        "episode_number": episode_number,
        "is_processing": MinimalEpisode.is_processing(episode_number),
        "has_episode_data": os.path.isdir(f"/home/episodes/{episode_number}")
    }