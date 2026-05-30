"""GET /segments/{slug} — segment detail (independently URL-addressable).

Tier-aware. `script_content` NEVER appears in responses (decision #5).
Public segment text comes from segment_transcripts.
"""
from fastapi import APIRouter, Depends, HTTPException

from ._shared import require_public_read, viewer_tier_rank

router = APIRouter()


@router.get('/segments/{slug}')
async def get_segment(
    slug: str,
    _principal=Depends(require_public_read),
    _viewer_rank: int = Depends(viewer_tier_rank),
    include: str | None = None,
):
    """STUB — returns 501 until implemented. See plan §Phase 2."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_2')


@router.get('/segments/{slug}/related')
async def list_related_segments(
    slug: str,
    _principal=Depends(require_public_read),
    _viewer_rank: int = Depends(viewer_tier_rank),
    limit: int = 5,
):
    """STUB — Tier 2. Tag-overlap scoring per plan."""
    raise HTTPException(status_code=501, detail='not_implemented_tier_2')
