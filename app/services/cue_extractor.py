"""Server-side cue extraction from rundown_items.script_content.

Mirrors the cue-block parsing half of
`disaffected-ui/src/utils/cueParser.js` (CueParser.parseContent +
parseCueBlock). Used by GET /api/episodes/{n}/rundown to surface
structured cues alongside the markdown script body, so downstream
consumers (showtime, vmix-promoter) don't have to port the parser.

Returns a list of dicts in declared cue order. Field names match
showtime's `Cue` pydantic model (sort_order, cue_type, title, trigger,
offset_seconds, status) so consumers can pass the dict straight into
`Cue(**c)` after dropping show-build-only fields:

    [
      {
        # showtime-aligned fields
        "sort_order": 0,
        "cue_type": "GFX",
        "title": "GFX: open-graphic",     # show-build slug or description
        "trigger": "manual",                # showtime default
        "offset_seconds": None,             # show-build doesn't track this
        "status": "pending",                # showtime default
        # show-build-native fields
        "slug": "open-graphic",
        "asset_id": "GFX...",
        "duration": "00:00:15:00",
        "description": "...",
        "media_url": "...",
        "thumbnail_url": "...",
        "audio_url": "...",
        "image_src": "...",
        "quote": "...",
        "attribution": "...",
        "fields": { ... all parsed fields, camelCase keys ... },
        # legacy aliases kept for backward compat (will be removed
        # after 2026-Q3 if no consumers remain):
        "order": 0,                         # alias of sort_order
        "type": "GFX",                      # alias of cue_type
      },
      ...
    ]

Reconstruction (segments → markdown) stays in JS; this module only
reads. If/when show-build owns full edit lifecycle on the server, mirror
the rest then.

See docs/SHOWTIME_INTEGRATION_ANALYSIS.md Gap A.
"""
from __future__ import annotations

import re
from typing import Any

_BEGIN = "<!-- Begin Cue -->"
_END = "<!-- End Cue -->"

# Field regex mirrors the JS one in cueParser.js:
#   /\[([^:\n\[\]]+):\s*([\s\S]*?)\](?=\s*(?:\n\s*\[|\n\s*<!--|$))/g
# Field name: no ':', no newline, no brackets. Value may span multiple
# lines; terminator is `]` followed by another `[`, an HTML comment
# (next cue marker), or end of content.
_FIELD_RE = re.compile(
    r"\[([^:\n\[\]]+):\s*([\s\S]*?)\](?=\s*(?:\n\s*\[|\n\s*<!--|$))",
)
_IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"[^>]*>')


def _to_camel(field_name: str) -> str:
    # Mirror cueParser.js toCamelCase: PascalCase → spaces, then split
    # on space/_/- and capitalize each piece after the first.
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", field_name)
    parts = re.split(r"[\s_\-]+", spaced)
    parts = [p for p in parts if p]
    if not parts:
        return ""
    out = [parts[0].lower()]
    for p in parts[1:]:
        out.append(p[0].upper() + p[1:].lower())
    return "".join(out)


def _parse_cue_block(cue_content: str) -> dict[str, Any] | None:
    """Parse one cue block body (text between Begin/End markers)."""
    if not cue_content:
        return None
    fields: dict[str, Any] = {}
    for m in _FIELD_RE.finditer(cue_content):
        name = m.group(1).strip()
        value = m.group(2).strip()
        # Strip surrounding quotes on Quote field (matches JS behavior).
        if name.lower() == "quote" and value:
            if value[:1] in ('"', "'"):
                value = value[1:]
            if value[-1:] in ('"', "'"):
                value = value[:-1]
        fields[_to_camel(name)] = value

    img_match = _IMG_RE.search(cue_content)
    if img_match:
        fields["imageTag"] = img_match.group(0)
        fields["imageSrc"] = img_match.group(1)

    if not fields.get("type"):
        return None
    return fields


def extract_cues(script_content: str | None) -> list[dict[str, Any]]:
    """Extract cue blocks from a markdown script. Returns a list of
    structured dicts in declared order, with a stable `order` index."""
    if not script_content or not isinstance(script_content, str):
        return []

    cues: list[dict[str, Any]] = []
    i = 0
    order = 0
    content = script_content

    while i < len(content):
        begin_idx = content.find(_BEGIN, i)
        if begin_idx == -1:
            break
        end_idx = content.find(_END, begin_idx + len(_BEGIN))
        next_begin_idx = content.find(_BEGIN, begin_idx + len(_BEGIN))
        malformed = (
            end_idx == -1
            or (next_begin_idx != -1 and next_begin_idx < end_idx)
        )
        if malformed:
            # Skip past this Begin marker only; do not consume the
            # next cue's content. The JS parser logs this as a
            # malformed cue; we silently skip on the server because
            # the editor will surface it on the next load.
            i = begin_idx + len(_BEGIN)
            continue

        cue_body = content[begin_idx + len(_BEGIN) : end_idx]
        parsed = _parse_cue_block(cue_body)
        if parsed is not None:
            cue_type = parsed.get("type")
            slug = parsed.get("slug")
            description = parsed.get("description")
            # Title: prefer description (human-readable), else slug,
            # else just the type. Mirrors cueParser.js generateCardTitle.
            if description:
                title = description
            elif slug:
                title = f"{cue_type}: {slug}" if cue_type else slug
            else:
                title = cue_type or "Unknown Cue"

            cues.append({
                # showtime-aligned fields (Cue pydantic model in
                # /home/kevin/showtime/backend/state/models.py:130)
                "sort_order": order,
                "cue_type": cue_type,
                "title": title,
                "trigger": "manual",
                "offset_seconds": None,
                "status": "pending",
                # show-build-native fields
                "slug": slug,
                "asset_id": parsed.get("assetId") or parsed.get("assetid"),
                "duration": parsed.get("duration"),
                "description": description,
                "media_url": parsed.get("mediaUrl") or parsed.get("mediaurl"),
                "thumbnail_url": (
                    parsed.get("thumbnailUrl") or parsed.get("thumbnailurl")
                ),
                "audio_url": parsed.get("audioUrl") or parsed.get("audiourl"),
                "image_src": parsed.get("imageSrc"),
                "quote": parsed.get("quote"),
                "attribution": parsed.get("attribution"),
                "fields": parsed,
                # legacy aliases (pre-c2c043 contract alignment 2026-05-20)
                "order": order,
                "type": cue_type,
            })
            order += 1

        i = end_idx + len(_END)

    return cues
