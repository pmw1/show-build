"""
Auto-description service — background tone classification + segment description generation.

Two-stage Celery pipeline, both tasks keyed by asset_id:
  Stage 1: classify_segment_tone   → reads full segment content, picks tone from palette
  Stage 2: generate_segment_description → renders prompt template, generates description

Both tasks talk directly to Postgres (via SessionLocal) and Ollama (via HTTP).
No FastAPI involvement — designed to run on any Celery worker with DB + Ollama access.

The sweep_segments_for_auto_generation task is fired by Celery Beat every 60s
and selects one eligible segment per tick.
"""
import json
import re
import logging
import requests
from datetime import datetime, timedelta
from sqlalchemy import text
from celery import shared_task
from database import SessionLocal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def get_ollama_host(db):
    """Read Ollama host from api_configs table, fallback to default."""
    try:
        result = db.execute(text(
            "SELECT config_value FROM api_configs WHERE service = 'ollama' AND config_key = 'host'"
        )).fetchone()
        if result:
            return result[0]
    except Exception as e:
        logger.error(f"Failed to get Ollama host: {e}")
    return 'http://172.17.0.1:11434'


def get_ollama_fallback_model(db, purpose='classifier'):
    """Read per-task fallback model from api_configs.
    Returns None if no fallback is configured for this purpose."""
    task_service_map = {
        'classifier': 'tone_classification',
        'generator': 'segment_description',
        'episode_generator': 'episode_description',
        'episode_short': 'episode_short_description',
        'legacy_cue_match': 'legacy_cue_convert',
    }
    service = task_service_map.get(purpose, '')
    if not service:
        return None
    try:
        result = db.execute(text(
            "SELECT config_value FROM api_configs "
            "WHERE workflow = 'generation' AND service = :svc AND config_key = 'fallback_model' LIMIT 1"
        ), {"svc": service}).fetchone()
        if result and result[0]:
            return result[0]
    except Exception:
        pass
    return None


def get_ollama_model(db, purpose='classifier'):
    """Read Ollama model from api_configs.
    Checks for a per-task model first (e.g. segment_description/model),
    then falls back to the global ollama/model setting.
    """
    # Per-task model override
    task_service_map = {
        'classifier': 'tone_classification',
        'generator': 'segment_description',
        'episode_generator': 'episode_description',
        'episode_short': 'episode_short_description',
        'legacy_cue_match': 'legacy_cue_convert',  # Picks media file by slug fuzzy-match tiebreaker
    }
    service = task_service_map.get(purpose, '')
    if service:
        try:
            result = db.execute(text(
                "SELECT config_value FROM api_configs "
                "WHERE workflow = 'generation' AND service = :svc AND config_key = 'model' LIMIT 1"
            ), {"svc": service}).fetchone()
            if result and result[0]:
                return result[0]
        except Exception:
            pass

    # Global fallback
    try:
        result = db.execute(text(
            "SELECT config_value FROM api_configs WHERE service = 'ollama' AND config_key = 'model'"
        )).fetchone()
        if result:
            return result[0]
    except Exception:
        pass

    # Hardcoded last resort
    if purpose == 'classifier':
        return 'qwen2.5:latest'
    return 'llama3:latest'


def get_tone_palette(db):
    """Read tone palette from the settings table, or return defaults."""
    # The tone palette is stored in localStorage on the frontend and doesn't
    # have a dedicated backend table yet. For now we hardcode the defaults —
    # a future enhancement would store this in api_configs or a settings table.
    return [
        'serious', 'somber', 'skeptical', 'irreverent', 'sarcastic',
        'lighthearted', 'urgent', 'analytical', 'mocking'
    ]


DEFAULT_EPISODE_PROMPT = (
    'Generate a compelling episode description for {{show_name}} Episode {{episode_number}}.\n\n'
    '{% if has_title %}Episode title: {{episode_title}}\n{% endif %}'
    '{% if has_guest %}Guest: {{guest}}\n{% endif %}'
    '{% if has_subtitle %}Subtitle: {{subtitle}}\n{% endif %}\n'
    'Segments:\n{{segment_summaries}}\n\n'
    'Requirements:\n'
    '- 2-4 sentences\n'
    '- Capture the key topics and why they matter\n'
    '- Match the show voice and audience'
)


def get_episode_prompt_template():
    """Read the episode description prompt from api_configs (set by Settings UI).
    Falls back to DEFAULT_EPISODE_PROMPT if not configured."""
    db = SessionLocal()
    try:
        row = db.execute(text(
            "SELECT config_value FROM api_configs "
            "WHERE workflow = 'generation' AND service = 'episode_description' "
            "AND config_key = 'prompt' LIMIT 1"
        )).fetchone()
        return row[0] if row and row[0] else DEFAULT_EPISODE_PROMPT
    except Exception:
        return DEFAULT_EPISODE_PROMPT
    finally:
        db.close()


DEFAULT_SEGMENT_PROMPT = (
    'Write a concise, engaging description for the "{{segment_title}}" segment '
    'of {{show_name}} Episode {{episode_number}}.\n\n'
    'Segment type: {{segment_type}}\n'
    'Duration: {{segment_duration}}\n\n'
    '{% if has_tone %}Editorial tone: {{segment_tone}} — {{segment_tone_rationale}}\n'
    'Write the description in that tone.\n\n{% endif %}'
    'Content:\n{{segment_content}}\n\n'
    '{% if has_adjacent_context %}Adjacent context:\n'
    'Previous: {{adjacent_previous}}\nNext: {{adjacent_next}}\n\n{% endif %}'
    'Requirements:\n'
    '- 2-3 sentences\n'
    '- Capture the key idea and why it matters\n'
    '- Match the segment tone, show voice, and audience'
)

