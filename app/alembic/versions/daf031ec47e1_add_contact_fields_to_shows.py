"""Add contact fields to shows

Revision ID: daf031ec47e1
Revises: 2eb1d08987c1
Create Date: 2025-08-10 06:54:00.493842

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'daf031ec47e1'
down_revision = '2eb1d08987c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add contact fields to shows table
    op.add_column('shows', sa.Column('contact_name', sa.String(255), nullable=True))
    op.add_column('shows', sa.Column('contact_phone', sa.String(20), nullable=True))
    op.add_column('shows', sa.Column('contact_email', sa.String(255), nullable=True))


def downgrade() -> None:
    # Remove the contact columns
    op.drop_column('shows', 'contact_email')
    op.drop_column('shows', 'contact_phone')
    op.drop_column('shows', 'contact_name')