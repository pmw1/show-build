"""
Autosave History Service

Writes segment-level and episode-level snapshot files to the filesystem
as a safety net against data loss. Files are stored in:

    episodes/{episode_number}/.history/segments/{item_id}_{timestamp}.md
    episodes/{episode_number}/.history/episode/{episode_number}_{timestamp}.md

Segment snapshots: written every N seconds (default 30), retain last M files (default 20)
Episode snapshots: written every N seconds (default 300), retain last M files (default 12)

Files are markdown with YAML frontmatter for human readability and programmatic restoration.
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# In-memory throttle tracking (last write timestamps)
_last_segment_write: Dict[int, float] = {}  # item_id -> epoch
_last_episode_write: Dict[str, float] = {}  # episode_number -> epoch

# Default settings
DEFAULT_SETTINGS = {
    "enabled": True,
    "segment_interval_seconds": 30,
    "episode_interval_seconds": 300,
    "segment_retention_count": 20,
    "episode_retention_count": 12,
}


def get_autosave_settings() -> Dict[str, Any]:
    """Load autosave settings from the settings file, with defaults."""
    from pathlib import Path
    import json

    settings_file = Path("/app/storage/settings.json") if Path("/app").exists() else Path("app/storage/settings.json")
    try:
        if settings_file.exists():
            with open(settings_file) as f:
                all_settings = json.load(f)
            stored = all_settings.get("autosave_history", {})
            # Merge with defaults
            return {**DEFAULT_SETTINGS, **stored}
    except Exception as e:
        logger.warning(f"Could not load autosave settings: {e}")

    return dict(DEFAULT_SETTINGS)


def _get_episodes_root() -> Path:
    """Get the episodes root directory."""
    if Path("/home/episodes").exists():
        return Path("/home/episodes")
    elif Path("/mnt/sync/disaffected/episodes").exists():
        return Path("/mnt/sync/disaffected/episodes")
    return Path("/home/episodes")


def _ensure_history_dir(episode_number: str, subdir: str) -> Path:
    """Create and return the .history subdirectory for an episode."""
    episodes_root = _get_episodes_root()
    # Normalize episode number to 4 digits
    ep_num = str(episode_number).zfill(4)
    history_dir = episodes_root / ep_num / ".history" / subdir
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def _format_timestamp() -> str:
    """Generate a filesystem-safe timestamp string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")


def _prune_old_files(directory: Path, prefix: str, max_count: int):
    """Remove oldest files matching prefix, keeping only max_count."""
    try:
        matching = sorted(
            [f for f in directory.iterdir() if f.name.startswith(prefix) and f.suffix == ".md"],
            key=lambda f: f.stat().st_mtime
        )
        while len(matching) > max_count:
            oldest = matching.pop(0)
            oldest.unlink()
            logger.debug(f"Pruned old history file: {oldest.name}")
    except Exception as e:
        logger.warning(f"Error pruning history files in {directory}: {e}")


def write_segment_snapshot(
    episode_number: str,
    item_id: int,
    asset_id: str,
    title: str,
    item_type: str,
    script_content: str,
    order_in_rundown: int = 0,
    force: bool = False
) -> Optional[Path]:
    """
    Write a segment-level snapshot file if enough time has elapsed.

    Returns the path of the written file, or None if skipped.
    """
    settings = get_autosave_settings()
    if not settings.get("enabled", True):
        return None

    interval = settings.get("segment_interval_seconds", 30)
    retention = settings.get("segment_retention_count", 20)

    # Throttle check
    now = time.time()
    if not force and item_id in _last_segment_write:
        elapsed = now - _last_segment_write[item_id]
        if elapsed < interval:
            return None

    # Don't snapshot empty content
    if not script_content or not script_content.strip():
        return None

    try:
        history_dir = _ensure_history_dir(episode_number, "segments")
        timestamp = _format_timestamp()
        filename = f"{item_id}_{timestamp}.md"
        filepath = history_dir / filename

        content_length = len(script_content)

        safe_title = (title or '').replace('"', "'")
        ts = datetime.now(timezone.utc).isoformat()
        file_content = f"""---
item_id: {item_id}
asset_id: "{asset_id or ''}"
title: "{safe_title}"
type: "{item_type or 'segment'}"
episode: "{episode_number}"
order: {order_in_rundown}
timestamp: "{ts}"
content_length: {content_length}
---

{script_content}
"""
        filepath.write_text(file_content, encoding="utf-8")
        _last_segment_write[item_id] = now

        # Prune old files for this item
        _prune_old_files(history_dir, f"{item_id}_", retention)

        logger.info(f"Segment snapshot: {filename} ({content_length} chars)")
        return filepath

    except Exception as e:
        logger.error(f"Failed to write segment snapshot for item {item_id}: {e}")
        return None


