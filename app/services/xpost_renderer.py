"""
X-Post (tweet) GFX renderer — broadcast-ready news-style tweet card.

Renders a GFX/xpost cue (rows in gfx_xpost_cues, captured from the whiteboard)
to two PNGs in {episode}/assets/graphics/:

  gfx_{slug}.png       1920x1080 full-frame: house background + centered tweet
                       card + archival caption. This is what gather-media
                       collects and what the editor preview/download uses.
  gfx_{slug}_key.png   The card (with drop shadow) on a transparent 1080p
                       canvas, for straight alpha keying in vMix.

Original avatar/media bytes are downloaded to assets/graphics/xpost_src/
{asset_id}/ and recorded in xpost_media_local_paths — the provable record of
what the post looked like even if X later deletes it.

Styling comes from display_sequence.style merged over HOUSE_STYLE; the
display_sequence.sequence steps are the (future) animation contract and are
ignored by this static renderer. Only 16:9 is rendered this phase — other
stored aspect ratios log a warning and fall back.

Runs on the dedicated 'xpost' queue (see celery_app.task_routes) consumed by
the bind-mounted xpost-worker service, NOT the baked-image media fleet.
"""
from celery import shared_task
import copy
import json
import logging
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Emoji rendering is best-effort: pilmoji pulls Twemoji images over HTTPS at
# draw time. If the package is missing or the network is down we fall back to
# plain PIL text (emoji render as tofu boxes) — a render must NEVER fail
# because of emoji.
try:
    from pilmoji import Pilmoji
    PILMOJI_AVAILABLE = True
except Exception:  # pragma: no cover - import guard
    PILMOJI_AVAILABLE = False

FONTS_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'fonts'
XPOST_ASSETS_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'xpost'

# Font fallback chains per weight: bundled Inter (Chirp substitute) →
# Liberation (media-gpu images) → DejaVu (root Dockerfile image) → PIL default.
_FONT_CHAINS = {
    'regular': [
        str(FONTS_DIR / 'Inter-Regular.ttf'),
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ],
    'semibold': [
        str(FONTS_DIR / 'Inter-SemiBold.ttf'),
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ],
    'bold': [
        str(FONTS_DIR / 'Inter-Bold.ttf'),
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ],
}

HOUSE_STYLE = {
    # Light theme: the tweet reads black-on-white on a WHITE card — no black
    # slab. The thick white border ring is part of the card silhouette.
    'theme': 'light',
    'avatar_shape': 'circle',
    'card_border': {'width': 10, 'color': '#FFFFFF'},
    # Slim charcoal stroke wrapped around the white ring: keeps the card edge
    # defined over bright keyed video as well as the dark house frame.
    'card_edge': {'width': 4, 'color': '#14181C', 'opacity': 0.85},
    'drop_shadow': {'enabled': True, 'blur': 56, 'opacity': 0.72, 'offset': [0, 16]},
    # The inset bubble: ~80% of frame width, centered, big soft corners,
    # slightly translucent, with a big blurred platform watermark INSIDE the
    # bubble (a watermark outside the card would turn to noise over keyed
    # video).
    'bubble': {
        'width_ratio': 0.80,
        'radius': 28,
        'bg_alpha': 0.97,
        'watermark_opacity': 0.08,
        'watermark_blur': 14,
    },
    'colors': {
        'card_bg': '#FFFFFF',
        'card_fg': '#0F1419',
        'muted': '#536471',
        'accent': '#1D9BF0',
        'frame_bg': '#0E1114',
        'frame_accent': '#C62828',
        # Caption sits on the dark frame background, not the white card.
        'frame_caption': '#8B98A5',
    },
}


# ── small helpers ──────────────────────────────────────────────────────────

