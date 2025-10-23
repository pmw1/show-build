#!/usr/bin/env python3
"""
Episode Folder Name Normalization Tool
Validates and fixes episode folder names in Google Drive that have been incorrectly renamed.

Usage:
    python normalize_episode_names.py [--dry-run] [--min-episode XXXX] [--max-episode XXXX]

Examples:
    python normalize_episode_names.py --dry-run          # Preview changes without applying
    python normalize_episode_names.py                     # Apply fixes
    python normalize_episode_names.py --min-episode 0200 --max-episode 0300
"""

import re
import sys
import argparse
import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from services.google_drive_service import get_drive_service_from_config
from database import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def extract_episode_number(folder_name: str) -> Optional[str]:
    """
    Extract 4-digit episode number from folder name using regex.

    Patterns recognized:
    - "0244" -> 0244
    - "0244.10.12.25" -> 0244
    - "Episode 0244" -> 0244
    - "EP0244-extra" -> 0244
    - "244" -> 0244 (pad with zeros)

    Args:
        folder_name: Folder name to parse

    Returns:
        4-digit episode number or None if not found
    """
    # Try to find 4-digit number
    match = re.search(r'\b0*(\d{3,4})\b', folder_name)
    if match:
        number = match.group(1)
        # Pad to 4 digits
        return number.zfill(4)

    return None


def is_valid_episode_format(folder_name: str) -> bool:
    """
    Check if folder name is already in correct format (exactly 4 digits).

    Args:
        folder_name: Folder name to check

    Returns:
        True if already correctly formatted
    """
    return bool(re.fullmatch(r'0\d{3}', folder_name))


def is_episode_in_range(episode: str, valid_episodes: List[str], tolerance: int = 50) -> bool:
    """
    Check if episode number is within reasonable range of other valid episodes.

    Args:
        episode: Episode number to validate (e.g., "0244")
        valid_episodes: List of known valid episode numbers
        tolerance: Maximum distance from nearest valid episode

    Returns:
        True if episode is in reasonable range
    """
    if not valid_episodes:
        # No reference episodes, accept anything 0001-9999
        episode_int = int(episode)
        return 1 <= episode_int <= 9999

    episode_int = int(episode)
    valid_ints = [int(ep) for ep in valid_episodes]

    # Check if within tolerance of any valid episode
    min_distance = min(abs(episode_int - valid) for valid in valid_ints)
    return min_distance <= tolerance


def normalize_episode_folders(
    dry_run: bool = True,
    min_episode: Optional[str] = None,
    max_episode: Optional[str] = None
) -> Dict[str, List[Dict]]:
    """
    Normalize episode folder names in Google Drive.

    Args:
        dry_run: If True, preview changes without applying
        min_episode: Minimum episode number to process (e.g., "0200")
        max_episode: Maximum episode number to process (e.g., "0300")

    Returns:
        Dictionary with report:
        - valid: Already correctly named folders
        - renamed: Folders that were renamed (or would be renamed)
        - flagged: Folders that need manual attention
        - errors: Folders that caused errors
    """
    report = {
        'valid': [],
        'renamed': [],
        'flagged': [],
        'errors': []
    }

    try:
        # Get Google Drive service and episodes root folder
        from api_config import APIConfigManager
        config_mgr = APIConfigManager()

        # Get Drive service using config manager
        drive_service = get_drive_service_from_config(config_mgr)

        # Get episodes root folder ID from drive service
        episodes_root_id = drive_service.get_episodes_folder_id()

        if not episodes_root_id:
            logger.error("❌ Episodes root folder ID not configured in Google Drive settings")
            return report

        logger.info(f"📁 Scanning Google Drive episodes folder (ID: {episodes_root_id})")

        # List all folders in episodes directory
        folders = drive_service.list_folders(parent_id=episodes_root_id)
        logger.info(f"📊 Found {len(folders)} folders to process")

        # First pass: identify valid episodes
        valid_episodes = []
        for folder in folders:
            if is_valid_episode_format(folder['name']):
                valid_episodes.append(folder['name'])

        logger.info(f"✅ Found {len(valid_episodes)} correctly formatted episode folders")

        # Second pass: normalize folder names
        for folder in folders:
            folder_name = folder['name']
            folder_id = folder['id']

            try:
                # Check if already valid
                if is_valid_episode_format(folder_name):
                    report['valid'].append({
                        'current_name': folder_name,
                        'reason': 'Already correctly formatted'
                    })
                    continue

                # Extract episode number
                episode_number = extract_episode_number(folder_name)

                if not episode_number:
                    report['flagged'].append({
                        'current_name': folder_name,
                        'reason': 'Could not extract 4-digit episode number',
                        'action_needed': 'Manual review required'
                    })
                    continue

                # Apply min/max filters if specified
                episode_int = int(episode_number)
                if min_episode and episode_int < int(min_episode):
                    logger.debug(f"⏭️  Skipping {folder_name} (below minimum {min_episode})")
                    continue
                if max_episode and episode_int > int(max_episode):
                    logger.debug(f"⏭️  Skipping {folder_name} (above maximum {max_episode})")
                    continue

                # Validate episode is in reasonable range
                if not is_episode_in_range(episode_number, valid_episodes):
                    report['flagged'].append({
                        'current_name': folder_name,
                        'extracted_episode': episode_number,
                        'reason': f'Episode {episode_number} is out of range (valid episodes: {min(valid_episodes)}-{max(valid_episodes)})',
                        'action_needed': 'Verify episode number is correct'
                    })
                    continue

                # Rename folder
                new_name = episode_number

                if dry_run:
                    logger.info(f"🔍 PREVIEW: Would rename '{folder_name}' → '{new_name}'")
                    report['renamed'].append({
                        'current_name': folder_name,
                        'new_name': new_name,
                        'status': 'Preview only (dry-run)'
                    })
                else:
                    logger.info(f"✏️  Renaming '{folder_name}' → '{new_name}'")
                    drive_service.service.files().update(
                        fileId=folder_id,
                        body={'name': new_name}
                    ).execute()
                    report['renamed'].append({
                        'current_name': folder_name,
                        'new_name': new_name,
                        'status': 'Successfully renamed'
                    })

            except Exception as e:
                logger.error(f"❌ Error processing folder '{folder_name}': {e}")
                report['errors'].append({
                    'current_name': folder_name,
                    'error': str(e)
                })

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        report['errors'].append({
            'error': f"Fatal error: {str(e)}"
        })

    return report


