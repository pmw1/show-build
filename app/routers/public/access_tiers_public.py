"""GET /access-tiers — canonical tier registry.

Drives both the website's content gate and the Discord chat gate.
Show-build is the single source of truth for tier slugs/names/ranks
across the platform.
"""
from fastapi import APIRouter, Depends, HTTPException

from ._shared import require_public_read

router = APIRouter()


@router.get('/access-tiers')
async def list_access_tiers(
    _principal=Depends(require_public_read),
):
    """STUB — returns the access_tiers table. Public list.
    See plan §Tier gating."""
    raise HTTPException(status_code=501, detail='not_implemented_phase_2')
