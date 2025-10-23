"""
File Inventory Scanner Service - Slot-Based Version
Scans episode directories and matches files to canonical slot expectations using LLM analysis.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from PIL import Image
import mimetypes

from services.file_inventory_llm import match_file_to_expectation, classify_stray_file

logger = logging.getLogger(__name__)

# Slot-based canonical expectations
CANONICAL_EXPECTATIONS = [
    # Core Episode Files
    {
        "slot": "episode_info",
        "category": "metadata",
        "purpose": "Contains episode metadata (number, title, air date, status, description)",
        "characteristics": "Markdown format with YAML frontmatter, contains fields: episode, title, air_date, duration, status",
        "location_hints": "info.md, metadata.md, README.md",
        "required": True,
        "multiplicity": "single"
    },
    {
        "slot": "rundown_json",
        "category": "metadata",
        "purpose": "Complete rundown structure export (regions, items, cues, media metadata)",
        "characteristics": "JSON format, contains: episode, regions, rundown_items, cues",
        "location_hints": "{EPISODE}-rundown.json, rundown.json",
        "required": False,
        "multiplicity": "single"
    },

    # Raw Captures (dynamic collections)
    {
        "slot": "capture_blocks",
        "category": "capture",
        "purpose": "Raw unedited recording of main show blocks",
        "characteristics": "Video file (MOV, MP4, MKV), large file size (multi-GB), high bitrate, contains BLOCK or Block in name or path, may have letter designation (A/B/C/D)",
        "location_hints": "captures/BLOCK-A.mov, captures/Block-A.mp4, BLOCK-A.mov",
        "required": False,
        "multiplicity": "multiple"
    },
    {
        "slot": "capture_breaks",
        "category": "capture",
        "purpose": "Recording of breaks between main blocks (optional, may not exist)",
        "characteristics": "Video file (MOV, MP4, MKV), contains BREAK or Break in name, numeric designation (1/2/3)",
        "location_hints": "captures/BREAK-1.mov, captures/Break1.mp4",
        "required": False,
        "multiplicity": "multiple"
    },

    # Thumbnail Masters
    {
        "slot": "thumbnail_master_16x9_source",
        "category": "thumbnail",
        "purpose": "Editable master artwork for video platforms (16:9 aspect ratio)",
        "characteristics": "PSD file, high resolution (3840x2160), 16:9 aspect ratio, contains master/16x9/widescreen",
        "location_hints": "thumbnails/master-16x9.psd, thumbnails/widescreen-master.psd",
        "required": False,
        "multiplicity": "single"
    },
    {
        "slot": "thumbnail_master_16x9_export",
        "category": "thumbnail",
        "purpose": "High-resolution export of widescreen artwork",
        "characteristics": "PNG or JPG, high resolution (1920x1080+), 16:9 aspect ratio",
        "location_hints": "thumbnails/master-16x9.png, thumbnails/thumbnail-16x9.jpg",
        "required": False,
        "multiplicity": "single"
    },
    {
        "slot": "thumbnail_master_1x1_source",
        "category": "thumbnail",
        "purpose": "Editable master artwork for podcast platforms (1:1 aspect ratio)",
        "characteristics": "PSD file, high resolution (3000x3000), square aspect ratio",
        "location_hints": "thumbnails/master-square.psd, thumbnails/podcast-master.psd",
        "required": False,
        "multiplicity": "single"
    },
    {
        "slot": "thumbnail_master_1x1_export",
        "category": "thumbnail",
        "purpose": "High-resolution export of square artwork",
        "characteristics": "PNG or JPG, high resolution (1400x1400+), square aspect ratio",
        "location_hints": "thumbnails/master-square.png, thumbnails/podcast.jpg",
        "required": False,
        "multiplicity": "single"
    },

    # Distribution Exports
    {
        "slot": "export_video_blocks",
        "category": "export",
        "purpose": "Finalized edited video for distribution (per block)",
        "characteristics": "MP4 video, standard resolution (1920x1080), contains episode number + block letter",
        "location_hints": "exports/{EPISODE}-A.mp4, {EPISODE}-Block-A.mp4",
        "required": False,
        "multiplicity": "multiple"
    },
    {
        "slot": "export_audio_blocks",
        "category": "export",
        "purpose": "Audio extracted from block video (MP3 format)",
        "characteristics": "MP3 audio file, 192kbps, contains episode number + block letter",
        "location_hints": "exports/{EPISODE}-A.mp3, {EPISODE}-Block-A.mp3",
        "required": False,
        "multiplicity": "multiple"
    },
    {
        "slot": "export_video_full",
        "category": "export",
        "purpose": "Complete stitched episode (all blocks + breaks merged)",
        "characteristics": "MP4 video, large file size, contains episode number without block letter",
        "location_hints": "exports/{EPISODE}.mp4, {EPISODE}-full.mp4",
        "required": False,
        "multiplicity": "single"
    },
    {
        "slot": "export_audio_full",
        "category": "export",
        "purpose": "Full episode audio (podcast format)",
        "characteristics": "MP3 audio, 192kbps, contains episode number, largest audio file",
        "location_hints": "exports/{EPISODE}.mp3, {EPISODE}-full.mp3",
        "required": False,
        "multiplicity": "single"
    },
    {
        "slot": "export_subtitles",
        "category": "export",
        "purpose": "Subtitle/caption file for full episode",
        "characteristics": "SRT, VTT, or SUB format, text-based, small file size",
        "location_hints": "exports/{EPISODE}.srt, {EPISODE}-subtitles.srt",
        "required": False,
        "multiplicity": "single"
    },
    {
        "slot": "export_thumbnail_1920x1080",
        "category": "export",
        "purpose": "HD distribution thumbnail (1920x1080)",
        "characteristics": "PNG or JPG, exactly 1920x1080, 16:9 aspect ratio",
        "location_hints": "exports/{EPISODE}-poster-16x9.png, exports/thumbnail-1920x1080.png",
        "required": False,
        "multiplicity": "single"
    },
    {
        "slot": "export_thumbnail_1280x720",
        "category": "export",
        "purpose": "Web-optimized thumbnail (YouTube, Rumble)",
        "characteristics": "PNG or JPG, 1280x720, under 2MB",
        "location_hints": "exports/{EPISODE}-poster-16x9-web.png, exports/youtube-thumbnail.jpg",
        "required": False,
        "multiplicity": "single"
    },
    {
        "slot": "export_thumbnail_1400x1400",
        "category": "export",
        "purpose": "Square podcast thumbnail",
        "characteristics": "PNG or JPG, 1400x1400, square aspect ratio",
        "location_hints": "exports/{EPISODE}-podcast-square.png",
        "required": False,
        "multiplicity": "single"
    },

    # Project Files
    {
        "slot": "project_vmix",
        "category": "project",
        "purpose": "vMix production project file for live show",
        "characteristics": "VMIX file format, contains episode number",
        "location_hints": "projects/{EPISODE}.vmix, {EPISODE}.vmix",
        "required": False,
        "multiplicity": "single"
    },
    {
        "slot": "project_guest_teaser_source",
        "category": "project",
        "purpose": "After Effects guest teaser master project (per guest)",
        "characteristics": "AEP file, in teaser directory with guest name",
        "location_hints": "projects/teasers/guest-teaser-{guest}/source/*.aep",
        "required": False,
        "multiplicity": "multiple"
    },
    {
        "slot": "project_guest_teaser_tonight",
        "category": "project",
        "purpose": "Guest Tonight teaser export (per guest)",
        "characteristics": "MP4 file, filename pattern: Guest_Tonight_{guest}.mp4",
        "location_hints": "projects/teasers/guest-teaser-{guest}/Guest_Tonight_*.mp4",
        "required": False,
        "multiplicity": "multiple"
    },
    {
        "slot": "project_guest_teaser_up_next",
        "category": "project",
        "purpose": "Guest Up Next teaser export (per guest)",
        "characteristics": "MP4 file, filename pattern: Guest_up_next_{guest}.mp4",
        "location_hints": "projects/teasers/guest-teaser-{guest}/Guest_up_next_*.mp4",
        "required": False,
        "multiplicity": "multiple"
    },
    {
        "slot": "project_guest_teaser_follow",
        "category": "project",
        "purpose": "Guest Follow on Social teaser export (per guest)",
        "characteristics": "MP4 file, filename pattern: Guest_follow_on_social_{guest}.mp4",
        "location_hints": "projects/teasers/guest-teaser-{guest}/Guest_follow_on_social_*.mp4",
        "required": False,
        "multiplicity": "multiple"
    },

    # Asset Collections
    {
        "slot": "assets_video",
        "category": "asset",
        "purpose": "Final video clip used in show",
        "characteristics": "MP4 or MOV, in assets/video or assets/sot folder",
        "location_hints": "assets/video/*.mp4, assets/sot/*.mp4",
        "required": False,
        "multiplicity": "multiple"
    },
    {
        "slot": "assets_images",
        "category": "asset",
        "purpose": "Still image used in show",
        "characteristics": "PNG or JPG, in assets/images folder",
        "location_hints": "assets/images/*.png, assets/images/*.jpg",
        "required": False,
        "multiplicity": "multiple"
    },
    {
        "slot": "assets_audio",
        "category": "asset",
        "purpose": "Audio clip used in show",
        "characteristics": "MP3 or WAV, in assets/audio folder",
        "location_hints": "assets/audio/*.mp3, assets/audio/*.wav",
        "required": False,
        "multiplicity": "multiple"
    },
    {
        "slot": "assets_graphics",
        "category": "asset",
        "purpose": "Graphics overlay (lower third, title card)",
        "characteristics": "PNG file, in assets/graphics or assets/gfx folder",
        "location_hints": "assets/graphics/*.png, assets/gfx/*.png",
        "required": False,
        "multiplicity": "multiple"
    }
]


def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from a file for LLM analysis.
    """
    try:
        stat = file_path.stat()

        metadata = {
            "path": str(file_path),
            "filename": file_path.name,
            "extension": file_path.suffix.lower(),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "folder_path": str(file_path.parent),
            "dimensions": "N/A",
            "duration": "N/A"
        }

        # Try to get image dimensions
        if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.psd', '.gif', '.webp']:
            try:
                with Image.open(file_path) as img:
                    metadata["dimensions"] = f"{img.width}x{img.height}"

                    # Calculate aspect ratio
                    if img.width > 0 and img.height > 0:
                        ratio = img.width / img.height
                        if 1.7 < ratio < 1.8:
                            metadata["aspect_ratio"] = "16:9"
                        elif 0.95 < ratio < 1.05:
                            metadata["aspect_ratio"] = "1:1 (square)"
                        elif 0.5 < ratio < 0.6:
                            metadata["aspect_ratio"] = "9:16 (vertical)"
                        else:
                            metadata["aspect_ratio"] = f"{ratio:.2f}"
            except Exception as e:
                logger.debug(f"Could not read image dimensions for {file_path}: {e}")

        return metadata

    except Exception as e:
        logger.error(f"Error getting file metadata for {file_path}: {e}")
        return {
            "path": str(file_path),
            "filename": file_path.name,
            "extension": file_path.suffix.lower(),
            "size": 0,
            "error": str(e)
        }