def write_episode_snapshot(
    episode_number: str,
    episode_title: str,
    rundown_items: list,
    force: bool = False
) -> Optional[Path]:
    """
    Write an episode-level snapshot file containing all rundown items.

    Args:
        episode_number: Episode number (e.g., "0264")
        episode_title: Episode title
        rundown_items: List of RundownItem ORM objects (or dicts with matching fields)
        force: Skip throttle check

    Returns the path of the written file, or None if skipped.
    """
    settings = get_autosave_settings()
    if not settings.get("enabled", True):
        return None

    interval = settings.get("episode_interval_seconds", 300)
    retention = settings.get("episode_retention_count", 12)

    ep_num = str(episode_number).zfill(4)

    # Throttle check
    now = time.time()
    if not force and ep_num in _last_episode_write:
        elapsed = now - _last_episode_write[ep_num]
        if elapsed < interval:
            return None

    if not rundown_items:
        return None

    try:
        history_dir = _ensure_history_dir(episode_number, "episode")
        timestamp = _format_timestamp()
        filename = f"{ep_num}_{timestamp}.md"
        filepath = history_dir / filename

        # Build the episode snapshot
        # Support both ORM objects and dicts
        def _get(obj, key, default=""):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        # Sort items by order
        sorted_items = sorted(rundown_items, key=lambda x: _get(x, "order_in_rundown", 0) or 0)

        total_content_length = sum(len(_get(item, "script_content", "") or "") for item in sorted_items)

        lines = [
            "---",
            f'episode: "{ep_num}"',
            f'title: "{(episode_title or "").replace(chr(34), chr(92) + chr(34))}"',
            f'timestamp: "{datetime.now(timezone.utc).isoformat()}"',
            f"item_count: {len(sorted_items)}",
            f"total_content_length: {total_content_length}",
            "---",
            "",
        ]

        for item in sorted_items:
            item_id = _get(item, "id", "")
            asset_id = _get(item, "asset_id", "")
            title = _get(item, "title", "Untitled")
            item_type = _get(item, "item_type", "segment")
            order = _get(item, "order_in_rundown", 0)
            script = _get(item, "script_content", "") or ""

            lines.append(f"## [{order}] {title}")
            lines.append(f"<!-- item_id: {item_id} | asset_id: {asset_id} | type: {item_type} -->")
            lines.append("")
            lines.append(script)
            lines.append("")
            lines.append("---")
            lines.append("")

        file_content = "\n".join(lines)
        filepath.write_text(file_content, encoding="utf-8")
        _last_episode_write[ep_num] = now

        # Prune old files
        _prune_old_files(history_dir, f"{ep_num}_", retention)

        logger.info(f"Episode snapshot: {filename} ({len(sorted_items)} items, {total_content_length} chars)")
        return filepath

    except Exception as e:
        logger.error(f"Failed to write episode snapshot for {episode_number}: {e}")
        return None


