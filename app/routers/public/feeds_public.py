"""GET /sitemap.xml, GET /rss.xml — auto-generated discovery feeds."""
from fastapi import APIRouter, Depends, HTTPException

from ._shared import require_public_read

router = APIRouter()


@router.get('/sitemap.xml')
async def sitemap(
    _principal=Depends(require_public_read),
):
    """STUB — Phase 4."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_4')


@router.get('/rss.xml')
async def rss_feed(
    _principal=Depends(require_public_read),
):
    """STUB — Phase 4."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_4')
