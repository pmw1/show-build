"""GET /tags, GET /tags/{slug} — tag index + landing pages.

For v1: tags are CSV strings on episodes/rundown_items, parsed at query
time. Tag normalization deferred to a separate g016 migration.
"""
from fastapi import APIRouter, Depends, HTTPException

from ._shared import require_public_read

router = APIRouter()


@router.get('/tags')
async def list_tags(
    _principal=Depends(require_public_read),
):
    """STUB — Phase 4."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_4')


@router.get('/tags/{slug}')
async def get_tag_detail(
    slug: str,
    _principal=Depends(require_public_read),
):
    """STUB — Phase 4."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_4')
