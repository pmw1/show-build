"""
FSQ Asset Generation Router
Automatically generates PNG graphics for Full Screen Quote cues
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
import subprocess
import json
import tempfile
from datetime import datetime

from auth.router import get_current_user_or_key
from core.paths import ShowBuildPaths

router = APIRouter()
path_manager = ShowBuildPaths()


class FSQAssetRequest(BaseModel):
    episode_id: str
    quote: str
    source: str
    style: str = "centered"
    slug: str
    asset_id: str
    duration: str = "00:00:05:00"
    timestamp: Optional[str] = None
    description: Optional[str] = None


class FSQAssetResponse(BaseModel):
    success: bool
    asset_path: str
    asset_url: str
    message: str


@router.post("/generate", response_model=FSQAssetResponse)
async def generate_fsq_asset(
    request: FSQAssetRequest,
    current_user=Depends(get_current_user_or_key)
):
    """
    Generate FSQ PNG asset automatically

    Process:
    1. Create temporary JSON with quote data
    2. Call render_fsq_png.py tool
    3. Move generated PNG to episode assets
    4. Return asset path/URL
    """
    try:
        print(f"📝 Generating FSQ asset for episode {request.episode_id}")
        print(f"   Quote: {request.quote[:50]}...")
        print(f"   Source: {request.source}")
        print(f"   Asset ID: {request.asset_id}")

        # Normalize episode ID
        episode_id = request.episode_id.zfill(4) if len(request.episode_id) < 4 else request.episode_id

        # Setup paths using ShowBuildPaths
        episode_dir = path_manager.get_episode_dir(episode_id)
        assets_dir = path_manager.get_asset_type_dir(episode_id, 'quotes')
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Create temporary JSON file with quote data
        quote_data = {
            "metadata": {
                "episode": episode_id,
                "generated_at": datetime.now().isoformat(),
                "asset_id": request.asset_id
            },
            "quotes": [
                {
                    "slug": request.slug,
                    "text": request.quote,
                    "attribution": request.source,
                    "duration": request.duration,
                    "metadata": {
                        "align": request.style,
                        "timestamp": request.timestamp or "",
                        "description": request.description or ""
                    }
                }
            ]
        }

        # Create temp JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            json.dump(quote_data, temp_file, indent=2, ensure_ascii=False)
            temp_json_path = temp_file.name

        print(f"   📄 Created temp JSON: {temp_json_path}")

        # Call render_fsq_png.py tool
        render_script = Path(__file__).parent.parent / "tools" / "render_fsq_png.py"

        if not render_script.exists():
            raise HTTPException(
                status_code=500,
                detail=f"FSQ render script not found: {render_script}"
            )

        # Execute rendering
        print(f"   🎨 Executing FSQ renderer...")
        result = subprocess.run(
            [
                "python3",
                str(render_script),
                "--json", temp_json_path,
                "--output", str(assets_dir),
                "--width", "1920",
                "--height", "1080"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Clean up temp file
        Path(temp_json_path).unlink(missing_ok=True)

        if result.returncode != 0:
            print(f"   ❌ Render failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"FSQ rendering failed: {result.stderr}"
            )

        print(f"   ✅ Render output: {result.stdout}")

        # Find generated PNG
        clean_slug = request.slug.lower().replace(' ', '-').replace('_', '-')
        expected_filename = f"fsq_{clean_slug}.png"
        asset_path = assets_dir / expected_filename

        if not asset_path.exists():
            # Try to find any PNG that was just created
            png_files = sorted(assets_dir.glob("fsq_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            if png_files:
                asset_path = png_files[0]
                print(f"   📁 Found generated PNG: {asset_path.name}")
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Generated PNG not found. Expected: {expected_filename}"
                )

        # Generate asset URL
        asset_relative_path = asset_path.relative_to(path_manager.episodes_root)
        asset_url = f"/episodes/{asset_relative_path}"

        print(f"   ✅ Asset generated successfully")
        print(f"   📁 Path: {asset_path}")
        print(f"   🔗 URL: {asset_url}")

        return FSQAssetResponse(
            success=True,
            asset_path=str(asset_path),
            asset_url=asset_url,
            message=f"FSQ asset generated successfully: {asset_path.name}"
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="FSQ rendering timed out after 30 seconds"
        )
    except Exception as e:
        print(f"   ❌ Error generating FSQ asset: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate FSQ asset: {str(e)}"
        )


@router.post("/regenerate/{asset_id}", response_model=FSQAssetResponse)
async def regenerate_fsq_asset(
    asset_id: str,
    request: FSQAssetRequest,
    current_user=Depends(get_current_user_or_key)
):
    """Regenerate an existing FSQ asset with updated data"""
    return await generate_fsq_asset(request, current_user)
