"""Admin endpoints under /public/v1/_admin/*.

Separate permission (`public.admin`), separate API key from the
read-only `public-reader` consumer key. Drives the website-side admin
freshness widget.
"""
from fastapi import APIRouter, Depends, HTTPException

from ._shared import require_public_admin

router = APIRouter()


@router.get('/_admin/freshness')
async def admin_freshness(
    slug: str,
    _principal=Depends(require_public_admin),
):
    """STUB. Returns the three freshness timestamps + queue state."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_6')


@router.post('/_admin/purge', status_code=202)
async def admin_purge(
    slug: str,
    _principal=Depends(require_public_admin),
):
    """STUB. Purges API CDN + Redis cache for the slug. Does NOT
    re-materialize."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_6')


@router.post('/_admin/rematerialize', status_code=202)
async def admin_rematerialize(
    slug: str,
    _principal=Depends(require_public_admin),
):
    """STUB. Re-runs public.materialize_episode + generate_poster_variants
    + invalidate_caches."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_6')