def print_report(report: Dict[str, List[Dict]], dry_run: bool):
    """Print formatted hygiene report."""
    print("\n" + "="*80)
    print("📋 EPISODE FOLDER HYGIENE REPORT")
    print("="*80)

    if dry_run:
        print("⚠️  DRY RUN MODE - No changes were applied")
        print()

    # Valid folders
    if report['valid']:
        print(f"\n✅ VALID FOLDERS ({len(report['valid'])})")
        print("-" * 80)
        for item in report['valid'][:10]:  # Show first 10
            print(f"  ✓ {item['current_name']}")
        if len(report['valid']) > 10:
            print(f"  ... and {len(report['valid']) - 10} more")

    # Renamed folders
    if report['renamed']:
        print(f"\n✏️  {'WOULD RENAME' if dry_run else 'RENAMED'} FOLDERS ({len(report['renamed'])})")
        print("-" * 80)
        for item in report['renamed']:
            status = "→" if dry_run else "✓"
            print(f"  {status} {item['current_name']} → {item['new_name']}")

    # Flagged folders
    if report['flagged']:
        print(f"\n⚠️  FLAGGED FOR MANUAL ATTENTION ({len(report['flagged'])})")
        print("-" * 80)
        for item in report['flagged']:
            print(f"  ! {item['current_name']}")
            print(f"    Reason: {item['reason']}")
            print(f"    Action: {item.get('action_needed', 'Manual review required')}")
            if 'extracted_episode' in item:
                print(f"    Extracted: {item['extracted_episode']}")
            print()

    # Errors
    if report['errors']:
        print(f"\n❌ ERRORS ({len(report['errors'])})")
        print("-" * 80)
        for item in report['errors']:
            if 'current_name' in item:
                print(f"  ✗ {item['current_name']}: {item['error']}")
            else:
                print(f"  ✗ {item['error']}")

    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"  Valid:   {len(report['valid'])} folders")
    print(f"  {'Would rename' if dry_run else 'Renamed'}: {len(report['renamed'])} folders")
    print(f"  Flagged: {len(report['flagged'])} folders need manual attention")
    print(f"  Errors:  {len(report['errors'])} folders had errors")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Normalize episode folder names in Google Drive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    parser.add_argument(
        '--min-episode',
        type=str,
        help='Minimum episode number to process (e.g., 0200)'
    )
    parser.add_argument(
        '--max-episode',
        type=str,
        help='Maximum episode number to process (e.g., 0300)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate episode number format if provided
    if args.min_episode and not re.match(r'^\d{4}$', args.min_episode):
        logger.error("❌ --min-episode must be 4 digits (e.g., 0200)")
        sys.exit(1)

    if args.max_episode and not re.match(r'^\d{4}$', args.max_episode):
        logger.error("❌ --max-episode must be 4 digits (e.g., 0300)")
        sys.exit(1)

    # Run normalization
    report = normalize_episode_folders(
        dry_run=args.dry_run,
        min_episode=args.min_episode,
        max_episode=args.max_episode
    )

    # Print report
    print_report(report, args.dry_run)

    # Exit with appropriate code
    if report['errors']:
        sys.exit(1)
    elif report['flagged']:
        sys.exit(2)  # Warnings but no errors
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
