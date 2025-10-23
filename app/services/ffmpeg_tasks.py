"""
FFmpeg processing tasks for Celery workers.

These tasks run on dedicated media processing workers (kairo/proxima/windows)
with ffmpeg installed and handle video/audio processing operations.

Cross-Platform Support:
    - Works on Linux (kairo, proxima) and Windows workers
    - Automatic path normalization
    - GPU acceleration when available (NVENC on Windows, VAAPI on Linux)
"""

import os
import subprocess
import platform
from pathlib import Path
from celery import shared_task
from celery.utils.log import get_task_logger

# Cross-platform utilities
from platform_utils import (
    normalize_path,
    get_ffmpeg_binary,
    get_ffprobe_binary,
    get_platform_info,
    get_media_root
)

logger = get_task_logger(__name__)

# Log worker platform on module load
_platform_info = get_platform_info()
logger.info(f"🖥️  FFmpeg Tasks Module Loaded on {_platform_info['platform']} ({_platform_info['hostname']})")


@shared_task(bind=True, queue='media', name='services.ffmpeg_tasks.process_sot_video')
def process_sot_video(
    self,
    video_path: str,
    episode: str,
    slug: str,
    trim_start: str = "00:00:00",
    trim_end: str = "00:00:00"
):
    """
    Process SOT (Sound on Tape) video file.

    Args:
        video_path: Path to uploaded video file
        episode: Episode number (e.g., "0245")
        slug: Item slug for naming
        trim_start: Start time for trimming (HH:MM:SS format)
        trim_end: End time for trimming (HH:MM:SS format)

    Returns:
        dict: {
            "thumbnail_path": str,
            "audio_path": str,
            "video_path": str,
            "duration": float
        }
    """
    try:
        worker_name = platform.node()
        worker_platform = platform.system()
        logger.info(f"🎬 Processing SOT video on {worker_name} ({worker_platform}): {video_path} for episode {episode}")

        # Normalize input path for this platform
        input_video = normalize_path(video_path)
        if not input_video.exists():
            raise FileNotFoundError(f"Input video not found: {input_video}")

        # Create output directory structure (cross-platform)
        media_root = get_media_root()
        episode_dir = media_root / "episodes" / episode / "assets" / "sots"
        episode_dir.mkdir(parents=True, exist_ok=True)

        base_name = f"{slug}"

        # Get platform-appropriate binaries
        ffmpeg = get_ffmpeg_binary()
        ffprobe = get_ffprobe_binary()

        # 1. Get video duration using ffprobe
        duration_cmd = [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(input_video)
        ]
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        duration = float(duration_result.stdout.strip())
        logger.info(f"Video duration: {duration}s")

        # 2. Generate thumbnail at 1 second mark
        thumbnail_path = episode_dir / f"{base_name}-thumb.jpg"
        thumbnail_cmd = [
            ffmpeg, "-y",
            "-ss", "1",
            "-i", str(input_video),
            "-vframes", "1",
            "-q:v", "2",
            str(thumbnail_path)
        ]
        subprocess.run(thumbnail_cmd, check=True, capture_output=True)
        logger.info(f"Thumbnail created: {thumbnail_path}")

        # 3. Extract audio as MP3
        audio_path = episode_dir / f"{base_name}.mp3"
        audio_cmd = [
            ffmpeg, "-y",
            "-i", str(input_video),
            "-vn",
            "-acodec", "libmp3lame",
            "-ab", "192k",
            str(audio_path)
        ]
        subprocess.run(audio_cmd, check=True, capture_output=True)
        logger.info(f"Audio extracted: {audio_path}")

        # 4. Process video (trim if needed, otherwise copy)
        output_video_path = episode_dir / f"{base_name}.mp4"

        if trim_start != "00:00:00" or trim_end != "00:00:00":
            # Calculate trim duration
            if trim_end != "00:00:00":
                # Parse time strings to seconds
                def time_to_seconds(time_str):
                    h, m, s = map(float, time_str.split(':'))
                    return h * 3600 + m * 60 + s

                start_sec = time_to_seconds(trim_start)
                end_sec = time_to_seconds(trim_end)
                trim_duration = end_sec - start_sec

                video_cmd = [
                    ffmpeg, "-y",
                    "-ss", trim_start,
                    "-i", str(input_video),
                    "-t", str(trim_duration),
                    "-c", "copy",
                    str(output_video_path)
                ]
            else:
                # Only trim from start
                video_cmd = [
                    ffmpeg, "-y",
                    "-ss", trim_start,
                    "-i", str(input_video),
                    "-c", "copy",
                    str(output_video_path)
                ]
        else:
            # No trimming, just copy
            video_cmd = [
                ffmpeg, "-y",
                "-i", str(input_video),
                "-c", "copy",
                str(output_video_path)
            ]

        subprocess.run(video_cmd, check=True, capture_output=True)
        logger.info(f"Video processed: {output_video_path}")

        # Clean up temp upload file (cross-platform temp detection)
        input_video_str = str(input_video)
        is_temp = any(temp_marker in input_video_str.lower() for temp_marker in ['/tmp/', '\\temp\\', 'c:\\temp'])
        if input_video.exists() and is_temp:
            input_video.unlink()
            logger.info(f"Removed temp file: {input_video}")

        # Return results with worker info
        return {
            "thumbnail_path": str(thumbnail_path),
            "audio_path": str(audio_path),
            "video_path": str(output_video_path),
            "duration": duration,
            "status": "completed",
            "worker": worker_name,
            "platform": worker_platform
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise


@shared_task(bind=True, queue='media', name='services.ffmpeg_tasks.extract_audio_from_video')
def extract_audio_from_video(self, video_path: str, output_path: str):
    """Extract audio from video file (cross-platform)."""
    try:
        ffmpeg = get_ffmpeg_binary()
        cmd = [
            ffmpeg, "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "libmp3lame",
            "-ab", "192k",
            output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return {"audio_path": output_path, "status": "completed"}
    except Exception as e:
        logger.error(f"Audio extraction failed: {str(e)}")
        raise


@shared_task(bind=True, queue='media', name='services.ffmpeg_tasks.generate_thumbnail')
def generate_thumbnail(self, video_path: str, output_path: str, timestamp: str = "1"):
    """Generate thumbnail from video at specified timestamp (cross-platform)."""
    try:
        ffmpeg = get_ffmpeg_binary()
        cmd = [
            ffmpeg, "-y",
            "-ss", timestamp,
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return {"thumbnail_path": output_path, "status": "completed"}
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {str(e)}")
        raise


def _update_job_status(temp_job_id: str, phase: str, status: str, error_message: str = None):
    """Update job status in database (helper function for multi-phase processing)."""
    try:
        from database import SessionLocal
        from models_v2 import SOTProcessingJob

        db = SessionLocal()
        job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
        if job:
            job.current_phase = phase
            job.status = status
            if error_message:
                job.error_message = error_message
            db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Failed to update job status: {e}")


def _normalize_slug(slug: str) -> str:
    """Normalize slug to lowercase with hyphens."""
    import re
    # Convert to lowercase
    slug = slug.lower()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove any characters that aren't alphanumeric or hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Strip leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def _update_sot_cue_block(episode: str, slug: str, asset_id: str, updates: dict):
    """
    Update SOT cue block in rundown item's script_content with processing progress.

    Args:
        episode: Episode number
        slug: SOT slug to find the cue block
        asset_id: AssetID to match the cue
        updates: Dict of fields to update (e.g., {'MediaURL': '/path/to/video.mp4', 'Status': 'Phase 2'})
    """
    try:
        from database import SessionLocal
        from models_v2 import Rundown, RundownItem
        import re

        db = SessionLocal()

        # Find the rundown for this episode
        rundown = db.query(Rundown).filter_by(episode_number=episode).first()
        if not rundown:
            logger.warning(f"No rundown found for episode {episode}")
            db.close()
            return

        # Search all rundown items for SOT cue with matching AssetID
        items = db.query(RundownItem).filter_by(rundown_id=rundown.id).all()

        for item in items:
            if not item.script_content:
                continue

            # Look for SOT cue block with matching AssetID
            cue_pattern = re.compile(
                r'(<!-- Begin Cue -->.*?\[Type: SOT\].*?\[AssetID: ' + re.escape(asset_id) + r'\].*?<!-- End Cue -->)',
                re.DOTALL
            )

            match = cue_pattern.search(item.script_content)
            if match:
                cue_block = match.group(1)
                updated_cue = cue_block

                # Update each field in the cue block
                for field, value in updates.items():
                    # Check if field exists, update it
                    field_pattern = re.compile(rf'\[{field}: [^\]]*\]')
                    if field_pattern.search(updated_cue):
                        updated_cue = field_pattern.sub(f'[{field}: {value}]', updated_cue)
                    else:
                        # Add new field before <!-- End Cue -->
                        updated_cue = updated_cue.replace(
                            '<!-- End Cue -->',
                            f'[{field}: {value}]\n<!-- End Cue -->'
                        )

                # Replace in script_content
                item.script_content = item.script_content.replace(cue_block, updated_cue)
                db.commit()

                logger.info(f"Updated SOT cue block in item {item.id} for AssetID {asset_id}")
                db.close()
                return

        logger.warning(f"No SOT cue found with AssetID {asset_id} in episode {episode}")
        db.close()

    except Exception as e:
        logger.error(f"Failed to update SOT cue block: {e}")
        if 'db' in locals():
            db.close()


def _generate_asset_id() -> str:
    """Generate a unique AssetID for SOT clips."""
    from services.asset_id import AssetIDService
    return AssetIDService.generate_id('AST')


def _process_individual_clips(temp_job_id, episode, slug, clips, parent_asset_id, working_dir, normalized_slug):
    """
    Process individual clips workflow:
    1. Split video into individual clips
    2. Generate unique AssetID for each clip
    3. Run full processing pipeline on each clip
    4. Insert multiple cue blocks into script_content

    Args:
        temp_job_id: Job ID
        episode: Episode number
        slug: Base slug for naming
        clips: List of clip objects with time_start, time_end, slug
        parent_asset_id: AssetID of parent cue block
        working_dir: Working directory path
        normalized_slug: Normalized slug for filenames

    Returns:
        dict: Processing results with multiple clip outputs
    """
    logger.info(f"🎬 INDIVIDUAL CLIPS: Processing {len(clips)} clips for {temp_job_id}")

    # Get platform-appropriate binaries
    ffmpeg = get_ffmpeg_binary()
    ffprobe = get_ffprobe_binary()

    input_file = working_dir / f"{temp_job_id}_upload.mp4"
    if not input_file.exists():
        raise FileNotFoundError(f"Upload file not found: {input_file}")

    clip_results = []

    # Process each clip individually
    for i, clip in enumerate(clips, 1):
        clip_slug = clip.get('slug', f"{slug}_CLIP_{i}")
        clip_start = clip.get('time_start', '00:00:00:00')
        clip_end = clip.get('time_end', '00:00:00:00')

        logger.info(f"📹 Processing clip {i}/{len(clips)}: {clip_slug} ({clip_start} → {clip_end})")

        # Generate unique AssetID for this clip
        clip_asset_id = _generate_asset_id()
        logger.info(f"🆔 Generated AssetID for clip {i}: {clip_asset_id}")

        # Update job status
        _update_job_status(temp_job_id, f'clip{i}_phase-1', 'processing')

        # Phase -1: Extract this clip from source video
        clip_extracted = working_dir / f"{temp_job_id}_clip{i}_extracted.mp4"

        # Convert timecode to seconds
        def timecode_to_seconds(tc):
            """Convert HH:MM:SS:FF to seconds (ignoring frames)"""
            parts = tc.split(':')
            if len(parts) == 4:
                h, m, s, f = parts
                return int(h) * 3600 + int(m) * 60 + int(s)
            return 0

        start_sec = timecode_to_seconds(clip_start)
        end_sec = timecode_to_seconds(clip_end)
        duration_sec = end_sec - start_sec

        # Extract clip with FFmpeg
        extract_cmd = [
            ffmpeg, "-y",
            "-ss", str(start_sec),
            "-i", str(input_file),
            "-t", str(duration_sec),
            "-c", "copy",  # Fast extraction, no re-encoding
            str(clip_extracted)
        ]
        subprocess.run(extract_cmd, check=True, capture_output=True)
        logger.info(f"✅ Clip {i} extracted: {clip_extracted}")

        # Now run full processing pipeline on this clip
        # (Phases 0, 0.5, 1, 1.1, 2, 3-skip, 4, 5)
        clip_result = _process_single_clip(
            clip_extracted, clip_slug, clip_asset_id, episode,
            working_dir, i, temp_job_id
        )

        clip_results.append(clip_result)

    # Phase 6: Insert multiple cue blocks into parent segment
    _insert_multiple_cue_blocks(episode, clip_results, parent_asset_id)

    # Mark job as complete
    _update_job_status(temp_job_id, 'complete', 'completed')

    logger.info(f"✅ INDIVIDUAL CLIPS: Completed processing {len(clips)} clips")

    return {
        "status": "completed",
        "clips": clip_results,
        "message": f"Processed {len(clips)} individual clips successfully"
    }


def _process_single_clip(clip_file, clip_slug, clip_asset_id, episode, working_dir, clip_index, temp_job_id):
    """
    Run full processing pipeline on a single clip.
    Phases: 0 (FFprobe), 0.5 (Whisper), 1 (normalize), 1.1 (audio check),
            2 (audio norm), 3-skip, 4 (thumbnails+MP3), 5 (final move)

    Returns:
        dict: Clip result with AssetID, MediaURL, thumbnails, etc.
    """
    # Get platform-appropriate binaries
    ffmpeg = get_ffmpeg_binary()
    ffprobe = get_ffprobe_binary()
    media_root = get_media_root()

    normalized_clip_slug = _normalize_slug(clip_slug)

    # PHASE 0: FFprobe analysis
    # (Simplified - just get duration for now)
    duration_probe = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(clip_file)],
        capture_output=True, text=True, check=True
    )
    clip_duration = float(duration_probe.stdout.strip())
    duration_formatted = _format_duration(clip_duration)

    logger.info(f"📊 Clip {clip_index} duration: {duration_formatted}")

    # PHASE 1: Video normalization
    phase1_output = working_dir / f"clip{clip_index}_1_normalized.mp4"
    phase1_cmd = [
        ffmpeg, "-y",
        "-i", str(clip_file),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-r", "29.97",
        "-b:v", "8000k",
        "-c:a", "aac",
        "-b:a", "192k",
        str(phase1_output)
    ]
    subprocess.run(phase1_cmd, check=True, capture_output=True)

    # PHASE 2: Audio normalization (EBU R128)
    phase2_output = working_dir / f"clip{clip_index}_2_audio_normalized.mp4"
    phase2_cmd = [
        ffmpeg, "-y",
        "-i", str(phase1_output),
        "-c:v", "copy",
        "-af", "loudnorm=I=-23:TP=-1:LRA=11",
        "-c:a", "aac",
        "-b:a", "192k",
        str(phase2_output)
    ]
    subprocess.run(phase2_cmd, check=True, capture_output=True)

    # PHASE 3: Skip (no trimming needed for already-extracted clips)
    phase3_output = phase2_output

    # PHASE 4: Generate thumbnails and MP3
    # Generate 1 thumbnail (middle of clip)
    thumb_time = clip_duration / 2
    thumb_file = working_dir / f"clip{clip_index}_thumb.jpg"
    thumb_cmd = [
        ffmpeg, "-y",
        "-ss", str(thumb_time),
        "-i", str(phase3_output),
        "-vframes", "1",
        "-q:v", "2",
        str(thumb_file)
    ]
    subprocess.run(thumb_cmd, check=True, capture_output=True)

    # Extract MP3
    mp3_file = working_dir / f"clip{clip_index}_audio.mp3"
    mp3_cmd = [
        ffmpeg, "-y",
        "-i", str(phase3_output),
        "-vn",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(mp3_file)
    ]
    subprocess.run(mp3_cmd, check=True, capture_output=True)

    # PHASE 5: Move to final location (cross-platform)
    final_dir = media_root / "episodes" / episode / "assets" / "sots"
    final_dir.mkdir(parents=True, exist_ok=True)

    final_video = final_dir / f"{normalized_clip_slug}.mp4"
    final_thumb = final_dir / f"{normalized_clip_slug}-thumb.jpg"
    final_audio = final_dir / f"{normalized_clip_slug}.mp3"

    import shutil
    shutil.move(str(phase3_output), str(final_video))
    shutil.move(str(thumb_file), str(final_thumb))
    shutil.move(str(mp3_file), str(final_audio))

    logger.info(f"✅ Clip {clip_index} processing complete: {final_video}")

    return {
        "asset_id": clip_asset_id,
        "slug": clip_slug,
        "media_url": f"/episodes/{episode}/assets/sots/{normalized_clip_slug}.mp4",
        "thumbnail_url": f"/episodes/{episode}/assets/sots/{normalized_clip_slug}-thumb.jpg",
        "audio_url": f"/episodes/{episode}/assets/sots/{normalized_clip_slug}.mp3",
        "duration": duration_formatted
    }


def _format_duration(seconds):
    """Format seconds to HH:MM:SS:00 timecode."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}:00"


def _insert_multiple_cue_blocks(episode, clip_results, parent_asset_id):
    """
    Insert multiple SOT cue blocks into the parent segment's script_content.
    Finds the parent cue by asset_id and inserts new cues after it.

    Args:
        episode: Episode number
        clip_results: List of dicts with asset_id, slug, media_url, etc.
        parent_asset_id: AssetID of the original SOT cue block
    """
    try:
        from database import SessionLocal
        from models_v2 import Rundown, RundownItem
        import re

        db = SessionLocal()

        # Find the rundown for this episode
        rundown = db.query(Rundown).filter_by(episode_number=episode).first()
        if not rundown:
            logger.warning(f"No rundown found for episode {episode}")
            db.close()
            return

        # Search all rundown items for parent SOT cue with matching AssetID
        items = db.query(RundownItem).filter_by(rundown_id=rundown.id).all()

        for item in items:
            if not item.script_content:
                continue

            # Look for parent SOT cue block
            cue_pattern = re.compile(
                r'(<!-- Begin Cue -->.*?\[Type: SOT\].*?\[AssetID: ' + re.escape(parent_asset_id) + r'\].*?<!-- End Cue -->)',
                re.DOTALL
            )

            match = cue_pattern.search(item.script_content)
            if match:
                parent_cue = match.group(1)
                insertion_point = match.end()

                # Build cue blocks for each clip
                new_cues = []
                for clip in clip_results:
                    cue_block = f"""
<!-- Begin Cue -->
[Type: SOT]
[AssetID: {clip['asset_id']}]
[Slug: {clip['slug']}]
[Description: ]
[MediaURL: {clip['media_url']}]
[Duration: {clip['duration']}]
[ThumbnailURL: {clip['thumbnail_url']}]
[AudioURL: {clip['audio_url']}]
[Credits: {{}}]
<!-- End Cue -->
"""
                    new_cues.append(cue_block)

                # Insert all new cues after parent cue
                all_cues = '\n\n'.join(new_cues)
                item.script_content = (
                    item.script_content[:insertion_point] +
                    '\n\n' + all_cues +
                    item.script_content[insertion_point:]
                )

                db.commit()
                logger.info(f"✅ Inserted {len(clip_results)} cue blocks after parent {parent_asset_id}")
                db.close()
                return

        logger.warning(f"Parent SOT cue {parent_asset_id} not found in episode {episode}")
        db.close()

    except Exception as e:
        logger.error(f"Failed to insert multiple cue blocks: {e}")
        if 'db' in locals():
            db.close()


def _process_montage(temp_job_id, episode, slug, clips, asset_id, working_dir, normalized_slug):
    """
    Process montage workflow:
    1. Extract clips individually
    2. Concatenate into single video
    3. Run full processing pipeline on montage
    4. Insert single cue block

    TODO: Implement montage concatenation logic
    """
    raise NotImplementedError("Montage workflow not yet implemented")


@shared_task(bind=True, queue='media', name='services.ffmpeg_tasks.process_sot_video_multi_phase')
def process_sot_video_multi_phase(
    self,
    temp_job_id: str,
    episode: str,
    slug: str,
    trim_start: str = "00:00:00",
    trim_end: str = "00:00:00",
    job_type: str = "full_process",
    clips: list = None,
    asset_id: str = None,
    devel_mode: bool = False
):
    """
    Multi-phase SOT video processing pipeline with intermediate files.

    NEW PHASE ORDER (as of 2025-10-22):
    - Phase 0: Pre-Analysis (analyze RAW uploaded file)
    - Phase 1: Trimming (remove unwanted content FIRST - skip if no trim needed)
    - Phase 1.5: Audio Extract + Whisper Transcription
    - Phase 2: Video Normalization (aspect-aware: 16:9, 9:16, 1:1)
    - Phase 2.5: Audio Channel Fix (dual-mono, channel mapping)
    - Phase 3: Audio Normalization (EBU R128 loudness)
    - Phase 4: Derivatives (10-15 thumbnails + MP3 extract)
    - Phase 5: Final Move to Assets
    - Phase 8: Post-Analysis (verify final output)

    Args:
        temp_job_id: Temporary job ID (e.g., "sot_20251011_143022_abc123")
        episode: Episode number (e.g., "0245")
        slug: Item slug for final naming
        trim_start: Start time for trimming (HH:MM:SS)
        trim_end: End time for trimming (HH:MM:SS)
        job_type: Processing workflow (single_trim, individual_clips, montage, full_process)
        clips: Array of clip objects for individual_clips/montage modes
        asset_id: AssetID for linking to cue block
        devel_mode: If True, keep all intermediate files and return paths in payload

    Returns:
        dict: Final file paths, processing metadata, and failure report
    """
    # Cross-platform working directory
    media_root = get_media_root()
    working_dir = media_root / "preproc" / "working" / temp_job_id
    normalized_slug = _normalize_slug(slug)

    # Get platform info for logging
    worker_name = platform.node()
    worker_platform = platform.system()

    try:
        logger.info(f"🎬 Starting multi-phase processing on {worker_name} ({worker_platform}) for {temp_job_id} (job_type: {job_type}, devel_mode: {devel_mode})")

        # Initialize failure tracking
        import json
        from database import SessionLocal
        from models_v2 import SOTProcessingJob  # Speaker now in models_v2, no import order issue

        processing_report = {
            "job_id": temp_job_id,
            "overall_status": "in_progress",
            "start_time": str(func.now()),
            "phases": {},
            "failures": [],
            "warnings": [],
            "devel_mode": devel_mode,
            "intermediate_files": [] if devel_mode else None
        }

        # Update job record with job_type and clips_data
        db = SessionLocal()
        try:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.job_type = job_type
                if clips:
                    job.clips_data = json.dumps(clips)
                db.commit()
        finally:
            db.close()

        # Route to appropriate processing workflow based on job_type
        if job_type == "single_trim":
            logger.info(f"Executing SINGLE_TRIM workflow for {temp_job_id}")
            # Single trim workflow: Phases 1-5 with simple trim
            # (Current implementation is suitable for this)
        elif job_type == "individual_clips":
            logger.info(f"Executing INDIVIDUAL_CLIPS workflow for {temp_job_id} with {len(clips or [])} clips")
            # Individual clips: Split first, then process each clip through full pipeline
            return _process_individual_clips(
                temp_job_id, episode, slug, clips, asset_id, working_dir, normalized_slug
            )
        elif job_type == "montage":
            logger.info(f"Executing MONTAGE workflow for {temp_job_id} with {len(clips or [])} clips")
            # Montage: Split, process individually, then concatenate
            return _process_montage(
                temp_job_id, episode, slug, clips, asset_id, working_dir, normalized_slug
            )
        else:  # full_process (default)
            logger.info(f"Executing FULL_PROCESS workflow for {temp_job_id}")

        # Get platform-appropriate binaries
        ffmpeg = get_ffmpeg_binary()
        ffprobe = get_ffprobe_binary()

        # Input file from background upload
        input_file = working_dir / f"{temp_job_id}_upload.mp4"
        if not input_file.exists():
            raise FileNotFoundError(f"Upload file not found: {input_file}")

        # ================================================================
        # PHASE 0: Technical Analysis with FFprobe
        # - Extract duration, resolution, framerate, audio channels
        # - Determine orientation (horizontal/vertical)
        # - Store technical metadata
        # ================================================================
        logger.info(f"Phase 0: Technical analysis for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase0', 'processing')

        # Get video stream info
        video_probe_cmd = [
            ffprobe,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,duration",
            "-of", "json",
            str(input_file)
        ]
        video_probe_result = subprocess.run(video_probe_cmd, capture_output=True, text=True, check=True)
        video_info = json.loads(video_probe_result.stdout)
        video_stream = video_info['streams'][0] if video_info.get('streams') else {}

        # Get audio stream info
        audio_probe_cmd = [
            ffprobe,
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=channels,channel_layout,sample_rate",
            "-of", "json",
            str(input_file)
        ]
        audio_probe_result = subprocess.run(audio_probe_cmd, capture_output=True, text=True, check=True)
        audio_info = json.loads(audio_probe_result.stdout)
        audio_stream = audio_info['streams'][0] if audio_info.get('streams') else {}

        # Get container duration
        duration_probe_cmd = [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(input_file)
        ]
        duration_probe_result = subprocess.run(duration_probe_cmd, capture_output=True, text=True, check=True)
        duration_seconds = float(duration_probe_result.stdout.strip())

        # Parse technical details
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))

        # Parse framerate (e.g., "30000/1001" -> 29.97)
        frame_rate_str = video_stream.get('r_frame_rate', '0/1')
        if '/' in frame_rate_str:
            num, denom = map(int, frame_rate_str.split('/'))
            frame_rate = round(num / denom, 2) if denom != 0 else 0
        else:
            frame_rate = float(frame_rate_str)

        audio_channels = audio_stream.get('channels', 0)
        audio_layout = audio_stream.get('channel_layout', 'unknown')
        sample_rate = audio_stream.get('sample_rate', 0)

        # Determine orientation
        if width > height:
            orientation = 'horizontal'
        elif height > width:
            orientation = 'vertical'
        else:
            orientation = 'square'

        # Determine audio configuration
        if audio_channels == 1:
            audio_config = 'mono'
        elif audio_channels == 2:
            audio_config = 'stereo'
        else:
            audio_config = f'{audio_channels}ch'

        # Format duration as HH:MM:SS
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        logger.info(f"Phase 0 analysis: {width}x{height} {orientation}, {frame_rate}fps, {audio_config}, {duration_formatted}")

        # Store pre-analysis in database
        pre_analysis_data = {
            "duration": duration_formatted,
            "duration_seconds": duration_seconds,
            "resolution": f"{width}x{height}",
            "width": width,
            "height": height,
            "aspect_ratio": round(width / height, 3) if height > 0 else 0,
            "orientation": orientation,
            "framerate": frame_rate,
            "audio_channels": audio_channels,
            "audio_layout": audio_layout,
            "sample_rate": sample_rate,
            "audio_config": audio_config
        }

        db = SessionLocal()
        try:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.pre_analysis = pre_analysis_data
                db.commit()
        finally:
            db.close()

        processing_report["phases"]["phase0"] = {"status": "success", "data": pre_analysis_data}

        # Update cue block with technical metadata
        if asset_id:
            _update_sot_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 0 Complete: Technical Analysis',
                'Duration': duration_formatted,
                'Resolution': f'{width}x{height}',
                'Framerate': f'{frame_rate}fps',
                'Orientation': orientation,
                'AudioChannels': audio_config,
                'AudioLayout': audio_layout,
                'SampleRate': f'{sample_rate}Hz'
            })

        # ================================================================
        # PHASE 0.5: Audio Extraction and Whisper Transcription
        # - Extract audio as WAV for transcription
        # - Send to Whisper (medium model on kairo)
        # - Store transcription in cue block
        # ================================================================
        logger.info(f"Phase 0.5: Audio extraction and transcription for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase0.5', 'processing')

        # Extract audio as WAV for Whisper
        phase05_audio = working_dir / f"{temp_job_id}_0.5_audio_for_whisper.wav"
        audio_extract_cmd = [
            ffmpeg, "-y",
            "-i", str(input_file),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # WAV format
            "-ar", "16000",  # 16kHz sample rate (Whisper standard)
            "-ac", "1",  # Mono
            str(phase05_audio)
        ]
        subprocess.run(audio_extract_cmd, check=True, capture_output=True)
        logger.info(f"Phase 0.5: Audio extracted to {phase05_audio}")

        # Transcribe with Whisper
        try:
            from wpm_audio_router import transcribe_audio
            import asyncio

            # Run async transcription in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            transcription = loop.run_until_complete(transcribe_audio(str(phase05_audio)))
            loop.close()

            logger.info(f"Phase 0.5: Transcription complete, {len(transcription)} characters")

            # Update cue block with transcription
            if asset_id:
                _update_sot_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': 'Phase 0.5 Complete: Transcribed',
                    'Transcription': transcription
                })

        except Exception as e:
            logger.error(f"Phase 0.5: Transcription failed: {e}")
            # Continue processing even if transcription fails
            if asset_id:
                _update_sot_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': 'Phase 0.5 Complete: Transcription Failed',
                    'Transcription': f'[Transcription failed: {str(e)}]'
                })

        # ================================================================
        # PHASE 1: Video Normalization
        # - Convert to H.264/AAC MP4
        # - Normalize framerate to 29.97fps
        # - Normalize resolution (maintain aspect ratio)
        # - Video bitrate: 8Mbps VBR
        # ================================================================
        logger.info(f"Phase 1: Video normalization for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase1', 'processing')

        phase1_output = working_dir / f"{temp_job_id}_1_normalized.mp4"
        phase1_cmd = [
            ffmpeg, "-y",
            "-i", str(input_file),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",  # High quality
            "-maxrate", "8M",
            "-bufsize", "16M",
            "-r", "29.97",  # Broadcast standard framerate
            "-vf", "scale='if(gt(iw,1920),1920,-2)':'-2'",  # Max width 1920, maintain aspect
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-ac", "2",
            str(phase1_output)
        ]
        subprocess.run(phase1_cmd, check=True, capture_output=True)
        logger.info(f"Phase 1 complete: {phase1_output}")

        # Update cue block with Phase 1 completion
        if asset_id:
            _update_sot_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 1 Complete: Video Normalized'
            })

        # ================================================================
        # PHASE 1.1: Audio Channel Analysis and Dual-Mono Conversion
        # - Analyze left/right channel distribution
        # - Convert to dual-mono if channels are unbalanced
        # ================================================================
        logger.info(f"Phase 1.1: Audio channel analysis for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase1.1', 'processing')

        # Analyze audio channels with volumedetect and astats
        analyze_cmd = [
            ffmpeg,
            "-i", str(phase1_output),
            "-map", "0:a:0",
            "-af", "astats=measure_overall=Peak_level:measure_perchannel=Peak_level",
            "-f", "null",
            "-"
        ]
        analyze_result = subprocess.run(analyze_cmd, capture_output=True, text=True)
        astats_output = analyze_result.stderr

        # Parse channel levels from astats output
        # Look for lines like: [Parsed_astats_0 @ ...] Peak level dB: -12.34
        import re
        channel_levels = []
        for line in astats_output.split('\n'):
            if 'Peak level dB' in line:
                match = re.search(r'Peak level dB: ([-\d.]+)', line)
                if match:
                    channel_levels.append(float(match.group(1)))

        logger.info(f"Phase 1.1: Channel levels: {channel_levels}")

        # Determine if dual-mono conversion is needed
        needs_dual_mono = False
        if len(channel_levels) >= 2:
            left_level = channel_levels[0]
            right_level = channel_levels[1]

            # If one channel is significantly quieter (>10dB difference), convert to dual-mono
            level_diff = abs(left_level - right_level)
            if level_diff > 10:
                needs_dual_mono = True
                logger.info(f"Phase 1.1: Unbalanced channels detected ({level_diff:.1f}dB diff), converting to dual-mono")

        phase1_1_output = working_dir / f"{temp_job_id}_1.1_audio-fixed.mp4"

        if needs_dual_mono:
            # Convert to dual-mono: mix both channels and output to both L/R
            dual_mono_cmd = [
                ffmpeg, "-y",
                "-i", str(phase1_output),
                "-c:v", "copy",  # Don't re-encode video
                "-af", "pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1",  # Mix both channels equally
                "-c:a", "aac",
                "-b:a", "192k",
                str(phase1_1_output)
            ]
            subprocess.run(dual_mono_cmd, check=True, capture_output=True)
            logger.info(f"Phase 1.1 complete: Converted to dual-mono")

            if asset_id:
                _update_sot_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': 'Phase 1.1 Complete: Dual-Mono Conversion Applied',
                    'AudioProcessing': 'Dual-mono conversion (unbalanced channels detected)'
                })
        else:
            # Channels are balanced, just copy
            import shutil
            shutil.copy2(phase1_output, phase1_1_output)
            logger.info(f"Phase 1.1 complete: Channels balanced, no conversion needed")

            if asset_id:
                _update_sot_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': 'Phase 1.1 Complete: Audio Channels OK',
                    'AudioProcessing': 'Channels balanced'
                })

        # ================================================================
        # PHASE 2: Audio Normalization
        # - EBU R128 loudness normalization (-23 LUFS target)
        # - Dynamic range compression
        # - Peak limiting to -1dB
        # ================================================================
        logger.info(f"Phase 2: Audio normalization for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase2', 'processing')

        phase2_output = working_dir / f"{temp_job_id}_2_audio-normalized.mp4"
        phase2_cmd = [
            ffmpeg, "-y",
            "-i", str(phase1_1_output),
            "-c:v", "copy",  # Don't re-encode video
            "-af", "loudnorm=I=-23:TP=-1:LRA=11,acompressor=threshold=-18dB:ratio=4:attack=5:release=50",
            "-c:a", "aac",
            "-b:a", "192k",
            str(phase2_output)
        ]
        subprocess.run(phase2_cmd, check=True, capture_output=True)
        logger.info(f"Phase 2 complete: {phase2_output}")

        # Update cue block with Phase 2 completion
        if asset_id:
            _update_sot_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 2 Complete: Audio Normalized'
            })

        # ================================================================
        # PHASE 3: Trimming (if requested)
        # - Trim based on trim_start and trim_end
        # - Skip entirely if no trimming needed
        # ================================================================

        # Check if trimming is actually needed
        if trim_start != "00:00:00" or trim_end != "00:00:00":
            logger.info(f"Phase 3: Trimming for {temp_job_id}")
            _update_job_status(temp_job_id, 'phase3', 'processing')

            phase3_output = working_dir / f"{temp_job_id}_3_trimmed.mp4"

            if trim_end != "00:00:00":
                # Calculate duration
                def time_to_seconds(time_str):
                    h, m, s = map(float, time_str.split(':'))
                    return h * 3600 + m * 60 + s

                start_sec = time_to_seconds(trim_start)
                end_sec = time_to_seconds(trim_end)
                trim_duration = end_sec - start_sec

                phase3_cmd = [
                    ffmpeg, "-y",
                    "-ss", trim_start,
                    "-i", str(phase2_output),
                    "-t", str(trim_duration),
                    "-c", "copy",
                    str(phase3_output)
                ]
            else:
                # Trim from start only
                phase3_cmd = [
                    ffmpeg, "-y",
                    "-ss", trim_start,
                    "-i", str(phase2_output),
                    "-c", "copy",
                    str(phase3_output)
                ]

            subprocess.run(phase3_cmd, check=True, capture_output=True)
            logger.info(f"Phase 3 complete (trimmed): {phase3_output}")

            # Update cue block with Phase 3 completion
            if asset_id:
                _update_sot_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': 'Phase 3 Complete: Trimmed'
                })
        else:
            # No trimming needed - skip phase entirely and use Phase 2 output
            logger.info(f"Phase 3: Skipped (no trimming needed) for {temp_job_id}")
            phase3_output = phase2_output

            # Update cue block to reflect skipped phase
            if asset_id:
                _update_sot_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': 'Phase 3 Skipped: No Trimming Needed'
                })

        # ================================================================
        # PHASE 4: Derivative Extraction
        # - Generate 5 thumbnail options at different timepoints
        # - Audio extract as MP3 (full segment)
        # ================================================================
        logger.info(f"Phase 4: Derivative extraction for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase4', 'processing')

        # Get video duration for thumbnail spacing
        duration_probe = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(phase3_output)],
            capture_output=True, text=True, check=True
        )
        video_duration = float(duration_probe.stdout.strip())

        # Generate 15 thumbnail options at evenly spaced intervals
        # Skip first 2 seconds and last 2 seconds to avoid fade/black
        start_offset = 2
        end_offset = max(2, video_duration - 2)
        usable_duration = end_offset - start_offset
        num_thumbnails = 15  # Generate 15 options for user selection

        thumbnail_times = []
        if usable_duration > 0:
            # Generate evenly spaced timepoints
            for i in range(num_thumbnails):
                time_point = start_offset + (usable_duration * i / (num_thumbnails - 1))
                thumbnail_times.append(time_point)
        else:
            # Video too short, just use 1 second mark
            thumbnail_times = [1] * num_thumbnails

        phase4_thumbs = []
        thumbnail_filenames = []  # Store just filenames for database
        for i, time_point in enumerate(thumbnail_times, 1):
            thumb_file = working_dir / f"{temp_job_id}_4_thumb_{i:02d}.jpg"
            thumb_cmd = [
                ffmpeg, "-y",
                "-ss", str(time_point),
                "-i", str(phase3_output),
                "-vframes", "1",
                "-q:v", "2",
                str(thumb_file)
            ]
            subprocess.run(thumb_cmd, check=True, capture_output=True)
            phase4_thumbs.append(thumb_file)
            thumbnail_filenames.append(f"{temp_job_id}_4_thumb_{i:02d}.jpg")
            logger.info(f"Phase 4: Generated thumbnail {i}/{num_thumbnails} at {time_point:.1f}s")

        # Store thumbnail candidates in database for user selection
        db = SessionLocal()
        try:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.thumbnail_candidates = thumbnail_filenames
                # Set first thumbnail as default selection
                job.selected_thumbnail = thumbnail_filenames[7] if len(thumbnail_filenames) >= 8 else thumbnail_filenames[0]
                db.commit()
        finally:
            db.close()

        logger.info(f"Phase 4: Stored {len(thumbnail_filenames)} thumbnail candidates in database")

        # Audio extract (full segment)
        phase4_audio = working_dir / f"{temp_job_id}_4_audio.mp3"
        audio_cmd = [
            ffmpeg, "-y",
            "-i", str(phase3_output),
            "-vn",
            "-acodec", "libmp3lame",
            "-ab", "192k",
            str(phase4_audio)
        ]
        subprocess.run(audio_cmd, check=True, capture_output=True)
        logger.info(f"Phase 4 complete: 5 thumbnails + audio")

        # Update cue block with Phase 4 completion
        if asset_id:
            _update_sot_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 4 Complete: 5 Thumbnails + MP3 Generated'
            })

        # ================================================================
        # PHASE 5: Final Move and Rename
        # - Move to episode assets directory
        # - Rename with normalized slug
        # - Clean up working directory
        # ================================================================
        logger.info(f"Phase 5: Final move for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase5', 'processing')

        # Create final output directory (cross-platform)
        final_dir = media_root / "episodes" / episode / "assets" / "sots"
        final_dir.mkdir(parents=True, exist_ok=True)

        # Move and rename files
        final_video = final_dir / f"{normalized_slug}.mp4"
        final_audio = final_dir / f"{normalized_slug}.mp3"

        import shutil
        shutil.move(str(phase3_output), str(final_video))
        shutil.move(str(phase4_audio), str(final_audio))

        # Move all 15 thumbnails
        final_thumbs = []
        for i, thumb_file in enumerate(phase4_thumbs, 1):
            final_thumb = final_dir / f"{normalized_slug}-thumb-{i:02d}.jpg"
            shutil.move(str(thumb_file), str(final_thumb))
            final_thumbs.append(final_thumb)

        logger.info(f"Phase 5 complete: video, audio, and {len(final_thumbs)} thumbnails moved to {final_dir}")

        # Get video duration for metadata
        duration_cmd = [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(final_video)
        ]
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        duration = float(duration_result.stdout.strip())

        # Update database with final paths
        from database import SessionLocal
        from models_v2 import SOTProcessingJob

        db = SessionLocal()
        job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
        if job:
            job.current_phase = 'completed'
            job.status = 'completed'
            job.final_video_path = str(final_video.relative_to("/home/episodes"))
            job.final_audio_path = str(final_audio.relative_to("/home/episodes"))
            job.final_thumbnail_path = str(final_thumbs[0].relative_to("/home/episodes"))  # Store first thumbnail as primary
            db.commit()
        db.close()

        # Convert duration to HH:MM:SS format
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Build thumbnail URLs for all 15 options
        thumbnail_urls = [
            f"/episodes/{episode}/assets/sots/{normalized_slug}-thumb-{i:02d}.jpg"
            for i in range(1, 16)
        ]

        # ================================================================
        # PHASE 8: Post-Analysis (verify final output)
        # ================================================================
        logger.info(f"Phase 8: Post-analysis of final video for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase8', 'processing')

        # Analyze final video
        post_video_probe = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,r_frame_rate,codec_name,bit_rate",
             "-of", "json", str(final_video)],
            capture_output=True, text=True, check=True
        )
        post_video_info = json.loads(post_video_probe.stdout)
        post_video_stream = post_video_info['streams'][0] if post_video_info.get('streams') else {}

        post_analysis_data = {
            "duration": duration_formatted,
            "duration_seconds": duration,
            "resolution": f"{post_video_stream.get('width', 0)}x{post_video_stream.get('height', 0)}",
            "codec": post_video_stream.get('codec_name', 'unknown'),
            "bitrate": post_video_stream.get('bit_rate', 'unknown'),
            "file_size_mb": round(final_video.stat().st_size / (1024 * 1024), 2)
        }

        db = SessionLocal()
        try:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.post_analysis = post_analysis_data
                db.commit()
        finally:
            db.close()

        processing_report["phases"]["phase8"] = {"status": "success", "data": post_analysis_data}
        processing_report["overall_status"] = "completed"
        logger.info(f"Phase 8 complete: {post_analysis_data}")

        # Update cue block with final completion and all MediaURLs
        if asset_id:
            _update_sot_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Complete',
                'MediaURL': f"/episodes/{episode}/assets/sots/{normalized_slug}.mp4",
                'ThumbnailURL': thumbnail_urls[7],  # Middle thumbnail (8/15) as primary
                'ThumbnailOptions': thumbnail_urls,  # All 15 thumbnail URLs
                'AudioURL': f"/episodes/{episode}/assets/sots/{normalized_slug}.mp3",
                'Duration': duration_formatted
            })

        # Store final processing report in database
        db = SessionLocal()
        try:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.processing_report = processing_report
                db.commit()
        finally:
            db.close()

        # Handle devel_mode: Keep or clean up working directory
        if devel_mode:
            logger.info(f"DEVEL MODE: Keeping working directory with intermediate files: {working_dir}")
            processing_report["intermediate_files"] = [
                str(f.relative_to(media_root)) for f in working_dir.glob("*")
            ]
        else:
            logger.info(f"Cleaning up working directory: {working_dir}")
            import shutil
            shutil.rmtree(working_dir)

        logger.info(f"Multi-phase processing complete for {temp_job_id}")

        return {
            "temp_job_id": temp_job_id,
            "episode": episode,
            "slug": normalized_slug,
            "video_path": str(final_video.relative_to("/home/episodes")),
            "audio_path": str(final_audio.relative_to("/home/episodes")),
            "thumbnail_path": str(final_thumbs[7].relative_to("/home/episodes")),  # Primary (middle) thumbnail
            "thumbnail_options": [str(t.relative_to("/home/episodes")) for t in final_thumbs],
            "duration": duration,
            "status": "completed",
            "pre_analysis": pre_analysis_data,
            "post_analysis": post_analysis_data,
            "processing_report": processing_report,
            "devel_mode": devel_mode
        }

    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg error in phase {self.request.retries + 1}: {e.stderr if hasattr(e, 'stderr') else str(e)}"
        logger.error(error_msg)
        _update_job_status(temp_job_id, f"phase{self.request.retries + 1}", 'failed', error_msg)
        raise
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        _update_job_status(temp_job_id, 'unknown', 'failed', error_msg)
        raise
