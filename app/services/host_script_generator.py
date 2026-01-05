"""
Host Script Generator - Database-based script compilation for PDF output.

Generates nicely formatted HTML scripts from database rundown items with:
- Block detection (A, B, C, D...) based on break regions
- Styled block headers (START BLOCK A / END BLOCK A)
- Segment headers
- IMG elements at 500px width
- FSQ with blockquote styling
- SOT with thumbnails
- Speaker attribution from paragraph classes
- Media resources copied to scripts/resources/ for portability
"""
import re
import html
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from database import SessionLocal
from models_v2 import Episode, Rundown, RundownItem, Season, Show

logger = logging.getLogger(__name__)

# Item types that define a break/commercial region
BREAK_ITEM_TYPES = {'advertisement', 'promo', 'transition', 'break', 'stinger', 'rejoin'}

# Speaker display names and colors
SPEAKER_CONFIG = {
    'josh': {'name': 'JOSH', 'color': '#1976d2'},
    'guest': {'name': 'GUEST', 'color': '#388e3c'},
    'caller': {'name': 'CALLER', 'color': '#f57c00'},
    'announcer': {'name': 'ANNOUNCER', 'color': '#7b1fa2'},
    'narrator': {'name': 'NARRATOR', 'color': '#5d4037'},
    'host': {'name': 'HOST', 'color': '#1976d2'},
}


