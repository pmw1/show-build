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
import sys
import subprocess
import platform
import requests
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy import func

# Ensure /app is in Python path
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

# Cross-platform utilities
from platform_utils import (
    normalize_path,
    get_ffmpeg_binary,
    get_ffprobe_binary,
    get_platform_info,
    get_media_root
)

logger = get_task_logger(__name__)


@contextmanager
def db_session():
    """
    Database session context manager for safe session handling.

    CRITICAL FIX: Ensures database connections are always properly closed,
    preventing connection pool exhaustion and leaked sessions.

    Usage:
        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(id=123).first()
            job.status = 'completed'
            db.commit()

    The session is automatically closed on exit, even if an exception occurs.
    """
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database error (rolled back): {str(e)}")
        raise
    finally:
        db.close()


def transcribe_audio_simple(audio_path: str, max_retries: int = 3) -> str:
    """
    Transcription function for Celery workers with retry logic.
    Uses Whisper server via HTTP - no FastAPI dependencies required.

    CRITICAL FIX: Added exponential backoff retry logic to improve reliability.

    Tries multiple Whisper servers with retries:
    1. whisper-medium on Kairo (192.168.51.197:8887)
    2. openwebui-whisper-api fallback (192.168.51.197:8886)

    Retry strategy: Exponential backoff (1s, 2s, 4s) between attempts.

    Args:
        audio_path: Path to the audio file to transcribe
        max_retries: Maximum number of retry attempts (default 3)

    Returns:
        str: Transcription text

    Raises:
        Exception: If all servers and retries fail
    """
    import httpx
    import time

    # Whisper servers — LAN-IP endpoints only, tried in order.
    # whisperbox (.210) is PRIMARY: benchmarked ~2.7x faster than kairo on a real
    # 5-min clip (5.3s vs 14.5s), identical transcript, both running
    # faster-distil-whisper-large-v3 + int8_float16. whisperbox's RTX 3060 Ti is
    # DEDICATED to whisper; kairo's RTX 3090 sits ~93% busy / 17GB used from
    # ollama + fishspeech, so the bigger card actually loses here. kairo is the
    # fallback (still sub-15s, same quality).
    # (The old "whisper-medium:8000" docker-name entry was removed 2026-06-04 — it
    # only resolved on whisper-medium's own docker network, which our workers
    # aren't on; published host ports work from any worker.)
    whisper_servers = [
        {
            "name": "whisperbox (LAN)",
            "url": "http://192.168.51.210:8885/v1/audio/transcriptions",
            "timeout": 120.0
        },
        {
            "name": "kairo (LAN)",
            "url": "http://192.168.51.197:8887/v1/audio/transcriptions",
            "timeout": 120.0
        }
    ]

    last_error = None
    total_attempts = 0

    for attempt in range(max_retries):
        # Exponential backoff: 0s, 1s, 2s, 4s...
        if attempt > 0:
            backoff_delay = 2 ** (attempt - 1)
            logger.info(f"⏳ Whisper retry attempt {attempt + 1}/{max_retries}, waiting {backoff_delay}s...")
            time.sleep(backoff_delay)

        for server in whisper_servers:
            total_attempts += 1
            try:
                logger.info(f"🎤 Attempting transcription with {server['name']} (attempt {attempt + 1}/{max_retries})")

                with open(audio_path, 'rb') as audio_file:
                    files = {'file': (Path(audio_path).name, audio_file, 'audio/mpeg')}
                    data = {
                        'model': 'whisper-1',
                        'response_format': 'text',
                        'language': 'en'
                    }

                    # Use httpx for the request
                    with httpx.Client(timeout=server['timeout']) as client:
                        response = client.post(server['url'], files=files, data=data)

                    if response.status_code == 200:
                        transcript = response.text.strip()
                        logger.info(f"✅ Transcription successful: {len(transcript)} chars (after {total_attempts} attempts)")
                        return transcript
                    else:
                        last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                        logger.warning(f"❌ {server['name']} failed: {last_error}")

            except httpx.TimeoutException as e:
                last_error = f"Timeout after {server['timeout']}s"
                logger.warning(f"⏱️ {server['name']} timeout: {last_error}")
                continue
            except httpx.ConnectError as e:
                last_error = f"Connection failed: {str(e)}"
                logger.warning(f"🔌 {server['name']} connection error: {last_error}")
                continue
            except Exception as e:
                last_error = str(e)
                logger.warning(f"❌ {server['name']} error: {last_error}")
                continue

    # All retries exhausted
    error_msg = f"All Whisper servers failed after {total_attempts} total attempts. Last error: {last_error}"
    logger.error(f"🚨 {error_msg}")
    raise Exception(error_msg)


def derive_outcue(transcription: str, word_count: int = 5) -> str:
    """
    Derive outcue from transcription - last N words with "..." prefix.

    Args:
        transcription: Full transcription text
        word_count: Number of words to include (default 5)

    Returns:
        str: Outcue in format "...last five words here"
    """
    if not transcription or transcription.startswith('['):
        # No valid transcription or error message
        return ""

    # Clean up the transcription and split into words
    words = transcription.strip().split()

    if len(words) <= word_count:
        # If transcription is shorter than word_count, use all words
        return "..." + " ".join(words)

    # Get last N words
    last_words = words[-word_count:]
    return "..." + " ".join(last_words)


