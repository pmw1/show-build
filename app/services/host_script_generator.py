"""
Host Script Generator - Database-based script compilation for PDF output.

Generates formatted HTML scripts from database rundown items with three preset modes:
1. HOST_FULL - Complete script with all cues, visuals, and production info
2. HOST_CLEAN - Spoken text only with minimal cue indicators (teleprompter-friendly)
3. PRODUCTION - Technical rundown with timing, all cues, media references

Block Structure:
- BLOCK A: All content from show start until BREAK 1
- BLOCK B: Content after BREAK 1 until BREAK 2
- BLOCK C: Content after BREAK 2 until BREAK 3
- And so on...

Each block has clear START/END headers for easy navigation.
"""
import re
import html
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from database import SessionLocal
from models_v2 import Episode, Rundown, RundownItem, Season, Show, SOTProcessingJob

logger = logging.getLogger(__name__)


def _extract_field(cue_content: str, field_pattern: str) -> str:
    """Extract a field value from cue content.

    Handles multi-line values and ] characters inside the value by anchoring
    the closing ] at a real field boundary (next [Field: line, end-cue marker,
    or end of content).

    Args:
        cue_content: The raw text inside <!-- Begin Cue -->...<!-- End Cue -->
        field_pattern: Field name regex (e.g. 'Quote', 'Media\\s*[Uu]rl', 'Asset\\s*Id')

    Returns:
        The captured value with surrounding whitespace stripped, or '' if not found.
    """
    pattern = rf'\[{field_pattern}:\s*(.*?)\](?=\s*(?:\n\s*\[|\n\s*<!--|\Z))'
    match = re.search(pattern, cue_content, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ''


class ScriptPreset(Enum):
    """Script generation presets."""
    HOST_FULL = "host_full"        # Everything: text, cues, visuals
    HOST_CLEAN = "host_clean"      # Spoken text + minimal cue markers
    PRODUCTION = "production"      # Technical view with all details


# Item types that represent a BREAK (block separator)
# Must match useRegions.js break region allowedItemTypes + legacy types
# Regions break types: ad, promo, cta  |  Legacy: break, advertisement
BREAK_ITEM_TYPES = {'break', 'advertisement', 'ad', 'promo', 'cta'}

# Speaker display configuration
SPEAKER_CONFIG = {
    'josh': {'name': 'JOSH', 'color': '#1565c0'},
    'host': {'name': 'HOST', 'color': '#1565c0'},
    'guest': {'name': 'GUEST', 'color': '#2e7d32'},
    'caller': {'name': 'CALLER', 'color': '#ef6c00'},
    'announcer': {'name': 'ANNOUNCER', 'color': '#7b1fa2'},
    'narrator': {'name': 'NARRATOR', 'color': '#5d4037'},
}


def generate_host_script(
    episode_number: str,
    output_dir: Optional[str] = None,
    preset: str = "host_full"
) -> Dict[str, Any]:
    """
    Generate a host script from database rundown items.

    Args:
        episode_number: Episode number (e.g., "0249")
        output_dir: Optional output directory. Defaults to episode's scripts/current/ folder.
        preset: Script preset - "host_full", "host_clean", or "production"

    Returns:
        Dict with success status, output path, and metadata
    """
    db = SessionLocal()

    try:
        # Validate preset
        try:
            script_preset = ScriptPreset(preset.lower())
        except ValueError:
            script_preset = ScriptPreset.HOST_FULL

        # Find episode
        episode = db.query(Episode).filter(
            Episode.episode_number == int(episode_number)
        ).first()

        if not episode:
            return {"success": False, "error": f"Episode {episode_number} not found"}

        # Get rundown
        rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
        if not rundown:
            return {"success": False, "error": f"No rundown found for episode {episode_number}"}

        # Get all rundown items ordered by position
        items = db.query(RundownItem).filter(
            RundownItem.rundown_id == rundown.id
        ).order_by(RundownItem.order_in_rundown).all()

        if not items:
            return {"success": False, "error": f"No rundown items found for episode {episode_number}"}

        # Get episode metadata (pass items for runtime calculation)
        episode_info = _get_episode_info(episode, db, items)

        # Determine output path
        ep_num_padded = episode_number.zfill(4)
        if output_dir:
            output_path = Path(output_dir)
        else:
            container_path = Path(f"/home/episodes/{ep_num_padded}/scripts/current")
            host_path = Path(f"/mnt/sync/disaffected/episodes/{ep_num_padded}/scripts/current")
            output_path = container_path if container_path.parent.parent.exists() else host_path

        output_path.mkdir(parents=True, exist_ok=True)

        # Create resources folder
        resources_path = output_path / "resources"
        resources_path.mkdir(parents=True, exist_ok=True)

        # Collect media resources
        url_mapping = _collect_media_resources(items, resources_path, ep_num_padded)

        # Build transcription cache from SOTProcessingJob records
        transcription_cache = _build_transcription_cache(items, db)

        # Detect blocks
        blocks = _detect_blocks(items)

        # Load settings (for FSQ quote rendering flags, etc.)
        try:
            from routers.settings._shared import load_settings
            settings = load_settings()
        except Exception as e:
            logger.warning(f"Failed to load settings, using defaults: {e}")
            settings = {}

        # Generate HTML
        html_content = _generate_html(episode_info, blocks, script_preset, url_mapping, transcription_cache, settings)

        # Generate filenames with revision numbers
        date_str = datetime.now().strftime("%Y%m%d")
        preset_suffix = script_preset.value.upper().replace("_", "-")

        # Determine next revision number
        revision = _get_next_revision(output_path, ep_num_padded, preset_suffix, date_str)
        revision_suffix = f"-r{revision}" if revision > 1 else ""

        html_filename = f"{ep_num_padded}-{preset_suffix}-{date_str}{revision_suffix}.html"
        pdf_filename = f"{ep_num_padded}-{preset_suffix}-{date_str}{revision_suffix}.pdf"
        md_filename = f"{ep_num_padded}-{preset_suffix}-{date_str}{revision_suffix}.md"
        html_path = output_path / html_filename
        pdf_path = output_path / pdf_filename
        md_path = output_path / md_filename

        logger.info(f"Generating script revision {revision}: {pdf_filename}")

        # Write HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Generated {preset} script HTML: {html_path}")

        # Generate Markdown
        md_content = _generate_markdown(episode_info, blocks, script_preset, url_mapping, transcription_cache)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"Generated {preset} script Markdown: {md_path}")

        # Convert to PDF
        pdf_generated = _convert_to_pdf(html_path, pdf_path, episode_info)

        return {
            "success": True,
            "html_path": str(html_path),
            "pdf_path": str(pdf_path) if pdf_generated else None,
            "md_path": str(md_path),
            "output_path": str(pdf_path) if pdf_generated else str(html_path),
            "episode_number": episode_number,
            "preset": script_preset.value,
            "item_count": len(items),
            "block_count": len(blocks),
            "revision": revision
        }

    except Exception as e:
        logger.error(f"Error generating script for episode {episode_number}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def _get_next_revision(output_path: Path, episode: str, preset: str, date_str: str) -> int:
    """
    Determine the next revision number for a script file.

    Checks for existing files matching the pattern and returns the next revision.
    First generation of the day has no suffix, subsequent ones get -r2, -r3, etc.

    Args:
        output_path: Directory where scripts are saved
        episode: Episode number (e.g., "0257")
        preset: Preset suffix (e.g., "HOST-FULL")
        date_str: Date string (e.g., "20260118")

    Returns:
        Next revision number (1 for first, 2 for second, etc.)
    """
    # Pattern matches: 0257-HOST-FULL-20260118.pdf, 0257-HOST-FULL-20260118-r2.pdf, etc.
    base_pattern = f"{episode}-{preset}-{date_str}"

    existing_revisions = []

    for file in output_path.glob(f"{base_pattern}*.pdf"):
        filename = file.stem  # Remove .pdf extension

        if filename == base_pattern:
            # First revision (no suffix)
            existing_revisions.append(1)
        elif filename.startswith(base_pattern + "-r"):
            # Extract revision number
            rev_part = filename[len(base_pattern) + 2:]  # Skip "-r"
            try:
                rev_num = int(rev_part)
                existing_revisions.append(rev_num)
            except ValueError:
                pass

    if not existing_revisions:
        return 1  # First generation of the day

    return max(existing_revisions) + 1


def _get_episode_info(episode: Episode, db, items: List[RundownItem] = None) -> Dict[str, Any]:
    """Extract episode information for cover page."""
    show_name = "DISAFFECTED"
    if episode.season_id:
        season = db.query(Season).filter(Season.id == episode.season_id).first()
        if season and season.show_id:
            show = db.query(Show).filter(Show.id == season.show_id).first()
            if show:
                show_name = show.name.upper()

    # Format air date
    date_str = ""
    if episode.air_date:
        date_str = episode.air_date.strftime("%B %d, %Y")
    elif episode.publish_date:
        date_str = episode.publish_date.strftime("%B %d, %Y")

    # Calculate total runtime from items if not set on episode
    duration = episode.duration_formatted or ""
    if not duration and items:
        duration = _calculate_total_runtime(items)

    return {
        "show_name": show_name,
        "episode_number": str(episode.episode_number).zfill(4),
        "title": episode.title or f"Episode {episode.episode_number}",
        "date_str": date_str,
        "guest_name": episode.guest_name or "",
        "guest_bio": getattr(episode, 'guest_bio', "") or "",
        "duration": duration,
    }


def _calculate_total_runtime(items: List[RundownItem]) -> str:
    """Calculate total runtime from rundown items."""
    total_seconds = 0
    for item in items:
        dur = item.duration or '00:00:00'
        # Parse duration (handle HH:MM:SS:FF format)
        parts = dur.replace('.', ':').split(':')
        if len(parts) >= 3:
            try:
                h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                total_seconds += h * 3600 + m * 60 + s
            except ValueError:
                pass

    if total_seconds == 0:
        return ""

    total_h = total_seconds // 3600
    total_m = (total_seconds % 3600) // 60
    total_s = total_seconds % 60
    return f"{total_h:02d}:{total_m:02d}:{total_s:02d}"


def _detect_blocks(items: List[RundownItem]) -> List[Dict[str, Any]]:
    """
    Detect content blocks based on BREAK items.

    Block structure:
    - BLOCK A: All content from start until first BREAK
    - BLOCK B: Content after BREAK 1 until BREAK 2
    - BLOCK C: Content after BREAK 2 until BREAK 3
    - etc.

    NOTE: Only 'break' type items separate blocks. 'ad' and 'advertisement'
    items are treated as content and rendered inline with their specific slug.

    Returns list of blocks with:
    - letter: Block letter (A, B, C...)
    - items: List of content RundownItems (excludes breaks)
    - break_after: The break item that follows this block (if any)
    """
    blocks = []
    current_items = []
    block_index = 0

    for item in items:
        item_type = (item.item_type or 'segment').lower()
        is_break = item_type in BREAK_ITEM_TYPES

        if is_break:
            # End current block
            if current_items:
                letter = chr(ord('A') + block_index)
                blocks.append({
                    'letter': letter,
                    'items': current_items,
                    'break_after': item  # The break that ends this block
                })
                current_items = []
                block_index += 1
        else:
            # Content item (including ads) - add to current block
            current_items.append(item)

    # Final block (after last break, or only block if no breaks)
    if current_items:
        letter = chr(ord('A') + block_index)
        blocks.append({
            'letter': letter,
            'items': current_items,
            'break_after': None
        })

    return blocks


def _collect_media_resources(
    items: List[RundownItem],
    resources_path: Path,
    episode_number: str
) -> Dict[str, str]:
    """
    Collect and copy media files from cue blocks.

    Returns mapping of original URL -> local relative path.
    """
    url_mapping = {}
    cue_counter = 0

    # Base paths for media files
    container_base = Path("/home/episodes")
    host_base = Path("/mnt/sync/disaffected/episodes")

    # Pattern to find cue blocks
    cue_pattern = re.compile(r'<!-- Begin Cue -->(.*?)<!-- End Cue -->', re.DOTALL | re.IGNORECASE)

    # Patterns for media URLs - handle both "Media Url" (with space) and "MediaUrl" (no space)
    media_patterns = [
        re.compile(r'\[Media\s*[Uu]rl:\s*([^\]]+)\]', re.IGNORECASE),
        re.compile(r'\[MediaURL:\s*([^\]]+)\]', re.IGNORECASE),
        re.compile(r'\[Thumbnail\s*[Uu]rl:\s*([^\]]+)\]', re.IGNORECASE),
        re.compile(r'\[ThumbnailURL:\s*([^\]]+)\]', re.IGNORECASE),
        re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE),
    ]

    for item in items:
        if not item.script_content:
            continue

        for cue_match in cue_pattern.finditer(item.script_content):
            cue_content = cue_match.group(1)
            cue_counter += 10

            # Extract slug for filename
            slug = _extract_field(cue_content, 'Slug') or 'media'

            for pattern in media_patterns:
                for match in pattern.finditer(cue_content):
                    original_url = match.group(1).strip()

                    if not original_url or original_url in url_mapping:
                        continue

                    # Skip blob and http URLs
                    if original_url.startswith(('http://', 'https://', 'blob:')):
                        continue

                    # Find and copy the file
                    source_path = _find_media_file(original_url, episode_number, container_base, host_base)

                    if source_path and source_path.exists():
                        dest_filename = source_path.name
                        dest_path = resources_path / dest_filename
                        try:
                            if not dest_path.exists():
                                shutil.copy2(source_path, dest_path)
                            url_mapping[original_url] = f"resources/{dest_filename}"
                        except Exception as e:
                            logger.warning(f"Failed to copy {source_path}: {e}")

    return url_mapping


