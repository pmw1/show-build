"""
Episode metadata and info router.
Handles episode info, script, statistics, and metadata save operations.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional, Dict, Any
from pathlib import Path
import yaml
import re
import logging
from auth.utils import get_current_user_or_key
from database import get_db
from sqlalchemy.orm import Session
from datetime import datetime

from ._shared import EPISODES_ROOT, logger

router = APIRouter()


@router.get("/{episode_number}/script")
async def get_episode_script(
    episode_number: str,
    format: str = "markdown",  # markdown, html, text
    current_user: Optional[dict] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the compiled script for an episode from database.

    Script Storage Strategy:
    - Individual segments are stored in rundown_items.script_content (database)
    - The full script is compiled from all segments in order_in_rundown order
    """
    from models_v2 import Episode, Rundown, RundownItem

    try:
        episode_num_int = int(episode_number)
        episode = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        # Get rundown items from database
        rundowns = db.query(Rundown).filter(Rundown.episode_id == episode.id).all()
        if not rundowns:
            return {
                "episode_number": episode_number,
                "script": "",
                "segments": [],
                "format": format,
                "total_segments": 0,
                "word_count": 0
            }

        segments = []
        compiled_script = []

        for rundown in rundowns:
            items = db.query(RundownItem).filter(
                RundownItem.rundown_id == rundown.id
            ).order_by(RundownItem.order_in_rundown).all()

            for item in items:
                script_text = item.script_content or ""
                segment_info = {
                    "asset_id": item.asset_id,
                    "order": item.order_in_rundown or 0,
                    "type": item.item_type or "segment",
                    "title": item.title or "Untitled",
                    "duration": item.duration or "00:00:00",
                    "script": script_text
                }
                segments.append(segment_info)

                if script_text:
                    compiled_script.append(f"### {segment_info['title']}\n\n{script_text}")

        # Sort by order
        segments.sort(key=lambda x: x["order"])

        # Join all scripts
        full_script = "\n\n---\n\n".join(compiled_script)

        # Convert format if needed
        if format == "html":
            try:
                import markdown
                full_script = markdown.markdown(full_script)
            except ImportError:
                logger.warning("markdown module not available, returning raw markdown")
        elif format == "text":
            full_script = re.sub(r'#{1,6}\s+', '', full_script)
            full_script = re.sub(r'\*\*(.+?)\*\*', r'\1', full_script)
            full_script = re.sub(r'\*(.+?)\*', r'\1', full_script)
            full_script = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', full_script)

        return {
            "episode_number": episode_number,
            "script": full_script,
            "segments": segments,
            "format": format,
            "total_segments": len(segments),
            "word_count": len(full_script.split())
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode number format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error compiling script from database: {e}")
        raise HTTPException(status_code=500, detail=f"Error compiling script: {str(e)}")


@router.get("/{episode_number}/info")
async def get_episode_info(episode_number: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get episode metadata from database."""
    from models_v2 import Episode, Season, Show

    try:
        # Convert episode number to int
        episode_num_int = int(episode_number)

        # Get episode from database
        episode = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        # Get show timezone via Season -> Show relationship
        show_timezone = "America/New_York"  # Default fallback
        show_name = None
        if episode.season_id:
            season = db.query(Season).filter(Season.id == episode.season_id).first()
            if season and season.show_id:
                show = db.query(Show).filter(Show.id == season.show_id).first()
                if show:
                    show_timezone = show.timezone or "America/New_York"
                    show_name = show.name

        # Convert database record to info format
        info = {
            "episode_number": f"{episode.episode_number:04d}",
            "title": episode.title or "Untitled",
            "slug": episode.slug or f"episode-{episode_number}",
            "status": episode.status or "draft",
            "airdate": episode.air_date.isoformat() if episode.air_date else None,
            "airtime": episode.air_time or "",
            "airtimezone": episode.air_timezone or show_timezone,
            "show_timezone": show_timezone,
            "show_name": show_name,
            "publish_date": episode.publish_date.isoformat() if episode.publish_date else None,
            "duration": episode.duration_formatted or "01:00:00",
            "guest": episode.guest_name or "",
            "guest_bio": episode.guest_bio or "",
            "guest_website": episode.guest_website or "",
            "template_type": episode.template_type or "",
            "template_id": episode.template_id or "",
            "template_name": episode.template_name or "",
            "asset_id": episode.asset_id,
            "season_id": episode.season_id,
            "created_at": episode.created_at.isoformat() if episode.created_at else None,
            "updated_at": episode.updated_at.isoformat() if episode.updated_at else None,
            "is_test_data": episode.is_test_data or False,
            "is_dummy": episode.is_dummy or False,

            # Core description
            "subtitle": episode.subtitle or "",
            "description": episode.description or "",
            "tags": episode.tags or "",
            "notes": episode.notes or "",

            # Content rating
            "explicit": episode.explicit or False,
            "content_warnings": episode.content_warnings or "",

            # Production crew
            "recording_date": episode.recording_date.isoformat() if episode.recording_date else None,
            "producer": episode.producer or "",
            "editor": episode.editor or "",

            # Master publishing control
            "publish_status": episode.publish_status or "draft",
            "schedule_datetime": episode.schedule_datetime.isoformat() if episode.schedule_datetime else None,
            "visibility": episode.visibility or "public",

            # OmnyStudio
            "omny_description": episode.omny_description or "",
            "omny_visibility": episode.omny_visibility or "public",
            "omny_publish_status": episode.omny_publish_status or "draft",
            "omny_schedule_datetime": episode.omny_schedule_datetime.isoformat() if episode.omny_schedule_datetime else None,

            # YouTube
            "yt_title": episode.yt_title or "",
            "yt_description": episode.yt_description or "",
            "yt_tags": episode.yt_tags or "",
            "yt_privacy_status": episode.yt_privacy_status or "private",
            "yt_schedule_datetime": episode.yt_schedule_datetime.isoformat() if episode.yt_schedule_datetime else None,

            # Social media
            "social_hashtags": episode.social_hashtags or "",
            "twitter_post_text": episode.twitter_post_text or "",
            "twitter_schedule_datetime": episode.twitter_schedule_datetime.isoformat() if episode.twitter_schedule_datetime else None,
            "instagram_caption": episode.instagram_caption or "",
            "instagram_schedule_datetime": episode.instagram_schedule_datetime.isoformat() if episode.instagram_schedule_datetime else None,
            "facebook_post_text": episode.facebook_post_text or "",
            "facebook_schedule_datetime": episode.facebook_schedule_datetime.isoformat() if episode.facebook_schedule_datetime else None,
            "tiktok_caption": episode.tiktok_caption or "",
            "tiktok_schedule_datetime": episode.tiktok_schedule_datetime.isoformat() if episode.tiktok_schedule_datetime else None,
        }

        logger.info(f"Retrieved episode info from database for episode {episode_number}")
        return {"info": info}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode number format")
    except Exception as e:
        logger.error(f"Error reading episode info from database: {e}")
        raise HTTPException(status_code=500, detail="Error reading episode info from database")


@router.put("/{episode_number}/script")
async def update_episode_script(
    episode_number: str,
    segment_file: str = Body(..., description="Rundown file name (e.g., '10 Opening.md')"),
    script_content: str = Body(..., description="New script content for the segment"),
    asset_id: Optional[str] = Body(None, description="Asset ID of the segment (preferred lookup)"),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    LEGACY: Update the script content for a specific segment.
    Prefer PUT /api/episodes/{ep}/save-rundown from rundown_router instead.

    Updates database first, then optionally writes to filesystem if it exists.
    """
    from models_v2 import RundownItem

    # Try database update first (authoritative)
    db_updated = False
    if asset_id:
        item = db.query(RundownItem).filter(RundownItem.asset_id == asset_id).first()
        if item:
            item.script_content = script_content
            item.updated_at = datetime.now()
            db.commit()
            db_updated = True
            logger.info(f"Updated script_content in DB for asset_id {asset_id}")

    # Also try to update filesystem if it exists (backward compat)
    try:
        episode_dir = EPISODES_ROOT / episode_number
        rundown_file = episode_dir / "rundown" / segment_file
        if rundown_file.exists():
            with open(rundown_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2]

                    if "## Script" in body:
                        script_start = body.find("## Script")
                        before_script = body[:script_start]
                        remaining = body[script_start:]
                        next_section = remaining.find("\n## ", 1)
                        after_script = remaining[next_section:] if next_section > 0 else ""
                        new_body = f"{before_script}## Script\n\n{script_content}\n{after_script}"
                    else:
                        new_body = f"{body}\n\n## Script\n\n{script_content}"

                    new_content = f"---{frontmatter}---{new_body}"
                    with open(rundown_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
    except Exception as fs_err:
        logger.warning(f"Filesystem write skipped for {segment_file}: {fs_err}")

    if not db_updated:
        logger.warning(f"update_episode_script: no DB record found for asset_id={asset_id}, segment_file={segment_file}")

    return {
        "success": True,
        "message": f"Script updated for segment {segment_file}",
        "episode_number": episode_number,
        "segment_file": segment_file,
        "db_updated": db_updated
    }


@router.put("/{episode_number}/info")
async def update_episode_info(episode_number: str, info_data: dict, current_user: dict = Depends(get_current_user_or_key)):
    """Update episode information in both info.md file and database"""
    from sqlalchemy.orm import Session
    from database import get_db
    from models_v2 import Episode
    from fastapi import Depends

    # Get database session
    db_gen = get_db()
    db = next(db_gen)

    try:
        info_path = EPISODES_ROOT / episode_number / "info.md"

        # Update info.md if the directory exists (optional — DB is authoritative)
        if info_path.parent.exists():
            existing_body = ""
            if info_path.exists():
                with open(info_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        existing_body = parts[2].strip()

            import yaml
            frontmatter_yaml = yaml.dump(info_data, default_flow_style=False, allow_unicode=True)
            new_content = f"---\n{frontmatter_yaml}---\n{existing_body}"

            with open(info_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            logging.info(f"No episode directory for {episode_number}, skipping info.md write")

        # Update database record
        try:
            episode_num = int(episode_number)
            db_episode = db.query(Episode).filter(Episode.episode_number == episode_num).first()

            if db_episode:
                # Update database fields from info_data
                if 'title' in info_data:
                    db_episode.title = info_data['title']
                if 'status' in info_data:
                    db_episode.status = info_data['status']
                if 'airdate' in info_data and info_data['airdate']:
                    from datetime import datetime
                    try:
                        db_episode.air_date = datetime.fromisoformat(info_data['airdate'])
                    except (ValueError, TypeError):
                        logging.warning(f"Could not parse airdate: {info_data['airdate']}")
                if 'duration' in info_data and info_data['duration']:
                    # Convert duration from HH:MM:SS to seconds
                    try:
                        duration_parts = info_data['duration'].split(':')
                        if len(duration_parts) == 3:
                            hours, minutes, seconds = map(int, duration_parts)
                            total_seconds = hours * 3600 + minutes * 60 + seconds
                            db_episode.actual_duration = total_seconds
                    except (ValueError, IndexError):
                        logging.warning(f"Could not parse duration: {info_data['duration']}")

                db.commit()
                logging.info(f"Updated database record for episode {episode_number}")
            else:
                logging.info(f"No database record found for episode {episode_number}")

        except (ValueError, TypeError) as e:
            logging.warning(f"Could not update database for episode {episode_number}: {e}")
        except Exception as db_error:
            logging.error(f"Database update failed for episode {episode_number}: {db_error}")
            db.rollback()
            # Don't fail the entire request if database update fails

        return {
            "message": f"Episode {episode_number} info updated successfully",
            "episode_number": episode_number,
            "info": info_data
        }

    except Exception as e:
        logging.error(f"Failed to update episode info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update episode info: {str(e)}")
    finally:
        db.close()


@router.put("/{episode_number}/save-episode")
async def save_episode_metadata(
    episode_number: str,
    episode_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Database-first episode metadata save - replaces filesystem approach"""
    from models_v2 import Episode

    try:
        # Convert episode number to int
        episode_num_int = int(episode_number)

        # Get episode from database
        episode = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        # Update episode fields
        for field, value in episode_data.items():
            if hasattr(episode, field) and value is not None:
                if field in ['air_date', 'publish_date', 'recording_date',
                             'schedule_datetime', 'omny_schedule_datetime',
                             'yt_schedule_datetime', 'twitter_schedule_datetime',
                             'instagram_schedule_datetime', 'facebook_schedule_datetime',
                             'tiktok_schedule_datetime']:
                    # Handle date/datetime fields - convert empty strings to None
                    if value == '' or value is None:
                        setattr(episode, field, None)
                    else:
                        from datetime import datetime
                        setattr(episode, field, datetime.fromisoformat(value) if isinstance(value, str) else value)
                else:
                    setattr(episode, field, value)

        # Always update the updated_at timestamp
        from datetime import datetime
        episode.updated_at = datetime.now()

        db.commit()
        db.refresh(episode)

        logger.info(f"Episode {episode_number} metadata saved to database")
        return {"status": "success", "message": f"Episode {episode_number} metadata saved"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode number format")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving episode metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save episode metadata: {str(e)}")


@router.get("/{episode_number}/statistics")
async def get_episode_statistics(episode_number: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get statistics for an episode's rundown items."""
    from models_v2 import Episode, Rundown, RundownItem
    from sqlalchemy import func

    try:
        # Convert episode number to int
        episode_num_int = int(episode_number)

        # Get episode from database
        episode = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        # Get rundowns for this episode
        rundowns = db.query(Rundown).filter(Rundown.episode_id == episode.id).all()
        if not rundowns:
            # Return empty statistics if no rundowns exist yet
            return {
                "total_items": 0,
                "by_status": {},
                "by_type": {},
                "progress_percentage": 0
            }

        # Get all rundown items for this episode
        rundown_ids = [r.id for r in rundowns]
        items = db.query(RundownItem).filter(RundownItem.rundown_id.in_(rundown_ids)).all()

        # Calculate statistics
        total_items = len(items)
        by_status = {}
        by_type = {}

        for item in items:
            # Count by status
            status = item.status or 'draft'
            by_status[status] = by_status.get(status, 0) + 1

            # Count by type
            item_type = item.item_type or 'segment'
            by_type[item_type] = by_type.get(item_type, 0) + 1

        # Calculate progress percentage
        # Items that are 'approved' or 'completed' count as done
        completed_count = by_status.get('approved', 0) + by_status.get('completed', 0)
        progress_percentage = round((completed_count / total_items * 100) if total_items > 0 else 0)

        logger.info(f"Retrieved statistics for episode {episode_number}: {total_items} items")
        return {
            "total_items": total_items,
            "by_status": by_status,
            "by_type": by_type,
            "progress_percentage": progress_percentage
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode number format")
    except Exception as e:
        logger.error(f"Error retrieving statistics for episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving episode statistics")