def list_segment_snapshots(episode_number: str, item_id: int) -> List[Dict[str, Any]]:
    """List available segment snapshots for a specific item."""
    try:
        history_dir = _ensure_history_dir(episode_number, "segments")
        prefix = f"{item_id}_"
        files = sorted(
            [f for f in history_dir.iterdir() if f.name.startswith(prefix) and f.suffix == ".md"],
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        results = []
        for f in files:
            stat = f.stat()
            results.append({
                "filename": f.name,
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "path": str(f),
            })
        return results
    except Exception as e:
        logger.error(f"Error listing segment snapshots: {e}")
        return []


def list_episode_snapshots(episode_number: str) -> List[Dict[str, Any]]:
    """List available episode snapshots."""
    try:
        ep_num = str(episode_number).zfill(4)
        history_dir = _ensure_history_dir(episode_number, "episode")
        prefix = f"{ep_num}_"
        files = sorted(
            [f for f in history_dir.iterdir() if f.name.startswith(prefix) and f.suffix == ".md"],
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        results = []
        for f in files:
            stat = f.stat()
            results.append({
                "filename": f.name,
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "path": str(f),
            })
        return results
    except Exception as e:
        logger.error(f"Error listing episode snapshots: {e}")
        return []


def read_segment_snapshot(episode_number: str, filename: str) -> Optional[Dict[str, Any]]:
    """Read a segment snapshot file and parse its frontmatter + content."""
    try:
        history_dir = _ensure_history_dir(episode_number, "segments")
        filepath = history_dir / filename
        if not filepath.exists():
            return None

        text = filepath.read_text(encoding="utf-8")
        return _parse_snapshot(text, filepath)
    except Exception as e:
        logger.error(f"Error reading segment snapshot {filename}: {e}")
        return None


def read_episode_snapshot(episode_number: str, filename: str) -> Optional[Dict[str, Any]]:
    """Read an episode snapshot file."""
    try:
        history_dir = _ensure_history_dir(episode_number, "episode")
        filepath = history_dir / filename
        if not filepath.exists():
            return None

        text = filepath.read_text(encoding="utf-8")
        return _parse_snapshot(text, filepath)
    except Exception as e:
        logger.error(f"Error reading episode snapshot {filename}: {e}")
        return None


def _parse_snapshot(text: str, filepath: Path) -> Dict[str, Any]:
    """Parse a snapshot file into frontmatter dict + body content."""
    import yaml

    result = {
        "filename": filepath.name,
        "frontmatter": {},
        "content": text,
        "items": [],
    }

    # Extract frontmatter
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                result["frontmatter"] = yaml.safe_load(parts[1]) or {}
            except Exception:
                pass
            result["content"] = parts[2].strip()

    # For episode snapshots, parse individual items
    if "item_count" in result["frontmatter"]:
        import re
        # Split on ## [order] headers
        item_blocks = re.split(r'^## \[(\d+)\] (.+)$', result["content"], flags=re.MULTILINE)
        # item_blocks: [preamble, order1, title1, content1, order2, title2, content2, ...]
        i = 1
        while i + 2 < len(item_blocks):
            order = int(item_blocks[i])
            title = item_blocks[i + 1]
            block = item_blocks[i + 2].strip()

            # Extract the comment line with IDs
            item_meta = {}
            comment_match = re.match(r'<!-- item_id: (\S+) \| asset_id: (\S+) \| type: (\S+) -->', block)
            if comment_match:
                item_meta["item_id"] = comment_match.group(1)
                item_meta["asset_id"] = comment_match.group(2)
                item_meta["type"] = comment_match.group(3)
                # Content is everything after the comment line, before trailing ---
                content_after_comment = block[comment_match.end():].strip()
                # Remove trailing --- separator
                if content_after_comment.endswith("---"):
                    content_after_comment = content_after_comment[:-3].strip()
                item_meta["script_content"] = content_after_comment
            else:
                item_meta["script_content"] = block

            item_meta["order"] = order
            item_meta["title"] = title
            result["items"].append(item_meta)
            i += 3

    return result


def restore_segment_from_snapshot(
    db,
    episode_number: str,
    filename: str,
) -> Optional[Dict[str, Any]]:
    """
    Restore a segment from a snapshot file. Matches by item_id (index-agnostic).

    Returns dict with restoration details or None on failure.
    """
    from models_v2 import RundownItem

    snapshot = read_segment_snapshot(episode_number, filename)
    if not snapshot:
        return None

    item_id = snapshot["frontmatter"].get("item_id")
    if not item_id:
        return None

    item = db.query(RundownItem).filter(RundownItem.id == int(item_id)).first()
    if not item:
        # Fallback: try asset_id
        asset_id = snapshot["frontmatter"].get("asset_id")
        if asset_id:
            item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()

    if not item:
        return None

    old_length = len(item.script_content or "")
    item.script_content = snapshot["content"]
    item.updated_at = datetime.now(timezone.utc)

    # Create a version snapshot for the restore
    try:
        from episodes_router import create_content_version
        create_content_version(db, item, change_type="restore")
    except Exception as e:
        logger.warning(f"Could not create version for restore: {e}")

    db.commit()

    return {
        "item_id": item.id,
        "asset_id": item.asset_id,
        "title": item.title,
        "old_length": old_length,
        "new_length": len(snapshot["content"]),
        "restored_from": filename,
        "snapshot_timestamp": snapshot["frontmatter"].get("timestamp"),
    }


def restore_episode_from_snapshot(
    db,
    episode_number: str,
    filename: str,
) -> Optional[Dict[str, Any]]:
    """
    Restore all segments from an episode snapshot. Uses item_id for matching,
    and restores order_in_rundown from the snapshot's index values.

    Returns dict with restoration details or None on failure.
    """
    from models_v2 import RundownItem

    snapshot = read_episode_snapshot(episode_number, filename)
    if not snapshot or not snapshot["items"]:
        return None

    restored = []
    not_found = []

    for snap_item in snapshot["items"]:
        item_id = snap_item.get("item_id")
        item = None

        if item_id:
            try:
                item = db.query(RundownItem).filter(RundownItem.id == int(item_id)).first()
            except (ValueError, TypeError):
                pass

        if not item:
            asset_id = snap_item.get("asset_id")
            if asset_id:
                item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()

        if not item:
            not_found.append(snap_item.get("title", "Unknown"))
            continue

        old_length = len(item.script_content or "")
        item.script_content = snap_item.get("script_content", "")
        item.order_in_rundown = snap_item.get("order", item.order_in_rundown)
        item.updated_at = datetime.now(timezone.utc)

        # Create version snapshot
        try:
            from episodes_router import create_content_version
            create_content_version(db, item, change_type="restore")
        except Exception:
            pass

        restored.append({
            "item_id": item.id,
            "title": item.title,
            "old_length": old_length,
            "new_length": len(snap_item.get("script_content", "")),
        })

    db.commit()

    return {
        "episode": episode_number,
        "restored_from": filename,
        "snapshot_timestamp": snapshot["frontmatter"].get("timestamp"),
        "items_restored": len(restored),
        "items_not_found": not_found,
        "details": restored,
    }
