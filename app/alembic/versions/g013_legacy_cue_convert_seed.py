"""Seed api_configs rows for the Legacy Cue Convert module.

Two rows are seeded:
  - service='legacy_cue_convert', config_key='model'
      Default LLM model for the find-media tiebreaker. Picked up by
      get_ollama_model(db, purpose='legacy_cue_match') via the
      task_service_map extension in auto_description_service.py.

  - service='legacy_cue_convert', config_key='media_match_prompt'
      Editable prompt template (with {{type}}, {{slug}}, {{file_list}})
      used by /api/legacy-cue-convert/find-media when the deterministic
      fuzzy match doesn't produce a clear winner.

PostgreSQL dollar-quoted strings ($$...$$) avoid escaping the prompt body's
double quotes / newlines / curly braces.

Revision ID: g013_legacy_cue_convert_seed
Revises: g012_user_location
"""
from alembic import op


revision = 'g013_legacy_cue_convert_seed'
down_revision = 'g012_user_location'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
        INSERT INTO api_configs (workflow, category, service, config_key, config_value, is_enabled)
        VALUES (
            'generation', 'llm', 'legacy_cue_convert', 'model',
            'qwen2.5:latest',
            true
        )
        ON CONFLICT (workflow, category, service, config_key) DO NOTHING;
    """)
    op.execute(r"""
        INSERT INTO api_configs (workflow, category, service, config_key, config_value, is_enabled)
        VALUES (
            'generation', 'llm', 'legacy_cue_convert', 'media_match_prompt',
            $LCC$You are matching a script cue slug to a media filename in a TV-show production folder.

Cue type: {{type}}
Cue slug: {{slug}}
Available filenames in the preshow folder:
{{file_list}}

Pick the filename whose stem most likely refers to the same media as the cue slug.
Respond with ONLY the exact filename, or the single word "none" if no candidate is a likely match.
Do not include extensions in the response unless they are part of the filename. Do not explain.
$LCC$,
            true
        )
        ON CONFLICT (workflow, category, service, config_key) DO NOTHING;
    """)


def downgrade():
    op.execute("""
        DELETE FROM api_configs
        WHERE workflow = 'generation'
          AND category = 'llm'
          AND service = 'legacy_cue_convert'
          AND config_key IN ('model', 'media_match_prompt');
    """)
