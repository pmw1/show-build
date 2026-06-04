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
    priority: str = 'normal',
    existing_media_url: str = None
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
        existing_media_url: When set (cue already has a PNG), render to that exact
            file to overwrite in place instead of minting a new slug-based name.

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

        # Output path resolution.
        #
        # REGENERATE-IN-PLACE: if the cue already has a rendered PNG, the
        # frontend hands us its existing media URL. We render to that exact
        # file so the regenerate OVERWRITES it — no slug-renamed orphan, and
        # the cue's stored mediaUrl never has to change. The asset URL is
        # always "/episodes/{path-relative-to-episodes_root}", so we reverse
        # that mapping. A path-traversal guard keeps the resolved file inside
        # this episode's quotes/ dir; if anything looks off we fall through to
        # fresh naming rather than writing somewhere unexpected.
        output_path = None
        if existing_media_url:
            try:
                rel = existing_media_url.split('?', 1)[0]  # drop cache-buster
                rel = rel.lstrip('/')
                if rel.startswith('episodes/'):
                    rel = rel[len('episodes/'):]
                candidate = (path_manager.episodes_root / rel).resolve()
                if str(candidate).startswith(str(assets_dir.resolve()) + '/') \
                        and candidate.suffix.lower() == '.png':
                    output_path = candidate
                    logger.info(f"   ♻️  Regenerate-in-place → {output_path}")
                else:
                    logger.warning(
                        f"   ⚠️ existing_media_url {existing_media_url!r} resolved "
                        f"outside quotes dir ({candidate}); using fresh name"
                    )
            except Exception as url_err:
                logger.warning(f"   ⚠️ Could not resolve existing_media_url "
                               f"{existing_media_url!r}: {url_err}; using fresh name")

        if output_path is None:
            # Fresh name (first-time generation or unresolvable existing URL)
            clean_slug = slug.lower().replace(' ', '-').replace('_', '-')
            # Remove any non-alphanumeric characters except hyphens
            clean_slug = re.sub(r'[^\w\-]', '', clean_slug)

            if enumerator:
                output_filename = f"{enumerator}-{clean_slug}.png"
            else:
                output_filename = f"fsq_{clean_slug}.png"

            output_path = assets_dir / output_filename

        output_filename = output_path.name

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
    title_font_size: int = None,
    line_spacing: int = 30,
    box_height: int = 80,
    box_opacity: int = 75,
    vertical_offset: int = 0,
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

        # Calculate black bar area from slider values. box_height is the
        # bar's % of canvas height; the bar is symmetric around vertical
        # center. box_opacity is 0-100 -> PIL alpha 0-255.
        bh_pct = max(0, min(100, int(box_height or 80)))
        bar_height = int(height * bh_pct / 100)
        bar_top = (height - bar_height) // 2
        bar_bottom = bar_top + bar_height

        op_pct = max(0, min(100, int(box_opacity or 75)))
        bar_alpha = int(255 * op_pct / 100)

        overlay = Image.new('RGBA', (width, bar_height), (0, 0, 0, bar_alpha))
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

        # Scale font sizes for 1080p (input is preview/modal scale).
        # Title size: explicit slider value if provided, else legacy
        # 1.3x body default.
        scaled_font_size = int(font_size * 2.5)
        if title_font_size and title_font_size > 0:
            scaled_title_size = int(title_font_size * 2.5)
        else:
            scaled_title_size = int(scaled_font_size * 1.3)

        for font_path in font_paths:
            try:
                body_font = ImageFont.truetype(font_path, scaled_font_size)
                title_font = ImageFont.truetype(font_path, scaled_title_size)
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
        text_area_width = width - (padding_x * 2)

        # Alignment mapping
        align_map = {
            'left': 'left',
            'center': 'center',
            'right': 'right'
        }
        text_align = align_map.get(alignment, 'center')

        # Pre-compute wrapped lines and total block height so the entire
        # title+body block can be vertically centered within the black bar
        # and then shifted as a unit by vertical_offset.
        title_lines = _wrap_text(title, title_font, text_area_width, draw) if title else []
        body_lines = _wrap_text(body, body_font, text_area_width, draw)

        # Inter-line gap derived from the spacing slider (% of body font).
        ls_pct = max(0, min(100, int(line_spacing or 30)))
        line_gap = int(scaled_font_size * ls_pct / 100)
        title_block_h = 0
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            title_block_h += (bbox[3] - bbox[1]) + line_gap
        # Title-body gap scales with the same spacing slider but a bit
        # larger so the title still feels separated from the body.
        title_body_gap = int(scaled_font_size * (ls_pct + 20) / 100) if title_lines else 0
        body_block_h = 0
        for line in body_lines:
            bbox = draw.textbbox((0, 0), line, font=body_font)
            body_block_h += (bbox[3] - bbox[1]) + line_gap
        total_block_h = title_block_h + title_body_gap + body_block_h

        # Clamp vertical_offset to [-40, 40] so callers can't shove text
        # outside the black bar.
        v_offset_pct = max(-40, min(40, int(vertical_offset or 0)))
        v_offset_px = int(bar_height * v_offset_pct / 100)

        # Start y = top of vertically-centered block, plus the offset shift.
        current_y = bar_top + (bar_height - total_block_h) // 2 + v_offset_px

        # Draw title if present
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
            current_y += line_height + line_gap

        if title_lines:
            current_y += title_body_gap

        # Draw body text
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
            current_y += line_height + line_gap

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


@shared_task(bind=True, name='services.asset_processing.convert_thumbnail_to_png')
def convert_thumbnail_to_png(self, source_path: str, episode_id: str):
    """
    Convert a non-PNG thumbnail image to PNG format.

    Converts the source file to PNG and removes the original.

    Args:
        source_path: Absolute path to the source image file
        episode_id: Episode identifier for logging

    Returns:
        dict: Conversion result with new path and URL
    """
    from PIL import Image

    try:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source thumbnail not found: {source_path}")

        logger.info(f"Converting thumbnail to PNG: {source.name} (episode {episode_id})")

        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Converting to PNG...',
                'progress': 30,
                'episode_id': episode_id,
                'source': source.name
            }
        )

        # Build output path: same name but .png extension
        png_path = source.with_suffix('.png')

        # Convert using Pillow
        with Image.open(source) as img:
            # Convert to RGBA if needed for PNG transparency support
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
            img.save(png_path, 'PNG', optimize=True)

        if not png_path.exists():
            raise FileNotFoundError(f"PNG conversion failed - output not found: {png_path}")

        # Remove original non-PNG file
        if source.suffix.lower() != '.png':
            source.unlink()
            logger.info(f"Removed original: {source.name}")

        # Build URL
        from core.paths import ShowBuildPaths
        path_manager = ShowBuildPaths()
        relative_path = png_path.relative_to(path_manager.episodes_root)
        new_url = f"/episodes/{relative_path}"

        file_size = png_path.stat().st_size

        logger.info(f"Thumbnail converted to PNG: {png_path.name} ({file_size:,} bytes)")

        return {
            "success": True,
            "source_path": source_path,
            "png_path": str(png_path),
            "png_url": new_url,
            "filename": png_path.name,
            "file_size": file_size,
            "episode_id": episode_id,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Thumbnail PNG conversion failed: {e}")
        import traceback
        traceback.print_exc()
        self.retry(countdown=10, max_retries=2, exc=e)


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
