"""Phase 2 Meta Extraction — Async Grok enrichment over Phase 1 output.

Phase 1 (segment_llm_extractor) is a synchronous, single-pass call to a
local Ollama model. It is fast and free but its training data ages, so
roles drift ("former president" for Trump in 2026), social handles outside
top-tier celebrity recall come back null, and recent activity is invisible.

Phase 2 takes the Phase 1 row + the segment script, and asks Grok
(api.x.ai/v1) to:
  - verify each entity's *current* role/title
  - resolve social handles across X / Bluesky / Facebook / Instagram /
    YouTube / TikTok / Mastodon / Threads
  - refine the relation-to-story (more detail, current framing)
  - generate a short (≤2-sentence) bio per person, "what we do" per
    organization/institution, plus founders / founded-when
  - add pronunciation guides, Wikipedia + image URLs
  - flag conflicts of interest with this story
  - emit segment-level extras: timeline, fact-check flags, counter-narrative,
    suggested hashtags, and which entities are currently trending on X

All output writes to segment_llm_data.phase2_data (JSONB) without
touching Phase 1 columns. Status / model / timing / errors / Celery task
id live in dedicated columns.
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from celery import shared_task
from sqlalchemy import text
from sqlalchemy.orm import Session

# Import for its side effect: celery_app.set_default(), so the shared_task
# below binds to the configured broker instead of an unconfigured default app.
import celery_app  # noqa: F401

from database import SessionLocal
from models_segment_llm import SegmentLLMData
from models_v2 import RundownItem
from api_config import api_config_manager
from services.social_media import (
    fetch_x_user_by_username,
    get_twitter_oauth_credentials,
)

logger = logging.getLogger(__name__)


PHASE2_SYSTEM_PROMPT = """You are an expert broadcast-journalism research assistant for the Disaffected media show.

CURRENT DATE: {today}. This is the production date of the show. Whenever you say "current", "now", "today", or describe a present-tense role, you MUST anchor that to {today}, not to your training cutoff. If your training data conflicts with what's true on {today}, USE LIVE SEARCH to verify and trust the live-search result. Do not call current officeholders "former". Do not call current candidates "candidates" if the election they ran in has already happened.

You receive (1) the full text of a single segment and (2) the entities a smaller offline LLM extracted from it. The offline model's training data is even older than yours and CONSERVATIVE — it returns null for handles it isn't sure about and may give stale roles.

Your job is to produce a verified, current, enriched version of that entity list, plus a few segment-level artifacts. USE LIVE SEARCH (web + X) aggressively for any role/title field, social handle, recent activity, or current-leadership entry. Be precise. When even live search can't confirm a value, return null rather than guessing — fabricated handles and bios are worse than nulls.

Return STRICT JSON only. No markdown, no explanations. CRITICAL: Do not embed citation tags, footnote markers, or any reference annotations inside string values. The JSON must be plain text — no `<grok:render>` tags, no `[[1]](url)` markdown citations, no `[citation: ...]` brackets, nothing extra. If you used live search, the citations are already tracked separately by the platform; do not duplicate them in the JSON output."""


PHASE2_USER_PROMPT = """TODAY IS {today}. All "current" claims must be true as of this date.

SEGMENT TITLE: {segment_title}
EPISODE: {episode_number}

------- FULL SEGMENT TEXT -------
{content}
------- END SEGMENT TEXT -------

------- PHASE 1 ENTITIES (from offline LLM, possibly stale/incomplete) -------
{phase1_entities_json}
------- END PHASE 1 ENTITIES -------

Return JSON in this exact shape:

