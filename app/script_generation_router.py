"""
Script Generation Router - API endpoints for generating various script formats.

Supports three presets:
- HOST_FULL: Complete script with all cues, visuals, and production info
- HOST_CLEAN: Spoken text only with minimal cue indicators (teleprompter-friendly)
- PRODUCTION: Technical rundown with timing, all cues, media references

Plus:
- Media list (list of all media cues)
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from enum import Enum
from auth.utils import get_current_user_or_key
from services.host_script_generator import generate_host_script, ScriptPreset
from services.cue_extractor import CUE_BLOCK_RE
from pathlib import Path
from datetime import datetime
from database import SessionLocal
from models_v2 import Episode, Rundown, RundownItem
import logging
import subprocess
import shutil
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scripts", tags=["Scripts"])


class ScriptPresetEnum(str, Enum):
    """Available script presets."""
    host_full = "host_full"
    host_clean = "host_clean"
    production = "production"


class ScriptGenerationResponse(BaseModel):
    """Response model for script generation."""
    success: bool
    output_path: Optional[str] = None
    html_path: Optional[str] = None
    pdf_path: Optional[str] = None
    md_path: Optional[str] = None
    episode_number: Optional[str] = None
    preset: Optional[str] = None
    item_count: Optional[int] = None
    block_count: Optional[int] = None
    revision: Optional[int] = None
    error: Optional[str] = None


class MediaListItem(BaseModel):
    """Single media item in the media list."""
    segmentSlug: str
    segmentOrder: Optional[int] = None
    cueType: str
    slug: str = ""
    mediaUrl: str = ""
    assetId: str = ""
    duration: str = ""
    description: str = ""
    hasMissingMedia: bool = False


class MediaListRequest(BaseModel):
    """Request model for media list generation."""
    media_items: List[MediaListItem]


@router.post("/generate/{episode_number}", response_model=ScriptGenerationResponse)
async def generate_script_endpoint(
    episode_number: str,
    preset: ScriptPresetEnum = Query(ScriptPresetEnum.host_full, description="Script preset"),
    output_dir: Optional[str] = Query(None, description="Custom output directory"),
    current_user: dict = Depends(get_current_user_or_key)
) -> ScriptGenerationResponse:
    """
    Generate a script for an episode with the specified preset.

    **Presets:**
    - **host_full**: Complete script with all cues, images, SOT thumbnails, and production info
    - **host_clean**: Spoken text only with minimal cue markers (teleprompter-friendly, large text)
    - **production**: Technical rundown with timing, all cue details, media references

    **Block Structure:**
    - BLOCK A: All content from show start until BREAK 1
    - BLOCK B: Content after BREAK 1 until BREAK 2
    - BLOCK C: Content after BREAK 2 until BREAK 3
    - And so on...

    **Output:**
    - HTML and PDF files saved to episode's scripts/current/ folder
    - PDF includes page numbers (Episode XXXX on left, Page X of Y on right)
    """
    try:
        result = generate_host_script(episode_number, output_dir, preset=preset.value)

        return ScriptGenerationResponse(
            success=result.get("success", False),
            output_path=result.get("output_path"),
            html_path=result.get("html_path"),
            pdf_path=result.get("pdf_path"),
            episode_number=result.get("episode_number"),
            preset=result.get("preset"),
            item_count=result.get("item_count"),
            block_count=result.get("block_count"),
            revision=result.get("revision"),
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"Error generating script for episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/host/{episode_number}", response_model=ScriptGenerationResponse)
async def generate_host_script_endpoint(
    episode_number: str,
    preset: ScriptPresetEnum = Query(ScriptPresetEnum.host_full, description="Script preset"),
    output_dir: Optional[str] = Query(None, description="Custom output directory"),
    current_user: dict = Depends(get_current_user_or_key)
) -> ScriptGenerationResponse:
    """
    Generate a host script for an episode (alias for /generate with host_full preset).

    See /generate/{episode_number} for full documentation.
    """
    try:
        result = generate_host_script(episode_number, output_dir, preset=preset.value)

        return ScriptGenerationResponse(
            success=result.get("success", False),
            output_path=result.get("output_path"),
            html_path=result.get("html_path"),
            pdf_path=result.get("pdf_path"),
            episode_number=result.get("episode_number"),
            preset=result.get("preset"),
            item_count=result.get("item_count"),
            block_count=result.get("block_count"),
            revision=result.get("revision"),
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"Error generating host script for episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/media-list/{episode_number}", response_model=ScriptGenerationResponse)
async def generate_media_list_endpoint(
    episode_number: str,
    request: MediaListRequest,
    current_user: dict = Depends(get_current_user_or_key)
) -> ScriptGenerationResponse:
    """
    Generate a media list for an episode.

    The media list is an HTML document listing all media cues in the episode:
    - Cue type (IMG, GFX, SOT, VO, etc.)
    - Slug and description
    - Media URL/path
    - Duration
    - Missing media highlighted

    The list is saved to the episode's scripts/ folder.
    """
    try:
        ep_num = episode_number.zfill(4)

        # Try container path first, then host path
        container_scripts_dir = Path(f"/home/episodes/{ep_num}/scripts")
        host_scripts_dir = Path(f"/mnt/sync/disaffected/episodes/{ep_num}/scripts")

        if container_scripts_dir.exists():
            scripts_dir = container_scripts_dir
        elif host_scripts_dir.exists():
            scripts_dir = host_scripts_dir
        else:
            # Create the directory
            host_scripts_dir.mkdir(parents=True, exist_ok=True)
            scripts_dir = host_scripts_dir

        # Generate HTML media list
        html_content = _generate_media_list_html(ep_num, request.media_items)

        # Save the HTML file
        html_path = scripts_dir / f"{ep_num}-MEDIA-LIST.html"
        html_path.write_text(html_content, encoding='utf-8')
        logger.info(f"Media list HTML generated for episode {episode_number}: {html_path}")

        # Convert to PDF with pagination
        pdf_path = scripts_dir / f"{ep_num}-MEDIA-LIST.pdf"
        pdf_generated = _convert_html_to_pdf(html_path, pdf_path, ep_num, "Media List")

        return ScriptGenerationResponse(
            success=True,
            output_path=str(pdf_path) if pdf_generated else str(html_path),
            episode_number=episode_number,
            item_count=len(request.media_items)
        )

    except Exception as e:
        logger.error(f"Error generating media list for episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/media-list/{episode_number}", response_model=ScriptGenerationResponse)
async def generate_media_list_from_db(
    episode_number: str,
    current_user: dict = Depends(get_current_user_or_key)
) -> ScriptGenerationResponse:
    """
    Generate a media list directly from the database.

    Scans all rundown items for cue blocks and extracts media information.
    This is more reliable than the POST endpoint which requires frontend to send data.
    """
    db = SessionLocal()
    try:
        ep_num = episode_number.zfill(4)

        # Find episode and rundown
        episode = db.query(Episode).filter(Episode.episode_number == int(episode_number)).first()
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
        if not rundown:
            raise HTTPException(status_code=404, detail=f"No rundown found for episode {episode_number}")

        # Get all rundown items ordered by position
        items = db.query(RundownItem).filter(
            RundownItem.rundown_id == rundown.id
        ).order_by(RundownItem.order_in_rundown).all()

        # Extract media cues from script content
        media_items = []
        cue_types = ['IMG', 'GFX', 'SOT', 'VO', 'NAT', 'PKG', 'BUMP', 'STING', 'FSQ', 'RIF', 'DIR']
        cue_pattern = CUE_BLOCK_RE  # matches expanded + collapsed cues

        for item in items:
            if not item.script_content:
                continue

            for match in cue_pattern.finditer(item.script_content):
                cue_content = match.group(1)

                # Extract fields (flexible patterns)
                type_match = re.search(r'\[Type:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
                slug_match = re.search(r'\[Slug:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
                media_url_match = re.search(r'\[Media\s*[Uu]rl:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
                asset_id_match = re.search(r'\[Asset\s*[Ii][Dd]:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
                duration_match = re.search(r'\[Duration:\s*([^\]]+)\]', cue_content, re.IGNORECASE)

                cue_type = type_match.group(1).strip().upper() if type_match else ''

                if cue_type in cue_types:
                    media_url = media_url_match.group(1).strip() if media_url_match else ''
                    media_items.append(MediaListItem(
                        segmentSlug=item.slug or item.title or 'Unknown',
                        segmentOrder=item.order_in_rundown,
                        cueType=cue_type,
                        slug=slug_match.group(1).strip() if slug_match else '',
                        mediaUrl=media_url,
                        assetId=asset_id_match.group(1).strip() if asset_id_match else '',
                        duration=duration_match.group(1).strip() if duration_match else '',
                        hasMissingMedia=not media_url
                    ))

        logger.info(f"Found {len(media_items)} media cues in episode {episode_number}")

        # Generate HTML
        container_scripts_dir = Path(f"/home/episodes/{ep_num}/scripts")
        host_scripts_dir = Path(f"/mnt/sync/disaffected/episodes/{ep_num}/scripts")

        if container_scripts_dir.exists():
            scripts_dir = container_scripts_dir
        elif host_scripts_dir.exists():
            scripts_dir = host_scripts_dir
        else:
            host_scripts_dir.mkdir(parents=True, exist_ok=True)
            scripts_dir = host_scripts_dir

        html_content = _generate_media_list_html(ep_num, media_items)

        html_path = scripts_dir / f"{ep_num}-MEDIA-LIST.html"
        html_path.write_text(html_content, encoding='utf-8')

        # Generate Markdown
        md_content = _generate_media_list_markdown(ep_num, media_items)
        md_path = scripts_dir / f"{ep_num}-MEDIA-LIST.md"
        md_path.write_text(md_content, encoding='utf-8')

        logger.info(f"Generated media list Markdown: {md_path}")

        # Convert to PDF
        pdf_path = scripts_dir / f"{ep_num}-MEDIA-LIST.pdf"
        pdf_generated = _convert_html_to_pdf(html_path, pdf_path, ep_num, "Media List")

        return ScriptGenerationResponse(
            success=True,
            output_path=str(pdf_path) if pdf_generated else str(html_path),
            html_path=str(html_path),
            pdf_path=str(pdf_path) if pdf_generated else None,
            md_path=str(md_path),
            episode_number=episode_number,
            item_count=len(media_items)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating media list from DB for episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


def _generate_media_list_html(episode_number: str, media_items: List[MediaListItem]) -> str:
    """Generate HTML content for the media list in chronological order."""
    missing_count = sum(1 for item in media_items if item.hasMissingMedia)
    total_count = len(media_items)

    # Sort items by segment order (chronological)
    sorted_items = sorted(media_items, key=lambda x: x.segmentOrder or 0)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Episode {episode_number} - Media List</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #1976d2, #1565c0);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .stats {{
            display: flex;
            gap: 20px;
        }}
        .stat {{
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 4px;
        }}
        .stat.warning {{
            background: rgba(255,152,0,0.5);
        }}
        .content {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: #424242;
            color: white;
            padding: 12px 10px;
            text-align: left;
            font-size: 0.85rem;
            text-transform: uppercase;
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #eee;
            font-size: 0.9rem;
            vertical-align: middle;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .missing {{
            background: #ffebee !important;
        }}
        .missing td {{
            color: #c62828;
        }}
        .row-num {{
            font-weight: bold;
            color: #666;
            text-align: center;
            width: 40px;
        }}
        .cue-type {{
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.8rem;
            display: inline-block;
            min-width: 40px;
            text-align: center;
        }}
        .cue-type.IMG {{ background: #e3f2fd; color: #1565c0; }}
        .cue-type.GFX {{ background: #f3e5f5; color: #7b1fa2; }}
        .cue-type.SOT {{ background: #e8f5e9; color: #2e7d32; }}
        .cue-type.VO {{ background: #fff3e0; color: #ef6c00; }}
        .cue-type.NAT {{ background: #fce4ec; color: #c2185b; }}
        .cue-type.PKG {{ background: #e0f2f1; color: #00695c; }}
        .cue-type.BUMP {{ background: #fff8e1; color: #f57f17; }}
        .cue-type.STING {{ background: #fbe9e7; color: #d84315; }}
        .cue-type.FSQ {{ background: #e8eaf6; color: #3949ab; }}
        .cue-type.RIF {{ background: #efebe9; color: #5d4037; }}
        .cue-type.DIR {{ background: #eceff1; color: #546e7a; }}
        .slug {{
            font-weight: 500;
        }}
        .segment {{
            color: #666;
            font-size: 0.85rem;
        }}
        .filename {{
            font-family: monospace;
            font-size: 0.85rem;
            word-break: break-all;
        }}
        .filename.missing-file {{
            color: #c62828;
            font-style: italic;
        }}
        .duration {{
            color: #666;
            font-size: 0.85rem;
            text-align: center;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.75rem;
            margin-top: 20px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Episode {episode_number} - Media List</h1>
        <div class="stats">
            <div class="stat">Total Items: {total_count}</div>
            <div class="stat {'warning' if missing_count > 0 else ''}">Missing Media: {missing_count}</div>
        </div>
    </div>

    <div class="content">
        <table>
            <thead>
                <tr>
                    <th style="width: 40px">#</th>
                    <th style="width: 60px">Type</th>
                    <th>Slug</th>
                    <th>Segment</th>
                    <th>Filename</th>
                    <th style="width: 80px">Duration</th>
                </tr>
            </thead>
            <tbody>
"""

    # Add each item in chronological order
    for idx, item in enumerate(sorted_items, 1):
        row_class = 'missing' if item.hasMissingMedia else ''

        # Extract just the filename from the media URL
        filename = ''
        if item.mediaUrl:
            filename = item.mediaUrl.split('/')[-1] if '/' in item.mediaUrl else item.mediaUrl
        else:
            filename = '<span class="missing-file">MISSING</span>'

        html += f"""
                <tr class="{row_class}">
                    <td class="row-num">{idx}</td>
                    <td><span class="cue-type {item.cueType}">{item.cueType}</span></td>
                    <td class="slug">{item.slug or '-'}</td>
                    <td class="segment">{item.segmentSlug}</td>
                    <td class="filename">{filename}</td>
                    <td class="duration">{item.duration or '-'}</td>
                </tr>
"""

    html += """
            </tbody>
        </table>
    </div>
"""

    # Footer
    html += f"""
    <div class="timestamp">
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>
"""

    return html


