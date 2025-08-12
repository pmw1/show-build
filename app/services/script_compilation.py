"""
Server-side script compilation service with database integration.
Migrated from tools/compile-script-dev.py to run as Celery background tasks.
"""
from celery import current_task
from celery_app import celery_app
from database import SessionLocal
from models import EpisodeLegacy as Episode, RundownItemLegacy as RundownItem, CueBlock, ProcessingJob, ProcessingStatus
from core.paths import paths
import logging
import re
import yaml
import html
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def compile_episode_script(
    self, 
    episode_id: str, 
    output_format: str = "html",
    include_cues: bool = True,
    validate_only: bool = False
) -> Dict[str, Any]:
    """
    Server-side script compilation with database storage and progress tracking.
    
    Args:
        episode_id: Episode number (e.g., "0225")
        output_format: Output format (html, pdf, txt)
        include_cues: Whether to include cue blocks
        validate_only: If True, only validate without generating output
        
    Returns:
        Dict with compilation results and metadata
    """
    db = SessionLocal()
    job_id = self.request.id
    
    try:
        # Update job status
        current_task.update_state(state="RUNNING", meta={"progress": 0, "status": "Starting compilation"})
        
        # Get or create episode in database
        episode = db.query(Episode).filter(Episode.episode_number == episode_id).first()
        if not episode:
            episode = _create_episode_from_filesystem(db, episode_id)
        
        # Create processing job record
        job = ProcessingJob(
            episode_id=episode.id,
            job_type="script_compilation",
            job_id=job_id,
            status=ProcessingStatus.RUNNING,
            parameters={
                "output_format": output_format,
                "include_cues": include_cues,
                "validate_only": validate_only
            }
        )
        db.add(job)
        db.commit()
        
        # Update progress
        current_task.update_state(state="RUNNING", meta={"progress": 10, "status": "Loading rundown files"})
        
        # Load and validate rundown files
        rundown_files = paths.get_rundown_files(episode_id)
        if not rundown_files:
            raise Exception(f"No rundown files found for episode {episode_id}")
        
        # Validate cue blocks
        current_task.update_state(state="RUNNING", meta={"progress": 20, "status": "Validating cue blocks"})
        validation_results = _validate_cue_blocks(rundown_files)
        
        if not validation_results["valid"]:
            job.status = ProcessingStatus.FAILED
            job.error_message = f"Validation failed: {'; '.join(validation_results['errors'])}"
            db.commit()
            raise Exception(job.error_message)
        
        if validate_only:
            job.status = ProcessingStatus.COMPLETED
            job.result = {"validation": validation_results}
            db.commit()
            return {"validation": validation_results, "message": "Validation completed"}
        
        # Parse episode info
        current_task.update_state(state="RUNNING", meta={"progress": 40, "status": "Parsing episode information"})
        episode_info = _parse_episode_info(episode_id)
        
        # Generate script content
        current_task.update_state(state="RUNNING", meta={"progress": 60, "status": "Generating script content"})
        script_html = _generate_script_html(episode_info, rundown_files, include_cues)
        
        # Save script to filesystem
        current_task.update_state(state="RUNNING", meta={"progress": 80, "status": "Saving compiled script"})
        output_path = _save_compiled_script(episode_id, script_html, episode_info)
        
        # Update episode last_compiled timestamp
        episode.last_compiled = datetime.utcnow()
        
        # Complete job
        current_task.update_state(state="RUNNING", meta={"progress": 100, "status": "Compilation completed"})
        job.status = ProcessingStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.result = {
            "output_path": str(output_path),
            "output_format": output_format,
            "validation": validation_results,
            "episode_info": episode_info,
            "rundown_files_count": len(rundown_files)
        }
        
        db.commit()
        
        return {
            "success": True,
            "output_path": str(output_path),
            "validation": validation_results,
            "message": f"Script compiled successfully for episode {episode_id}"
        }
        
    except Exception as e:
        logger.error(f"Script compilation failed for episode {episode_id}: {str(e)}")
        
        # Update job with failure
        if 'job' in locals():
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            db.commit()
        
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e), "progress": 0}
        )
        raise
    finally:
        db.close()

