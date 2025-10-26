"""
Asset processing service for Celery background processing.
Handles media file processing, optimization, and metadata extraction.
"""
from celery import shared_task
import logging
import os
import subprocess
import json
import tempfile
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def process_media_asset(self, asset_path: str, episode_id: str, options: dict = None):
    """
    Process a media asset file.
    
    Args:
        asset_path: Path to the media file
        episode_id: Episode identifier
        options: Optional processing parameters
    
    Returns:
        dict: Processing results
    """
    try:
        logger.info(f"Starting asset processing for {asset_path} in episode {episode_id}")
        
        # Placeholder for asset processing logic
        # This would integrate with existing media processing tools
        
        if not os.path.exists(asset_path):
            raise FileNotFoundError(f"Asset file not found: {asset_path}")
        
        result = {
            "asset_path": asset_path,
            "episode_id": episode_id,
            "status": "completed",
            "file_size": os.path.getsize(asset_path) if os.path.exists(asset_path) else 0,
            "message": "Asset processing service placeholder"
        }
        
        logger.info(f"Asset processing completed for {asset_path}")
        return result
        
    except Exception as e:
        logger.error(f"Asset processing failed for {asset_path}: {str(e)}")
        self.retry(countdown=60, max_retries=3)

@shared_task
def optimize_episode_assets(episode_id: str):
    """
    Optimize all assets for an episode.
    
    Args:
        episode_id: Episode identifier
        
    Returns:
        dict: Optimization results
    """
    try:
        logger.info(f"Starting asset optimization for episode {episode_id}")
        
        # Placeholder for batch asset optimization
        # This would scan episode directories and process media files
        
        result = {
            "episode_id": episode_id,
            "status": "completed",
            "assets_processed": 0,
            "message": "Episode asset optimization placeholder"
        }
        
        logger.info(f"Asset optimization completed for episode {episode_id}")
        return result
        
    except Exception as e:
        logger.error(f"Asset optimization failed for episode {episode_id}: {str(e)}")
        raise

@shared_task
def extract_asset_metadata(asset_path: str):
    """
    Extract metadata from a media asset.
    
    Args:
        asset_path: Path to the media file
        
    Returns:
        dict: Extracted metadata
    """
    try:
        logger.info(f"Extracting metadata from {asset_path}")
        
        if not os.path.exists(asset_path):
            raise FileNotFoundError(f"Asset file not found: {asset_path}")
        
        # Placeholder for metadata extraction
        # This would use tools like ffprobe for media files
        
        result = {
            "asset_path": asset_path,
            "metadata": {
                "file_size": os.path.getsize(asset_path),
                "file_extension": os.path.splitext(asset_path)[1],
                "extracted": False  # Placeholder
            },
            "status": "completed"
        }
        
        logger.info(f"Metadata extraction completed for {asset_path}")
        return result

    except Exception as e:
        logger.error(f"Metadata extraction failed for {asset_path}: {str(e)}")
        raise


