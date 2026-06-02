"""Add public-API publish lifecycle: timestamps, SEO overrides, access tiers, transcripts.

Per `docs/WEBSITE_PUBLIC_API_PLAN.md` (v13). All four blocker decisions are
resolved; this migration lays down everything the public API needs that
isn't already in the schema.

Adds:
- episodes: published_at, unpublished_at, seo_title, seo_description,
  canonical_url, access_tier (FK -> access_tiers.slug, default 'public')
- rundown_items: publish_status (default 'inherit'), seo_title,
  seo_description, og_poster_path, access_tier (default 'public')
- access_tiers (NEW): slug PK, name, rank UNIQUE, public bool — seeded
  with the single 'public' row at rank 0
- segment_transcripts (NEW): post-broadcast whisper+diarize output keyed
  to rundown_items, with text_plain/vtt/srt/json_diarized variants and a
  per-row published flag

Indexes:
- idx_episodes_published_status (partial: WHERE publish_status='published')
- uq_episodes_slug
- idx_rundown_items_episode_slug (unique on rundown_id + slug)

Decision references (Kevin, 2026-05-08):
- #5: script_content stays internal; transcripts live here, public segment
  text comes from this table
- #11: access_tier column lands now; full distribution-matrix
  (PUBLICATION_DESTINATIONS_PLAN.md) is out of scope for v1

Revision ID: g015_public_api_publish_lifecycle
Revises: g014_segment_llm_phase2
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'g015_public_api_publish_lifecycle'
down_revision = 'g014_segment_llm_phase2'
branch_labels = None
depends_on = None


def upgrade():
    # -----------------------------------------------------------------
    # 1. access_tiers lookup table (must come first — episodes + rundown_items
    #    will FK to it). Seeded with 'public' at rank 0.
    # -----------------------------------------------------------------
    op.create_table(
        'access_tiers',
        sa.Column('slug', sa.String(32), primary_key=True),
        sa.Column('name', sa.String(80), nullable=False),
        sa.Column('rank', sa.Integer, nullable=False),
        sa.Column('public', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('rank', name='uq_access_tiers_rank'),
    )
    op.execute(
        "INSERT INTO access_tiers (slug, name, rank, public) "
        "VALUES ('public', 'Public', 0, true)"
    )

    # -----------------------------------------------------------------
    # 2. Episodes: publish lifecycle + SEO overrides + access_tier
    # -----------------------------------------------------------------
    op.add_column('episodes', sa.Column('published_at', sa.DateTime(timezone=True)))
    op.add_column('episodes', sa.Column('unpublished_at', sa.DateTime(timezone=True)))
    op.add_column('episodes', sa.Column('seo_title', sa.String(200)))
    op.add_column('episodes', sa.Column('seo_description', sa.Text))
    op.add_column('episodes', sa.Column('canonical_url', sa.String(500)))
    op.add_column('episodes', sa.Column(
        'access_tier', sa.String(32),
        sa.ForeignKey('access_tiers.slug', name='fk_episodes_access_tier'),
        nullable=False, server_default='public',
    ))

    op.create_index(
        'idx_episodes_published_status',
        'episodes', ['publish_status', 'published_at'],
        postgresql_where=sa.text("publish_status = 'published'"),
    )
    op.create_unique_constraint('uq_episodes_slug', 'episodes', ['slug'])

    # -----------------------------------------------------------------
    # 3. Rundown items: per-segment publish flag + SEO + access_tier
    # -----------------------------------------------------------------
    op.add_column('rundown_items', sa.Column(
        'publish_status', sa.String(20),
        server_default='inherit', nullable=False,
    ))
    op.add_column('rundown_items', sa.Column('seo_title', sa.String(200)))
    op.add_column('rundown_items', sa.Column('seo_description', sa.Text))
    op.add_column('rundown_items', sa.Column('og_poster_path', sa.String(500)))
    op.add_column('rundown_items', sa.Column(
        'access_tier', sa.String(32),
        sa.ForeignKey('access_tiers.slug', name='fk_rundown_items_access_tier'),
        nullable=False, server_default='public',
    ))

    # -----------------------------------------------------------------
    # 3b. rundown_item_types lookup (drives publishable-slug uniqueness).
    #     Flag-driven so adding a new content type later is a row update,
    #     NOT a migration/index rebuild. Mirrors the access_tiers pattern.
    #     Seeded from RundownItemType enum; is_publishable marks the
    #     content-bearing types whose slugs become public URLs.
    # -----------------------------------------------------------------
    op.create_table(
        'rundown_item_types',
        sa.Column('slug', sa.String(40), primary_key=True),
        sa.Column('label', sa.String(80), nullable=False),
        sa.Column('is_publishable', sa.Boolean, nullable=False,
                  server_default=sa.text('false')),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    # (slug, label, is_publishable, sort_order)
    op.execute("""
        INSERT INTO rundown_item_types (slug, label, is_publishable, sort_order) VALUES
          ('segment',    'Segment',       true,  10),
          ('open',       'Open',          true,  20),
          ('coldopen',   'Cold Open',     true,  30),
          ('interview',  'Interview',     true,  40),
          ('package',    'Package',       true,  50),
          ('reader',     'Reader',        true,  60),
          ('tease',      'Tease',         false, 70),
          ('ad',         'Ad',            false, 80),
          ('promo',      'Promo',         false, 90),
          ('transition', 'Transition',    false, 100),
          ('stinger',    'Stinger',       false, 110),
          ('rejoin',     'Rejoin',        false, 120),
          ('close',      'Close',         false, 130),
          ('break',      'Break',         false, 140)
    """)

    # Data cleanup: legacy 'advertisement' -> canonical 'ad' (enum renamed it).
    op.execute("UPDATE rundown_items SET item_type = 'ad' WHERE item_type = 'advertisement'")

    # Uniqueness rule: slug must be unique WITHIN a rundown, but ONLY for
    # PUBLISHABLE item types (their slugs become public URLs) and only when a
    # slug is actually set. Structural items (ad/promo/tease/break/...) repeat
    # freely; blank/placeholder slugs are exempt until named.
    #
    # This is enforced by a trigger rather than a partial unique index because
    # the "publishable" set is FLAG-DRIVEN (rundown_item_types.is_publishable)
    # and Postgres partial-index predicates cannot contain a subquery. The
    # trigger consults the lookup table at write time, so flipping a type's
    # is_publishable flag changes enforcement instantly — no migration, no
    # index rebuild. Adding a new content type = insert/flag a lookup row.
    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_publishable_slug_unique()
        RETURNS trigger AS $$
        BEGIN
            -- Only enforce for publishable types with a non-empty slug.
            IF NEW.slug IS NULL OR NEW.slug = '' THEN
                RETURN NEW;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM rundown_item_types t
                WHERE t.slug = NEW.item_type AND t.is_publishable
            ) THEN
                RETURN NEW;
            END IF;
            IF EXISTS (
                SELECT 1 FROM rundown_items ri
                WHERE ri.rundown_id = NEW.rundown_id
                  AND ri.slug = NEW.slug
                  AND ri.id <> COALESCE(NEW.id, -1)
                  AND EXISTS (
                      SELECT 1 FROM rundown_item_types t2
                      WHERE t2.slug = ri.item_type AND t2.is_publishable
                  )
            ) THEN
                RAISE EXCEPTION
                  'duplicate publishable slug % in rundown % (item_type %)',
                  NEW.slug, NEW.rundown_id, NEW.item_type
                  USING ERRCODE = 'unique_violation';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_rundown_items_publishable_slug_unique
        BEFORE INSERT OR UPDATE OF slug, item_type, rundown_id
        ON rundown_items
        FOR EACH ROW
        EXECUTE FUNCTION enforce_publishable_slug_unique();
    """)
    # Non-unique helper index for the lookup/filter path the public API uses.
    op.create_index(
        'idx_rundown_items_episode_slug',
        'rundown_items', ['rundown_id', 'slug'],
    )

    # -----------------------------------------------------------------
    # 4. segment_transcripts: post-broadcast whisper + pyannote output
    # -----------------------------------------------------------------
    op.create_table(
        'segment_transcripts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column(
            'rundown_item_id', sa.Integer,
            sa.ForeignKey('rundown_items.id', ondelete='CASCADE',
                          name='fk_segment_transcripts_rundown_item'),
            nullable=False, index=True,
        ),
        sa.Column('language', sa.String(10),
                  nullable=False, server_default='en'),
        sa.Column('text_plain', sa.Text, nullable=False),
        sa.Column('vtt', sa.Text),
        sa.Column('srt', sa.Text),
        sa.Column('json_diarized', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('source', sa.String(40)),
        # 'whisper-medium', 'whisper-medium-diarized', 'manual', 'edited'
        sa.Column('generated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('published', sa.Boolean,
                  nullable=False, server_default=sa.text('false')),
        sa.UniqueConstraint(
            'rundown_item_id', 'language',
            name='uq_segment_transcripts_segment_lang',
        ),
    )