def get_generation_temperature(db, service='segment_description', default=0.4):
    """Read temperature setting from api_configs."""
    try:
        row = db.execute(text(
            "SELECT config_value FROM api_configs "
            "WHERE workflow = 'generation' AND service = :svc AND config_key = 'temperature' LIMIT 1"
        ), {"svc": service}).fetchone()
        return float(row[0]) if row and row[0] else default
    except Exception:
        return default


def get_segment_prompt_template():
    """Read the segment description prompt from api_configs (set by Settings UI).
    Falls back to DEFAULT_SEGMENT_PROMPT if not configured."""
    db = SessionLocal()
    try:
        row = db.execute(text(
            "SELECT config_value FROM api_configs "
            "WHERE workflow = 'generation' AND service = 'segment_description' "
            "AND config_key = 'prompt' LIMIT 1"
        )).fetchone()
        return row[0] if row and row[0] else DEFAULT_SEGMENT_PROMPT
    except Exception:
        return DEFAULT_SEGMENT_PROMPT
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Ollama caller
# ---------------------------------------------------------------------------

def call_ollama(host, model, prompt, temperature=0.2, max_tokens=500, timeout=600, fallback_model=None, think=None):
    """Synchronous Ollama /api/generate call. Returns the response text.
    If `fallback_model` is provided and the primary model 404s, retries once with the fallback.

    `think=False` disables the thinking phase on reasoning models (qwen3
    etc., Ollama >= 0.9). IMPORTANT for structured-output calls: thinking
    tokens count against num_predict, so a reasoning model can burn the
    whole budget thinking and return an EMPTY response — that's exactly
    what broke extract-cue on real-sized prompts. None omits the field."""
    candidates = [model]
    if fallback_model and fallback_model != model:
        candidates.append(fallback_model)
    last_exc = None
    for idx, m in enumerate(candidates):
        try:
            payload = {
                "model": m,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            if think is not None:
                payload["think"] = think
            resp = requests.post(
                f"{host}/api/generate",
                json=payload,
                timeout=timeout
            )
            if resp.status_code == 404 and idx < len(candidates) - 1:
                continue
            resp.raise_for_status()
            data = resp.json()
            return (data.get("response") or "").strip()
        except requests.RequestException as exc:
            last_exc = exc
            if idx < len(candidates) - 1:
                continue
            raise
    if last_exc:
        raise last_exc
    return ""




# ---------------------------------------------------------------------------
# Template rendering (simple Jinja-like)
# ---------------------------------------------------------------------------

def render_template(template, variables):
    """Replace {{var}} placeholders and evaluate {% if flag %}...{% endif %} blocks."""
    result = template
    # Conditionals first
    def eval_conditional(match):
        flag = match.group(1).strip()
        content = match.group(2)
        return content if variables.get(flag) else ''
    result = re.sub(
        r'\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}',
        eval_conditional,
        result,
        flags=re.DOTALL
    )
    # Variable substitution
    for key, value in variables.items():
        placeholder = '{{' + key + '}}'
        result = result.replace(placeholder, str(value) if value else '')
    # Clean up leftover unreplaced variables
    result = re.sub(r'\{\{[^}]+\}\}', '', result)
    return result.strip()


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_segment_context(db, asset_id):
    """Load full segment context needed for tone classification and description generation.
    Returns a dict with all relevant fields, or None if not found.
    """
    row = db.execute(text("""
        SELECT
            ri.id, ri.asset_id, ri.title, ri.slug, ri.item_type,
            ri.script_content, ri.description, ri.duration,
            ri.guests, ri.tags, ri.resources, ri.priority,
            ri.tone, ri.tone_rationale, ri.tone_confidence,
            ri.llm_generated_fields, ri.auto_generate_attempts,
            ri.order_in_rundown, ri.rundown_id, ri.status,
            ri.speaker_id,
            e.episode_number, e.title as episode_title, e.air_date,
            e.auto_generate_enabled
        FROM rundown_items ri
        JOIN rundowns r ON r.id = ri.rundown_id
        JOIN episodes e ON e.id = r.episode_id
        WHERE ri.asset_id = :aid
    """), {"aid": asset_id}).fetchone()

    if not row:
        return None

    ctx = dict(row._mapping)

    # Load adjacent segments for context
    if ctx['order_in_rundown'] is not None and ctx['rundown_id']:
        prev_row = db.execute(text("""
            SELECT title, script_content FROM rundown_items
            WHERE rundown_id = :rid AND order_in_rundown = :ord
            LIMIT 1
        """), {"rid": ctx['rundown_id'], "ord": ctx['order_in_rundown'] - 1}).fetchone()

        next_row = db.execute(text("""
            SELECT title, script_content FROM rundown_items
            WHERE rundown_id = :rid AND order_in_rundown = :ord
            LIMIT 1
        """), {"rid": ctx['rundown_id'], "ord": ctx['order_in_rundown'] + 1}).fetchone()

        ctx['adjacent_previous'] = (
            f"{prev_row.title}: {(prev_row.script_content or '')[:200]}"
            if prev_row else ''
        )
        ctx['adjacent_next'] = (
            f"{next_row.title}: {(next_row.script_content or '')[:200]}"
            if next_row else ''
        )
    else:
        ctx['adjacent_previous'] = ''
        ctx['adjacent_next'] = ''

    # Load show identity from api_configs (if available)
    si = {}
    try:
        si_row = db.execute(text(
            "SELECT config_value FROM api_configs WHERE service = 'show_identity' AND config_key = 'show_identity'"
        )).fetchone()
        if si_row:
            si = json.loads(si_row[0]) if isinstance(si_row[0], str) else si_row[0]
    except Exception:
        pass
    ctx['show_name'] = si.get('name', 'Disaffected')
    ctx['show_thesis'] = si.get('thesis', '')
    ctx['show_tone'] = si.get('tone', '')
    ctx['show_audience'] = si.get('audience', '')

    return ctx


def update_segment_fields(db, asset_id, fields: dict):
    """Update specific columns on a rundown_item by asset_id."""
    set_clauses = []
    params = {"aid": asset_id}
    for key, value in fields.items():
        set_clauses.append(f"{key} = :{key}")
        params[key] = value
    if not set_clauses:
        return
    sql = f"UPDATE rundown_items SET {', '.join(set_clauses)} WHERE asset_id = :aid"
    db.execute(text(sql), params)
    db.commit()


def append_segment_description_history(db, asset_id, role, text_content):
    """Append an entry to the description_gen_history JSON array."""
    row = db.execute(text(
        "SELECT description_gen_history FROM rundown_items WHERE asset_id = :aid"
    ), {"aid": asset_id}).fetchone()

    history = row[0] if row and row[0] else []
    history.append({
        "role": role,
        "text": text_content,
        "ts": datetime.utcnow().isoformat() + "Z"
    })
    db.execute(text(
        "UPDATE rundown_items SET description_gen_history = :val WHERE asset_id = :aid"
    ), {"aid": asset_id, "val": json.dumps(history)})
    db.commit()


def get_segment_description_history(db, asset_id):
    """Read the description_gen_history array."""
    row = db.execute(text(
        "SELECT description_gen_history FROM rundown_items WHERE asset_id = :aid"
    ), {"aid": asset_id}).fetchone()
    return (row[0] if row and row[0] else [])


def send_llm_notification(db, content_type, asset_id, segment_title, episode_number, status, message):
    """Write a notification record for the frontend to pick up via polling."""
    try:
        db.execute(text("""
            INSERT INTO llm_notifications (type, content_type, asset_id, segment_title, episode_number, status, message)
            VALUES ('llm_content', :ct, :aid, :title, :ep, :status, :msg)
        """), {
            "ct": content_type, "aid": asset_id, "title": segment_title or '',
            "ep": episode_number or '', "status": status, "msg": message
        })
        db.commit()
    except Exception as e:
        logger.error(f"[notify] Failed to write notification: {e}")


def add_llm_generated_field(db, asset_id, field_name):
    """Add a field name to llm_generated_fields JSON array (idempotent)."""
    row = db.execute(text(
        "SELECT llm_generated_fields FROM rundown_items WHERE asset_id = :aid"
    ), {"aid": asset_id}).fetchone()

    current = row[0] if row and row[0] else []
    if field_name not in current:
        current.append(field_name)
        db.execute(text(
            "UPDATE rundown_items SET llm_generated_fields = :val WHERE asset_id = :aid"
        ), {"aid": asset_id, "val": json.dumps(current)})
        db.commit()


# ---------------------------------------------------------------------------
# Stage 1: Tone classification
# ---------------------------------------------------------------------------

@shared_task(name="services.auto_description_service.classify_segment_tone")
def classify_segment_tone(asset_id: str) -> dict:
    """Classify the editorial tone of a segment by feeding its full content
    to a small LLM with a constrained output set (the tone palette).

    Returns: {tone, confidence, rationale} or raises on failure.
    """
    logger.info(f"[tone] Classifying tone for segment {asset_id}")
    db = SessionLocal()
    try:
        ctx = load_segment_context(db, asset_id)
        if not ctx:
            raise ValueError(f"Segment {asset_id} not found")

        if not ctx.get('script_content') or len(ctx['script_content'].strip()) < 50:
            raise ValueError(f"Segment {asset_id} has insufficient content for tone classification")

        host = get_ollama_host(db)
        model = get_ollama_model(db, purpose='classifier')
        fallback = get_ollama_fallback_model(db, purpose='classifier')
        palette = get_tone_palette(db)

        # Read tone prompt from settings or use default
        tone_prompt_template = None
        try:
            row = db.execute(text(
                "SELECT config_value FROM api_configs "
                "WHERE workflow = 'generation' AND service = 'tone_classification' "
                "AND config_key = 'prompt' LIMIT 1"
            )).fetchone()
            if row and row[0]:
                tone_prompt_template = row[0]
        except Exception:
            pass

        if tone_prompt_template:
            tone_vars = {
                'tone_palette': ', '.join(palette),
                'segment_title': ctx.get('title', 'Untitled'),
                'segment_type': ctx.get('item_type', 'segment'),
                'segment_content': ctx['script_content'][:4000],
            }
            prompt = render_template(tone_prompt_template, tone_vars)
        else:
            prompt = (
                f"Classify the editorial tone of this broadcast segment. "
                f"Choose exactly ONE tone from this list: {', '.join(palette)}.\n\n"
                f"Respond ONLY with valid JSON: "
                f'{{"tone": "<chosen tone>", "confidence": <0.0-1.0>, "rationale": "<one sentence>"}}\n\n'
                f"Segment title: {ctx.get('title', 'Untitled')}\n"
                f"Segment type: {ctx.get('item_type', 'segment')}\n\n"
                f"Full segment content:\n{ctx['script_content'][:4000]}"
            )

        temp = get_generation_temperature(db, 'tone_classification', 0.1)
        raw = call_ollama(host, model, prompt, temperature=temp, max_tokens=200, timeout=120, fallback_model=fallback)
        logger.info(f"[tone] Raw LLM response for {asset_id}: {raw[:300]}")

        if not raw or not raw.strip():
            raise ValueError(f"LLM returned empty response for tone classification")

        # Parse JSON from response (tolerate markdown code fences)
        cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip())
        cleaned = re.sub(r'\s*```$', '', cleaned.strip())
        parsed = json.loads(cleaned)

        tone = str(parsed.get('tone', '')).lower().strip()
        confidence = float(parsed.get('confidence', 0.5))
        rationale = str(parsed.get('rationale', ''))

        # Validate tone is in palette (fallback to raw if not)
        if tone not in [p.lower() for p in palette]:
            logger.warning(f"[tone] LLM returned '{tone}' which is not in palette, using anyway")

        # Write to DB
        update_segment_fields(db, asset_id, {
            'tone': tone,
            'tone_rationale': rationale,
            'tone_confidence': confidence
        })
        add_llm_generated_field(db, asset_id, 'tone')

        result = {'tone': tone, 'confidence': confidence, 'rationale': rationale}
        logger.info(f"[tone] Classified {asset_id}: {result}")
        return result

    except Exception as e:
        logger.error(f"[tone] Failed for {asset_id}: {e}")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Stage 2: Description generation
