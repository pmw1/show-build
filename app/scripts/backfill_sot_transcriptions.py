#!/usr/bin/env python3
"""
Backfill SOT Transcriptions

This script updates existing SOT cue blocks in rundown items with transcription
and outcue data from SOTProcessingJob records.

Use this for SOTs that were processed before the automatic cue-block update
feature was implemented.

Usage:
    python scripts/backfill_sot_transcriptions.py --episode 0257
    python scripts/backfill_sot_transcriptions.py --episode 0257 --dry-run
    python scripts/backfill_sot_transcriptions.py --all-episodes
"""

import argparse
import re
import sys
from pathlib import Path
from contextlib import contextmanager

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models_v2 import Episode, Rundown, RundownItem, SOTProcessingJob


@contextmanager
def db_session():
    """Database session context manager for safe session handling."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def derive_outcue(transcription: str, word_count: int = 5) -> str:
    """Derive outcue from transcription - last N words with '...' prefix."""
    if not transcription or transcription.startswith('['):
        return ''

    words = transcription.strip().split()
    if len(words) >= word_count:
        return '...' + ' '.join(words[-word_count:])
    elif words:
        return '...' + ' '.join(words)
    return ''


def find_sot_cue_blocks(script_content: str) -> list:
    """
    Find all SOT cue blocks in script content.

    Returns list of tuples: (full_cue_block, asset_id)
    """
    if not script_content:
        return []

    cue_blocks = []
    # Matches expanded + collapsed cues; the whole block (incl. its original
    # Begin marker) is captured and field-edited in place, preserving the marker.
    cue_pattern = re.compile(
        r'(<!-- Begin Cue(?: collapsed)? -->(?:(?!<!-- End Cue -->).)*?\[Type:\s*SOT\](?:(?!<!-- End Cue -->).)*?<!-- End Cue -->)',
        re.DOTALL | re.IGNORECASE
    )

    for match in cue_pattern.finditer(script_content):
        cue_block = match.group(1)

        # Extract Asset ID
        asset_match = re.search(r'\[Asset\s*[Ii][Dd]:\s*([^\]]+)\]', cue_block, re.IGNORECASE)
        if asset_match:
            asset_id = asset_match.group(1).strip()
            cue_blocks.append((cue_block, asset_id))

    return cue_blocks


def has_transcription(cue_block: str) -> bool:
    """Check if cue block already has a valid transcription."""
    trans_match = re.search(r'\[Transcription:\s*([^\]]+)\]', cue_block, re.IGNORECASE)
    if not trans_match:
        return False

    transcription = trans_match.group(1).strip()
    # Consider empty or error transcriptions as not having valid transcription
    if not transcription or transcription.startswith('[') or transcription == '':
        return False

    return True


def update_cue_block_transcription(cue_block: str, transcription: str, outcue: str) -> str:
    """Update cue block with transcription and outcue."""
    updated = cue_block

    # Update or add Transcription field
    trans_pattern = re.compile(r'\[Transcription:\s*[^\]]*\]', re.IGNORECASE)
    if trans_pattern.search(updated):
        updated = trans_pattern.sub(f'[Transcription: {transcription}]', updated)
    else:
        updated = updated.replace(
            '<!-- End Cue -->',
            f'[Transcription: {transcription}]\n<!-- End Cue -->'
        )

    # Update or add Outcue field
    outcue_pattern = re.compile(r'\[Outcue:\s*[^\]]*\]', re.IGNORECASE)
    if outcue_pattern.search(updated):
        updated = outcue_pattern.sub(f'[Outcue: {outcue}]', updated)
    else:
        updated = updated.replace(
            '<!-- End Cue -->',
            f'[Outcue: {outcue}]\n<!-- End Cue -->'
        )

    return updated


def backfill_episode(episode_number: str, dry_run: bool = False) -> dict:
    """
    Backfill transcriptions for all SOT cue blocks in an episode.

    Returns dict with statistics.
    """
    stats = {
        'episode': episode_number,
        'sots_found': 0,
        'sots_updated': 0,
        'sots_skipped_has_transcription': 0,
        'sots_skipped_no_db_transcription': 0,
        'items_modified': 0,
        'errors': []
    }

    with db_session() as db:
        # Find episode and rundown
        episode = db.query(Episode).filter_by(episode_number=episode_number).first()
        if not episode:
            stats['errors'].append(f"Episode {episode_number} not found")
            return stats

        rundown = db.query(Rundown).filter_by(episode_id=episode.id).first()
        if not rundown:
            stats['errors'].append(f"No rundown found for episode {episode_number}")
            return stats

        # Get all rundown items
        items = db.query(RundownItem).filter_by(rundown_id=rundown.id).all()

        # Build transcription cache from SOTProcessingJob records
        jobs = db.query(SOTProcessingJob).all()
        transcription_cache = {}
        for job in jobs:
            if job.asset_id and job.transcription:
                transcription_cache[job.asset_id] = job.transcription
            if job.final_asset_id and job.transcription:
                transcription_cache[job.final_asset_id] = job.transcription

        print(f"\n📦 Found {len(transcription_cache)} transcriptions in database")

        # Process each rundown item
        for item in items:
            if not item.script_content:
                continue

            sot_blocks = find_sot_cue_blocks(item.script_content)
            if not sot_blocks:
                continue

            item_modified = False
            new_content = item.script_content

            for cue_block, asset_id in sot_blocks:
                stats['sots_found'] += 1

                # Check if already has valid transcription
                if has_transcription(cue_block):
                    stats['sots_skipped_has_transcription'] += 1
                    print(f"  ⏭️  SOT {asset_id} already has transcription")
                    continue

                # Look up transcription from database
                transcription = transcription_cache.get(asset_id)
                if not transcription:
                    stats['sots_skipped_no_db_transcription'] += 1
                    print(f"  ❌ SOT {asset_id} has no transcription in database")
                    continue

                # Derive outcue from transcription
                outcue = derive_outcue(transcription)

                # Update cue block
                updated_cue = update_cue_block_transcription(cue_block, transcription, outcue)
                new_content = new_content.replace(cue_block, updated_cue)
                item_modified = True
                stats['sots_updated'] += 1

                print(f"  ✅ SOT {asset_id}: Added transcription ({len(transcription)} chars), outcue: {outcue}")

            # Save changes if modified
            if item_modified:
                if not dry_run:
                    item.script_content = new_content
                    db.commit()
                stats['items_modified'] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description='Backfill SOT transcriptions in rundown cue blocks')
    parser.add_argument('--episode', type=str, help='Episode number to process (e.g., 0257)')
    parser.add_argument('--all-episodes', action='store_true', help='Process all episodes')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')

    args = parser.parse_args()

    if not args.episode and not args.all_episodes:
        parser.error("Either --episode or --all-episodes is required")

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")

    if args.episode:
        episodes = [args.episode]
    else:
        # Get all episodes from database
        with db_session() as db:
            all_eps = db.query(Episode).all()
            episodes = [ep.episode_number for ep in all_eps if ep.episode_number]

    total_stats = {
        'episodes_processed': 0,
        'sots_found': 0,
        'sots_updated': 0,
        'sots_skipped_has_transcription': 0,
        'sots_skipped_no_db_transcription': 0,
        'items_modified': 0,
        'errors': []
    }

    for episode_number in episodes:
        print(f"\n{'='*60}")
        print(f"📺 Processing episode {episode_number}")
        print('='*60)

        stats = backfill_episode(episode_number, dry_run=args.dry_run)

        total_stats['episodes_processed'] += 1
        total_stats['sots_found'] += stats['sots_found']
        total_stats['sots_updated'] += stats['sots_updated']
        total_stats['sots_skipped_has_transcription'] += stats['sots_skipped_has_transcription']
        total_stats['sots_skipped_no_db_transcription'] += stats['sots_skipped_no_db_transcription']
        total_stats['items_modified'] += stats['items_modified']
        total_stats['errors'].extend(stats['errors'])

    # Print summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print('='*60)
    print(f"Episodes processed:              {total_stats['episodes_processed']}")
    print(f"SOT cue blocks found:            {total_stats['sots_found']}")
    print(f"SOTs updated with transcription: {total_stats['sots_updated']}")
    print(f"SOTs skipped (already had):      {total_stats['sots_skipped_has_transcription']}")
    print(f"SOTs skipped (no DB record):     {total_stats['sots_skipped_no_db_transcription']}")
    print(f"Rundown items modified:          {total_stats['items_modified']}")

    if total_stats['errors']:
        print(f"\n⚠️  Errors: {len(total_stats['errors'])}")
        for error in total_stats['errors']:
            print(f"  - {error}")

    if args.dry_run:
        print("\n🔍 This was a DRY RUN - no changes were made")
        print("   Run without --dry-run to apply changes")


if __name__ == '__main__':
    main()
