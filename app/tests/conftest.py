"""
Pytest fixtures for SOT processing tests.

Provides mocks for database, FFmpeg, Whisper, and filesystem operations.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import tempfile
import shutil


@pytest.fixture
def mock_db_session():
    """Mock database session context manager."""
    mock_session = MagicMock()

    # Create a context manager that yields the mock session
    class MockContextManager:
        def __enter__(self):
            return mock_session

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    with patch('services.ffmpeg_tasks.db_session', return_value=MockContextManager()):
        yield mock_session


@pytest.fixture
def mock_ffmpeg():
    """Mock subprocess.run for FFmpeg/FFprobe commands."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = b"30.0"  # Default duration output
    mock_result.stderr = b""

    with patch('subprocess.run', return_value=mock_result) as mock_run:
        yield mock_run


@pytest.fixture
def mock_ffmpeg_with_error():
    """Mock subprocess.run that simulates FFmpeg failure."""
    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stdout = b""
    mock_result.stderr = b"FFmpeg error: invalid input"

    with patch('subprocess.run', return_value=mock_result) as mock_run:
        yield mock_run


@pytest.fixture
def mock_whisper():
    """Mock transcribe_audio_simple function."""
    with patch('services.ffmpeg_tasks.transcribe_audio_simple') as mock:
        mock.return_value = "This is a test transcription for the video clip."
        yield mock


@pytest.fixture
def mock_whisper_failure():
    """Mock transcribe_audio_simple that raises an exception."""
    with patch('services.ffmpeg_tasks.transcribe_audio_simple') as mock:
        mock.side_effect = Exception("Whisper server unavailable")
        yield mock


@pytest.fixture
def mock_derive_outcue():
    """Mock derive_outcue function."""
    with patch('services.ffmpeg_tasks.derive_outcue') as mock:
        mock.return_value = "...for the video clip."
        yield mock


@pytest.fixture
def temp_working_dir():
    """Create a temporary working directory with a dummy upload file."""
    temp_dir = tempfile.mkdtemp(prefix="sot_test_")
    working_dir = Path(temp_dir)

    # Create a dummy upload file (just an empty file for path testing)
    upload_file = working_dir / "test_job_upload.mp4"
    upload_file.write_bytes(b"dummy video content for testing")

    yield working_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_clips():
    """Standard 3-clip test data."""
    return [
        {
            "slug": "clip-1-intro",
            "time_start": "00:00:05:00",
            "time_end": "00:00:15:00"
        },
        {
            "slug": "clip-2-main",
            "time_start": "00:00:30:00",
            "time_end": "00:01:00:00"
        },
        {
            "slug": "clip-3-outro",
            "time_start": "00:02:00:00",
            "time_end": "00:02:30:00"
        }
    ]


@pytest.fixture
def sample_clips_with_invalid():
    """Test data including an invalid clip (end before start)."""
    return [
        {
            "slug": "clip-1-valid",
            "time_start": "00:00:05:00",
            "time_end": "00:00:15:00"
        },
        {
            "slug": "clip-2-invalid",
            "time_start": "00:00:30:00",
            "time_end": "00:00:20:00"  # End before start - invalid
        },
        {
            "slug": "clip-3-valid",
            "time_start": "00:01:00:00",
            "time_end": "00:01:30:00"
        }
    ]


@pytest.fixture
def mock_platform_utils():
    """Mock platform_utils functions for cross-platform testing."""
    with patch('services.ffmpeg_tasks.get_ffmpeg_binary', return_value='ffmpeg'), \
         patch('services.ffmpeg_tasks.get_ffprobe_binary', return_value='ffprobe'), \
         patch('services.ffmpeg_tasks.get_media_root', return_value=Path('/mnt/sync/disaffected')), \
         patch('platform_utils.IS_WINDOWS', False), \
         patch('platform_utils.has_nvidia_gpu', return_value=False):
        yield


@pytest.fixture
def mock_asset_id_generator():
    """Mock _generate_asset_id to return predictable values."""
    call_count = [0]

    def generate_id():
        call_count[0] += 1
        return f"TEST-ASSET-{call_count[0]:04d}"

    with patch('services.ffmpeg_tasks._generate_asset_id', side_effect=generate_id):
        yield call_count


@pytest.fixture
def mock_update_job_status():
    """Mock _update_job_status to track status updates."""
    status_history = []

    def record_status(job_id, phase, status, error=None):
        status_history.append({
            'job_id': job_id,
            'phase': phase,
            'status': status,
            'error': error
        })

    with patch('services.ffmpeg_tasks._update_job_status', side_effect=record_status):
        yield status_history


@pytest.fixture
def mock_insert_cue_blocks():
    """Mock _insert_multiple_cue_blocks to track insertions."""
    insertions = []

    def record_insertion(episode, clip_results, parent_asset_id):
        insertions.append({
            'episode': episode,
            'clip_results': clip_results,
            'parent_asset_id': parent_asset_id
        })

    with patch('services.ffmpeg_tasks._insert_multiple_cue_blocks', side_effect=record_insertion):
        yield insertions


@pytest.fixture
def mock_update_cue_block():
    """Mock _update_cue_block_with_result to track updates."""
    updates = []

    def record_update(episode, asset_id, result):
        updates.append({
            'episode': episode,
            'asset_id': asset_id,
            'result': result
        })

    with patch('services.ffmpeg_tasks._update_cue_block_with_result', side_effect=record_update):
        yield updates


@pytest.fixture
def mock_shutil_move():
    """Mock shutil.move to track file movements."""
    moves = []

    def record_move(src, dst):
        moves.append({'src': src, 'dst': dst})

    with patch('shutil.move', side_effect=record_move):
        yield moves
