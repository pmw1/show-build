"""
script_scrub_service — server-side port of the client "Autoscrub" normalizer.

This is the single source of truth for script_content normalization. It is a
faithful port of the (now-disabled) client-side scrub that lived in
EditorPanel.autoscrubContent() + ContentEditor.autoscrubAllItems(). Keeping it
here, in one function, removes the old split-brain duplication and lets both a
Celery beat job (idle items) and the rundown-item save endpoint (the focused
item) call the same logic.

See docs/AUTOSCRUB_SERVER_REFACTOR_PLAN.md (todo #31).

Pure text-in / text-out. No DB, no I/O — callers persist the result.

Rules ported (in order), each gated by a setting:
  0. Strip YAML frontmatter if present (always; DB-first never stores it).
  1. strip_spans      — strip <span>/<div> cruft, convert font-weight/style
                        spans to <b>/<i>, drop Google-Docs paste artifacts.
  1b. clean_whitespace — &nbsp; -> space, collapse runs of spaces.
  3. remove_leading_dashes — drop a leading dash from a paragraph unless the
                        paragraph is a dash list (2+ lines all dashed).
  3b. flag invalid cues / unwelcome HTML — prefix "*** " + data-needs-attention
                        + data-flag-note (semantic; drives UI + blocks script gen).
  3c. un-flag paragraphs whose offending content is gone.

STEP 4 (empty-paragraph manipulation) is intentionally NOT ported — it was
suspended client-side because it removed blank paragraphs users need around cues.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# --- Pattern source-of-truth (mirror of disaffected-ui legacyCueConvert/patterns.js) ---
# Invalid legacy cue codes like {SOT/slug} or (VO/slug) that must never reach
# rendered output — they are flagged, not auto-converted.
LEGACY_CUE_REGEX = re.compile(
    r"[{(](SOT|VO|VOT|NAT|FSQ|FS\s*QUOTE|GFX|IMG|PKG|DIR|BUMP|STING|VOX|MUS|LIVE|RIF|CUE)\s*/([^})]+)[})]",
    re.IGNORECASE,
)
LEGACY_CUE_FLAG_LABEL = "Invalid cue code"

# HTML tags that are not welcome inside a <p> body. Allowed inline tags:
# b, i, u, em, strong, mark, br, sub, sup.
UNWELCOME_HTML_REGEX = re.compile(
    r"</?(?:img|a|div|span|table|thead|tbody|tr|td|th|iframe|style|script|link|embed|object|"
    r"svg|video|audio|source|picture|figure|figcaption|form|input|select|textarea|button|"
    r"canvas|map|area|meta|base|section|article|aside|nav|header|footer|main|details|summary|"
    r"dialog|pre|code|blockquote|ol|ul|li|dl|dt|dd|hr|font|center)\b[^>]*>",
    re.IGNORECASE,
)
UNWELCOME_HTML_FLAG_LABEL = "Unwelcome HTML detected"

# A <p ...>...</p> block, capturing the class attr (if any) and inner content.
_P_BLOCK = re.compile(r'<p(?:\s+class="([^"]*)")?[^>]*>([\s\S]*?)</p>', re.IGNORECASE)
# A previously auto-scrub-flagged paragraph (has our flag note).
_FLAGGED_P = re.compile(
    r'<p\s+class="([^"]*)"([^>]*data-flag-note="(?:Invalid cue code|Unwelcome HTML detected)"[^>]*)>([\s\S]*?)</p>',
    re.IGNORECASE,
)
_FRONTMATTER = re.compile(r"^\s*---\s*\n.*?\n---\s*\n?", re.DOTALL)
_LEADING_DASH = re.compile(r"^\s*[-–—]")  # -, en-dash, em-dash


@dataclass
class ScrubSettings:
    """Admin-configured toggles (mirror of showbuild_interface_settings)."""
    enabled: bool = True
    strip_spans: bool = True
    remove_leading_dashes: bool = True
    clean_whitespace: bool = True

    interval: int = 30

    @classmethod
    def from_dict(cls, d: Optional[dict]) -> "ScrubSettings":
        """Build from a settings dict. Accepts both the snake_case server keys
        (InterfaceSettings: autoscrub_enabled, …) and the legacy camelCase
        localStorage keys (autoscrubEnabled / autoformatEnabled, …)."""
        d = d or {}

        def pick(*keys, default=True):
            for k in keys:
                if k in d and d[k] is not None:
                    return d[k] is not False
            return default

        def pick_int(*keys, default=30):
            for k in keys:
                if k in d and d[k] is not None:
                    try:
                        return int(d[k])
                    except (TypeError, ValueError):
                        pass
            return default

        return cls(
            enabled=pick("autoscrub_enabled", "autoscrubEnabled", "autoformatEnabled"),
            strip_spans=pick("autoscrub_strip_spans", "autoscrubStripSpans", "autoformatStripSpans"),
            remove_leading_dashes=pick("autoscrub_remove_leading_dashes", "autoscrubRemoveLeadingDashes", "autoformatRemoveLeadingDashes"),
            clean_whitespace=pick("autoscrub_clean_whitespace", "autoscrubCleanWhitespace", "autoformatCleanWhitespace"),
            interval=pick_int("autoscrub_interval", "autoscrubInterval", "autoformatInterval"),
        )


def load_scrub_settings() -> ScrubSettings:
    """Read the admin-configured Autoscrub settings from the DB-backed interface
    settings. Safe to call from a Celery worker or a request handler. Falls back
    to defaults if settings can't be loaded."""
    try:
        from routers.settings._shared import load_settings
        return ScrubSettings.from_dict((load_settings() or {}).get("interface"))
    except Exception:
        return ScrubSettings()