# Notification helper
def send_notification(title: str, message: str, priority: str = "normal", task_id: str = None):
    """Send notification to the LLM notification system."""
    try:
        notif_data = {
            "id": str(uuid.uuid4()),
            "title": title,
            "message": message,
            "priority": priority,
            "type": "ffmpeg_processing",
            "operationId": task_id or str(uuid.uuid4()),
            "success": True,
            "read": False,
            "dismissed": False,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send to API
        # CRITICAL FIX: Use environment variable for API key (security)
        llm_state_api_key = os.getenv("LLM_STATE_API_KEY", "")
        if not llm_state_api_key:
            logger.warning("LLM_STATE_API_KEY not set, skipping notification")
            return

        response = requests.post(
            "http://192.168.51.210:8888/llm-state/notifications",
            json={"notifications": [notif_data]},
            headers={"X-API-Key": llm_state_api_key},
            timeout=3
        )

        if response.status_code == 200:
            logger.info(f"Notification sent: {title}")
        else:
            logger.warning(f"Notification failed: {response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to send notification: {str(e)}")

# Log worker platform on module load
_platform_info = get_platform_info()
logger.info(f"🖥️  FFmpeg Tasks Module Loaded on {_platform_info['platform']} ({_platform_info['hostname']})")


def calculate_frame_sharpness(image_path: str, ffmpeg: str = None) -> float:
    """
    Calculate frame sharpness using Laplacian variance method.

    Uses FFmpeg to compute edge detection and measures variance.
    Higher values = sharper image, lower values = blurry.

    Typical thresholds:
    - < 50: Very blurry (motion blur, out of focus)
    - 50-100: Somewhat blurry
    - 100-200: Acceptable sharpness
    - > 200: Sharp/detailed image

    Args:
        image_path: Path to the image file
        ffmpeg: Path to ffmpeg binary (auto-detected if None)

    Returns:
        float: Sharpness score (higher = sharper)
    """
    if ffmpeg is None:
        ffmpeg = get_ffmpeg_binary()

    try:
        # Use FFmpeg to calculate edge variance via the 'entropy' of edge-detected image
        # This applies a Laplacian edge detection and measures the standard deviation
        cmd = [
            ffmpeg, "-y",
            "-i", str(image_path),
            "-vf", "format=gray,convolution=0 -1 0 -1 4 -1 0 -1 0:0 -1 0 -1 4 -1 0 -1 0:0 -1 0 -1 4 -1 0 -1 0,signalstats",
            "-f", "null", "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Parse signalstats output for YAVG (average luminance of edge-detected image)
        # Higher edge content = sharper image
        stderr = result.stderr

        # Look for lavfi.signalstats.YAVG or similar metrics
        import re

        # Try to find YAVG (average luminance after edge detection)
        yavg_match = re.search(r'YAVG:\s*([\d.]+)', stderr)
        if yavg_match:
            sharpness = float(yavg_match.group(1))
            return sharpness

        # Fallback: measure file size as proxy (more detail = larger compressed size)
        # This is a rough approximation but works for comparing similar frames
        file_size = os.path.getsize(image_path)
        # Normalize to a 0-500 range based on typical thumbnail sizes
        sharpness = min(500, file_size / 100)
        logger.debug(f"Using file size proxy for sharpness: {sharpness:.1f}")
        return sharpness

    except subprocess.TimeoutExpired:
        logger.warning(f"Sharpness calculation timed out for {image_path}")
        return 0.0
    except Exception as e:
        logger.warning(f"Failed to calculate sharpness for {image_path}: {str(e)}")
        # Fallback to file size proxy
        try:
            file_size = os.path.getsize(image_path)
            return min(500, file_size / 100)
        except:
            return 0.0


def calculate_sharpness_simple(image_path: str) -> float:
    """
    Simple sharpness calculation using file size and image analysis.

    More detailed/sharp images compress to larger files because they have
    more high-frequency content that's harder to compress.

    This is a fast, reliable proxy when FFmpeg filter analysis fails.

    Args:
        image_path: Path to the image file

    Returns:
        float: Sharpness score (higher = sharper)

    Raises:
        FileNotFoundError: If the image file doesn't exist
        ValueError: If the image file is empty or corrupted
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Thumbnail file not found: {image_path}")

    file_size = os.path.getsize(image_path)

    # A truncated ffmpeg write can leave a near-empty file; treat that as corrupt.
    # Anything larger but still small (e.g. a near-uniform black/fade frame that
    # PNG compresses well) is valid — it just gets a low sharpness score.
    MIN_VALID_SIZE = 200
    if file_size < MIN_VALID_SIZE:
        raise ValueError(f"Thumbnail file truncated ({file_size} bytes): {image_path}")

    # Validate PNG magic bytes — definitive signal that ffmpeg produced a real PNG
    with open(image_path, 'rb') as f:
        magic = f.read(8)
        # PNG magic: 89 50 4E 47 0D 0A 1A 0A
        if magic[:4] != b'\x89PNG':
            raise ValueError(f"Invalid PNG file (bad magic bytes): {image_path}")

    # PNG files are typically larger than JPEG, adjust threshold
    # Typical PNG thumbnail: 30KB-150KB
    # Very blurry: < 30KB, Sharp: > 80KB
    sharpness = file_size / 300  # Scale to roughly 0-500 for PNG
    return sharpness


# Sharpness thresholds (adjusted for PNG which is larger than JPEG)
SHARPNESS_THRESHOLD_BLURRY = 100  # Below this = blurry
SHARPNESS_THRESHOLD_WARNING = 150  # Below this = warn user


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
        task_id = self.request.id
        logger.info(f"🎬 Processing SOT video on {worker_name} ({worker_platform}): {video_path} for episode {episode}")

        # Send start notification
        send_notification(
            f"SOT Processing Started",
            f"Processing {slug} on {worker_name} ({worker_platform})",
            priority="normal",
            task_id=task_id
        )
        self.update_state(state='PROGRESS', meta={'stage': 'Starting', 'progress': 0})

        # Normalize input path for this platform
        input_video = normalize_path(video_path)
        if not input_video.exists():
            raise FileNotFoundError(f"Input video not found: {input_video}")

        # Create output directory structure (cross-platform)
        media_root = get_media_root()
        episode_dir = media_root / "episodes" / episode / "assets" / "video"
        episode_dir.mkdir(parents=True, exist_ok=True)

        base_name = f"{slug}"

        # Get platform-appropriate binaries
        ffmpeg = get_ffmpeg_binary()
        ffprobe = get_ffprobe_binary()

        # 1. Get video duration using ffprobe
        self.update_state(state='PROGRESS', meta={'stage': 'Analyzing video', 'progress': 10})
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

        send_notification(
            f"Video Analyzed",
            f"{slug}: Duration {duration:.1f}s detected",
            priority="normal",
            task_id=task_id
        )

        # 2. Generate thumbnail at 1 second mark (PNG format)
        self.update_state(state='PROGRESS', meta={'stage': 'Generating thumbnail', 'progress': 30})
        thumbnail_path = episode_dir / f"{base_name}-thumb.png"
        thumbnail_cmd = [
            ffmpeg, "-y",
            "-ss", "1",
            "-i", str(input_video),
            "-vframes", "1",
            str(thumbnail_path)
        ]
        subprocess.run(thumbnail_cmd, check=True, capture_output=True)

        # Validate thumbnail was created properly
        if not thumbnail_path.exists():
            raise RuntimeError(f"Thumbnail generation failed - file not created: {thumbnail_path}")
        if thumbnail_path.stat().st_size < 5000:
            raise RuntimeError(f"Thumbnail appears corrupted - file too small: {thumbnail_path.stat().st_size} bytes")

        logger.info(f"Thumbnail created: {thumbnail_path}")

        send_notification(
            f"Thumbnail Generated",
            f"{slug}: Thumbnail created",
            priority="normal",
            task_id=task_id
        )

        # 3. Extract audio as MP3
        self.update_state(state='PROGRESS', meta={'stage': 'Extracting audio', 'progress': 50})
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

        send_notification(
            f"Audio Extracted",
            f"{slug}: Audio track extracted to MP3",
            priority="normal",
            task_id=task_id
        )

        # 4. Process video (trim if needed, otherwise copy)
        self.update_state(state='PROGRESS', meta={'stage': 'Processing video', 'progress': 70})
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

        send_notification(
            f"Video Processed",
            f"{slug}: Video encoding complete",
            priority="normal",
            task_id=task_id
        )

        # Clean up temp upload file (cross-platform temp detection)
        self.update_state(state='PROGRESS', meta={'stage': 'Cleaning up', 'progress': 90})
        input_video_str = str(input_video)
        is_temp = any(temp_marker in input_video_str.lower() for temp_marker in ['/tmp/', '\\temp\\', 'c:\\temp'])
        if input_video.exists() and is_temp:
            input_video.unlink()
            logger.info(f"Removed temp file: {input_video}")

        # Send completion notification
        send_notification(
            f"✅ SOT Processing Complete",
            f"{slug}: All assets generated successfully (thumbnail, audio, video)",
            priority="normal",
            task_id=task_id
        )
        self.update_state(state='PROGRESS', meta={'stage': 'Complete', 'progress': 100})

        # Return results with worker info
        return {
            "thumbnail_path": str(thumbnail_path),
            "audio_path": str(audio_path),
            "video_path": str(output_video_path),
            "duration": duration,
            "status": "completed",
            "worker": worker_name,
            "platform": worker_platform,
            "task_id": task_id
        }

    except subprocess.CalledProcessError as e:
        # CRITICAL FIX: Properly extract FFmpeg stderr for debugging
        # stderr is bytes when capture_output=True without text=True
        if hasattr(e, 'stderr') and e.stderr:
            error_msg = e.stderr.decode('utf-8', errors='replace') if isinstance(e.stderr, bytes) else str(e.stderr)
        else:
            error_msg = f"Exit code {e.returncode}: {str(e)}"
        logger.error(f"FFmpeg error: {error_msg}")
        send_notification(
            f"❌ SOT Processing Failed",
            f"{slug}: FFmpeg error - {error_msg[:100]}",
            priority="high",
            task_id=self.request.id
        )
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        send_notification(
            f"❌ SOT Processing Failed",
            f"{slug}: {str(e)[:100]}",
            priority="high",
            task_id=self.request.id
        )
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


@shared_task(bind=True, queue='media', name='services.ffmpeg_tasks.generate_episode_mp3',
             soft_time_limit=3600, time_limit=7200)
def generate_episode_mp3(self, episode: str, profile_id: int = None, bitrate: str = "192k", source_file: str = None):
    """Generate MP3 from master episode video file.

    Supports .mov, .mp4, and .avi source files in the episode exports directory.
    Reports progress via celery state updates for UI polling.

    When profile_id is provided, encoding parameters are loaded from the
    mp3_encoding_profiles database table. Otherwise falls back to bitrate arg.

    Args:
        episode: Episode number string (e.g. "0261")
        profile_id: Optional database profile ID to load encoding settings from
        bitrate: Fallback MP3 bitrate if no profile_id (default "192k")
        source_file: Optional specific source filename to use (e.g. "0261.avi")
    """
    # Load profile settings from database if profile_id provided
    profile_settings = None
    if profile_id:
        try:
            from database import SessionLocal
            from models_episode import Mp3EncodingProfile
            db = SessionLocal()
            try:
                profile = db.query(Mp3EncodingProfile).filter(
                    Mp3EncodingProfile.id == profile_id
                ).first()
                if profile:
                    profile_settings = {
                        "bitrate": profile.bitrate,
                        "sample_rate": profile.sample_rate,
                        "channels": profile.channels,
                        "quality": profile.quality,
                        "normalize_audio": profile.normalize_audio,
                        "name": profile.name,
                    }
                    logger.info(f"Using MP3 profile '{profile.name}': {profile.bitrate}, {profile.sample_rate}Hz, {profile.channels}ch")
                else:
                    logger.warning(f"MP3 profile {profile_id} not found, using defaults")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to load MP3 profile {profile_id}: {e}, using defaults")

    # Resolve encoding parameters
    enc_bitrate = profile_settings["bitrate"] if profile_settings else bitrate
    enc_sample_rate = profile_settings["sample_rate"] if profile_settings else 44100
    enc_channels = profile_settings["channels"] if profile_settings else 2
    enc_quality = profile_settings["quality"] if profile_settings else None
    enc_normalize = profile_settings["normalize_audio"] if profile_settings else False

    media_root = get_media_root()
    exports_dir = os.path.join(media_root, "episodes", episode, "exports")

    # Use specific source file if provided, otherwise auto-detect
    source_path = None
    if source_file:
        candidate = os.path.join(exports_dir, source_file)
        if os.path.isfile(candidate):
            source_path = candidate
        else:
            raise FileNotFoundError(f"Specified source file not found: {source_file}")
    else:
        # Find source video (.mov preferred, then .mp4, then .avi)
        for ext in [".mov", ".mp4", ".avi"]:
            candidate = os.path.join(exports_dir, f"{episode}{ext}")
            if os.path.isfile(candidate):
                source_path = candidate
                break

    if not source_path:
        raise FileNotFoundError(f"No source video found for episode {episode} in {exports_dir}")

    output_path = os.path.join(exports_dir, f"{episode}.mp3")
    logger.info(f"Generating MP3: {source_path} -> {output_path}")

    self.update_state(state='PROGRESS', meta={'progress': 5, 'stage': 'starting'})

    try:
        ffmpeg = get_ffmpeg_binary()
        cmd = [
            ffmpeg, "-y",
            "-i", source_path,
            "-vn",
            "-acodec", "libmp3lame",
        ]

        # VBR mode (quality) takes precedence over CBR (bitrate)
        if enc_quality is not None:
            cmd.extend(["-q:a", str(enc_quality)])
        else:
            cmd.extend(["-ab", enc_bitrate])

        cmd.extend(["-ar", str(enc_sample_rate)])
        cmd.extend(["-ac", str(enc_channels)])

        # Audio normalization (EBU R128)
        if enc_normalize:
            cmd.extend(["-af", "loudnorm=I=-16:LRA=11:TP=-1.5"])

        cmd.append(output_path)

        self.update_state(state='PROGRESS', meta={'progress': 10, 'stage': 'encoding'})

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, stderr = process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='replace')[-500:]
            raise subprocess.CalledProcessError(process.returncode, cmd, stderr=error_msg)

        self.update_state(state='PROGRESS', meta={'progress': 95, 'stage': 'finalizing'})

        file_size = os.path.getsize(output_path)
        file_size_mb = round(file_size / (1024 * 1024), 1)

        logger.info(f"MP3 generated: {output_path} ({file_size_mb} MB)")

        return {
            "mp3_path": output_path,
            "file_size_mb": file_size_mb,
            "source": os.path.basename(source_path),
            "profile": profile_settings["name"] if profile_settings else "default",
            "bitrate": enc_bitrate,
            "sample_rate": enc_sample_rate,
            "channels": enc_channels,
            "status": "completed"
        }

    except subprocess.CalledProcessError as e:
        error_msg = str(e.stderr) if hasattr(e, 'stderr') else str(e)
        logger.error(f"MP3 generation failed: {error_msg}")
        # Clean up partial output
        if os.path.exists(output_path):
            os.remove(output_path)
        raise
    except Exception as e:
        logger.error(f"MP3 generation error: {str(e)}")
        if os.path.exists(output_path):
            os.remove(output_path)
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


@shared_task(bind=True, queue='media', name='services.ffmpeg_tasks.process_vo_montage')
def process_vo_montage(
    self,
    clips_data: list,
    episode: str,
    slug: str,
    asset_id: str
):
    """
    Process VO montage from multiple video clips with trim points.

    Args:
        clips_data: List of dicts with keys: video_path, trim_start, trim_end
                   Example: [{"video_path": "/path/to/video.mp4",
                             "trim_start": "00:00:10:00",
                             "trim_end": "00:00:20:00"}, ...]
        episode: Episode number (e.g., "0245")
        slug: Item slug for naming
        asset_id: AssetID for final output

    Returns:
        dict: {
            "video_path": str,
            "duration": float,
            "clip_count": int
        }
    """
    try:
        worker_name = platform.node()
        worker_platform = platform.system()
        logger.info(f"🎞️  Processing VO montage on {worker_name} ({worker_platform}): {len(clips_data)} clips for episode {episode}")

        # Get platform-appropriate binaries
        ffmpeg = get_ffmpeg_binary()
        ffprobe = get_ffprobe_binary()

        # Create output directory structure
        media_root = get_media_root()
        episode_dir = media_root / "episodes" / episode / "assets" / "video"
        episode_dir.mkdir(parents=True, exist_ok=True)

        # Create temp directory for trimmed clips
        temp_dir = episode_dir / "temp_montage"
        temp_dir.mkdir(exist_ok=True)

        trimmed_clips = []
        total_duration = 0.0

        # Helper function to convert timecode to seconds
        def timecode_to_seconds(timecode):
            """Convert HH:MM:SS:FF timecode to seconds (assuming 30fps for frames)."""
            parts = timecode.split(':')
            if len(parts) == 3:
                h, m, s = map(float, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 4:
                h, m, s, f = map(float, parts)
                return h * 3600 + m * 60 + s + (f / 30.0)
            return 0.0

        # Step 1: Trim each clip
        for idx, clip_data in enumerate(clips_data):
            video_path = normalize_path(clip_data['video_path'])
            trim_start = clip_data['trim_start']
            trim_end = clip_data['trim_end']

            if not video_path.exists():
                logger.error(f"Clip {idx} not found: {video_path}")
                continue

            # Convert timecodes to seconds
            start_sec = timecode_to_seconds(trim_start)
            end_sec = timecode_to_seconds(trim_end)
            clip_duration = end_sec - start_sec

            if clip_duration <= 0:
                logger.warning(f"Clip {idx} has invalid duration, skipping")
                continue

            # Output path for trimmed clip
            trimmed_clip_path = temp_dir / f"clip_{idx:03d}.mp4"

            # Trim the clip using FFmpeg
            # Determine video encoder based on platform
            from platform_utils import IS_WINDOWS, has_nvidia_gpu
            if IS_WINDOWS and has_nvidia_gpu():
                video_encoder_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23"]
            else:
                video_encoder_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "23"]

            trim_cmd = [
                ffmpeg, "-y",
                "-ss", str(start_sec),
                "-i", str(video_path),
                "-t", str(clip_duration),
                *video_encoder_args,
                "-c:a", "aac",
                "-b:a", "192k",
                str(trimmed_clip_path)
            ]

            logger.info(f"Trimming clip {idx}: {start_sec}s to {end_sec}s ({clip_duration}s)")
            subprocess.run(trim_cmd, check=True, capture_output=True)

            trimmed_clips.append(trimmed_clip_path)
            total_duration += clip_duration

            logger.info(f"✓ Clip {idx} trimmed: {trimmed_clip_path}")

        if not trimmed_clips:
            raise ValueError("No valid clips to concatenate")

        # Step 2: Create concat file for FFmpeg
        concat_file = temp_dir / "concat_list.txt"
        with open(concat_file, 'w') as f:
            for clip_path in trimmed_clips:
                # FFmpeg concat requires forward slashes even on Windows
                f.write(f"file '{clip_path.as_posix()}'\n")

        logger.info(f"Created concat file with {len(trimmed_clips)} clips")

        # Step 3: Concatenate all clips into final montage
        output_video_path = episode_dir / f"{slug}.mp4"

        concat_cmd = [
            ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(output_video_path)
        ]

        logger.info(f"Concatenating {len(trimmed_clips)} clips into final montage")
        subprocess.run(concat_cmd, check=True, capture_output=True)

        logger.info(f"✓ Montage created: {output_video_path}")

        # Step 4: Clean up temporary files
        for clip_path in trimmed_clips:
            if clip_path.exists():
                clip_path.unlink()
        concat_file.unlink()
        temp_dir.rmdir()

        logger.info(f"✓ Cleaned up {len(trimmed_clips)} temp files")

        # Step 5: Get final video duration
        duration_cmd = [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(output_video_path)
        ]
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        final_duration = float(duration_result.stdout.strip())

        logger.info(f"🎬 VO Montage complete: {final_duration}s from {len(clips_data)} clips")

        return {
            "video_path": str(output_video_path),
            "duration": final_duration,
            "clip_count": len(clips_data),
            "status": "completed",
            "worker": worker_name,
            "platform": worker_platform
        }

    except subprocess.CalledProcessError as e:
        # CRITICAL FIX: Properly extract FFmpeg stderr for debugging
        if hasattr(e, 'stderr') and e.stderr:
            stderr_text = e.stderr.decode('utf-8', errors='replace') if isinstance(e.stderr, bytes) else str(e.stderr)
        else:
            stderr_text = f"Exit code {e.returncode}"
        logger.error(f"FFmpeg error during montage: {stderr_text}")
        # Clean up on error
        if 'temp_dir' in locals() and temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during montage: {str(e)}")
        # Clean up on error
        if 'temp_dir' in locals() and temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def _update_job_status(temp_job_id: str, phase: str, status: str, error_message: str = None):
    """Update job status in database (helper function for multi-phase processing)."""
    try:
        from models_v2 import SOTProcessingJob

        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.current_phase = phase
                job.status = status
                if error_message:
                    job.error_message = error_message
                db.commit()
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


def _replace_sot_cue_asset_id(episode: str, old_asset_id: str, new_asset_id: str):
    """
    Replace the AssetID in a SOT cue block (source → final).

    When processing completes, the cue block should reference the final processed
    asset rather than the source upload.

    Args:
        episode: Episode number
        old_asset_id: Original source AssetID
        new_asset_id: New final AssetID to replace it with
    """
    try:
        from models_v2 import Rundown, RundownItem, Episode
        import re

        with db_session() as db:
            # Find the rundown for this episode by joining with Episode
            rundown = db.query(Rundown).join(Episode).filter(Episode.episode_number == episode).first()
            if not rundown:
                logger.warning(f"No rundown found for episode {episode}")
                return

            # Search all rundown items for SOT cue with matching AssetID
            items = db.query(RundownItem).filter_by(rundown_id=rundown.id).all()

            for item in items:
                if not item.script_content:
                    continue

                # Look for SOT cue block with matching AssetID (case-insensitive).
                # Matches expanded + collapsed cues; the whole block (incl. its
                # original Begin marker) is captured and field-edited in place,
                # so the collapsed marker is preserved.
                cue_pattern = re.compile(
                    r'(<!-- Begin Cue(?: collapsed)? -->(?:(?!<!-- End Cue -->).)*?\[Type:\s*SOT\](?:(?!<!-- End Cue -->).)*?<!-- End Cue -->)',
                    re.DOTALL | re.IGNORECASE
                )
                asset_pattern = re.compile(r'\[Asset[Ii][Dd]:\s*' + re.escape(old_asset_id) + r'\s*\]', re.IGNORECASE)

                for match in cue_pattern.finditer(item.script_content):
                    cue_block = match.group(1)

                    # Check if this cue block contains our asset_id
                    if not asset_pattern.search(cue_block):
                        continue

                    # Replace old AssetID with new one (case-insensitive)
                    updated_cue = re.sub(
                        r'\[Asset[Ii][Dd]:\s*' + re.escape(old_asset_id) + r'\s*\]',
                        f'[AssetID: {new_asset_id}]',
                        cue_block,
                        flags=re.IGNORECASE
                    )

                    # Also add SourceAssetID field to preserve reference
                    if '[SourceAssetID:' not in updated_cue.lower():
                        updated_cue = updated_cue.replace(
                            f'[AssetID: {new_asset_id}]',
                            f'[AssetID: {new_asset_id}]\n[SourceAssetID: {old_asset_id}]'
                        )

                    # Replace in script_content
                    item.script_content = item.script_content.replace(cue_block, updated_cue)
                    db.commit()

                    logger.info(f"✅ Replaced AssetID in cue: {old_asset_id} → {new_asset_id}")
                    return

            logger.warning(f"No SOT cue found with AssetID {old_asset_id} in episode {episode}")

    except Exception as e:
        logger.error(f"Failed to replace SOT cue AssetID: {e}")


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
        from models_v2 import Rundown, RundownItem, Episode
        import re

        with db_session() as db:
            # Find the rundown for this episode by joining with Episode
            rundown = db.query(Rundown).join(Episode).filter(Episode.episode_number == episode).first()
            if not rundown:
                logger.warning(f"No rundown found for episode {episode}")
                return

            # Search all rundown items for SOT cue with matching AssetID
            items = db.query(RundownItem).filter_by(rundown_id=rundown.id).all()

            for item in items:
                if not item.script_content:
                    continue

                # Look for SOT cue block with matching AssetID (case-insensitive for field names)
                # The cue block contains [Type: SOT] and [Asset Id: xxx] or [AssetID: xxx] in any order
                cue_pattern = re.compile(
                    r'(<!-- Begin Cue(?: collapsed)? -->(?:(?!<!-- End Cue -->).)*?\[Type:\s*SOT\](?:(?!<!-- End Cue -->).)*?<!-- End Cue -->)',
                    re.DOTALL | re.IGNORECASE
                )
                # Find cue blocks and check if they contain our asset_id
                # Match both "Asset Id" (space-separated) and "AssetId"/"AssetID" (camelCase)
                asset_pattern = re.compile(r'\[Asset\s*[Ii][Dd]:\s*' + re.escape(asset_id) + r'\s*\]', re.IGNORECASE)

                # Find all SOT cue blocks and check each for our asset_id
                for match in cue_pattern.finditer(item.script_content):
                    cue_block = match.group(1)

                    # Check if this cue block contains our asset_id
                    if not asset_pattern.search(cue_block):
                        continue

                    updated_cue = cue_block

                    # Update each field in the cue block (case-insensitive matching)
                    for field, value in updates.items():
                        # Check if field exists (case-insensitive), update it
                        field_pattern = re.compile(rf'\[{field}:\s*[^\]]*\]', re.IGNORECASE)
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
                    return

            logger.warning(f"No SOT cue found with AssetID {asset_id} in episode {episode}")

    except Exception as e:
        logger.error(f"Failed to update SOT cue block: {e}")


def _generate_asset_id() -> str:
    """
    Generate a unique AssetID for SOT clips.

    Uses local AssetIDService when available (main server),
    falls back to API call for remote workers (Windows/external).
    """
    try:
        # Try local service first (main server/Docker)
        from services.asset_id import AssetIDService
        return AssetIDService.generate('CUE')
    except ImportError:
        # Remote worker - use API call
        import requests
        try:
            response = requests.post(
                "http://192.168.51.210:8888/assetid/generate",
                json={"entity_type": "CUE", "reason": "sot_clip_generation"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("asset_id", data.get("id"))
            else:
                raise RuntimeError(f"AssetID API returned {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to generate AssetID via API: {e}")
            raise


def _process_individual_clips(temp_job_id, episode, slug, clips, parent_asset_id, working_dir, normalized_slug):
    """
    DEPRECATED: This function is no longer used.

    As of 2026-01-21, individual clips are processed as independent SOT cues
    via the frontend's submit-multiple event. Each clip gets its own AssetID
    and is processed via the standard single_trim workflow.

    This parent-child approach is deprecated because:
    - Complex parent cue lookup that can fail
    - Single point of failure for multi-clip jobs
    - Unable to process clips in parallel

    The new approach:
    - Frontend generates AssetIDs for each clip
    - Frontend inserts N independent cue blocks
    - Frontend triggers N independent processing jobs
    - Each uses standard single_trim workflow

    Legacy Args (kept for reference):
        temp_job_id: Job ID
        episode: Episode number
        slug: Base slug for naming
        clips: List of clip objects with time_start, time_end, slug
        parent_asset_id: AssetID of parent cue block
        working_dir: Working directory path
        normalized_slug: Normalized slug for filenames
    """
    # DEPRECATION WARNING
    logger.warning("⚠️ DEPRECATED: _process_individual_clips() called - this workflow is deprecated")
    logger.warning("⚠️ Individual clips should now be processed as independent SOTs via single_trim workflow")
    logger.warning("⚠️ The frontend should emit 'submit-multiple' event with separate AssetIDs per clip")

    # Mark job as failed with deprecation notice
    _update_job_status(
        temp_job_id,
        'deprecated_workflow',
        'failed',
        'individual_clips workflow is deprecated. Please use the updated frontend that creates independent SOT cues.'
    )

    raise DeprecationWarning(
        "individual_clips workflow is deprecated. "
        "Use the updated frontend that emits independent SOT cues via 'submit-multiple' event. "
        "Each clip should be processed as a separate single_trim job."
    )

    # === LEGACY CODE BELOW (unreachable, kept for reference) ===
    logger.info(f"🎬 INDIVIDUAL CLIPS: Processing {len(clips)} clips for {temp_job_id}")

    # Validate inputs early
    if not clips:
        error_msg = "No clips provided for individual clips processing"
        logger.error(f"❌ {error_msg}")
        _update_job_status(temp_job_id, 'failed', 'failed', error_msg)
        raise ValueError(error_msg)

    if not parent_asset_id:
        error_msg = "No parent_asset_id provided for individual clips processing"
        logger.error(f"❌ {error_msg}")
        _update_job_status(temp_job_id, 'failed', 'failed', error_msg)
        raise ValueError(error_msg)

    # Get platform-appropriate binaries
    ffmpeg = get_ffmpeg_binary()
    ffprobe = get_ffprobe_binary()

    input_file = working_dir / f"{temp_job_id}_upload.mp4"
    if not input_file.exists():
        error_msg = f"Upload file not found: {input_file}"
        logger.error(f"❌ {error_msg}")
        _update_job_status(temp_job_id, 'failed', 'failed', error_msg)
        raise FileNotFoundError(error_msg)

    clip_results = []

    try:
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

            # Validate clip times
            if duration_sec <= 0:
                error_msg = f"Invalid clip {i} times: start={clip_start}, end={clip_end} (duration={duration_sec}s)"
                logger.error(f"❌ {error_msg}")
                _update_job_status(temp_job_id, f'clip{i}_failed', 'failed', error_msg)
                raise ValueError(error_msg)

            # Extract clip with FFmpeg
            extract_cmd = [
                ffmpeg, "-y",
                "-ss", str(start_sec),
                "-i", str(input_file),
                "-t", str(duration_sec),
                "-c", "copy",  # Fast extraction, no re-encoding
                str(clip_extracted)
            ]
            result = subprocess.run(extract_cmd, capture_output=True)
            if result.returncode != 0:
                stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else 'Unknown'
                error_msg = f"FFmpeg clip extraction failed for clip {i}: {stderr[:200]}"
                logger.error(f"❌ {error_msg}")
                _update_job_status(temp_job_id, f'clip{i}_extraction_failed', 'failed', error_msg)
                raise RuntimeError(error_msg)
            logger.info(f"✅ Clip {i} extracted: {clip_extracted}")

            # Now run full processing pipeline on this clip
            # (Phases 0, 0.5, 1, 1.1, 2, 3-skip, 4, 5)
            clip_result = _process_single_clip(
                clip_extracted, clip_slug, clip_asset_id, episode,
                working_dir, i, temp_job_id
            )

            clip_results.append(clip_result)

        # Phase 6: Insert multiple cue blocks into parent segment
        logger.info(f"📝 Inserting {len(clip_results)} cue blocks for parent {parent_asset_id}")
        _update_job_status(temp_job_id, 'inserting_cues', 'processing')

        inserted_count = _insert_multiple_cue_blocks(episode, clip_results, parent_asset_id)
        logger.info(f"✅ Successfully inserted {inserted_count} cue blocks")

        # Mark job as complete
        _update_job_status(temp_job_id, 'complete', 'completed')

        logger.info(f"✅ INDIVIDUAL CLIPS: Completed processing {len(clips)} clips")

        return {
            "status": "completed",
            "clips": clip_results,
            "message": f"Processed {len(clips)} individual clips successfully"
        }

    except CueInsertionError as e:
        # Specific handling for cue insertion failures
        error_msg = f"Failed to insert cue blocks: {str(e)}"
        logger.error(f"❌ INDIVIDUAL CLIPS FAILED: {error_msg}")
        _update_job_status(temp_job_id, 'cue_insertion_failed', 'failed', error_msg)
        raise

    except Exception as e:
        # Catch-all for any other errors
        error_msg = f"Individual clips processing failed: {str(e)}"
        logger.error(f"❌ INDIVIDUAL CLIPS FAILED: {error_msg}")
        _update_job_status(temp_job_id, 'failed', 'failed', error_msg)
        raise


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

    # PHASE 0.5: Audio extraction and Whisper transcription
    logger.info(f"Clip {clip_index} Phase 0.5: Extracting audio for transcription")

    phase05_audio = working_dir / f"clip{clip_index}_audio_for_whisper.wav"
    audio_extract_cmd = [
        ffmpeg, "-y",
        "-i", str(clip_file),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(phase05_audio)
    ]

    # Extract audio with error capture
    audio_result = subprocess.run(audio_extract_cmd, capture_output=True)
    if audio_result.returncode != 0:
        stderr = audio_result.stderr.decode('utf-8', errors='replace') if audio_result.stderr else 'Unknown'
        logger.warning(f"Phase 0.5 Clip {clip_index}: Audio extraction failed: {stderr[:200]}")
        # Continue without transcription rather than failing entirely
        transcription_text = '[Audio extraction failed]'
        outcue_text = ''
    else:
        # Transcribe with Whisper
        transcription_text = None
        outcue_text = ""
        try:
            transcription_text = transcribe_audio_simple(str(phase05_audio))
            outcue_text = derive_outcue(transcription_text, word_count=5)
            logger.info(f"✅ Phase 0.5 Clip {clip_index}: Transcription complete ({len(transcription_text)} chars)")
        except Exception as e:
            logger.warning(f"Phase 0.5 Clip {clip_index}: Transcription failed: {e}")
            transcription_text = f'[Transcription failed: {str(e)[:100]}]'
            outcue_text = ''
        finally:
            if phase05_audio.exists():
                phase05_audio.unlink()

    # PHASE 1: Video normalization
    # Determine video encoder based on platform
    from platform_utils import IS_WINDOWS, has_nvidia_gpu
    if IS_WINDOWS and has_nvidia_gpu():
        video_encoder_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23"]
    else:
        video_encoder_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "23"]

    phase1_output = working_dir / f"clip{clip_index}_1_normalized.mp4"
    phase1_cmd = [
        ffmpeg, "-y",
        "-i", str(clip_file),
        *video_encoder_args,
        "-r", "29.97",
        "-b:v", "8000k",
        "-c:a", "aac",
        "-b:a", "192k",
        str(phase1_output)
    ]
    result = subprocess.run(phase1_cmd, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else 'Unknown'
        logger.error(f"Phase 1 video normalization failed for clip {clip_index}: {stderr[:500]}")
        raise RuntimeError(f"Phase 1 failed: {stderr[:200]}")

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
    result = subprocess.run(phase2_cmd, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else 'Unknown'
        logger.error(f"Phase 2 audio normalization failed for clip {clip_index}: {stderr[:500]}")
        raise RuntimeError(f"Phase 2 failed: {stderr[:200]}")

    # PHASE 3: Skip (no trimming needed for already-extracted clips)
    phase3_output = phase2_output

    # PHASE 4: Generate thumbnails (PNG) and MP3
    # Generate 1 thumbnail (middle of clip)
    thumb_time = clip_duration / 2
    thumb_file = working_dir / f"clip{clip_index}_thumb.png"
    thumb_cmd = [
        ffmpeg, "-y",
        "-ss", str(thumb_time),
        "-i", str(phase3_output),
        "-vframes", "1",
        str(thumb_file)
    ]
    result = subprocess.run(thumb_cmd, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else 'Unknown'
        logger.error(f"Phase 4 thumbnail generation failed for clip {clip_index}: {stderr[:500]}")
        raise RuntimeError(f"Phase 4 thumbnail failed: {stderr[:200]}")

    # Validate thumbnail
    if not thumb_file.exists():
        raise RuntimeError(f"Phase 4 thumbnail not created for clip {clip_index}")
    if thumb_file.stat().st_size < 5000:
        raise RuntimeError(f"Phase 4 thumbnail corrupted for clip {clip_index} - only {thumb_file.stat().st_size} bytes")

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
    result = subprocess.run(mp3_cmd, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else 'Unknown'
        logger.error(f"Phase 4 MP3 extraction failed for clip {clip_index}: {stderr[:500]}")
        raise RuntimeError(f"Phase 4 MP3 failed: {stderr[:200]}")

    # PHASE 5: Move to final location (cross-platform)
    # Videos/audio go to assets/video/, thumbnails go to assets/thumbnails/
    final_video_dir = media_root / "episodes" / episode / "assets" / "video"
    final_thumb_dir = media_root / "episodes" / episode / "assets" / "thumbnails"
    final_video_dir.mkdir(parents=True, exist_ok=True)
    final_thumb_dir.mkdir(parents=True, exist_ok=True)

    final_video = final_video_dir / f"{normalized_clip_slug}.mp4"
    final_thumb = final_thumb_dir / f"{normalized_clip_slug}-thumb.png"
    final_audio = final_video_dir / f"{normalized_clip_slug}.mp3"

    import shutil
    shutil.move(str(phase3_output), str(final_video))
    shutil.move(str(thumb_file), str(final_thumb))
    shutil.move(str(mp3_file), str(final_audio))

    logger.info(f"✅ Clip {clip_index} processing complete: {final_video}")

    return {
        "asset_id": clip_asset_id,
        "slug": clip_slug,
        "media_url": f"/episodes/{episode}/assets/video/{normalized_clip_slug}.mp4",
        "thumbnail_url": f"/episodes/{episode}/assets/thumbnails/{normalized_clip_slug}-thumb.png",
        "audio_url": f"/episodes/{episode}/assets/video/{normalized_clip_slug}.mp3",
        "duration": duration_formatted,
        "transcription": transcription_text,
        "outcue": outcue_text
    }


def _format_duration(seconds):
    """Format seconds to HH:MM:SS:00 timecode."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}:00"


class CueInsertionError(Exception):
    """Raised when cue block insertion fails."""
    pass


def _insert_multiple_cue_blocks(episode, clip_results, parent_asset_id):
    """
    DEPRECATED: This function is no longer used.

    As of 2026-01-21, individual clips are inserted by the frontend as
    independent SOT cue blocks. This backend insertion function that
    searches for a parent cue is no longer needed.

    The new approach:
    - Frontend inserts all cue blocks before triggering processing
    - Each cue block is independent with its own AssetID
    - Processing updates each cue block individually by AssetID (no parent lookup)

    This function is deprecated because:
    - Complex parent cue lookup that can fail
    - Database race conditions during insertion
    - Tight coupling between clips and parent cue

    Legacy Args (kept for reference):
        episode: Episode number
        clip_results: List of dicts with asset_id, slug, media_url, etc.
        parent_asset_id: AssetID of the original SOT cue block
    """
    # DEPRECATION WARNING
    logger.warning("⚠️ DEPRECATED: _insert_multiple_cue_blocks() called - this function is deprecated")
    logger.warning("⚠️ Cue blocks should now be inserted by the frontend before processing starts")

    raise DeprecationWarning(
        "_insert_multiple_cue_blocks is deprecated. "
        "The frontend now inserts all cue blocks before triggering processing. "
        "Each clip has its own independent AssetID and cue block."
    )

    # === LEGACY CODE BELOW (unreachable, kept for reference) ===
    from models_v2 import Rundown, RundownItem, Episode
    import re

    with db_session() as db:
        # Find the rundown for this episode by joining with Episode
        rundown = db.query(Rundown).join(Episode).filter(Episode.episode_number == episode).first()
        if not rundown:
            raise CueInsertionError(f"No rundown found for episode {episode}")

        # Search all rundown items for parent SOT cue with matching AssetID
        items = db.query(RundownItem).filter_by(rundown_id=rundown.id).all()
        logger.info(f"🔍 Searching {len(items)} rundown items for parent cue {parent_asset_id}")

        for item in items:
            if not item.script_content:
                continue

            # Look for parent SOT cue block - more flexible pattern
            # Try exact match first
            cue_pattern = re.compile(
                r'(<!-- Begin Cue(?: collapsed)? -->.*?\[Type: SOT\].*?\[AssetID: ' + re.escape(parent_asset_id) + r'\].*?<!-- End Cue -->)',
                re.DOTALL
            )

            match = cue_pattern.search(item.script_content)

            # Fallback: try searching just for AssetID in any cue block
            if not match:
                fallback_pattern = re.compile(
                    r'(<!-- Begin Cue(?: collapsed)? -->.*?\[AssetID: ' + re.escape(parent_asset_id) + r'\].*?<!-- End Cue -->)',
                    re.DOTALL
                )
                match = fallback_pattern.search(item.script_content)
                if match:
                    logger.info(f"📎 Found parent cue via fallback pattern (non-SOT type)")

            if match:
                parent_cue = match.group(1)
                insertion_point = match.end()
                logger.info(f"✅ Found parent cue in item '{item.title}' (id={item.id})")

                # Build cue blocks for each clip
                new_cues = []
                for clip in clip_results:
                    # Get transcription and outcue with fallbacks
                    transcription = clip.get('transcription', '')
                    outcue = clip.get('outcue', '')

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
[Transcription: {transcription}]
[Outcue: {outcue}]
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
                return len(clip_results)

        # If we get here, parent cue was not found in any item
        # Log detailed debug info
        logger.error(f"❌ Parent SOT cue {parent_asset_id} not found in episode {episode}")
        logger.error(f"   Searched {len(items)} rundown items")
        for item in items:
            if item.script_content and 'AssetID' in item.script_content:
                # Extract all AssetIDs in this item for debugging
                asset_ids = re.findall(r'\[AssetID: ([^\]]+)\]', item.script_content)
                logger.error(f"   Item '{item.title}' has AssetIDs: {asset_ids}")

        raise CueInsertionError(
            f"Parent SOT cue with AssetID {parent_asset_id} not found in episode {episode}. "
            f"Searched {len(items)} rundown items."
        )


def _process_montage(temp_job_id, episode, slug, clips, asset_id, working_dir, normalized_slug):
    """
    Process montage workflow:
    1. Extract clips individually from source video
    2. Concatenate into single video using FFmpeg concat demuxer
    3. Run full processing pipeline on montage (including Whisper transcription)
    4. Update existing cue block with montage result

    Args:
        temp_job_id: Job ID
        episode: Episode number
        slug: Base slug for naming
        clips: List of clip objects with time_start, time_end
        asset_id: AssetID of the cue block to update
        working_dir: Working directory path
        normalized_slug: Normalized slug for filenames

    Returns:
        dict: Processing results with montage output
    """
    logger.info(f"🎬 MONTAGE: Processing {len(clips)} clips for {temp_job_id}")

    # Get platform-appropriate binaries
    ffmpeg = get_ffmpeg_binary()
    ffprobe = get_ffprobe_binary()

    input_file = working_dir / f"{temp_job_id}_upload.mp4"
    if not input_file.exists():
        raise FileNotFoundError(f"Upload file not found: {input_file}")

    # Helper function to convert timecode to seconds
    def timecode_to_seconds(tc):
        """Convert HH:MM:SS:FF to seconds (ignoring frames)"""
        parts = tc.split(':')
        if len(parts) == 4:
            h, m, s, f = parts
            return int(h) * 3600 + int(m) * 60 + int(s) + (int(f) / 30.0)
        elif len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        return 0

    # Create temp directory for extracted clips
    temp_montage_dir = working_dir / "montage_clips"
    temp_montage_dir.mkdir(exist_ok=True)

    extracted_clips = []
    total_duration = 0.0

    # Determine video encoder based on platform
    from platform_utils import IS_WINDOWS, has_nvidia_gpu
    if IS_WINDOWS and has_nvidia_gpu():
        video_encoder_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23"]
    else:
        video_encoder_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "23"]

    # Step 1: Extract each clip from source video
    for idx, clip in enumerate(clips, 1):
        clip_start = clip.get('time_start', '00:00:00:00')
        clip_end = clip.get('time_end', '00:00:00:00')

        start_sec = timecode_to_seconds(clip_start)
        end_sec = timecode_to_seconds(clip_end)
        clip_duration = end_sec - start_sec

        # Skip invalid duration clips
        if clip_duration <= 0:
            logger.warning(f"Montage clip {idx} has invalid duration ({start_sec}s to {end_sec}s), skipping")
            continue

        extracted_clip_path = temp_montage_dir / f"clip_{idx:03d}.mp4"

        # Extract with re-encoding to ensure consistent format for concatenation
        extract_cmd = [
            ffmpeg, "-y",
            "-ss", str(start_sec),
            "-i", str(input_file),
            "-t", str(clip_duration),
            *video_encoder_args,
            "-c:a", "aac",
            "-b:a", "192k",
            str(extracted_clip_path)
        ]

        logger.info(f"📹 Extracting montage clip {idx}: {start_sec}s to {end_sec}s ({clip_duration}s)")

        result = subprocess.run(extract_cmd, capture_output=True)
        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else 'Unknown'
            logger.error(f"FFmpeg clip extraction failed for clip {idx}: {stderr[:500]}")
            raise RuntimeError(f"Failed to extract clip {idx}: {stderr[:200]}")

        extracted_clips.append(extracted_clip_path)
        total_duration += clip_duration
        logger.info(f"✅ Montage clip {idx} extracted: {extracted_clip_path}")

    if not extracted_clips:
        raise ValueError("No valid clips to concatenate for montage")

    # Step 2: Create concat demuxer file
    concat_file = temp_montage_dir / "concat_list.txt"
    with open(concat_file, 'w') as f:
        for clip_path in extracted_clips:
            # FFmpeg concat requires forward slashes even on Windows
            f.write(f"file '{clip_path.as_posix()}'\n")

    logger.info(f"📝 Created concat file with {len(extracted_clips)} clips")

    # Step 3: Concatenate all clips into single montage video
    montage_concat_output = temp_montage_dir / f"{temp_job_id}_montage_concat.mp4"

    concat_cmd = [
        ffmpeg, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",  # Stream copy since clips are already encoded
        str(montage_concat_output)
    ]

    logger.info(f"🔗 Concatenating {len(extracted_clips)} clips into montage")

    result = subprocess.run(concat_cmd, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else 'Unknown'
        logger.error(f"FFmpeg concatenation failed: {stderr[:500]}")
        raise RuntimeError(f"Montage concatenation failed: {stderr[:200]}")

    logger.info(f"✅ Montage concatenated: {montage_concat_output}")

    # Step 4: Run full processing pipeline on the concatenated montage
    # Generate a new AssetID for the montage output (use existing if provided)
    montage_asset_id = asset_id if asset_id else _generate_asset_id()

    logger.info(f"🔄 Running full pipeline on montage (AssetID: {montage_asset_id})")

    # Update job status
    _update_job_status(temp_job_id, 'montage_processing', 'processing')

    # Process the concatenated montage through _process_single_clip
    # This includes transcription, normalization, thumbnails, etc.
    montage_result = _process_single_clip(
        montage_concat_output,
        slug,
        montage_asset_id,
        episode,
        working_dir,
        0,  # clip_index 0 for montage
        temp_job_id
    )

    # Step 5: Clean up temp files
    for clip_path in extracted_clips:
        if clip_path.exists():
            clip_path.unlink()
    if concat_file.exists():
        concat_file.unlink()
    if montage_concat_output.exists():
        montage_concat_output.unlink()
    if temp_montage_dir.exists():
        try:
            temp_montage_dir.rmdir()
        except OSError:
            pass  # Directory not empty, leave it

    logger.info(f"🧹 Cleaned up {len(extracted_clips)} temp montage files")

    # Step 6: Update the existing cue block with montage result
    _update_cue_block_with_result(episode, asset_id, montage_result)

    # Mark job as complete
    _update_job_status(temp_job_id, 'complete', 'completed')

    logger.info(f"✅ MONTAGE: Completed processing {len(clips)} clips into single montage")

    return {
        "status": "completed",
        "montage": montage_result,
        "clip_count": len(extracted_clips),
        "total_duration": total_duration,
        "message": f"Processed {len(clips)} clips into montage successfully"
    }


def _update_cue_block_with_result(episode, asset_id, result):
    """
    Update an existing SOT cue block with processing results.

    Args:
        episode: Episode number
        asset_id: AssetID of the cue block to update
        result: Processing result dict with media_url, thumbnail_url, etc.
    """
    try:
        from models_v2 import Rundown, RundownItem, Episode
        import re

        with db_session() as db:
            # Find the rundown for this episode
            rundown = db.query(Rundown).join(Episode).filter(Episode.episode_number == episode).first()
            if not rundown:
                logger.warning(f"No rundown found for episode {episode}")
                return

            # Search all rundown items for the cue with matching AssetID
            items = db.query(RundownItem).filter_by(rundown_id=rundown.id).all()

            for item in items:
                if not item.script_content:
                    continue

                # Look for the SOT cue block with matching AssetID (expanded or
                # collapsed). Capture the marker suffix so a collapsed cue is
                # rebuilt collapsed (the new_cue below is built from scratch).
                cue_pattern = re.compile(
                    r'(<!-- Begin Cue( collapsed)? -->.*?\[AssetID: ' + re.escape(asset_id) + r'\].*?<!-- End Cue -->)',
                    re.DOTALL
                )

                match = cue_pattern.search(item.script_content)
                if match:
                    old_cue = match.group(1)
                    marker_suffix = match.group(2) or ''

                    # Get transcription and outcue with fallbacks
                    transcription = result.get('transcription', '')
                    outcue = result.get('outcue', '')

                    # Build updated cue block (preserve the original marker)
                    new_cue = f"""<!-- Begin Cue{marker_suffix} -->
[Type: SOT]
[AssetID: {asset_id}]
[Slug: {result.get('slug', '')}]
[Description: ]
[MediaURL: {result.get('media_url', '')}]
[Duration: {result.get('duration', '')}]
[ThumbnailURL: {result.get('thumbnail_url', '')}]
[AudioURL: {result.get('audio_url', '')}]
[Transcription: {transcription}]
[Outcue: {outcue}]
[Credits: {{}}]
<!-- End Cue -->"""

                    # Replace the old cue with the new one
                    item.script_content = item.script_content.replace(old_cue, new_cue)

                    db.commit()
                    logger.info(f"✅ Updated cue block {asset_id} with montage result")
                    return

            logger.warning(f"SOT cue {asset_id} not found in episode {episode}")

    except Exception as e:
        logger.error(f"Failed to update cue block: {e}")


def _resolve_shared_media_root() -> Path:
    """Return the platform-appropriate shared_media root.

    Docker: /shared_media · Linux worker (kairo): /mnt/sync/shared_media ·
    Windows worker: W:/mnt/sync/shared_media. Centralised so all three chain
    links compute the same working directory.
    """
    if platform.system() == 'Windows':
        return Path('W:/mnt/sync/shared_media')
    elif Path('/shared_media').exists():
        return Path('/shared_media')
    else:
        return Path('/mnt/sync/shared_media')


def _is_zero_time(time_str) -> bool:
    """Check if timecode is effectively zero (handles 00:00:00 and 00:00:00:00)."""
    return time_str in ("00:00:00", "00:00:00:00", "0", "0.0", "", None)


def _timecode_to_seconds(time_str) -> float:
    """Convert HH:MM:SS or HH:MM:SS:FF (30fps assumed) timecode to seconds."""
    parts = str(time_str).split(':')
    if len(parts) == 3:
        h, m, s = map(float, parts)
        return h * 3600 + m * 60 + s
    elif len(parts) == 4:
        h, m, s, f = map(float, parts)
        return h * 3600 + m * 60 + s + (f / 30.0)
    return 0.0


# ============================================================================
# SOT single_trim / full_process CELERY CHAIN
# ----------------------------------------------------------------------------
# The single_trim / full_process pipeline runs as a 3-link Celery chain so that
# transcription is a genuine chain LINK on the dedicated whisper queue — no
# `.get()` inside a task (which Celery forbids):
#
#   chain(sot_prepare.s(...), transcribe_sot_audio.s(), sot_finalize.s())
#
#   1. sot_prepare      (media)   phases 1-3: validate + raw probe + TRIM +
#                                 extract audio (from the TRIMMED file)
#   2. transcribe_sot_audio (whisper) phase 4: receives the ctx dict, transcribes
#                                 the trimmed wav, returns ctx + transcription/outcue
#   3. sot_finalize     (media)   phases 5-11: analyze trimmed clip + normalize
#                                 video + fix audio + loudness + derivatives +
#                                 move-to-assets + post-analysis verify
#
# State flows between links through a single JSON-serialisable `ctx` dict
# (strings / numbers / lists / dicts only — Path objects are stored as str).
# Every link keeps calling _update_job_status() and _update_sot_cue_block() so
# the ShowBuild cue block stays live at each phase. Phases are clean integers
# 1-11 (the SOTProcessingJob model has current_phase but NO phase_message
# column, so only the integer phase strings are written).
# ============================================================================


@shared_task(
    bind=True,
    queue='media',
    name='services.ffmpeg_tasks.sot_prepare',
    max_retries=3,
    soft_time_limit=1800,
    time_limit=2400,
    acks_late=True,
    reject_on_worker_lost=True
)
def sot_prepare(
    self,
    temp_job_id: str,
    episode: str,
    slug: str,
    trim_start: str = "00:00:00",
    trim_end: str = "00:00:00",
    job_type: str = "full_process",
    asset_id: str = None,
    devel_mode: bool = False
):
    """
    Chain link 1/3 — phases 1-3 of the single_trim/full_process SOT pipeline.

    Phase 1: validate upload (size/duration/resolution/framerate/audio).
    Phase 2: ffprobe the RAW upload (sanity only — detects has_audio, dimensions,
             codec; does NOT write user-facing duration, phase 5 does that on the
             trimmed clip).
    Phase 3: TRIM the upload EARLY (no-op pass-through if no trim requested).
    Then extract audio (WAV 16kHz mono) from the TRIMMED file for the whisper link.

    Returns a JSON-serialisable `ctx` dict carrying everything the downstream
    links need (Paths are stored as strings).
    """
    import json
    from models_v2 import SOTProcessingJob

    media_root = get_media_root()
    shared_media_root = _resolve_shared_media_root()
    working_dir = shared_media_root / "preproc" / "working" / temp_job_id
    normalized_slug = _normalize_slug(slug)

    worker_name = platform.node()
    worker_platform = platform.system()

    try:
        logger.info(f"🎬 sot_prepare on {worker_name} ({worker_platform}) for {temp_job_id} (job_type: {job_type}, devel_mode: {devel_mode})")

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

        ffmpeg = get_ffmpeg_binary()
        ffprobe = get_ffprobe_binary()

        # Input file from background upload
        input_file = working_dir / f"{temp_job_id}_upload.mp4"
        if not input_file.exists():
            raise FileNotFoundError(f"Upload file not found: {input_file}")

        # Copy source video to permanent storage if source asset exists
        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job and job.source_asset_id:
                source_dir = media_root / "episodes" / episode / "assets" / "video" / "sources"
                source_dir.mkdir(parents=True, exist_ok=True)
                source_filename = f"{job.source_asset_id}.mp4"
                source_path = source_dir / source_filename
                if not source_path.exists():
                    import shutil
                    shutil.copy2(input_file, source_path)
                    logger.info(f"✅ Saved source video: {source_path}")

        # ================================================================
        # PHASE 2: ffprobe the RAW upload (sanity only)
        #  - Extract duration, resolution, framerate, audio channels
        #  - Determine orientation + has_audio
        #  - This is the cheap raw probe; the real cue-block metadata is
        #    written by phase 5 (analyze) AFTER trim.
        # ================================================================
        logger.info(f"Phase 2: Probing source for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase2', 'processing')

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

        frame_rate_str = video_stream.get('r_frame_rate', '0/1')
        if '/' in frame_rate_str:
            num, denom = map(int, frame_rate_str.split('/'))
            frame_rate = round(num / denom, 2) if denom != 0 else 0
        else:
            frame_rate = float(frame_rate_str)

        audio_channels = audio_stream.get('channels', 0)
        audio_layout = audio_stream.get('channel_layout', 'unknown')
        sample_rate = audio_stream.get('sample_rate', 0)
        has_audio = audio_channels > 0

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

        # Format raw duration as HH:MM:SS (informational only)
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        logger.info(f"Phase 2 probe: {width}x{height} {orientation}, {frame_rate}fps, {audio_config}, {duration_formatted}")

        # ================================================================
        # PHASE 1: PRE-PROCESSING VALIDATION
        # Fail fast on invalid inputs to prevent wasted processing time
        # ================================================================
        _update_job_status(temp_job_id, 'phase1', 'processing')
        validation_errors = []
        validation_warnings = []

        # 1. File size check (max 10GB)
        MAX_FILE_SIZE_GB = 10
        file_size_bytes = input_file.stat().st_size
        file_size_gb = file_size_bytes / (1024 ** 3)
        if file_size_gb > MAX_FILE_SIZE_GB:
            validation_errors.append(f"File too large: {file_size_gb:.2f}GB (max {MAX_FILE_SIZE_GB}GB)")
        elif file_size_gb > MAX_FILE_SIZE_GB * 0.8:
            validation_warnings.append(f"Large file: {file_size_gb:.2f}GB (may take extended processing time)")

        # 2. Duration check (min 1s, max 1 hour) — validates the EFFECTIVE
        # duration: when trim points are set, phase 3 trims early and only the
        # clip is ever fully processed, so a multi-hour full-show recording is
        # a legitimate source for a short trimmed SOT (the legacy-cue-convert
        # "FULL VIDEO IS TITLED ..." workflow). The raw-source cap applies
        # only when no trim is requested.
        MIN_DURATION_SECONDS = 1
        MAX_DURATION_SECONDS = 3600  # 1 hour

        def _fmt_secs(s: float) -> str:
            s = max(0, int(s))
            return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"

        has_trim = not _is_zero_time(trim_start) or not _is_zero_time(trim_end)
        if has_trim:
            trim_start_sec = _timecode_to_seconds(trim_start)
            trim_end_sec = (
                _timecode_to_seconds(trim_end)
                if not _is_zero_time(trim_end) else duration_seconds
            )
            effective_seconds = trim_end_sec - trim_start_sec
            if trim_start_sec >= duration_seconds:
                validation_errors.append(
                    f"Trim start {trim_start} is beyond the end of the video "
                    f"({duration_formatted})"
                )
            elif effective_seconds < MIN_DURATION_SECONDS:
                validation_errors.append(
                    f"Trimmed clip too short: {effective_seconds:.2f}s "
                    f"(trim {trim_start} → {trim_end}, min {MIN_DURATION_SECONDS}s)"
                )
            elif effective_seconds > MAX_DURATION_SECONDS:
                validation_errors.append(
                    f"Trimmed clip too long: {_fmt_secs(effective_seconds)} (max 1 hour)"
                )
            elif effective_seconds > MAX_DURATION_SECONDS * 0.8:
                validation_warnings.append(
                    f"Long trimmed clip: {_fmt_secs(effective_seconds)} "
                    f"(may take extended processing time)"
                )
            if duration_seconds > MAX_DURATION_SECONDS:
                validation_warnings.append(
                    f"Long source video: {duration_formatted} — only the trimmed "
                    f"clip ({_fmt_secs(effective_seconds)}) will be processed"
                )
        else:
            if duration_seconds < MIN_DURATION_SECONDS:
                validation_errors.append(f"Video too short: {duration_seconds:.2f}s (min {MIN_DURATION_SECONDS}s)")
            elif duration_seconds > MAX_DURATION_SECONDS:
                validation_errors.append(f"Video too long: {duration_formatted} (max 1 hour)")
            elif duration_seconds > MAX_DURATION_SECONDS * 0.8:
                validation_warnings.append(f"Long video: {duration_formatted} (may take extended processing time)")

        # 3. Resolution validation
        MIN_WIDTH = 100
        MIN_HEIGHT = 100
        MAX_WIDTH = 7680  # 8K
        MAX_HEIGHT = 4320  # 8K
        if width < MIN_WIDTH or height < MIN_HEIGHT:
            validation_errors.append(f"Resolution too small: {width}x{height} (min {MIN_WIDTH}x{MIN_HEIGHT})")
        elif width > MAX_WIDTH or height > MAX_HEIGHT:
            validation_errors.append(f"Resolution too large: {width}x{height} (max {MAX_WIDTH}x{MAX_HEIGHT})")
        elif width == 0 or height == 0:
            validation_errors.append(f"Invalid resolution: {width}x{height} (video stream may be corrupt)")

        # 4. Framerate validation
        MIN_FRAMERATE = 10
        MAX_FRAMERATE = 120
        if frame_rate < MIN_FRAMERATE:
            validation_warnings.append(f"Low framerate: {frame_rate}fps (quality may be degraded)")
        elif frame_rate > MAX_FRAMERATE:
            validation_warnings.append(f"High framerate: {frame_rate}fps (will be normalized to 30fps)")

        # 5. Audio stream validation
        # Audio is no longer required — silent videos process through a reduced pipeline.
        if not has_audio:
            validation_warnings.append(
                "No audio stream detected — skipping transcription, channel analysis, "
                "loudness normalization, and MP3 extraction"
            )

        # Log validation results
        for warning in validation_warnings:
            logger.warning(f"⚠️ Validation warning: {warning}")
            processing_report["warnings"].append(warning)

        # Fail if critical errors found
        if validation_errors:
            error_msg = "; ".join(validation_errors)
            logger.error(f"❌ Pre-processing validation failed: {error_msg}")
            processing_report["overall_status"] = "failed"
            processing_report["phases"]["phase1"] = {"status": "failed", "errors": validation_errors}
            _update_job_status(temp_job_id, 'phase1', 'failed', error_msg)
            if asset_id:
                _update_sot_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': f'❌ Validation Failed: {error_msg}'
                })
            raise ValueError(f"Pre-processing validation failed: {error_msg}")

        logger.info(f"✅ Phase 1 validation passed for {temp_job_id}")
        processing_report["phases"]["phase1"] = {"status": "success", "file_size_gb": round(file_size_gb, 2)}

        # Store pre-analysis (raw probe) in database
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

        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.pre_analysis = pre_analysis_data
                db.commit()

        processing_report["phases"]["phase2"] = {"status": "success", "data": pre_analysis_data}

        # Update cue block with raw probe metadata (sanity values, refined in phase 5)
        if asset_id:
            _update_sot_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 2 Complete: Source Probed',
                'Resolution': f'{width}x{height}',
                'Framerate': f'{frame_rate}fps',
                'Orientation': orientation,
                'AudioChannels': audio_config,
                'AudioLayout': audio_layout,
                'SampleRate': f'{sample_rate}Hz'
            })

        # ================================================================
        # PHASE 3: Trimming (EARLY — before transcription + analyze)
        #  - Trim based on trim_start and trim_end
        #  - No-op pass-through when no trim requested
        # ================================================================
        if not _is_zero_time(trim_start) or not _is_zero_time(trim_end):
            logger.info(f"Phase 3: Trimming for {temp_job_id} (start={trim_start}, end={trim_end})")
            _update_job_status(temp_job_id, 'phase3', 'processing')

            phase3_output = working_dir / f"{temp_job_id}_3_trimmed.mp4"

            # Frame-accurate trim: -ss BEFORE -i fast-seeks to the nearest
            # keyframe, then re-encoding decodes forward to the EXACT requested
            # IN/OUT frame. Stream-copy (-c copy) was keyframe-bounded and could
            # overrun the OUT point by up to one GOP (~8s); re-encoding lands both
            # ends on the exact requested frame. The full resolution/framerate
            # normalization still happens later in Phase 6 (sot_finalize) — here
            # we only re-encode for cut accuracy, so use the same encoder pick.
            from platform_utils import IS_WINDOWS, has_nvidia_gpu
            if IS_WINDOWS and has_nvidia_gpu():
                video_encoder_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18", "-maxrate", "8M", "-bufsize", "16M"]
            else:
                video_encoder_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "18"]

            # Audio handling for the trim re-encode. When the source has audio,
            # re-encode it to AAC alongside the video; when it doesn't, drop it
            # (the silent track is injected later in Phase 6).
            trim_audio_args = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"] if has_audio else ["-an"]

            if not _is_zero_time(trim_end):
                start_sec = _timecode_to_seconds(trim_start)
                end_sec = _timecode_to_seconds(trim_end)
                trim_duration = end_sec - start_sec
                phase3_cmd = [
                    ffmpeg, "-y",
                    "-ss", str(start_sec),  # fast seek to nearby keyframe
                    "-i", str(input_file),
                    "-t", str(trim_duration),
                    *video_encoder_args,
                    *trim_audio_args,
                    str(phase3_output)
                ]
            else:
                # Trim from start only (frame-accurate re-encode; see note above)
                start_sec = _timecode_to_seconds(trim_start)
                phase3_cmd = [
                    ffmpeg, "-y",
                    "-ss", str(start_sec),  # fast seek to nearby keyframe
                    "-i", str(input_file),
                    *video_encoder_args,
                    *trim_audio_args,
                    str(phase3_output)
                ]

            subprocess.run(phase3_cmd, check=True, capture_output=True)
            logger.info(f"Phase 3 complete (trimmed): {phase3_output}")
            trimmed_file = phase3_output

            if asset_id:
                _update_sot_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': 'Phase 3 Complete: Trimmed'
                })
        else:
            # No trimming needed — pass the upload through unchanged
            logger.info(f"Phase 3: Skipped (no trimming needed) for {temp_job_id}")
            trimmed_file = input_file
            if asset_id:
                _update_sot_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': 'Phase 3 Skipped: No Trimming Needed'
                })

        # Extract audio (WAV 16kHz mono) from the TRIMMED file for the whisper link.
        audio_wav_path = None
        if has_audio:
            phase3_audio = working_dir / f"{temp_job_id}_4_audio.wav"
            audio_extract_cmd = [
                ffmpeg, "-y",
                "-i", str(trimmed_file),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(phase3_audio)
            ]
            subprocess.run(audio_extract_cmd, check=True, capture_output=True)
            audio_wav_path = str(phase3_audio)
            logger.info(f"Phase 3: Trimmed audio extracted to {phase3_audio} (for whisper link)")

        # Build the JSON-serialisable context for the rest of the chain.
        ctx = {
            "temp_job_id": temp_job_id,
            "episode": episode,
            "slug": slug,
            "asset_id": asset_id,
            "normalized_slug": normalized_slug,
            "job_type": job_type,
            "devel_mode": devel_mode,
            "trim_start": trim_start,
            "trim_end": trim_end,
            "working_dir": str(working_dir),
            "media_root": str(media_root),
            "trimmed_file": str(trimmed_file),
            "audio_wav_path": audio_wav_path,
            "has_audio": has_audio,
            "pre_analysis_data": pre_analysis_data,
            "processing_report": processing_report,
            # transcription/outcue are filled in by the whisper link
            "transcription": None,
            "outcue": "",
        }
        return ctx

    except subprocess.CalledProcessError as e:
        if hasattr(e, 'stderr') and e.stderr:
            stderr_text = e.stderr.decode('utf-8', errors='replace') if isinstance(e.stderr, bytes) else str(e.stderr)
        else:
            stderr_text = f"Exit code {e.returncode}"
        error_msg = f"FFmpeg error in sot_prepare: {stderr_text}"
        logger.error(error_msg)
        _update_job_status(temp_job_id, 'phase3', 'failed', error_msg)
        raise
    except Exception as e:
        error_msg = f"sot_prepare error: {str(e)}"
        logger.error(error_msg)
        _update_job_status(temp_job_id, 'phase1', 'failed', error_msg)
        raise


