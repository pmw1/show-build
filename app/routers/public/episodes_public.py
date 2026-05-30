"""GET /episodes (list), GET /episodes/{slug} (detail).

Tier-aware. Listings always show paywalled episodes (with `requires_tier`).
Detail redacts gated fields when viewer rank < required.
"""
from fastapi import APIRouter, Depends, HTTPException

from ._shared import require_public_read, viewer_tier_rank

router = APIRouter()


@router.get('/episodes')
async def list_episodes(
    _principal=Depends(require_public_read),
    _viewer_rank: int = Depends(viewer_tier_rank),
    cursor: str | None = None,
    limit: int = 20,
):
    """STUB — returns 501 until implemented. See plan §Phase 2."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_2')


@router.get('/episodes/{slug}')
async def get_episode(
    slug: str,
    _principal=Depends(require_public_read),
    _viewer_rank: int = Depends(viewer_tier_rank),
    include: str | None = None,
):
    """STUB — returns 501 until implemented. See plan §Phase 2."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_2')


@router.get('/episodes/{slug}/segments')
async def list_segments_for_episode(
    slug: str,
    _principal=Depends(require_public_read),
    _viewer_rank: int = Depends(viewer_tier_rank),
):
    """STUB — returns 501 until implemented. See plan §Phase 2."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_2')
