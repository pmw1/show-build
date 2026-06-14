"""
Cue enumeration router.
Handles cue block enumeration for episodes.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from pathlib import Path
import re
from auth.utils import get_current_user_or_key
from database import get_db
from sqlalchemy.orm import Session
import logging

from ._shared import logger
from services.cue_extractor import (
    CUE_BLOCK_RE,
    CUE_BLOCK_RE_MARKER,
    rebuild_cue,
)

router = APIRouter()


@router.post("/{episode_number}/enumerate-cues")
async def enumerate_cue_blocks(
    episode_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """
    Enumerate all MEDIA-BEARING cue blocks in an episode with sequential numbering.

    Process:
    1. Iterate through all rundown items in chronological order
    2. Find all cue blocks (<!-- Begin Cue --> or <!-- Begin Cue collapsed -->
       ... <!-- End Cue -->); collapsed cues are handled identically and their
       collapsed marker is preserved through enumeration.
    3. Skip non-media cue types (RIF, DIR) - only enumerate media cues
    4. Strip any existing enumeration prefix from slugs
    5. Add new enumeration prefix (10, 20, 30, ...)
    6. Add/update [Enumerator: XX] field for display
    7. Rename associated media files
    8. Update MediaUrl fields
    9. Save changes to database

    Media cue types: IMG, GFX, SOT, FSQ, VO, NAT, PKG, BUMP, STING, VOX, MUS, LIVE
    Non-media cue types (skipped): RIF, DIR

    This is idempotent - running again will re-enumerate cleanly.
    """
    from models_v2 import RundownItem, Rundown, Episode
    import shutil

    # Cue types that have media and should be enumerated
    MEDIA_CUE_TYPES = {'IMG', 'GFX', 'SOT', 'FSQ', 'VO', 'NAT', 'PKG', 'BUMP', 'STING', 'VOX', 'MUS', 'LIVE'}

    try:
        logger.info(f"Starting cue block enumeration for episode {episode_number}")

        # Normalize episode number
        episode_id_normalized = episode_number.zfill(4) if len(episode_number) < 4 else episode_number

        # Get episode
        episode = db.query(Episode).filter(
            Episode.episode_number == int(episode_id_normalized)
        ).first()

        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        # Get rundown
        rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
        if not rundown:
            raise HTTPException(status_code=404, detail=f"Rundown not found for episode {episode_number}")

        # Get all rundown items in order
        rundown_items = db.query(RundownItem).filter(
            RundownItem.rundown_id == rundown.id
        ).order_by(RundownItem.order_in_rundown).all()

        # Episode assets directory - use ShowBuildPaths for correct Docker/host path
        from core.paths import ShowBuildPaths
        path_manager = ShowBuildPaths()
        episodes_root = path_manager.episodes_root
        episode_assets_dir = episodes_root / episode_id_normalized / "assets"

        # Patterns
        slug_pattern = re.compile(r'\[Slug:\s*([^\]]+)\]', re.IGNORECASE)
        mediaurl_pattern = re.compile(r'\[Media\s*Url:\s*([^\]]+)\]', re.IGNORECASE)
        enumerator_pattern = re.compile(r'\[Enumerator:\s*[^\]]*\]\n?', re.IGNORECASE)
        enum_prefix_pattern = re.compile(r'^(\d+)[-_](.+)$')
        type_pattern = re.compile(r'\[Type:\s*([^\]]+)\]', re.IGNORECASE)

        # Track statistics
        total_cues = 0
        de_enumerated = 0
        files_de_enumerated = 0
        skipped_non_media = 0
        updated_cues = 0
        renamed_files = 0

        # ============================================================
        # PHASE 1: DE-ENUMERATE - Remove all existing enumeration
        # ============================================================
        # This cleans up ALL cues (including non-media) to start fresh
        logger.info(f"Phase 1: De-enumerating all cues for episode {episode_number}")

        for item in rundown_items:
            if not item.script_content:
                continue

            content = item.script_content
            modified = False

            # Find all cue blocks in this item (both expanded and collapsed).
            # CUE_BLOCK_RE_MARKER captures the marker suffix in group(1) so a
            # collapsed cue is rebuilt collapsed (never silently expanded);
            # the cue body is group(2).
            cue_block_pattern = CUE_BLOCK_RE_MARKER

            def de_enumerate_cue(match):
                nonlocal de_enumerated, files_de_enumerated, modified
                marker_suffix = match.group(1) or ''
                cue_body = match.group(2)
                original_body = cue_body

                # Remove [Enumerator: XX] field
                cue_body = enumerator_pattern.sub('', cue_body)

                # Strip enumeration prefix from slug
                slug_match = slug_pattern.search(cue_body)
                if slug_match:
                    current_slug = slug_match.group(1).strip()
                    enum_match = enum_prefix_pattern.match(current_slug)
                    if enum_match:
                        base_slug = enum_match.group(2)
                        cue_body = slug_pattern.sub(f'[Slug: {base_slug}]', cue_body)

                        # Also update MediaUrl to remove prefix from filename
                        mediaurl_match = mediaurl_pattern.search(cue_body)
                        if mediaurl_match:
                            old_url = mediaurl_match.group(1).strip()
                            old_path = Path(old_url)
                            old_filename = old_path.name

                            # Check if filename has enum prefix
                            filename_enum_match = enum_prefix_pattern.match(old_filename)
                            if filename_enum_match:
                                base_filename = filename_enum_match.group(2)
                                new_url = str(old_path.parent / base_filename)
                                cue_body = mediaurl_pattern.sub(f'[Mediaurl: {new_url}]', cue_body)

                                # Rename actual file on disk
                                old_file = episodes_root / old_url.lstrip('/').replace('episodes/', '')
                                new_file = old_file.parent / base_filename

                                if old_file.exists() and str(old_file) != str(new_file):
                                    try:
                                        # Don't overwrite if target exists
                                        if not new_file.exists():
                                            shutil.move(str(old_file), str(new_file))
                                            files_de_enumerated += 1
                                            logger.debug(f"De-enumerated file: {old_file.name} -> {new_file.name}")
                                    except Exception as e:
                                        logger.warning(f"Could not de-enumerate file {old_file}: {e}")

                if cue_body != original_body:
                    de_enumerated += 1
                    modified = True

                return rebuild_cue(marker_suffix, cue_body)

            content = cue_block_pattern.sub(de_enumerate_cue, content)

            if modified:
                item.script_content = content
                db.add(item)

        # Commit de-enumeration changes
        db.flush()
        logger.info(f"Phase 1 complete: De-enumerated {de_enumerated} cues, renamed {files_de_enumerated} files")

        # ============================================================
        # PHASE 2: RE-ENUMERATE - Assign fresh numbers to media cues
        # ============================================================
        logger.info(f"Phase 2: Re-enumerating media cues for episode {episode_number}")

        # Re-fetch items to get updated content
        rundown_items = db.query(RundownItem).filter(
            RundownItem.rundown_id == rundown.id
        ).order_by(RundownItem.order_in_rundown).all()

        # Collect all MEDIA cue blocks across all items to enumerate globally
        all_cue_data = []

        for item in rundown_items:
            if not item.script_content:
                continue

            # Find all cue blocks in this item (expanded + collapsed). This is a
            # read-only scan — CUE_BLOCK_RE keeps the cue body in group(1).
            matches = list(CUE_BLOCK_RE.finditer(item.script_content))

            for match in matches:
                total_cues += 1
                cue_body = match.group(1)

                # Extract cue type and check if it's a media cue
                type_match = type_pattern.search(cue_body)
                cue_type = type_match.group(1).strip().upper() if type_match else None

                # Skip non-media cue types (RIF, DIR, etc.)
                if cue_type and cue_type not in MEDIA_CUE_TYPES:
                    skipped_non_media += 1
                    logger.debug(f"Skipping non-media cue type: {cue_type}")
                    continue

                # Extract current slug
                slug_match = slug_pattern.search(cue_body)
                if not slug_match:
                    continue

                all_cue_data.append({
                    'item': item,
                    'match_start': match.start(),
                    'match_end': match.end(),
                    'cue_body': cue_body,
                    'current_slug': slug_match.group(1).strip(),
                    'cue_type': cue_type
                })

        # Second pass: enumerate and update
        enumeration_counter = 10

        # Group by item for batch updates
        items_to_update = {}

        for cue_info in all_cue_data:
            item = cue_info['item']
            cue_body = cue_info['cue_body']
            current_slug = cue_info['current_slug']

            # Strip existing enumeration prefix
            base_slug = current_slug
            enum_match = enum_prefix_pattern.match(current_slug)
            if enum_match:
                base_slug = enum_match.group(2)

            # Normalize slug: lowercase, replace spaces with hyphens
            normalized_slug = base_slug.lower().replace(' ', '-').replace('_', '-')
            normalized_slug = re.sub(r'-+', '-', normalized_slug)
            normalized_slug = re.sub(r'[^\w-]', '', normalized_slug)

            # Create new enumerated slug
            new_slug = f"{enumeration_counter:02d}-{normalized_slug}"
            enumerator_value = f"{enumeration_counter:02d}"

            # Extract current mediaurl - use last match if multiple exist
            # (previous enumerations may have left duplicate fields)
            mediaurl_matches = mediaurl_pattern.findall(cue_body)
            old_mediaurl = mediaurl_matches[-1].strip() if mediaurl_matches else None

            # Extract cue type to determine correct asset directory
            type_match = re.search(r'\[Type:\s*([^\]]+)\]', cue_body, re.IGNORECASE)
            cue_type = type_match.group(1).strip().upper() if type_match else None

            # Determine new mediaurl and rename file
            new_mediaurl = None

            # Determine asset type directory based on CUE TYPE first, then path
            if cue_type == 'SOT':
                asset_type = "video"
            elif cue_type == 'IMG':
                asset_type = "images"
            elif cue_type == 'FSQ':
                asset_type = "quotes"
            elif cue_type == 'AUDIO':
                asset_type = "audio"
            elif old_mediaurl and "/video/" in old_mediaurl:
                asset_type = "video"
            elif old_mediaurl and "/images/" in old_mediaurl:
                asset_type = "images"
            elif old_mediaurl and "/audio/" in old_mediaurl:
                asset_type = "audio"
            elif old_mediaurl and "/sot/" in old_mediaurl:
                asset_type = "video"
            else:
                asset_type = "quotes"  # fallback

            if old_mediaurl:
                old_filename = Path(old_mediaurl).name
                ext = Path(old_filename).suffix

                # SOT files are mp4, ensure correct extension
                if cue_type == 'SOT' and (not ext or ext.lower() not in ['.mp4', '.mov', '.mp3']):
                    ext = '.mp4'

                new_filename = f"{new_slug}{ext}"
                new_mediaurl = f"/episodes/{episode_id_normalized}/assets/{asset_type}/{new_filename}"

                # Try to rename the actual file
                old_file_path = episodes_root / old_mediaurl.lstrip('/').replace('episodes/', '')
                new_file_path = episode_assets_dir / asset_type / new_filename

                if old_file_path.exists() and str(old_file_path) != str(new_file_path):
                    try:
                        new_file_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(old_file_path), str(new_file_path))
                        renamed_files += 1
                        logger.info(f"Renamed: {old_file_path.name} -> {new_file_path.name}")
                    except Exception as e:
                        logger.warning(f"Could not rename file {old_file_path}: {e}")

            elif cue_type == 'FSQ':
                # FSQ cues with no MediaUrl - try to find file by slug with fsq_ prefix
                clean_slug_for_search = normalized_slug
                ext = '.png'
                asset_dir = episode_assets_dir / asset_type

                # Try fsq_{slug}.png first
                fsq_path = asset_dir / f"fsq_{clean_slug_for_search}{ext}"
                if fsq_path.exists():
                    new_filename = f"{new_slug}{ext}"
                    new_file_path = asset_dir / new_filename
                    new_mediaurl = f"/episodes/{episode_id_normalized}/assets/{asset_type}/{new_filename}"
                    if str(fsq_path) != str(new_file_path):
                        try:
                            shutil.move(str(fsq_path), str(new_file_path))
                            renamed_files += 1
                            logger.info(f"Renamed FSQ (no mediaurl): {fsq_path.name} -> {new_file_path.name}")
                        except Exception as e:
                            logger.warning(f"Could not rename FSQ file {fsq_path}: {e}")
                else:
                    # Try {slug}.png (already enumerated name)
                    existing_path = asset_dir / f"{new_slug}{ext}"
                    if existing_path.exists():
                        new_mediaurl = f"/episodes/{episode_id_normalized}/assets/{asset_type}/{new_slug}{ext}"
                        logger.info(f"FSQ file already at target: {existing_path.name}")

            # Store update info for this item
            if item.id not in items_to_update:
                items_to_update[item.id] = {
                    'item': item,
                    'replacements': []
                }

            items_to_update[item.id]['replacements'].append({
                'old_slug': current_slug,
                'new_slug': new_slug,
                'enumerator': enumerator_value,
                'old_mediaurl': old_mediaurl,
                'new_mediaurl': new_mediaurl
            })

            updated_cues += 1
            enumeration_counter += 10

        # Third pass: apply all replacements to each item's content
        for item_id, update_info in items_to_update.items():
            item = update_info['item']
            content = item.script_content

            for repl in update_info['replacements']:
                # Find and update each cue block
                def update_cue_block(match):
                    cue_body = match.group(0)

                    # Check if this is the cue block we're looking for
                    slug_m = slug_pattern.search(cue_body)
                    if not slug_m or slug_m.group(1).strip() != repl['old_slug']:
                        return cue_body

                    # Remove existing Enumerator field if present
                    updated_body = enumerator_pattern.sub('', cue_body)

                    # Update slug
                    updated_body = slug_pattern.sub(f"[Slug: {repl['new_slug']}]", updated_body)

                    # Update mediaurl if applicable - remove ALL old MediaUrl fields, add single clean one
                    if repl['new_mediaurl']:
                        # Remove all existing MediaUrl/Media Url/Mediaurl fields
                        updated_body = mediaurl_pattern.sub('', updated_body)
                        # Clean up any resulting blank lines from removal
                        updated_body = re.sub(r'\n{3,}', '\n\n', updated_body)
                        # Add single clean Mediaurl field before <!-- End Cue -->
                        updated_body = updated_body.rstrip()
                        if updated_body.endswith('<!-- End Cue -->'):
                            updated_body = updated_body[:-len('<!-- End Cue -->')].rstrip()
                            updated_body += f"\n[Mediaurl: {repl['new_mediaurl']}]\n<!-- End Cue -->"
                        else:
                            updated_body += f"\n[Mediaurl: {repl['new_mediaurl']}]"

                    # Add Enumerator field after [Type: XXX] line
                    type_pattern = re.compile(r'(\[Type:\s*[^\]]+\]\n)', re.IGNORECASE)
                    type_match = type_pattern.search(updated_body)
                    if type_match:
                        insert_pos = type_match.end()
                        updated_body = (
                            updated_body[:insert_pos] +
                            f"[Enumerator: {repl['enumerator']}]\n" +
                            updated_body[insert_pos:]
                        )

                    return updated_body

                # Apply update - process ALL cue blocks (expanded + collapsed).
                # update_cue_block operates on match.group(0) (the whole block)
                # and only edits fields + the End marker, so the Begin marker
                # (collapsed or not) passes through verbatim and is preserved.
                content = CUE_BLOCK_RE.sub(update_cue_block, content)
                # Update old_slug for subsequent iterations within same item
                repl['old_slug'] = repl['new_slug']

            item.script_content = content
            db.add(item)

        # Commit all changes
        db.commit()

        logger.info(f"Cue enumeration completed: Phase 1 de-enumerated {de_enumerated} cues/{files_de_enumerated} files, Phase 2 enumerated {updated_cues}/{total_cues} media cues, {skipped_non_media} non-media skipped, {renamed_files} files renamed")

        return {
            "success": True,
            "phase1_de_enumerated": de_enumerated,
            "phase1_files_renamed": files_de_enumerated,
            "total": total_cues,
            "enumerated": updated_cues,
            "skipped_non_media": skipped_non_media,
            "files_renamed": renamed_files,
            "message": f"Phase 1: De-enumerated {de_enumerated} cues, {files_de_enumerated} files. Phase 2: Enumerated {updated_cues} media cues, skipped {skipped_non_media} non-media (RIF, DIR), renamed {renamed_files} files."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enumerate cue blocks for episode {episode_number}: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to enumerate cue blocks: {str(e)}")
