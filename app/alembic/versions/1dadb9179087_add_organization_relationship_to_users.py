"""Add organization relationship to users

Revision ID: 1dadb9179087
Revises: 004
Create Date: 2025-08-10 06:36:55.524451

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1dadb9179087'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add organization_id foreign key to users table
    op.add_column('users', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_organization', 'users', 'organizations', ['organization_id'], ['id'])
    
    # Update kevin user to be linked to Polaris Broadcasting (organization id = 1)
    op.execute("UPDATE users SET organization_id = 1 WHERE username = 'kevin'")


def downgrade() -> None:
    # Remove foreign key and column
    op.drop_constraint('fk_users_organization', 'users', type_='foreignkey')
    op.drop_column('users', 'organization_id')