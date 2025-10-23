"""
File Inventory Scanner - Batched LLM Approach
Scans episode directories using batched LLM calls for efficient semantic matching.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from PIL import Image

from services.file_inventory_llm_v2 import OllamaLLMService

logger = logging.getLogger(__name__)

# ============================================================================
# LLM FILE CLASSIFICATION HINT SYSTEM
# ============================================================================
# This dictionary defines semantic "slots" (expected file types) that the LLM
# should match against the actual files in an episode directory.
#
# HOW IT WORKS:
# 1. Each slot (e.g., "export_video_full") represents ONE expected file type
# 2. The LLM reads the file tree (list of all files) for an episode
# 3. For each slot, the LLM uses the hints below to decide which file matches
# 4. The LLM returns: {"matches": ["path/to/file.ext"], "confidence": 90, "reasoning": "..."}
#
# HOW TO ADD HINTS:
# To help the LLM avoid classification mistakes, add hints to the "characteristics"
# field. These are sent as part of the prompt for every LLM classification batch.
#
# EXAMPLE: If you notice the LLM confusing EP0239.mp4 vs EP0239-2.mp4:
# - Add a hint explaining numeric suffixes (-2, -3) indicate re-renders
# - Specify that the HIGHEST number is the correct/final version
# - The LLM will read this context and make better decisions
#
# PROMPT CONSTRUCTION (see build_slot_batch_prompt() function):
# - Lines 416-429: Loop through each slot in a batch
# - Lines 418-427: Format each slot's purpose, characteristics, location, examples
# - Line 437: "slot_definitions" variable contains ALL formatted slot hints
# - Line 440-444: get_inventory_prompt() inserts slot_definitions into prompt template
# - The LLM sees: "SLOT: export_video_full\nPurpose: ...\nCharacteristics: ..."
#
# WHERE HINTS APPEAR IN PROMPT:
# The final prompt sent to the LLM includes a section like this:
#   ============================================================
#   SLOT: export_video_full
#   Purpose: Complete stitched episode (all blocks + breaks merged)
#
#   Characteristics:
#   - Format: MP4 or MOV
#   - Re-render suffixes: If multiple versions exist with NUMERIC suffixes...
#
#   Location: Expected in exports/ but frequently in root
#   Examples: 0239.mp4, EP0239-2.mov (re-render)
#   ============================================================
#
# Detailed slot prompts with characteristics
SLOT_PROMPTS = {
    "episode_info": {
        "purpose": "Episode metadata file containing episode number, title, air date, status, description",
        "characteristics": """- Format: Markdown file with YAML frontmatter
- Filename patterns: info.md, metadata.md, README.md, {episode}-info.md
- Location: Root of episode directory (not in subdirectories)
- Size: Small text file, typically 300-2000 bytes
- Content structure: YAML frontmatter delimited by --- followed by markdown content
- Required YAML fields: episode, title, air_date, duration, status""",
        "location_notes": "Always in root directory, never in subdirectories",
        "filename_variations": "info.md, 0239-info.md, metadata.md"
    },

    "rundown_json": {
        "purpose": "Complete rundown structure export with regions, items, cues, and media metadata",
        "characteristics": """- Format: JSON file (must be valid JSON)
- Filename patterns: {episode}-rundown.json, rundown.json
- Location: Root of episode directory
- Size: Medium file, typically 10KB-500KB
- Content structure: Contains keys like: episode, regions, rundown_items, cues""",
        "location_notes": "Root directory only",
        "filename_variations": "0239-rundown.json, rundown.json"
    },

    "capture_blocks": {
        "purpose": "Raw unedited recording of main show blocks",
        "characteristics": """- Format: Video file (MOV, MP4, MKV) - MOV most common from vMix