# ---------------------------------------------------------------------------

@shared_task(name="services.auto_description_service.generate_segment_description")
def generate_segment_description(asset_id: str) -> dict:
    """Generate a segment description using the prompt template from settings,
    with all available segment/episode/tone variables resolved.

    Returns: {description: str} or raises on failure.
    """
    logger.info(f"[desc] Generating description for segment {asset_id}")
    db = SessionLocal()
    try:
        ctx = load_segment_context(db, asset_id)
        if not ctx:
            raise ValueError(f"Segment {asset_id} not found")

        host = get_ollama_host(db)
        model = get_ollama_model(db, purpose='generator')
        fallback = get_ollama_fallback_model(db, purpose='generator')
        template = get_segment_prompt_template()

        # Build template variables
        variables = {
            'segment_title': ctx.get('title') or ctx.get('slug') or 'Untitled',
            'segment_slug': ctx.get('slug') or '',
            'segment_type': ctx.get('item_type') or 'segment',
            'segment_duration': ctx.get('duration') or '',
            'segment_order': ctx.get('order_in_rundown') or '',
            'segment_priority': ctx.get('priority') or '',
            'segment_content': (ctx.get('script_content') or '')[:6000],
            'segment_current_description': ctx.get('description') or '',
            'segment_speaker': '',  # TODO: resolve speaker name from speaker_id
            'segment_guests': ctx.get('guests') or '',
            'segment_tags': ctx.get('tags') or '',
            'segment_resources': ctx.get('resources') or '',
            'segment_customer': '',  # customer column not on all schemas
            'segment_tone': ctx.get('tone') or '',
            'segment_tone_rationale': ctx.get('tone_rationale') or '',
            'segment_tone_confidence': ctx.get('tone_confidence') or '',
            'adjacent_previous': ctx.get('adjacent_previous') or '',
            'adjacent_next': ctx.get('adjacent_next') or '',
            'show_name': ctx.get('show_name') or 'Disaffected',
            'episode_number': ctx.get('episode_number') or '',
            'episode_title': ctx.get('episode_title') or '',
            'air_date': str(ctx.get('air_date') or ''),
            'host_name': '',  # TODO: resolve from show identity
            'show_thesis': ctx.get('show_thesis') or '',
            'show_tone': ctx.get('show_tone') or '',
            'show_audience': ctx.get('show_audience') or '',
            # Boolean flags for conditionals
            'has_tone': bool(ctx.get('tone')),
            'has_adjacent_context': bool(ctx.get('adjacent_previous') or ctx.get('adjacent_next')),
            'has_full_text': bool(ctx.get('script_content')),
            'has_speaker': bool(ctx.get('speaker_id')),
            'has_guests': bool(ctx.get('guests')),
            'has_tags': bool(ctx.get('tags')),
            'inject_show_identity': bool(ctx.get('show_thesis')),
        }

        rendered_prompt = render_template(template, variables)
        logger.info(f"[desc] Rendered prompt for {asset_id} ({len(rendered_prompt)} chars)")

        temp = get_generation_temperature(db, 'segment_description', 0.4)
        description = call_ollama(host, model, rendered_prompt, temperature=temp, max_tokens=500, fallback_model=fallback)

        # Write to DB + record in history
        update_segment_fields(db, asset_id, {
            'description': description,
            'description_model': model,
            'auto_generate_attempts': 0  # Reset on success
        })
        add_llm_generated_field(db, asset_id, 'description')
        append_segment_description_history(db, asset_id, 'llm', description)

        result = {'description': description, 'description_model': model}
        logger.info(f"[desc] Generated for {asset_id}: {description[:120]}...")
        send_llm_notification(db, 'segment_description', asset_id,
                              ctx.get('title', ''), ctx.get('episode_number', ''),
                              'success', f"Description generated for \"{ctx.get('title', asset_id)}\"")
        return result

    except Exception as e:
        logger.error(f"[desc] Failed for {asset_id}: {e}")
        try:
            ndb = SessionLocal()
            send_llm_notification(ndb, 'segment_description', asset_id, '', '', 'failed', str(e)[:500])
            ndb.close()
        except Exception:
            pass
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Regenerate — user-initiated with feedback, full history as context
# ---------------------------------------------------------------------------