def generate_host_script(episode_number: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a host script HTML from database rundown items.

    Args:
        episode_number: Episode number (e.g., "0249")
        output_dir: Optional output directory. Defaults to episode's scripts/ folder.

    Returns:
        Dict with success status, output path, and metadata
    """
    db = SessionLocal()

    try:
        # Find episode in database
        episode = db.query(Episode).filter(
            Episode.episode_number == int(episode_number)
        ).first()

        if not episode:
            return {
                "success": False,
                "error": f"Episode {episode_number} not found in database"
            }

        # Get rundown for this episode
        rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()

        if not rundown:
            return {
                "success": False,
                "error": f"No rundown found for episode {episode_number}"
            }

        # Get all rundown items ordered by position
        items = db.query(RundownItem).filter(
            RundownItem.rundown_id == rundown.id
        ).order_by(RundownItem.order_in_rundown).all()

        if not items:
            return {
                "success": False,
                "error": f"No rundown items found for episode {episode_number}"
            }

        # Get episode info for cover page
        episode_info = _get_episode_info(episode, db)

        # Determine output path
        # Use /home/episodes inside container, /mnt/sync/disaffected/episodes on host
        ep_num_padded = episode_number.zfill(4)
        if output_dir:
            output_path = Path(output_dir)
        else:
            # Try container path first, fall back to host path
            container_path = Path(f"/home/episodes/{ep_num_padded}/scripts")
            host_path = Path(f"/mnt/sync/disaffected/episodes/{ep_num_padded}/scripts")

            if container_path.parent.exists():
                output_path = container_path
            elif host_path.parent.exists():
                output_path = host_path
            else:
                output_path = container_path  # Default, will create if possible

        output_path.mkdir(parents=True, exist_ok=True)

        # Use scripts/current/ subdirectory for generated scripts
        current_scripts_path = output_path / "current"
        current_scripts_path.mkdir(parents=True, exist_ok=True)

        # Create resources subfolder for media assets
        resources_path = current_scripts_path / "resources"
        resources_path.mkdir(parents=True, exist_ok=True)

        # Collect and copy all media resources, get URL mapping
        url_mapping = _collect_and_copy_resources(items, resources_path, ep_num_padded)
        logger.info(f"Collected {len(url_mapping)} media resources")

        # Generate HTML content with mapped URLs
        html_content = _generate_html(episode_info, items, episode_number, url_mapping)

        # Generate filename - save to current/ subdirectory
        date_str = datetime.now().strftime("%Y%m%d")
        html_filename = f"{ep_num_padded}-HOST-SCRIPT-{date_str}.html"
        pdf_filename = f"{ep_num_padded}-HOST-SCRIPT-{date_str}.pdf"
        html_path = current_scripts_path / html_filename
        pdf_path = current_scripts_path / pdf_filename

        # Write HTML file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Generated host script HTML: {html_path}")

        # Convert to PDF with page numbers
        pdf_generated = _convert_to_pdf(html_path, pdf_path, episode_info)

        return {
            "success": True,
            "html_path": str(html_path),
            "pdf_path": str(pdf_path) if pdf_generated else None,
            "output_path": str(pdf_path) if pdf_generated else str(html_path),
            "episode_number": episode_number,
            "item_count": len(items),
            "block_count": _count_blocks(items)
        }

    except Exception as e:
        logger.error(f"Error generating host script for episode {episode_number}: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def _convert_to_pdf(html_path: Path, pdf_path: Path, episode_info: Dict[str, Any]) -> bool:
    """
    Convert HTML to PDF with page numbers using wkhtmltopdf.

    Returns True if PDF was generated successfully, False otherwise.
    """
    import subprocess
    import shutil

    # Check if wkhtmltopdf is available
    wkhtmltopdf = shutil.which('wkhtmltopdf')
    if not wkhtmltopdf:
        logger.warning("wkhtmltopdf not found - skipping PDF generation")
        return False

    try:
        # Build wkhtmltopdf command with page numbers
        # Footer format: Episode number on left, page X of Y on right
        episode_num = episode_info.get('episode_number', '0000')
        footer_left = f"Episode {episode_num}"
        footer_right = "Page [page] of [topage]"

        cmd = [
            wkhtmltopdf,
            '--page-size', 'Letter',
            '--margin-top', '0.75in',
            '--margin-bottom', '0.75in',
            '--margin-left', '0.75in',
            '--margin-right', '0.75in',
            '--footer-left', footer_left,
            '--footer-right', footer_right,
            '--footer-font-size', '9',
            '--footer-spacing', '5',
            '--enable-local-file-access',
            '--print-media-type',
            str(html_path),
            str(pdf_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

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


def _get_episode_info(episode: Episode, db) -> Dict[str, Any]:
    """Extract episode information for cover page."""
    # Get show name via season relationship
    show_name = "DISAFFECTED"
    if episode.season:
        season = db.query(Season).filter(Season.id == episode.season_id).first()
        if season:
            show = db.query(Show).filter(Show.id == season.show_id).first()
            if show:
                show_name = show.name.upper()

    # Format air date
    date_str = ""
    if episode.air_date:
        date_str = episode.air_date.strftime("%B %d, %Y at 9:00 PM")
    elif episode.publish_date:
        date_str = episode.publish_date.strftime("%B %d, %Y")

    return {
        "show_name": show_name,
        "episode_number": str(episode.episode_number).zfill(4) if episode.episode_number else "0000",
        "title": episode.title or f"Episode {episode.episode_number}",
        "date_str": date_str,
        "guest_name": episode.guest_name or "",
        "duration": episode.duration_formatted or "",
    }


def _collect_and_copy_resources(items: List[RundownItem], resources_path: Path, episode_number: str) -> Dict[str, str]:
    """
    Collect all media URLs from rundown items and copy them to the list folder.

    Iterates through each cue in order, extracting media URLs and copying files
    with enumerated names (e.g., "10-eirika-kirk.png", "20-charlie-kirk.png").

    Files are copied to the rundown/list/ subdirectory.

    Returns a mapping of original URL -> (relative path, cue_number) for HTML generation.
    """
    url_mapping = {}
    cue_counter = 0

    # Create media-list folder in the rundown directory (sibling to scripts/)
    # resources_path is scripts/resources, we want rundown/media-list
    media_list_path = resources_path.parent.parent / "rundown" / "media-list"
    media_list_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Media list folder: {media_list_path}")

    # Also keep resources folder for HTML script
    resources_path.mkdir(parents=True, exist_ok=True)

    # Base paths to search for media files
    container_base = Path("/home/episodes")
    host_base = Path("/mnt/sync/disaffected/episodes")

    # Cue block pattern
    cue_pattern = re.compile(
        r'<!-- Begin Cue -->(.*?)<!-- End Cue -->',
        re.DOTALL | re.IGNORECASE
    )

    # Patterns to find media URLs within cue blocks
    media_patterns = [
        re.compile(r'\[Media[Uu][Rr][Ll]:\s*([^\]]+)\]', re.IGNORECASE),
        re.compile(r'\[Thumbnail[Uu]rl:\s*([^\]]+)\]', re.IGNORECASE),
        re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE),
    ]

    # Iterate through items in order
    for item in items:
        if not item.script_content:
            continue

        # Find each cue block in order within this item
        for cue_match in cue_pattern.finditer(item.script_content):
            cue_content = cue_match.group(1)

            # Increment cue counter for each cue block (by 10)
            cue_counter += 10

            # Extract cue type for logging
            type_match = re.search(r'\[Type:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
            cue_type = type_match.group(1).strip().upper() if type_match else 'UNKNOWN'

            # Extract slug for filename
            slug_match = re.search(r'\[Slug:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
            slug = slug_match.group(1).strip() if slug_match else 'unknown'

            # Find all media URLs in this cue block
            for pattern in media_patterns:
                for match in pattern.finditer(cue_content):
                    original_url = match.group(1).strip()

                    if not original_url or original_url in url_mapping:
                        continue

                    # Skip http/https URLs (external resources)
                    if original_url.startswith('http://') or original_url.startswith('https://'):
                        continue

                    # Try to find the actual file
                    source_path = _find_media_file(original_url, episode_number, container_base, host_base)

                    if source_path and source_path.exists():
                        # Generate enumerated filename: "10-eirika-kirk.png"
                        original_filename = source_path.name
                        enumerated_filename = f"{cue_counter}-{original_filename}"

                        # Copy to media-list folder with enumerated name
                        media_list_dest_path = media_list_path / enumerated_filename
                        try:
                            shutil.copy2(source_path, media_list_dest_path)
                            logger.info(f"[{cue_type}] Copied {source_path.name} -> {enumerated_filename}")
                        except Exception as e:
                            logger.warning(f"Failed to copy to media-list: {e}")

                        # Also copy to resources folder (original name for backwards compat)
                        resources_dest_path = resources_path / original_filename
                        try:
                            if not resources_dest_path.exists():
                                shutil.copy2(source_path, resources_dest_path)
                        except Exception as e:
                            logger.warning(f"Failed to copy to resources: {e}")

                        # Store mapping: original URL -> resources path
                        # The cue formatter will add enumeration when referencing
                        url_mapping[original_url] = f"resources/{original_filename}"
                        logger.debug(f"Mapped {original_url} -> resources/{original_filename}")
                    else:
                        logger.warning(f"Media file not found: {original_url}")

    logger.info(f"Processed {cue_counter // 10} cues, copied {len(url_mapping)} media files to rundown/media-list/")
    return url_mapping


def _find_media_file(url: str, episode_number: str, container_base: Path, host_base: Path) -> Optional[Path]:
    """
    Find a media file from a URL, trying various path resolutions.

    Returns the Path to the file if found, None otherwise.
    """
    # Clean the URL
    url = url.strip()

    # Handle /episodes/... paths (web URL format) - strip leading slash
    if url.startswith('/episodes/'):
        url = url[1:]  # Remove leading slash, treat as relative path

    # Already an absolute path (real filesystem path like /mnt/... or /home/...)
    if url.startswith('/'):
        path = Path(url)
        if path.exists():
            return path
        return None

    # Relative path starting with "episodes/"
    if url.startswith('episodes/'):
        # Try container path
        container_path = container_base.parent / url
        if container_path.exists():
            return container_path

        # Try host path
        host_path = host_base.parent / url
        if host_path.exists():
            return host_path

    # Relative path starting with "../assets/" or "assets/"
    if url.startswith('../assets/') or url.startswith('assets/'):
        clean_url = url.replace('../', '')
        # Try container path
        container_path = container_base / episode_number / clean_url
        if container_path.exists():
            return container_path

        # Try host path
        host_path = host_base / episode_number / clean_url
        if host_path.exists():
            return host_path

    # Just a filename - search in common locations
    filename = Path(url).name
    search_dirs = [
        container_base / episode_number / "assets" / "images",
        container_base / episode_number / "assets" / "video",
        container_base / episode_number / "assets" / "graphics",
        container_base / episode_number / "assets" / "quotes",
        host_base / episode_number / "assets" / "images",
        host_base / episode_number / "assets" / "video",
        host_base / episode_number / "assets" / "graphics",
        host_base / episode_number / "assets" / "quotes",
    ]

    for search_dir in search_dirs:
        if search_dir.exists():
            candidate = search_dir / filename
            if candidate.exists():
                return candidate

    return None


def _count_blocks(items: List[RundownItem]) -> int:
    """Count the number of content blocks in the rundown."""
    blocks = _detect_blocks(items)
    return len(blocks)


def _detect_blocks(items: List[RundownItem]) -> List[Dict[str, Any]]:
    """
    Detect content blocks based on break regions.

    A block starts with the first non-break item and ends when a break item is encountered.
    Block A is the first block, Block B is after the first break region, etc.

    Returns list of blocks, each containing:
    - letter: Block letter (A, B, C, D...)
    - items: List of RundownItem objects in this block
    - start_index: Index of first item
    - end_index: Index of last item
    """
    blocks = []
    current_block_items = []
    block_letter_index = 0
    in_break_region = False

    for i, item in enumerate(items):
        item_type = (item.item_type or 'segment').lower()
        is_break_item = item_type in BREAK_ITEM_TYPES

        if is_break_item:
            # End current block if we have items
            if current_block_items and not in_break_region:
                block_letter = chr(ord('A') + block_letter_index)
                blocks.append({
                    'letter': block_letter,
                    'items': current_block_items,
                    'start_index': i - len(current_block_items),
                    'end_index': i - 1
                })
                current_block_items = []
                block_letter_index += 1
            in_break_region = True
        else:
            # Content item - add to current block
            in_break_region = False
            current_block_items.append(item)

    # Don't forget the last block
    if current_block_items:
        block_letter = chr(ord('A') + block_letter_index)
        blocks.append({
            'letter': block_letter,
            'items': current_block_items,
            'start_index': len(items) - len(current_block_items),
            'end_index': len(items) - 1
        })

    return blocks


def _generate_html(episode_info: Dict[str, Any], items: List[RundownItem], episode_number: str = "0000", url_mapping: Optional[Dict[str, str]] = None) -> str:
    """Generate the complete HTML document.

    Args:
        episode_info: Episode metadata for cover page
        items: List of rundown items
        episode_number: Episode number string
        url_mapping: Optional mapping of original URL -> relative path in resources folder
    """
    if url_mapping is None:
        url_mapping = {}

    ep_num = episode_info.get('episode_number', episode_number)

    # CSS styles with page numbering via CSS counters
    css = """
        @page {
            size: letter;
            margin: 0.75in 0.75in 1in 0.75in;
            @bottom-left {
                content: "Episode """ + ep_num + """";
                font-size: 9pt;
                color: #666;
            }
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 14pt;
            line-height: 1.6;
            color: #1a1a1a;
            margin: 0;
            padding: 0;
            background: #fff;
        }

        .container {
            max-width: 7.5in;
            margin: 0 auto;
            padding: 0.5in;
        }

        /* Cover Page */
        .cover-page {
            text-align: center;
            page-break-after: always;
            padding-top: 2in;
        }

        .show-title {
            font-size: 36pt;
            font-weight: bold;
            letter-spacing: 0.1em;
            margin-bottom: 0.5in;
        }

        .episode-number {
            font-size: 18pt;
            color: #666;
            margin-bottom: 0.25in;
        }

        .episode-date {
            font-size: 14pt;
            color: #888;
            margin-bottom: 0.5in;
        }

        .episode-title {
            font-size: 24pt;
            font-weight: 600;
            margin-top: 0.5in;
        }

        .guest-name {
            font-size: 16pt;
            color: #444;
            margin-top: 0.25in;
            font-style: italic;
        }

        /* Block Headers */
        .block-start, .block-end {
            text-align: center;
            font-size: 16pt;
            font-weight: bold;
            padding: 0.3in 0;
            margin: 0.4in 0;
            border-top: 3px double #333;
            border-bottom: 3px double #333;
            background: linear-gradient(to right, #f8f8f8, #fff, #f8f8f8);
            letter-spacing: 0.15em;
        }

        .block-end {
            background: linear-gradient(to right, #eee, #f5f5f5, #eee);
            color: #555;
        }

        /* Segment Headers */
        .segment-header {
            font-size: 16pt;
            font-weight: bold;
            color: #1565c0;
            margin-top: 0.4in;
            margin-bottom: 0.15in;
            padding-bottom: 0.1in;
            border-bottom: 2px solid #1565c0;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .segment-duration {
            font-size: 10pt;
            color: #888;
            font-weight: normal;
            float: right;
            text-transform: none;
        }

        /* Script Content */
        .script-content {
            margin: 0.2in 0;
        }

        .script-paragraph {
            text-align: justify;
            margin: 0.15in 0;
            text-indent: 0;
        }

        /* Speaker Attribution */
        .speaker-tag {
            font-weight: bold;
            font-size: 10pt;
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            margin-right: 8px;
            margin-bottom: 4px;
        }

        .speaker-josh { background: #e3f2fd; color: #1565c0; }
        .speaker-guest { background: #e8f5e9; color: #2e7d32; }
        .speaker-caller { background: #fff3e0; color: #ef6c00; }
        .speaker-announcer { background: #f3e5f5; color: #7b1fa2; }
        .speaker-narrator { background: #efebe9; color: #5d4037; }
        .speaker-host { background: #e3f2fd; color: #1565c0; }

        /* FSQ - Full Screen Quote */
        .cue-fsq {
            margin: 0.3in 0;
            padding: 0.3in;
            background: #fafafa;
            border-left: 6px solid #ccc;
            border-right: 6px solid #ccc;
            page-break-inside: avoid;
        }

        .cue-fsq .cue-label {
            font-size: 10pt;
            font-weight: bold;
            color: #888;
            margin-bottom: 0.1in;
        }

        .cue-fsq blockquote {
            font-size: 16pt;
            font-style: italic;
            color: #444;
            margin: 0;
            padding: 0;
            line-height: 1.5;
        }

        .cue-fsq .attribution {
            text-align: right;
            font-size: 12pt;
            color: #666;
            margin-top: 0.15in;
        }

        /* SOT - Sound on Tape */
        .cue-sot {
            margin: 0.3in 0;
            padding: 0.2in;
            background: #fff8e1;
            border: 2px solid #ffc107;
            border-radius: 8px;
            page-break-inside: avoid;
        }

        .cue-sot .cue-label {
            font-size: 10pt;
            font-weight: bold;
            color: #ff8f00;
            margin-bottom: 0.1in;
        }

        .cue-sot .sot-content {
            display: flex;
            align-items: flex-start;
            gap: 0.2in;
        }

        .cue-sot .sot-thumbnail {
            width: 120px;
            height: 68px;
            object-fit: cover;
            border: 1px solid #ddd;
            border-radius: 4px;
        }

        .cue-sot .sot-info {
            flex: 1;
        }

        .cue-sot .sot-slug {
            font-weight: bold;
            font-size: 12pt;
        }

        .cue-sot .sot-duration {
            font-size: 10pt;
            color: #666;
        }

        .cue-sot .sot-transcription {
            font-size: 10pt;
            color: #555;
            font-style: italic;
            margin-top: 0.1in;
        }

        /* IMG - Image/GFX */
        .cue-img {
            margin: 0.3in 0;
            text-align: center;
            page-break-inside: avoid;
        }

        .cue-img .cue-label {
            font-size: 10pt;
            font-weight: bold;
            color: #888;
            margin-bottom: 0.1in;
        }

        .cue-img img {
            max-width: 500px;
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
        }

        .cue-img .img-caption {
            font-size: 10pt;
            color: #666;
            margin-top: 0.1in;
            font-style: italic;
        }

        /* GFX - Graphics (same as IMG) */
        .cue-gfx {
            margin: 0.3in 0;
            text-align: center;
            page-break-inside: avoid;
        }

        .cue-gfx .cue-label {
            font-size: 10pt;
            font-weight: bold;
            color: #888;
            margin-bottom: 0.1in;
        }

        .cue-gfx img {
            max-width: 500px;
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
        }

        /* Page breaks */
        .page-break {
            page-break-before: always;
        }

        /* Print optimizations */
        @media print {
            body {
                font-size: 12pt;
            }
            .container {
                padding: 0;
            }
        }
    """

    # Build HTML
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        f'<title>{episode_info["show_name"]} - Episode {episode_info["episode_number"]} - Host Script</title>',
        '<style>',
        css,
        '</style>',
        '</head>',
        '<body>',
        '<div class="container">',
    ]

    # Cover page
    html_parts.append(_generate_cover_page(episode_info))

    # Detect blocks
    blocks = _detect_blocks(items)

    # Initialize cue counter for enumeration (tracks across all blocks)
    cue_counter = {'count': 0}

    # Generate content for each block
    for block in blocks:
        html_parts.append(_generate_block_content(block, url_mapping, cue_counter))

    html_parts.extend([
        '</div>',
        '</body>',
        '</html>'
    ])

    return '\n'.join(html_parts)


def _generate_cover_page(episode_info: Dict[str, Any]) -> str:
    """Generate the cover page HTML."""
    cover = [
        '<div class="cover-page">',
        f'<div class="show-title">{html.escape(episode_info["show_name"])}</div>',
        f'<div class="episode-number">EPISODE {html.escape(episode_info["episode_number"])}</div>',
    ]

    if episode_info["date_str"]:
        cover.append(f'<div class="episode-date">{html.escape(episode_info["date_str"])}</div>')

    cover.append(f'<div class="episode-title">{html.escape(episode_info["title"])}</div>')

    if episode_info["guest_name"]:
        cover.append(f'<div class="guest-name">Guest: {html.escape(episode_info["guest_name"])}</div>')

    cover.append('</div>')

    return '\n'.join(cover)


def _generate_block_content(block: Dict[str, Any], url_mapping: Dict[str, str], cue_counter: Dict[str, int]) -> str:
    """Generate HTML content for a single block.

    Args:
        block: Block data with letter and items
        url_mapping: URL to local path mapping
        cue_counter: Mutable dict with 'count' key to track cue enumeration across blocks
    """
    parts = []

    # Block start header
    parts.append(f'<div class="block-start">★ ★ ★  START BLOCK {block["letter"]}  ★ ★ ★</div>')

    # Process each item in the block
    last_speaker = None
    for item in block['items']:
        segment_html, last_speaker = _process_rundown_item(item, last_speaker, url_mapping, cue_counter)
        parts.append(segment_html)

    # Block end header
    parts.append(f'<div class="block-end">— — —  END BLOCK {block["letter"]}  — — —</div>')

    return '\n'.join(parts)


def _process_rundown_item(item: RundownItem, last_speaker: Optional[str], url_mapping: Dict[str, str], cue_counter: Dict[str, int]) -> Tuple[str, Optional[str]]:
    """
    Process a single rundown item and return HTML content.

    Args:
        item: The rundown item to process
        last_speaker: Last speaker used for attribution
        url_mapping: URL to local path mapping
        cue_counter: Mutable dict with 'count' key to track cue enumeration

    Returns tuple of (html_content, last_speaker_used)
    """
    parts = []
    current_speaker = last_speaker

    # Get item type
    item_type = (item.item_type or 'segment').lower()

    # Skip empty items (ads with no content, empty segments, etc.)
    has_content = item.script_content and item.script_content.strip()

    # Clean script content to check if it's truly empty
    if has_content:
        # Remove frontmatter and check if there's actual content
        cleaned = re.sub(r'^---.*?---\s*', '', item.script_content, flags=re.DOTALL)
        cleaned = re.sub(r'<p[^>]*>\s*</p>', '', cleaned)
        cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.DOTALL)
        has_content = bool(cleaned.strip())

    # Skip items that are truly empty
    if not has_content:
        return '', current_speaker

    # Segment header
    title = item.title or item.slug or "Untitled Segment"
    duration_str = item.duration or ""

    # Clean up duration format (remove extra colons if present)
    if duration_str and duration_str.count(':') > 2:
        # Format is likely HH:MM:SS:FF - convert to HH:MM:SS
        parts_list = duration_str.split(':')
        if len(parts_list) >= 3:
            duration_str = ':'.join(parts_list[:3])

    parts.append('<div class="segment">')
    parts.append(f'<div class="segment-header">{html.escape(title)}')
    if duration_str:
        parts.append(f'<span class="segment-duration">{html.escape(duration_str)}</span>')
    parts.append('</div>')

    # Process script content
    if item.script_content:
        content_html, current_speaker = _process_script_content(
            item.script_content,
            last_speaker,
            url_mapping,
            cue_counter
        )
        if content_html.strip():
            parts.append('<div class="script-content">')
            parts.append(content_html)
            parts.append('</div>')

    parts.append('</div>')

    return '\n'.join(parts), current_speaker


def _process_script_content(content: str, last_speaker: Optional[str], url_mapping: Dict[str, str], cue_counter: Dict[str, int]) -> Tuple[str, Optional[str]]:
    """
    Process script content, handling cue blocks and paragraphs.

    Args:
        content: Raw script content with cue blocks
        last_speaker: Last speaker used for attribution
        url_mapping: URL to local path mapping
        cue_counter: Mutable dict with 'count' key to track cue enumeration

    Returns tuple of (html_content, last_speaker_used)
    """
    parts = []
    current_speaker = last_speaker

    # Pattern to match cue blocks
    cue_pattern = re.compile(
        r'<!-- Begin Cue -->(.*?)<!-- End Cue -->',
        re.DOTALL | re.IGNORECASE
    )

    # Pattern to match paragraphs with speaker class
    para_pattern = re.compile(
        r'<p(?:\s+class="([^"]*)")?[^>]*>(.*?)</p>',
        re.DOTALL | re.IGNORECASE
    )

    # Split content by cue blocks
    last_end = 0
    for match in cue_pattern.finditer(content):
        # Process text before this cue
        text_before = content[last_end:match.start()]
        if text_before.strip():
            text_html, current_speaker = _process_text_content(text_before, current_speaker)
            parts.append(text_html)

        # Process cue block - increment counter for each cue
        cue_content = match.group(1)
        cue_counter['count'] += 10  # Increment by 10 for each cue (e.g., 10, 20, 30...)
        cue_html = _process_cue_block(cue_content, url_mapping, cue_counter['count'])
        if cue_html:
            parts.append(cue_html)

        last_end = match.end()

    # Process remaining text after last cue
    text_after = content[last_end:]
    if text_after.strip():
        text_html, current_speaker = _process_text_content(text_after, current_speaker)
        parts.append(text_html)

    return '\n'.join(parts), current_speaker


def _process_text_content(text: str, last_speaker: Optional[str]) -> Tuple[str, Optional[str]]:
    """
    Process text content (paragraphs with speaker classes).

    Returns tuple of (html_content, last_speaker_used)
    """
    parts = []
    current_speaker = last_speaker

    # Remove YAML frontmatter first (handles both --- and - - - variants)
    text = re.sub(r'^-\s*-\s*-.*?-\s*-\s*-\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'^---.*?---\s*', '', text, flags=re.DOTALL)

    # Remove markdown headers
    text = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)

    # Fix double-nested paragraph tags (data quality issue)
    # <p class="josh"><p class="josh">content</p> -> <p class="josh">content</p>
    text = re.sub(r'<p([^>]*)>\s*<p[^>]*>', r'<p\1>', text, flags=re.IGNORECASE)

    # Pattern to match paragraphs with optional speaker class
    para_pattern = re.compile(
        r'<p(?:\s+class="([^"]*)")?[^>]*>(.*?)</p>',
        re.DOTALL | re.IGNORECASE
    )

    for match in para_pattern.finditer(text):
        speaker_class = match.group(1) or 'josh'
        content = match.group(2).strip()

        if not content:
            continue

        # Clean up content (remove nested tags, normalize whitespace)
        content = re.sub(r'<br\s*/?>', ' ', content)
        content = re.sub(r'\s+', ' ', content)

        # Check if speaker changed or coming back from break
        show_speaker = (speaker_class != current_speaker)
        current_speaker = speaker_class

        # Get speaker config
        speaker_info = SPEAKER_CONFIG.get(speaker_class, {'name': speaker_class.upper(), 'color': '#666'})

        parts.append('<p class="script-paragraph">')

        if show_speaker:
            parts.append(
                f'<span class="speaker-tag speaker-{html.escape(speaker_class)}">'
                f'{html.escape(speaker_info["name"])}</span>'
            )

        parts.append(html.escape(content))
        parts.append('</p>')

    # If no paragraphs found, try to process as plain text
    if not parts and text.strip():
        # Remove any remaining raw <p> tags that weren't matched
        text = re.sub(r'<p[^>]*>\s*</p>', '', text)
        text = re.sub(r'</?p[^>]*>', '', text)

        paragraphs = text.strip().split('\n\n')
        for para in paragraphs:
            para = para.strip()
            # Skip empty, metadata, or comment lines
            if para and not para.startswith('[') and not para.startswith('<!--') and not para.startswith('---'):
                # Skip lines that look like YAML
                if ':' in para and para.count(':') > para.count(' '):
                    continue
                parts.append(f'<p class="script-paragraph">{html.escape(para)}</p>')

    return '\n'.join(parts), current_speaker


def _process_cue_block(cue_content: str, url_mapping: Dict[str, str], cue_number: int) -> str:
    """Process a cue block and return formatted HTML.

    Args:
        cue_content: Raw cue block content
        url_mapping: URL to local path mapping
        cue_number: Enumerated cue number for this cue (10, 20, 30, etc.)
    """

    # Extract cue type
    type_match = re.search(r'\[Type:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
    if not type_match:
        return ''

    cue_type = type_match.group(1).strip().upper()

    # Extract common fields
    slug_match = re.search(r'\[Slug:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
    slug = slug_match.group(1).strip() if slug_match else 'unknown'

    # Create enumerated slug: "80-eirika-kirk" format
    enumerated_slug = f"{cue_number}-{slug}"

    if cue_type == 'FSQ':
        return _format_fsq_cue(cue_content, enumerated_slug, url_mapping, cue_number)
    elif cue_type == 'SOT':
        return _format_sot_cue(cue_content, enumerated_slug, url_mapping, cue_number)
    elif cue_type in ('IMG', 'GFX'):
        return _format_img_cue(cue_content, enumerated_slug, cue_type, url_mapping, cue_number)
    else:
        # Generic cue display
        return f'<div class="cue-generic"><strong>[{cue_type}]</strong> {html.escape(enumerated_slug)}</div>'


def _format_fsq_cue(cue_content: str, slug: str, url_mapping: Dict[str, str], cue_number: int) -> str:
    """Format a Full Screen Quote (FSQ) cue.

    Args:
        cue_content: Raw cue block content
        slug: Enumerated slug (e.g., "80-quote-name")
        url_mapping: URL to local path mapping
        cue_number: Enumerated cue number for media filename
    """

    # Extract quote
    quote_match = re.search(r'\[Quote:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
    quote = quote_match.group(1).strip().strip('"\'') if quote_match else ''

    # Extract attribution
    attr_match = re.search(r'\[Attribution:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
    attribution = attr_match.group(1).strip() if attr_match else ''

    # Extract media URL for FSQ image (if present)
    media_match = re.search(r'\[Media[Uu][Rr][Ll]:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
    media_url = media_match.group(1).strip() if media_match else ''

    # Apply URL mapping if available - use mapped path directly (already has correct filename)
    if media_url and media_url in url_mapping:
        media_url = url_mapping[media_url]

    parts = [
        '<div class="cue-fsq">',
        f'<div class="cue-label">FSQ: {html.escape(slug)}</div>',
    ]

    # Include FSQ image if present
    if media_url:
        parts.append(f'<img src="{html.escape(media_url)}" alt="{html.escape(slug)}" style="max-width:500px; margin-bottom:0.15in;">')

    parts.append(f'<blockquote>{html.escape(quote)}</blockquote>')

    if attribution:
        parts.append(f'<div class="attribution">— {html.escape(attribution)}</div>')

    parts.append('</div>')

    return '\n'.join(parts)


def _format_sot_cue(cue_content: str, slug: str, url_mapping: Dict[str, str], cue_number: int) -> str:
    """Format a Sound On Tape (SOT) cue.

    Args:
        cue_content: Raw cue block content
        slug: Enumerated slug (e.g., "80-clip-name")
        url_mapping: URL to local path mapping
        cue_number: Enumerated cue number for media filename
    """

    # Extract duration
    duration_match = re.search(r'\[Duration:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
    duration = duration_match.group(1).strip() if duration_match else ''

    # Extract thumbnail URL
    thumb_match = re.search(r'\[Thumbnail[Uu]rl:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
    thumbnail_url = thumb_match.group(1).strip() if thumb_match else ''

    # Apply URL mapping if available - use mapped path directly (already has correct filename)
    if thumbnail_url and thumbnail_url in url_mapping:
        thumbnail_url = url_mapping[thumbnail_url]

    # Extract transcription
    trans_match = re.search(r'\[Transcription:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
    transcription = trans_match.group(1).strip() if trans_match else ''

    parts = [
        '<div class="cue-sot">',
        f'<div class="cue-label">▶ SOT: {html.escape(slug)}</div>',
        '<div class="sot-content">',
    ]

    if thumbnail_url:
        parts.append(f'<img class="sot-thumbnail" src="{html.escape(thumbnail_url)}" alt="SOT thumbnail">')

    parts.append('<div class="sot-info">')
    parts.append(f'<div class="sot-slug">{html.escape(slug)}</div>')

    if duration:
        parts.append(f'<div class="sot-duration">Duration: {html.escape(duration)}</div>')

    if transcription:
        # Truncate long transcriptions for print
        if len(transcription) > 200:
            transcription = transcription[:200] + '...'
        parts.append(f'<div class="sot-transcription">"{html.escape(transcription)}"</div>')

    parts.extend([
        '</div>',
        '</div>',
        '</div>'
    ])

    return '\n'.join(parts)


def _get_enumerated_media_path(mapped_path: str, cue_number: int) -> str:
    """
    Convert a mapped media path to an enumerated filename.

    Example: "resources/eirika-kirk.png" with cue_number=80 becomes "resources/80-eirika-kirk.png"

    Args:
        mapped_path: The path from url_mapping (e.g., "resources/filename.png")
        cue_number: The cue enumeration number

    Returns:
        Path with enumerated filename
    """
    if not mapped_path:
        return mapped_path

    # Split path into directory and filename
    path = Path(mapped_path)
    directory = path.parent
    filename = path.name

    # Prepend cue number to filename
    enumerated_filename = f"{cue_number}-{filename}"

    # Reconstruct path
    if str(directory) == '.':
        return enumerated_filename
    return str(directory / enumerated_filename)


def _resolve_media_url(url: str) -> str:
    """
    Convert relative media URLs to absolute file paths for PDF generation.
    """
    if not url:
        return url

    # Already absolute
    if url.startswith('/') or url.startswith('file://') or url.startswith('http'):
        return url

    # Relative path like "episodes/0249/assets/images/..."
    if url.startswith('episodes/'):
        # Try container path first
        container_path = Path('/home') / url
        if container_path.exists():
            return f'file://{container_path}'

        # Try host path
        host_path = Path('/mnt/sync/disaffected') / url
        if host_path.exists():
            return f'file://{host_path}'

    return url


def _format_img_cue(cue_content: str, slug: str, cue_type: str, url_mapping: Dict[str, str], cue_number: int) -> str:
    """Format an IMG or GFX cue.

    Args:
        cue_content: Raw cue block content
        slug: Enumerated slug (e.g., "80-image-name")
        cue_type: IMG or GFX
        url_mapping: URL to local path mapping
        cue_number: Enumerated cue number for media filename
    """

    # Extract media URL
    media_match = re.search(r'\[Media[Uu][Rr][Ll]:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
    original_media_url = media_match.group(1).strip() if media_match else ''

    # Also check for embedded img tag
    if not original_media_url:
        img_match = re.search(r'<img[^>]+src="([^"]+)"', cue_content, re.IGNORECASE)
        original_media_url = img_match.group(1) if img_match else ''

    # Apply URL mapping if available - use mapped path directly (already has correct filename)
    if original_media_url and original_media_url in url_mapping:
        media_url = url_mapping[original_media_url]
    else:
        # Fallback to resolved absolute path
        media_url = _resolve_media_url(original_media_url)

    # Extract description/caption
    desc_match = re.search(r'\[Description:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
    description = desc_match.group(1).strip() if desc_match else ''

    css_class = 'cue-gfx' if cue_type == 'GFX' else 'cue-img'

    parts = [
        f'<div class="{css_class}">',
        f'<div class="cue-label">{cue_type}: {html.escape(slug)}</div>',
    ]

    if media_url:
        parts.append(f'<img src="{html.escape(media_url)}" alt="{html.escape(slug)}">')
    else:
        parts.append(f'<div style="padding: 1in; background: #f0f0f0; color: #888;">[Image: {html.escape(slug)}]</div>')

    if description:
        parts.append(f'<div class="img-caption">{html.escape(description)}</div>')

    parts.append('</div>')

    return '\n'.join(parts)


# CLI support for testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python host_script_generator.py <episode_number>")
        sys.exit(1)

    episode_num = sys.argv[1]
    result = generate_host_script(episode_num)

    if result["success"]:
        print(f"Success! Script generated at: {result['output_path']}")
        print(f"Items: {result['item_count']}, Blocks: {result['block_count']}")
    else:
        print(f"Error: {result['error']}")
        sys.exit(1)
