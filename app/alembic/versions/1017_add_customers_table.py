"""Add customers table for advertiser/sponsor management

Revision ID: 1017_customers
Revises: 1016_add_scratch_content_to_content_library
Create Date: 2026-01-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '1017_customers'
down_revision = '1016_scratch_content'
branch_labels = None
depends_on = None


def upgrade():
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.String(50), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Company information
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),

        # Primary contact
        sa.Column('contact_name', sa.String(255), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('contact_title', sa.String(100), nullable=True),

        # Billing information
        sa.Column('billing_email', sa.String(255), nullable=True),
        sa.Column('billing_address', sa.Text(), nullable=True),

        # Relationship metadata
        sa.Column('customer_type', sa.String(50), server_default='advertiser'),
        sa.Column('tier', sa.String(50), server_default='standard'),
        sa.Column('notes', sa.Text(), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_customers_asset_id', 'customers', ['asset_id'], unique=True)
    op.create_index('ix_customers_company_name', 'customers', ['company_name'])
    op.create_index('ix_customers_organization_id', 'customers', ['organization_id'])
    op.create_index('ix_customers_is_active', 'customers', ['is_active'])


def downgrade():
    op.drop_index('ix_customers_is_active', table_name='customers')
    op.drop_index('ix_customers_organization_id', table_name='customers')
    op.drop_index('ix_customers_company_name', table_name='customers')
    op.drop_index('ix_customers_asset_id', table_name='customers')
    op.drop_table('customers')