{{
  "people": [
    {{
      "name": "...",
      "current_role_verified": "Most accurate current title/role as of today, e.g. 'President of the United States' not 'former President'",
      "pronunciation": "Phonetic guide if non-obvious, else null",
      "bio_short": "1-2 sentence bio. Null if unknown.",
      "wikipedia_url": "Full https URL or null",
      "image_url": "Direct image URL (Wikipedia thumbnail preferred) or null",
      "social_handles": {{
        "x": "@handle or null",
        "bluesky": "handle.bsky.social or null",
        "facebook": "username or null",
        "instagram": "@handle or null",
        "youtube": "@channel or null",
        "tiktok": "@handle or null",
        "mastodon": "@handle@instance or null",
        "threads": "@handle or null"
      }},
      "recent_activity": [
        {{"date": "YYYY-MM-DD", "event": "What they did/said", "source_url": "https://... or null"}}
      ],
      "conflicts_with_story": "If this person has a stake or COI in the segment's topic, describe it. Else null.",
      "relation_to_story_refined": "Updated, more detailed framing of how they fit this story"
    }}
  ],
  "organizations": [
    {{
      "name": "...",
      "current_role_verified": "Brief description of what they currently do",
      "what_we_do": "1-2 sentence 'what we do' summary",
      "founded_year": 1234,
      "founders": ["Name1", "Name2"],
      "headquarters": "City, Country or null",
      "current_leadership": [{{"name": "...", "title": "..."}}],
      "parent_org": "Name of parent/owner or null",
      "wikipedia_url": "...",
      "logo_url": "...",
      "social_handles": {{ "x": "...", "bluesky": "...", "facebook": "...", "instagram": "...", "youtube": "...", "tiktok": "..." }},
      "recent_activity": [{{"date": "YYYY-MM-DD", "event": "...", "source_url": "..."}}],
      "conflicts_with_story": "...",
      "relation_to_story_refined": "..."
    }}
  ],
  "institutions": [
    {{
      "name": "...",
      "current_role_verified": "...",
      "what_we_do": "...",
      "founded_year": 1234,
      "jurisdiction": "Federal/State/County/etc, or N/A",
      "current_head": {{"name": "...", "title": "..."}},
      "headquarters": "...",
      "wikipedia_url": "...",
      "logo_url": "...",
      "social_handles": {{ "x": "...", "bluesky": "...", "facebook": "...", "instagram": "...", "youtube": "..." }},
      "recent_activity": [{{"date": "YYYY-MM-DD", "event": "...", "source_url": "..."}}],
      "relation_to_story_refined": "..."
    }}
  ],
  "segment_extras": {{
    "timeline": [
      {{"date": "YYYY-MM-DD", "fact": "Dated fact relevant to this segment", "source_url": "..."}}
    ],
    "fact_check_flags": [
      {{"claim": "Claim made in segment", "status": "disputed|unverified|misleading|accurate", "dispute_source_url": "..."}}
    ],
    "counter_narrative": "Strongest opposing framing of this story, with attribution if possible. Null if not applicable.",
    "suggested_hashtags": ["#Tag1", "#Tag2"],
    "trending_entities": ["Names of entities from above currently trending on X, or empty array"]
  }}
}}

Rules:
- Match every name in phase1 entities exactly (case-sensitive). Don't drop entities; if you can't verify one, still return it with the fields you can confirm and null elsewhere.
- Don't invent entities not in phase1. If the segment mentions someone phase1 missed, you may add them but mark `"name": "...", "added_by_phase2": true`.
- Recent activity: cap at 5 entries per entity, sorted newest first, last 90 days only.
- bio_short / what_we_do: max 2 sentences. Hard limit.
- All URLs must start with `https://`. Otherwise return null.
- Return ONLY the JSON object. Nothing before, nothing after."""


def _get_grok_config() -> Dict[str, str]:
    """Pull Grok credentials + endpoint from api_configs (decrypted)."""
    config = api_config_manager.load_config()
    grok = (
        config.get("preproduction", {})
        .get("ai_services", {})
        .get("grok", {})
    )
    api_key = grok.get("apiKey") or grok.get("api_key")
    base_url = grok.get("baseUrl") or grok.get("base_url") or "https://api.x.ai/v1"
    model = grok.get("model") or "grok-4-latest"

    if not api_key:
        raise RuntimeError(
            "Grok API key not configured (preproduction.ai_services.grok.apiKey)"
        )
    return {"api_key": api_key, "base_url": base_url.rstrip("/"), "model": model}


def _build_phase1_entities_payload(llm_row: SegmentLLMData) -> Dict[str, Any]:
    """Compact view of Phase 1 entities for inclusion in the Grok prompt."""
    return {
        "people": llm_row.extracted_people or [],
        "organizations": llm_row.extracted_organizations or [],
        "institutions": llm_row.extracted_institutions or [],
    }


def _call_grok(
    api_key: str,
    base_url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Single Grok call against the new /v1/responses Agent Tools API.

    The legacy /v1/chat/completions + search_parameters / live_search route
    was deprecated by xAI in 2026Q1. We now hit /v1/responses with `tools:
    [{"type":"web_search"}, {"type":"x_search"}]` so Grok can verify
    current roles, recent activity, and trending state against the web + X
    in real time — sidestepping its training cutoff (which predates the
    Nov-2024 election and Jan-2025 inauguration).

    Response shape:
        {"output": [
            {"type":"web_search_call", ...},   # search bookkeeping
            {"type":"message", "content":[
                {"type":"output_text", "text":"...JSON...", "annotations":[citations]}
            ]}
        ]}
    """
    url = f"{base_url}/responses"
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "tools": [
            {"type": "web_search"},
            {"type": "x_search"},
        ],
        # Cap tool calls so a single run can't snowball into an open-ended
        # search session. 20 is enough for ~25 entities (one search per
        # entity for handle verification, plus a few segment-level
        # searches).
        "max_tool_calls": 20,
        "temperature": 0.2,
        "text": {"format": {"type": "json_object"}},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # Granular timeouts. The xAI server keeps the connection alive while
    # reasoning + searching, so a single big read timeout could wait
    # forever; explicit per-stage timeouts give us a real wall-clock cap.
    timeout = httpx.Timeout(connect=15.0, read=240.0, write=30.0, pool=10.0)
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            body_excerpt = (resp.text or "").strip()[:600]
            raise RuntimeError(
                f"Grok API {resp.status_code} {resp.reason_phrase}: {body_excerpt or '(empty body)'}"
            )
        data = resp.json()

    # Walk the new response shape to find the assistant message text.
    for item in data.get("output", []):
        if item.get("type") == "message":
            for block in item.get("content", []):
                if block.get("type") in ("output_text", "text"):
                    return block.get("text", "")
    raise RuntimeError(
        f"Grok /v1/responses returned no message content; raw output: {json.dumps(data)[:500]}"
    )