def _hex_rgba(hex_color, alpha=255):
    h = (hex_color or '#000000').lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def _merge_style(overrides):
    """HOUSE_STYLE with display_sequence.style laid over it (one level deep)."""
    style = copy.deepcopy(HOUSE_STYLE)
    for key, val in (overrides or {}).items():
        if isinstance(val, dict) and isinstance(style.get(key), dict):
            style[key].update(val)
        else:
            style[key] = val
    return style


def _load_font(weight, size):
    from PIL import ImageFont
    for path in _FONT_CHAINS.get(weight, _FONT_CHAINS['regular']):
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    logger.warning(f"   ⚠️ No truetype font found for weight '{weight}' — using PIL default")
    return ImageFont.load_default()


def _resolve_local_media(url):
    """Map a root-relative served URL to its filesystem path, if local."""
    if not url or not url.startswith('/'):
        return None
    from core.paths import ShowBuildPaths
    mounts = {
        '/pool/': Path('/home/pool'),
        '/repo/': Path('/home/repo'),
        '/episodes/': ShowBuildPaths().episodes_root,
    }
    for prefix, root in mounts.items():
        if url.startswith(prefix):
            candidate = root / url[len(prefix):]
            if candidate.exists():
                return candidate
    return None


def _fetch_image(url, dest_dir, basename):
    """Load an image from a remote URL or a locally-served path.

    The ORIGINAL bytes are always copied into dest_dir (archival). Returns
    (PIL RGBA image, archived path str) or (None, None) on any failure.
    """
    import requests
    from PIL import Image
    if not url:
        return None, None
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        local = _resolve_local_media(url)
        if local:
            ext = local.suffix or '.img'
            dest = dest_dir / f"{basename}{ext}"
            shutil.copyfile(local, dest)
        else:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            ext = Path(url.split('?')[0]).suffix or '.img'
            dest = dest_dir / f"{basename}{ext}"
            dest.write_bytes(resp.content)
        return Image.open(dest).convert('RGBA'), str(dest)
    except Exception as e:
        logger.warning(f"   ⚠️ Could not fetch image {url}: {e}")
        return None, None


def _fetch_avatar(url, dest_dir):
    """Avatar fetch with pbs.twimg size upgrade (_normal → _400x400)."""
    if url and '_normal.' in url:
        img, path = _fetch_image(url.replace('_normal.', '_400x400.'), dest_dir, 'avatar')
        if img:
            return img, path
    return _fetch_image(url, dest_dir, 'avatar')


def _rounded(img, radius):
    """Apply a rounded-corner alpha mask to an RGBA image."""
    from PIL import Image, ImageDraw
    mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1],
                                           radius=radius, fill=255)
    img.putalpha(mask)
    return img