def downgrade():
    op.drop_table('segment_transcripts')

    op.drop_index('idx_rundown_items_episode_slug', table_name='rundown_items')
    op.execute("DROP TRIGGER IF EXISTS trg_rundown_items_publishable_slug_unique ON rundown_items")
    op.execute("DROP FUNCTION IF EXISTS enforce_publishable_slug_unique()")
    op.drop_table('rundown_item_types')
    op.drop_constraint('fk_rundown_items_access_tier', 'rundown_items', type_='foreignkey')
    op.drop_column('rundown_items', 'access_tier')
    op.drop_column('rundown_items', 'og_poster_path')
    op.drop_column('rundown_items', 'seo_description')
    op.drop_column('rundown_items', 'seo_title')
    op.drop_column('rundown_items', 'publish_status')

    op.drop_constraint('uq_episodes_slug', 'episodes', type_='unique')
    op.drop_index('idx_episodes_published_status', table_name='episodes')
    op.drop_constraint('fk_episodes_access_tier', 'episodes', type_='foreignkey')
    op.drop_column('episodes', 'access_tier')
    op.drop_column('episodes', 'canonical_url')
    op.drop_column('episodes', 'seo_description')
    op.drop_column('episodes', 'seo_title')
    op.drop_column('episodes', 'unpublished_at')
    op.drop_column('episodes', 'published_at')

    op.drop_table('access_tiers')