@shared_task(
    bind=True,
    queue='whisper',
    name='services.ffmpeg_tasks.transcribe_sot_audio',
    max_retries=0,
    soft_time_limit=900,
    time_limit=1200,
    acks_late=True,
    reject_on_worker_lost=True
)
def transcribe_sot_audio(self, ctx: dict):
    """
    Chain link 2/3 — phase 4: transcribe the TRIMMED audio on the whisper queue.

    As a chain link this RECEIVES the previous task's return value (the prepare
    `ctx` dict) as its first positional arg. It pulls the wav path from the ctx,
    runs Whisper via transcribe_audio_simple(), and RETURNS the same ctx dict
    augmented with `transcription` + `outcue` so sot_finalize gets everything.

    Transcription failure is NON-FATAL: it sets transcription to a sentinel
    ('[Transcription failed: ...]') and outcue '', and passes the ctx on so the
    chain continues (preserves the original pipeline's behaviour).
    """
    temp_job_id = ctx["temp_job_id"]
    episode = ctx["episode"]
    slug = ctx["slug"]
    asset_id = ctx["asset_id"]
    has_audio = ctx.get("has_audio", False)
    audio_wav_path = ctx.get("audio_wav_path")

    from models_v2 import SOTProcessingJob

    if not has_audio or not audio_wav_path:
        logger.info(f"Phase 4: Skipped (no audio track) for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase4', 'skipped')
        ctx["transcription"] = ''
        ctx["outcue"] = ''
        if asset_id:
            _update_sot_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 4 Skipped: No Audio Track',
                'Transcription': '',
                'Outcue': ''
            })
        return ctx

    logger.info(f"Phase 4: Transcribing trimmed audio for {temp_job_id} on {platform.node()}")
    _update_job_status(temp_job_id, 'phase4', 'processing')

    try:
        transcription_text = transcribe_audio_simple(audio_wav_path)
        logger.info(f"Phase 4: Transcription complete, {len(transcription_text)} characters")

        outcue_text = derive_outcue(transcription_text, word_count=5)
        logger.info(f"Phase 4: Outcue derived: {outcue_text}")

        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.transcription = transcription_text
                db.commit()

        ctx["transcription"] = transcription_text
        ctx["outcue"] = outcue_text

        if asset_id:
            _update_sot_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 4 Complete: Transcribed',
                'Transcription': transcription_text,
                'Outcue': outcue_text
            })

    except Exception as e:
        # NON-FATAL: keep the chain going so the rest of the pipeline still runs.
        logger.error(f"Phase 4: Transcription failed: {e}")
        ctx["transcription"] = f'[Transcription failed: {str(e)}]'
        ctx["outcue"] = ''
        if asset_id:
            _update_sot_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 4 Complete: Transcription Failed',
                'Transcription': ctx["transcription"]
            })

    return ctx


