"""
LLM slug generation for rundown-item segments.

Generates a short, broadcast-friendly slug (2-4 words, prefer 2-3) from a
segment's title + script body. Follows the canonical generation pipeline:
- model/host/temperature resolved from api_configs (workflow 'generation',
  service 'segment_slug', falling back to global ollama config),
- the shared call_ollama() + render/context/history helpers from
  auto_description_service,
- the {field}_gen_history pattern (slug_gen_history) + llm_generated_fields.

Trigger rules (see sweep + generate_slug):
- slug is empty  -> generate from title + body.
- slug has >= 5 words -> SHORTEN: the prompt includes the existing long slug so
  the model produces a shorter broadcast slug.
A user's valid 1-4 word slug is never auto-overwritten.
"""

import re
import json
import logging
from datetime import datetime

from sqlalchemy import text
from celery import shared_task
from database import SessionLocal

# Reuse the canonical pipeline pieces — do NOT reimplement the LLM call / config.
from services.auto_description_service import (
    call_ollama,
    load_segment_context,
    update_segment_fields,
    add_llm_generated_field,
    send_llm_notification,
    get_ollama_host,
    get_ollama_model,
    get_ollama_fallback_model,
    get_generation_temperature,
)

logger = logging.getLogger(__name__)

MAX_SLUG_WORDS = 4
LONG_SLUG_TRIGGER_WORDS = 5  # a user slug this long (or longer) triggers shortening

DEFAULT_SLUG_PROMPT = (
    "You are naming a broadcast segment with a short slug for a rundown.\n\n"
    "Show: {{show_name}}\n"
    "Segment title: {{segment_title}}\n"
    "{% if has_long_slug %}The current slug is too long for broadcast: \"{{long_slug}}\"\n"
    "Generate a SHORTER replacement.\n{% endif %}"
    "Segment content:\n{{segment_content}}\n\n"
    "Write a slug that:\n"
    "- is 2 to 4 words MAX (prefer 2 or 3 words),\n"
    "- captures the core topic of the segment,\n"
    "- is broadcast-friendly and easy to say,\n"
    "- contains no punctuation other than spaces between words.\n\n"
    "Output ONLY the slug words, nothing else. No quotes, no preamble, no explanation.\n"
    "/no_think"
)


def _slugify(raw: str) -> str:
    """Normalize the model's output into a clean lowercase, hyphen-joined slug
    of at most MAX_SLUG_WORDS words (matches the frontend slug rules)."""
    if not raw:
        return ""
    s = raw
    # Strip <think>...</think> reasoning blocks (qwen3 etc.) before parsing.
    s = re.sub(r"<think>.*?</think>", " ", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"</?think>", " ", s, flags=re.IGNORECASE)
    s = s.strip().strip('"').strip("'")
    if not s:
        return ""
    # Take the last non-empty line (the answer usually follows any reasoning).
    lines = [ln for ln in s.splitlines() if ln.strip()]
    s = lines[-1] if lines else ""
    # Drop anything that isn't a word char or separator.
    s = re.sub(r"[^A-Za-z0-9\s\-_]", " ", s)
    words = [w for w in re.split(r"[\s\-_]+", s) if w]
    words = words[:MAX_SLUG_WORDS]
    return "-".join(w.lower() for w in words)


def _word_count(slug: str) -> int:
    if not slug:
        return 0
    return len([w for w in re.split(r"[\s\-_]+", slug) if w])


def get_slug_prompt_template(db) -> str:
    """Prompt override from prompt_overrides (category 'generate', operation_key
    'slug-generator' — the key surfaced in the Settings PromptManager / the
    frontend PROMPTS registry), else the built-in default."""
    try:
        row = db.execute(text(
            "SELECT user_prompt_template FROM prompt_overrides "
            "WHERE category = 'generate' AND operation_key = 'slug-generator' "
            "AND is_enabled = true LIMIT 1"
        )).fetchone()
        if row and row[0]:
            return row[0]
    except Exception:
        pass
    return DEFAULT_SLUG_PROMPT


