"""init_schema

Revision ID: 9d94c566de79
Revises: 
Create Date: 2025-12-28 18:34:32.498379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d94c566de79'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create assets, market_data, and corporate_actions tables."""

    # Create assets table
    op.create_table(
        'assets',
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('exchange', sa.String(10), nullable=False),
        sa.Column('asset_type', sa.String(20), nullable=False, server_default='Common Stock'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('last_synced', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('symbol'),
    )
    op.create_index('ix_assets_symbol', 'assets', ['symbol'])
    op.create_index('ix_assets_is_active', 'assets', ['is_active'])

    # Create market_data table (will be converted to hypertable)
    op.create_table(
        'market_data',
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('open', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('high', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('low', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('close', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('adjusted_close', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('volume', sa.BigInteger, nullable=False),
        sa.PrimaryKeyConstraint('time', 'symbol'),
    )
    op.create_index('idx_market_data_symbol_time', 'market_data', ['symbol', 'time'], postgresql_using='brin')

    # Create corporate_actions table
    op.create_table(
        'corporate_actions',
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('action_type', sa.String(20), nullable=False),
        sa.Column('value', sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column('currency', sa.String(3), nullable=True, server_default='USD'),
        sa.PrimaryKeyConstraint('date', 'symbol'),
    )
    op.create_index('idx_corp_actions_symbol_date', 'corporate_actions', ['symbol', 'date'])

    # Convert market_data to TimescaleDB hypertable
    op.execute("""
        SELECT create_hypertable(
            'market_data',
            'time',
            if_not_exists => TRUE,
            chunk_time_interval => INTERVAL '1 month'
        );
    """)

    # Enable compression (optional, for storage optimization)
    op.execute("""
        ALTER TABLE market_data SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'symbol',
            timescaledb.compress_orderby = 'time DESC'
        );
    """)


def downgrade() -> None:
    """Downgrade schema: Drop all tables."""
    # Drop tables in reverse order of creation
    op.drop_table('corporate_actions')
    op.drop_table('market_data')
    op.drop_table('assets')