def _find_media_file(
    url: str,
    episode_number: str,
    container_base: Path,
    host_base: Path
) -> Optional[Path]:
    """Find a media file from a URL."""
    url = url.strip()

    # Handle /episodes/... paths
    if url.startswith('/episodes/'):
        url = url[1:]

    # Absolute path
    if url.startswith('/'):
        path = Path(url)
        if path.exists():
            return path
        return None

    # Relative path starting with episodes/
    if url.startswith('episodes/'):
        for base in [container_base.parent, host_base.parent]:
            path = base / url
            if path.exists():
                return path

    # Relative path with assets/
    if url.startswith(('../assets/', 'assets/')):
        clean_url = url.replace('../', '')
        for base in [container_base, host_base]:
            path = base / episode_number / clean_url
            if path.exists():
                return path

    # Just a filename - search common locations
    filename = Path(url).name
    search_dirs = ['assets/images', 'assets/video', 'assets/graphics', 'assets/quotes', 'assets/thumbnails']

    for base in [container_base, host_base]:
        for subdir in search_dirs:
            candidate = base / episode_number / subdir / filename
            if candidate.exists():
                return candidate

    return None


def _build_transcription_cache(items: List[RundownItem], db) -> Dict[str, str]:
    """
    Build a cache of transcriptions from SOTProcessingJob records.

    Returns mapping of AssetID -> transcription text.
    """
    cache = {}

    # Extract all Asset IDs from SOT cues
    asset_ids = set()
    for item in items:
        if not item.script_content:
            continue
        # Find all SOT cues and extract Asset IDs
        for cue in re.findall(r'<!-- Begin Cue -->(.*?)<!-- End Cue -->', item.script_content, re.DOTALL):
            if '[Type: SOT]' in cue:
                asset_id = _extract_field(cue, r'Asset\s*Id')
                if asset_id:
                    asset_ids.add(asset_id)

    if not asset_ids:
        return cache

    # Query SOTProcessingJob for transcriptions
    try:
        jobs = db.query(SOTProcessingJob).filter(
            SOTProcessingJob.asset_id.in_(asset_ids)
        ).all()

        for job in jobs:
            if job.transcription:
                cache[job.asset_id] = job.transcription
                logger.debug(f"Found transcription for {job.asset_id}: {job.transcription[:50]}...")
    except Exception as e:
        logger.warning(f"Failed to fetch transcriptions: {e}")

    return cache


