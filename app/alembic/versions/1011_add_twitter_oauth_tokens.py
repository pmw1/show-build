"""add_twitter_oauth_tokens

Revision ID: 1011_add_oauth_tokens
Revises: 1010_add_title_field
Create Date: 2025-10-16 05:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '1011_add_oauth_tokens'
down_revision = '1010_add_title_field'
branch_labels = None
depends_on = None


def upgrade():
    # Create table for storing Twitter OAuth tokens
    op.create_table(
        'twitter_oauth_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_type', sa.String(50), nullable=False, server_default='Bearer'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('twitter_user_id', sa.String(100), nullable=True),
        sa.Column('twitter_username', sa.String(100), nullable=True),
        sa.Column('twitter_name', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_twitter_oauth_tokens_user_id', 'user_id')
    )


def downgrade():
    op.drop_table('twitter_oauth_tokens')
