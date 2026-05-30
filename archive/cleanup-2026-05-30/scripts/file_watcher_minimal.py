"""
Minimal file watcher to detect new/changed markdown files.
Records creation/modification without disrupting current workflow.
"""
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import os
import json
import time

class MarkdownFileHandler(FileSystemEventHandler):
    """Watch for markdown file changes in episode directories."""
    
    def __init__(self, base_path="/home/episodes"):
        self.base_path = base_path
        self.log_file = os.path.join(base_path, ".file_changes.json")
        
    def log_change(self, event_type, file_path, episode_number):
        """Log file changes to simple JSON file."""
        change_record = {
            "timestamp": time.time(),
            "event_type": event_type,
            "file_path": file_path,
            "episode_number": episode_number,
            "filename": os.path.basename(file_path)
        }
        
        # Read existing log
        changes = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    changes = json.load(f)
            except:
                changes = []
        
        # Add new change
        changes.append(change_record)
        
        # Keep only last 1000 changes
        changes = changes[-1000:]
        
        # Write back
        with open(self.log_file, 'w') as f:
            json.dump(changes, f, indent=2)
        
        print(f"[FILE_WATCHER] {event_type}: {file_path}")
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        if file_path.endswith('.md'):
            # Extract episode number from path like /home/episodes/0237/rundown/file.md
            path_parts = Path(file_path).parts
            if 'episodes' in path_parts:
                episodes_idx = path_parts.index('episodes')
                if episodes_idx + 1 < len(path_parts):
                    episode_number = path_parts[episodes_idx + 1]
                    self.log_change("created", file_path, episode_number)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        if file_path.endswith('.md'):
            # Extract episode number from path
            path_parts = Path(file_path).parts
            if 'episodes' in path_parts:
                episodes_idx = path_parts.index('episodes')
                if episodes_idx + 1 < len(path_parts):
                    episode_number = path_parts[episodes_idx + 1]
                    self.log_change("modified", file_path, episode_number)

def start_file_watcher(episodes_path="/home/episodes"):
    """Start watching for markdown file changes."""
    event_handler = MarkdownFileHandler(episodes_path)
    observer = Observer()
    observer.schedule(event_handler, episodes_path, recursive=True)
    observer.start()
    print(f"[FILE_WATCHER] Started watching {episodes_path}")
    return observer

# API endpoint to get recent changes
def get_recent_changes(episodes_path="/home/episodes", limit=50):
    """Get recent markdown file changes."""
    log_file = os.path.join(episodes_path, ".file_changes.json")
    
    if not os.path.exists(log_file):
        return []
    
    try:
        with open(log_file, 'r') as f:
            changes = json.load(f)
        
        # Return most recent changes first
        return sorted(changes, key=lambda x: x['timestamp'], reverse=True)[:limit]
    except:
        return []