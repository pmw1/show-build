"""
Public website-facing API router package — `/public/v1/*`.

READ-ONLY surface gated by API key (RBAC role: `public-reader` or
`public-surface-admin`). Never accepts JWTs. Never serves the editor
surface. See `docs/WEBSITE_PUBLIC_API_PLAN.md` for the full contract.

Defense in depth (3 layers):
1. Pydantic public schemas in `schemas/` define an explicit field
   allow-list. Never `model_dump()` an ORM row.
2. `app/services/public_asset_resolver.py` translates internal
   filesystem paths into public URLs on `media.disaffected.com`.
3. `app/tasks/public_materialize.py` materializes only public-safe
   files into `{episode}/public/`. Anything not materialized cannot
   be served regardless of API leaks.

CRITICAL: `script_content` (production script) is permanently
FORBIDDEN from this surface. Public segment text comes from
`segment_transcripts` (post-broadcast whisper + diarization).
See decision #5 in the plan.
"""
from fastapi import APIRouter

from .episodes_public import router as episodes_router
from .segments_public import router as segments_router
from .transcripts_public import router as transcripts_router
from .thumbnails_public import router as thumbnails_router
from .tags_public import router as tags_router
from .feeds_public import router as feeds_router
from .access_tiers_public import router as access_tiers_router
from .admin_public import router as admin_router

# Single mount point. All sub-routers live under /public/v1.
router = APIRouter(prefix="/public/v1", tags=["public"])

router.include_router(episodes_router)
router.include_router(segments_router)
router.include_router(transcripts_router)
router.include_router(thumbnails_router)
router.include_router(tags_router)
router.include_router(feeds_router)
router.include_router(access_tiers_router)
router.include_router(admin_router)