def _build_slug_variables(ctx: dict) -> dict:
    long_slug = ctx.get("slug") or ""
    has_long = _word_count(long_slug) >= LONG_SLUG_TRIGGER_WORDS
    return {
        "show_name": ctx.get("show_name", "Disaffected"),
        "segment_title": ctx.get("title", "") or "",
        "segment_content": (ctx.get("script_content", "") or "")[:4000],
        "has_long_slug": has_long,
        "long_slug": long_slug,
    }


# ---------------------------------------------------------------------------
# History helpers (field-specific, per the LLM Generation History Pattern)
# ---------------------------------------------------------------------------

def append_slug_history(db, asset_id, role, text_content):
    row = db.execute(text(
        "SELECT slug_gen_history FROM rundown_items WHERE asset_id = :aid"
    ), {"aid": asset_id}).fetchone()
    history = row[0] if row and row[0] else []
    history.append({"role": role, "text": text_content,
                    "ts": datetime.utcnow().isoformat() + "Z"})
    db.execute(text(
        "UPDATE rundown_items SET slug_gen_history = :val WHERE asset_id = :aid"
    ), {"aid": asset_id, "val": json.dumps(history)})
    db.commit()


def get_slug_history(db, asset_id):
    row = db.execute(text(
        "SELECT slug_gen_history FROM rundown_items WHERE asset_id = :aid"
    ), {"aid": asset_id}).fetchone()
    return (row[0] if row and row[0] else [])


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

def _render(template, variables):
    # Reuse the same simple renderer the description service uses.
    from services.auto_description_service import render_template
    return render_template(template, variables)


def _generate_slug_core(db, asset_id) -> str:
    ctx = load_segment_context(db, asset_id)
    if not ctx:
        raise ValueError(f"Segment {asset_id} not found")

    host = get_ollama_host(db)
    model = get_ollama_model(db, purpose='generator')
    fallback = get_ollama_fallback_model(db, purpose='generator')
    template = get_slug_prompt_template(db)
    variables = _build_slug_variables(ctx)
    prompt = _render(template, variables)
    temp = get_generation_temperature(db, 'segment_slug', 0.3)

    raw = call_ollama(host, model, prompt, temperature=temp, max_tokens=500, fallback_model=fallback)
    slug = _slugify(raw)

    if not slug:
        raise ValueError("Model returned an empty slug")

    update_segment_fields(db, asset_id, {'slug': slug})
    add_llm_generated_field(db, asset_id, 'slug')
    append_slug_history(db, asset_id, 'llm', slug)
    return slug


@shared_task(name="services.slug_gen_service.generate_slug")
def generate_slug(asset_id: str) -> dict:
    """First-pass slug generation. Used by the sweep and the manual button."""
    db = SessionLocal()
    try:
        ctx = load_segment_context(db, asset_id)
        slug = _generate_slug_core(db, asset_id)
        logger.info(f"[slug] Generated for {asset_id}: {slug}")
        try:
            send_llm_notification(db, 'segment_slug', asset_id,
                                  (ctx or {}).get('title'), (ctx or {}).get('episode_number'),
                                  'success', f"Slug: {slug}")
        except Exception:
            pass
        return {'slug': slug}
    except Exception as e:
        logger.error(f"[slug] generate failed for {asset_id}: {e}")
        return {'error': str(e)}
    finally:
        db.close()