- Filename patterns: Contains BLOCK or Block, followed by letter (A, B, C, D)
- Location: captures/ directory OR sometimes in root
- Size: VERY LARGE - typically 2GB to 20GB+ per block
- Multiple files: Usually 2-4 blocks per episode
- Letter designation: A, B, C, D indicating order
- File size is key: These are the LARGEST video files""",
        "location_notes": "Expected in captures/ but sometimes in root",
        "filename_variations": "BLOCK-A.mov, Block-B.mp4, captures/BLOCK-A.mov"
    },

    "capture_breaks": {
        "purpose": "Recording of breaks between blocks (optional - may not exist)",
        "characteristics": """- Format: Video file (MOV, MP4, MKV)
- Filename patterns: Contains BREAK or Break, followed by number (1, 2, 3)
- Location: captures/ directory OR root
- Size: Smaller than blocks (500MB-3GB) but still large
- Optional: Not all episodes have breaks - absence is normal
- Numbering: Sequential 1, 2, 3""",
        "location_notes": "captures/ or root, may not exist",
        "filename_variations": "BREAK-1.mov, Break1.mp4"
    },

    "thumbnail_master_16x9_source": {
        "purpose": "Editable master artwork source for video platforms (widescreen)",
        "characteristics": """- Format: PSD file (Photoshop layered source)
- Filename patterns: Contains master, 16x9, widescreen, video
- Location: thumbnails/ directory
- Dimensions: 3840x2160 (4K) or 3000x1688
- Aspect ratio: MUST be 16:9 (1.77:1)
- Size: Large (20MB-200MB) due to layers""",
        "location_notes": "thumbnails/ directory",
        "filename_variations": "master-16x9.psd, widescreen-master.psd"
    },

    "thumbnail_master_16x9_export": {
        "purpose": "Flattened export of widescreen thumbnail",
        "characteristics": """- Format: PNG or JPG (no layers)
- Filename patterns: Contains 16x9, widescreen, master
- Location: thumbnails/ directory
- Dimensions: 1920x1080 or 3840x2160
- Aspect ratio: MUST be 16:9
- Size: Moderate (2MB-50MB)""",
        "location_notes": "thumbnails/ directory",
        "filename_variations": "master-16x9.png, thumb-16x9.jpg"
    },

    "thumbnail_master_1x1_source": {
        "purpose": "Editable master artwork for podcast platforms (square)",
        "characteristics": """- Format: PSD file
- Filename patterns: Contains square, 1x1, podcast, master
- Location: thumbnails/ directory
- Dimensions: 3000x3000
- Aspect ratio: MUST be 1:1 (perfect square)
- Size: Large (20MB-200MB)""",
        "location_notes": "thumbnails/ directory",
        "filename_variations": "master-square.psd, podcast-master.psd"
    },

    "thumbnail_master_1x1_export": {
        "purpose": "Flattened export of square podcast thumbnail",
        "characteristics": """- Format: PNG or JPG
- Filename patterns: Contains square, 1x1, podcast
- Location: thumbnails/ directory
- Dimensions: 1400x1400 or higher
- Aspect ratio: MUST be 1:1
- Size: Moderate (2MB-30MB)""",
        "location_notes": "thumbnails/ directory",
        "filename_variations": "podcast-square.png, thumb-square.jpg"
    },

    "export_video_blocks": {
        "purpose": "Finalized edited video per block for distribution",
        "characteristics": """- Format: MP4 video
- Filename patterns: {episode}-A.mp4, EP{episode}-Block-A.mp4
- Location: exports/ directory OR sometimes root
- Size: Moderate (500MB-3GB) - SMALLER than raw captures
- Multiple files: One per block (A, B, C, D)
- Block designation: Episode number AND block letter""",
        "location_notes": "Expected in exports/ but sometimes in root",
        "filename_variations": "0239-A.mp4, EP0239-Block-A.mp4"
    },

    "export_audio_blocks": {
        "purpose": "Audio extracted from block videos (MP3 per block)",
        "characteristics": """- Format: MP3 audio
