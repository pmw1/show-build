"""
Asset processing service for Celery background processing.
Handles media file processing, optimization, and metadata extraction.

FSQ (Full Screen Quote) Generation:
- Uses FSQPNGRenderer as direct module import (no subprocess)
- Supports priority queues: assets_high, assets, assets_low
- Output: {episode}/assets/quotes/{slug}.png
"""
from celery import shared_task
import logging
import os
from pathlib import Path

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
    font_family: str = 'sans-serif',
    font_size: int = None,
    max_font_size: int = None,
    box_height: int = 80,
    box_opacity: int = 75,
    line_spacing: int = 30,
    attribution_size: int = None,
    max_attribution_size: int = None,
    duration: str = '00:00:05:00',
    enumerator: str = None,
    priority: str = 'normal'
):
    """
    Generate FSQ (Full Screen Quote) PNG asset using Celery background processing.

    This task uses the FSQPNGRenderer directly as an imported module for better
    performance and error handling (no subprocess overhead).

    Font sizing modes:
    - max_font_size only: Auto-fit within box, using max as upper limit (RECOMMENDED)
    - font_size only: Force exact size (may overflow box)
    - Neither: Full auto-sizing (default 12-200px range)

    Args:
        episode_id: Episode identifier (e.g., '0246')
        quote: The quote text
        attribution: Source attribution (e.g., '1 Corinthians 14:34-35')
        slug: URL-safe slug for filename
        asset_id: AssetID for tracking
        alignment: Text alignment ('center', 'left', 'right')
        font_family: Font family ('serif', 'sans-serif')
        font_size: [DEPRECATED] Force exact font size (ignores fitting)
        max_font_size: Maximum font size for auto-fitting (maintains 10% padding)
        box_height: Black overlay height as % of canvas (50-100)
        box_opacity: Black overlay opacity as % (50-100)
        line_spacing: Line spacing as % of font size (10-60)
        attribution_size: [DEPRECATED] Force exact attribution size
        max_attribution_size: Maximum attribution size for auto-fitting
        duration: Timecode duration
        enumerator: Optional enumerator prefix for filename (e.g., "10_05")
        priority: Task priority ('high', 'normal', 'low') - affects queue routing

    Returns:
        dict: Generation results with asset_path and asset_url
    """
    import re

    try:
        logger.info(f"📝 Starting FSQ PNG generation for episode {episode_id}")
        logger.info(f"   Quote: {quote[:50]}...")
        logger.info(f"   Attribution: {attribution}")
        logger.info(f"   Asset ID: {asset_id}")
        logger.info(f"   Priority: {priority}")

        # Import renderer directly - no subprocess needed
        # This provides better performance and error handling
        import sys

        # Try multiple paths for render_fsq_png:
        # 1. /app (Kairo worker layout)
        # 2. project_root/tools (main server layout)
        app_dir = Path('/app')
        tools_dir = Path(__file__).parent.parent.parent / "tools"

        for path in [app_dir, tools_dir]:
            if str(path) not in sys.path and path.exists():
                sys.path.insert(0, str(path))

        from render_fsq_png import FSQPNGRenderer

        # Import ShowBuildPaths here to avoid circular imports
        from core.paths import ShowBuildPaths
        path_manager = ShowBuildPaths()

        # Normalize episode ID
        episode_id = episode_id.zfill(4) if len(episode_id) < 4 else episode_id

        # Setup paths - FSQ assets go to quotes directory
        assets_dir = path_manager.get_asset_type_dir(episode_id, 'quotes')
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Update progress state
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Initializing renderer...',
                'progress': 10,
                'episode_id': episode_id,
                'asset_id': asset_id
            }
        )

        # Create renderer instance with style parameters
        # Support both auto-fitting (max_font_size) and legacy forced sizing (font_size)
        renderer_kwargs = {
            'width': 1920,
            'height': 1080,
            'font_family': font_family,
            'box_height': box_height,
            'box_opacity': box_opacity,
            'line_spacing': line_spacing,
        }

        # Font size handling priority:
        # 1. max_font_size: Auto-fit with upper limit (RECOMMENDED - maintains 10% padding)
        # 2. font_size: Force exact size (legacy - may overflow)
        # 3. Neither: Full auto with defaults (12-200px)
        if max_font_size:
            # Auto-fit mode: Use default min (12px), scaled max
            renderer_kwargs['max_font_size'] = max_font_size
            logger.info(f"   Auto-fit mode: max={max_font_size}px (maintains 10% padding)")
        elif font_size:
            # Legacy forced mode: Set both min and max
            renderer_kwargs['min_font_size'] = font_size
            renderer_kwargs['max_font_size'] = font_size
            logger.info(f"   Forced mode: exact {font_size}px (may overflow)")

        # Attribution size handling (same priority logic)
        if max_attribution_size:
            # Auto-fit attribution with upper limit
            renderer_kwargs['attribution_size'] = None  # Let renderer auto-calculate
            # Note: renderer doesn't have max_attribution_size, so we cap the auto result
            logger.info(f"   Attribution auto-fit: max={max_attribution_size}px")
        elif attribution_size:
            renderer_kwargs['attribution_size'] = attribution_size
            logger.info(f"   Attribution forced: {attribution_size}px")

        renderer = FSQPNGRenderer(**renderer_kwargs)

        # Build output filename
        clean_slug = slug.lower().replace(' ', '-').replace('_', '-')
        # Remove any non-alphanumeric characters except hyphens
        clean_slug = re.sub(r'[^\w\-]', '', clean_slug)

        if enumerator:
            output_filename = f"{enumerator}-{clean_slug}.png"
        else:
            output_filename = f"fsq_{clean_slug}.png"

        output_path = assets_dir / output_filename

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Rendering PNG...',
                'progress': 50,
                'episode_id': episode_id,
                'asset_id': asset_id,
                'filename': output_filename
            }
        )

        logger.info(f"   🎨 Rendering FSQ PNG directly (no subprocess)...")
        logger.info(f"   📁 Output: {output_path}")

        # Render directly using the module
        success = renderer.render_single(
            quote_text=quote,
            attribution=attribution,
            output_path=output_path,
            slug=slug,
            alignment=alignment
        )

        if not success:
            raise RuntimeError(f"FSQ rendering failed for slug: {slug}")

        # Verify file was created
        if not output_path.exists():
            raise FileNotFoundError(f"Generated PNG not found: {output_path}")

        # Generate asset URL
        asset_relative_path = output_path.relative_to(path_manager.episodes_root)
        asset_url = f"/episodes/{asset_relative_path}"

        file_size = output_path.stat().st_size

        logger.info(f"   ✅ FSQ PNG generated successfully")
        logger.info(f"   📁 Path: {output_path}")
        logger.info(f"   🔗 URL: {asset_url}")
        logger.info(f"   📦 Size: {file_size:,} bytes")

        return {
            "success": True,
            "asset_path": str(output_path),
            "asset_url": asset_url,
            "asset_id": asset_id,
            "episode_id": episode_id,
            "file_size": file_size,
            "filename": output_path.name,
            "message": f"FSQ PNG generated successfully: {output_path.name}",
            "task_id": self.request.id,
            "worker": self.request.hostname,
            "priority": priority,
            "render_method": "direct_module"  # Indicates no subprocess was used
        }

    except Exception as e:
        logger.error(f"   ❌ Error generating FSQ PNG: {e}")
        import traceback
        traceback.print_exc()
        # Retry with exponential backoff
        self.retry(countdown=30, max_retries=2, exc=e)


