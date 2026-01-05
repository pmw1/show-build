"""
Script Generation Router - API endpoints for generating various script formats.

Supports:
- Host script (for host/talent to read from)
- Media list (list of all media cues)
- Teleprompter format (future)
- Director script (future)
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from auth.utils import get_current_user_or_key
from services.host_script_generator import generate_host_script
from pathlib import Path
from datetime import datetime
import logging
import subprocess
import shutil

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scripts", tags=["Scripts"])


class ScriptGenerationResponse(BaseModel):
    """Response model for script generation."""
    success: bool
    output_path: Optional[str] = None
    episode_number: Optional[str] = None
    item_count: Optional[int] = None
    block_count: Optional[int] = None
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


@router.post("/host/{episode_number}", response_model=ScriptGenerationResponse)
async def generate_host_script_endpoint(
    episode_number: str,
    output_dir: Optional[str] = Query(None, description="Custom output directory"),
    current_user: dict = Depends(get_current_user_or_key)
) -> ScriptGenerationResponse:
    """
    Generate a host script for an episode.

    The host script is an HTML document optimized for PDF conversion with:
    - Cover page with episode information
    - Block headers (START BLOCK A / END BLOCK A)
    - Segment headers with duration
    - Formatted cue blocks (FSQ, SOT, IMG, GFX)
    - Speaker attribution for dialogue paragraphs

    Block detection:
    - Block A: First content block (before first promo/ad/break)
    - Block B: Next content block after first break region
    - Block C, D, etc.: Continue with same logic

    The script is saved to the episode's scripts/ folder by default.
    """
    try:
        result = generate_host_script(episode_number, output_dir)

        return ScriptGenerationResponse(
            success=result.get("success", False),
            output_path=result.get("output_path"),
            episode_number=result.get("episode_number"),
            item_count=result.get("item_count"),
            block_count=result.get("block_count"),
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


def _generate_media_list_html(episode_number: str, media_items: List[MediaListItem]) -> str:
    """Generate HTML content for the media list."""
    missing_count = sum(1 for item in media_items if item.hasMissingMedia)
    total_count = len(media_items)

    # Group items by cue type
    items_by_type = {}
    for item in media_items:
        cue_type = item.cueType
        if cue_type not in items_by_type:
            items_by_type[cue_type] = []
        items_by_type[cue_type].append(item)

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
        .section {{
            background: white;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section-header {{
            background: #424242;
            color: white;
            padding: 12px 16px;
            border-radius: 8px 8px 0 0;
            font-weight: bold;
        }}
        .section-content {{
            padding: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: #e0e0e0;
            padding: 10px;
            text-align: left;
            font-size: 0.85rem;
            text-transform: uppercase;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #eee;
            font-size: 0.9rem;
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
        .cue-type {{
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
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
        .media-url {{
            font-family: monospace;
            font-size: 0.8rem;
            word-break: break-all;
            max-width: 400px;
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
"""

    # Add section for each cue type
    for cue_type in sorted(items_by_type.keys()):
        items = items_by_type[cue_type]
        type_missing = sum(1 for item in items if item.hasMissingMedia)

        html += f"""
    <div class="section">
        <div class="section-header">
            {cue_type} ({len(items)} items{f', {type_missing} missing' if type_missing > 0 else ''})
        </div>
        <div class="section-content">
            <table>
                <thead>
                    <tr>
                        <th>Segment</th>
                        <th>Slug</th>
                        <th>Media URL</th>
                        <th>Asset ID</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
"""
        for item in items:
            row_class = 'missing' if item.hasMissingMedia else ''
            media_display = item.mediaUrl if item.mediaUrl else '<span style="color:#c62828">MISSING</span>'

            html += f"""
                    <tr class="{row_class}">
                        <td>{item.segmentSlug}</td>
                        <td>{item.slug or '-'}</td>
                        <td class="media-url">{media_display}</td>
                        <td>{item.assetId or '-'}</td>
                        <td>{item.duration or '-'}</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>
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


@router.get("/available-formats")
async def get_available_formats(
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """
    Get list of available script formats.
    """
    return {
        "formats": [
            {
                "id": "host",
                "name": "Host Script",
                "description": "HTML script for host/talent to read from, optimized for PDF conversion",
                "endpoint": "/scripts/host/{episode_number}",
                "status": "available"
            },
            {
                "id": "teleprompter",
                "name": "Teleprompter",
                "description": "Large text format for teleprompter display",
                "endpoint": "/scripts/teleprompter/{episode_number}",
                "status": "planned"
            },
            {
                "id": "director",
                "name": "Director Script",
                "description": "Technical cue sheet for director with timing marks",
                "endpoint": "/scripts/director/{episode_number}",
                "status": "planned"
            },
            {
                "id": "media-list",
                "name": "Media List",
                "description": "List of all media cues with URLs, grouped by type",
                "endpoint": "/scripts/media-list/{episode_number}",
                "status": "available"
            },
            {
                "id": "flat-text",
                "name": "Flat Text",
                "description": "Plain text script without formatting",
                "endpoint": "/scripts/flat-text/{episode_number}",
                "status": "planned"
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

    documents = []

    # List all files in scripts directory (excluding subdirectories like resources/)
    for file in scripts_dir.iterdir():
        # Skip directories (like resources/)
        if file.is_dir():
            continue

        # Determine document type from filename
        doc_type = "unknown"
        if "HOST-SCRIPT" in file.name:
            doc_type = "host_script"
        elif "TELEPROMPTER" in file.name:
            doc_type = "teleprompter"
        elif "DIRECTOR" in file.name:
            doc_type = "director"
        elif "MEDIA-LIST" in file.name:
            doc_type = "media_list"

        # Get file stats
        stats = file.stat()
        modified_dt = datetime.fromtimestamp(stats.st_mtime)

        # Build URL for frontend access
        # The file is served via static mount at /episodes/
        url_path = f"/episodes/{ep_num}/scripts/{file.name}"

        documents.append({
            "filename": file.name,
            "type": doc_type,
            "format": file.suffix.lstrip('.'),
            "path": str(file),
            "url": url_path,
            "size": stats.st_size,
            "size_formatted": _format_file_size(stats.st_size),
            "modified": stats.st_mtime,
            "modified_formatted": modified_dt.strftime("%Y-%m-%d %H:%M")
        })

    # Sort by modification time, newest first
    documents.sort(key=lambda x: x["modified"], reverse=True)

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