def _generate_html(
    episode_info: Dict[str, Any],
    blocks: List[Dict[str, Any]],
    preset: ScriptPreset,
    url_mapping: Dict[str, str],
    transcription_cache: Dict[str, str] = None,
    settings: Dict[str, Any] = None
) -> str:
    """Generate the complete HTML document."""
    if transcription_cache is None:
        transcription_cache = {}
    if settings is None:
        settings = {}

    # Get CSS for the preset
    css = _get_css(preset, episode_info['episode_number'])

    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        f'<title>{episode_info["show_name"]} - Episode {episode_info["episode_number"]}</title>',
        '<style>',
        css,
        '</style>',
        '</head>',
        '<body>',
    ]

    # Cover page
    html_parts.append(_generate_cover_page(episode_info, blocks, preset))

    # Content blocks
    for block in blocks:
        html_parts.append(_generate_block(block, preset, url_mapping, transcription_cache, settings))

    html_parts.extend(['</body>', '</html>'])

    return '\n'.join(html_parts)


def _generate_markdown(
    episode_info: Dict[str, Any],
    blocks: List[Dict[str, Any]],
    preset: ScriptPreset,
    url_mapping: Dict[str, str],
    transcription_cache: Dict[str, str] = None
) -> str:
    """Generate clean markdown document from script data."""
    if transcription_cache is None:
        transcription_cache = {}

    md_parts = []

    # Title/Cover section
    md_parts.append(f"# {episode_info['show_name']}")
    md_parts.append(f"## Episode {episode_info['episode_number']}")
    md_parts.append("")

    if episode_info.get('title'):
        md_parts.append(f"### {episode_info['title']}")
        md_parts.append("")

    # Metadata table
    md_parts.append("| Field | Value |")
    md_parts.append("|-------|-------|")
    if episode_info.get('episode_date'):
        md_parts.append(f"| Date | {episode_info['episode_date']} |")
    if episode_info.get('guests'):
        md_parts.append(f"| Guests | {episode_info['guests']} |")
    if episode_info.get('total_runtime'):
        md_parts.append(f"| Runtime | {episode_info['total_runtime']} |")
    md_parts.append(f"| Blocks | {len(blocks)} |")
    md_parts.append("")

    # Block summary
    md_parts.append("### Block Summary")
    md_parts.append("")
    for block in blocks:
        item_count = len(block.get('items', []))
        md_parts.append(f"- **Block {block['letter']}**: {item_count} segment(s)")
    md_parts.append("")
    md_parts.append("---")
    md_parts.append("")

    # Content blocks
    for block in blocks:
        md_parts.append(_generate_markdown_block(block, preset, url_mapping, transcription_cache))

    return '\n'.join(md_parts)


def _generate_markdown_block(
    block: Dict[str, Any],
    preset: ScriptPreset,
    url_mapping: Dict[str, str],
    transcription_cache: Dict[str, str] = None
) -> str:
    """Generate markdown for a single block."""
    if transcription_cache is None:
        transcription_cache = {}

    parts = []
    letter = block['letter']

    # Block header
    parts.append(f"## ★ BLOCK {letter} ★")
    parts.append("")

    # Process each segment
    for item in block['items']:
        segment_md = _process_segment_markdown(item, preset, url_mapping, transcription_cache)
        if segment_md:
            parts.append(segment_md)

    # Block end
    parts.append(f"— END BLOCK {letter} —")
    parts.append("")

    # Break indicator
    if block.get('break_after'):
        break_item = block['break_after']
        item_type = (break_item.item_type or 'break').lower()
        is_ad = item_type in ('ad', 'advertisement')

        if is_ad:
            ad_slug = break_item.slug or break_item.title or 'Advertisement'
            if ad_slug.lower() in ('advertisement', 'ad', 'untitled'):
                ad_slug = break_item.slug or 'Advertisement'
            ad_duration = break_item.duration or ''
            dur_str = f" `{ad_duration}`" if ad_duration else ''
            parts.append(f"### ▶ AD: {ad_slug.upper()} ◀{dur_str}")
        else:
            break_title = break_item.title
            if not break_title or break_title.lower() in ('untitled', 'break'):
                break_title = "COMMERCIAL BREAK"
            parts.append(f"### ▶ {break_title.upper()} ◀")
        parts.append("")

    parts.append("---")
    parts.append("")

    return '\n'.join(parts)


