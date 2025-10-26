"""
Platform Utilities for Cross-Platform Media Processing

Provides path normalization, command detection, and platform-specific
optimizations for Celery workers running on Linux and Windows.

Usage:
    from platform_utils import normalize_path, get_ffmpeg_binary

    input_file = normalize_path("/mnt/sync/disaffected/episodes/0245/video.mp4")
    ffmpeg = get_ffmpeg_binary()
    subprocess.run([ffmpeg, "-i", str(input_file), ...])
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional


# Platform detection
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'


def get_media_root() -> Path:
    """
    Get platform-appropriate media root directory.

    Respects MEDIA_ROOT environment variable if set (for Docker containers).
    Falls back to platform defaults if not set.

    Returns:
        Path: Media root path (e.g., /home, /mnt/sync/disaffected, or W:/mnt/sync/disaffected)
    """
    # Check for MEDIA_ROOT environment variable (Docker containers)
    media_root_env = os.getenv('MEDIA_ROOT')
    if media_root_env:
        return Path(media_root_env)

    # Fall back to platform defaults
    if IS_WINDOWS:
        return Path('W:/mnt/sync/disaffected')
    else:
        return Path('/mnt/sync/disaffected')


def normalize_path(path_input) -> Path:
    """
    Convert any path format to platform-native Path object.

    Handles:
        - Linux paths: /mnt/sync/disaffected/...
        - Windows paths: Z:\\... or Z:/...
        - Relative paths: episodes/0245/...

    Args:
        path_input: String path or Path object

    Returns:
        Path: Platform-native pathlib.Path object

    Examples:
        # On Linux:
        normalize_path("Z:\\episodes\\0245\\video.mp4")
        # → PosixPath('/mnt/sync/disaffected/episodes/0245/video.mp4')

        # On Windows:
        normalize_path("/mnt/sync/disaffected/episodes/0245/video.mp4")
        # → WindowsPath('Z:\\episodes\\0245\\video.mp4')
    """
    path_str = str(path_input)

    # Normalize separators to forward slashes for processing
    path_str = path_str.replace('\\', '/')

    # Convert between Windows and Linux root paths
    if IS_WINDOWS:
        # Convert Linux path to Windows
        if path_str.startswith('/mnt/sync/disaffected'):
            path_str = path_str.replace('/mnt/sync/disaffected', 'W:/mnt/sync/disaffected', 1)
        # Ensure W: paths use backslashes on Windows
        if path_str.startswith('W:'):
            path_str = path_str.replace('/', '\\')
    else:
        # Convert Windows path to Linux
        if path_str.upper().startswith('W:'):
            # Remove W: prefix and extract the path after /mnt/sync/disaffected
            path_str = path_str[2:].lstrip('/\\')  # Remove W: prefix
            # W:\mnt\sync\disaffected\... -> /mnt/sync/disaffected/...
            if path_str.lower().startswith('mnt\\sync\\disaffected') or path_str.lower().startswith('mnt/sync/disaffected'):
                path_str = '/' + path_str
            else:
                path_str = f'/mnt/sync/disaffected/{path_str}'
        # Ensure forward slashes on Linux
        path_str = path_str.replace('\\', '/')

    return Path(path_str)


def get_ffmpeg_binary() -> str:
    """
    Get platform-appropriate FFmpeg binary command.

    Returns:
        str: 'ffmpeg.exe' on Windows, 'ffmpeg' on Linux
    """
    if IS_WINDOWS:
        return 'ffmpeg.exe'
    else:
        return 'ffmpeg'


def get_ffprobe_binary() -> str:
    """
    Get platform-appropriate FFprobe binary command.

    Returns:
        str: 'ffprobe.exe' on Windows, 'ffprobe' on Linux
    """
    if IS_WINDOWS:
        return 'ffprobe.exe'
    else:
        return 'ffprobe'


def has_nvidia_gpu() -> bool:
    """
    Check if NVIDIA GPU with NVENC support is available (Windows).

    Returns:
        bool: True if NVENC hardware encoder is available
    """
    if not IS_WINDOWS:
        return False

    try:
        # Check for nvidia-smi on Windows
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0 and len(result.stdout.strip()) > 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def has_vaapi() -> bool:
    """
    Check if VAAPI hardware encoding is available (Linux).

    Returns:
        bool: True if VAAPI device exists
    """
    if not IS_LINUX:
        return False

    # Check for VAAPI device
    return Path('/dev/dri/renderD128').exists()


def get_video_encoder_flags(quality: str = 'high') -> list:
    """
    Get platform-optimized video encoding flags for FFmpeg.

    Automatically detects and uses:
        - NVENC on Windows with NVIDIA GPU
        - VAAPI on Linux with Intel GPU
        - libx264 CPU fallback

    Args:
        quality: 'high', 'medium', or 'fast'

    Returns:
        list: FFmpeg encoding flags ready to insert into command

    Examples:
        cmd = [ffmpeg, "-i", input_file] + get_video_encoder_flags() + [output_file]
    """
    quality_presets = {
        'high': {'crf': 18, 'preset': 'slow', 'nvenc_cq': 18},
        'medium': {'crf': 23, 'preset': 'medium', 'nvenc_cq': 23},
        'fast': {'crf': 28, 'preset': 'fast', 'nvenc_cq': 28}
    }

    params = quality_presets.get(quality, quality_presets['medium'])

    # Windows: Try NVENC first
    if IS_WINDOWS and has_nvidia_gpu():
        return [
            '-c:v', 'h264_nvenc',
            '-preset', 'fast',
            '-rc', 'vbr',
            '-cq', str(params['nvenc_cq']),
            '-b:v', '0'  # VBR mode
        ]

    # Linux: Try VAAPI
    if IS_LINUX and has_vaapi():
        return [
            '-hwaccel', 'vaapi',
            '-vaapi_device', '/dev/dri/renderD128',
            '-c:v', 'h264_vaapi',
            '-qp', str(params['crf'])
        ]

    # Fallback: CPU encoding with libx264
    return [
        '-c:v', 'libx264',
        '-preset', params['preset'],
        '-crf', str(params['crf'])
    ]


def get_platform_info() -> dict:
    """
    Get detailed platform information for logging/debugging.

    Returns:
        dict: Platform details including OS, hostname, GPU status
    """
    info = {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'hostname': platform.node(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'media_root': str(get_media_root()),
        'ffmpeg_binary': get_ffmpeg_binary()
    }

    # Add GPU info
    if IS_WINDOWS:
        info['has_nvenc'] = has_nvidia_gpu()
        if info['has_nvenc']:
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                info['gpu_name'] = result.stdout.strip()
            except:
                info['gpu_name'] = 'Unknown NVIDIA GPU'
    elif IS_LINUX:
        info['has_vaapi'] = has_vaapi()

    return info


def create_temp_directory() -> Path:
    """
    Create platform-appropriate temporary directory for media processing.

    Returns:
        Path: Temp directory path
    """
    if IS_WINDOWS:
        temp_root = Path('C:/Temp/show-build-media')
    else:
        temp_root = Path('/tmp/show-build-media')

    temp_root.mkdir(parents=True, exist_ok=True)
    return temp_root


def test_media_access() -> dict:
    """
    Test access to media root and return diagnostic information.

    Returns:
        dict: Test results including accessibility and read/write status
    """
    media_root = get_media_root()

    result = {
        'media_root': str(media_root),
        'exists': media_root.exists(),
        'is_dir': media_root.is_dir() if media_root.exists() else False,
        'readable': False,
        'writable': False,
        'error': None
    }

    if result['exists'] and result['is_dir']:
        try:
            # Test read
            list(media_root.iterdir())
            result['readable'] = True

            # Test write
            test_file = media_root / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
            result['writable'] = True
        except Exception as e:
            result['error'] = str(e)

    return result


# Module-level diagnostics on import
_platform_info = get_platform_info()
_media_access = test_media_access()

# Log platform info on import (visible in Celery worker logs)
import logging
logger = logging.getLogger(__name__)

logger.info(f"Platform Utils Initialized: {_platform_info['platform']} on {_platform_info['hostname']}")
logger.info(f"Media Root: {_platform_info['media_root']} (accessible: {_media_access['exists']})")

if IS_WINDOWS and _platform_info.get('has_nvenc'):
    logger.info(f"NVENC Available: {_platform_info.get('gpu_name', 'Unknown GPU')}")
elif IS_LINUX and _platform_info.get('has_vaapi'):
    logger.info("VAAPI Hardware Acceleration Available")
else:
    logger.info("Using CPU encoding (no hardware acceleration detected)")

if not _media_access['readable']:
    logger.warning(f"⚠️  Media root not accessible: {_media_access.get('error', 'Unknown error')}")