- Filename patterns: {episode}-A.mp3, {episode}-Block-A.mp3
- Location: exports/ directory
- Bitrate: 192kbps or 320kbps
- Size: 50MB-200MB per block
- Block designation: Episode number AND block letter""",
        "location_notes": "exports/ directory",
        "filename_variations": "0239-A.mp3, 0239-Block-A.mp3"
    },

    "export_video_full": {
        "purpose": "Complete stitched episode (all blocks + breaks merged)",
        "characteristics": """- Format: MP4 or MOV (MP4 most common)
- Filename patterns: {episode}.mp4, {episode}-full.mp4, EP{episode}.mp4
- Location: Expected in exports/ BUT sometimes left in root
- Size: VERY LARGE - multiple gigabytes (4GB-15GB+)
- No block designation: Filename does NOT contain block letters
- File size indicator: Usually LARGEST or second-largest file
- Non-specific naming: Often just episode number indicates main file
- Prefix variations: Some episodes use "EP" prefix before episode number
- RE-RENDER PATTERN (semantic rule): When multiple video files match the same episode,
  some may have VARIATION INDICATORS suggesting they are subsequent attempts/corrections.
  These indicators mean "this supersedes the earlier version" - ALWAYS prefer the version with indicators.

  REASONING: Production workflows often require re-rendering videos due to technical issues,
  corrections, or improvements. The original file is kept for reference, but the variation
  indicates the CURRENT/CORRECT version to use.

  Variation indicators appear AFTER episode identifier, BEFORE file extension, and can be:

  1. NUMERIC suffixes: {episode}[sep]N.ext where N=integer (2,3,4...), sep is -, _, or space
     Pattern meaning: "This is the Nth attempt"
     Selection rule: Higher number = more recent = correct file
     Examples: "0244-2.mov" > "0244.mov" | "0199_3.mp4" > "0199.mp4"

  2. SEMANTIC labels: {episode}-LABEL.ext indicating retry/correction
     Pattern meaning: Label suggests "this replaces the original"
     Common patterns: RE, REDO, FIX, FIXED, FINAL, V2, V3, RERENDER, CORRECTED, RETRY, NEW, UPDATED
     Any word suggesting "subsequent attempt" qualifies
     Selection rule: Labeled version > unlabeled version
     Examples: "EP0239-RE.mov" > "EP0239.mov" | "0155-UPDATED.mp4" > "0155.mp4"

  3. COMBINED patterns: {episode}-LABEL[N].ext
     Example: "EP0244-RE2.mov" means "second re-render attempt"
     Selection rule: Higher number within same label wins

  GENERAL PRINCIPLE: If filename suggests it's NOT the first attempt, it's probably the correct one.
  Think: "Why would someone add extra text to the filename? To distinguish it from the original.""",
        "location_notes": "Expected in exports/ but frequently in root",
        "filename_variations": "{episode}.mp4, EP{episode}.mp4, {episode}-full.mp4, {episode}-N.mov (N=re-render number)"
    },

    "export_audio_full": {
        "purpose": "Full episode audio for podcast (all blocks merged)",
        "characteristics": """- Format: MP3 audio
- Filename patterns: {episode}.mp3, {episode}-full.mp3, {episode}-podcast.mp3
- Location: exports/ directory
- Bitrate: 192kbps or 320kbps
- Size: LARGEST audio file (200MB-600MB)
- No block designation: Full episode length""",
        "location_notes": "exports/ directory",
        "filename_variations": "0239.mp3, 0239-full.mp3, 0239-podcast.mp3"
    },

    "export_subtitles": {
        "purpose": "Subtitle/caption file for full episode",
        "characteristics": """- Format: SRT, VTT, or SUB
- Filename patterns: {episode}.srt, {episode}-subtitles.srt
- Location: exports/ directory
- Size: Very small text file (10KB-200KB)
- Extension: .srt most common""",
        "location_notes": "exports/ directory",
        "filename_variations": "0239.srt, 0239-subtitles.srt, 0239.vtt"
    },

    "export_thumbnail_1920x1080": {
        "purpose": "HD distribution thumbnail at exactly 1920x1080",
        "characteristics": """- Format: PNG or JPG
- Filename patterns: Contains poster, thumbnail, 1920x1080, 16x9
- Location: exports/ directory
- Dimensions: EXACTLY 1920x1080 pixels
- Aspect ratio: 16:9
- Size: 500KB-5MB""",
        "location_notes": "exports/ directory",
        "filename_variations": "0239-poster-16x9.png, thumbnail-1920x1080.png"
    },

    "export_thumbnail_1280x720": {
        "purpose": "Web-optimized thumbnail for YouTube/Rumble (720p)",
        "characteristics": """- Format: PNG or JPG
- Filename patterns: Contains web, 720, youtube, 1280x720
- Location: exports/ directory
- Dimensions: Exactly 1280x720 pixels
- Size: Must be under 2MB
- Purpose: YouTube/Rumble optimized""",
        "location_notes": "exports/ directory",
        "filename_variations": "0239-youtube.jpg, thumbnail-720p.png"
    },

    "export_thumbnail_1400x1400": {
        "purpose": "Square podcast thumbnail",
        "characteristics": """- Format: PNG or JPG
- Filename patterns: Contains podcast, square, 1400
- Location: exports/ directory
- Dimensions: 1400x1400 or 1500x1500
- Aspect ratio: 1:1 (square)
- Purpose: Podcast platforms""",
        "location_notes": "exports/ directory",
        "filename_variations": "0239-podcast-square.png, podcast-1400.jpg"
    },

    "project_vmix": {
        "purpose": "vMix production project file from live show",
        "characteristics": """- Format: VMIX file
- Filename patterns: {episode}.vmix
- Location: projects/ directory OR root
- Extension: .vmix (unique to vMix)
- Size: 1MB-50MB""",
        "location_notes": "projects/ directory or root",
        "filename_variations": "0239.vmix, EP0239.vmix"
    },

    "project_guest_teaser_source": {
        "purpose": "After Effects source for guest teasers",
        "characteristics": """- Format: AEP file (After Effects)
- Filename patterns: teaser.aep, guest-teaser.aep
- Location: projects/teasers/guest-teaser-{guest}/source/
- Extension: .aep
- Multiple files: One per guest""",
        "location_notes": "Deep in projects/teasers/{guest}/source/ structure",
        "filename_variations": "teaser.aep, john-doe-teaser.aep"
    },

    "project_guest_teaser_tonight": {
        "purpose": "Guest Tonight teaser video export",
        "characteristics": """- Format: MP4 video
- Filename patterns: MUST contain 'Guest_Tonight' or 'tonight' AND guest name
- Location: projects/teasers/guest-teaser-{guest}/
- Naming: Guest_Tonight_{guest}.mp4
- Size: 10MB-100MB, short duration""",
        "location_notes": "projects/teasers/{guest}/ directory",
        "filename_variations": "Guest_Tonight_john-doe.mp4, tonight-jane-smith.mp4"
    },

    "project_guest_teaser_up_next": {
        "purpose": "Guest Up Next teaser video export",
        "characteristics": """- Format: MP4 video
- Filename patterns: MUST contain 'Guest_up_next' or 'up_next' or 'upnext'
- Location: projects/teasers/guest-teaser-{guest}/
- Naming: Guest_up_next_{guest}.mp4
- Size: 10MB-100MB""",
        "location_notes": "projects/teasers/{guest}/ directory",
        "filename_variations": "Guest_up_next_john-doe.mp4, upnext-jane-smith.mp4"
    },

    "project_guest_teaser_follow": {
        "purpose": "Guest Follow on Social teaser video",
        "characteristics": """- Format: MP4 video
- Filename patterns: MUST contain 'Guest_follow' or 'follow' or 'social'
- Location: projects/teasers/guest-teaser-{guest}/
- Naming: Guest_follow_on_social_{guest}.mp4
- Size: 10MB-100MB""",
        "location_notes": "projects/teasers/{guest}/ directory",
        "filename_variations": "Guest_follow_on_social_john-doe.mp4, follow-jane.mp4"
    },

    "assets_video": {
        "purpose": "Video clips used in show (NOT captures or exports)",
        "characteristics": """- Format: MP4 or MOV
- Location: assets/video/ OR assets/sot/ only
- Size: 5MB-500MB - SMALLER than captures/exports
- Multiple files: Collection of clips
- Descriptive names: Song names, clip descriptions
- NOT captures: Finished clips, not raw recordings
- NOT exports: Source assets used IN show""",
        "location_notes": "assets/video/ or assets/sot/ only",
        "filename_variations": "frog-song.mp4, mary-grace-instagram.mp4"
    },

    "assets_images": {
        "purpose": "Still images used in show",
        "characteristics": """- Format: PNG, JPG, JPEG, WEBP
- Location: assets/images/ directory only
- Size: 10KB-10MB
- Multiple files: Collection of images
- NOT thumbnails: Assets used IN show
- NOT in gfx folder: General images""",
        "location_notes": "assets/images/ only",
        "filename_variations": "dan-frost.jpg, charlie-kirk.png"
    },

    "assets_audio": {
        "purpose": "Audio clips used in show (NOT full episode audio)",
        "characteristics": """- Format: MP3 or WAV
- Location: assets/audio/ directory only
- Size: 100KB-50MB
- Multiple files: Sound effects, music clips
- NOT full episode: Clips used IN show""",
        "location_notes": "assets/audio/ only",
        "filename_variations": "intro-music.mp3, sound-effect.wav"
    },

    "assets_graphics": {
        "purpose": "Graphics overlays like lower thirds, title cards",
        "characteristics": """- Format: PNG files (often with transparency)
- Location: assets/graphics/ OR assets/gfx/ only
- Size: 50KB-5MB
- Multiple files: Overlay graphics
- Purpose: Lower thirds, name plates, title cards""",
        "location_notes": "assets/graphics/ or assets/gfx/ only",
        "filename_variations": "lower-third.png, title-card.png"
    }
}