def _process_segment_markdown(
    item,
    preset: ScriptPreset,
    url_mapping: Dict[str, str],
    transcription_cache: Dict[str, str] = None
) -> str:
    """Process a single rundown item to markdown."""
    if transcription_cache is None:
        transcription_cache = {}

    # Check if item has content
    if not item.script_content or not item.script_content.strip():
        return ''

    # Remove frontmatter and check for actual content
    content = item.script_content
    content_check = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
    content_check = re.sub(r'<!--.*?-->', '', content_check, flags=re.DOTALL)
    content_check = re.sub(r'<p[^>]*>\s*</p>', '', content_check)

    if not content_check.strip():
        return ''

    parts = []

    # Segment header
    title = item.title
    if not title or title.lower() == 'untitled':
        title = item.slug or "Segment"
    duration = item.duration or ""

    if duration:
        parts.append(f"### {title} `[{duration}]`")
    else:
        parts.append(f"### {title}")
    parts.append("")

    # Process content
    content_md = _process_content_markdown(content, preset, url_mapping, transcription_cache)
    if content_md.strip():
        parts.append(content_md)
        parts.append("")

    return '\n'.join(parts)


def _process_content_markdown(
    content: str,
    preset: ScriptPreset,
    url_mapping: Dict[str, str],
    transcription_cache: Dict[str, str] = None
) -> str:
    """Process script content to markdown with cue blocks and paragraphs."""
    if transcription_cache is None:
        transcription_cache = {}

    parts = []

    # Pattern for cue blocks
    cue_pattern = re.compile(r'<!-- Begin Cue -->(.*?)<!-- End Cue -->', re.DOTALL | re.IGNORECASE)

    # Split by cue blocks and process
    last_end = 0
    for match in cue_pattern.finditer(content):
        # Text before cue
        text_before = content[last_end:match.start()]
        if text_before.strip():
            text_md = _process_text_markdown(text_before, preset)
            parts.append(text_md)

        # Cue block
        cue_md = _process_cue_markdown(match.group(1), preset, url_mapping, transcription_cache)
        if cue_md:
            parts.append(cue_md)

        last_end = match.end()

    # Text after last cue
    text_after = content[last_end:]
    if text_after.strip():
        text_md = _process_text_markdown(text_after, preset)
        parts.append(text_md)

    return '\n'.join(parts)


def _process_text_markdown(text: str, preset: ScriptPreset) -> str:
    """Process text content to markdown paragraphs."""
    parts = []

    # Remove frontmatter
    text = re.sub(r'^---.*?---\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'^-\s*-\s*-.*?-\s*-\s*-\s*', '', text, flags=re.DOTALL)

    # Remove markdown headers (we add our own)
    text = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)

    # Parse paragraphs with speaker classes
    p_pattern = re.compile(r'<p\s+class=["\']([^"\']+)["\'][^>]*>(.*?)</p>', re.DOTALL | re.IGNORECASE)

    for match in p_pattern.finditer(text):
        speaker_class = match.group(1).strip().lower()
        paragraph_text = match.group(2).strip()

        if not paragraph_text:
            continue

        # Clean HTML entities and tags
        paragraph_text = html.unescape(paragraph_text)
        paragraph_text = re.sub(r'<[^>]+>', '', paragraph_text)

        # Get speaker name
        speaker_config = SPEAKER_CONFIG.get(speaker_class, {'name': speaker_class.upper()})
        speaker_name = speaker_config['name']

        # Format based on preset
        if preset == ScriptPreset.HOST_CLEAN:
            # Clean mode: just the text with speaker prefix on new paragraphs
            parts.append(f"**{speaker_name}:** {paragraph_text}")
            parts.append("")
        else:
            # Full/Production mode: speaker labeled paragraphs
            parts.append(f"**{speaker_name}:**")
            parts.append(f"> {paragraph_text}")
            parts.append("")

    return '\n'.join(parts)


def _process_cue_markdown(
    cue_content: str,
    preset: ScriptPreset,
    url_mapping: Dict[str, str],
    transcription_cache: Dict[str, str] = None
) -> str:
    """Process a cue block to markdown format."""
    if transcription_cache is None:
        transcription_cache = {}

    # Extract cue fields
    cue_type = (_extract_field(cue_content, 'Type') or 'CUE').upper()
    slug = _extract_field(cue_content, 'Slug')
    duration = _extract_field(cue_content, 'Duration')
    media_url = _extract_field(cue_content, r'Media\s*[Uu]rl')
    asset_id = _extract_field(cue_content, r'Asset\s*[Ii][Dd]')
    transcription = _extract_field(cue_content, 'Transcription')
    description = _extract_field(cue_content, 'Description')

    # Check transcription cache
    if not transcription and asset_id and asset_id in transcription_cache:
        transcription = transcription_cache[asset_id]

    # Skip certain cue types in clean mode
    if preset == ScriptPreset.HOST_CLEAN:
        # Only show media cues with transcription
        if cue_type in ['SOT', 'VO', 'NAT', 'PKG'] and transcription:
            parts = [f"**[{cue_type}]** _{slug}_"]
            if duration:
                parts[0] += f" `{duration}`"
            parts.append("")
            parts.append(f"> {transcription}")
            parts.append("")
            return '\n'.join(parts)
        elif cue_type in ['FSQ']:
            return f"**[{cue_type}]** _{slug}_ `{duration}`\n"
        else:
            return ''

    # Full/Production mode - show all cue details
    parts = []

    # Cue header
    header = f"**[{cue_type}]**"
    if slug:
        header += f" _{slug}_"
    if duration:
        header += f" `{duration}`"
    parts.append(header)

    # Details as a list
    if preset == ScriptPreset.PRODUCTION:
        if asset_id:
            parts.append(f"  - AssetID: `{asset_id}`")
        if media_url:
            parts.append(f"  - Media: `{media_url}`")

    # Transcription/Description
    if transcription:
        parts.append("")
        parts.append(f"> *\"{transcription}\"*")
    elif description:
        parts.append("")
        parts.append(f"> {description}")

    parts.append("")
    return '\n'.join(parts)