def _build_segment_variables(ctx, previous_description=''):
    """Build the standard template variable dict from a segment context."""
    return {
        'segment_title': ctx.get('title') or ctx.get('slug') or 'Untitled',
        'segment_slug': ctx.get('slug') or '',
        'segment_type': ctx.get('item_type') or 'segment',
        'segment_duration': ctx.get('duration') or '',
        'segment_order': ctx.get('order_in_rundown') or '',
        'segment_priority': ctx.get('priority') or '',
        'segment_content': (ctx.get('script_content') or '')[:6000],
        'segment_current_description': previous_description,
        'segment_speaker': '',
        'segment_guests': ctx.get('guests') or '',
        'segment_tags': ctx.get('tags') or '',
        'segment_resources': ctx.get('resources') or '',
        'segment_customer': '',
        'segment_tone': ctx.get('tone') or '',
        'segment_tone_rationale': ctx.get('tone_rationale') or '',
        'segment_tone_confidence': ctx.get('tone_confidence') or '',
        'adjacent_previous': ctx.get('adjacent_previous') or '',
        'adjacent_next': ctx.get('adjacent_next') or '',
        'show_name': ctx.get('show_name') or 'Disaffected',
        'episode_number': ctx.get('episode_number') or '',
        'episode_title': ctx.get('episode_title') or '',
        'air_date': str(ctx.get('air_date') or ''),
        'host_name': '',
        'show_thesis': ctx.get('show_thesis') or '',
        'show_tone': ctx.get('show_tone') or '',
        'show_audience': ctx.get('show_audience') or '',
        'has_tone': bool(ctx.get('tone')),
        'has_adjacent_context': bool(ctx.get('adjacent_previous') or ctx.get('adjacent_next')),
        'has_full_text': bool(ctx.get('script_content')),
        'has_speaker': bool(ctx.get('speaker_id')),
        'has_guests': bool(ctx.get('guests')),
        'has_tags': bool(ctx.get('tags')),
        'inject_show_identity': bool(ctx.get('show_thesis')),
    }


