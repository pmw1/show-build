"""GET /segments/{slug}/transcript — post-broadcast diarized transcript.

Source: segment_transcripts table (whisper-medium + pyannote).
NEVER `script_content`. Tier-gated.
"""
from fastapi import APIRouter, Depends, HTTPException

from ._shared import require_public_read, viewer_tier_rank

router = APIRouter()


@router.get('/segments/{slug}/transcript')
async def get_transcript_json(
    slug: str,
    _principal=Depends(require_public_read),
    _viewer_rank: int = Depends(viewer_tier_rank),
    language: str = 'en',
):
    """STUB. Returns the transcript envelope (text_plain + optional
    diarized JSON). Format-specific endpoints below."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_3')


@router.get('/segments/{slug}/transcript.vtt')
async def get_transcript_vtt(
    slug: str,
    _principal=Depends(require_public_read),
    _viewer_rank: int = Depends(viewer_tier_rank),
    language: str = 'en',
):
    """STUB. Returns raw VTT, Content-Type: text/vtt."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_3')


@router.get('/segments/{slug}/transcript.srt')
async def get_transcript_srt(
    slug: str,
    _principal=Depends(require_public_read),
    _viewer_rank: int = Depends(viewer_tier_rank),
    language: str = 'en',
):
    """STUB. Returns raw SRT, Content-Type: text/srt."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_3')
