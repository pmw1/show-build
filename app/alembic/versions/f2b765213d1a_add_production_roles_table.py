"""add_production_roles_table

Revision ID: f2b765213d1a
Revises: 1021_segment_llm_data
Create Date: 2026-02-21 14:32:32.572365

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2b765213d1a'
down_revision = '1021_segment_llm_data'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'production_roles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
        sa.Column('display_order', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_production_roles_id', 'production_roles', ['id'])

    # Seed default roles
    op.execute("""
        INSERT INTO production_roles (name, display_order) VALUES
        ('Host', 1),
        ('Director', 2),
        ('Teleprompter', 3)
    """)


def downgrade() -> None:
    op.drop_index('ix_production_roles_id', table_name='production_roles')
    op.drop_table('production_roles')
