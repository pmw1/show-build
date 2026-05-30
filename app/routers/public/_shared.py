"""
Shared helpers for the public-API router package.

This module owns:
- The single source of truth `is_publishable()` predicate that every
  public read endpoint MUST run queries through.
- API key + permission dependencies (NOT JWT — see plan decision §AuthN).
- Tier-gating header parsing (`X-Viewer-Tier-Rank`).
- ETag computation helpers.
- Response-header injection (`X-Showbuild-Cache-Generated`,
  `X-Showbuild-Source-Updated`, `X-Showbuild-Materialized-At`).

NOTE: This is a stub scaffold. Implementations are TODO and gated
behind their respective workstreams (see ACTIVE_WORK_QUEUE.md).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import or_, func
from sqlalchemy.orm import Query, Session

from database import get_db
# Existing auth dep — accepts user JWT or api key. We'll narrow to
# api-key-only + permission check via require_api_key_with_permission
# once that's wired (see plan §Auth specifics).
from auth.utils import get_current_user_or_key


# ---------------------------------------------------------------------------
# is_publishable predicate (single source of truth)
# ---------------------------------------------------------------------------

def episode_is_publishable_q(q: Query) -> Query:
    """Apply to any Episode query to filter to publicly-visible rows.

    Filters:
      - publish_status = 'published'
      - visibility = 'public'  (editor-only intent block)
      - not test/dummy data
      - published_at <= NOW()
      - unpublished_at NULL or in the future
    """
    from models.episode import Episode

    return q.filter(
        Episode.publish_status == 'published',
        Episode.visibility == 'public',
        Episode.is_test_data == False,  # noqa: E712 — SQLAlchemy needs `==`
        Episode.is_dummy == False,      # noqa: E712
        or_(Episode.published_at == None,             # noqa: E711
            Episode.published_at <= func.now()),
        or_(Episode.unpublished_at == None,           # noqa: E711
            Episode.unpublished_at > func.now()),
    )


def segment_is_publishable_q(q: Query) -> Query:
    """Segment is publishable iff its episode is publishable AND
    rundown_items.publish_status is 'inherit' or 'published'.

    Joins via Rundown -> Episode (rundown_items.rundown_id -> rundowns.id
    -> episode_id).
    """
    from models.episode import Episode, Rundown, RundownItem

    return (
        episode_is_publishable_q(q.join(Rundown).join(Episode))
        .filter(
            RundownItem.publish_status.in_(['inherit', 'published']),
            RundownItem.is_test_data == False,  # noqa: E712
        )
    )


# ---------------------------------------------------------------------------
# Tier gating
# ---------------------------------------------------------------------------

def viewer_tier_rank(
    x_viewer_tier_rank: Optional[str] = Header(default=None),
) -> int:
    """Read `X-Viewer-Tier-Rank` header.

    Set by the website's server-side fetcher AFTER it has authenticated
    the viewer through its own identity provider. Show-build does not
    know the viewer's identity — it trusts the header because the
    request also carries an authorized API key.

    Defaults to 0 (anonymous public) when absent or malformed.
    """
    if not x_viewer_tier_rank:
        return 0
    try:
        rank = int(x_viewer_tier_rank)
        return max(0, rank)
    except (TypeError, ValueError):
        return 0


def viewer_can_access(content_tier_rank: int, viewer_rank: int) -> bool:
    """Pure helper. Used by detail endpoints to decide which fields
    redact. Listings ALWAYS show paywalled items; only detail
    redacts."""
    return viewer_rank >= content_tier_rank


# ---------------------------------------------------------------------------
# Response header injection
# ---------------------------------------------------------------------------

def attach_freshness_headers(
    request: Request,
    cache_generated: Optional[datetime] = None,
    source_updated: Optional[datetime] = None,
    materialized_at: Optional[datetime] = None,
) -> dict:
    """Returns headers dict that the endpoint includes in its Response.
    Drives the website's admin freshness widget (see plan)."""
    now = datetime.now(timezone.utc)
    return {
        'X-Showbuild-Cache-Generated': (cache_generated or now).isoformat(),
        'X-Showbuild-Source-Updated':  (source_updated or now).isoformat(),
        'X-Showbuild-Materialized-At': (materialized_at or now).isoformat(),
    }


# ---------------------------------------------------------------------------
# Slug resolver — used by every detail endpoint
# ---------------------------------------------------------------------------

def get_episode_or_404(db: Session, slug: str):
    """Resolve a slug to a publishable Episode or raise 404.

    NEVER returns an unpublishable episode, even to authenticated viewers
    on the public surface — admin-side episode access is via /api/episodes,
    not /public/v1.
    """
    from models.episode import Episode

    q = episode_is_publishable_q(db.query(Episode))
    ep = q.filter(Episode.slug == slug).first()
    if not ep:
        raise HTTPException(status_code=404, detail='episode_not_found')
    return ep


def get_segment_or_404(db: Session, slug: str, episode_slug: Optional[str] = None):
    """Resolve a segment slug to a publishable RundownItem or 404."""
    from models.episode import Episode, Rundown, RundownItem

    q = segment_is_publishable_q(db.query(RundownItem))
    q = q.filter(RundownItem.slug == slug)
    if episode_slug:
        q = q.filter(Episode.slug == episode_slug)
    seg = q.first()
    if not seg:
        raise HTTPException(status_code=404, detail='segment_not_found')
    return seg


# ---------------------------------------------------------------------------
# Auth gate — placeholder until require_api_key_with_permission lands
# ---------------------------------------------------------------------------

def require_public_read(principal=Depends(get_current_user_or_key)):
    """STUB. Today: any authenticated principal passes. TODO: narrow to
    API keys with the appropriate `public.*.read` permission per
    endpoint. See plan §Auth specifics."""
    if principal is None:
        raise HTTPException(status_code=401, detail='auth_required')
    return principal


def require_public_admin(principal=Depends(get_current_user_or_key)):
    """STUB. Will require `public.admin` permission. Today blocks
    everything until wired."""
    if principal is None:
        raise HTTPException(status_code=401, detail='auth_required')
    # TODO: check for public.admin permission
    return principal