# Grok's tools-API output embeds inline citation tags inside JSON string
# values, e.g. `"role":"President<grok:render type=\"render_inline_citation\">
# <argument name=\"citation_id\">2</argument></grok:render>"`. Strip them
# so json.loads() (and the rendered UI) don't choke on them.
_CITATION_TAG_RE = re.compile(
    r"<grok:render\b[^>]*>.*?</grok:render>",
    flags=re.DOTALL | re.IGNORECASE,
)
# Markdown-style inline citations sometimes appear too: `[[1]](https://...)`.
_MD_CITATION_RE = re.compile(r"\[\[\d+\]\]\([^)]+\)")


def _parse_phase2_response(raw: str) -> Dict[str, Any]:
    """Parse Grok response, tolerate stray code-fences and inline citations."""
    txt = raw.strip()
    if txt.startswith("```"):
        # strip ```json ... ``` or ``` ... ```
        first_nl = txt.find("\n")
        if first_nl >= 0:
            txt = txt[first_nl + 1:]
        if txt.endswith("```"):
            txt = txt[: -3]
        txt = txt.strip()

    # Strip citation pollution before parsing.
    txt = _CITATION_TAG_RE.sub("", txt)
    txt = _MD_CITATION_RE.sub("", txt)
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        # last resort: extract outermost JSON object
        start = txt.find("{")
        end = txt.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(txt[start:end])
        raise


def _verify_x_handles(db: Session, phase2_payload: Dict[str, Any]) -> None:
    """Verify Grok-suggested X handles against the X API and merge profile data.

    Mutates `phase2_payload` in place. For every entity in `people`,
    `organizations`, or `institutions` that has a non-empty `social_handles.x`,
    we call api.x.com/2/users/by/username/{handle}. Result lands on the
    entity as:
        x_verified: bool
        x_profile: { id, name, username, description, profile_image_url,
                     verified, public_metrics, location, url, created_at }
                   — present only when verified == True

    Each handle is looked up at most once per call (cached locally) so
    repeated names across entity types don't burn rate-limit headroom.
    Falls back silently when creds are missing — Phase 2 still completes
    with Grok-only data.
    """
    creds = get_twitter_oauth_credentials(db)
    if not creds:
        logger.info("Skipping X handle verification — Twitter OAuth creds not configured")
        return

    seen: Dict[str, Optional[Dict[str, Any]]] = {}

    def _lookup(handle: str) -> Optional[Dict[str, Any]]:
        key = handle.lstrip('@').strip().lower()
        if not key:
            return None
        if key in seen:
            return seen[key]
        result = fetch_x_user_by_username(key, creds)
        seen[key] = result
        return result

    for bucket in ('people', 'organizations', 'institutions'):
        entries = phase2_payload.get(bucket) or []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            handles = entry.get('social_handles') or {}
            x_handle = handles.get('x')
            if not x_handle or x_handle in (None, '', 'null'):
                entry['x_verified'] = False
                continue
            profile = _lookup(str(x_handle))
            if profile:
                entry['x_verified'] = True
                entry['x_profile'] = profile
                # Normalize the handle to whatever X reports (case-correct,
                # leading @ stripped).
                entry['social_handles']['x'] = f"@{profile.get('username')}"
            else:
                entry['x_verified'] = False


