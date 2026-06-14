"""
Celery Tasks for Production Tools

Async tasks for:
- Asset Metadata Validation
- Duration Reconciliation (ffprobe)
- Production Report Generation
"""

import os
import re
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from celery import shared_task, current_task
from services.cue_extractor import CUE_BLOCK_RE

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="services.tools_tasks.validate_metadata")
def validate_metadata_task(self, episode: Optional[str] = None):
    """
    Validate cue block metadata across rundown items.

    Scans for:
    - Missing required fields (AssetID, Duration, Type)
    - Invalid field values
    - Orphaned references

    Args:
        episode: Specific episode to validate, or None for all
    """
    from database import SessionLocal
    from models_v2 import RundownItem, Episode, Rundown

    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "episode": episode or "all",
        "issues": [],
        "summary": {
            "total_items_scanned": 0,
            "items_with_issues": 0,
            "missing_asset_ids": 0,
            "missing_durations": 0,
            "invalid_cue_blocks": 0
        }
    }

    db = SessionLocal()
    try:
        # Get rundown items
        query = db.query(RundownItem)
        if episode:
            episode_record = db.query(Episode).filter(
                Episode.episode_number == int(episode.lstrip('0')) if episode.isdigit() else Episode.episode_number == episode
            ).first()
            if not episode_record:
                return {"error": f"Episode {episode} not found"}
            # Get rundowns for this episode
            rundowns = db.query(Rundown).filter(Rundown.episode_id == episode_record.id).all()
            rundown_ids = [r.id for r in rundowns]
            if rundown_ids:
                query = query.filter(RundownItem.rundown_id.in_(rundown_ids))

        items = query.all()
        total_items = len(items)
        results["summary"]["total_items_scanned"] = total_items

        for idx, item in enumerate(items):
            # Update progress
            progress = int((idx + 1) / total_items * 100)
            self.update_state(state='PROGRESS', meta={'progress': progress})

            item_issues = []

            # Check asset_id
            if not item.asset_id:
                item_issues.append({
                    "field": "asset_id",
                    "issue": "missing",
                    "severity": "warning"
                })
                results["summary"]["missing_asset_ids"] += 1

            # Check duration
            if not item.duration or item.duration == "00:00:00":
                item_issues.append({
                    "field": "duration",
                    "issue": "missing_or_zero",
                    "severity": "info"
                })
                results["summary"]["missing_durations"] += 1

            # Parse script_content for cue blocks
            if item.script_content:
                cue_issues = _validate_cue_blocks(item.script_content)
                if cue_issues:
                    item_issues.extend(cue_issues)
                    results["summary"]["invalid_cue_blocks"] += len(cue_issues)

            if item_issues:
                results["issues"].append({
                    "item_id": item.id,
                    "asset_id": item.asset_id,
                    "slug": item.slug,
                    "title": item.title,
                    "issues": item_issues
                })
                results["summary"]["items_with_issues"] += 1

        return results

    except Exception as e:
        logger.error(f"Metadata validation failed: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@shared_task(bind=True, name="services.tools_tasks.reconcile_durations")
def reconcile_durations_task(self, episode: str):
    """
    Compare database durations with actual media file durations.

    Uses ffprobe to get actual durations and compares with stored values.

    Args:
        episode: Episode number to reconcile
    """
    from database import SessionLocal
    from models_v2 import RundownItem, Episode, Rundown
    from platform_utils import get_ffprobe_binary

    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "episode": episode,
        "mismatches": [],
        "missing_files": [],
        "summary": {
            "total_items": 0,
            "items_with_media": 0,
            "mismatches_found": 0,
            "files_not_found": 0
        }
    }

    db = SessionLocal()
    try:
        # Get episode
        episode_record = db.query(Episode).filter(
            Episode.episode_number == int(episode.lstrip('0')) if episode.isdigit() else Episode.episode_number == episode
        ).first()

        if not episode_record:
            return {"error": f"Episode {episode} not found"}

        # Get rundowns for this episode
        rundowns = db.query(Rundown).filter(Rundown.episode_id == episode_record.id).all()
        rundown_ids = [r.id for r in rundowns]

        if not rundown_ids:
            return {"error": f"No rundowns found for episode {episode}"}

        # Get rundown items
        items = db.query(RundownItem).filter(
            RundownItem.rundown_id.in_(rundown_ids)
        ).all()

        results["summary"]["total_items"] = len(items)

        # Episode assets directory
        episode_dir = Path("/home/episodes") / episode.zfill(4) / "assets"

        ffprobe = get_ffprobe_binary()

        for idx, item in enumerate(items):
            # Update progress
            progress = int((idx + 1) / len(items) * 100)
            self.update_state(state='PROGRESS', meta={'progress': progress})

            # Look for media files associated with this item
            if not item.script_content:
                continue

            # Find SOT cue blocks with media references
            sot_pattern = r'\[AssetID:\s*([^\]]+)\]'
            asset_ids = re.findall(sot_pattern, item.script_content)

            for asset_id in asset_ids:
                # Look for video file
                possible_paths = [
                    episode_dir / "sots" / f"{item.slug}.mp4",
                    episode_dir / "video" / f"{item.slug}.mp4",
                    episode_dir / "sots" / f"{asset_id}.mp4",
                ]

                media_path = None
                for path in possible_paths:
                    if path.exists():
                        media_path = path
                        break

                if not media_path:
                    results["missing_files"].append({
                        "item_id": item.id,
                        "asset_id": asset_id,
                        "slug": item.slug,
                        "searched_paths": [str(p) for p in possible_paths]
                    })
                    results["summary"]["files_not_found"] += 1
                    continue

                results["summary"]["items_with_media"] += 1

                # Get actual duration with ffprobe
                try:
                    cmd = [
                        ffprobe, "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "json",
                        str(media_path)
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                    if result.returncode == 0:
                        probe_data = json.loads(result.stdout)
                        actual_seconds = float(probe_data.get("format", {}).get("duration", 0))

                        # Parse stored duration
                        stored_seconds = _parse_duration_to_seconds(item.duration)

                        # Check for mismatch (more than 1 second difference)
                        if abs(actual_seconds - stored_seconds) > 1:
                            results["mismatches"].append({
                                "item_id": item.id,
                                "asset_id": asset_id,
                                "slug": item.slug,
                                "media_path": str(media_path),
                                "stored_duration": item.duration,
                                "stored_seconds": stored_seconds,
                                "actual_seconds": round(actual_seconds, 2),
                                "actual_duration": _seconds_to_duration(actual_seconds),
                                "difference_seconds": round(actual_seconds - stored_seconds, 2)
                            })
                            results["summary"]["mismatches_found"] += 1

                except subprocess.TimeoutExpired:
                    logger.warning(f"ffprobe timeout for {media_path}")
                except Exception as e:
                    logger.error(f"ffprobe error for {media_path}: {e}")

        return results

    except Exception as e:
        logger.error(f"Duration reconciliation failed: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@shared_task(bind=True, name="services.tools_tasks.generate_production_report")
def generate_production_report_task(
    self,
    episode: str,
    include_assets: bool = True,
    include_scripts: bool = True,
    include_timeline: bool = True
):
    """
    Generate comprehensive production report for an episode.

    Creates HTML report with:
    - Episode summary
    - Rundown overview
    - Asset inventory
    - Script completion status
    - Timeline visualization

    Args:
        episode: Episode number
        include_assets: Include asset inventory section
        include_scripts: Include script status section
        include_timeline: Include timeline visualization
    """
    from database import SessionLocal
    from models_v2 import RundownItem, Episode, Rundown

    db = SessionLocal()
    try:
        # Get episode
        episode_record = db.query(Episode).filter(
            Episode.episode_number == int(episode.lstrip('0')) if episode.isdigit() else Episode.episode_number == episode
        ).first()

        if not episode_record:
            return {"error": f"Episode {episode} not found"}

        self.update_state(state='PROGRESS', meta={'progress': 10})

        # Get rundowns for this episode
        rundowns = db.query(Rundown).filter(Rundown.episode_id == episode_record.id).all()
        rundown_ids = [r.id for r in rundowns]

        if not rundown_ids:
            return {"error": f"No rundowns found for episode {episode}"}

        # Get rundown items
        items = db.query(RundownItem).filter(
            RundownItem.rundown_id.in_(rundown_ids)
        ).order_by(RundownItem.order_in_rundown).all()

        self.update_state(state='PROGRESS', meta={'progress': 30})

        # Build report data
        report_data = {
            "episode": {
                "number": episode,
                "title": episode_record.title or f"Episode {episode}",
                "airdate": str(episode_record.airdate) if episode_record.airdate else "TBD",
                "status": episode_record.status or "unknown"
            },
            "rundown": {
                "total_items": len(items),
                "items": []
            },
            "summary": {
                "by_type": {},
                "by_status": {},
                "total_duration": "00:00:00",
                "scripts_complete": 0,
                "scripts_incomplete": 0
            }
        }

        total_seconds = 0
        for item in items:
            item_data = {
                "order": item.order_in_rundown,
                "slug": item.slug,
                "title": item.title,
                "type": item.item_type,
                "duration": item.duration or "00:00:00",
                "status": item.status or "draft",
                "has_script": bool(item.script_content and len(item.script_content) > 100)
            }
            report_data["rundown"]["items"].append(item_data)

            # Count by type
            item_type = item.item_type or "unknown"
            report_data["summary"]["by_type"][item_type] = report_data["summary"]["by_type"].get(item_type, 0) + 1

            # Count by status
            status = item.status or "draft"
            report_data["summary"]["by_status"][status] = report_data["summary"]["by_status"].get(status, 0) + 1

            # Sum duration
            total_seconds += _parse_duration_to_seconds(item.duration)

            # Script status
            if item_data["has_script"]:
                report_data["summary"]["scripts_complete"] += 1
            else:
                report_data["summary"]["scripts_incomplete"] += 1

        report_data["summary"]["total_duration"] = _seconds_to_duration(total_seconds)

        self.update_state(state='PROGRESS', meta={'progress': 60})

        # Generate HTML report
        html_content = _generate_report_html(report_data, include_assets, include_scripts, include_timeline)

        self.update_state(state='PROGRESS', meta={'progress': 80})

        # Save report
        reports_dir = Path("/home/episodes") / episode.zfill(4) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"production-report-{timestamp}.html"
        report_path = reports_dir / report_filename

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        self.update_state(state='PROGRESS', meta={'progress': 100})

        return {
            "success": True,
            "report_path": str(report_path),
            "download_url": f"/episodes/{episode.zfill(4)}/reports/{report_filename}",
            "summary": report_data["summary"]
        }

    except Exception as e:
        logger.error(f"Production report generation failed: {e}")
        return {"error": str(e)}
    finally:
        db.close()


# ============================================================================
# Helper Functions
# ============================================================================

def _validate_cue_blocks(script_content: str) -> List[Dict[str, Any]]:
    """Validate cue blocks in script content."""
    issues = []

    # Find cue blocks (expanded + collapsed; group 1 = cue body).
    cue_blocks = CUE_BLOCK_RE.findall(script_content)

    for idx, block in enumerate(cue_blocks):
        # Check for required fields based on cue type

        # Get cue type
        type_match = re.search(r'\[Type:\s*([^\]]+)\]', block)
        cue_type = type_match.group(1).strip() if type_match else None

        if not cue_type:
            issues.append({
                "field": f"cue_block_{idx}_type",
                "issue": "missing_type",
                "severity": "error"
            })
            continue

        # Check AssetID
        asset_id_match = re.search(r'\[AssetID:\s*([^\]]+)\]', block)
        if not asset_id_match:
            issues.append({
                "field": f"cue_block_{idx}_asset_id",
                "issue": "missing_asset_id",
                "severity": "warning",
                "cue_type": cue_type
            })

        # SOT-specific validations
        if cue_type == 'SOT':
            # Check for duration
            duration_match = re.search(r'\[Duration:\s*([^\]]+)\]', block)
            if not duration_match:
                issues.append({
                    "field": f"cue_block_{idx}_duration",
                    "issue": "missing_duration",
                    "severity": "info",
                    "cue_type": cue_type
                })

    return issues


def _parse_duration_to_seconds(duration: Optional[str]) -> float:
    """Parse duration string to seconds."""
    if not duration:
        return 0

    try:
        parts = duration.split(":")
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        else:
            return float(duration)
    except (ValueError, TypeError):
        return 0


def _seconds_to_duration(seconds: float) -> str:
    """Convert seconds to duration string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _generate_report_html(
    data: Dict[str, Any],
    include_assets: bool,
    include_scripts: bool,
    include_timeline: bool
) -> str:
    """Generate HTML report from data."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Production Report - Episode {data['episode']['number']}</title>
    <style>
        :root {{
            --bg: #0d1117;
            --card: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --text-muted: #8b949e;
            --accent: #58a6ff;
            --success: #3fb950;
            --warning: #d29922;
            --error: #f85149;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; color: #fff; }}
        h2 {{ font-size: 1.5rem; margin: 2rem 0 1rem; color: #fff; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }}
        h3 {{ font-size: 1.1rem; margin-bottom: 0.5rem; color: var(--text); }}
        .meta {{ color: var(--text-muted); margin-bottom: 2rem; }}
        .card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: var(--accent); }}
        .stat-label {{ color: var(--text-muted); font-size: 0.875rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ color: var(--text-muted); font-weight: 600; font-size: 0.875rem; text-transform: uppercase; }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        .badge-segment {{ background: #1f6feb; color: #fff; }}
        .badge-ad {{ background: #238636; color: #fff; }}
        .badge-promo {{ background: #8957e5; color: #fff; }}
        .badge-draft {{ background: var(--border); color: var(--text-muted); }}
        .badge-approved {{ background: #238636; color: #fff; }}
        .badge-production {{ background: #1f6feb; color: #fff; }}
        .check {{ color: var(--success); }}
        .cross {{ color: var(--error); }}
        .timestamp {{ color: var(--text-muted); font-size: 0.875rem; margin-top: 2rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Production Report</h1>
        <p class="meta">Episode {data['episode']['number']} - {data['episode']['title']}</p>

        <div class="card">
            <div class="grid">
                <div class="stat">
                    <div class="stat-value">{data['rundown']['total_items']}</div>
                    <div class="stat-label">Total Items</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{data['summary']['total_duration']}</div>
                    <div class="stat-label">Total Duration</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{data['summary']['scripts_complete']}</div>
                    <div class="stat-label">Scripts Complete</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{data['episode']['status']}</div>
                    <div class="stat-label">Status</div>
                </div>
            </div>
        </div>

        <h2>Rundown Overview</h2>
        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Duration</th>
                        <th>Status</th>
                        <th>Script</th>
                    </tr>
                </thead>
                <tbody>
"""

    for item in data['rundown']['items']:
        type_class = f"badge-{item['type']}" if item['type'] in ['segment', 'ad', 'promo'] else 'badge-draft'
        status_class = f"badge-{item['status']}" if item['status'] in ['draft', 'approved', 'production'] else 'badge-draft'
        script_icon = '<span class="check">✓</span>' if item['has_script'] else '<span class="cross">✗</span>'

        html += f"""                    <tr>
                        <td>{item['order']}</td>
                        <td><strong>{item['title'] or item['slug']}</strong></td>
                        <td><span class="badge {type_class}">{item['type']}</span></td>
                        <td>{item['duration']}</td>
                        <td><span class="badge {status_class}">{item['status']}</span></td>
                        <td>{script_icon}</td>
                    </tr>
"""

    html += f"""                </tbody>
            </table>
        </div>

        <h2>Summary by Type</h2>
        <div class="card">
            <div class="grid">
"""

    for item_type, count in data['summary']['by_type'].items():
        html += f"""                <div class="stat">
                    <div class="stat-value">{count}</div>
                    <div class="stat-label">{item_type.title()}</div>
                </div>
"""

    html += f"""            </div>
        </div>

        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
</body>
</html>"""

    return html