@shared_task(
    bind=True,
    queue='media',
    name='services.ffmpeg_tasks.sot_finalize',
    max_retries=3,
    soft_time_limit=1800,
    time_limit=2400,
    acks_late=True,
    reject_on_worker_lost=True
)
def sot_finalize(self, ctx: dict):
    """
    Chain link 3/3 — phases 5-11 of the single_trim/full_process SOT pipeline.

    Receives the ctx dict (now carrying transcription + outcue from the whisper
    link) and runs, on the TRIMMED clip:
      Phase 5  — analyze trimmed clip (real cue-block duration/metadata)
      Phase 6  — normalize video (H.264)
      Phase 7  — fix audio channels (dual-mono)
      Phase 8  — normalize loudness (EBU R128)
      Phase 9  — derivatives (thumbnails + MP3)
      Phase 10 — move to assets + DB final paths + asset relationship
      Phase 11 — post-analysis verify

    Returns the final result dict (same shape the original returned).
    """
    import json
    from models_v2 import SOTProcessingJob

    temp_job_id = ctx["temp_job_id"]
    episode = ctx["episode"]
    slug = ctx["slug"]
    asset_id = ctx["asset_id"]
    normalized_slug = ctx["normalized_slug"]
    job_type = ctx["job_type"]
    devel_mode = ctx["devel_mode"]
    trim_start = ctx["trim_start"]
    trim_end = ctx["trim_end"]
    working_dir = Path(ctx["working_dir"])
    media_root = Path(ctx["media_root"])
    trimmed_file = Path(ctx["trimmed_file"])
    has_audio = ctx.get("has_audio", False)
    pre_analysis_data = ctx.get("pre_analysis_data")
    processing_report = ctx.get("processing_report") or {
        "job_id": temp_job_id, "overall_status": "in_progress",
        "phases": {}, "failures": [], "warnings": [],
        "devel_mode": devel_mode, "intermediate_files": [] if devel_mode else None
    }
    transcription_text = ctx.get("transcription")

    ffmpeg = get_ffmpeg_binary()
    ffprobe = get_ffprobe_binary()
    episodes_root = media_root / "episodes"

    try:
        logger.info(f"🎬 sot_finalize on {platform.node()} for {temp_job_id}")

        # ================================================================
        # PHASE 5: Analyze the TRIMMED clip (real cue-block metadata)
        #  - Re-probe the trimmed file so duration/etc reflect what the user
        #    actually kept (the raw probe in phase 2 was sanity-only).
        # ================================================================
        logger.info(f"Phase 5: Analyzing trimmed clip for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase5', 'processing')

        trimmed_duration_probe = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(trimmed_file)],
            capture_output=True, text=True, check=True
        )
        trimmed_duration_seconds = float(trimmed_duration_probe.stdout.strip())
        t_hours = int(trimmed_duration_seconds // 3600)
        t_minutes = int((trimmed_duration_seconds % 3600) // 60)
        t_seconds = int(trimmed_duration_seconds % 60)
        trimmed_duration_formatted = f"{t_hours:02d}:{t_minutes:02d}:{t_seconds:02d}"

        processing_report["phases"]["phase5"] = {
            "status": "success",
            "data": {"duration": trimmed_duration_formatted, "duration_seconds": trimmed_duration_seconds}
        }
        logger.info(f"Phase 5 analyze: trimmed duration {trimmed_duration_formatted}")

        if asset_id:
            _update_sot_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 5 Complete: Trimmed Clip Analyzed',
                'Duration': trimmed_duration_formatted
            })

        # ================================================================
        # PHASE 6: Video Normalization
        #  - Convert to H.264/AAC MP4, 29.97fps, max width 1920
        # ================================================================
        logger.info(f"Phase 6: Video normalization for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase6', 'processing')

        phase6_output = working_dir / f"{temp_job_id}_6_normalized.mp4"

        # Determine video encoder based on platform.
        # NVENC for Windows with GPU, libx264 CPU fallback for Linux workers.
        from platform_utils import IS_WINDOWS, has_nvidia_gpu
        if IS_WINDOWS and has_nvidia_gpu():
            video_encoder_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18", "-maxrate", "8M", "-bufsize", "16M"]
        else:
            video_encoder_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "18"]

        # When the source has NO audio track, synthesize a silent stereo track
        # (anullsrc) as a second input so the normalized MP4 always carries audio.
        # Every downstream phase (channel analysis, loudness, MP3 extraction) then
        # runs unchanged, and the SOT ships WITH a real (silent) audio track
        # instead of being audio-less — broadcast-safer and consistent across
        # workers. See MEMORY: project_audioless_sot_silent_inject.
        if has_audio:
            phase6_cmd = [
                ffmpeg, "-y",
                "-i", str(trimmed_file),
                *video_encoder_args,
                "-r", "29.97",  # Broadcast standard framerate
                "-vf", "scale='if(gt(iw,1920),1920,-2)':'-2'",  # Max width 1920, maintain aspect
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                str(phase6_output)
            ]
        else:
            phase6_cmd = [
                ffmpeg, "-y",
                "-i", str(trimmed_file),
                "-f", "lavfi",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-map", "0:v:0",
                "-map", "1:a:0",
                *video_encoder_args,
                "-r", "29.97",  # Broadcast standard framerate
                "-vf", "scale='if(gt(iw,1920),1920,-2)':'-2'",  # Max width 1920, maintain aspect
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                "-shortest",  # stop at end of video (silent input is infinite)
                str(phase6_output)
            ]
        subprocess.run(phase6_cmd, check=True, capture_output=True)
        logger.info(f"Phase 6 complete: {phase6_output}")

        # From here on the normalized file ALWAYS has an audio track (real or the
        # injected silent one), so let the audio phases (7 channels, 8/9 loudness,
        # MP3) run normally instead of being skipped.
        has_audio = True

        if asset_id:
            _update_sot_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 6 Complete: Video Normalized'
            })

        # ================================================================
        # PHASE 7: Audio Channel Analysis and Dual-Mono Conversion
        #  - Convert to dual-mono if channels are unbalanced
        #  - Skipped entirely when the source has no audio track.
        # ================================================================
        if not has_audio:
            logger.info(f"Phase 7: Skipped (no audio track) for {temp_job_id}")
            _update_job_status(temp_job_id, 'phase7', 'skipped')
            phase7_output = phase6_output
            if asset_id:
                _update_sot_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': 'Phase 7 Skipped: No Audio Track',
                    'AudioProcessing': 'No audio track'
                })
        else:
            logger.info(f"Phase 7: Audio channel analysis for {temp_job_id}")
            _update_job_status(temp_job_id, 'phase7', 'processing')

            analyze_cmd = [
                ffmpeg,
                "-i", str(phase6_output),
                "-map", "0:a:0",
                "-af", "astats=measure_overall=Peak_level:measure_perchannel=Peak_level",
                "-f", "null",
                "-"
            ]
            analyze_result = subprocess.run(analyze_cmd, capture_output=True, text=True)
            astats_output = analyze_result.stderr

            import re
            channel_levels = []
            for line in astats_output.split('\n'):
                if 'Peak level dB' in line:
                    if '-inf' in line.lower():
                        channel_levels.append(-96.0)
                    elif 'inf' in line.lower():
                        channel_levels.append(0.0)
                    else:
                        match = re.search(r'Peak level dB:\s*([-]?\d+\.?\d*)', line)
                        if match:
                            try:
                                channel_levels.append(float(match.group(1)))
                            except ValueError:
                                logger.warning(f"Could not parse dB level from: {line}")
                                channel_levels.append(-96.0)

            logger.info(f"Phase 7: Channel levels: {channel_levels}")

            needs_dual_mono = False
            if len(channel_levels) >= 2:
                left_level = channel_levels[0]
                right_level = channel_levels[1]
                level_diff = abs(left_level - right_level)
                if level_diff > 10:
                    needs_dual_mono = True
                    logger.info(f"Phase 7: Unbalanced channels detected ({level_diff:.1f}dB diff), converting to dual-mono")

            phase7_output = working_dir / f"{temp_job_id}_7_audio-fixed.mp4"

            if needs_dual_mono:
                dual_mono_cmd = [
                    ffmpeg, "-y",
                    "-i", str(phase6_output),
                    "-c:v", "copy",
                    "-af", "pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    str(phase7_output)
                ]
                subprocess.run(dual_mono_cmd, check=True, capture_output=True)
                logger.info(f"Phase 7 complete: Converted to dual-mono")
                if asset_id:
                    _update_sot_cue_block(episode, slug, asset_id, {
                        'ProcessingStatus': 'Phase 7 Complete: Dual-Mono Conversion Applied',
                        'AudioProcessing': 'Dual-mono conversion (unbalanced channels detected)'
                    })
            else:
                import shutil
                shutil.copy2(phase6_output, phase7_output)
                logger.info(f"Phase 7 complete: Channels balanced, no conversion needed")
                if asset_id:
                    _update_sot_cue_block(episode, slug, asset_id, {
                        'ProcessingStatus': 'Phase 7 Complete: Audio Channels OK',
                        'AudioProcessing': 'Channels balanced'
                    })

        # ================================================================
        # PHASE 8: Audio Normalization (EBU R128 loudness)
        #  - -23 LUFS target, dynamic range compression, peak limit -1dB
        #  - Skipped entirely when the source has no audio track.
        # ================================================================
        if not has_audio:
            logger.info(f"Phase 8: Skipped (no audio track) for {temp_job_id}")
            _update_job_status(temp_job_id, 'phase8', 'skipped')
            phase8_output = phase7_output
            if asset_id:
                _update_sot_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': 'Phase 8 Skipped: No Audio Track'
                })
        else:
            logger.info(f"Phase 8: Audio normalization for {temp_job_id}")
            _update_job_status(temp_job_id, 'phase8', 'processing')

            phase8_output = working_dir / f"{temp_job_id}_8_audio-normalized.mp4"
            phase8_cmd = [
                ffmpeg, "-y",
                "-i", str(phase7_output),
                "-c:v", "copy",
                "-af", "loudnorm=I=-23:TP=-1:LRA=11,acompressor=threshold=-18dB:ratio=4:attack=5:release=50",
                "-c:a", "aac",
                "-b:a", "192k",
                str(phase8_output)
            ]
            subprocess.run(phase8_cmd, check=True, capture_output=True)
            logger.info(f"Phase 8 complete: {phase8_output}")
            if asset_id:
                _update_sot_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': 'Phase 8 Complete: Audio Normalized'
                })

        # ================================================================
        # PHASE 9: Derivative Extraction
        #  - Generate 15 thumbnail options + MP3 audio extract
        # ================================================================
        logger.info(f"Phase 9: Derivative extraction for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase9', 'processing')

        # Get video duration for thumbnail spacing (use the processed clip)
        duration_probe = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(phase8_output)],
            capture_output=True, text=True, check=True
        )
        video_duration = float(duration_probe.stdout.strip())

        num_thumbnails = 15  # Generate 15 options for user selection

        if video_duration < 10:
            start_offset = min(0.5, video_duration * 0.1)
            end_offset = max(start_offset, video_duration - start_offset)
            logger.info(f"Phase 9: Short video ({video_duration:.1f}s), using reduced offsets: {start_offset:.1f}s")
        else:
            start_offset = 2
            end_offset = max(2, video_duration - 2)

        usable_duration = end_offset - start_offset

        thumbnail_times = []
        if usable_duration > 0:
            for i in range(num_thumbnails):
                time_point = start_offset + (usable_duration * i / (num_thumbnails - 1))
                thumbnail_times.append(time_point)
        else:
            for i in range(num_thumbnails):
                time_point = video_duration * i / (num_thumbnails - 1)
                thumbnail_times.append(max(0.1, time_point))
            logger.warning(f"Phase 9: Very short video, using full duration for thumbnails")

        phase9_thumbs = []
        thumbnail_data = []  # Store (filename, sharpness, time_point) tuples
        for i, time_point in enumerate(thumbnail_times, 1):
            thumb_file = working_dir / f"{temp_job_id}_9_thumb_{i:02d}.png"
            thumb_cmd = [
                ffmpeg, "-y",
                "-i", str(phase8_output),
                "-ss", str(time_point),
                "-vframes", "1",
                str(thumb_file)
            ]
            subprocess.run(thumb_cmd, check=True, capture_output=True)

            # Calculate sharpness score — also validates the file is a real PNG.
            # A single corrupt thumbnail shouldn't kill an otherwise successful job.
            try:
                sharpness = calculate_sharpness_simple(str(thumb_file))
            except (ValueError, FileNotFoundError) as e:
                logger.warning(f"Phase 9: skipping thumbnail {i}/{num_thumbnails} at {time_point:.1f}s ({e})")
                try:
                    thumb_file.unlink()
                except FileNotFoundError:
                    pass
                continue

            phase9_thumbs.append(thumb_file)
            thumbnail_data.append({
                'filename': f"{temp_job_id}_9_thumb_{i:02d}.png",
                'sharpness': sharpness,
                'time': time_point,
                'index': i
            })
            logger.info(f"Phase 9: Generated thumbnail {i}/{num_thumbnails} at {time_point:.1f}s (sharpness: {sharpness:.1f})")

        thumbnail_data_sorted = sorted(thumbnail_data, key=lambda x: x['sharpness'], reverse=True)

        max_sharpness = thumbnail_data_sorted[0]['sharpness'] if thumbnail_data_sorted else 0
        avg_sharpness = sum(t['sharpness'] for t in thumbnail_data) / len(thumbnail_data) if thumbnail_data else 0

        if max_sharpness < SHARPNESS_THRESHOLD_BLURRY:
            logger.warning(f"⚠️ Phase 9: ALL thumbnails appear blurry! Max sharpness: {max_sharpness:.1f} (threshold: {SHARPNESS_THRESHOLD_BLURRY})")
            logger.warning(f"⚠️ Source video may contain motion blur or be out of focus")
        elif avg_sharpness < SHARPNESS_THRESHOLD_WARNING:
            logger.warning(f"⚠️ Phase 9: Thumbnails have below-average sharpness. Avg: {avg_sharpness:.1f}")

        thumbnail_filenames = [t['filename'] for t in thumbnail_data]
        best_thumbnail_idx = next((i for i, t in enumerate(thumbnail_data) if t['filename'] == thumbnail_data_sorted[0]['filename']), 0)

        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.thumbnail_candidates = thumbnail_filenames
                job.selected_thumbnail = thumbnail_data_sorted[0]['filename'] if thumbnail_data_sorted else thumbnail_filenames[0]
                db.commit()

        logger.info(f"Phase 9: Stored {len(thumbnail_filenames)} thumbnail candidates (best sharpness: {max_sharpness:.1f} at index {best_thumbnail_idx + 1})")

        processing_report["phases"]["phase9"] = {
            "status": "success",
            "data": {
                "thumbnail_count": len(thumbnail_data),
                "thumbnail_data": thumbnail_data,
                "best_thumbnail": thumbnail_data_sorted[0] if thumbnail_data_sorted else None,
                "max_sharpness": max_sharpness,
                "avg_sharpness": avg_sharpness
            }
        }

        if max_sharpness < SHARPNESS_THRESHOLD_BLURRY:
            processing_report["warnings"].append(f"low_sharpness: All thumbnails appear blurry (max: {max_sharpness:.1f})")
        elif avg_sharpness < SHARPNESS_THRESHOLD_WARNING:
            processing_report["warnings"].append(f"moderate_blur: Thumbnails below average sharpness (avg: {avg_sharpness:.1f})")

        # Audio extract (full segment) — skipped when source has no audio track
        if has_audio:
            phase9_audio = working_dir / f"{temp_job_id}_9_audio.mp3"
            audio_cmd = [
                ffmpeg, "-y",
                "-i", str(phase8_output),
                "-vn",
                "-acodec", "libmp3lame",
                "-ab", "192k",
                str(phase9_audio)
            ]
            subprocess.run(audio_cmd, check=True, capture_output=True)
            logger.info(f"Phase 9 complete: thumbnails + audio")
            phase9_status = 'Phase 9 Complete: Thumbnails + MP3 Generated'
        else:
            phase9_audio = None
            logger.info(f"Phase 9 complete: thumbnails only (no audio track)")
            phase9_status = 'Phase 9 Complete: Thumbnails Only (No Audio Track)'

        if asset_id:
            _update_sot_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': phase9_status
            })

        # ================================================================
        # PHASE 10: Final Move and Rename
        #  - Move to episode assets directory, rename with normalized slug
        # ================================================================
        logger.info(f"Phase 10: Final move for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase10', 'processing')

        final_video_dir = media_root / "episodes" / episode / "assets" / "video"
        final_thumb_dir = media_root / "episodes" / episode / "assets" / "thumbnails"
        final_video_dir.mkdir(parents=True, exist_ok=True)
        final_thumb_dir.mkdir(parents=True, exist_ok=True)

        final_video = final_video_dir / f"{normalized_slug}.mp4"
        final_audio = final_video_dir / f"{normalized_slug}.mp3" if has_audio else None

        import shutil
        shutil.move(str(phase8_output), str(final_video))
        if has_audio and phase9_audio is not None:
            shutil.move(str(phase9_audio), str(final_audio))

        final_thumbs = []
        for i, thumb_file in enumerate(phase9_thumbs, 1):
            final_thumb = final_thumb_dir / f"{normalized_slug}-thumb-{i:02d}.png"
            shutil.move(str(thumb_file), str(final_thumb))
            final_thumbs.append(final_thumb)

        logger.info(f"Phase 10 complete: video/audio moved to {final_video_dir}, {len(final_thumbs)} thumbnails moved to {final_thumb_dir}")

        # Get final video duration for metadata
        duration_cmd = [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(final_video)
        ]
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        duration = float(duration_result.stdout.strip())

        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.current_phase = 'phase10'
                job.status = 'processing'
                job.final_video_path = str(final_video.relative_to(episodes_root))
                job.final_audio_path = str(final_audio.relative_to(episodes_root)) if final_audio else None
                job.final_thumbnail_path = str(final_thumbs[0].relative_to(episodes_root)) if final_thumbs else None
                db.commit()

                # Create parent/child asset relationship if source asset exists
                if job.source_asset_id and job.final_asset_id:
                    if '/app' not in sys.path:
                        sys.path.insert(0, '/app')
                    import models_assetid
                    AssetIDRegistry = models_assetid.AssetIDRegistry
                    AssetRelationship = models_assetid.AssetRelationship

                    final_asset = db.query(AssetIDRegistry).filter_by(asset_id=job.final_asset_id).first()
                    if final_asset:
                        final_asset.parent_asset_id = job.source_asset_id
                        final_asset.asset_role = 'final'
                        final_asset.derivative_type = job_type or 'trimmed'
                        db.commit()
                        logger.info(f"✅ Updated final asset {job.final_asset_id} with parent {job.source_asset_id}")

                    relationship = AssetRelationship(
                        parent_asset_id=job.source_asset_id,
                        child_asset_id=job.final_asset_id,
                        relationship_type=f"{job_type}_from" if job_type else "trimmed_from",
                        processing_metadata={
                            'trim_start': trim_start,
                            'trim_end': trim_end,
                            'job_type': job_type,
                            'temp_job_id': temp_job_id,
                            'processing_date': str(func.now())
                        }
                    )
                    db.add(relationship)
                    db.commit()
                    logger.info(f"✅ Created asset relationship: {job.source_asset_id} → {job.final_asset_id}")

        # Convert duration to HH:MM:SS format
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        thumbnail_urls = [
            f"/episodes/{episode}/assets/thumbnails/{normalized_slug}-thumb-{i:02d}.png"
            for i in range(1, 16)
        ]

        # ================================================================
        # PHASE 11: Post-Analysis (verify final output)
        # ================================================================
        logger.info(f"Phase 11: Post-analysis of final video for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase11', 'processing')

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

        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.post_analysis = post_analysis_data
                db.commit()

        processing_report["phases"]["phase11"] = {"status": "success", "data": post_analysis_data}
        processing_report["overall_status"] = "completed"
        logger.info(f"Phase 11 complete: {post_analysis_data}")

        # Update cue block with final completion and all MediaURLs
        if asset_id:
            final_outcue = derive_outcue(transcription_text) if transcription_text else ''
            cue_updates = {
                'ProcessingStatus': 'Complete',
                'MediaURL': f"/episodes/{episode}/assets/video/{normalized_slug}.mp4",
                'ThumbnailURL': thumbnail_urls[7],  # Middle thumbnail (8/15) as primary
                'ThumbnailOptions': json.dumps(thumbnail_urls),
                'Duration': duration_formatted,
                'Transcription': transcription_text or '',
                'Outcue': final_outcue
            }
            if has_audio:
                cue_updates['AudioURL'] = f"/episodes/{episode}/assets/video/{normalized_slug}.mp3"
            _update_sot_cue_block(episode, slug, asset_id, cue_updates)

        # Replace source AssetID with final AssetID in cue block
        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job and job.source_asset_id and job.final_asset_id and job.source_asset_id != job.final_asset_id:
                logger.info(f"🔄 Replacing AssetID in cue: {job.source_asset_id} → {job.final_asset_id}")
                _replace_sot_cue_asset_id(episode, job.source_asset_id, job.final_asset_id)

        # Store final processing report and mark completed
        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.processing_report = processing_report
                job.current_phase = 'completed'
                job.status = 'completed'
                db.commit()
                logger.info(f"✅ Job {temp_job_id} marked as completed")

        # Handle devel_mode: keep or clean up working directory
        if devel_mode:
            logger.info(f"DEVEL MODE: Keeping working directory with intermediate files: {working_dir}")
            processing_report["intermediate_files"] = [
                str(f.relative_to(media_root)) for f in working_dir.glob("*")
            ]
        else:
            logger.info(f"Cleaning up working directory: {working_dir}")
            shutil.rmtree(working_dir)

        logger.info(f"Multi-phase processing complete for {temp_job_id}")

        return {
            "temp_job_id": temp_job_id,
            "episode": episode,
            "slug": normalized_slug,
            "asset_id": asset_id,
            "video_path": str(final_video.relative_to(episodes_root)),
            "audio_path": str(final_audio.relative_to(episodes_root)) if final_audio else None,
            "thumbnail_path": str(final_thumbs[7].relative_to(episodes_root)) if len(final_thumbs) > 7 else (str(final_thumbs[0].relative_to(episodes_root)) if final_thumbs else None),
            "thumbnail_options": [str(t.relative_to(episodes_root)) for t in final_thumbs],
            "duration": duration,
            "transcription": transcription_text,
            "status": "completed",
            "pre_analysis": pre_analysis_data,
            "post_analysis": post_analysis_data,
            "processing_report": processing_report,
            "devel_mode": devel_mode
        }

    except subprocess.CalledProcessError as e:
        if hasattr(e, 'stderr') and e.stderr:
            stderr_text = e.stderr.decode('utf-8', errors='replace') if isinstance(e.stderr, bytes) else str(e.stderr)
        else:
            stderr_text = f"Exit code {e.returncode}"
        error_msg = f"FFmpeg error in sot_finalize: {stderr_text}"
        logger.error(error_msg)
        _update_job_status(temp_job_id, 'phase11', 'failed', error_msg)
        raise
    except Exception as e:
        error_msg = f"sot_finalize error: {str(e)}"
        logger.error(error_msg)
        _update_job_status(temp_job_id, 'unknown', 'failed', error_msg)
        raise


@shared_task(
    bind=True,
    queue='media',
    name='services.ffmpeg_tasks.process_sot_video_multi_phase',
    max_retries=3,
    soft_time_limit=1800,      # Warn at 30 minutes
    time_limit=2400,           # Hard kill at 40 minutes
    acks_late=True,            # Don't ack until task completes
    reject_on_worker_lost=True  # Reject task if worker dies
)
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
    Orchestrator for SOT video processing.

    For montage / individual_clips this delegates to the existing helpers
    (unchanged). For single_trim / full_process it builds and fires a Celery
    CHAIN of three tasks so transcription runs as a real chain LINK on the
    whisper queue — NO `.get()` inside a task:

        chain(sot_prepare.s(...), transcribe_sot_audio.s(), sot_finalize.s())

    CORRECTED PHASE ORDER (trim moved EARLY; integers 1-11):
    - Phase 1:  Validate upload                (sot_prepare,        media)
    - Phase 2:  Probe source (raw, sanity)     (sot_prepare,        media)
    - Phase 3:  Trim (no-op if not requested)  (sot_prepare,        media)
    - Phase 4:  Transcribe TRIMMED audio       (transcribe_sot_audio, whisper)
    - Phase 5:  Analyze trimmed clip           (sot_finalize,       media)
    - Phase 6:  Normalize video                (sot_finalize,       media)
    - Phase 7:  Fix audio channels             (sot_finalize,       media)
    - Phase 8:  Normalize loudness (EBU R128)  (sot_finalize,       media)
    - Phase 9:  Derivatives (thumbnails + MP3) (sot_finalize,       media)
    - Phase 10: Move to assets                 (sot_finalize,       media)
    - Phase 11: Post-analysis verify           (sot_finalize,       media)

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
        For single_trim/full_process: a dict {"chain_id": <AsyncResult id>, ...}
        describing the dispatched chain (the chain runs asynchronously, so the
        final result dict is produced by sot_finalize, not returned here).
        For montage/individual_clips: the existing synchronous return value.
    """
    from celery import chain

    # Cross-platform working directory (used only for the montage/individual paths)
    shared_media_root = _resolve_shared_media_root()
    working_dir = shared_media_root / "preproc" / "working" / temp_job_id
    normalized_slug = _normalize_slug(slug)

    worker_name = platform.node()
    worker_platform = platform.system()

    try:
        logger.info(f"\U0001F3AC Orchestrating SOT processing on {worker_name} ({worker_platform}) for {temp_job_id} (job_type: {job_type}, devel_mode: {devel_mode})")

        import json
        from models_v2 import SOTProcessingJob

        # Update job record with job_type and clips_data
        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.job_type = job_type
                if clips:
                    job.clips_data = json.dumps(clips)
                db.commit()

        # Route to appropriate processing workflow based on job_type
        if job_type == "individual_clips":
            logger.info(f"Executing INDIVIDUAL_CLIPS workflow for {temp_job_id} with {len(clips or [])} clips")
            # DEPRECATED path — left UNCHANGED.
            return _process_individual_clips(
                temp_job_id, episode, slug, clips, asset_id, working_dir, normalized_slug
            )
        elif job_type == "montage":
            logger.info(f"Executing MONTAGE workflow for {temp_job_id} with {len(clips or [])} clips")
            # Montage path — left UNCHANGED (trim-correct upstream).
            return _process_montage(
                temp_job_id, episode, slug, clips, asset_id, working_dir, normalized_slug
            )

        # single_trim / full_process → fire the 3-link chain.
        logger.info(f"Executing {job_type.upper()} workflow for {temp_job_id} via Celery chain")
        pipeline = chain(
            sot_prepare.s(
                temp_job_id=temp_job_id,
                episode=episode,
                slug=slug,
                trim_start=trim_start,
                trim_end=trim_end,
                job_type=job_type,
                asset_id=asset_id,
                devel_mode=devel_mode,
            ),
            transcribe_sot_audio.s(),
            sot_finalize.s(),
        )
        async_result = pipeline.apply_async()
        chain_id = async_result.id
        logger.info(f"\u2705 Dispatched SOT chain {chain_id} for {temp_job_id}")

        # Record the chain's terminal task id on the job for traceability.
        try:
            with db_session() as db:
                job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
                if job:
                    job.celery_task_id = chain_id
                    job.status = 'processing'
                    job.current_phase = 'phase1'
                    db.commit()
        except Exception as track_err:
            logger.warning(f"Could not record chain id on job {temp_job_id}: {track_err}")

        return {
            "temp_job_id": temp_job_id,
            "episode": episode,
            "slug": normalized_slug,
            "asset_id": asset_id,
            "job_type": job_type,
            "chain_id": chain_id,
            "status": "dispatched",
            "message": "SOT processing chain dispatched (sot_prepare → transcribe_sot_audio → sot_finalize)",
            "devel_mode": devel_mode,
        }

    except Exception as e:
        error_msg = f"Failed to dispatch SOT processing chain: {str(e)}"
        logger.error(error_msg)
        _update_job_status(temp_job_id, 'phase1', 'failed', error_msg)
        raise


# ============================================================================
# VO (VOICE OVER) VIDEO PROCESSING
# ============================================================================
# Simplified processing for B-roll video that will be voiced over live.
# NO audio requirements - skips transcription, audio normalization, MP3 extraction.
# ============================================================================

def _update_vo_cue_block(episode: str, slug: str, asset_id: str, updates: dict):
    """
    Update a VO cue block in the rundown item's script_content — mirror of
    _update_sot_cue_block with [Type: VO].

    REWRITTEN 2026-07-18: the previous implementation was pre-DB-first dead
    code — it looked for cues in a YAML-frontmatter `cues:` metadata list
    (a format that no longer exists) and filtered on a nonexistent
    RundownItem.episode_number column, so every VO write-back silently
    failed and VO cues stayed at 'MediaURL: Processing...' forever.
    """
    try:
        from models_v2 import Rundown, RundownItem, Episode
        import re

        with db_session() as db:
            rundown = db.query(Rundown).join(Episode).filter(Episode.episode_number == episode).first()
            if not rundown:
                logger.warning(f"No rundown found for episode {episode}")
                return False

            items = db.query(RundownItem).filter_by(rundown_id=rundown.id).all()

            cue_pattern = re.compile(
                r'(<!-- Begin Cue(?: collapsed)? -->(?:(?!<!-- End Cue -->).)*?\[Type:\s*VO\](?:(?!<!-- End Cue -->).)*?<!-- End Cue -->)',
                re.DOTALL | re.IGNORECASE
            )
            asset_pattern = re.compile(r'\[Asset\s*[Ii][Dd]:\s*' + re.escape(asset_id) + r'\s*\]', re.IGNORECASE)

            for item in items:
                if not item.script_content:
                    continue
                for match in cue_pattern.finditer(item.script_content):
                    cue_block = match.group(1)
                    if not asset_pattern.search(cue_block):
                        continue

                    updated_cue = cue_block
                    for field, value in updates.items():
                        field_pattern = re.compile(rf'\[{field}:\s*[^\]]*\]', re.IGNORECASE)
                        if field_pattern.search(updated_cue):
                            updated_cue = field_pattern.sub(f'[{field}: {value}]', updated_cue)
                        else:
                            updated_cue = updated_cue.replace(
                                '<!-- End Cue -->',
                                f'[{field}: {value}]\n<!-- End Cue -->'
                            )

                    item.script_content = item.script_content.replace(cue_block, updated_cue)
                    db.commit()
                    logger.info(f"✅ Updated VO cue block in item {item.id} for AssetID {asset_id}")
                    return True

            logger.warning(f"⚠️ VO cue block not found for asset_id={asset_id} in episode={episode}")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to update VO cue block: {e}")
        return False


@shared_task(
    bind=True,
    name='services.ffmpeg_tasks.process_vo_video',
    queue='media',
    soft_time_limit=1200,      # Warn at 20 minutes (shorter than SOT - no audio processing)
    time_limit=1800,           # Hard kill at 30 minutes
    acks_late=True,
    reject_on_worker_lost=True
)
def process_vo_video(
    self,
    temp_job_id: str,
    episode: str,
    slug: str,
    trim_start: str = "00:00:00",
    trim_end: str = "00:00:00",
    asset_id: str = None
):
    """
    VO (Voice Over) video processing - simplified pipeline for B-roll.

    This is a streamlined version of SOT processing that:
    - Does NOT require audio tracks
    - Does NOT transcribe audio (no Whisper)
    - Does NOT normalize audio (no EBU R128)
    - Does NOT extract MP3
    - DOES normalize video codec/resolution
    - DOES generate thumbnails for selection
    - DOES support trimming

    Use case: B-roll footage that host will voice over live during the show.

    Phases:
    - Phase 0: Pre-Analysis (video only, no audio validation)
    - Phase 1: Trimming (if trim points provided)
    - Phase 2: Video Normalization (codec, resolution, framerate)
    - Phase 3: Generate Thumbnails (10-15 candidates)
    - Phase 4: Final Move to Assets
    - Phase 5: Post-Analysis

    Args:
        temp_job_id: Temporary job ID (e.g., "vo_20251011_143022_abc123")
        episode: Episode number (e.g., "0245")
        slug: Item slug for final naming
        trim_start: Start time for trimming (HH:MM:SS)
        trim_end: End time for trimming (HH:MM:SS)
        asset_id: AssetID for linking to cue block

    Returns:
        dict: Final file paths, processing metadata
    """
    import json
    import shutil
    from models_v2 import SOTProcessingJob

    # Cross-platform working directory
    media_root = get_media_root()
    if platform.system() == 'Windows':
        shared_media_root = Path('W:/mnt/sync/shared_media')
    elif Path('/shared_media').exists():
        shared_media_root = Path('/shared_media')
    else:
        shared_media_root = Path('/mnt/sync/shared_media')
    working_dir = shared_media_root / "preproc" / "working" / temp_job_id
    normalized_slug = _normalize_slug(slug)

    worker_name = platform.node()
    worker_platform = platform.system()

    try:
        logger.info(f"🎥 Starting VO processing on {worker_name} ({worker_platform}) for {temp_job_id}")

        # Initialize processing report
        processing_report = {
            "job_id": temp_job_id,
            "job_category": "vo",
            "overall_status": "in_progress",
            "start_time": str(func.now()),
            "phases": {},
            "warnings": []
        }

        # Get platform-appropriate binaries
        ffmpeg = get_ffmpeg_binary()
        ffprobe = get_ffprobe_binary()

        # Input file from background upload
        input_file = working_dir / f"{temp_job_id}_upload.mp4"
        if not input_file.exists():
            raise FileNotFoundError(f"Upload file not found: {input_file}")

        # ================================================================
        # PHASE 0: Technical Analysis (VIDEO ONLY - no audio validation)
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

        frame_rate_str = video_stream.get('r_frame_rate', '0/1')
        if '/' in frame_rate_str:
            num, denom = map(int, frame_rate_str.split('/'))
            frame_rate = round(num / denom, 2) if denom != 0 else 0
        else:
            frame_rate = float(frame_rate_str)

        # Determine orientation
        if width > height:
            orientation = 'horizontal'
        elif height > width:
            orientation = 'vertical'
        else:
            orientation = 'square'

        # Format duration
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        logger.info(f"Phase 0 analysis: {width}x{height} {orientation}, {frame_rate}fps, {duration_formatted}")

        # Validation (minimal for VO - no audio requirement)
        validation_errors = []
        if width < 100 or height < 100:
            validation_errors.append(f"Resolution too small: {width}x{height}")
        if width == 0 or height == 0:
            validation_errors.append(f"Invalid resolution: {width}x{height}")
        if duration_seconds < 1:
            validation_errors.append(f"Video too short: {duration_seconds:.2f}s")

        if validation_errors:
            error_msg = "; ".join(validation_errors)
            logger.error(f"❌ VO validation failed: {error_msg}")
            _update_job_status(temp_job_id, 'validation', 'failed', error_msg)
            raise ValueError(f"VO validation failed: {error_msg}")

        pre_analysis_data = {
            "duration": duration_formatted,
            "duration_seconds": duration_seconds,
            "resolution": f"{width}x{height}",
            "width": width,
            "height": height,
            "orientation": orientation,
            "framerate": frame_rate,
            "audio_required": False  # Key difference from SOT
        }

        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.pre_analysis = pre_analysis_data
                db.commit()

        processing_report["phases"]["phase0"] = {"status": "success", "data": pre_analysis_data}

        if asset_id:
            _update_vo_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 0 Complete: Analysis',
                'Duration': duration_formatted,
                'Resolution': f'{width}x{height}',
                'Orientation': orientation
            })

        # ================================================================
        # PHASE 1: Trimming (if needed)
        # ================================================================
        def is_zero_time(time_str):
            return time_str in ("00:00:00", "00:00:00:00", "0", "0.0", "")

        def time_to_seconds(time_str):
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = map(float, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 4:
                h, m, s, f = map(float, parts)
                return h * 3600 + m * 60 + s + (f / 30.0)
            return 0.0

        current_input = input_file

        if not is_zero_time(trim_start) or not is_zero_time(trim_end):
            logger.info(f"Phase 1: Trimming for {temp_job_id} (start={trim_start}, end={trim_end})")
            _update_job_status(temp_job_id, 'phase1', 'processing')

            phase1_output = working_dir / f"{temp_job_id}_1_trimmed.mp4"

            # Frame-accurate trim: -ss BEFORE -i fast-seeks to the nearest
            # keyframe, then re-encoding decodes forward to the EXACT
            # requested IN/OUT frame. Stream-copy (-c copy) was keyframe-
            # bounded — on long-GOP sources (surveillance footage) the cut
            # landed seconds off the requested points. Same fix as the SOT
            # phase-3 trim (2026-06). Audio (if any) re-encodes to AAC via
            # the optional 0:a:0? map; audio-less sources pass through.
            from platform_utils import IS_WINDOWS, has_nvidia_gpu
            if IS_WINDOWS and has_nvidia_gpu():
                trim_encoder_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18", "-maxrate", "8M", "-bufsize", "16M"]
            else:
                trim_encoder_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "18"]

            if not is_zero_time(trim_end):
                start_sec = time_to_seconds(trim_start)
                end_sec = time_to_seconds(trim_end)
                trim_duration = end_sec - start_sec

                phase1_cmd = [
                    ffmpeg, "-y",
                    "-ss", str(start_sec),
                    "-i", str(current_input),
                    "-t", str(trim_duration),
                    "-map", "0:v:0", "-map", "0:a:0?",
                    *trim_encoder_args,
                    "-c:a", "aac", "-b:a", "192k",
                    str(phase1_output)
                ]
            else:
                start_sec = time_to_seconds(trim_start)
                phase1_cmd = [
                    ffmpeg, "-y",
                    "-ss", str(start_sec),
                    "-i", str(current_input),
                    "-map", "0:v:0", "-map", "0:a:0?",
                    *trim_encoder_args,
                    "-c:a", "aac", "-b:a", "192k",
                    str(phase1_output)
                ]

            subprocess.run(phase1_cmd, check=True, capture_output=True)
            current_input = phase1_output
            logger.info(f"Phase 1 complete: Trimmed to {phase1_output}")

            if asset_id:
                _update_vo_cue_block(episode, slug, asset_id, {
                    'ProcessingStatus': 'Phase 1 Complete: Trimmed'
                })
        else:
            logger.info(f"Phase 1: Skipped (no trimming needed)")

        # ================================================================
        # PHASE 2: Video Normalization
        # - H.264/AAC MP4
        # - 29.97fps
        # - Max width 1920
        # - Audio passed through as-is (if present)
        # ================================================================
        logger.info(f"Phase 2: Video normalization for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase2', 'processing')

        phase2_output = working_dir / f"{temp_job_id}_2_normalized.mp4"

        from platform_utils import IS_WINDOWS, has_nvidia_gpu
        if IS_WINDOWS and has_nvidia_gpu():
            video_encoder_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18", "-maxrate", "8M", "-bufsize", "16M"]
        else:
            video_encoder_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "18"]

        # Check if video has audio - if so, copy it through
        audio_check_cmd = [
            ffprobe, "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0",
            str(current_input)
        ]
        audio_check = subprocess.run(audio_check_cmd, capture_output=True, text=True)
        has_audio = audio_check.stdout.strip() == "audio"

        if has_audio:
            # Video has audio - copy it through
            phase2_cmd = [
                ffmpeg, "-y",
                "-i", str(current_input),
                *video_encoder_args,
                "-r", "29.97",
                "-vf", "scale='if(gt(iw,1920),1920,-2)':'-2'",
                "-c:a", "copy",  # Pass audio through unchanged
                str(phase2_output)
            ]
        else:
            # Video has no audio
            phase2_cmd = [
                ffmpeg, "-y",
                "-i", str(current_input),
                *video_encoder_args,
                "-r", "29.97",
                "-vf", "scale='if(gt(iw,1920),1920,-2)':'-2'",
                "-an",  # No audio output
                str(phase2_output)
            ]

        subprocess.run(phase2_cmd, check=True, capture_output=True)
        current_input = phase2_output
        logger.info(f"Phase 2 complete: Video normalized to {phase2_output}")

        if asset_id:
            _update_vo_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 2 Complete: Normalized'
            })

        # ================================================================
        # PHASE 3: Generate Thumbnails (15 candidates)
        # ================================================================
        logger.info(f"Phase 3: Thumbnail generation for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase3', 'processing')

        # Get updated duration after trimming
        duration_probe = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(current_input)],
            capture_output=True, text=True, check=True
        )
        video_duration = float(duration_probe.stdout.strip())

        # Generate 15 thumbnails with adaptive offsets for short videos
        num_thumbnails = 15

        if video_duration < 10:
            # Short video: use minimal offsets (0.5s) to maximize usable range
            start_offset = min(0.5, video_duration * 0.1)
            end_offset = max(start_offset, video_duration - start_offset)
            logger.info(f"Phase 3: Short video ({video_duration:.1f}s), using reduced offsets: {start_offset:.1f}s")
        else:
            # Normal video: skip first/last 2 seconds to avoid fade/black
            start_offset = 2
            end_offset = max(2, video_duration - 2)

        usable_duration = end_offset - start_offset

        thumbnail_times = []
        if usable_duration > 0:
            for i in range(num_thumbnails):
                time_point = start_offset + (usable_duration * i / (num_thumbnails - 1))
                thumbnail_times.append(time_point)
        else:
            # Video extremely short, spread across full duration
            for i in range(num_thumbnails):
                time_point = video_duration * i / (num_thumbnails - 1)
                thumbnail_times.append(max(0.1, time_point))
            logger.warning(f"Phase 3: Very short video, using full duration for thumbnails")

        phase3_thumbs = []
        thumbnail_data = []  # Store (filename, sharpness, time_point) tuples
        for i, time_point in enumerate(thumbnail_times, 1):
            thumb_file = working_dir / f"{temp_job_id}_thumb_{i:02d}.png"
            # Use accurate seeking (-ss after -i) for better frame quality
            # This decodes from nearest keyframe ensuring sharp frames
            # PNG format for sharpness validation
            thumb_cmd = [
                ffmpeg, "-y",
                "-i", str(current_input),
                "-ss", str(time_point),
                "-vframes", "1",
                str(thumb_file)
            ]
            subprocess.run(thumb_cmd, check=True, capture_output=True)

            # Calculate sharpness score - also validates the file is a real PNG.
            # If validation fails, drop the bad frame and keep going — one
            # corrupt thumbnail shouldn't kill an otherwise successful job.
            try:
                sharpness = calculate_sharpness_simple(str(thumb_file))
            except (ValueError, FileNotFoundError) as e:
                logger.warning(f"Phase 3: skipping thumbnail {i}/{num_thumbnails} at {time_point:.1f}s ({e})")
                try:
                    thumb_file.unlink()
                except FileNotFoundError:
                    pass
                continue

            phase3_thumbs.append(thumb_file)
            thumbnail_data.append({
                'filename': f"{temp_job_id}_thumb_{i:02d}.png",
                'sharpness': sharpness,
                'time': time_point,
                'index': i
            })
            logger.info(f"Phase 3: Generated thumbnail {i}/{num_thumbnails} at {time_point:.1f}s (sharpness: {sharpness:.1f})")

        # Sort thumbnails by sharpness (highest first) for better default selection
        thumbnail_data_sorted = sorted(thumbnail_data, key=lambda x: x['sharpness'], reverse=True)

        # Check for blur warning
        max_sharpness = thumbnail_data_sorted[0]['sharpness'] if thumbnail_data_sorted else 0
        avg_sharpness = sum(t['sharpness'] for t in thumbnail_data) / len(thumbnail_data) if thumbnail_data else 0

        if max_sharpness < SHARPNESS_THRESHOLD_BLURRY:
            logger.warning(f"⚠️ Phase 3: ALL thumbnails appear blurry! Max sharpness: {max_sharpness:.1f} (threshold: {SHARPNESS_THRESHOLD_BLURRY})")
            logger.warning(f"⚠️ Source video may contain motion blur or be out of focus")
        elif avg_sharpness < SHARPNESS_THRESHOLD_WARNING:
            logger.warning(f"⚠️ Phase 3: Thumbnails have below-average sharpness. Avg: {avg_sharpness:.1f}")

        # Keep original order for filenames list but track best thumbnail
        thumbnail_filenames = [t['filename'] for t in thumbnail_data]
        best_thumbnail_idx = next((i for i, t in enumerate(thumbnail_data) if t['filename'] == thumbnail_data_sorted[0]['filename']), 0)

        # Store thumbnails in database
        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.thumbnail_candidates = thumbnail_filenames
                # Select the SHARPEST thumbnail as default (not middle anymore)
                job.selected_thumbnail = thumbnail_data_sorted[0]['filename'] if thumbnail_data_sorted else thumbnail_filenames[0]
                db.commit()

        logger.info(f"Phase 3 complete: {len(thumbnail_filenames)} thumbnails (best sharpness: {max_sharpness:.1f} at index {best_thumbnail_idx + 1})")

        # Store thumbnail data with sharpness scores in processing_report for API access
        processing_report["phases"]["phase3"] = {
            "status": "success",
            "data": {
                "thumbnail_count": len(thumbnail_data),
                "thumbnail_data": thumbnail_data,  # Full array with sharpness scores
                "best_thumbnail": thumbnail_data_sorted[0] if thumbnail_data_sorted else None,
                "max_sharpness": max_sharpness,
                "avg_sharpness": avg_sharpness
            }
        }

        # Add blur warning to processing_report if detected
        if max_sharpness < SHARPNESS_THRESHOLD_BLURRY:
            processing_report["warnings"].append(f"low_sharpness: All thumbnails appear blurry (max: {max_sharpness:.1f})")
        elif avg_sharpness < SHARPNESS_THRESHOLD_WARNING:
            processing_report["warnings"].append(f"moderate_blur: Thumbnails below average sharpness (avg: {avg_sharpness:.1f})")

        if asset_id:
            _update_vo_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Phase 3 Complete: Thumbnails Generated'
            })

        # ================================================================
        # PHASE 4: Final Move to Assets
        # ================================================================
        logger.info(f"Phase 4: Final move for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase4', 'processing')

        # Create output directories
        final_video_dir = media_root / "episodes" / episode / "assets" / "video"
        final_thumb_dir = media_root / "episodes" / episode / "assets" / "thumbnails"
        final_video_dir.mkdir(parents=True, exist_ok=True)
        final_thumb_dir.mkdir(parents=True, exist_ok=True)

        # Move video
        final_video = final_video_dir / f"{normalized_slug}.mp4"
        shutil.move(str(current_input), str(final_video))

        # Move thumbnails (PNG format)
        final_thumbs = []
        for i, thumb_file in enumerate(phase3_thumbs, 1):
            final_thumb = final_thumb_dir / f"{normalized_slug}-thumb-{i:02d}.png"
            shutil.move(str(thumb_file), str(final_thumb))
            final_thumbs.append(final_thumb)

        logger.info(f"Phase 4 complete: Video and thumbnails moved to assets")

        # Get final duration
        duration_cmd = [
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(final_video)
        ]
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        final_duration = float(duration_result.stdout.strip())

        hours = int(final_duration // 3600)
        minutes = int((final_duration % 3600) // 60)
        seconds = int(final_duration % 60)
        final_duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # ================================================================
        # PHASE 5: Post-Analysis and Completion
        # ================================================================
        logger.info(f"Phase 5: Post-analysis for {temp_job_id}")
        _update_job_status(temp_job_id, 'phase5', 'processing')

        post_video_probe = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,r_frame_rate,codec_name",
             "-of", "json", str(final_video)],
            capture_output=True, text=True, check=True
        )
        post_video_info = json.loads(post_video_probe.stdout)
        post_video_stream = post_video_info['streams'][0] if post_video_info.get('streams') else {}

        post_analysis_data = {
            "duration": final_duration_formatted,
            "duration_seconds": final_duration,
            "resolution": f"{post_video_stream.get('width', 0)}x{post_video_stream.get('height', 0)}",
            "codec": post_video_stream.get('codec_name', 'unknown'),
            "file_size_mb": round(final_video.stat().st_size / (1024 * 1024), 2)
        }

        episodes_root = media_root / "episodes"

        with db_session() as db:
            job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
            if job:
                job.current_phase = 'completed'
                job.status = 'completed'
                job.final_video_path = str(final_video.relative_to(episodes_root))
                job.final_thumbnail_path = str(final_thumbs[0].relative_to(episodes_root))
                job.post_analysis = post_analysis_data
                job.processing_report = processing_report
                db.commit()

        # Build thumbnail URLs (PNG format)
        thumbnail_urls = [
            f"/episodes/{episode}/assets/thumbnails/{normalized_slug}-thumb-{i:02d}.png"
            for i in range(1, 16)
        ]

        # Update cue block with final completion
        if asset_id:
            _update_vo_cue_block(episode, slug, asset_id, {
                'ProcessingStatus': 'Complete',
                'MediaURL': f"/episodes/{episode}/assets/video/{normalized_slug}.mp4",
                'ThumbnailURL': thumbnail_urls[7],
                'ThumbnailOptions': json.dumps(thumbnail_urls),
                'Duration': final_duration_formatted
            })

        # Cleanup working directory
        logger.info(f"Cleaning up working directory: {working_dir}")
        shutil.rmtree(working_dir)

        logger.info(f"✅ VO processing complete for {temp_job_id}")

        return {
            "temp_job_id": temp_job_id,
            "episode": episode,
            "slug": normalized_slug,
            "asset_id": asset_id,
            "video_path": str(final_video.relative_to(episodes_root)),
            "thumbnail_path": str(final_thumbs[7].relative_to(episodes_root)),
            "thumbnail_options": [str(t.relative_to(episodes_root)) for t in final_thumbs],
            "duration": final_duration,
            "duration_formatted": final_duration_formatted,
            "status": "completed",
            "pre_analysis": pre_analysis_data,
            "post_analysis": post_analysis_data,
            "processing_report": processing_report
        }

    except subprocess.CalledProcessError as e:
        if hasattr(e, 'stderr') and e.stderr:
            stderr_text = e.stderr.decode('utf-8', errors='replace') if isinstance(e.stderr, bytes) else str(e.stderr)
        else:
            stderr_text = f"Exit code {e.returncode}"
        error_msg = f"FFmpeg error: {stderr_text}"
        logger.error(error_msg)
        _update_job_status(temp_job_id, 'failed', 'failed', error_msg)
        raise
    except Exception as e:
        error_msg = f"VO processing error: {str(e)}"
        logger.error(error_msg)
        _update_job_status(temp_job_id, 'failed', 'failed', error_msg)
        raise
