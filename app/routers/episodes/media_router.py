"""
Media gathering and graphics packages router.
Handles media gathering for show and graphics package creation/download.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from pathlib import Path
import re
import logging
from auth.utils import get_current_user_or_key
from database import get_db
from sqlalchemy.orm import Session

from ._shared import logger
from services.cue_extractor import CUE_BLOCK_RE

router = APIRouter()


@router.post("/{episode_number}/gather-media")
async def gather_media_for_show(
    episode_number: str,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Gather media files from ENUMERATED cue blocks and copy them to assets/rundown directory.

    Creates: {episode}/assets/rundown/
    Copies each ENUMERATED cue's MediaURL source file with enumerated filename.

    IMPORTANT: Only cues with [Enumerator: XX] field are gathered.
    Non-media cues (RIF, DIR) are never enumerated, so they are automatically skipped.
    Run enumerate-cues endpoint first to enumerate media cues.

    Returns:
        Summary of gathered files with counts including skipped non-enumerated cues
    """
    import shutil
    from models_v2 import RundownItem, Rundown, Episode
    from core.paths import ShowBuildPaths

    path_manager = ShowBuildPaths()

    try:
        print(f"Starting media gather for episode {episode_number}")

        # Normalize episode number
        episode_id = episode_number.zfill(4) if len(episode_number) < 4 else episode_number

        # Get episode
        episode = db.query(Episode).filter(
            Episode.episode_number == int(episode_id)
        ).first()

        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")

        # Get rundown
        rundown = db.query(Rundown).filter(
            Rundown.episode_id == episode.id
        ).first()

        if not rundown:
            raise HTTPException(status_code=404, detail=f"No rundown found for episode {episode_id}")

        # Create assets/rundown directory (clear existing contents first)
        episode_path = path_manager.episodes_root / episode_id
        media_list_dir = episode_path / "assets" / "rundown"
        if media_list_dir.exists():
            import shutil as _shutil
            _shutil.rmtree(media_list_dir)
            print(f"   Cleared existing assets/rundown directory")
        media_list_dir.mkdir(parents=True, exist_ok=True)
        print(f"   Rundown media directory: {media_list_dir}")

        # Get all rundown items with script content
        items = db.query(RundownItem).filter(
            RundownItem.rundown_id == rundown.id
        ).order_by(RundownItem.order_in_rundown).all()

        # Cue block patterns — CUE_BLOCK_RE matches expanded + collapsed cues.
        cue_pattern = CUE_BLOCK_RE
        # Match both "MediaUrl" and "Media Url" (with optional space before colon)
        mediaurl_pattern = re.compile(r'\[Media\s*Url:\s*([^\]]+)\]', re.IGNORECASE)
        enumerator_pattern = re.compile(r'\[Enumerator:\s*([^\]]+)\]', re.IGNORECASE)
        slug_pattern = re.compile(r'\[Slug:\s*([^\]]+)\]', re.IGNORECASE)
        type_pattern = re.compile(r'\[Type:\s*([^\]]+)\]', re.IGNORECASE)

        copied = 0
        skipped = 0
        skipped_not_enumerated = 0
        failed = 0
        total = 0
        gathered_files = []
        failures = []
        skipped_cues = []

        # Process each rundown item
        for item in items:
            if not item.script_content:
                continue

            # Find all cue blocks
            cue_matches = cue_pattern.findall(item.script_content)

            for cue_content in cue_matches:
                total += 1

                # Extract cue type, slug, and enumerator
                type_match_local = type_pattern.search(cue_content)
                slug_match_local = slug_pattern.search(cue_content)
                enumerator_match_local = enumerator_pattern.search(cue_content)

                cue_type_local = type_match_local.group(1).strip().upper() if type_match_local else 'UNKNOWN'
                slug_local = slug_match_local.group(1).strip() if slug_match_local else None
                enumerator_local = enumerator_match_local.group(1).strip() if enumerator_match_local else None

                # Only gather media for ENUMERATED cues (those with [Enumerator: XX] field)
                # Non-media cues (RIF, DIR) are not enumerated and should be skipped
                # EXCEPTION: FSQ cues - always gather since their PNGs exist in quotes/ dir
                if not enumerator_local and cue_type_local not in ('FSQ', 'GFX'):
                    skipped_not_enumerated += 1
                    print(f"   Skipping non-enumerated cue: {cue_type_local} '{slug_local}' (run enumerate-cues first for media cues)")
                    continue

                # Extract MediaURL - use LAST match if multiple exist
                # (enumeration adds [Mediaurl: ...] with updated path, but original [Media Url: ...] remains)
                mediaurl_matches = mediaurl_pattern.findall(cue_content)
                media_url = mediaurl_matches[-1].strip() if mediaurl_matches else None

                # GFX cues store path in [Asset Url: ...] instead of [Media Url: ...]
                # But don't trust stale Asset Url — let the slug-based fallback find the correct file
                if not media_url and cue_type_local == 'GFX':
                    pass  # Fall through to slug-based file search below

                # Check if MediaURL is a blob URL (unprocessed) - treat as no URL
                is_blob_url = media_url and media_url.startswith('blob:')
                if is_blob_url:
                    print(f"   Blob URL detected for {cue_type_local} '{slug_local}', trying fallback...")
                    media_url = None  # Clear so fallback kicks in

                # For cues without MediaURL (or with blob URLs), try to construct path from slug
                if not media_url and slug_local:
                    # Normalize slug for filename
                    clean_slug = slug_local.lower().replace(' ', '-').replace('_', '-')
                    clean_slug = re.sub(r'[^\w\-]', '', clean_slug)
                    # Strip existing enum prefix from slug if present (e.g., "40-im-a-narcissist" -> "im-a-narcissist")
                    enum_prefix_match = re.match(r'^(\d+)[-_](.+)$', clean_slug)
                    if enum_prefix_match:
                        clean_slug = enum_prefix_match.group(2)

                    # Determine asset folder and extension based on cue type
                    if cue_type_local == 'FSQ':
                        asset_folder = 'quotes'
                        extensions = ['.png']
                        if enumerator_local:
                            filename_base = f"{enumerator_local}-{clean_slug}"
                        else:
                            filename_base = f"fsq_{clean_slug}"
                    elif cue_type_local == 'GFX':
                        # X-post GFX renders live in assets/gfx/xpost/.
                        gfxtype_m = re.search(r'\[GfxType:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
                        if gfxtype_m and gfxtype_m.group(1).strip().lower() == 'xpost':
                            asset_folder = 'gfx/xpost'
                        else:
                            asset_folder = 'graphics'
                        extensions = ['.png']
                        if enumerator_local:
                            filename_base = f"{enumerator_local}-{clean_slug}"
                        else:
                            filename_base = f"gfx_{clean_slug}"
                    elif cue_type_local == 'IMG':
                        asset_folder = 'images'
                        extensions = ['.png', '.jpg', '.jpeg', '.webp']
                        filename_base = clean_slug
                    elif cue_type_local in ['SOT', 'VO', 'PKG']:
                        asset_folder = 'video'
                        extensions = ['.mp4', '.mov', '.webm']
                        filename_base = clean_slug
                    else:
                        asset_folder = None
                        extensions = []
                        filename_base = clean_slug

                    # Try to find the file
                    if asset_folder:
                        for ext in extensions:
                            test_path = episode_path / "assets" / asset_folder / f"{filename_base}{ext}"
                            if test_path.exists():
                                media_url = f"episodes/{episode_id}/assets/{asset_folder}/{filename_base}{ext}"
                                print(f"   {cue_type_local} path constructed from slug: {media_url}")
                                break

                        # FSQ fallback: try fsq_ prefix, then glob for *-{slug}.png (enumerated files)
                        if not media_url and cue_type_local == 'FSQ':
                            for ext in extensions:
                                fsq_path = episode_path / "assets" / asset_folder / f"fsq_{clean_slug}{ext}"
                                if fsq_path.exists():
                                    media_url = f"episodes/{episode_id}/assets/{asset_folder}/fsq_{clean_slug}{ext}"
                                    print(f"   FSQ fallback found with fsq_ prefix: {media_url}")
                                    break

                        # FSQ/GFX fallback: search for files ending with -{slug}.ext (e.g., 30-although-gay-activists.png)
                        if not media_url and cue_type_local in ('FSQ', 'GFX'):
                            search_dir = episode_path / "assets" / asset_folder
                            if search_dir.exists():
                                for ext in extensions:
                                    matches = sorted(search_dir.glob(f"*-{clean_slug}{ext}"))
                                    if matches:
                                        matched_file = matches[0]
                                        media_url = f"episodes/{episode_id}/assets/{asset_folder}/{matched_file.name}"
                                        print(f"   {cue_type_local} glob match found: {matched_file.name}")
                                        break

                        # GFX fallback: try gfx_ prefix (legacy naming)
                        if not media_url and cue_type_local == 'GFX':
                            for ext in extensions:
                                gfx_path = episode_path / "assets" / asset_folder / f"gfx_{clean_slug}{ext}"
                                if gfx_path.exists():
                                    media_url = f"episodes/{episode_id}/assets/{asset_folder}/gfx_{clean_slug}{ext}"
                                    print(f"   GFX fallback found with gfx_ prefix: {media_url}")
                                    break

                # Skip if still no media URL
                if not media_url:
                    skipped += 1
                    skipped_cues.append({
                        'type': cue_type_local,
                        'slug': slug_local
                    })
                    continue

                # Use already extracted values
                enumerator = enumerator_local
                slug = slug_local if slug_local else 'media'
                cue_type = cue_type_local

                # Convert MediaURL to actual file path
                # MediaURL formats:
                #   - /episodes/XXXX/assets/... (absolute URL path with leading /)
                #   - episodes/XXXX/assets/... (relative to episodes root, no leading /)
                #   - assets/... (relative to episode directory)
                #   - http://... (external URL - skip)
                #   - blob:... (browser blob URL - skip, indicates unprocessed media)
                if media_url.startswith('http') or media_url.startswith('blob:'):
                    # Skip external URLs and blob URLs (unprocessed media)
                    reason = "blob URL (unprocessed)" if media_url.startswith('blob:') else "external URL"
                    print(f"   Skipping {reason}: {media_url[:60]}...")
                    skipped += 1
                    skipped_cues.append({
                        'type': cue_type,
                        'slug': slug,
                        'reason': reason,
                        'mediaUrl': media_url[:100]
                    })
                    continue
                elif media_url.startswith('/episodes/') or media_url.startswith('episodes/'):
                    # Path relative to episodes root
                    relative_path = media_url.lstrip('/').replace('episodes/', '', 1)
                    source_path = path_manager.episodes_root / relative_path
                else:
                    # Try as relative to episode directory
                    source_path = episode_path / media_url.lstrip('/')

                if not source_path.exists():
                    # Try fallback: look for file without enumeration prefix
                    # e.g., if looking for "20-bomb-mausoleum.mp4", try "bomb-mausoleum.mp4"
                    fallback_found = False
                    original_source = source_path

                    # Extract base slug without enumeration prefix
                    filename = source_path.name
                    enum_prefix_match = re.match(r'^(\d+)[-_](.+)$', filename)
                    if enum_prefix_match:
                        base_filename = enum_prefix_match.group(2)
                        fallback_path = source_path.parent / base_filename
                        if fallback_path.exists():
                            source_path = fallback_path
                            fallback_found = True
                            print(f"   Fallback found: {fallback_path.name}")

                    # Try double-prefix pattern (e.g., 110-110-slug.png when looking for 110-slug.png)
                    if not fallback_found and enum_prefix_match:
                        enum_num = enum_prefix_match.group(1)
                        double_prefix = source_path.parent / f"{enum_num}-{filename}"
                        if double_prefix.exists():
                            source_path = double_prefix
                            fallback_found = True
                            print(f"   Double-prefix fallback found: {double_prefix.name}")

                    # Also try with fsq_ prefix for quotes
                    if not fallback_found and cue_type == 'FSQ':
                        # Extract slug without enumeration prefix or fsq_ prefix
                        slug_part = re.sub(r'^\d+[-_]', '', filename)  # Strip enum prefix
                        slug_part = re.sub(r'^fsq_', '', slug_part)    # Strip existing fsq_ prefix
                        slug_part = re.sub(r'\.png$', '', slug_part, flags=re.IGNORECASE)
                        fsq_fallback = source_path.parent / f"fsq_{slug_part}.png"
                        if fsq_fallback.exists():
                            source_path = fsq_fallback
                            fallback_found = True
                            print(f"   FSQ fallback found: {fsq_fallback.name}")

                    # Glob fallback: search directory for any file ending with the base slug
                    if not fallback_found and enum_prefix_match:
                        base_slug = enum_prefix_match.group(2)  # e.g., "united-airlines-is.png"
                        parent_dir = source_path.parent
                        if parent_dir.exists():
                            matches = sorted(parent_dir.glob(f"*-{base_slug}"))
                            if matches:
                                source_path = matches[0]
                                fallback_found = True
                                print(f"   Glob fallback found: {matches[0].name}")

                    if not fallback_found:
                        hint = 'Run "Regenerate All FSQ & GFX" to generate missing PNGs' if cue_type in ('FSQ', 'GFX') else 'File may not have been imported or processed'
                        print(f"   Source not found: {original_source} - {hint}")
                        failed += 1
                        failures.append({
                            'type': cue_type,
                            'slug': slug,
                            'mediaUrl': media_url,
                            'expectedPath': str(original_source),
                            'hint': hint
                        })
                        continue

                # Build destination filename
                # Format: {enumerator}-{type}-{slug}.{ext}
                ext = source_path.suffix
                clean_slug = re.sub(r'[^\w\-]', '', slug.lower().replace(' ', '-'))

                # Strip leading enumerator from slug if it's already there
                # e.g. slug "100-pauls-legal-drama" with enumerator "100"
                # should become "pauls-legal-drama" not "100-pauls-legal-drama"
                if enumerator and clean_slug.startswith(f"{enumerator}-"):
                    clean_slug = clean_slug[len(f"{enumerator}-"):]

                if enumerator:
                    dest_filename = f"{enumerator}-{cue_type}-{clean_slug}{ext}"
                else:
                    dest_filename = f"{cue_type}-{clean_slug}{ext}"

                dest_path = media_list_dir / dest_filename

                # Copy file to media-list directory
                try:
                    # Remove existing file if present
                    if dest_path.exists() or dest_path.is_symlink():
                        dest_path.unlink()

                    # Copy file (preserves metadata)
                    shutil.copy2(source_path, dest_path)

                    gathered_files.append({
                        'source': str(source_path),
                        'dest': dest_filename,
                        'type': cue_type,
                        'enumerator': enumerator
                    })
                    copied += 1
                    print(f"   Copied: {dest_filename}")

                    # X-post (and any future) GFX renders ship a transparent
                    # "_key" sibling for vMix alpha keying — carry it along.
                    key_source = source_path.with_name(f"{source_path.stem}_key{source_path.suffix}")
                    if cue_type == 'GFX' and key_source.exists():
                        key_dest = dest_path.with_name(f"{dest_path.stem}_key{dest_path.suffix}")
                        if key_dest.exists() or key_dest.is_symlink():
                            key_dest.unlink()
                        shutil.copy2(key_source, key_dest)
                        gathered_files.append({
                            'source': str(key_source),
                            'dest': key_dest.name,
                            'type': cue_type,
                            'enumerator': enumerator
                        })
                        print(f"   Copied key variant: {key_dest.name}")

                except Exception as e:
                    print(f"   Failed to copy {dest_filename}: {e}")
                    failed += 1

        # Count blob URLs in skipped cues for better messaging
        blob_count = sum(1 for s in skipped_cues if s.get('reason') == 'blob URL (unprocessed)')
        no_url_count = skipped - blob_count

        # Build detailed message
        parts = [f"{copied} copied"]
        if skipped_not_enumerated > 0:
            parts.append(f"{skipped_not_enumerated} non-enumerated (RIF/DIR)")
        if skipped > 0:
            if blob_count > 0:
                parts.append(f"{skipped} skipped ({blob_count} blob URLs, {no_url_count} no MediaURL)")
            else:
                parts.append(f"{skipped} skipped (no MediaURL)")
        if failed > 0:
            parts.append(f"{failed} failed")

        message = f"Media gather: {', '.join(parts)}"
        if copied == 0 and blob_count > 0:
            message += " - SOT/VO videos need to be processed first (Submit in modal to trigger processing)"
        print(f"   {message}")

        return {
            "success": True,
            "episode_id": episode_id,
            "media_list_path": str(media_list_dir),
            "total": total,
            "copied": copied,
            "skipped": skipped,
            "skipped_not_enumerated": skipped_not_enumerated,
            "failed": failed,
            "blobUrlCount": blob_count,
            "files": gathered_files,
            "failures": failures,
            "skippedCues": skipped_cues,
            "message": message
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error gathering media for episode {episode_number}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{episode_number}/graphics-package")
async def create_graphics_package(
    episode_number: str,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Create a ZIP archive of the rundown/media-list directory for download.

    The zip file is cached on disk. If any file in media-list is newer than
    the existing zip, the zip is regenerated automatically.

    Returns:
        JSON summary of the package contents and a download URL.
    """
    import zipfile
    from models_v2 import Episode
    from core.paths import ShowBuildPaths

    path_manager = ShowBuildPaths()

    try:
        episode_id = episode_number.zfill(4) if len(episode_number) < 4 else episode_number

        episode = db.query(Episode).filter(
            Episode.episode_number == int(episode_id)
        ).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")

        episode_dir = path_manager.get_episode_dir(episode_id)
        media_list_dir = Path(episode_dir) / "assets" / "rundown"

        if not media_list_dir.exists() or not any(media_list_dir.iterdir()):
            raise HTTPException(
                status_code=404,
                detail="No assets/rundown directory found. Run 'Gather for Show' first."
            )

        # Collect all files in media-list
        media_files = sorted([
            f for f in media_list_dir.iterdir()
            if f.is_file() and f.name != f"{episode_id}-graphics-package.zip"
        ])

        if not media_files:
            raise HTTPException(
                status_code=404,
                detail="assets/rundown directory is empty. Run 'Gather for Show' first."
            )

        zip_path = media_list_dir / f"{episode_id}-graphics-package.zip"

        # Check if zip needs regeneration
        needs_rebuild = not zip_path.exists()
        if not needs_rebuild:
            zip_mtime = zip_path.stat().st_mtime
            for f in media_files:
                if f.stat().st_mtime > zip_mtime:
                    needs_rebuild = True
                    break

        # Build file manifest
        file_manifest = []
        total_size = 0
        type_counts = {}

        for f in media_files:
            fsize = f.stat().st_size
            total_size += fsize
            # Extract type from filename pattern: {enum}-{type}-{slug}.{ext}
            parts = f.stem.split("-", 2)
            ftype = parts[1].upper() if len(parts) >= 2 else "OTHER"
            type_counts[ftype] = type_counts.get(ftype, 0) + 1
            file_manifest.append({
                "name": f.name,
                "size": fsize,
                "type": ftype
            })

        # Create or reuse zip
        if needs_rebuild:
            logger.info(f"Building graphics package for episode {episode_id} ({len(media_files)} files)")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in media_files:
                    zf.write(f, f.name)
            logger.info(f"Graphics package created: {zip_path} ({zip_path.stat().st_size} bytes)")
        else:
            logger.info(f"Using cached graphics package for episode {episode_id}")

        zip_size = zip_path.stat().st_size

        return {
            "success": True,
            "episode_id": episode_id,
            "cached": not needs_rebuild,
            "zip_filename": zip_path.name,
            "zip_size": zip_size,
            "file_count": len(media_files),
            "total_uncompressed_size": total_size,
            "type_counts": type_counts,
            "files": file_manifest,
            "download_url": f"/episodes/{episode_id}/graphics-package/download"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating graphics package for episode {episode_number}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{episode_number}/graphics-package/download")
async def download_graphics_package(
    episode_number: str,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Download the cached graphics package ZIP file.
    """
    from fastapi.responses import FileResponse
    from models_v2 import Episode
    from core.paths import ShowBuildPaths

    path_manager = ShowBuildPaths()

    episode_id = episode_number.zfill(4) if len(episode_number) < 4 else episode_number

    episode = db.query(Episode).filter(
        Episode.episode_number == int(episode_id)
    ).first()
    if not episode:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")

    episode_dir = path_manager.get_episode_dir(episode_id)
    zip_path = Path(episode_dir) / "assets" / "rundown" / f"{episode_id}-graphics-package.zip"

    if not zip_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Graphics package not found. Create it first."
        )

    return FileResponse(
        path=str(zip_path),
        filename=f"{episode_id}-graphics-package.zip",
        media_type="application/zip"
    )
