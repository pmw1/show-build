"""
Announcements API - List and retrieve announcement HTML files
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import List, Dict
import re
from datetime import datetime

router = APIRouter(prefix="/api/announcements", tags=["announcements"])

ANNOUNCEMENTS_DIR = Path("/app/docs/announcements")

@router.get("/")
async def list_announcements() -> List[Dict[str, str]]:
    """List all available announcement HTML files"""
    try:
        if not ANNOUNCEMENTS_DIR.exists():
            return []

        announcements = []

        for html_file in sorted(ANNOUNCEMENTS_DIR.glob("*.html"), reverse=True):
            # Extract metadata from filename: YYYY-MM-DD-title.html
            match = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)\.html', html_file.name)

            if match:
                date_str, title_slug = match.groups()

                # Convert slug to title (replace hyphens with spaces, title case)
                title = title_slug.replace('-', ' ').title()

                announcements.append({
                    "id": html_file.stem,  # filename without extension
                    "title": title,
                    "date": date_str,
                    "filename": html_file.name
                })

        return announcements

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing announcements: {str(e)}")

@router.get("/{announcement_id}")
async def get_announcement(announcement_id: str) -> Dict[str, str]:
    """Get announcement HTML content by ID"""
    try:
        # Find file matching ID (stem)
        html_file = None
        for file in ANNOUNCEMENTS_DIR.glob("*.html"):
            if file.stem == announcement_id:
                html_file = file
                break

        if not html_file or not html_file.exists():
            raise HTTPException(status_code=404, detail="Announcement not found")

        content = html_file.read_text(encoding='utf-8')

        return {
            "id": announcement_id,
            "filename": html_file.name,
            "content": content
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading announcement: {str(e)}")