def _get_css(preset: ScriptPreset, episode_number: str) -> str:
    """Get CSS styles based on preset."""

    # Base font size varies by preset (+3pt from original)
    if preset == ScriptPreset.HOST_CLEAN:
        body_font = "23pt"  # Larger for teleprompter/easy reading
        line_height = "1.8"
    elif preset == ScriptPreset.PRODUCTION:
        body_font = "14pt"  # More readable
        line_height = "1.4"
    else:  # HOST_FULL
        body_font = "19pt"  # Main body text
        line_height = "1.6"

    return f"""
        @page {{
            size: letter;
            margin: 0.75in;
            @bottom-left {{
                content: "Episode {episode_number}";
                font-size: 9pt;
                color: #666;
            }}
            @bottom-right {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }}
        }}

        * {{ box-sizing: border-box; }}

        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: {body_font};
            line-height: {line_height};
            color: #111;
            margin: 0;
            padding: 0.5in;
            background: #fff;
        }}

        /* Cover Page */
        .cover-page {{
            text-align: center;
            page-break-after: always;
            padding-top: 1.5in;
        }}

        .show-title {{
            font-size: 42pt;
            font-weight: bold;
            letter-spacing: 0.15em;
            margin-bottom: 0.3in;
            color: #111;
        }}

        .episode-number {{
            font-size: 24pt;
            color: #444;
            margin-bottom: 0.15in;
        }}

        .episode-date {{
            font-size: 14pt;
            color: #666;
            margin-bottom: 0.4in;
        }}

        .episode-title {{
            font-size: 28pt;
            font-weight: 600;
            margin-bottom: 0.3in;
            color: #222;
        }}

        .guest-info {{
            font-size: 16pt;
            color: #444;
            font-style: italic;
            margin-bottom: 0.5in;
        }}

        .duration-info {{
            font-size: 14pt;
            color: #666;
            margin-top: 0.5in;
        }}

        .block-summary {{
            margin-top: 0.75in;
            text-align: left;
            padding: 0.3in;
            background: #f5f5f5;
            border-radius: 8px;
        }}

        .block-summary h3 {{
            margin: 0 0 0.15in 0;
            font-size: 14pt;
            color: #333;
        }}

        .block-summary ul {{
            margin: 0;
            padding-left: 1.2em;
            font-size: 12pt;
            color: #555;
        }}

        /* Block Headers - prominent delineators */
        .block-header {{
            text-align: center;
            font-size: 28pt;
            font-weight: bold;
            padding: 0.3in 0;
            margin: 0.6in 0 0.3in 0;
            border-top: 6px solid #1565c0;
            border-bottom: 6px solid #1565c0;
            background: #e3f2fd;
            color: #0d47a1;
            letter-spacing: 0.2em;
            page-break-before: always;
        }}

        .block-header.first {{
            page-break-before: auto;
        }}

        .block-end {{
            text-align: center;
            font-size: 20pt;
            font-weight: bold;
            padding: 0.25in 0;
            margin: 0.5in 0;
            border-top: 4px solid #1565c0;
            border-bottom: 4px solid #1565c0;
            background: #e8eaf6;
            color: #283593;
            letter-spacing: 0.15em;
        }}

        /* Segment Headers */
        .segment {{
            margin-bottom: 0.3in;
        }}

        .segment-header {{
            font-size: 18pt;
            font-weight: bold;
            color: #1565c0;
            margin: 0.3in 0 0.15in 0;
            padding-bottom: 0.1in;
            border-bottom: 2px solid #1565c0;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}

        .segment-duration {{
            font-size: 12pt;
            color: #888;
            font-weight: normal;
            float: right;
            text-transform: none;
        }}

        /* Tease / End Segment divider */
        .segment-end-divider {{
            text-align: center;
            font-size: 12pt;
            font-weight: bold;
            color: #888;
            margin: 0.2in 0 0.1in 0;
            padding: 0.05in 0;
            letter-spacing: 0.15em;
            border-top: 1px solid #ccc;
        }}

        .segment-tease .script-content {{
            font-style: italic;
            color: #555;
        }}

        /* Script Content */
        .script-content {{
            margin: 0.15in 0;
        }}

        .script-paragraph {{
            text-align: left;
            margin: 0.2in 0;
            text-indent: 0;
        }}

        /* Speaker Attribution */
        .speaker-tag {{
            font-weight: bold;
            font-size: 11pt;
            display: inline-block;
            padding: 3px 10px;
            border-radius: 4px;
            margin-right: 10px;
            margin-bottom: 5px;
        }}

        .speaker-josh, .speaker-host {{ background: #e3f2fd; color: #1565c0; }}
        .speaker-guest {{ background: #e8f5e9; color: #2e7d32; }}
        .speaker-caller {{ background: #fff3e0; color: #ef6c00; }}
        .speaker-announcer {{ background: #f3e5f5; color: #7b1fa2; }}
        .speaker-narrator {{ background: #efebe9; color: #5d4037; }}

        /* Cue Blocks - Full preset */
        .cue-block {{
            margin: 0.25in 0;
            padding: 0.2in;
            border-radius: 6px;
            page-break-inside: avoid;
        }}

        .cue-label {{
            font-size: 19pt;
            font-weight: bold;
            margin-bottom: 0.1in;
        }}

        /* FSQ */
        .cue-fsq {{
            background: #fafafa;
            border-left: 5px solid #9e9e9e;
            border-right: 5px solid #9e9e9e;
        }}

        .cue-fsq .cue-label {{ color: #666; }}

        .cue-fsq blockquote {{
            font-size: 19pt;
            font-style: italic;
            color: #333;
            margin: 0.1in 0;
            line-height: 1.5;
        }}

        .cue-fsq .attribution {{
            text-align: right;
            font-size: 17pt;
            color: #555;
            margin-top: 0.1in;
        }}

        /* SOT */
        .cue-sot {{
            background: #fff8e1;
            border: 2px solid #ffc107;
        }}

        .cue-sot .cue-label {{ color: #f57c00; }}

        .sot-content {{
            display: flex;
            align-items: flex-start;
            gap: 0.2in;
            justify-content: space-between;
        }}

        .sot-thumbnail {{
            max-width: 280px;
            max-height: 280px;
            width: auto;
            height: auto;
            object-fit: contain;
            border: 1px solid #ddd;
            border-radius: 4px;
            order: 2;
            flex-shrink: 0;
            margin-left: auto;
        }}

        .sot-info {{ flex: 1; order: 1; }}
        .sot-slug {{ font-weight: bold; font-size: 19pt; }}
        .sot-duration {{ font-size: 17pt; color: #666; }}
        .sot-outcue {{ font-size: 19pt; color: #d84315; font-weight: bold; margin-top: 0.05in; }}
        .sot-transcription {{ font-size: 17pt; color: #444; font-style: italic; margin-top: 0.1in; }}

        /* IMG/GFX */
        .cue-img, .cue-gfx {{
            background: #f5f5f5;
            border: 1px solid #ddd;
            text-align: center;
        }}

        .cue-img .cue-label, .cue-gfx .cue-label {{ color: #666; }}

        .cue-img img, .cue-gfx img {{
            max-width: 100%;
            width: 100%;
            border: 1px solid #ccc;
            border-radius: 4px;
        }}

        .img-caption {{
            font-size: 17pt;
            color: #666;
            margin-top: 0.1in;
            font-style: italic;
        }}

        /* Cue markers for RIF, VOX, etc. */
        .cue-marker {{
            display: inline-block;
            background: #eee;
            color: #666;
            padding: 6px 14px;
            border-radius: 4px;
            font-size: 19pt;
            font-weight: bold;
            margin: 0.15in 0;
        }}

        /* Inline production note - compact monospace */
        .inline-note {{
            font-family: 'Courier New', Courier, monospace;
            font-size: 85%;
            color: #555;
            margin: 2em 0;
            line-height: 1.4;
        }}

        /* Production preset - compact tables */
        .production-cue {{
            background: #f9f9f9;
            border: 1px solid #ddd;
            padding: 0.1in;
            margin: 0.1in 0;
            font-size: 10pt;
        }}

        .production-cue .cue-type {{
            font-weight: bold;
            color: #333;
        }}

        /* Break indicator - prominent */
        .break-indicator {{
            text-align: center;
            padding: 0.25in;
            margin: 0.4in 0;
            background: #fff3e0;
            border: 4px dashed #ff9800;
            color: #e65100;
            font-weight: bold;
            font-size: 20pt;
            letter-spacing: 0.1em;
        }}

        /* Ad break - prominent blue styling */
        .break-indicator.ad-break {{
            background: #e3f2fd;
            border: 4px dashed #1976d2;
            color: #0d47a1;
        }}

        .ad-label {{
            font-weight: bold;
            font-size: 14pt;
            background: #1976d2;
            color: #fff;
            padding: 4px 14px;
            border-radius: 4px;
            margin-right: 12px;
        }}

        .ad-slug {{
            font-weight: bold;
            font-size: 22pt;
            color: #0d47a1;
        }}

        .ad-duration {{
            font-size: 13pt;
            color: #42a5f5;
            margin-left: 12px;
        }}

        @media print {{
            body {{ padding: 0; }}
            .block-header {{ page-break-before: always; }}
            .block-header.first {{ page-break-before: avoid; }}
        }}
    """