@shared_task(bind=True, name='services.asset_processing.generate_fsq_png')
def generate_fsq_png(
    self,
    episode_id: str,
    quote: str,
    attribution: str,
    slug: str,
    asset_id: str,
    alignment: str = 'center',
    font_family: str = 'serif',
    font_size: int = 70,
    duration: str = '00:00:05:00'
):
    """
    Generate FSQ (Full Screen Quote) PNG asset using Celery background processing.

    This task can run on any worker machine (local or remote Windows worker).

    Args:
        episode_id: Episode identifier (e.g., '0246')
        quote: The quote text
        attribution: Source attribution (e.g., '1 Corinthians 14:34-35')
        slug: URL-safe slug for filename
        asset_id: AssetID for tracking
        alignment: Text alignment ('center', 'left', 'right')
        font_family: Font family ('serif', 'sans-serif', 'monospace')
        font_size: Base font size in pixels
        duration: Timecode duration

    Returns:
        dict: Generation results with asset_path and asset_url
    """
    try:
        logger.info(f"📝 Starting FSQ PNG generation for episode {episode_id}")
        logger.info(f"   Quote: {quote[:50]}...")
        logger.info(f"   Attribution: {attribution}")
        logger.info(f"   Asset ID: {asset_id}")

        # Import ShowBuildPaths here to avoid circular imports
        from core.paths import ShowBuildPaths
        path_manager = ShowBuildPaths()

        # Normalize episode ID
        episode_id = episode_id.zfill(4) if len(episode_id) < 4 else episode_id

        # Setup paths
        episode_dir = path_manager.get_episode_dir(episode_id)
        assets_dir = path_manager.get_asset_type_dir(episode_id, 'images')
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Create temporary JSON file with quote data
        quote_data = {
            "metadata": {
                "episode": episode_id,
                "generated_at": datetime.now().isoformat(),
                "asset_id": asset_id,
                "task_id": self.request.id,
                "worker": self.request.hostname
            },
            "quotes": [
                {
                    "slug": slug,
                    "text": quote,
                    "attribution": attribution,
                    "duration": duration,
                    "metadata": {
                        "align": alignment,
                        "font_family": font_family,
                        "font_size": font_size
                    }
                }
            ]
        }

        # Create temp JSON file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as temp_file:
            json.dump(quote_data, temp_file, indent=2, ensure_ascii=False)
            temp_json_path = temp_file.name

        logger.info(f"   📄 Created temp JSON: {temp_json_path}")

        # Locate render script
        render_script = Path(__file__).parent.parent.parent / "tools" / "render_fsq_png.py"

        if not render_script.exists():
            raise FileNotFoundError(f"FSQ render script not found: {render_script}")

        # Execute rendering
        logger.info(f"   🎨 Executing FSQ renderer...")
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Rendering PNG...', 'progress': 50}
        )

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
            logger.error(f"   ❌ Render failed: {result.stderr}")
            raise RuntimeError(f"FSQ rendering failed: {result.stderr}")

        logger.info(f"   ✅ Render output: {result.stdout}")

        # Find generated PNG
        clean_slug = slug.lower().replace(' ', '-').replace('_', '-')
        expected_filename = f"fsq_{clean_slug}.png"
        asset_path = assets_dir / expected_filename

        if not asset_path.exists():
            # Try to find any PNG that was just created
            png_files = sorted(
                assets_dir.glob("fsq_*.png"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if png_files:
                asset_path = png_files[0]
                logger.info(f"   📁 Found generated PNG: {asset_path.name}")
            else:
                raise FileNotFoundError(
                    f"Generated PNG not found. Expected: {expected_filename}"
                )

        # Generate asset URL
        asset_relative_path = asset_path.relative_to(path_manager.episodes_root)
        asset_url = f"/episodes/{asset_relative_path}"

        file_size = asset_path.stat().st_size

        logger.info(f"   ✅ FSQ PNG generated successfully")
        logger.info(f"   📁 Path: {asset_path}")
        logger.info(f"   🔗 URL: {asset_url}")
        logger.info(f"   📦 Size: {file_size:,} bytes")

        return {
            "success": True,
            "asset_path": str(asset_path),
            "asset_url": asset_url,
            "asset_id": asset_id,
            "episode_id": episode_id,
            "file_size": file_size,
            "filename": asset_path.name,
            "message": f"FSQ PNG generated successfully: {asset_path.name}",
            "task_id": self.request.id,
            "worker": self.request.hostname
        }

    except subprocess.TimeoutExpired:
        logger.error(f"   ⏱️ FSQ rendering timed out after 30 seconds")
        self.retry(countdown=60, max_retries=2)
    except Exception as e:
        logger.error(f"   ❌ Error generating FSQ PNG: {e}")
        import traceback
        traceback.print_exc()
        # Retry with exponential backoff
        self.retry(countdown=30, max_retries=2)