@shared_task(bind=True, name='services.asset_processing.generate_gfx_png')
def generate_gfx_png(
    self,
    episode_id: str,
    gfx_type: str,
    body: str,
    slug: str,
    asset_id: str,
    title: str = None,
    alignment: str = 'center',
    font_family: str = 'sans-serif',
    font_size: int = 25,
    render_mode: str = 'png',
    priority: str = 'normal'
):
    """
    Generate GFX (Graphics) PNG asset using Celery background processing.

    This task generates full-screen text graphics with a black bar overlay
    on a video background frame, similar to FSQ but for general text content.

    Args:
        episode_id: Episode identifier (e.g., '0246')
        gfx_type: Type of GFX ('fullscreen-text')
        body: The main body text
        slug: URL-safe slug for filename
        asset_id: AssetID for tracking
        title: Optional title text (displayed above body)
        alignment: Text alignment ('center', 'left', 'right')
        font_family: Font family ('serif', 'sans-serif', 'monospace')
        font_size: Base font size in pixels
        render_mode: Output mode ('png' or 'video')
        priority: Task priority ('high', 'normal', 'low')

    Returns:
        dict: Generation results with asset_path and asset_url
    """
    import re
    from PIL import Image, ImageDraw, ImageFont

    try:
        logger.info(f"🎨 Starting GFX PNG generation for episode {episode_id}")
        logger.info(f"   GFX Type: {gfx_type}")
        logger.info(f"   Body: {body[:50]}...")
        logger.info(f"   Asset ID: {asset_id}")
        logger.info(f"   Priority: {priority}")

        # Import ShowBuildPaths here to avoid circular imports
        from core.paths import ShowBuildPaths
        path_manager = ShowBuildPaths()

        # Normalize episode ID
        episode_id = episode_id.zfill(4) if len(episode_id) < 4 else episode_id

        # Setup paths - GFX assets go to graphics directory
        assets_dir = path_manager.get_asset_type_dir(episode_id, 'graphics')
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Update progress state
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Initializing renderer...',
                'progress': 10,
                'episode_id': episode_id,
                'asset_id': asset_id
            }
        )

        # Canvas dimensions (1920x1080)
        width = 1920
        height = 1080

        # Create base image with black background
        img = Image.new('RGB', (width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Calculate black bar area (10% top/bottom margin, 80% height)
        bar_top = int(height * 0.10)
        bar_bottom = int(height * 0.90)
        bar_height = bar_bottom - bar_top

        # Draw semi-transparent black bar
        overlay = Image.new('RGBA', (width, bar_height), (0, 0, 0, 191))  # 75% opacity
        img.paste(overlay, (0, bar_top), overlay)

        # Font setup
        font_map = {
            'sans-serif': ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                          '/System/Library/Fonts/Helvetica.ttc',
                          'arial.ttf'],
            'serif': ['/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
                     '/System/Library/Fonts/Times.ttc',
                     'times.ttf'],
            'monospace': ['/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
                         '/System/Library/Fonts/Courier.ttc',
                         'cour.ttf']
        }

        # Try to load font
        font_paths = font_map.get(font_family, font_map['sans-serif'])
        body_font = None
        title_font = None

        # Scale font size for 1080p (input is preview scale)
        scaled_font_size = int(font_size * 2.5)  # Scale up for full HD
        title_font_size = int(scaled_font_size * 1.3)  # Title 30% larger

        for font_path in font_paths:
            try:
                body_font = ImageFont.truetype(font_path, scaled_font_size)
                title_font = ImageFont.truetype(font_path, title_font_size)
                break
            except (IOError, OSError):
                continue

        if not body_font:
            # Fallback to default font
            body_font = ImageFont.load_default()
            title_font = body_font
            logger.warning("   ⚠️ Using default font (truetype fonts not found)")

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Rendering text...',
                'progress': 50,
                'episode_id': episode_id,
                'asset_id': asset_id
            }
        )

        # Text positioning
        padding_x = int(width * 0.08)  # 8% horizontal padding
        padding_y = int(bar_height * 0.15)  # 15% vertical padding within bar
        text_area_width = width - (padding_x * 2)
        text_area_top = bar_top + padding_y

        # Alignment mapping
        align_map = {
            'left': 'left',
            'center': 'center',
            'right': 'right'
        }
        text_align = align_map.get(alignment, 'center')

        # Draw title if present
        current_y = text_area_top
        if title:
            # Word wrap title
            title_lines = _wrap_text(title, title_font, text_area_width, draw)
            for line in title_lines:
                bbox = draw.textbbox((0, 0), line, font=title_font)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]

                if text_align == 'center':
                    x = (width - line_width) // 2
                elif text_align == 'right':
                    x = width - padding_x - line_width
                else:
                    x = padding_x

                draw.text((x, current_y), line, font=title_font, fill='white')
                current_y += line_height + int(scaled_font_size * 0.3)

            # Add space between title and body
            current_y += int(scaled_font_size * 0.5)

        # Draw body text
        body_lines = _wrap_text(body, body_font, text_area_width, draw)
        for line in body_lines:
            bbox = draw.textbbox((0, 0), line, font=body_font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]

            if text_align == 'center':
                x = (width - line_width) // 2
            elif text_align == 'right':
                x = width - padding_x - line_width
            else:
                x = padding_x

            draw.text((x, current_y), line, font=body_font, fill='white')
            current_y += line_height + int(scaled_font_size * 0.3)

        # Build output filename
        clean_slug = slug.lower().replace(' ', '-').replace('_', '-')
        clean_slug = re.sub(r'[^\w\-]', '', clean_slug)
        output_filename = f"gfx_{clean_slug}.png"
        output_path = assets_dir / output_filename

        # Save PNG
        img.save(output_path, 'PNG', optimize=True)

        # Verify file was created
        if not output_path.exists():
            raise FileNotFoundError(f"Generated PNG not found: {output_path}")

        # Generate asset URL
        asset_relative_path = output_path.relative_to(path_manager.episodes_root)
        asset_url = f"/episodes/{asset_relative_path}"

        file_size = output_path.stat().st_size

        logger.info(f"   ✅ GFX PNG generated successfully")
        logger.info(f"   📁 Path: {output_path}")
        logger.info(f"   🔗 URL: {asset_url}")
        logger.info(f"   📦 Size: {file_size:,} bytes")

        return {
            "success": True,
            "asset_path": str(output_path),
            "asset_url": asset_url,
            "asset_id": asset_id,
            "episode_id": episode_id,
            "file_size": file_size,
            "filename": output_path.name,
            "message": f"GFX PNG generated successfully: {output_path.name}",
            "task_id": self.request.id,
            "worker": self.request.hostname,
            "priority": priority,
            "gfx_type": gfx_type
        }

    except Exception as e:
        logger.error(f"   ❌ Error generating GFX PNG: {e}")
        import traceback
        traceback.print_exc()
        # Retry with exponential backoff
        self.retry(countdown=30, max_retries=2, exc=e)


def _wrap_text(text: str, font, max_width: int, draw) -> list:
    """
    Wrap text to fit within max_width.

    Args:
        text: Text to wrap
        font: PIL font object
        max_width: Maximum width in pixels
        draw: ImageDraw object for measuring

    Returns:
        List of wrapped lines
    """
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]

        if line_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines if lines else ['']