def regenerate_segment_description(asset_id: str, previous_description: str, feedback: str) -> dict:
    """Regenerate a segment description incorporating the user's feedback.

    The LLM receives:
    - The full standard prompt (segment content, tone, template variables)
    - The complete generation history (every prior LLM attempt + user feedback)
    - The latest user feedback

    Each iteration builds on all previous ones so the LLM can converge
    toward the user's desired description across multiple rounds.

    Returns: {description: str}
    """
    logger.info(f"[regen] Regenerating description for {asset_id} with feedback: {feedback[:100]}...")
    db = SessionLocal()
    try:
        ctx = load_segment_context(db, asset_id)
        if not ctx:
            raise ValueError(f"Segment {asset_id} not found")

        host = get_ollama_host(db)
        model = get_ollama_model(db, purpose='generator')
        fallback = get_ollama_fallback_model(db, purpose='generator')
        template = get_segment_prompt_template()

        variables = _build_segment_variables(ctx, previous_description)
        rendered_base = render_template(template, variables)

        # Build the full conversation history for context
        history = get_segment_description_history(db, asset_id)
        history_block = ""
        if history:
            history_block = "\n--- GENERATION HISTORY ---\n"
            for entry in history:
                role_label = "LLM generated" if entry.get('role') == 'llm' else "User feedback"
                history_block += f"[{role_label}]: {entry.get('text', '')}\n\n"

        regen_prompt = (
            f"{rendered_base}\n\n"
            f"{history_block}"
            f"---\n"
            f"The current description is:\n"
            f'"{previous_description}"\n\n'
            f"The user wants changes. Their latest feedback:\n"
            f'"{feedback}"\n\n'
            f"Write a NEW description that addresses ALL the user's feedback "
            f"(both current and any prior rounds above). "
            f"IMPORTANT: Output ONLY the raw description text. "
            f"Do NOT include any preamble like 'Here is...' or 'Here's a rewritten...'. "
            f"Do NOT wrap in quotes. Just the description itself, nothing else."
        )

        logger.info(f"[regen] Rendered regen prompt for {asset_id} ({len(regen_prompt)} chars, {len(history)} history entries)")

        temp = get_generation_temperature(db, 'segment_description', 0.4)
        description = call_ollama(host, model, regen_prompt, temperature=temp, max_tokens=500, fallback_model=fallback)

        # Record user feedback + new generation in history
        append_segment_description_history(db, asset_id, 'user', feedback)
        append_segment_description_history(db, asset_id, 'llm', description)

        # Write to DB
        update_segment_fields(db, asset_id, {'description': description, 'description_model': model})
        add_llm_generated_field(db, asset_id, 'description')

        logger.info(f"[regen] Regenerated for {asset_id}: {description[:120]}...")
        return {'description': description, 'description_model': model}

    except Exception as e:
        logger.error(f"[regen] Failed for {asset_id}: {e}")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Sweeper — selects the next eligible segment and enqueues the pipeline
# ---------------------------------------------------------------------------