def _avatar_thumb(img, size, shape):
    from PIL import Image, ImageDraw
    img = img.resize((size, size), Image.LANCZOS)
    if shape == 'square':
        return _rounded(img, size // 6)
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    img.putalpha(mask)
    return img


def _fmt_metric(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return None
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".rstrip('0').rstrip('.') + 'M'
    if n >= 1_000:
        return f"{n / 1_000:.1f}".rstrip('0').rstrip('.') + 'K'
    return str(n)


def _fmt_timestamp(dt):
    if not dt:
        return None
    try:
        # "3:41 PM · Jul 22, 2026" — strip the leading zero portably.
        return dt.strftime('%I:%M %p · %b %-d, %Y') if hasattr(dt, 'strftime') else None
    except ValueError:
        return dt.strftime('%I:%M %p · %b %d, %Y').replace(' 0', ' ')


# Rough emoji detector for width correction (FE0F variation selectors are
# stripped before counting so "⚖️" counts once, not twice).
_EMOJI_RE = re.compile(
    '[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\U00002B00-\U00002BFF]'
)


def _text_width(draw, text, font):
    """Measured text width, corrected for emoji.

    PIL measures emoji as narrow (often tofu) glyphs, but Pilmoji draws each
    one ~1 em wide — un-corrected wraps overflow the card edge.
    """
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    if PILMOJI_AVAILABLE:
        emoji_count = len(_EMOJI_RE.findall(text.replace('\ufe0f', '')))
        if emoji_count:
            width += int(emoji_count * font.size * 0.85)
    return width


def _wrap_text(draw, text, font, max_width):
    """Word-wrap honoring explicit newlines. Returns list of lines."""
    lines = []
    for para in (text or '').replace('\\n', '\n').split('\n'):
        words = para.split(' ')
        current = ''
        for word in words:
            trial = f"{current} {word}".strip()
            if _text_width(draw, trial, font) <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _fit_text(draw, text, max_width, max_lines=9, start_size=48, floor_size=34):
    """Auto-shrink: largest size whose wrap fits max_lines; ellipsize at floor.

    Returns (font, lines, line_height).
    """
    size = start_size
    while True:
        font = _load_font('regular', size)
        lines = _wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines or size <= floor_size:
            break
        size -= 2
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip('.…') + '…'
    bbox = draw.textbbox((0, 0), 'Agj', font=font)
    return font, lines, bbox[3] - bbox[1]


def _draw_text(img, draw, xy, text, font, fill):
    """Draw one line of text, with emoji via Pilmoji when available."""
    if PILMOJI_AVAILABLE:
        try:
            with Pilmoji(img) as pilmoji:
                pilmoji.text((int(xy[0]), int(xy[1])), text, fill=fill, font=font)
            return
        except Exception as e:  # network/CDN failure — degrade silently
            logger.debug(f"pilmoji fallback: {e}")
    draw.text(xy, text, font=font, fill=fill)


def _pick_media(row):
    """First photo (or video preview) to show on the card.

    Returns (url, is_video). Prefers structured media_objects; falls back to
    media_urls[0].
    """
    objects = row.xpost_media_objects or []
    if isinstance(objects, str):
        try:
            objects = json.loads(objects)
        except (ValueError, TypeError):
            objects = []
    saw_video = False
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        mtype = (obj.get('type') or '').lower()
        if mtype in ('photo', 'image'):
            url = obj.get('url') or obj.get('media_url') or obj.get('preview_url')
            if url:
                return url, False
        if mtype in ('video', 'animated_gif'):
            saw_video = True
            # Only ever fetch a STILL for the card — obj.url is the .mp4.
            # X API v2 uses preview_image_url; syndication uses preview_url.
            url = obj.get('preview_url') or obj.get('preview_image_url') or obj.get('thumbnail_url')
            if url:
                return url, True
    # media_urls typically holds photo/thumbnail URLs (for videos it's the
    # video thumb), so it doubles as the video-preview fallback.
    urls = row.xpost_media_urls or []
    if isinstance(urls, str):
        try:
            urls = json.loads(urls)
        except (ValueError, TypeError):
            urls = []
    if urls:
        return urls[0], saw_video
    return None, False


# ── card renderer ──────────────────────────────────────────────────────────

def _display_text(row):
    """Tweet text prepped for the screen: real newlines, trailing t.co link
    junk stripped (the archive keeps the verbatim text)."""
    text = (row.xpost_post_text or '').replace('\\n', '\n').strip()
    text = re.sub(r'(?:\s*https?://t\.co/\w+)+\s*$', '', text).strip()
    return text


def _render_card(row, style, avatar_img, media_img, media_is_video):
    """Compose the inset tweet bubble as an RGBA image.

    A single centered bubble at bubble.width_ratio of the 1920 frame, big
    soft corners, slightly translucent, faint X watermark inside — designed
    to sit over a transparent canvas and key cleanly in vMix.
    """
    from PIL import Image, ImageDraw

    colors = style['colors']
    bubble = style.get('bubble', HOUSE_STYLE['bubble'])
    fg = _hex_rgba(colors['card_fg'])
    muted = _hex_rgba(colors['muted'])
    accent = _hex_rgba(colors['accent'])

    card_w = int(1920 * float(bubble.get('width_ratio', 0.80)))
    radius = int(bubble.get('radius', 56))
    pad = 56
    content_w = card_w - 2 * pad

    scratch = Image.new('RGBA', (10, 10))
    sdraw = ImageDraw.Draw(scratch)

    name_font = _load_font('bold', 44)
    handle_font = _load_font('regular', 34)
    ts_font = _load_font('regular', 32)
    metric_num_font = _load_font('bold', 32)
    metric_lbl_font = _load_font('regular', 32)

    text = _display_text(row)
    max_lines = 7 if media_img else 9
    body_font, body_lines, body_line_h = _fit_text(
        sdraw, text, content_w, max_lines=max_lines, start_size=52, floor_size=36)
    line_gap = int(body_line_h * 0.32)
    body_h = len(body_lines) * (body_line_h + line_gap) - line_gap if body_lines else 0

    media_h = 0
    if media_img:
        scale = content_w / media_img.width
        media_h = min(int(media_img.height * scale), 460)

    ts_text = _fmt_timestamp(row.xpost_datetime)
    metrics = [(_fmt_metric(v), label) for v, label in (
        (row.xpost_replies, 'Replies'),
        (row.xpost_retweets, 'Reposts'),
        (row.xpost_likes, 'Likes'),
        (row.xpost_view_count, 'Views'),
    ) if _fmt_metric(v) is not None]

    avatar_size = 112
    section_gap = 32
    footer_line_h = 44

    card_h = pad + avatar_size + section_gap + body_h
    if media_img:
        card_h += section_gap + media_h
    if ts_text or metrics:
        card_h += section_gap + 1 + 22  # divider + gap
        if ts_text:
            card_h += footer_line_h
        if metrics:
            card_h += footer_line_h
    card_h += pad

    card = Image.new('RGBA', (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)

    border = style['card_border']
    bg_alpha = int(255 * float(bubble.get('bg_alpha', 0.92)))
    draw.rounded_rectangle(
        [0, 0, card_w - 1, card_h - 1], radius=radius,
        fill=_hex_rgba(colors['card_bg'], bg_alpha),
        outline=_hex_rgba(border.get('color', '#3A3F45')),
        width=int(border.get('width', 1)),
    )

    # Platform watermark INSIDE the bubble (X only): rendered BIG, off-centre
    # (hanging past the right edge), gaussian-blurred, and translucent — a soft
    # ghost of the X logo behind the content. Clipped to the rounded shape so
    # it never spills past the corners.
    platform = (row.xpost_platform or 'x').lower()
    wm_opacity = float(bubble.get('watermark_opacity', 0.08))
    if platform in ('x', 'twitter') and wm_opacity > 0:
        from PIL import ImageFilter
        wm_size = int(card_h * 1.35)
        wm_font = _load_font('bold', wm_size)
        wm_layer = Image.new('RGBA', (card_w, card_h), (0, 0, 0, 0))
        wm_draw = ImageDraw.Draw(wm_layer)
        wm_bbox = wm_draw.textbbox((0, 0), 'X', font=wm_font)
        wm_w = wm_bbox[2] - wm_bbox[0]
        wm_draw.text(
            (card_w - int(wm_w * 0.78), int(card_h * 0.5 - wm_size * 0.62)),
            'X', font=wm_font,
            fill=_hex_rgba(colors['card_fg'], int(255 * wm_opacity)))
        wm_layer = wm_layer.filter(
            ImageFilter.GaussianBlur(int(bubble.get('watermark_blur', 14))))
        mask = Image.new('L', (card_w, card_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, card_w - 1, card_h - 1], radius=radius, fill=255)
        wm_layer.putalpha(Image.composite(
            wm_layer.getchannel('A'), Image.new('L', (card_w, card_h), 0), mask))
        card.alpha_composite(wm_layer)

    # Author row
    x = pad
    y = pad
    if avatar_img:
        card.alpha_composite(_avatar_thumb(avatar_img, avatar_size, style['avatar_shape']), (x, y))
    text_x = x + avatar_size + 28
    name = row.xpost_name or (f"@{row.xpost_username}" if row.xpost_username else 'Unknown')
    _draw_text(card, draw, (text_x, y + 8), name, name_font, fg)
    if row.xpost_verified:
        name_w = _text_width(draw, name, name_font)
        bx = text_x + name_w + 16
        by = y + 14
        draw.ellipse([bx, by, bx + 38, by + 38], fill=accent)
        # Simple white check inside the badge
        draw.line([(bx + 10, by + 20), (bx + 17, by + 27)], fill=(255, 255, 255, 255), width=4)
        draw.line([(bx + 17, by + 27), (bx + 29, by + 12)], fill=(255, 255, 255, 255), width=4)
    if row.xpost_username:
        _draw_text(card, draw, (text_x, y + 62), f"@{row.xpost_username}", handle_font, muted)

    # Tweet text
    y = pad + avatar_size + section_gap
    for line in body_lines:
        if line:
            _draw_text(card, draw, (pad, y), line, body_font, fg)
        y += body_line_h + line_gap
    if body_lines:
        y -= line_gap

    # Media
    if media_img:
        y += section_gap
        from PIL import Image as PILImage
        scale = content_w / media_img.width
        scaled = media_img.resize((content_w, int(media_img.height * scale)), PILImage.LANCZOS)
        if scaled.height > media_h:  # center-crop overflow
            top = (scaled.height - media_h) // 2
            scaled = scaled.crop((0, top, content_w, top + media_h))
        scaled = _rounded(scaled, 28)
        card.alpha_composite(scaled, (pad, y))
        if media_is_video:
            # Play triangle over the middle of the media
            cx, cy = pad + content_w // 2, y + media_h // 2
            draw.ellipse([cx - 48, cy - 48, cx + 48, cy + 48], fill=(0, 0, 0, 170))
            draw.polygon([(cx - 15, cy - 24), (cx - 15, cy + 24), (cx + 27, cy)],
                         fill=(255, 255, 255, 235))
        y += media_h

    # Divider + timestamp + metrics
    if ts_text or metrics:
        y += section_gap
        draw.line([(pad, y), (card_w - pad, y)], fill=_hex_rgba(colors['muted'], 80), width=1)
        y += 22
        if ts_text:
            _draw_text(card, draw, (pad, y), ts_text, ts_font, muted)
            y += footer_line_h
        if metrics:
            mx = pad
            for value, label in metrics:
                _draw_text(card, draw, (mx, y), value, metric_num_font, fg)
                mx += draw.textbbox((0, 0), value, font=metric_num_font)[2] + 12
                _draw_text(card, draw, (mx, y), label, metric_lbl_font, muted)
                mx += draw.textbbox((0, 0), label, font=metric_lbl_font)[2] + 40

    # Wrap the finished card in the outer edge stroke: a rounded ring of
    # edge.width around the whole bubble. Done by compositing the card inset
    # on a slightly larger rounded rect, so the drop shadow in
    # _compose_frames automatically follows the bordered silhouette.
    edge = style.get('card_edge', HOUSE_STYLE.get('card_edge', {})) or {}
    edge_w = int(edge.get('width', 0))
    if edge_w > 0:
        edge_alpha = int(255 * float(edge.get('opacity', 0.85)))
        bordered = Image.new('RGBA', (card_w + 2 * edge_w, card_h + 2 * edge_w), (0, 0, 0, 0))
        ImageDraw.Draw(bordered).rounded_rectangle(
            [0, 0, bordered.width - 1, bordered.height - 1],
            radius=radius + edge_w,
            fill=_hex_rgba(edge.get('color', '#14181C'), edge_alpha))
        bordered.alpha_composite(card, (edge_w, edge_w))
        card = bordered

    return card


def _compose_frames(card, row, style, captured_at):
    """Full-frame 1920x1080 + transparent key variant, card centered."""
    from PIL import Image, ImageDraw, ImageFilter

    width, height = 1920, 1080
    colors = style['colors']
    bubble = style.get('bubble', HOUSE_STYLE['bubble'])
    radius = int(bubble.get('radius', 56))

    # Keep the card inside the frame with breathing room.
    if card.height > 980:
        scale = 980 / card.height
        card = card.resize((int(card.width * scale), 980), Image.LANCZOS)
        radius = max(16, int(radius * scale))

    card_x = (width - card.width) // 2
    card_y = (height - card.height) // 2

    # Drop shadow layer (shared by both frames)
    shadow_cfg = style['drop_shadow']
    shadow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    if shadow_cfg.get('enabled', True):
        off = shadow_cfg.get('offset', [0, 12])
        alpha = int(255 * float(shadow_cfg.get('opacity', 0.6)))
        sdraw = ImageDraw.Draw(shadow)
        sdraw.rounded_rectangle(
            [card_x + off[0], card_y + off[1],
             card_x + off[0] + card.width, card_y + off[1] + card.height],
            radius=radius, fill=(0, 0, 0, alpha))
        shadow = shadow.filter(ImageFilter.GaussianBlur(int(shadow_cfg.get('blur', 40)) // 2))

    # ── Full frame ── (the platform watermark lives inside the bubble now)
    frame = Image.new('RGBA', (width, height), _hex_rgba(colors['frame_bg']))
    frame.alpha_composite(shadow)
    frame.alpha_composite(card, (card_x, card_y))
    fdraw = ImageDraw.Draw(frame)
    # Accent rule along the bottom
    fdraw.rectangle([0, height - 6, width, height], fill=_hex_rgba(colors['frame_accent']))
    # Archival caption bottom-left
    handle = f"@{row.xpost_username}" if row.xpost_username else (row.xpost_name or 'X post')
    ts = captured_at.strftime('%Y-%m-%d %H:%M %Z') if captured_at else 'unknown'
    caption_font = _load_font('regular', 24)
    fdraw.text((40, height - 6 - 40), f"{handle} · captured {ts} · Disaffected",
               font=caption_font,
               fill=_hex_rgba(colors.get('frame_caption', colors['muted'])))
    full_frame = frame.convert('RGB')

    # ── Key frame (transparent) ──
    key_frame = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    key_frame.alpha_composite(shadow)
    key_frame.alpha_composite(card, (card_x, card_y))

    return full_frame, key_frame


# ── the Celery task ────────────────────────────────────────────────────────

@shared_task(bind=True, name='services.xpost_renderer.generate_xpost_png')
def generate_xpost_png(self, asset_id: str, episode_id: str, priority: str = 'normal'):
    """Render the X-post GFX card for a gfx_xpost_cues row to PNG (+key).

    Mirrors generate_gfx_png's return shape so the existing frontend pollers
    (/api/gfx/task/{id}) consume the result unchanged, plus key_asset_url.
    """
    from core.paths import ShowBuildPaths
    from database import SessionLocal
    from models.settings import GfxXpostCue

    db = SessionLocal()
    row = None
    try:
        logger.info(f"🐦 Starting X-post PNG render for {asset_id} (episode {episode_id})")
        episode_id = episode_id.zfill(4) if len(episode_id) < 4 else episode_id

        row = db.query(GfxXpostCue).filter(GfxXpostCue.asset_id == asset_id).first()
        if not row:
            logger.error(f"   ❌ No gfx_xpost_cues row for asset_id {asset_id}")
            return {
                "success": False,
                "asset_id": asset_id,
                "episode_id": episode_id,
                "message": f"No captured X-post data for AssetID {asset_id} — insert the cue first.",
            }

        row.status = 'generating'
        row.last_render_task_id = self.request.id
        db.commit()

        self.update_state(state='PROGRESS', meta={
            'status': 'Fetching post media...', 'progress': 15,
            'episode_id': episode_id, 'asset_id': asset_id,
        })

        path_manager = ShowBuildPaths()
        assets_dir = path_manager.get_asset_type_dir(episode_id, 'graphics')
        assets_dir.mkdir(parents=True, exist_ok=True)
        src_dir = assets_dir / 'xpost_src' / asset_id

        if row.aspect_ratio and row.aspect_ratio not in ('16:9',):
            logger.warning(f"   ⚠️ Aspect ratio {row.aspect_ratio} not supported yet — rendering 16:9")

        avatar_img, avatar_path = _fetch_avatar(row.xpost_profile_photo, src_dir)
        media_url, media_is_video = _pick_media(row)
        media_img, media_path = _fetch_image(media_url, src_dir, 'media_0') if media_url else (None, None)

        local_paths = dict(row.xpost_media_local_paths or {})
        if avatar_path:
            local_paths['avatar'] = avatar_path
        if media_path:
            local_paths.setdefault('media', [])
            if media_path not in local_paths['media']:
                local_paths['media'].append(media_path)
        row.xpost_media_local_paths = local_paths or None

        self.update_state(state='PROGRESS', meta={
            'status': 'Rendering card...', 'progress': 50,
            'episode_id': episode_id, 'asset_id': asset_id,
        })

        seq = row.display_sequence if isinstance(row.display_sequence, dict) else {}
        style = _merge_style(seq.get('style'))

        card = _render_card(row, style, avatar_img, media_img, media_is_video)

        captured_at = row.captured_at or datetime.now(timezone.utc)
        full_frame, key_frame = _compose_frames(card, row, style, captured_at)

        # Filenames: identical slug cleaning to generate_gfx_png, with the
        # fleet's enumerated form when an enumerator is present.
        clean_slug = (row.slug or 'xpost').lower().replace(' ', '-').replace('_', '-')
        clean_slug = re.sub(r'[^\w\-]', '', clean_slug)
        if row.enumerator:
            base_name = f"{row.enumerator}-{clean_slug}"
        else:
            base_name = f"gfx_{clean_slug}"
        output_path = assets_dir / f"{base_name}.png"
        key_path = assets_dir / f"{base_name}_key.png"

        full_frame.save(output_path, 'PNG', optimize=True)
        key_frame.save(key_path, 'PNG', optimize=True)

        if not output_path.exists():
            raise FileNotFoundError(f"Generated PNG not found: {output_path}")

        asset_url = f"/episodes/{output_path.relative_to(path_manager.episodes_root)}"
        key_url = f"/episodes/{key_path.relative_to(path_manager.episodes_root)}"

        row.status = 'complete'
        row.generated_asset_path = str(output_path)
        row.generated_asset_url = asset_url
        row.generated_key_path = str(key_path)
        row.generated_key_url = key_url
        db.commit()

        file_size = output_path.stat().st_size
        logger.info(f"   ✅ X-post PNG rendered: {output_path.name} (+ key) — {file_size:,} bytes")

        return {
            "success": True,
            "asset_path": str(output_path),
            "asset_url": asset_url,
            "key_asset_path": str(key_path),
            "key_asset_url": key_url,
            "asset_id": asset_id,
            "episode_id": episode_id,
            "file_size": file_size,
            "filename": output_path.name,
            "message": f"X-post PNG generated successfully: {output_path.name}",
            "task_id": self.request.id,
            "worker": self.request.hostname,
            "priority": priority,
            "gfx_type": "xpost",
        }

    except Exception as e:
        logger.error(f"   ❌ Error rendering X-post PNG: {e}")
        import traceback
        traceback.print_exc()
        try:
            if row is not None:
                row.status = 'failed'
                db.commit()
        except Exception:
            db.rollback()
        self.retry(countdown=30, max_retries=2, exc=e)
    finally:
        db.close()