@dataclass
class ScrubResult:
    content: str
    changed: bool = False
    notes: list = field(default_factory=list)


def scrub_script_content(content: str, settings: Optional[ScrubSettings] = None) -> ScrubResult:
    """Normalize one script_content string. Returns the scrubbed text + whether
    anything changed. Faithful port of the client autoscrubContent rules."""
    if not isinstance(content, str) or not content:
        return ScrubResult(content=content or "", changed=False)

    s = settings or ScrubSettings()
    if not s.enabled:
        return ScrubResult(content=content, changed=False)

    out = content
    notes: list = []

    # STEP 0: strip YAML frontmatter (DB-first never stores it).
    if out.lstrip().startswith("---"):
        stripped = _FRONTMATTER.sub("", out, count=1)
        if stripped != out:
            out = stripped
            notes.append("stripped frontmatter")

    # STEP 1: strip spans/divs + convert bold/italic spans.
    if s.strip_spans:
        before = len(out)
        out = re.sub(r'<span id="docs-internal-guid-[^"]*">', "", out, flags=re.IGNORECASE)
        out = re.sub(r'<p dir="ltr"[^>]*>', "", out, flags=re.IGNORECASE)
        # Convert weight/style spans to <b>/<i> BEFORE stripping bare spans.
        out = re.sub(r"<span[^>]*font-weight:\s*700[^>]*>([\s\S]*?)</span>", r"<b>\1</b>", out, flags=re.IGNORECASE)
        out = re.sub(r"<span[^>]*font-weight:\s*bold[^>]*>([\s\S]*?)</span>", r"<b>\1</b>", out, flags=re.IGNORECASE)
        out = re.sub(r"<span[^>]*font-style:\s*italic[^>]*>([\s\S]*?)</span>", r"<i>\1</i>", out, flags=re.IGNORECASE)
        out = re.sub(r"<span[^>]*>", "", out, flags=re.IGNORECASE)
        out = re.sub(r"</span>", "", out, flags=re.IGNORECASE)
        out = re.sub(r"&lt;span[^&]*&gt;", "", out, flags=re.IGNORECASE)
        out = re.sub(r"&lt;/span&gt;", "", out, flags=re.IGNORECASE)
        out = re.sub(r"<div></div>", "", out, flags=re.IGNORECASE)
        out = re.sub(r"<div><br\s*/?></div>", "", out, flags=re.IGNORECASE)
        out = re.sub(r"<div[^>]*>", "", out, flags=re.IGNORECASE)
        out = re.sub(r"</div>", "", out, flags=re.IGNORECASE)
        out = re.sub(r"<p([^>]*)>\s+", r"<p\1>", out, flags=re.IGNORECASE)
        out = re.sub(r"\s+</p>", "</p>", out, flags=re.IGNORECASE)
        if len(out) != before:
            notes.append("stripped spans/divs")

    # STEP 1b: clean whitespace.
    if s.clean_whitespace:
        before = len(out)
        out = re.sub(r"&nbsp;", " ", out, flags=re.IGNORECASE)
        out = re.sub(r"  +", " ", out)
        if len(out) != before:
            notes.append("cleaned whitespace")

    # STEP 3: remove leading dashes (unless the paragraph is a dash list).
    if s.remove_leading_dashes:
        def _dedash(m):
            speaker = m.group(1) or "josh"
            inner = m.group(2)
            if not _LEADING_DASH.match(inner):
                return m.group(0)
            lines = [l for l in inner.split("\n") if l.strip()]
            dash_lines = [l for l in lines if _LEADING_DASH.match(l)]
            is_list = len(dash_lines) >= 2 and len(dash_lines) == len(lines)
            if is_list:
                return m.group(0)
            cleaned = re.sub(r"^\s*[-–—]\s*", "", inner)
            new_tag = f'<p class="{speaker}">{cleaned}</p>'
            return new_tag if new_tag != m.group(0) else m.group(0)

        new_out = _P_BLOCK.sub(_dedash, out)
        if new_out != out:
            out = new_out
            notes.append("removed leading dashes")

    # STEP 3b: flag invalid cues / unwelcome HTML.
    def _flag(m):
        full = m.group(0)
        speaker = m.group(1) or "josh"
        inner = m.group(2)
        plain = re.sub(r"<[^>]+>", "", inner)
        if plain.strip().startswith("***"):
            return full
        reason = None
        if LEGACY_CUE_REGEX.search(plain):
            reason = LEGACY_CUE_FLAG_LABEL
        elif UNWELCOME_HTML_REGEX.search(inner):
            reason = UNWELCOME_HTML_FLAG_LABEL
        if not reason:
            return full
        attrs = "" if "data-needs-attention" in full else ' data-needs-attention="true"'
        note = "" if "data-flag-note" in full else f' data-flag-note="{reason}"'
        return f'<p class="{speaker}"{attrs}{note}>*** {inner}</p>'

    new_out = _P_BLOCK.sub(_flag, out)
    if new_out != out:
        out = new_out
        notes.append("flagged invalid content")

    # STEP 3c: un-flag paragraphs whose offending content is gone.
    def _unflag(m):
        speaker = m.group(1) or "josh"
        inner = m.group(3)
        plain = re.sub(r"<[^>]+>", "", inner)
        still_cue = bool(LEGACY_CUE_REGEX.search(plain))
        still_html = bool(UNWELCOME_HTML_REGEX.search(inner))
        if still_cue or still_html:
            return m.group(0)
        cleaned = re.sub(r"^\*\*\*\s*", "", inner)
        return f'<p class="{speaker}">{cleaned}</p>'

    new_out = _FLAGGED_P.sub(_unflag, out)
    if new_out != out:
        out = new_out
        notes.append("cleared resolved flags")

    return ScrubResult(content=out, changed=(out != content), notes=notes)


