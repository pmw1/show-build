#!/usr/bin/env python3
"""
Delete episode 0241 from database completely while preserving filesystem
"""
import sys
sys.path.append('/mnt/process/show-build/app')

from database import SessionLocal
from models_v2 import Episode, Rundown, RundownItem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_episode_0241():
    """Delete episode 0241 and all related data from database"""
    db = SessionLocal()

    try:
        # Find episode 0241
        episode = db.query(Episode).filter(Episode.episode_number == 241).first()

        if not episode:
            logger.info("Episode 0241 not found in database")
            return

        logger.info(f"Found episode 0241: {episode.title} (ID: {episode.id})")

        # Get all rundowns for this episode
        rundowns = db.query(Rundown).filter(Rundown.episode_id == episode.id).all()
        logger.info(f"Found {len(rundowns)} rundowns for episode 0241")

        # Delete all rundown items first
        total_items_deleted = 0
        for rundown in rundowns:
            items = db.query(RundownItem).filter(RundownItem.rundown_id == rundown.id).all()
            logger.info(f"Deleting {len(items)} rundown items from rundown: {rundown.name}")

            for item in items:
                logger.info(f"  - Deleting item: {item.title} (AssetID: {item.asset_id})")
                db.delete(item)
                total_items_deleted += 1

        # Delete rundowns
        for rundown in rundowns:
            logger.info(f"Deleting rundown: {rundown.name} (AssetID: {rundown.asset_id})")
            db.delete(rundown)

        # Delete the episode
        logger.info(f"Deleting episode: {episode.title} (AssetID: {episode.asset_id})")
        db.delete(episode)

        # Commit all deletions
        db.commit()

        logger.info(f"✅ Successfully deleted episode 0241:")
        logger.info(f"  - Episode: {episode.title}")
        logger.info(f"  - Rundowns: {len(rundowns)}")
        logger.info(f"  - Rundown Items: {total_items_deleted}")

        # Verify deletion
        verify_episode = db.query(Episode).filter(Episode.episode_number == 241).first()
        if verify_episode is None:
            logger.info("✅ Verified: Episode 0241 completely removed from database")
        else:
            logger.error("❌ Error: Episode 0241 still exists in database")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete episode 0241: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    delete_episode_0241()