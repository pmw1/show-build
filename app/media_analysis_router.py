"""
Media Analysis Router - FFprobe integration for video/audio metadata extraction
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import subprocess
import json
import os
from pathlib import Path
import shutil
from datetime import datetime

router = APIRouter(prefix="/api/media", tags=["media-analysis"])

# Configure media storage paths
MEDIA_BASE = Path("/mnt/sync/disaffected/assets")
VIDEO_PATH = MEDIA_BASE / "video"
THUMBNAILS_PATH = MEDIA_BASE / "thumbnails"

# Ensure directories exist (only if we have permissions)
try:
    VIDEO_PATH.mkdir(parents=True, exist_ok=True)
    THUMBNAILS_PATH.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Skip directory creation if no permissions (directories likely exist)
    pass


def format_duration_timecode(seconds: float, fps: float = 29.97) -> str:
    """Convert seconds to HH:MM:SS:FF timecode format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    frames = int((seconds % 1) * fps)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"


def run_ffprobe(filepath: str) -> dict:
    """Run ffprobe on a media file and return metadata"""
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        filepath
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"FFprobe failed: {e.stderr}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse ffprobe output: {str(e)}")


def extract_thumbnail(filepath: str, output_path: str, timestamp: str = "00:00:01") -> bool:
    """Extract a thumbnail from video at specified timestamp"""
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output
        '-ss', timestamp,
        '-i', filepath,
        '-vframes', '1',
        '-q:v', '2',  # High quality
        output_path
    ]

    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


@router.post("/analyze-sot")
async def analyze_sot_media(file: UploadFile = File(...)):
    """
    Upload and analyze video/audio file for SOT cue
    Returns: metadata including duration, dimensions, fps, thumbnail
    """

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{file.filename}"
    filepath = VIDEO_PATH / filename

    # Save uploaded file
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Run ffprobe analysis
    try:
        probe_data = run_ffprobe(str(filepath))
    except Exception as e:
        # Clean up file on error
        filepath.unlink(missing_ok=True)
        raise e

    # Extract video stream data
    video_stream = next(
        (s for s in probe_data.get('streams', []) if s['codec_type'] == 'video'),
        None
    )

    # Extract audio stream data
    audio_stream = next(
        (s for s in probe_data.get('streams', []) if s['codec_type'] == 'audio'),
        None
    )

    format_data = probe_data.get('format', {})

    # Calculate FPS
    fps = 29.97  # Default NTSC
    if video_stream:
        fps_str = video_stream.get('r_frame_rate', '30000/1001')
        try:
            num, den = map(int, fps_str.split('/'))
            fps = num / den
        except:
            pass

    # Get duration
    duration_seconds = float(format_data.get('duration', 0))
    duration_timecode = format_duration_timecode(duration_seconds, fps)

    # Generate thumbnail
    thumbnail_filename = f"{timestamp}-{Path(file.filename).stem}.jpg"
    thumbnail_path = THUMBNAILS_PATH / thumbnail_filename
    thumbnail_url = ""

    if video_stream:
        if extract_thumbnail(str(filepath), str(thumbnail_path)):
            thumbnail_url = f"../assets/thumbnails/{thumbnail_filename}"

    # Build response
    response = {
        "slug": Path(file.filename).stem,
        "filename": filename,
        "media_url": f"../assets/video/{filename}",
        "duration": duration_timecode,
        "duration_seconds": duration_seconds,
        "fps": round(fps, 2),
        "thumbnail_url": thumbnail_url,
        "width": video_stream.get('width') if video_stream else None,
        "height": video_stream.get('height') if video_stream else None,
        "codec": video_stream.get('codec_name') if video_stream else audio_stream.get('codec_name'),
        "bitrate": int(format_data.get('bit_rate', 0)),
        "file_size": int(format_data.get('size', 0)),
        "has_video": video_stream is not None,
        "has_audio": audio_stream is not None
    }

    return JSONResponse(content=response)