def _generate_cover_page(
    episode_info: Dict[str, Any],
    blocks: List[Dict[str, Any]],
    preset: ScriptPreset
) -> str:
    """Generate the cover page."""

    parts = [
        '<div class="cover-page">',
        f'<div class="show-title">{html.escape(episode_info["show_name"])}</div>',
        f'<div class="episode-number">EPISODE {html.escape(episode_info["episode_number"])}</div>',
    ]

    if episode_info["date_str"]:
        parts.append(f'<div class="episode-date">{html.escape(episode_info["date_str"])}</div>')

    parts.append(f'<div class="episode-title">{html.escape(episode_info["title"])}</div>')

    if episode_info["guest_name"]:
        guest_text = f'Guest: {episode_info["guest_name"]}'
        if episode_info.get("guest_bio"):
            guest_text += f'<br><small>{episode_info["guest_bio"][:150]}</small>'
        parts.append(f'<div class="guest-info">{guest_text}</div>')

    if episode_info["duration"]:
        parts.append(f'<div class="duration-info">Total Runtime: {html.escape(episode_info["duration"])}</div>')

    # Block summary
    if len(blocks) > 1:
        parts.append('<div class="block-summary">')
        parts.append('<h3>SHOW STRUCTURE</h3>')
        parts.append('<ul>')
        for block in blocks:
            item_count = len(block['items'])
            first_title = block['items'][0].title if block['items'] else "Content"
            parts.append(f'<li><strong>BLOCK {block["letter"]}</strong>: {item_count} segment(s) — starts with "{html.escape(first_title or "Segment")}"</li>')
        parts.append('</ul>')
        parts.append('</div>')

    parts.append('</div>')

    return '\n'.join(parts)


def _generate_block(
    block: Dict[str, Any],
    preset: ScriptPreset,
    url_mapping: Dict[str, str],
    transcription_cache: Dict[str, str] = None,
    settings: Dict[str, Any] = None
) -> str:
    """Generate HTML for a single block."""
    if transcription_cache is None:
        transcription_cache = {}
    if settings is None:
        settings = {}

    parts = []
    letter = block['letter']
    is_first = letter == 'A'

    # Block start header
    header_class = "block-header first" if is_first else "block-header"
    parts.append(f'<div class="{header_class}">★ ★ ★  BLOCK {letter}  ★ ★ ★</div>')

    # Process each segment in the block
    last_speaker = None
    for item in block['items']:
        segment_html, last_speaker = _process_segment(item, last_speaker, preset, url_mapping, transcription_cache, settings)
        if segment_html:
            parts.append(segment_html)

    # Block end header
    parts.append(f'<div class="block-end">— — —  END BLOCK {letter}  — — —</div>')

    # Break indicator (if there's a break after this block)
    if block.get('break_after'):
        break_item = block['break_after']
        item_type = (break_item.item_type or 'break').lower()
        is_ad = item_type in ('ad', 'advertisement')

        if is_ad:
            # Ad break - show the specific ad slug prominently
            ad_slug = break_item.slug or break_item.title or 'Advertisement'
            # Don't show generic titles like "Advertisement" or "Ad" - use slug instead
            if ad_slug.lower() in ('advertisement', 'ad', 'untitled'):
                ad_slug = break_item.slug or 'Advertisement'
            ad_duration = break_item.duration or ''
            parts.append('<div class="break-indicator ad-break">')
            parts.append(f'<span class="ad-label">AD</span> ')
            parts.append(f'<span class="ad-slug">{html.escape(ad_slug.upper())}</span>')
            if ad_duration:
                parts.append(f' <span class="ad-duration">[{html.escape(ad_duration)}]</span>')
            parts.append('</div>')
        else:
            # Generic break
            break_title = break_item.title
            if not break_title or break_title.lower() in ('untitled', 'break'):
                break_title = "COMMERCIAL BREAK"
            parts.append(f'<div class="break-indicator">▶ {html.escape(break_title.upper())} ◀</div>')

    return '\n'.join(parts)


def _process_segment(
    item: RundownItem,
    last_speaker: Optional[str],
    preset: ScriptPreset,
    url_mapping: Dict[str, str],
    transcription_cache: Dict[str, str] = None,
    settings: Dict[str, Any] = None
) -> Tuple[str, Optional[str]]:
    """Process a single rundown item (segment)."""
    if transcription_cache is None:
        transcription_cache = {}
    if settings is None:
        settings = {}

    # Check if item has content
    if not item.script_content or not item.script_content.strip():
        return '', last_speaker

    # Remove frontmatter and check for actual content
    content = item.script_content
    content_check = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
    content_check = re.sub(r'<!--.*?-->', '', content_check, flags=re.DOTALL)
    content_check = re.sub(r'<p[^>]*>\s*</p>', '', content_check)

    if not content_check.strip():
        return '', last_speaker

    item_type = (item.item_type or 'segment').lower()

    # Tease items render as subtle end-of-segment dividers, not full segment headers
    if item_type == 'tease':
        parts = ['<div class="segment segment-tease">']
        parts.append('<div class="segment-end-divider">— END SEGMENT —</div>')
    else:
        parts = ['<div class="segment">']

        # Segment header - use slug as fallback for empty or "Untitled" titles
        title = item.title
        if not title or title.lower() == 'untitled':
            title = item.slug or "Segment"
        duration = item.duration or ""

        parts.append(f'<div class="segment-header">{html.escape(title)}')
        if duration:
            parts.append(f'<span class="segment-duration">{html.escape(duration)}</span>')
        parts.append('</div>')

    # Process content based on preset
    content_html, last_speaker = _process_content(content, last_speaker, preset, url_mapping, transcription_cache, settings)

    if content_html.strip():
        parts.append('<div class="script-content">')
        parts.append(content_html)
        parts.append('</div>')

    parts.append('</div>')

    return '\n'.join(parts), last_speaker


