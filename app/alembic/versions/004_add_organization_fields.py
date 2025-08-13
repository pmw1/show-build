"""add comprehensive organization fields

Revision ID: 004
Revises: 003
Create Date: 2025-08-10 05:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add comprehensive organization fields
    
    # Rename existing 'name' to 'legal_name' 
    op.alter_column('organizations', 'name', new_column_name='legal_name')
    
    # Add new name fields
    op.add_column('organizations', sa.Column('name', sa.String(255), nullable=True))
    op.add_column('organizations', sa.Column('trade_name', sa.String(255), nullable=True))
    
    # Add organization type and classification
    op.add_column('organizations', sa.Column('organization_type', sa.String(50), nullable=True))  # LLC, Corp, etc
    op.add_column('organizations', sa.Column('industry', sa.String(100), nullable=True))
    op.add_column('organizations', sa.Column('sector', sa.String(100), nullable=True))
    
    # Add identification numbers
    op.add_column('organizations', sa.Column('registration_number', sa.String(100), nullable=True))
    op.add_column('organizations', sa.Column('tax_id', sa.String(50), nullable=True))
    
    # Add contact information
    op.add_column('organizations', sa.Column('address_line1', sa.String(255), nullable=True))
    op.add_column('organizations', sa.Column('address_line2', sa.String(255), nullable=True))
    op.add_column('organizations', sa.Column('city', sa.String(100), nullable=True))
    op.add_column('organizations', sa.Column('state_province', sa.String(100), nullable=True))
    op.add_column('organizations', sa.Column('postal_code', sa.String(20), nullable=True))
    op.add_column('organizations', sa.Column('country', sa.String(100), nullable=False, server_default='United States'))
    
    op.add_column('organizations', sa.Column('phone', sa.String(30), nullable=True))
    op.add_column('organizations', sa.Column('email', sa.String(255), nullable=True))
    op.add_column('organizations', sa.Column('website', sa.String(255), nullable=True))
    
    # Add operational data
    op.add_column('organizations', sa.Column('founded_date', sa.Date(), nullable=True))
    op.add_column('organizations', sa.Column('number_of_employees', sa.Integer(), nullable=True))
    op.add_column('organizations', sa.Column('annual_revenue', sa.BigInteger(), nullable=True))  # Store in cents
    op.add_column('organizations', sa.Column('status', sa.String(20), nullable=False, server_default='active'))
    
    # Add system tracking
    op.add_column('organizations', sa.Column('created_by', sa.String(100), nullable=True))
    op.add_column('organizations', sa.Column('notes', sa.Text(), nullable=True))
    
    # Update existing Polaris Broadcasting record to set name from legal_name
    op.execute("UPDATE organizations SET name = legal_name WHERE legal_name = 'Polaris Broadcasting'")


def downgrade():
    # Remove all added columns
    op.drop_column('organizations', 'notes')
    op.drop_column('organizations', 'created_by')
    op.drop_column('organizations', 'status')
    op.drop_column('organizations', 'annual_revenue')
    op.drop_column('organizations', 'number_of_employees')
    op.drop_column('organizations', 'founded_date')
    op.drop_column('organizations', 'website')
    op.drop_column('organizations', 'email')
    op.drop_column('organizations', 'phone')
    op.drop_column('organizations', 'country')
    op.drop_column('organizations', 'postal_code')
    op.drop_column('organizations', 'state_province')
    op.drop_column('organizations', 'city')
    op.drop_column('organizations', 'address_line2')
    op.drop_column('organizations', 'address_line1')
    op.drop_column('organizations', 'tax_id')
    op.drop_column('organizations', 'registration_number')
    op.drop_column('organizations', 'sector')
    op.drop_column('organizations', 'industry')
    op.drop_column('organizations', 'organization_type')
    op.drop_column('organizations', 'trade_name')
    op.drop_column('organizations', 'name')
    
    # Rename legal_name back to name
    op.alter_column('organizations', 'legal_name', new_column_name='name')