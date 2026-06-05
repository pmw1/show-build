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

import re
from dataclasses import dataclass, field
from typing import Optional

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

    @classmethod
    def from_dict(cls, d: Optional[dict]) -> "ScrubSettings":
        d = d or {}

        def pick(*keys, default=True):
            for k in keys:
                if k in d and d[k] is not None:
                    return d[k] is not False
            return default

        return cls(
            enabled=pick("autoscrubEnabled", "autoformatEnabled"),
            strip_spans=pick("autoscrubStripSpans", "autoformatStripSpans"),
            remove_leading_dashes=pick("autoscrubRemoveLeadingDashes", "autoformatRemoveLeadingDashes"),
            clean_whitespace=pick("autoscrubCleanWhitespace", "autoformatCleanWhitespace"),
        )


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