def _process_content(
    content: str,
    last_speaker: Optional[str],
    preset: ScriptPreset,
    url_mapping: Dict[str, str],
    transcription_cache: Dict[str, str] = None,
    settings: Dict[str, Any] = None
) -> Tuple[str, Optional[str]]:
    """Process script content with cue blocks and paragraphs."""
    if transcription_cache is None:
        transcription_cache = {}
    if settings is None:
        settings = {}

    parts = []
    current_speaker = last_speaker

    # Pattern for cue blocks
    cue_pattern = re.compile(r'<!-- Begin Cue -->(.*?)<!-- End Cue -->', re.DOTALL | re.IGNORECASE)

    # Split by cue blocks and process
    last_end = 0
    for match in cue_pattern.finditer(content):
        # Text before cue
        text_before = content[last_end:match.start()]
        if text_before.strip():
            text_html, current_speaker = _process_text(text_before, current_speaker, preset)
            parts.append(text_html)

        # Cue block
        cue_html = _process_cue(match.group(1), preset, url_mapping, transcription_cache, settings)
        if cue_html:
            parts.append(cue_html)

        last_end = match.end()

    # Text after last cue
    text_after = content[last_end:]
    if text_after.strip():
        text_html, current_speaker = _process_text(text_after, current_speaker, preset)
        parts.append(text_html)

    return '\n'.join(parts), current_speaker


