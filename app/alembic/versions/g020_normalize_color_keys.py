"""Normalize / de-pollute the theme_colors_default settings profile.

The color picker historically wrote each color slot under BOTH a canonical
lowercase key (e.g. 'selection') AND a PascalCase + suffix key
(e.g. 'Selection-interface'), polluting the single global color profile with
duplicate keys for every concept. The canonical lowercase keys are now the only
source of truth (see colorRegistry.js). This migration rewrites that one
settings row, folding the legacy keys into canonical ones (canonical wins on
collision) and dropping the redundant legacy keys.

Read-time normalization already exists in both the frontend
(themeColorMap.loadColorsFromDatabase) and backend
(settings_colors_router.normalize_color_keys), so the app renders correctly
regardless; this migration cleans the stored data so future writes start clean.

Affects only the single global row: key='theme_colors_default',
category='colors', user_id IS NULL. Data-only; downgrade is a no-op.

Revision ID: g020_normalize_color_keys
Revises: g018_triggers_table
Create Date: 2026-06-04
"""
import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'g020_normalize_color_keys'
down_revision = 'g018_triggers_table'
branch_labels = None
depends_on = None


# Keep in sync with colorRegistry.js `legacyKeys` and
# settings_colors_router.LEGACY_COLOR_KEY_MAP.
LEGACY_COLOR_KEY_MAP = {
    "selection-interface": "selection",
    "hover-interface": "hover",
    "highlight-interface": "highlight",
    "dropline-interface": "dropline",
    "draglight-interface": "draglight",
    "locatorflash-interface": "locatorflash",
    "draft-script": "draft",
    "approved-script": "approved",
    "production-script": "production",
    "promotion-script": "promotion",
    "scheduled-script": "scheduled",
    "running-script": "running",
    "completed-script": "completed",
    "autosave-global": "autosave",
    "needs-attention-global": "needs-attention",
    "block-header-ui": "block-header",
}


def _normalize(raw_colors):
    """Lowercase keys, fold legacy -> canonical; canonical wins on collision."""
    if not isinstance(raw_colors, dict):
        return {}
    out = {}
    canonical_seen = set()
    for key, value in raw_colors.items():
        lower = str(key).lower()
        if lower in LEGACY_COLOR_KEY_MAP:
            continue
        out[lower] = value
        canonical_seen.add(lower)
    for key, value in raw_colors.items():
        lower = str(key).lower()
        canonical = LEGACY_COLOR_KEY_MAP.get(lower)
        if canonical and canonical not in canonical_seen:
            out[canonical] = value
    return out


def upgrade():
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT id, value FROM settings "
            "WHERE category = 'colors' AND user_id IS NULL "
            "AND key LIKE 'theme_colors_%'"
        )
    ).fetchall()

    for row in rows:
        value = row[1]
        # value is JSON; SQLAlchemy may hand it back as dict or str depending on column type.
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (ValueError, TypeError):
                continue
        cleaned = _normalize(value)
        # Cast the bound string to json so Postgres stores the object, not a
        # double-encoded JSON string (the `value` column is type `json`).
        bind.execute(
            sa.text("UPDATE settings SET value = CAST(:val AS json) WHERE id = :id"),
            {"val": json.dumps(cleaned), "id": row[0]},
        )


def downgrade():
    # No-op: legacy keys were redundant duplicates; nothing depends on them.
    pass