def _create_episode_from_filesystem(db: SessionLocal, episode_id: str) -> Episode:
    """Create episode record from filesystem data."""
    episode_dir = paths.get_episode_dir(episode_id)
    info_path = paths.get_episode_info_path(episode_id)
    
    # Parse info.md if it exists
    info_data = {}
    if info_path.exists():
        with open(info_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.strip().startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 2:
                    info_data = yaml.safe_load(parts[1]) or {}
    
    # Create episode record
    episode = Episode(
        episode_number=episode_id,
        title=info_data.get('title', f'Episode {episode_id}'),
        subtitle=info_data.get('subtitle'),
        status=info_data.get('status', 'draft'),
        duration=info_data.get('duration'),
        guest=info_data.get('guest', ''),
        tags=info_data.get('tags', []),
        slug=info_data.get('slug', f'episode-{episode_id}'),
        episode_path=str(episode_dir)
    )
    
    # Parse airdate
    if info_data.get('airdate'):
        try:
            if isinstance(info_data['airdate'], str):
                episode.airdate = datetime.strptime(info_data['airdate'], '%Y-%m-%d')
            else:
                episode.airdate = info_data['airdate']
        except ValueError:
            logger.warning(f"Invalid airdate format for episode {episode_id}")
    
    db.add(episode)
    db.commit()
    return episode

def _validate_cue_blocks(rundown_files: List[Path]) -> Dict[str, Any]:
    """Validate cue blocks in rundown files."""
    validation = {"valid": True, "errors": [], "warnings": []}
    cue_pattern = re.compile(r"(<<!--\s*Begin Cue\s*-->>.*?(?:<<!--\s*End Cue\s*-->>|$))", re.DOTALL | re.IGNORECASE)
    
    for file_path in rundown_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            validation["errors"].append(f"Failed to read {file_path.name}: {str(e)}")
            validation["valid"] = False
            continue
        
        # Parse frontmatter
        frontmatter = {}
        if content.strip().startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 2:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError as e:
                    validation["errors"].append(f"YAML error in {file_path.name}: {str(e)}")
                    validation["valid"] = False
        
        # Validate cue blocks
        cue_blocks = cue_pattern.findall(content)
        for block in cue_blocks:
            block_validation = _validate_single_cue_block(block, file_path.name)
            if block_validation["errors"]:
                validation["errors"].extend(block_validation["errors"])
                validation["valid"] = False
            if block_validation["warnings"]:
                validation["warnings"].extend(block_validation["warnings"])
    
    return validation

def _validate_single_cue_block(block: str, filename: str) -> Dict[str, List[str]]:
    """Validate a single cue block."""
    errors = []
    warnings = []
    
    # Extract cue components
    cue_type = re.search(r"\[Type:\s*(.*?)\]", block, re.IGNORECASE)
    slug = re.search(r"\[Slug:\s*(.*?)\]", block, re.IGNORECASE)
    asset_id = re.search(r"\[AssetID:\s*(.*?)\]", block, re.IGNORECASE)
    media_url = re.search(r"\[MediaURL:\s*(.*?)\]", block, re.IGNORECASE)
    quote = re.search(r"\[Quote:\s*(.*?)(?=\[Attribution:|\[MediaURL:|\s*<<!--\s*End Cue\s*-->>|$)", block, re.IGNORECASE | re.DOTALL)
    
    # Validate required fields
    if not cue_type:
        errors.append(f"Missing [Type] in {filename}")
    elif cue_type.group(1).strip().upper() not in ["FSQ", "SOT", "GFX"]:
        errors.append(f"Invalid [Type: {cue_type.group(1)}] in {filename}")
    
    if not slug or not slug.group(1).strip():
        errors.append(f"Missing or empty [Slug] in {filename}")
    
    # Type-specific validation
    if cue_type and cue_type.group(1).strip().upper() == "FSQ":
        if not quote or not quote.group(1).strip():
            errors.append(f"Missing or empty [Quote] for FSQ in {filename}")
    
    if cue_type and cue_type.group(1).strip().upper() == "GFX":
        if not media_url or not media_url.group(1).strip():
            errors.append(f"Missing or empty [MediaURL] for GFX in {filename}")
    
    # Check for proper cue ending
    if not re.search(r"<<!--\s*End Cue\s*-->>", block, re.IGNORECASE):
        errors.append(f"Missing End Cue in {filename}")
    
    return {"errors": errors, "warnings": warnings}

def _parse_episode_info(episode_id: str) -> Dict[str, Any]:
    """Parse episode information from info.md."""
    info_path = paths.get_episode_info_path(episode_id)
    
    if not info_path.exists():
        return {
            "episode_number": episode_id,
            "title": f"Episode {episode_id}",
            "status": "unknown",
            "airdate": "",
            "date_str": ""
        }
    
    with open(info_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    info_data = {}
    if content.strip().startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 2:
            info_data = yaml.safe_load(parts[1]) or {}
    
    # Process airdate
    date_str = ""
    if info_data.get('airdate'):
        try:
            airdate = info_data['airdate']
            if isinstance(airdate, str):
                airdate_date = datetime.strptime(airdate.split("T")[0], "%Y-%m-%d")
            else:
                airdate_date = airdate
            date_str = airdate_date.strftime("%B %dth, %Y at 9:00 PM")
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing airdate for episode {episode_id}: {e}")
    
    return {
        "episode_number": info_data.get("episode_number", episode_id),
        "title": info_data.get("title", f"Episode {episode_id}"),
        "subtitle": info_data.get("subtitle", ""),
        "status": info_data.get("status", "unknown"),
        "airdate": info_data.get("airdate", ""),
        "date_str": date_str
    }

def _generate_script_html(episode_info: Dict[str, Any], rundown_files: List[Path], include_cues: bool) -> str:
    """Generate HTML script content."""
    # HTML template
    html_template = """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Helvetica, sans-serif; font-size: 18px; }
        .container { width: 95%; max-width: 800px; margin: 0 auto; border-left: 1px dotted rgba(128, 128, 128, 0.5); border-right: 1px dotted rgba(128, 128, 128, 0.5); padding: 1em; }
        .cue { margin-top: 2em; }
        .cue-header { font-weight: bold; font-size: 1em; margin-bottom: 0.5em; }
        .gfx { text-align: left; }
        .sot { text-align: left; font-size: 0.9em; }
        .fsq { text-align: left; max-width: 100%; }
        .fsq blockquote { width: 100%; max-width: 100%; margin: 0; padding: 1.65em; border-left: 9px solid #ccc; border-right: 9px solid #ccc; line-height: 1.5; color: rgba(0, 0, 0, 0.75); box-sizing: border-box; }
        .fsq p { font-size: 0.9em; margin-top: 0.5em; }
    </style>
</head>
<body>
<div class='container'>
{content}
</div>
</body>
</html>"""
    
    # Cover page
    cover_html = f"""
    <div style='text-align: center; font-size: 2.5em'>DISAFFECTED</div>
    <div style='text-align: center; font-size: 1em'>EPISODE: {episode_info['episode_number']}</div>
    <div style='text-align: center; font-size: 1.2em'>{episode_info['date_str']}</div>
    <br><br>
    <div style='text-align: center; font-size: 1.2em'>Title:</div>
    <div style='text-align: center; font-size: 1.5em'>{episode_info['title']}</div>
    """
    
    if episode_info.get('subtitle'):
        cover_html += f"<br><br><div style='text-align: center; font-size: 1.2em'>Subtitle</div><div style='text-align: center; font-size: 1.2em'>{episode_info['subtitle']}</div>"
    
    cover_html += "<br><br>"
    
    # Process rundown files
    content_parts = [cover_html]
    para_counter = 0
    
    for file_path in sorted(rundown_files):
        segment_html, para_counter = _process_segment_file(file_path, para_counter, include_cues)
        content_parts.extend(segment_html)
    
    return html_template.format(content="\n".join(content_parts))

def _process_segment_file(file_path: Path, para_counter: int, include_cues: bool) -> tuple:
    """Process a single rundown segment file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return [], para_counter
    
    # Parse frontmatter
    frontmatter = {}
    if content.strip().startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 2:
            frontmatter = yaml.safe_load(parts[1]) or {}
            if len(parts) > 2:
                content = parts[2]
    
    slug = frontmatter.get("slug", file_path.stem).strip().lower()
    
    # Remove sections we don't want in the script
    content = re.sub(r'##\s*Notes\s*.*?($|\n##|\n---)', '', content, flags=re.DOTALL)
    content = re.sub(r'##\s*Description\s*.*?($|\n##|\n---)', '', content, flags=re.DOTALL)
    
    if not content.strip():
        return [], para_counter
    
    # Segment header
    header_html = f"<p style='text-align:left; font-weight:bold; font-size:1.5em; font-family:Helvetica,sans-serif;'>{slug}</p>"
    output = [header_html]
    
    if include_cues:
        # Process cue blocks and content
        cue_pattern = re.compile(r"(?=(<<!--\s*Begin Cue\s*-->>.*?<<!--\s*End Cue\s*-->>))", re.DOTALL | re.IGNORECASE)
        sot_pattern = r"(?:\{SOT/[^}]+\})"
        
        parts = re.split(r"(?=(?:{}|{}))".format(cue_pattern.pattern, sot_pattern), content, flags=re.DOTALL | re.IGNORECASE)
        
        for part in parts:
            if not isinstance(part, str) or not part.strip():
                continue
                
            if re.match(r"<<!--\s*Begin Cue\s*-->>", part, re.IGNORECASE):
                cue_html = _format_cue_block(part)
                if cue_html:
                    output.append(cue_html)
            elif re.match(r"\{SOT/[^}]+\}", part):
                sot_name = part[5:-1] if len(part) > 6 else "unknown"
                sot_html = f"""
                <div class='cue'>
                <p class='cue-header' style='font-weight:bold; font-size:1em;'>[[ SOT / {sot_name} ]]</p>
                <div class='sot'>
                <p style='margin-top: 0.1em; margin-bottom: 0; font-size: 0.72em;'>No Transcript</p>
                </div>
                </div>
                """
                output.append(sot_html)
            else:
                # Regular content
                paragraphs = part.strip().split("\n\n")
                for para in paragraphs:
                    para = para.strip()
                    if not para or re.match(r"\[MediaURL:[^\]]+\]", para, re.IGNORECASE):
                        continue
                    para = html.escape(para).replace("\n", "<br>")
                    para_counter += 1
                    output.append(f"<p id='para-{para_counter}' style='text-align:justify; width:100%; font-family:Helvetica,sans-serif; line-height:1.5;'>{para}</p>")
    else:
        # Just process text content without cues
        paragraphs = content.strip().split("\n\n")
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            para = html.escape(para).replace("\n", "<br>")
            para_counter += 1
            output.append(f"<p id='para-{para_counter}' style='text-align:justify; width:100%; font-family:Helvetica,sans-serif; line-height:1.5;'>{para}</p>")
    
    return output, para_counter

def _format_cue_block(block: str) -> str:
    """Format a cue block as HTML."""
    # Extract cue components
    cue_type = re.search(r"\[Type:\s*(.*?)\]", block, re.IGNORECASE)
    slug = re.search(r"\[Slug:\s*(.*?)\]", block, re.IGNORECASE)
    asset_id = re.search(r"\[AssetID:\s*(.*?)\]", block, re.IGNORECASE)
    media_url = re.search(r"\[MediaURL:\s*(.*?)\]", block, re.IGNORECASE)
    quote = re.search(r"\[Quote:\s*(.*?)(?=\[Attribution:|\[MediaURL:|\s*<<!--\s*End Cue\s*-->>|$)", block, re.IGNORECASE | re.DOTALL)
    attribution = re.search(r"\[Attribution:\s*(.*?)\]", block, re.IGNORECASE)
    duration = re.search(r"\[Duration:\s*(.*?)\]", block, re.IGNORECASE)
    transcription = re.search(r"\[Transcription:\s*(.*?)\]", block, re.IGNORECASE)
    
    if not cue_type:
        return ""
    
    cue_type_str = cue_type.group(1).strip().upper()
    slug_str = slug.group(1).strip().lower() if slug else "unknown-slug"
    
    entry = f"""
    <div class='cue'>
    <p class='cue-header' style='font-weight:bold; font-size:1em;'>[[ {cue_type_str} / {slug_str} ]]</p>
    """
    
    if cue_type_str == "GFX" and media_url:
        media_url_str = media_url.group(1).strip()
        entry += f"""
        <div class='gfx'>
        <img src='{media_url_str}' style='max-width:350px; max-height:350px; border:1px solid #ccc;' />
        </div>
        """
    
    elif cue_type_str == "SOT":
        entry += "<div class='sot'>"
        if duration and duration.group(1).strip():
            entry += f"<p style='margin-top: 0.1em; margin-bottom: 0; font-size: 0.72em;'>Duration: {duration.group(1).strip()}</p>"
        if transcription and transcription.group(1).strip():
            entry += f"<p style='margin-top: 0.1em; margin-bottom: 0; font-size: 0.72em;'>Trans: {html.escape(transcription.group(1).strip())}</p>"
        else:
            entry += "<p style='margin-top: 0.1em; margin-bottom: 0; font-size: 0.72em;'>No Transcript</p>"
        entry += "</div>"
    
    elif cue_type_str == "FSQ" and quote:
        quote_text = quote.group(1).strip().rstrip(']')
        if quote_text:
            attribution_text = attribution.group(1).strip() if attribution else ""
            entry += f"""
            <div class='fsq'>
            <blockquote>{html.escape(quote_text)}</blockquote>
            <p>— {html.escape(attribution_text)}</p>
            </div>
            """
    
    entry += "</div>"
    return entry

def _save_compiled_script(episode_id: str, script_html: str, episode_info: Dict[str, Any]) -> Path:
    """Save compiled script to filesystem."""
    rundown_dir = paths.get_rundown_dir(episode_id)
    
    # Generate filename based on airdate and status
    airdate = episode_info.get('airdate', '')
    status = episode_info.get('status', 'unknown')
    
    if airdate:
        try:
            if isinstance(airdate, str):
                date_obj = datetime.strptime(airdate.split("T")[0], "%Y-%m-%d")
            else:
                date_obj = airdate
            date_part = date_obj.strftime("%m-%d-%y")
        except (ValueError, TypeError):
            date_part = "unknown"
    else:
        date_part = "unknown"
    
    base_filename = f"script-{date_part}-{status}-1.html"
    output_path = rundown_dir / base_filename
    
    # Find available version number
    version = 1
    while output_path.exists():
        version += 1
        output_path = rundown_dir / f"script-{date_part}-{status}-{version}.html"
    
    # Write the file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(script_html)
    
    return output_path