def _process_text(
    text: str,
    last_speaker: Optional[str],
    preset: ScriptPreset
) -> Tuple[str, Optional[str]]:
    """Process text content (paragraphs with speaker classes)."""

    parts = []
    current_speaker = last_speaker

    # Remove frontmatter
    text = re.sub(r'^---.*?---\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'^-\s*-\s*-.*?-\s*-\s*-\s*', '', text, flags=re.DOTALL)

    # Remove markdown headers
    text = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)

    # Fix double-nested paragraphs
    text = re.sub(r'<p([^>]*)>\s*<p[^>]*>', r'<p\1>', text, flags=re.IGNORECASE)

    # Pattern for paragraphs
    para_pattern = re.compile(r'<p(?:\s+class="([^"]*)")?[^>]*>(.*?)</p>', re.DOTALL | re.IGNORECASE)

    for match in para_pattern.finditer(text):
        speaker_class = match.group(1) or 'josh'
        content = match.group(2).strip()

        if not content:
            continue

        # Clean content - remove unwanted HTML tags
        # Strip ALL div tags (both empty and with content)
        content = re.sub(r'<div[^>]*>', '', content)  # Remove opening div tags
        content = re.sub(r'</div>', '', content)  # Remove closing div tags
        content = re.sub(r'<span[^>]*>', '', content)  # Remove opening span tags
        content = re.sub(r'</span>', '', content)  # Remove closing span tags
        content = re.sub(r'<br\s*/?>', ' ', content)
        # Also remove HTML-escaped versions of div/span tags
        content = re.sub(r'&lt;div[^&]*?&gt;', '', content, flags=re.IGNORECASE)
        content = re.sub(r'&lt;/div&gt;', '', content, flags=re.IGNORECASE)
        content = re.sub(r'&lt;span[^&]*?&gt;', '', content, flags=re.IGNORECASE)
        content = re.sub(r'&lt;/span&gt;', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\s+', ' ', content)

        # Check if speaker changed
        show_speaker = (speaker_class != current_speaker)
        current_speaker = speaker_class

        speaker_info = SPEAKER_CONFIG.get(speaker_class, {'name': speaker_class.upper()})

        parts.append('<p class="script-paragraph">')

        if show_speaker:
            parts.append(
                f'<span class="speaker-tag speaker-{html.escape(speaker_class)}">'
                f'{html.escape(speaker_info["name"])}</span>'
            )

        # Preserve safe inline formatting tags (bold, italic, underline, strikethrough)
        escaped = html.escape(content)
        # Restore whitelisted tags that were escaped
        for tag in ('b', 'i', 'u', 's', 'em', 'strong', 'mark', 'sub', 'sup'):
            escaped = escaped.replace(f'&lt;{tag}&gt;', f'<{tag}>')
            escaped = escaped.replace(f'&lt;/{tag}&gt;', f'</{tag}>')
            escaped = escaped.replace(f'&lt;{tag.upper()}&gt;', f'<{tag}>')
            escaped = escaped.replace(f'&lt;/{tag.upper()}&gt;', f'</{tag}>')
        parts.append(escaped)
        parts.append('</p>')

    return '\n'.join(parts), current_speaker


def _process_cue(
    cue_content: str,
    preset: ScriptPreset,
    url_mapping: Dict[str, str],
    transcription_cache: Dict[str, str] = None,
    settings: Dict[str, Any] = None
) -> str:
    """Process a cue block based on preset."""
    if transcription_cache is None:
        transcription_cache = {}
    if settings is None:
        settings = {}

    # Extract cue type
    cue_type = _extract_field(cue_content, 'Type').upper()
    if not cue_type:
        return ''

    # Extract slug
    slug = _extract_field(cue_content, 'Slug') or 'cue'

    # HOST_CLEAN: Just show a simple marker
    if preset == ScriptPreset.HOST_CLEAN:
        return f'<div class="cue-marker">[{cue_type}: {html.escape(slug)}]</div>'

    # PRODUCTION: Compact technical view
    if preset == ScriptPreset.PRODUCTION:
        return _format_production_cue(cue_content, cue_type, slug, url_mapping)

    # HOST_FULL: Full visual rendering
    if cue_type == 'FSQ':
        return _format_fsq(cue_content, slug, url_mapping, settings)
    elif cue_type == 'SOT':
        return _format_sot(cue_content, slug, url_mapping, transcription_cache)
    elif cue_type in ('IMG', 'GFX'):
        return _format_img(cue_content, slug, cue_type, url_mapping)
    elif cue_type == 'NOTE':
        return _format_note(cue_content)
    else:
        return f'<div class="cue-marker">[{cue_type}: {html.escape(slug)}]</div>'


def _format_note(cue_content: str) -> str:
    """Format NOTE cue as inline production note for iPad script view."""
    note_for = _extract_field(cue_content, 'Note For').upper()
    note_text = _extract_field(cue_content, 'Note Text')

    if not note_text:
        return ''

    label = f'{note_for}:NOTE' if note_for else 'NOTE'
    return f'<div class="inline-note">[[{html.escape(label)}--{html.escape(note_text)}]]</div>'


def _format_fsq(cue_content: str, slug: str, url_mapping: Dict[str, str], settings: Dict[str, Any] = None) -> str:
    """Format Full Screen Quote cue."""
    settings = settings or {}
    regenerate_exterior_quotes = bool(
        settings.get('generation', {}).get('fsq_regenerate_exterior_quotes', False)
    )

    quote = _extract_field(cue_content, 'Quote').strip('"\'')
    attribution = _extract_field(cue_content, 'Attribution')

    original_url = _extract_field(cue_content, r'Media\s*[Uu]rl')
    media_url = url_mapping.get(original_url, '') if original_url else ''

    parts = [
        '<div class="cue-block cue-fsq">',
        f'<div class="cue-label">FSQ: {html.escape(slug)}</div>',
    ]

    # FSQ already outputs the actual quote text — skip the generated PNG image.
    # Only wrap in exterior quotation marks when the "Regenerate exterior quotes
    # at render" setting is on; otherwise emit the stored quote text as-is.
    escaped_quote = html.escape(quote)
    if regenerate_exterior_quotes:
        parts.append(f'<blockquote>"{escaped_quote}"</blockquote>')
    else:
        parts.append(f'<blockquote>{escaped_quote}</blockquote>')

    if attribution:
        parts.append(f'<div class="attribution">— {html.escape(attribution)}</div>')

    parts.append('</div>')

    return '\n'.join(parts)


def _format_sot(cue_content: str, slug: str, url_mapping: Dict[str, str], transcription_cache: Dict[str, str] = None) -> str:
    """Format Sound On Tape cue."""
    if transcription_cache is None:
        transcription_cache = {}

    duration = _extract_field(cue_content, 'Duration')

    original_thumb = _extract_field(cue_content, r'Thumbnail\s*[Uu]rl') or _extract_field(cue_content, 'ThumbnailURL')
    thumbnail_url = ''
    if original_thumb:
        # Use local copy if available, otherwise use original URL (wkhtmltopdf can fetch HTTP)
        thumbnail_url = url_mapping.get(original_thumb, original_thumb)
        # Skip blob URLs as they won't work
        if thumbnail_url.startswith('blob:'):
            thumbnail_url = ''

    # Get transcription - first check cue block, then transcription cache by Asset ID
    transcription = _extract_field(cue_content, 'Transcription')

    if not transcription:
        # Look up by Asset ID in transcription cache
        asset_id = _extract_field(cue_content, r'Asset\s*Id')
        if asset_id:
            transcription = transcription_cache.get(asset_id, '')

    # Calculate outcue from last 5 words of transcription
    outcue = ''
    if transcription:
        words = transcription.split()
        if len(words) >= 5:
            outcue = ' '.join(words[-5:])
        elif words:
            outcue = ' '.join(words)

    parts = [
        '<div class="cue-block cue-sot">',
        f'<div class="cue-label">▶ SOT: {html.escape(slug)}</div>',
        '<div class="sot-content">',
    ]

    if thumbnail_url:
        parts.append(f'<img class="sot-thumbnail" src="{html.escape(thumbnail_url)}" alt="thumbnail">')

    parts.append('<div class="sot-info">')
    parts.append(f'<div class="sot-slug">{html.escape(slug)}</div>')

    if duration:
        parts.append(f'<div class="sot-duration">Duration: {html.escape(duration)}</div>')

    if outcue:
        parts.append(f'<div class="sot-outcue">Outcue: "{html.escape(outcue)}"</div>')

    parts.extend(['</div>', '</div>', '</div>'])

    return '\n'.join(parts)


def _format_img(cue_content: str, slug: str, cue_type: str, url_mapping: Dict[str, str]) -> str:
    """Format IMG or GFX cue."""

    original_url = _extract_field(cue_content, r'Media\s*[Uu]rl')
    media_url = url_mapping.get(original_url, '') if original_url else ''

    if not media_url:
        img_match = re.search(r'<img[^>]+src="([^"]+)"', cue_content, re.IGNORECASE)
        if img_match:
            original_url = img_match.group(1)
            media_url = url_mapping.get(original_url, '')

    description = _extract_field(cue_content, 'Description')

    css_class = 'cue-gfx' if cue_type == 'GFX' else 'cue-img'

    parts = [
        f'<div class="cue-block {css_class}">',
        f'<div class="cue-label">{cue_type}: {html.escape(slug)}</div>',
    ]

    if media_url:
        parts.append(f'<img src="{html.escape(media_url)}" alt="{html.escape(slug)}">')
    else:
        parts.append(f'<div style="padding:0.5in; background:#eee; color:#888;">[{cue_type}: {html.escape(slug)}]</div>')

    if description:
        parts.append(f'<div class="img-caption">{html.escape(description)}</div>')

    parts.append('</div>')

    return '\n'.join(parts)


def _format_production_cue(cue_content: str, cue_type: str, slug: str, url_mapping: Dict[str, str]) -> str:
    """Format cue for production preset (compact technical view)."""

    parts = [f'<div class="production-cue">']
    parts.append(f'<span class="cue-type">[{cue_type}]</span> <strong>{html.escape(slug)}</strong>')

    # Duration
    duration = _extract_field(cue_content, 'Duration')
    if duration:
        parts.append(f' — {html.escape(duration)}')

    # Media URL
    media_url_raw = _extract_field(cue_content, r'Media\s*[Uu]rl')
    if media_url_raw:
        parts.append(f'<br><small>Media: {html.escape(media_url_raw)}</small>')

    parts.append('</div>')

    return '\n'.join(parts)


def _convert_to_pdf(html_path: Path, pdf_path: Path, episode_info: Dict[str, Any]) -> bool:
    """Convert HTML to PDF with page numbers using wkhtmltopdf."""

    wkhtmltopdf = shutil.which('wkhtmltopdf')
    if not wkhtmltopdf:
        logger.warning("wkhtmltopdf not found - skipping PDF generation")
        return False

    try:
        episode_num = episode_info.get('episode_number', '0000')

        cmd = [
            wkhtmltopdf,
            '--page-size', 'Letter',
            '--margin-top', '0.75in',
            '--margin-bottom', '0.75in',
            '--margin-left', '0.75in',
            '--margin-right', '0.75in',
            '--footer-left', f'Episode {episode_num}',
            '--footer-right', 'Page [page] of [topage]',
            '--footer-font-size', '9',
            '--footer-spacing', '5',
            '--enable-local-file-access',
            '--print-media-type',
            str(html_path),
            str(pdf_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            logger.info(f"Generated PDF: {pdf_path}")
            return True
        else:
            logger.error(f"wkhtmltopdf failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("wkhtmltopdf timed out")
        return False
    except Exception as e:
        logger.error(f"PDF conversion failed: {e}")
        return False


# CLI support
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python host_script_generator.py <episode_number> [preset]")
        print("Presets: host_full (default), host_clean, production")
        sys.exit(1)

    episode_num = sys.argv[1]
    preset = sys.argv[2] if len(sys.argv) > 2 else "host_full"

    result = generate_host_script(episode_num, preset=preset)

    if result["success"]:
        print(f"Success! Generated {result['preset']} script")
        print(f"Output: {result['output_path']}")
        print(f"Items: {result['item_count']}, Blocks: {result['block_count']}")
    else:
        print(f"Error: {result['error']}")
        sys.exit(1)