@shared_task(name="services.auto_description_service.sweep_segments_for_auto_generation")
def sweep_segments_for_auto_generation():
    """Periodic task (fired by Beat every 60s). Finds one eligible segment
    and enqueues the tone-classify → description-generate chain.

    Selection criteria (all must be true):
    - Episode: status draft/production, auto_generate_enabled = true
    - Segment: type in (segment, interview, coldopen)
    - Description empty AND not previously auto-filled then rejected
    - Has real content (>= 100 chars)
    - Not recently edited (2 min cool-down)
    - Ordered by: nearest air-date, then rundown order
    """
    logger.info("[sweep] Running auto-description sweep")

    # Ollama health gate — skip the tick if the LLM server is unreachable
    try:
        ollama_host = get_ollama_host(SessionLocal())
        health = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if health.status_code != 200:
            logger.warning(f"[sweep] Ollama unhealthy (HTTP {health.status_code}), skipping tick")
            return {"status": "skipped", "reason": "ollama_unhealthy"}
    except Exception as e:
        logger.warning(f"[sweep] Ollama unreachable ({e}), skipping tick")
        return {"status": "skipped", "reason": "ollama_unreachable"}

    db = SessionLocal()
    try:
        row = db.execute(text("""
            SELECT ri.asset_id,
                   (ri.tone IS NULL OR ri.tone = '') AS needs_tone,
                   COALESCE(ri.auto_generate_attempts, 0) AS attempts
            FROM rundown_items ri
            JOIN rundowns r ON r.id = ri.rundown_id
            JOIN episodes e ON e.id = r.episode_id
            WHERE e.status IN ('draft', 'production')
              AND COALESCE(e.auto_generate_enabled, TRUE) = TRUE
              AND ri.item_type IN ('segment', 'interview', 'coldopen', 'close')
              AND LENGTH(TRIM(COALESCE(ri.description, ''))) < 3
              AND COALESCE(ri.auto_description_enabled, TRUE) = TRUE
              AND LENGTH(COALESCE(ri.script_content, '')) >= 100
              AND ri.updated_at < NOW() - INTERVAL '2 minutes'
            ORDER BY COALESCE(ri.auto_generate_attempts, 0) ASC,
                     e.air_date ASC NULLS LAST, ri.order_in_rundown ASC
            LIMIT 1
        """)).fetchone()

        if not row:
            logger.info("[sweep] No eligible segments found")
            return {"status": "idle", "message": "No segments need processing"}

        asset_id = row.asset_id
        needs_tone = row.needs_tone
        attempts = row.attempts if hasattr(row, 'attempts') else 0
        logger.info(f"[sweep] Selected segment {asset_id} (needs_tone={needs_tone}, attempts={attempts})")

        # Run synchronously (we're already on the worker; concurrency=1 ensures
        # only one of these runs at a time). If we move to async dispatch later,
        # swap these for chain().apply_async().
        if needs_tone:
            if attempts >= 2:
                # Tone classification keeps failing — skip it, use fallback tone,
                # and proceed to description generation
                logger.warning(f"[sweep] Skipping tone classification for {asset_id} after {attempts} failed attempts, using fallback")
                update_segment_fields(db, asset_id, {'tone': 'analytical', 'tone_rationale': 'Fallback — tone classification failed after multiple attempts'})
            else:
                classify_segment_tone(asset_id)
        generate_segment_description(asset_id)

        return {"status": "processed", "asset_id": asset_id, "tone_classified": needs_tone}

    except Exception as e:
        logger.error(f"[sweep] Error: {e}")
        # Increment attempts so a permanently failing segment doesn't block others
        try:
            db.execute(text(
                "UPDATE rundown_items SET auto_generate_attempts = COALESCE(auto_generate_attempts, 0) + 1 "
                "WHERE asset_id = :aid"
            ), {"aid": asset_id})
            db.commit()
            logger.info(f"[sweep] Incremented auto_generate_attempts for {asset_id}")
        except Exception:
            db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Episode description generation
# ---------------------------------------------------------------------------

def _build_priority_hierarchy(ep_settings):
    """Build a numbered priority hierarchy string from settings."""
    try:
        order = json.loads(ep_settings.get('priority_order', '[]'))
        if not order:
            return ''
        lines = []
        for i, item in enumerate(order, 1):
            tag = item.get('tag', '')
            label = item.get('label', tag)
            lines.append(f"  {i}. {tag} — {label}")
        return '\n'.join(lines)
    except (json.JSONDecodeError, TypeError):
        return ''