def _generate_media_list_markdown(episode_number: str, media_items: List[MediaListItem]) -> str:
    """Generate Markdown content for the media list."""
    missing_count = sum(1 for item in media_items if item.hasMissingMedia)
    total_count = len(media_items)

    # Sort items by segment order (chronological)
    sorted_items = sorted(media_items, key=lambda x: x.segmentOrder or 0)

    md_parts = []

    # Header
    md_parts.append(f"# Episode {episode_number} - Media List")
    md_parts.append("")

    # Summary
    md_parts.append("## Summary")
    md_parts.append("")
    md_parts.append(f"- **Total Items:** {total_count}")
    md_parts.append(f"- **Missing Media:** {missing_count}")
    md_parts.append(f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_parts.append("")

    # Table header
    md_parts.append("## Media Items")
    md_parts.append("")
    md_parts.append("| # | Type | Slug | Segment | Filename | Duration |")
    md_parts.append("|---|------|------|---------|----------|----------|")

    # Table rows
    for idx, item in enumerate(sorted_items, 1):
        # Extract just the filename from the media URL
        filename = ''
        if item.mediaUrl:
            filename = item.mediaUrl.split('/')[-1] if '/' in item.mediaUrl else item.mediaUrl
        else:
            filename = '⚠️ MISSING'

        slug = item.slug or '-'
        segment = item.segmentSlug or '-'
        duration = item.duration or '-'

        md_parts.append(f"| {idx} | {item.cueType} | {slug} | {segment} | `{filename}` | {duration} |")

    md_parts.append("")

    # Group by type summary
    md_parts.append("## By Type")
    md_parts.append("")

    type_counts = {}
    for item in media_items:
        type_counts[item.cueType] = type_counts.get(item.cueType, 0) + 1

    for cue_type, count in sorted(type_counts.items()):
        md_parts.append(f"- **{cue_type}:** {count}")

    md_parts.append("")

    # Missing media section (if any)
    if missing_count > 0:
        md_parts.append("## ⚠️ Missing Media")
        md_parts.append("")
        for item in sorted_items:
            if item.hasMissingMedia:
                md_parts.append(f"- [{item.cueType}] {item.slug} (Segment: {item.segmentSlug})")
        md_parts.append("")

    return '\n'.join(md_parts)


@router.get("/available-formats")
async def get_available_formats(
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """
    Get list of available script formats and presets.
    """
    return {
        "presets": [
            {
                "id": "host_full",
                "name": "Host Script (Full)",
                "description": "Complete script with all cues, images, SOT thumbnails, and production info. Large readable text.",
                "endpoint": "/scripts/generate/{episode_number}?preset=host_full",
                "status": "available",
                "features": ["Cover page", "Block headers", "Segment headers", "Images rendered", "SOT thumbnails", "FSQ quotes", "Speaker tags", "Page numbers"]
            },
            {
                "id": "host_clean",
                "name": "Host Script (Clean)",
                "description": "Teleprompter-friendly format. Spoken text only with minimal cue markers. Extra large text for easy reading.",
                "endpoint": "/scripts/generate/{episode_number}?preset=host_clean",
                "status": "available",
                "features": ["Cover page", "Block headers", "Segment headers", "Minimal cue markers", "Extra large text (20pt)", "Speaker tags", "Page numbers"]
            },
            {
                "id": "production",
                "name": "Production Rundown",
                "description": "Technical rundown with compact cue details, timing, and media references. Smaller text for density.",
                "endpoint": "/scripts/generate/{episode_number}?preset=production",
                "status": "available",
                "features": ["Cover page", "Block headers", "Segment headers", "Compact cue info", "Media paths", "Duration info", "Page numbers"]
            }
        ],
        "other_formats": [
            {
                "id": "media-list",
                "name": "Media List",
                "description": "List of all media cues with URLs, grouped by type. Highlights missing media.",
                "endpoint": "/scripts/media-list/{episode_number}",
                "status": "available"
            }
        ]
    }


@router.get("/episode/{episode_number}/generated")
async def list_generated_scripts(
    episode_number: str,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """
    List all generated documents for an episode (scripts, PDFs, etc.).
    Returns only the latest version of each document type, with past revisions nested.
    """
    ep_num = episode_number.zfill(4)

    # Try container path first, then host path
    container_scripts_dir = Path(f"/home/episodes/{ep_num}/scripts")
    host_scripts_dir = Path(f"/mnt/sync/disaffected/episodes/{ep_num}/scripts")

    if container_scripts_dir.exists():
        scripts_dir = container_scripts_dir
    elif host_scripts_dir.exists():
        scripts_dir = host_scripts_dir
    else:
        return {
            "episode_number": episode_number,
            "documents": [],
            "message": "No scripts directory found"
        }

    all_files = []

    # Also check scripts/current/ subdirectory
    current_dir = scripts_dir / "current"
    dirs_to_scan = [scripts_dir]
    if current_dir.exists():
        dirs_to_scan.append(current_dir)

    # List all files in scripts directories (excluding subdirectories like resources/)
    for scan_dir in dirs_to_scan:
        for file in scan_dir.iterdir():
            # Skip directories (like resources/)
            if file.is_dir():
                continue

            # Determine document type from filename
            doc_type = "unknown"
            if "HOST-FULL" in file.name:
                doc_type = "host_full"
            elif "HOST-CLEAN" in file.name:
                doc_type = "host_clean"
            elif "PRODUCTION" in file.name:
                doc_type = "production"
            elif "HOST-SCRIPT" in file.name:
                doc_type = "host_script"  # Legacy naming
            elif "MEDIA-LIST" in file.name:
                doc_type = "media_list"

            # Extract revision number from filename (e.g., "0257-HOST-FULL-20260120-r3.pdf" -> 3)
            revision = 1
            rev_match = re.search(r'-r(\d+)\.', file.name)
            if rev_match:
                revision = int(rev_match.group(1))

            # Get file stats
            stats = file.stat()
            modified_dt = datetime.fromtimestamp(stats.st_mtime)

            # Build URL for frontend access
            if scan_dir == current_dir:
                url_path = f"/episodes/{ep_num}/scripts/current/{file.name}"
            else:
                url_path = f"/episodes/{ep_num}/scripts/{file.name}"

            all_files.append({
                "filename": file.name,
                "type": doc_type,
                "format": file.suffix.lstrip('.'),
                "path": str(file),
                "url": url_path,
                "size": stats.st_size,
                "size_formatted": _format_file_size(stats.st_size),
                "modified": stats.st_mtime,
                "modified_formatted": modified_dt.strftime("%Y-%m-%d %H:%M"),
                "revision": revision
            })

    # Group files by type AND format (so PDF and HTML are separate)
    grouped = {}
    for doc in all_files:
        key = f"{doc['type']}_{doc['format']}"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(doc)

    # For each group, sort by revision (highest first) and modification time
    documents = []
    for key, docs in grouped.items():
        # Sort by revision descending, then by modification time descending
        docs.sort(key=lambda x: (x["revision"], x["modified"]), reverse=True)

        # Latest is the first one
        latest = docs[0]

        # Past revisions are all the others
        past_revisions = docs[1:] if len(docs) > 1 else []

        # Add past revisions to the latest document
        latest["pastRevisions"] = past_revisions

        documents.append(latest)

    # Sort final list by type for consistent display order
    type_order = ["host_full", "host_clean", "production", "host_script", "media_list", "unknown"]
    format_order = ["pdf", "html", "txt"]

    def sort_key(doc):
        type_idx = type_order.index(doc["type"]) if doc["type"] in type_order else 99
        format_idx = format_order.index(doc["format"]) if doc["format"] in format_order else 99
        return (type_idx, format_idx)

    documents.sort(key=sort_key)

    return {
        "episode_number": episode_number,
        "scripts_dir": str(scripts_dir),
        "documents": documents,
        "count": len(documents)
    }


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _convert_html_to_pdf(html_path: Path, pdf_path: Path, episode_number: str, doc_type: str) -> bool:
    """
    Convert HTML to PDF with page numbers using wkhtmltopdf.

    Args:
        html_path: Path to the HTML file
        pdf_path: Path for the output PDF
        episode_number: Episode number for footer
        doc_type: Document type (e.g., "Media List", "Host Script")

    Returns:
        True if PDF was generated successfully, False otherwise.
    """
    # Check if wkhtmltopdf is available
    wkhtmltopdf = shutil.which('wkhtmltopdf')
    if not wkhtmltopdf:
        logger.warning("wkhtmltopdf not found - skipping PDF generation")
        return False

    try:
        # Build wkhtmltopdf command with page numbers
        footer_left = f"Episode {episode_number} - {doc_type}"
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


@router.get("/ipad-scroll/{episode_number}")
async def get_ipad_scroll_content(
    episode_number: str,
    preset: ScriptPresetEnum = Query(ScriptPresetEnum.host_full, description="Script preset"),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """
    Get compiled host script content optimized for iPad scroll view.

    Returns the same compiled content as PDF generation but as structured data
    for rendering in a responsive, touch-friendly web view.

    **Response includes:**
    - episode_info: Episode metadata (title, number, date, guest, etc.)
    - blocks: List of script blocks with compiled HTML content
    - html_content: Full compiled HTML (for direct rendering if needed)
    """
    from services.host_script_generator import (
        generate_host_script,
        _get_episode_info,
        _detect_blocks,
        _collect_media_resources,
        _build_transcription_cache,
        _generate_html
    )

    db = SessionLocal()

    try:
        # Validate preset
        try:
            from services.host_script_generator import ScriptPreset as GeneratorPreset
            script_preset = GeneratorPreset(preset.value)
        except ValueError:
            from services.host_script_generator import ScriptPreset as GeneratorPreset
            script_preset = GeneratorPreset.HOST_FULL

        # Find episode
        episode = db.query(Episode).filter(
            Episode.episode_number == int(episode_number)
        ).first()

        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found")

        # Get rundown
        rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
        if not rundown:
            raise HTTPException(status_code=404, detail=f"No rundown found for episode {episode_number}")

        # Get all rundown items ordered by position
        items = db.query(RundownItem).filter(
            RundownItem.rundown_id == rundown.id
        ).order_by(RundownItem.order_in_rundown).all()

        if not items:
            raise HTTPException(status_code=404, detail=f"No rundown items found for episode {episode_number}")

        # Get episode metadata
        episode_info = _get_episode_info(episode, db, items)

        # Create temporary resources path for media collection
        ep_num_padded = episode_number.zfill(4)
        container_path = Path(f"/home/episodes/{ep_num_padded}/scripts/current")
        host_path = Path(f"/mnt/sync/disaffected/episodes/{ep_num_padded}/scripts/current")
        output_path = container_path if container_path.parent.parent.exists() else host_path
        resources_path = output_path / "resources"
        resources_path.mkdir(parents=True, exist_ok=True)

        # Collect media resources
        url_mapping = _collect_media_resources(items, resources_path, ep_num_padded)

        # Build transcription cache
        transcription_cache = _build_transcription_cache(items, db)

        # Detect blocks
        blocks = _detect_blocks(items)

        # Generate HTML content
        html_content = _generate_html(episode_info, blocks, script_preset, url_mapping, transcription_cache)

        # Fix relative image/resource paths to absolute URLs for web viewing
        # Replace resources/ with /episodes/{episode}/scripts/current/resources/
        html_content = html_content.replace(
            'src="resources/',
            f'src="/episodes/{ep_num_padded}/scripts/current/resources/'
        )
        html_content = html_content.replace(
            "src='resources/",
            f"src='/episodes/{ep_num_padded}/scripts/current/resources/"
        )

        return {
            "success": True,
            "episode_info": episode_info,
            "html_content": html_content,
            "block_count": len(blocks),
            "item_count": len(items),
            "preset": preset.value
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating iPad scroll content for episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