def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from file for directory tree."""
    try:
        stat = file_path.stat()
        metadata = {
            "path": str(file_path),
            "filename": file_path.name,
            "extension": file_path.suffix.lower(),
            "size": stat.st_size,
            "relative_path": None  # Will be set by caller
        }

        # Get image dimensions if applicable
        if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.psd', '.gif', '.webp']:
            try:
                with Image.open(file_path) as img:
                    metadata["dimensions"] = f"{img.width}x{img.height}"
                    ratio = img.width / img.height
                    if 1.7 < ratio < 1.8:
                        metadata["aspect_ratio"] = "16:9"
                    elif 0.95 < ratio < 1.05:
                        metadata["aspect_ratio"] = "1:1"
                    else:
                        metadata["aspect_ratio"] = f"{ratio:.2f}"
            except:
                pass

        return metadata
    except Exception as e:
        logger.error(f"Error getting file metadata: {e}")
        return None


def scan_directory_recursive(base_path: Path, exclude_dirs: List[str] = None) -> List[Dict[str, Any]]:
    """Scan directory and collect file metadata."""
    if exclude_dirs is None:
        exclude_dirs = [
            '.git', '.syncthing', '.stfolder', '.blackmagicsync-v2',
            '.DS_Store', '.claude', '.vscode', '__pycache__',
            'node_modules', '.stversions'
        ]

    files = []
    for item in base_path.rglob('*'):
        if any(excluded in item.parts for excluded in exclude_dirs):
            continue
        if item.is_file() and not item.name.startswith('.'):
            file_meta = get_file_metadata(item)
            if file_meta:
                file_meta["relative_path"] = str(item.relative_to(base_path))
                files.append(file_meta)

    return files


def build_directory_tree(files: List[Dict[str, Any]]) -> str:
    """Build readable directory tree from file list."""
    tree_lines = []
    for f in files:
        size_mb = f['size'] / (1024 * 1024)
        size_str = f"{size_mb:.1f}MB" if size_mb >= 1 else f"{f['size']}bytes"
        dims = f.get('dimensions', '')
        ratio = f.get('aspect_ratio', '')

        details = f"{f['extension']}, {size_str}"
        if dims:
            details += f", {dims}"
        if ratio:
            details += f", {ratio}"

        tree_lines.append(f"  {f['relative_path']} ({details})")

    return "\n".join(sorted(tree_lines))


def build_slot_batch_prompt(slot_names: List[str], file_tree: str, episode_number: str, db_session=None) -> Tuple[str, str, bool]:
    """
    Build system and user prompts for batched slot matching.

    Args:
        slot_names: List of slot names to evaluate
        file_tree: Directory tree string
        episode_number: Episode number
        db_session: Database session for prompt overrides (optional)

    Returns:
        Tuple of (system_prompt, user_prompt, overridden)
    """
    from services.file_inventory_llm_v2 import get_inventory_prompt

    # Build slot list (explicit enumeration)
    slot_list = "\n".join([f"  - {slot_name}" for slot_name in slot_names])

    # Build slot definitions string
    slot_definitions = ""
    for slot_name in slot_names:
        slot_info = SLOT_PROMPTS[slot_name]
        slot_definitions += f"""{'='*60}
