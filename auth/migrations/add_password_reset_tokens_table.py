"""Add password_reset_tokens table.

Revision ID: add_password_reset_tokens
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_password_reset_tokens'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create password_reset_tokens table."""
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_user_id', 'password_reset_tokens', ['user_id'])
    op.create_index('idx_token', 'password_reset_tokens', ['token'])
    op.create_index('idx_expires_at', 'password_reset_tokens', ['expires_at'])
    op.create_index('idx_user_id_expires_at', 'password_reset_tokens', ['user_id', 'expires_at'])
    op.create_index('idx_token_expires_at', 'password_reset_tokens', ['token', 'expires_at'])
    
    # Create unique constraint on token
    op.create_unique_constraint('uq_token', 'password_reset_tokens', ['token'])


def downgrade() -> None:
    """Drop password_reset_tokens table."""
    op.drop_table('password_reset_tokens')
