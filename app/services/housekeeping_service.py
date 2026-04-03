"""
Housekeeping service for detecting and optionally fixing data inconsistencies.
Runs asynchronously in background to monitor database integrity.

IMPORTANT: Housekeeping only runs on items NOT currently being edited.
"""
import logging
from typing import List, Dict, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

EPISODES_ROOT = Path("/home/episodes")

# Track which items are currently being edited (by asset_id)
# Format: {asset_id: last_active_timestamp}
ACTIVE_EDITS: Dict[str, datetime] = {}
EDIT_TIMEOUT_MINUTES = 30  # Consider edit session stale after 30 minutes


class IntegrityIssue:
    """Represents a detected integrity issue"""
    def __init__(self, severity: str, category: str, description: str, details: Dict[str, Any]):
        self.severity = severity  # 'critical', 'warning', 'info'
        self.category = category  # 'duplicate', 'orphan', 'mismatch', 'corruption'
        self.description = description
        self.details = details
        self.detected_at = datetime.now()

    def to_dict(self):
        return {
            'severity': self.severity,
            'category': self.category,
            'description': self.description,
            'details': self.details,
            'detected_at': self.detected_at.isoformat()
        }


class HousekeepingService:
    """Service for detecting data inconsistencies"""

    @staticmethod
    def register_active_edit(asset_id: str):
        """Register that an item is currently being edited"""
        ACTIVE_EDITS[asset_id] = datetime.now()
        logger.debug(f"Registered active edit for asset {asset_id}")

    @staticmethod
    def unregister_active_edit(asset_id: str):
        """Unregister an item from active editing"""
        if asset_id in ACTIVE_EDITS:
            del ACTIVE_EDITS[asset_id]
            logger.debug(f"Unregistered active edit for asset {asset_id}")

    @staticmethod
    def get_actively_edited_assets() -> Set[str]:
        """Get set of asset_ids currently being edited (excluding stale sessions)"""
        cutoff = datetime.now() - timedelta(minutes=EDIT_TIMEOUT_MINUTES)
        active = {
            asset_id for asset_id, timestamp in ACTIVE_EDITS.items()
            if timestamp > cutoff
        }
        # Clean up stale entries
        stale = [aid for aid, ts in ACTIVE_EDITS.items() if ts <= cutoff]
        for stale_id in stale:
            del ACTIVE_EDITS[stale_id]
            logger.info(f"Removed stale edit session for asset {stale_id}")
        return active

    @staticmethod
    def is_asset_being_edited(asset_id: str) -> bool:
        """Check if a specific asset is currently being edited"""
        if asset_id not in ACTIVE_EDITS:
            return False
        cutoff = datetime.now() - timedelta(minutes=EDIT_TIMEOUT_MINUTES)
        return ACTIVE_EDITS[asset_id] > cutoff

    @staticmethod
    def check_duplicate_slugs(db: Session, exclude_active: bool = True) -> List[IntegrityIssue]:
        """Detect duplicate slugs within same episode"""
        from models_v2 import RundownItem, Rundown, Episode

        issues = []
        active_assets = HousekeepingService.get_actively_edited_assets() if exclude_active else set()

        # Find duplicates: same slug, same episode, different asset_id
        duplicates = db.query(
            RundownItem.slug,
            Rundown.episode_id,
            Episode.episode_number,
            func.count(RundownItem.id).label('count')
        ).join(
            Rundown, RundownItem.rundown_id == Rundown.id
        ).join(
            Episode, Rundown.episode_id == Episode.id
        ).group_by(
            RundownItem.slug, Rundown.episode_id, Episode.episode_number
        ).having(
            func.count(RundownItem.id) > 1
        ).all()

        for slug, episode_id, episode_number, count in duplicates:
            # Get details of duplicate items
            items = db.query(RundownItem).join(
                Rundown
            ).filter(
                RundownItem.slug == slug,
                Rundown.episode_id == episode_id
            ).all()

            # Filter out actively edited items
            if exclude_active:
                items = [item for item in items if item.asset_id not in active_assets]
                if len(items) <= 1:
                    continue  # Skip if only one or zero non-active items remain

            issues.append(IntegrityIssue(
                severity='critical',
                category='duplicate',
                description=f'Duplicate slug "{slug}" in episode {episode_number}',
                details={
                    'slug': slug,
                    'episode_number': episode_number,
                    'count': len(items),
                    'asset_ids': [item.asset_id for item in items],
                    'created_dates': [item.created_at.isoformat() if item.created_at else None for item in items],
                    'excluded_active': len(active_assets) if exclude_active else 0
                }
            ))

        return issues

    @staticmethod
    def check_identical_script_content(db: Session) -> List[IntegrityIssue]:
        """Detect multiple items with identical script content (likely corruption)"""
        from models_v2 import RundownItem, Rundown, Episode

        issues = []

        # Find items with same non-empty script_content in same episode
        episodes = db.query(Episode).all()

        for episode in episodes:
            rundowns = db.query(Rundown).filter(Rundown.episode_id == episode.id).all()

            for rundown in rundowns:
                items = db.query(RundownItem).filter(
                    RundownItem.rundown_id == rundown.id,
                    RundownItem.script_content.isnot(None),
                    RundownItem.script_content != ''
                ).all()

                # Group by script_content
                content_map = {}
                for item in items:
                    content_hash = item.script_content[:100] if item.script_content else ''
                    if content_hash not in content_map:
                        content_map[content_hash] = []
                    content_map[content_hash].append(item)

                # Report duplicates
                for content_hash, duplicate_items in content_map.items():
                    if len(duplicate_items) > 1:
                        issues.append(IntegrityIssue(
                            severity='critical',
                            category='corruption',
                            description=f'Multiple items with identical script content in episode {episode.episode_number}',
                            details={
                                'episode_number': episode.episode_number,
                                'count': len(duplicate_items),
                                'asset_ids': [item.asset_id for item in duplicate_items],
                                'slugs': [item.slug for item in duplicate_items],
                                'content_preview': content_hash
                            }
                        ))

        return issues

    @staticmethod
    def check_orphaned_rundown_items(db: Session) -> List[IntegrityIssue]:
        """Detect rundown items without valid rundown or episode"""
        from models_v2 import RundownItem, Rundown, Episode

        issues = []

        # Items with rundown_id that doesn't exist
        orphaned = db.query(RundownItem).outerjoin(
            Rundown, RundownItem.rundown_id == Rundown.id
        ).filter(Rundown.id.is_(None)).all()

        if orphaned:
            issues.append(IntegrityIssue(
                severity='warning',
                category='orphan',
                description=f'{len(orphaned)} rundown items without valid rundown',
                details={
                    'count': len(orphaned),
                    'asset_ids': [item.asset_id for item in orphaned],
                    'rundown_ids': [item.rundown_id for item in orphaned]
                }
            ))

        return issues

    @staticmethod
    def check_order_conflicts(db: Session) -> List[IntegrityIssue]:
        """Detect multiple items with same order_in_rundown value"""
        from models_v2 import RundownItem, Rundown, Episode

        issues = []

        rundowns = db.query(Rundown).all()

        for rundown in rundowns:
            # Find duplicate order values
            duplicates = db.query(
                RundownItem.order_in_rundown,
                func.count(RundownItem.id).label('count')
            ).filter(
                RundownItem.rundown_id == rundown.id
            ).group_by(
                RundownItem.order_in_rundown
            ).having(
                func.count(RundownItem.id) > 1
            ).all()

            if duplicates:
                episode = db.query(Episode).filter(Episode.id == rundown.episode_id).first()
                for order_value, count in duplicates:
                    items = db.query(RundownItem).filter(
                        RundownItem.rundown_id == rundown.id,
                        RundownItem.order_in_rundown == order_value
                    ).all()

                    issues.append(IntegrityIssue(
                        severity='warning',
                        category='duplicate',
                        description=f'Multiple items with order {order_value} in episode {episode.episode_number if episode else "unknown"}',
                        details={
                            'episode_number': episode.episode_number if episode else None,
                            'rundown_id': rundown.id,
                            'order_value': order_value,
                            'count': count,
                            'asset_ids': [item.asset_id for item in items],
                            'slugs': [item.slug for item in items]
                        }
                    ))

        return issues

    @staticmethod
    def check_missing_asset_ids(db: Session) -> List[IntegrityIssue]:
        """Detect rundown items without asset_id"""
        from models_v2 import RundownItem, Rundown, Episode

        issues = []

        missing = db.query(RundownItem).filter(
            (RundownItem.asset_id.is_(None)) | (RundownItem.asset_id == '')
        ).all()

        if missing:
            # Group by episode
            episode_groups = {}
            for item in missing:
                rundown = db.query(Rundown).filter(Rundown.id == item.rundown_id).first()
                if rundown:
                    episode = db.query(Episode).filter(Episode.id == rundown.episode_id).first()
                    ep_num = episode.episode_number if episode else 'unknown'
                    if ep_num not in episode_groups:
                        episode_groups[ep_num] = []
                    episode_groups[ep_num].append(item)

            for ep_num, items in episode_groups.items():
                issues.append(IntegrityIssue(
                    severity='critical',
                    category='corruption',
                    description=f'{len(items)} rundown items without asset_id in episode {ep_num}',
                    details={
                        'episode_number': ep_num,
                        'count': len(items),
                        'item_ids': [item.id for item in items],
                        'slugs': [item.slug for item in items]
                    }
                ))

        return issues

    @staticmethod
    async def run_all_checks(db: Session) -> Dict[str, Any]:
        """Run all integrity checks and return report"""
        logger.info("🔍 Starting housekeeping integrity checks...")

        all_issues = []

        # Run all checks
        all_issues.extend(HousekeepingService.check_duplicate_slugs(db))
        all_issues.extend(HousekeepingService.check_identical_script_content(db))
        all_issues.extend(HousekeepingService.check_orphaned_rundown_items(db))
        all_issues.extend(HousekeepingService.check_order_conflicts(db))
        all_issues.extend(HousekeepingService.check_missing_asset_ids(db))

        # Categorize by severity
        critical = [i for i in all_issues if i.severity == 'critical']
        warnings = [i for i in all_issues if i.severity == 'warning']
        info = [i for i in all_issues if i.severity == 'info']

        report = {
            'timestamp': datetime.now().isoformat(),
            'total_issues': len(all_issues),
            'critical_count': len(critical),
            'warning_count': len(warnings),
            'info_count': len(info),
            'issues': [issue.to_dict() for issue in all_issues]
        }

        if critical:
            logger.error(f"🚨 Found {len(critical)} CRITICAL integrity issues!")
        if warnings:
            logger.warning(f"⚠️ Found {len(warnings)} WARNING integrity issues")
        if not all_issues:
            logger.info("✅ No integrity issues detected")

        return report
