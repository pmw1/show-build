"""Legacy and deprecated endpoints — preserved for backward compatibility."""

import os
import logging
import yaml

from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from database import get_db
from utils.frontmatter_parser import parse_markdown_file
from utils.validator import validate_front_matter
from auth.utils import get_current_user_or_key
from enhanced_reorder import reorder_rundown_with_rename

logger = logging.getLogger(__name__)

router = APIRouter(tags=["legacy"])


class ReorderRequest(BaseModel):
    segments: list[dict]


class NewRundownItem(BaseModel):
    title: str = Field(..., description="Title of the rundown item")
    type: str = Field(..., description="Type of rundown item (segment, promo, advert, etc.)")
    slug: str = Field(..., description="Short slug for the item")
    duration: Optional[str] = Field("00:00:30", description="Estimated duration")
    description: Optional[str] = Field("", description="Description of the item")
    priority: Optional[str] = Field("", description="Priority level")
    guests: Optional[str] = Field("", description="Guests for this item")
    tags: Optional[str] = Field("", description="Tags for this item")


@router.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <html>
      <head>
        <title>Show Builder API</title>
        <style>
          body { font-family: sans-serif; margin: 2em; }
          code { background: #f0f0f0; padding: 2px 4px; border-radius: 4px; }
          h2 { margin-top: 1.5em; }
        </style>
      </head>
      <body>
        <h1>Show Builder API</h1>
        <p>This server powers the Disaffected Rundown Builder.</p>
        <p>See <code>/docs</code> for API documentation.</p>
      </body>
    </html>
    """


@router.get("/outline", response_class=HTMLResponse)
async def show_outline():
    """Temporary route to display show outline HTML"""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Show Outline (Highlighted)</title>
<style>
  :root{
    --bg:#0b0d10;
    --card:#141820;
    --text:#e8eef5;
    --muted:#a8b3c0;
    --accent:#ffd54a;
    --rule:#222833;
  }
  html,body{margin:0;padding:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,Roboto,Inter,Helvetica,Arial,sans-serif;line-height:1.45}
  .wrap{max-width:920px;margin:32px auto;padding:0 20px 64px}
  h1,h2,h3{line-height:1.2;margin:0 0 12px}
  h1{font-size:28px;margin-top:8px}
  h2{font-size:22px;margin-top:24px;color:var(--text)}
  h3{font-size:18px;margin-top:18px;color:var(--text)}
  p{margin:8px 0;color:var(--muted)}
  ul{margin:8px 0 16px 20px}
  li{margin:6px 0}
  mark{background:var(--accent);color:#111;padding:0 .18em;border-radius:.2em}
  .card{background:var(--card);border:1px solid var(--rule);border-radius:12px;padding:18px;margin:16px 0}
  .note{font-size:13px;color:var(--muted)}
  .kicker{font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-size:12px;margin-bottom:6px}
  .hr{height:1px;background:var(--rule);margin:24px 0}
</style>
</head>
<body>
  <div class="wrap">
    <h1>Phone Call Brainstorm &rarr; Show Episode (Tight Outline)</h1>
    <p class="note">This is a placeholder outline page.</p>
  </div>
</body>
</html>
"""
    return html


@router.get("/show-info")
@router.get("/api/show-info")
async def get_show_info():
    """Returns basic information about the show."""
    return {
        "show_title": "Disaffected",
        "show_description": "A show about current events and technology.",
        "episodes_base_path": "/home/episodes"
    }


@router.get("/episodes")
async def list_episodes(db: Session = Depends(get_db)):
    """
    LEGACY: Lists all available episodes by scanning the /home/episodes directory.
    Prefer /api/episodes from episodes_router instead.
    """
    base_path = "/home/episodes"
    if not os.path.isdir(base_path):
        logging.error(f"Episodes base path not found: {base_path}")
        raise HTTPException(status_code=500, detail="Episodes directory not configured.")

    episodes = []
    for item in sorted(os.listdir(base_path), reverse=True):
        episode_path = os.path.join(base_path, item)
        if not os.path.isdir(episode_path):
            continue

        info_path = os.path.join(episode_path, "info.md")

        title = f"Episode {item}"
        airdate = None
        status = "unknown"
        asset_id = None

        if os.path.exists(info_path):
            metadata = None
            try:
                metadata, _ = parse_markdown_file(info_path)

                if metadata and isinstance(metadata, dict):
                    title = metadata.get("title", title)
                    airdate = metadata.get("airdate")
                    status = metadata.get("status", "unknown")
                    asset_id = metadata.get("AssetID")
                elif metadata:
                    logging.warning(f"Metadata for episode {item} is not a dictionary. Type: {type(metadata)}. Data: {metadata}")

            except Exception as e:
                logging.warning(f"Could not process info.md for episode {item}: {e}")

        if not asset_id:
            try:
                from models_v2 import Episode
                try:
                    episode_num_int = int(item.lstrip('0')) if item.isdigit() else None
                    if episode_num_int:
                        episode_record = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
                    else:
                        episode_record = None
                except ValueError:
                    episode_record = None
                if episode_record and episode_record.asset_id:
                    asset_id = episode_record.asset_id
            except Exception as e:
                logging.warning(f"Could not query database for episode {item} AssetID: {e}")

        episodes.append({
            "episode_number": item,
            "title": title,
            "airdate": airdate,
            "status": status,
            "asset_id": asset_id
        })

    if not episodes:
        logging.warning(f"No valid episodes found in {base_path}")

    return {"episodes": episodes}


@router.post("/next-id")
async def next_id_legacy_redirect(slug: str = Form(...), type: str = Form(...)):
    """
    DEPRECATED: Use /assetid/generate-legacy instead.
    """
    logging.warning("DEPRECATED: /next-id endpoint used. Migrate to /assetid/generate-legacy")

    try:
        from utils.id import get_next_id
        next_id_value = get_next_id(slug, type)
        return {
            "id": next_id_value,
            "deprecated": True,
            "message": "This endpoint is deprecated. Use /assetid/generate-legacy instead.",
            "migration_url": "/assetid/generate-legacy"
        }
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logging.error(f"Failed to generate ID: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate_asset_id/rundown")
async def generate_rundown_asset_id(
    type: str = Form(...),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Generate AssetID for rundown items - Obsidian plugin compatibility endpoint."""
    try:
        from services.asset_id import AssetIDService

        asset_id = AssetIDService.request_asset_id(
            db=db,
            entity_type="rundown",
            reason="create",
            requested_by=current_user.get("username", current_user.get("client_name", "obsidian_plugin")),
            context={
                "source": "obsidian_plugin",
                "legacy_type": type
            }
        )

        return {"asset_id": asset_id}

    except Exception as e:
        logging.error(f"Failed to generate rundown AssetID: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate AssetID: {str(e)}")


@router.post("/generate_asset_id/cue")
async def generate_cue_asset_id(
    type: str = Form(...),
    media_url: str = Form(None),
    cue_type: str = Form(None),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Generate AssetID for cue blocks - Obsidian plugin compatibility endpoint."""
    try:
        from services.asset_id import AssetIDService

        context = {
            "source": "obsidian_plugin",
            "cue_type": type,
            "legacy_type": type
        }

        if media_url:
            context["media_url"] = media_url
        if cue_type:
            context["specific_cue_type"] = cue_type

        asset_id = AssetIDService.request_asset_id(
            db=db,
            entity_type="cue",
            reason="create",
            requested_by=current_user.get("username", current_user.get("client_name", "obsidian_plugin")),
            context=context
        )

        return {"asset_id": asset_id}

    except Exception as e:
        logging.error(f"Failed to generate cue AssetID: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate AssetID: {str(e)}")


@router.get("/rundown/{episode_number}/debug")
async def debug_rundown(episode_number: str):
    base_path = "/home/episodes"
    episode_path = os.path.join(base_path, episode_number, "rundown")

    debug_info = {
        "episode_number": episode_number,
        "episode_path": episode_path,
        "path_exists": os.path.isdir(episode_path),
        "files": [],
        "errors": []
    }

    if not os.path.isdir(episode_path):
        debug_info["errors"].append(f"Directory does not exist: {episode_path}")
        return debug_info

    all_files = os.listdir(episode_path)
    md_files = [f for f in all_files if f.endswith('.md')]

    debug_info["all_files"] = all_files
    debug_info["md_files"] = md_files

    for file_name in md_files:
        file_path = os.path.join(episode_path, file_name)
        file_info = {
            "filename": file_name,
            "status": "unknown",
            "error": None,
            "has_frontmatter": False,
            "frontmatter_preview": None
        }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            file_info["file_size"] = len(content)
            file_info["starts_with_yaml"] = content.startswith("---")

            if content.startswith("---"):
                file_info["has_frontmatter"] = True
                fm_end = content.find("\n---", 4)
                if fm_end == -1:
                    file_info["error"] = "Front matter block not properly closed"
                    file_info["status"] = "error"
                else:
                    yaml_block = content[4:fm_end]
                    file_info["frontmatter_preview"] = yaml_block[:200] + "..." if len(yaml_block) > 200 else yaml_block

                    try:
                        front_matter = yaml.safe_load(yaml_block)
                        file_info["parsed_yaml"] = True

                        try:
                            validated_metadata = validate_front_matter(front_matter, filename=file_name)
                            file_info["status"] = "valid"
                            file_info["metadata_keys"] = list(validated_metadata.keys()) if validated_metadata else []
                        except Exception as ve:
                            file_info["status"] = "validation_error"
                            file_info["error"] = str(ve)

                    except Exception as ye:
                        file_info["status"] = "yaml_error"
                        file_info["error"] = f"YAML parsing error: {str(ye)}"
            else:
                file_info["error"] = "No YAML front matter found"
                file_info["status"] = "no_frontmatter"

        except Exception as e:
            file_info["status"] = "file_error"
            file_info["error"] = f"File reading error: {str(e)}"

        debug_info["files"].append(file_info)

    return debug_info


@router.post("/rundown/{episode_number}/reorder")
async def reorder_rundown(episode_number: str, payload: ReorderRequest):
    """Reorder rundown items and rename files to match their new order."""
    return await reorder_rundown_with_rename(episode_number, payload.dict())


@router.get("/episodes/{episode_number}/info")
async def get_episode_info(episode_number: str, current_user: dict = Depends(get_current_user_or_key)):
    """Get episode information from info.md file"""
    base_path = "/home/episodes"
    info_path = os.path.join(base_path, episode_number, "info.md")

    if not os.path.exists(info_path):
        raise HTTPException(
            status_code=404,
            detail=f"Episode info file not found: {info_path}"
        )

    try:
        with open(info_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 2:
                frontmatter_text = parts[1].strip()
                body = parts[2].strip() if len(parts) > 2 else ""

                frontmatter = yaml.safe_load(frontmatter_text) or {}

                return {
                    "episode_number": episode_number,
                    "info": frontmatter,
                    "body": body
                }

        return {
            "episode_number": episode_number,
            "info": {},
            "body": content
        }

    except Exception as e:
        logging.error(f"Failed to read episode info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read episode info: {str(e)}"
        )


@router.get("/protected-endpoint")
async def protected_route(current_user: dict = Depends(get_current_user_or_key)):
    return {
        "message": "Access granted to protected endpoint",
        "user": current_user
    }


@router.post("/secured-route")
async def secured_route(
    payload: dict,
    current_user: dict = Depends(get_current_user_or_key)
):
    return {
        "message": "Secured operation successful",
        "user": current_user,
        "data": payload
    }