SLOT: {slot_name}
Purpose: {slot_info['purpose']}

Characteristics:
{slot_info['characteristics']}

Location: {slot_info['location_notes']}
Examples: {slot_info['filename_variations']}
{'='*60}

"""

    # Get prompt with optional override
    variables = {
        "episode_number": episode_number,
        "file_tree": file_tree,
        "slot_count": len(slot_names),
        "slot_list": slot_list,  # NEW: Explicit slot enumeration
        "slot_definitions": slot_definitions
    }

    system_prompt, user_prompt, overridden = get_inventory_prompt(
        "inventory-batch-match-slots",
        variables,
        db_session
    )

    return system_prompt, user_prompt, overridden


async def match_slots_batched(
    files: List[Dict[str, Any]],
    episode_number: str,
    llm_service: OllamaLLMService,
    batch_size: int = 5,
    db_session = None
) -> Dict[str, Any]:
    """
    Match files to slots using batched LLM calls.

    Args:
        files: List of file metadata
        episode_number: Episode number
        llm_service: Ollama LLM service
        batch_size: Number of slots per LLM call
        db_session: Database session for prompt overrides (optional)

    Returns:
        Dictionary mapping slot names to match results
    """
    # Build directory tree once
    file_tree = build_directory_tree(files)

    # Get all slot names
    all_slots = list(SLOT_PROMPTS.keys())

    # Process slots in batches
    all_results = {}

    for i in range(0, len(all_slots), batch_size):
        batch = all_slots[i:i+batch_size]
        logger.info(f"Processing slot batch {i//batch_size + 1}: {batch}")

        # Build prompts (with optional override support)
        system_prompt, user_prompt, overridden = build_slot_batch_prompt(batch, file_tree, episode_number, db_session)
        if overridden:
            logger.info(f"Using prompt override for batch {i//batch_size + 1}")

        try:
            # Call LLM with optimized parameters
            response_text = await llm_service.generate(
                system_prompt,
                user_prompt,
                temperature=0.1,  # Lower for stricter adherence (was 0.3)
                response_format="json",
                max_tokens=2000,  # Ensure complete output
                top_p=0.9  # Allow diverse token choices
            )

            # Parse response
            batch_results = json.loads(response_text)

            # POST-PROCESSING FALLBACK: Ensure all slots from batch are present
            # This is the safety net recommended by all LLM consultations
            for slot_name in batch:
                if slot_name not in batch_results:
                    logger.warning(f"Slot '{slot_name}' missing from LLM response, adding empty fallback")
                    batch_results[slot_name] = {
                        "matches": [],
                        "confidence": 0,
                        "reasoning": "Slot missing from LLM response (post-processing fallback applied)"
                    }

            # Build set of actual file paths for validation
            actual_files = set(f.get('relative_path', f.get('path', '')) for f in files)

            # Validate and normalize response structure
            for slot_name in batch:
                if slot_name in batch_results:
                    slot_value = batch_results[slot_name]

                    # Extract matches list
                    if isinstance(slot_value, list):
                        matches = slot_value
                        confidence = 75
                        reasoning = "LLM returned simplified list format"
                    elif isinstance(slot_value, dict):
                        matches = slot_value.get('matches', [])
                        confidence = slot_value.get('confidence', 75)
                        reasoning = slot_value.get('reasoning', 'No reasoning provided')
                    else:
                        matches = []
                        confidence = 0
                        reasoning = f"Invalid response format: {type(slot_value)}"

                    # Validate that matched files actually exist
                    if isinstance(matches, list):
                        validated_matches = []
                        hallucinated = []
                        for match in matches:
                            if match in actual_files:
                                validated_matches.append(match)
                            else:
                                hallucinated.append(match)

                        if hallucinated:
                            logger.warning(f"LLM hallucinated non-existent files for {slot_name}: {hallucinated}")
                            if validated_matches:
                                reasoning += f" (removed {len(hallucinated)} hallucinated files)"
                            else:
                                reasoning = f"LLM hallucinated files that don't exist: {', '.join(hallucinated)}"
                                confidence = 0

                        all_results[slot_name] = {
                            "matches": validated_matches,
                            "confidence": confidence,
                            "reasoning": reasoning
                        }
                    else:
                        all_results[slot_name] = {
                            "matches": [],
                            "confidence": 0,
                            "reasoning": "Matches field was not a list"
                        }
                else:
                    all_results[slot_name] = {
                        "matches": [],
                        "confidence": 0,
                        "reasoning": "Slot missing from LLM response"
                    }

            logger.info(f"Batch {i//batch_size + 1} completed successfully")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON for batch {batch}: {e}")
            # Return empty for this batch
            for slot in batch:
                all_results[slot] = {
                    "matches": [],
                    "confidence": 0,
                    "reasoning": f"JSON parse error: {str(e)}"
                }
        except Exception as e:
            logger.error(f"Error processing batch {batch}: {e}")
            for slot in batch:
                all_results[slot] = {
                    "matches": [],
                    "confidence": 0,
                    "reasoning": f"Error: {str(e)}"
                }

    return all_results


def generate_mapping_yaml(
    episode_number: str,
    slot_results: Dict[str, Any],
    total_files: int,
    scan_metadata: Dict[str, Any]
) -> str:
    """Generate YAML mapping file from slot results."""

    # Calculate statistics
    slots_filled = sum(1 for r in slot_results.values() if r.get('matches'))
    total_slots = len(slot_results)
    files_matched = len(set(
        match for result in slot_results.values()
        for match in result.get('matches', [])
    ))

    mapping = {
        "episode": episode_number,
        "scan_timestamp": datetime.now().isoformat(),
        "scan_version": "3.0-batched",
        "llm_model": scan_metadata.get("llm_model", "llama3:latest"),
        "source_system": scan_metadata.get("source_system", "syncthing"),
        "batch_size": scan_metadata.get("batch_size", 5),
        "slots": slot_results,
        "statistics": {
            "total_slots": total_slots,
            "slots_filled": slots_filled,
            "slots_empty": total_slots - slots_filled,
            "total_files_scanned": total_files,
            "files_matched": files_matched,
            "files_unmatched": total_files - files_matched
        }
    }

    return yaml.dump(mapping, default_flow_style=False, allow_unicode=True, sort_keys=False)