def regenerate_slug(asset_id: str, previous_slug: str = "", feedback: str = "") -> dict:
    """Regenerate the slug incorporating the full history + the user's feedback.
    Runs inline (request-level) so the button gets the new slug back directly."""
    db = SessionLocal()
    try:
        ctx = load_segment_context(db, asset_id)
        if not ctx:
            raise ValueError(f"Segment {asset_id} not found")

        host = get_ollama_host(db)
        model = get_ollama_model(db, purpose='generator')
        fallback = get_ollama_fallback_model(db, purpose='generator')
        template = get_slug_prompt_template(db)
        variables = _build_slug_variables(ctx)
        base = _render(template, variables)

        history = get_slug_history(db, asset_id)
        history_block = ""
        if history:
            history_block = "\n--- GENERATION HISTORY ---\n"
            for entry in history:
                label = "LLM generated" if entry.get('role') == 'llm' else "User feedback"
                history_block += f"[{label}]: {entry.get('text', '')}\n"

        regen_prompt = (
            f"{base}\n\n{history_block}\n"
            f"The current slug is: \"{previous_slug}\"\n"
            f"The user wants changes. Their feedback: \"{feedback}\"\n\n"
            f"Write a NEW slug (2-4 words, prefer 2-3) addressing all the feedback above. "
            f"Output ONLY the slug words, nothing else."
        )

        temp = get_generation_temperature(db, 'segment_slug', 0.3)
        raw = call_ollama(host, model, regen_prompt, temperature=temp, max_tokens=500, fallback_model=fallback)
        slug = _slugify(raw)
        if not slug:
            raise ValueError("Model returned an empty slug")

        append_slug_history(db, asset_id, 'user', feedback)
        append_slug_history(db, asset_id, 'llm', slug)
        update_segment_fields(db, asset_id, {'slug': slug})
        add_llm_generated_field(db, asset_id, 'slug')

        logger.info(f"[slug] Regenerated for {asset_id}: {slug}")
        return {'slug': slug}
    except Exception as e:
        logger.error(f"[slug] regenerate failed for {asset_id}: {e}")
        raise
    finally:
        db.close()


def slug_needs_generation(slug: str) -> bool:
    """Eligibility for the auto sweep: empty slug OR a too-long (>=5 word) one."""
    wc = _word_count(slug or "")
    return wc == 0 or wc >= LONG_SLUG_TRIGGER_WORDS


@shared_task(name="services.slug_gen_service.sweep_segments_for_slug_generation")
def sweep_segments_for_slug_generation():
    """Periodic task (Beat). Finds one segment whose slug needs (re)generation —
    empty OR >= 5 words — with real content, and generates a short slug. Never
    overwrites a user's valid 1-4 word slug. Word-count is computed in SQL
    (separators are space/hyphen/underscore) so the query only returns the two
    eligible cases.
    """
    # Health-gate the LLM like the description sweep does.
    try:
        host = get_ollama_host(SessionLocal())
        import requests
        h = requests.get(f"{host}/api/tags", timeout=5)
        if h.status_code != 200:
            return {"status": "skipped", "reason": "ollama_unhealthy"}
    except Exception:
        return {"status": "skipped", "reason": "ollama_unreachable"}

    db = SessionLocal()
    try:
        # regexp_count of word separators + 1 gives the word count; eligible when
        # slug is blank OR has >= LONG_SLUG_TRIGGER_WORDS words.
        row = db.execute(text("""
            SELECT ri.asset_id
            FROM rundown_items ri
            JOIN rundowns r ON r.id = ri.rundown_id
            JOIN episodes e ON e.id = r.episode_id
            WHERE e.status IN ('draft', 'production')
              AND COALESCE(e.auto_generate_enabled, TRUE) = TRUE
              AND ri.item_type IN ('segment', 'interview', 'coldopen', 'close')
              AND LENGTH(COALESCE(ri.script_content, '')) >= 100
              AND ri.updated_at < NOW() - INTERVAL '2 minutes'
              AND (
                    LENGTH(TRIM(COALESCE(ri.slug, ''))) = 0
                    OR COALESCE(array_length(
                         regexp_split_to_array(TRIM(ri.slug), '[[:space:]_-]+'), 1), 0) >= :longwords
                  )
            ORDER BY e.air_date ASC NULLS LAST, ri.order_in_rundown ASC
            LIMIT 1
        """), {"longwords": LONG_SLUG_TRIGGER_WORDS}).fetchone()

        if not row:
            return {"status": "idle"}

        asset_id = row.asset_id
        slug = _generate_slug_core(db, asset_id)
        logger.info(f"[slug-sweep] Generated slug for {asset_id}: {slug}")
        return {"status": "processed", "asset_id": asset_id, "slug": slug}
    except Exception as e:
        logger.error(f"[slug-sweep] Error: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
