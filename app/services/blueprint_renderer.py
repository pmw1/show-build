"""
Blueprint Renderer - Template-based document generation system.

Renders documents using Jinja2 templates from the blueprints directory.
Separates presentation (templates) from logic (data gathering).
"""
import re
import html
import yaml
import shutil
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

from database import SessionLocal
from models_v2 import Episode, Rundown, RundownItem, Season, Show, SOTProcessingJob
from services.cue_extractor import CUE_BLOCK_RE

logger = logging.getLogger(__name__)

# Base paths
# In container: /tools/blueprints (mounted volume)
# On host (fallback): relative to project root
BLUEPRINTS_DIR = Path("/tools/blueprints") if Path("/tools/blueprints").exists() else Path(__file__).parent.parent.parent / "tools" / "blueprints"
CONTAINER_EPISODES = Path("/home/episodes")
HOST_EPISODES = Path("/mnt/sync/disaffected/episodes")

# Item types that represent a BREAK
BREAK_ITEM_TYPES = {'break', 'advertisement', 'ad'}


class BlueprintRenderer:
    """
    Renders documents using blueprint templates.

    Usage:
        renderer = BlueprintRenderer("scripts/host-full")
        result = renderer.render(episode_number="0249")
    """

    def __init__(self, blueprint_path: str):
        """
        Initialize renderer with a blueprint.

        Args:
            blueprint_path: Relative path to blueprint (e.g., "scripts/host-full")
        """
        self.blueprint_dir = BLUEPRINTS_DIR / blueprint_path
        self.config = self._load_config()
        self.env = self._create_jinja_env()

    def _load_config(self) -> Dict[str, Any]:
        """Load blueprint configuration from blueprint.yaml."""
        config_path = self.blueprint_dir / "blueprint.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Blueprint config not found: {config_path}")

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _create_jinja_env(self) -> Environment:
        """Create Jinja2 environment with blueprint templates."""
        env = Environment(
            loader=FileSystemLoader(str(self.blueprint_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        env.filters['upper'] = str.upper
        env.filters['escape_html'] = html.escape

        return env

    def render(
        self,
        episode_number: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Render document for an episode.

        Args:
            episode_number: Episode number (e.g., "0249")
            output_dir: Optional output directory

        Returns:
            Dict with success status, output paths, and metadata
        """
        db = SessionLocal()

        try:
            # Gather all data
            context = self._gather_context(episode_number, db)

            if not context:
                return {"success": False, "error": f"Episode {episode_number} not found"}

            # Add config to context
            context['config'] = self.config

            # Determine output path
            ep_num_padded = episode_number.zfill(4)
            output_path = self._get_output_path(ep_num_padded, output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Collect media resources
            resources_path = output_path / "resources"
            resources_path.mkdir(parents=True, exist_ok=True)
            context['url_mapping'] = self._collect_media(context['blocks'], resources_path, ep_num_padded)

            # Render template
            template = self.env.get_template(self.config['files']['template'])
            html_content = template.render(**context)

            # Generate filenames with revision
            date_str = datetime.now().strftime("%Y%m%d")
            preset_suffix = self.config['id'].upper().replace("-", "-")
            revision = self._get_next_revision(output_path, ep_num_padded, preset_suffix, date_str)
            revision_suffix = f"-r{revision}" if revision > 1 else ""

            html_filename = f"{ep_num_padded}-{preset_suffix}-{date_str}{revision_suffix}.html"
            pdf_filename = f"{ep_num_padded}-{preset_suffix}-{date_str}{revision_suffix}.pdf"
            html_path = output_path / html_filename
            pdf_path = output_path / pdf_filename

            logger.info(f"Generating {self.config['name']} revision {revision}: {pdf_filename}")

            # Write HTML
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Convert to PDF
            pdf_generated = self._convert_to_pdf(html_path, pdf_path, context['episode'])

            return {
                "success": True,
                "html_path": str(html_path),
                "pdf_path": str(pdf_path) if pdf_generated else None,
                "output_path": str(pdf_path) if pdf_generated else str(html_path),
                "episode_number": episode_number,
                "blueprint": self.config['id'],
                "revision": revision,
                "block_count": len(context['blocks'])
            }

        except Exception as e:
            logger.error(f"Error rendering {self.config['id']} for episode {episode_number}: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def _gather_context(self, episode_number: str, db) -> Optional[Dict[str, Any]]:
        """Gather all data needed for template rendering."""

        # Find episode
        episode = db.query(Episode).filter(
            Episode.episode_number == int(episode_number)
        ).first()

        if not episode:
            return None

        # Get rundown
        rundown = db.query(Rundown).filter(Rundown.episode_id == episode.id).first()
        if not rundown:
            return None

        # Get rundown items
        items = db.query(RundownItem).filter(
            RundownItem.rundown_id == rundown.id
        ).order_by(RundownItem.order_in_rundown).all()

        if not items:
            return None

        # Build episode info
        episode_info = self._build_episode_info(episode, db, items)

        # Detect blocks
        blocks = self._detect_blocks(items)

        # Process segments within blocks
        transcription_cache = self._build_transcription_cache(items, db)
        for block in blocks:
            block['items'] = [
                self._process_segment(item, transcription_cache)
                for item in block['items']
            ]

        return {
            'episode': episode_info,
            'blocks': blocks,
            'transcription_cache': transcription_cache
        }

    def _build_episode_info(self, episode: Episode, db, items: List[RundownItem]) -> Dict[str, Any]:
        """Build episode information dict."""
        show_name = "DISAFFECTED"
        if episode.season_id:
            season = db.query(Season).filter(Season.id == episode.season_id).first()
            if season and season.show_id:
                show = db.query(Show).filter(Show.id == season.show_id).first()
                if show:
                    show_name = show.name.upper()

        date_str = ""
        if episode.air_date:
            date_str = episode.air_date.strftime("%B %d, %Y")
        elif episode.publish_date:
            date_str = episode.publish_date.strftime("%B %d, %Y")

        duration = episode.duration_formatted or self._calculate_runtime(items)

        return {
            "show_name": show_name,
            "episode_number": str(episode.episode_number).zfill(4),
            "title": episode.title or f"Episode {episode.episode_number}",
            "date_str": date_str,
            "guest_name": episode.guest_name or "",
            "guest_bio": getattr(episode, 'guest_bio', "") or "",
            "duration": duration,
        }

    def _calculate_runtime(self, items: List[RundownItem]) -> str:
        """Calculate total runtime from rundown items."""
        total_seconds = 0
        for item in items:
            dur = item.duration or '00:00:00'
            parts = dur.replace('.', ':').split(':')
            if len(parts) >= 3:
                try:
                    h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                    total_seconds += h * 3600 + m * 60 + s
                except ValueError:
                    pass

        if total_seconds == 0:
            return ""

        return f"{total_seconds // 3600:02d}:{(total_seconds % 3600) // 60:02d}:{total_seconds % 60:02d}"

    def _detect_blocks(self, items: List[RundownItem]) -> List[Dict[str, Any]]:
        """Detect content blocks based on BREAK items."""
        blocks = []
        current_items = []
        block_index = 0

        for item in items:
            item_type = (item.item_type or 'segment').lower()
            is_break = item_type in BREAK_ITEM_TYPES

            if is_break:
                if current_items:
                    blocks.append({
                        'letter': chr(ord('A') + block_index),
                        'items': current_items,
                        'break_after': item
                    })
                    current_items = []
                    block_index += 1
            else:
                current_items.append(item)

        if current_items:
            blocks.append({
                'letter': chr(ord('A') + block_index),
                'items': current_items,
                'break_after': None
            })

        return blocks

    def _process_segment(self, item: RundownItem, transcription_cache: Dict[str, str]) -> Dict[str, Any]:
        """Process a segment into template-friendly format."""
        content = item.script_content or ""

        # Check if has meaningful content
        content_check = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
        content_check = re.sub(r'<!--.*?-->', '', content_check, flags=re.DOTALL)
        content_check = re.sub(r'<p[^>]*>\s*</p>', '', content_check)
        has_content = bool(content_check.strip())

        # Parse content into elements
        elements = self._parse_content(content, transcription_cache) if has_content else []

        return {
            'title': item.title,
            'slug': item.slug,
            'duration': item.duration,
            'has_content': has_content,
            'elements': elements
        }

    def _parse_content(self, content: str, transcription_cache: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse script content into elements (paragraphs and cues)."""
        elements = []
        last_speaker = None

        # Pattern for cue blocks
        cue_pattern = CUE_BLOCK_RE  # matches expanded + collapsed cues

        last_end = 0
        for match in cue_pattern.finditer(content):
            # Text before cue
            text_before = content[last_end:match.start()]
            if text_before.strip():
                paragraphs, last_speaker = self._parse_paragraphs(text_before, last_speaker)
                elements.extend(paragraphs)

            # Cue block
            cue = self._parse_cue(match.group(1), transcription_cache)
            if cue:
                elements.append(cue)

            last_end = match.end()

        # Text after last cue
        text_after = content[last_end:]
        if text_after.strip():
            paragraphs, _ = self._parse_paragraphs(text_after, last_speaker)
            elements.extend(paragraphs)

        return elements

    def _parse_paragraphs(self, text: str, last_speaker: Optional[str]) -> tuple:
        """Parse text into paragraph elements."""
        elements = []
        current_speaker = last_speaker

        # Remove frontmatter
        text = re.sub(r'^---.*?---\s*', '', text, flags=re.DOTALL)
        text = re.sub(r'^-\s*-\s*-.*?-\s*-\s*-\s*', '', text, flags=re.DOTALL)
        text = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)

        # Pattern for paragraphs
        para_pattern = re.compile(r'<p(?:\s+class="([^"]*)")?[^>]*>(.*?)</p>', re.DOTALL | re.IGNORECASE)

        for match in para_pattern.finditer(text):
            speaker_class = match.group(1) or 'josh'
            content = match.group(2).strip()

            if not content:
                continue

            # Clean content
            content = re.sub(r'<[^>]+>', '', content)  # Remove HTML tags
            content = re.sub(r'\s+', ' ', content)

            show_speaker = speaker_class != current_speaker
            current_speaker = speaker_class

            elements.append({
                'type': 'paragraph',
                'speaker': speaker_class,
                'show_speaker': show_speaker,
                'text': content
            })

        return elements, current_speaker

    def _parse_cue(self, cue_content: str, transcription_cache: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse a cue block into a dict."""
        type_match = re.search(r'\[Type:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
        if not type_match:
            return None

        cue_type = type_match.group(1).strip().upper()

        # Extract common fields
        slug_match = re.search(r'\[Slug:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
        slug = slug_match.group(1).strip() if slug_match else 'cue'

        cue = {
            'type': 'cue',
            'cue_type': cue_type,
            'slug': slug
        }

        # Type-specific fields
        if cue_type == 'FSQ':
            quote_match = re.search(r'\[Quote:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
            cue['quote'] = quote_match.group(1).strip().strip('"\'') if quote_match else ''

            attr_match = re.search(r'\[Attribution:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
            cue['attribution'] = attr_match.group(1).strip() if attr_match else ''

            media_match = re.search(r'\[Media\s*[Uu]rl:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
            cue['media_url'] = media_match.group(1).strip() if media_match else ''

        elif cue_type == 'SOT':
            dur_match = re.search(r'\[Duration:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
            cue['duration'] = dur_match.group(1).strip() if dur_match else ''

            thumb_match = re.search(r'\[Thumbnail\s*[Uu]rl:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
            cue['thumbnail_url'] = thumb_match.group(1).strip() if thumb_match else ''

            # Get transcription
            trans_match = re.search(r'\[Transcription:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
            transcription = trans_match.group(1).strip() if trans_match else ''

            if not transcription:
                asset_match = re.search(r'\[Asset\s*Id:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
                if asset_match:
                    transcription = transcription_cache.get(asset_match.group(1).strip(), '')

            cue['transcription'] = transcription

            # Calculate outcue
            if transcription:
                words = transcription.split()
                cue['outcue'] = ' '.join(words[-5:]) if len(words) >= 5 else ' '.join(words)
            else:
                cue['outcue'] = ''

        elif cue_type in ('IMG', 'GFX'):
            media_match = re.search(r'\[Media\s*[Uu]rl:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
            cue['media_url'] = media_match.group(1).strip() if media_match else ''

            desc_match = re.search(r'\[Description:\s*([^\]]+)\]', cue_content, re.IGNORECASE)
            cue['description'] = desc_match.group(1).strip() if desc_match else ''

        return cue

    def _build_transcription_cache(self, items: List[RundownItem], db) -> Dict[str, str]:
        """Build cache of transcriptions from SOTProcessingJob records."""
        cache = {}
        asset_ids = set()

        for item in items:
            if not item.script_content:
                continue
            for cue in CUE_BLOCK_RE.findall(item.script_content):
                if '[Type: SOT]' in cue:
                    asset_match = re.search(r'\[Asset\s*Id:\s*([^\]]+)\]', cue, re.IGNORECASE)
                    if asset_match:
                        asset_ids.add(asset_match.group(1).strip())

        if asset_ids:
            try:
                jobs = db.query(SOTProcessingJob).filter(
                    SOTProcessingJob.asset_id.in_(asset_ids)
                ).all()
                for job in jobs:
                    if job.transcription:
                        cache[job.asset_id] = job.transcription
            except Exception as e:
                logger.warning(f"Failed to fetch transcriptions: {e}")

        return cache

    def _collect_media(self, blocks: List[Dict], resources_path: Path, episode_number: str) -> Dict[str, str]:
        """Collect and copy media files, return URL mapping."""
        url_mapping = {}

        for block in blocks:
            for segment in block['items']:
                for element in segment.get('elements', []):
                    if element.get('type') != 'cue':
                        continue

                    for url_field in ['media_url', 'thumbnail_url']:
                        original_url = element.get(url_field, '')
                        if not original_url or original_url in url_mapping:
                            continue
                        if original_url.startswith(('http://', 'https://', 'blob:')):
                            continue

                        source_path = self._find_media_file(original_url, episode_number)
                        if source_path and source_path.exists():
                            dest_path = resources_path / source_path.name
                            try:
                                if not dest_path.exists():
                                    shutil.copy2(source_path, dest_path)
                                url_mapping[original_url] = f"resources/{source_path.name}"
                                element[url_field] = url_mapping[original_url]
                            except Exception as e:
                                logger.warning(f"Failed to copy {source_path}: {e}")

        return url_mapping

    def _find_media_file(self, url: str, episode_number: str) -> Optional[Path]:
        """Find a media file from a URL."""
        url = url.strip()

        if url.startswith('/episodes/'):
            url = url[1:]

        if url.startswith('/'):
            path = Path(url)
            if path.exists():
                return path
            return None

        if url.startswith('episodes/'):
            for base in [CONTAINER_EPISODES.parent, HOST_EPISODES.parent]:
                path = base / url
                if path.exists():
                    return path

        if url.startswith(('../assets/', 'assets/')):
            clean_url = url.replace('../', '')
            for base in [CONTAINER_EPISODES, HOST_EPISODES]:
                path = base / episode_number / clean_url
                if path.exists():
                    return path

        filename = Path(url).name
        search_dirs = ['assets/images', 'assets/video', 'assets/graphics', 'assets/quotes', 'assets/thumbnails']

        for base in [CONTAINER_EPISODES, HOST_EPISODES]:
            for subdir in search_dirs:
                candidate = base / episode_number / subdir / filename
                if candidate.exists():
                    return candidate

        return None

    def _get_output_path(self, episode_number: str, output_dir: Optional[str]) -> Path:
        """Determine output directory."""
        if output_dir:
            return Path(output_dir)

        container_path = CONTAINER_EPISODES / episode_number / "scripts" / "current"
        if container_path.parent.parent.exists():
            return container_path

        return HOST_EPISODES / episode_number / "scripts" / "current"

    def _get_next_revision(self, output_path: Path, episode: str, preset: str, date_str: str) -> int:
        """Determine next revision number."""
        base_pattern = f"{episode}-{preset}-{date_str}"
        existing_revisions = []

        for file in output_path.glob(f"{base_pattern}*.pdf"):
            filename = file.stem
            if filename == base_pattern:
                existing_revisions.append(1)
            elif filename.startswith(base_pattern + "-r"):
                try:
                    rev_num = int(filename[len(base_pattern) + 2:])
                    existing_revisions.append(rev_num)
                except ValueError:
                    pass

        return max(existing_revisions) + 1 if existing_revisions else 1

    def _convert_to_pdf(self, html_path: Path, pdf_path: Path, episode_info: Dict) -> bool:
        """Convert HTML to PDF using wkhtmltopdf."""
        wkhtmltopdf = shutil.which('wkhtmltopdf')
        if not wkhtmltopdf:
            logger.warning("wkhtmltopdf not found - skipping PDF generation")
            return False

        try:
            margins = self.config.get('output', {}).get('margins', {})
            episode_num = episode_info.get('episode_number', '0000')

            cmd = [
                wkhtmltopdf,
                '--page-size', self.config.get('output', {}).get('page_size', 'Letter'),
                '--margin-top', margins.get('top', '0.75in'),
                '--margin-bottom', margins.get('bottom', '0.75in'),
                '--margin-left', margins.get('left', '0.75in'),
                '--margin-right', margins.get('right', '0.75in'),
                '--footer-left', f'Episode {episode_num}',
                '--footer-right', 'Page [page] of [topage]',
                '--footer-font-size', '9',
                '--footer-spacing', '5',
                '--enable-local-file-access',
                '--print-media-type',
                str(html_path),
                str(pdf_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

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


# Convenience function
def render_from_blueprint(
    blueprint_path: str,
    episode_number: str,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Render a document using a blueprint.

    Args:
        blueprint_path: Path to blueprint (e.g., "scripts/host-full")
        episode_number: Episode number
        output_dir: Optional output directory

    Returns:
        Result dict with success status and paths
    """
    renderer = BlueprintRenderer(blueprint_path)
    return renderer.render(episode_number, output_dir)


# CLI support
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python blueprint_renderer.py <blueprint_path> <episode_number>")
        print("Example: python blueprint_renderer.py scripts/host-full 0249")
        sys.exit(1)

    blueprint = sys.argv[1]
    episode = sys.argv[2]

    result = render_from_blueprint(blueprint, episode)

    if result["success"]:
        print(f"Success! Generated {result['blueprint']} revision {result['revision']}")
        print(f"Output: {result['output_path']}")
    else:
        print(f"Error: {result['error']}")
        sys.exit(1)