def scan_directory_recursive(base_path: Path, exclude_dirs: List[str] = None) -> List[Dict[str, Any]]:
    """
    Recursively scan a directory and collect all file metadata.
    """
    if exclude_dirs is None:
        exclude_dirs = [
            '.git', '.syncthing', '.stfolder', '.blackmagicsync-v2',
            '.DS_Store', '.claude', '.vscode', '__pycache__',
            'node_modules', '.stversions'
        ]

    files = []

    try:
        for item in base_path.rglob('*'):
            # Skip excluded directories
            if any(excluded in item.parts for excluded in exclude_dirs):
                continue

            # Skip directories, only process files
            if item.is_file():
                # Skip hidden files
                if item.name.startswith('.'):
                    continue

                file_meta = get_file_metadata(item)
                # Add relative path for easier matching
                file_meta["relative_path"] = str(item.relative_to(base_path))
                files.append(file_meta)

    except Exception as e:
        logger.error(f"Error scanning directory {base_path}: {e}")

    return files


async def match_files_to_expectations(
    files: List[Dict[str, Any]],
    episode_number: str,
    llm_service,
    db_session = None,
    confidence_threshold: int = 80
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Match scanned files to canonical slot expectations using LLM.
    """
    matched = []
    unmatched_files = files.copy()

    for expectation in CANONICAL_EXPECTATIONS:
        # Substitute episode number in location hints
        location_hints = expectation["location_hints"].replace("{EPISODE}", episode_number)
        expectation_copy = expectation.copy()
        expectation_copy["location_hints"] = location_hints

        best_match = None
        best_confidence = 0
        best_file_idx = None

        # Try to match each remaining file to this expectation
        for idx, file_meta in enumerate(unmatched_files):
            try:
                result = await match_file_to_expectation(
                    file_meta,
                    expectation_copy,
                    llm_service,
                    db_session
                )

                if result.get("matches") and result.get("confidence", 0) > best_confidence:
                    best_match = result
                    best_confidence = result["confidence"]
                    best_file_idx = idx

            except Exception as e:
                logger.error(f"Error matching file {file_meta['filename']}: {e}")

        # If we found a good match, record it
        if best_match and best_confidence >= confidence_threshold:
            matched_expectation = {
                "slot": expectation["slot"],
                "category": expectation["category"],
                "purpose": expectation["purpose"],
                "matched": True,
                "confidence": best_confidence,
                "file_path": unmatched_files[best_file_idx]["relative_path"],
                "file_size": unmatched_files[best_file_idx]["size"],
                "reasoning": best_match.get("reasoning", ""),
                "needs_review": best_confidence < 90
            }
            matched.append(matched_expectation)

            # Remove matched file from unmatched list
            unmatched_files.pop(best_file_idx)

            # For single-file expectations, stop after first match
            if expectation["multiplicity"] == "single":
                continue
        else:
            # No match found for this expectation
            matched_expectation = {
                "slot": expectation["slot"],
                "category": expectation["category"],
                "purpose": expectation["purpose"],
                "matched": False,
                "confidence": 0,
                "file_path": None,
                "reasoning": "No file found matching this expectation"
            }
            matched.append(matched_expectation)

    return matched, unmatched_files


async def classify_unmatched_files(
    files: List[Dict[str, Any]],
    llm_service,
    db_session = None
) -> List[Dict[str, Any]]:
    """
    Classify files that didn't match any canonical slot expectation.
    """
    classified = []

    for file_meta in files:
        try:
            result = await classify_stray_file(file_meta, llm_service, db_session)

            stray_file = {
                "file_path": file_meta["relative_path"],
                "file_size": file_meta["size"],
                "category": result.get("category", "stray.unknown"),
                "confidence": result.get("confidence", 0),
                "reasoning": result.get("reasoning", ""),
                "suggested_action": result.get("suggested_action", "review"),
                "relocation_target": result.get("relocation_target"),
                "safety": result.get("safety", "caution")
            }
            classified.append(stray_file)

        except Exception as e:
            logger.error(f"Error classifying file {file_meta['filename']}: {e}")
            classified.append({
                "file_path": file_meta["relative_path"],
                "file_size": file_meta["size"],
                "category": "stray.unknown",
                "confidence": 0,
                "reasoning": f"Error during classification: {str(e)}",
                "suggested_action": "review",
                "safety": "caution"
            })

    return classified


def generate_mapping_file(
    episode_number: str,
    matched: List[Dict[str, Any]],
    stray_files: List[Dict[str, Any]],
    total_files_scanned: int,
    scan_metadata: Dict[str, Any]
) -> str:
    """
    Generate UFDP-format YAML mapping file with slot-based structure.
    """
    matched_count = sum(1 for m in matched if m["matched"])
    unmatched_count = len(matched) - matched_count
    needs_review_count = sum(1 for m in matched if m.get("needs_review", False))

    mapping = {
        "episode": episode_number,
        "scan_timestamp": datetime.now().isoformat(),
        "scan_version": "2.0",
        "llm_model": scan_metadata.get("llm_model", "llama3.2"),
        "source_system": scan_metadata.get("source_system", "syncthing"),
        "slots": matched,
        "unclassified_files": stray_files,
        "statistics": {
            "total_slots": len(matched),
            "slots_filled": matched_count,
            "slots_empty": unmatched_count,
            "needs_review": needs_review_count,
            "unclassified_files": len(stray_files),
            "total_files_scanned": total_files_scanned
        }
    }

    return yaml.dump(mapping, default_flow_style=False, allow_unicode=True, sort_keys=False)