# ---------------------------------------------------------------------------
# Celery beat task — normalize idle rundown items across active episodes.
# Registered in app/celery_app.py beat_schedule. The save endpoint handles the
# focused item; this catches items edited by other users / never opened, and
# items pasted into before the client save lands. Items touched in the last
# 2 minutes are SKIPPED so we never rewrite something being actively edited.
# ---------------------------------------------------------------------------
try:
    from celery import shared_task
except Exception:  # celery not importable in some contexts (tests) — task optional
    shared_task = None


def _scrub_idle_items_impl(limit: int = 200) -> dict:
    from database import SessionLocal
    from sqlalchemy import text

    settings = load_scrub_settings()
    if not settings.enabled:
        return {"status": "disabled", "scrubbed": 0, "scanned": 0}

    db = SessionLocal()
    scrubbed = 0
    scanned = 0
    try:
        rows = db.execute(text("""
            SELECT ri.asset_id, ri.script_content
            FROM rundown_items ri
            JOIN rundowns r ON r.id = ri.rundown_id
            JOIN episodes e ON e.id = r.episode_id
            WHERE e.status IN ('draft', 'production')
              AND ri.script_content IS NOT NULL
              AND LENGTH(ri.script_content) > 0
              AND ri.updated_at < NOW() - INTERVAL '2 minutes'
            ORDER BY ri.updated_at ASC
            LIMIT :lim
        """), {"lim": limit}).fetchall()

        for row in rows:
            scanned += 1
            result = scrub_script_content(row.script_content or "", settings)
            if not result.changed:
                continue
            # Re-check the row hasn't been touched since we read it (avoid
            # clobbering an edit that started mid-sweep), then write.
            upd = db.execute(text("""
                UPDATE rundown_items
                SET script_content = :sc, updated_at = updated_at
                WHERE asset_id = :aid
                  AND updated_at < NOW() - INTERVAL '2 minutes'
            """), {"sc": result.content, "aid": row.asset_id})
            if upd.rowcount:
                scrubbed += 1
                logger.info(f"[scrub-sweep] {row.asset_id}: {', '.join(result.notes)}")
        db.commit()
        return {"status": "ok", "scanned": scanned, "scrubbed": scrubbed}
    except Exception as e:
        db.rollback()
        logger.error(f"[scrub-sweep] failed: {e}")
        return {"status": "error", "error": str(e), "scanned": scanned, "scrubbed": scrubbed}
    finally:
        db.close()


if shared_task is not None:
    @shared_task(name="services.script_scrub_service.sweep_idle_items_for_scrub")
    def sweep_idle_items_for_scrub(limit: int = 200) -> dict:
        """Beat task: normalize idle rundown items (>2min since last edit)."""
        return _scrub_idle_items_impl(limit)