@shared_task(name="services.auto_description_service.generate_episode_description")
def generate_episode_description(episode_number):
    """Generate an episode-level description from segment titles/descriptions."""
    logger.info(f"[ep-desc] Generating description for episode {episode_number}")
    db = SessionLocal()
    try:
        # Load episode metadata
        ep = db.execute(text("""
            SELECT e.id, e.title, e.subtitle, e.guest_name, e.guest_bio,
                   e.episode_number, e.duration_formatted, e.air_date
            FROM episodes e
            WHERE e.episode_number = :ep
        """), {"ep": str(episode_number)}).fetchone()

        if not ep:
            raise ValueError(f"Episode {episode_number} not found")

        # Load show identity for show_name
        si = {}
        try:
            si_row = db.execute(text(
                "SELECT config_value FROM api_configs WHERE service = 'show_identity' AND config_key = 'show_identity'"
            )).fetchone()
            if si_row:
                si = json.loads(si_row[0]) if isinstance(si_row[0], str) else si_row[0]
        except Exception:
            pass

        # Read item types from settings
        ep_settings = get_episode_desc_settings(db)
        try:
            item_types_cfg = json.loads(ep_settings.get('item_types', '{}'))
            include_types = [k for k, v in item_types_cfg.items() if v]
        except (json.JSONDecodeError, TypeError):
            include_types = []
        if not include_types:
            include_types = ['segment', 'interview']
        # By default, do NOT use 'close' content in the show description
        # prompt (close items can still be auto-described — see segment sweep).
        # Set api_configs key 'include_close_in_description' to 'true' to opt in.
        include_close = str(ep_settings.get('include_close_in_description', 'false')).lower() == 'true'
        if not include_close:
            include_types = [t for t in include_types if t != 'close']
        type_placeholders = ', '.join(f"'{t}'" for t in include_types)

        # Gather segment summaries with all available info
        segments = db.execute(text(f"""
            SELECT ri.title, ri.description, ri.item_type, ri.tone,
                   ri.tone_rationale, ri.duration, ri.priority, ri.tags,
                   ri.order_in_rundown
            FROM rundown_items ri
            JOIN rundowns r ON r.id = ri.rundown_id
            WHERE r.episode_id = :eid
              AND ri.item_type IN ({type_placeholders})
            ORDER BY ri.order_in_rundown ASC
        """), {"eid": ep.id}).fetchall()

        segment_summaries = []
        for seg in segments:
            title = seg.title or 'Untitled'
            desc = seg.description or ''
            parts = [f"- {title}"]
            if seg.tone:
                parts.append(f"[{seg.tone}]")
            if seg.priority and seg.priority not in ('normal', ''):
                parts.append(f"({seg.priority})")
            if seg.duration and seg.duration != '00:00:00':
                parts.append(f"[{seg.duration}]")
            header = ' '.join(parts)
            if desc:
                segment_summaries.append(f"{header}: {desc}")
            else:
                segment_summaries.append(header)

        host = get_ollama_host(db)
        model = get_ollama_model(db, purpose='episode_generator')
        fallback = get_ollama_fallback_model(db, purpose='episode_generator')
        template = get_episode_prompt_template()

        # Format air date
        air_date_str = ''
        if ep.air_date:
            try:
                air_date_str = ep.air_date.strftime('%B %d, %Y')
            except Exception:
                air_date_str = str(ep.air_date)

        ep_num = ep.episode_number or episode_number
        ep_num_padded = f"{int(ep_num):04d}" if str(ep_num).isdigit() else str(ep_num)

        # Scan priority tags across all segments
        all_priorities = set()
        tagged_summaries = {}  # tag -> list of segment summaries
        for seg in segments:
            seg_priority = seg.priority or ''
            for tag in seg_priority.split(','):
                tag = tag.strip().lower()
                if tag:
                    all_priorities.add(tag)
                    summary = f"{seg.title or 'Untitled'}: {seg.description or ''}"
                    tagged_summaries.setdefault(tag, []).append(summary)

        variables = {
            'show_name': si.get('name', 'Disaffected'),
            'episode_number': ep_num_padded,
            'episode_title': ep.title or '',
            'title': ep.title or '',
            'subtitle': ep.subtitle or '',
            'guest': ep.guest_name or '',
            'guest_names': ep.guest_name or '',
            'guest_bios': ep.guest_bio or '',
            'duration': ep.duration_formatted or '',
            'air_date': air_date_str,
            'segment_summaries': '\n'.join(segment_summaries),
            'has_title': bool(ep.title),
            'has_subtitle': bool(ep.subtitle),
            'has_guest': bool(ep.guest_name),
            'has_guest_bio': bool(ep.guest_bio),
            'has_duration': bool(ep.duration_formatted),
            'has_air_date': bool(ep.air_date),
            # Priority tag conditionals
            'has_breaking': 'breaking' in all_priorities,
            'has_main_feature': 'main-feature' in all_priorities,
            'has_top_story': 'top-story' in all_priorities,
            'has_deep_dive': 'deep-dive' in all_priorities,
            # Priority tag summaries
            'breaking_summary': '\n'.join(tagged_summaries.get('breaking', [])),
            'main_feature_summary': '\n'.join(tagged_summaries.get('main-feature', [])),
            'top_story_summary': '\n'.join(tagged_summaries.get('top-story', [])),
            'deep_dive_summary': '\n'.join(tagged_summaries.get('deep-dive', [])),
            # Dynamic priority hierarchy from settings
            'priority_hierarchy': _build_priority_hierarchy(ep_settings),
            # Show identity
            'show_thesis': si.get('thesis', ''),
            'show_tone': si.get('tone', ''),
            'show_audience': si.get('audience', ''),
            'has_show_identity': bool(si.get('thesis') or si.get('tone') or si.get('audience')),
            # Stubs for future implementation
            'topics': '',
            'key_quotes': '',
            'weighted_content': '',
            'speaker_name': '',
            'host_name': si.get('name', ''),
        }

        rendered_prompt = render_template(template, variables)
        logger.info(f"[ep-desc] Rendered prompt for ep {episode_number} ({len(rendered_prompt)} chars, {len(segments)} segments)")

        temp = get_generation_temperature(db, 'episode_description', 0.4)
        description = call_ollama(host, model, rendered_prompt, temperature=temp, max_tokens=600, fallback_model=fallback)

        # Save to episode
        db.execute(text(
            "UPDATE episodes SET description = :desc, description_model = :model WHERE episode_number = :ep"
        ), {"desc": description, "model": model, "ep": str(episode_number)})
        db.commit()

        # Send notification
        send_llm_notification(db, 'episode_description', str(episode_number),
                              ep.title or '', str(episode_number),
                              'success', f"Episode description generated for Ep {episode_number}")

        logger.info(f"[ep-desc] Generated for ep {episode_number}: {description[:120]}...")
        return {"status": "success", "episode_number": episode_number, "description": description}

    except Exception as e:
        logger.error(f"[ep-desc] Error for episode {episode_number}: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


def get_episode_desc_settings(db):
    """Read episode description generation settings from api_configs."""
    settings = {}
    rows = db.execute(text(
        "SELECT config_key, config_value FROM api_configs "
        "WHERE workflow = 'generation' AND service = 'episode_description'"
    )).fetchall()
    for row in rows:
        settings[row[0]] = row[1]
    return settings


def get_episode_short_desc_prompt():
    """Read the short description prompt from api_configs."""
    db = SessionLocal()
    try:
        row = db.execute(text(
            "SELECT config_value FROM api_configs "
            "WHERE workflow = 'generation' AND service = 'episode_short_description' "
            "AND config_key = 'prompt' LIMIT 1"
        )).fetchone()
        return row[0] if row and row[0] else None
    except Exception:
        return None
    finally:
        db.close()


@shared_task(name="services.auto_description_service.generate_episode_short_description")
def generate_episode_short_description(episode_number):
    """Generate a short episode description from the full description."""
    logger.info(f"[ep-short] Generating short description for episode {episode_number}")
    db = SessionLocal()
    try:
        ep = db.execute(text("""
            SELECT e.id, e.title, e.episode_number, e.description
            FROM episodes e WHERE e.episode_number = :ep
        """), {"ep": str(episode_number)}).fetchone()

        if not ep:
            raise ValueError(f"Episode {episode_number} not found")
        if not ep.description or len(ep.description.strip()) < 10:
            return {"status": "skipped", "reason": "no full description yet"}

        template = get_episode_short_desc_prompt()
        if not template:
            return {"status": "skipped", "reason": "no short description prompt configured"}

        si = {}
        try:
            si_row = db.execute(text(
                "SELECT config_value FROM api_configs WHERE service = 'show_identity' AND config_key = 'show_identity'"
            )).fetchone()
            if si_row:
                si = json.loads(si_row[0]) if isinstance(si_row[0], str) else si_row[0]
        except Exception:
            pass

        ep_settings = get_episode_desc_settings(db)
        try:
            item_types_cfg = json.loads(ep_settings.get('item_types', '{}'))
            include_types = [k for k, v in item_types_cfg.items() if v]
        except (json.JSONDecodeError, TypeError):
            include_types = []
        if not include_types:
            include_types = ['segment', 'interview']
        type_placeholders = ', '.join(f"'{t}'" for t in include_types)

        segments = db.execute(text(f"""
            SELECT ri.title, ri.description, ri.tone
            FROM rundown_items ri
            JOIN rundowns r ON r.id = ri.rundown_id
            WHERE r.episode_id = :eid AND ri.item_type IN ({type_placeholders})
            ORDER BY ri.order_in_rundown ASC
        """), {"eid": ep.id}).fetchall()

        seg_lines = []
        for seg in segments:
            t = seg.title or 'Untitled'
            d = seg.description or ''
            seg_lines.append(f"- {t}: {d}" if d else f"- {t}")

        ep_num_padded = f"{int(ep.episode_number):04d}"

        variables = {
            'show_name': si.get('name', 'Disaffected'),
            'episode_number': ep_num_padded,
            'title': ep.title or '',
            'description': ep.description or '',
            'segment_summaries': '\n'.join(seg_lines),
        }

        rendered = render_template(template, variables)
        host = get_ollama_host(db)
        model = get_ollama_model(db, purpose='episode_short')
        fallback = get_ollama_fallback_model(db, purpose='episode_short')

        temp = get_generation_temperature(db, 'episode_description', 0.4)
        short_desc = call_ollama(host, model, rendered, temperature=temp, max_tokens=150, fallback_model=fallback)

        db.execute(text(
            "UPDATE episodes SET short_description = :desc, short_description_model = :model WHERE episode_number = :ep"
        ), {"desc": short_desc, "model": model, "ep": str(episode_number)})
        db.commit()

        send_llm_notification(db, 'episode_short_description', str(episode_number),
                              ep.title or '', str(episode_number),
                              'success', f"Short description generated for Ep {episode_number}")

        logger.info(f"[ep-short] Generated for ep {episode_number}: {short_desc[:80]}...")
        return {"status": "success", "episode_number": episode_number, "short_description": short_desc}

    except Exception as e:
        logger.error(f"[ep-short] Error for episode {episode_number}: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@shared_task(name="services.auto_description_service.sweep_episodes_for_auto_generation")
def sweep_episodes_for_auto_generation():
    """Periodic task fired by Beat. Finds one episode with empty description
    where all segments already have descriptions, and generates an episode description."""
    logger.info("[ep-sweep] Running episode description sweep")

    db = SessionLocal()
    try:
        # Check if episode description generation is enabled
        ep_settings = get_episode_desc_settings(db)
        if ep_settings.get('enabled') == 'false':
            logger.info("[ep-sweep] Episode description generation disabled in settings")
            return {"status": "skipped", "reason": "disabled"}
    finally:
        db.close()

    try:
        ollama_host = get_ollama_host(SessionLocal())
        health = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if health.status_code != 200:
            return {"status": "skipped", "reason": "ollama_unhealthy"}
    except Exception as e:
        logger.warning(f"[ep-sweep] Ollama unreachable ({e}), skipping tick")
        return {"status": "skipped", "reason": "ollama_unreachable"}

    db = SessionLocal()
    try:
        # Read which item types must have descriptions from settings
        ep_settings = get_episode_desc_settings(db)
        try:
            item_types_cfg = json.loads(ep_settings.get('item_types', '{}'))
            required_types = [k for k, v in item_types_cfg.items() if v]
        except (json.JSONDecodeError, TypeError):
            required_types = []
        if not required_types:
            required_types = ['segment', 'interview']

        # Build type list for SQL
        type_placeholders = ', '.join(f"'{t}'" for t in required_types)

        # Gate: only block on items that *could plausibly* be auto-described
        # (script_content >= 100 chars). Empty placeholder items (e.g. an unused
        # "Close" stub) are ignored so they can't deadlock generation.
        row = db.execute(text(f"""
            SELECT e.episode_number
            FROM episodes e
            JOIN rundowns r ON r.episode_id = e.id
            JOIN rundown_items ri ON ri.rundown_id = r.id
            WHERE e.status IN ('draft', 'production')
              AND COALESCE(e.auto_generate_enabled, TRUE) = TRUE
              AND LENGTH(TRIM(COALESCE(e.description, ''))) < 3
              AND ri.item_type IN ({type_placeholders})
            GROUP BY e.id, e.episode_number, e.air_date
            HAVING COUNT(CASE WHEN LENGTH(TRIM(COALESCE(ri.description, ''))) >= 3 THEN 1 END) > 0
               AND COUNT(CASE WHEN LENGTH(TRIM(COALESCE(ri.description, ''))) < 3
                                   AND LENGTH(COALESCE(ri.script_content, '')) >= 100
                              THEN 1 END) = 0
            ORDER BY e.air_date ASC NULLS LAST
            LIMIT 1
        """)).fetchone()

        if not row:
            logger.info("[ep-sweep] No eligible episodes found")
            return {"status": "idle", "message": "No episodes need processing"}

        episode_number = row.episode_number
        logger.info(f"[ep-sweep] Selected episode {episode_number}")

        generate_episode_description(episode_number)
        generate_episode_short_description(episode_number)

        return {"status": "processed", "episode_number": episode_number}

    except Exception as e:
        logger.error(f"[ep-sweep] Error: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