def run_phase2_enrichment(db: Session, rundown_item_id: int) -> SegmentLLMData:
    """Synchronous core. Celery task wraps this with its own session."""
    llm_row = (
        db.query(SegmentLLMData)
        .filter(SegmentLLMData.rundown_item_id == rundown_item_id)
        .first()
    )
    if not llm_row:
        raise ValueError(
            f"No Phase 1 segment_llm_data row for rundown_item_id={rundown_item_id} — run Phase 1 first."
        )

    rundown_item = (
        db.query(RundownItem).filter(RundownItem.id == rundown_item_id).first()
    )
    if not rundown_item:
        raise ValueError(f"Rundown item {rundown_item_id} not found")

    cfg = _get_grok_config()

    # Mark running
    llm_row.phase2_status = "running"
    llm_row.phase2_started_at = datetime.now(timezone.utc)
    llm_row.phase2_model = cfg["model"]
    llm_row.phase2_error = None
    db.commit()

    try:
        episode_number = ""
        if rundown_item.rundown and rundown_item.rundown.episode:
            episode_number = str(rundown_item.rundown.episode.episode_number or "")

        today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        user_prompt = PHASE2_USER_PROMPT.format(
            today=today_iso,
            segment_title=rundown_item.title or "",
            episode_number=episode_number,
            content=rundown_item.script_content or "",
            phase1_entities_json=json.dumps(
                _build_phase1_entities_payload(llm_row), ensure_ascii=False
            ),
        )
        system_prompt = PHASE2_SYSTEM_PROMPT.format(today=today_iso)

        raw = _call_grok(
            cfg["api_key"],
            cfg["base_url"],
            cfg["model"],
            system_prompt,
            user_prompt,
        )
        parsed = _parse_phase2_response(raw)

        # Verify Grok-suggested X handles against the actual X API and
        # merge the authoritative profile back into phase2_data. Failures
        # here are non-fatal — the Grok payload is still useful even if
        # the X API is rate-limited or down.
        try:
            _verify_x_handles(db, parsed)
        except Exception as verify_exc:  # noqa: BLE001
            logger.warning("X handle verification step failed: %s", verify_exc)

        # Persist
        llm_row.phase2_data = parsed
        llm_row.phase2_status = "completed"
        llm_row.phase2_completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(llm_row)
        logger.info(
            "Phase 2 enrichment complete for rundown_item_id=%s (model=%s)",
            rundown_item_id, cfg["model"],
        )
        return llm_row

    except Exception as exc:  # noqa: BLE001
        logger.exception("Phase 2 enrichment failed for rundown_item_id=%s", rundown_item_id)
        llm_row.phase2_status = "failed"
        llm_row.phase2_error = str(exc)[:2000]
        llm_row.phase2_completed_at = datetime.now(timezone.utc)
        db.commit()
        raise


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

@shared_task(name="services.phase2_enrichment_service.run_phase2_enrichment")
def run_phase2_enrichment_task(rundown_item_id: int) -> Dict[str, Any]:
    """Celery entry point. Owns its own DB session."""
    db = SessionLocal()
    try:
        row = run_phase2_enrichment(db, rundown_item_id)
        return {
            "rundown_item_id": rundown_item_id,
            "status": row.phase2_status,
            "completed_at": row.phase2_completed_at.isoformat() if row.phase2_completed_at else None,
        }
    finally:
        db.close()


def queue_phase2_enrichment(db: Session, rundown_item_id: int) -> str:
    """Mark the row as queued and dispatch the Celery task. Returns task id."""
    llm_row = (
        db.query(SegmentLLMData)
        .filter(SegmentLLMData.rundown_item_id == rundown_item_id)
        .first()
    )
    if not llm_row:
        raise ValueError(
            f"No Phase 1 row for rundown_item_id={rundown_item_id} — run Phase 1 first."
        )

    async_result = run_phase2_enrichment_task.apply_async(args=[rundown_item_id])
    llm_row.phase2_status = "queued"
    llm_row.phase2_task_id = async_result.id
    llm_row.phase2_error = None
    llm_row.phase2_started_at = None
    llm_row.phase2_completed_at = None
    db.commit()
    return async_result.id
