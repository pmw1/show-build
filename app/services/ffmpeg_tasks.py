"""
FFmpeg processing tasks for Celery workers.

These tasks run on dedicated media processing workers (kairo/proxima)
with ffmpeg installed and handle video/audio processing operations.
"""

import os
import subprocess
from pathlib import Path
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


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
        logger.info(f"Processing SOT video: {video_path} for episode {episode}")

        # Create output directory structure
        episode_dir = Path("/home/episodes") / episode / "assets" / "sots"
        episode_dir.mkdir(parents=True, exist_ok=True)

        base_name = f"{slug}"

        # 1. Get video duration using ffprobe
        duration_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        duration = float(duration_result.stdout.strip())
        logger.info(f"Video duration: {duration}s")

        # 2. Generate thumbnail at 1 second mark
        thumbnail_path = episode_dir / f"{base_name}-thumb.jpg"
        thumbnail_cmd = [
            "ffmpeg", "-y",
            "-ss", "1",
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            str(thumbnail_path)
        ]
        subprocess.run(thumbnail_cmd, check=True, capture_output=True)
        logger.info(f"Thumbnail created: {thumbnail_path}")

        # 3. Extract audio as MP3
        audio_path = episode_dir / f"{base_name}.mp3"
        audio_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
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
                    "ffmpeg", "-y",
                    "-ss", trim_start,
                    "-i", video_path,
                    "-t", str(trim_duration),
                    "-c", "copy",
                    str(output_video_path)
                ]
            else:
                # Only trim from start
                video_cmd = [
                    "ffmpeg", "-y",
                    "-ss", trim_start,
                    "-i", video_path,
                    "-c", "copy",
                    str(output_video_path)
                ]
        else:
            # No trimming, just copy
            video_cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-c", "copy",
                str(output_video_path)
            ]

        subprocess.run(video_cmd, check=True, capture_output=True)
        logger.info(f"Video processed: {output_video_path}")

        # Clean up temp upload file
        if os.path.exists(video_path) and "/tmp/" in video_path:
            os.remove(video_path)
            logger.info(f"Removed temp file: {video_path}")

        # Return results
        return {
            "thumbnail_path": str(thumbnail_path.relative_to("/home/episodes")),
            "audio_path": str(audio_path.relative_to("/home/episodes")),
            "video_path": str(output_video_path.relative_to("/home/episodes")),
            "duration": duration,
            "status": "completed"
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise


@shared_task(bind=True, queue='media', name='services.ffmpeg_tasks.extract_audio_from_video')
def extract_audio_from_video(self, video_path: str, output_path: str):
    """Extract audio from video file."""
    try:
        cmd = [
            "ffmpeg", "-y",
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
    """Generate thumbnail from video at specified timestamp."""
    try:
        cmd = [
            "ffmpeg", "-y",
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
