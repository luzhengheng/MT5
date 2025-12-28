"""
SQLAlchemy ORM Models for Data Nexus

Defines the database schema for:
- Asset management (tracking which symbols to sync)
- Market data (OHLC historical data as TimescaleDB hypertable)
- Corporate actions (splits and dividends)

All models use TimescaleDB with PostgreSQL backend.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Asset(Base):
    """
    Asset (Stock/ETF) master table.

    Manages the list of securities to be synced from EODHD.
    Since Bulk API is unavailable, we must track each asset's sync state.

    Columns:
        symbol: Ticker with exchange (e.g., AAPL.US) - Primary Key
        exchange: Exchange code (e.g., US, LSE, TSE)
        asset_type: Common Stock, ETF, Index, Preferred Stock, etc.
        is_active: Control whether to ingest this asset
        last_synced: Last successful EOD sync timestamp (for incremental updates)
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "assets"

    symbol = Column(String(20), primary_key=True, nullable=False, index=True)
    exchange = Column(String(10), nullable=False)
    asset_type = Column(String(20), nullable=False, default="Common Stock")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    last_synced = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships (without FK constraints for performance - denormalized design)
    # Note: These are query conveniences only, no database-level FK constraints
    market_data = relationship("MarketData", foreign_keys="[MarketData.symbol]", primaryjoin="Asset.symbol==MarketData.symbol", back_populates="asset")
    corporate_actions = relationship("CorporateAction", foreign_keys="[CorporateAction.symbol]", primaryjoin="Asset.symbol==CorporateAction.symbol", back_populates="asset")

    def __repr__(self) -> str:
        return f"<Asset(symbol={self.symbol}, exchange={self.exchange}, is_active={self.is_active})>"


class MarketData(Base):
    """
    OHLC Market Data - TimescaleDB Hypertable.

    Stores daily OHLC data from EODHD EOD endpoint.
    This table will be converted to a TimescaleDB hypertable for
    efficient time-series queries.

    Composite Primary Key: (time, symbol)
    - time: Trading date (TIMESTAMP WITH TIME ZONE) - TimescaleDB partition key
    - symbol: Stock ticker

    All prices are NUMERIC (exact decimal) for financial accuracy.

    Columns:
        time: Trading date/time in US/Eastern timezone
        symbol: Stock ticker (AAPL.US, etc.)
        open: Opening price
        high: Daily high price
        low: Daily low price
        close: Closing price
        adjusted_close: Price adjusted for splits and dividends
        volume: Trading volume in shares
    """

    __tablename__ = "market_data"

    time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    symbol = Column(String(20), primary_key=True, nullable=False)
    open = Column(Numeric(precision=12, scale=4), nullable=False)
    high = Column(Numeric(precision=12, scale=4), nullable=False)
    low = Column(Numeric(precision=12, scale=4), nullable=False)
    close = Column(Numeric(precision=12, scale=4), nullable=False)
    adjusted_close = Column(Numeric(precision=12, scale=4), nullable=False)
    volume = Column(BigInteger, nullable=False)

    __table_args__ = (
        # Index for efficient symbol-based queries
        Index("idx_market_data_symbol_time", "symbol", "time", postgresql_using="brin"),
        # TimescaleDB hypertable configuration (applied via Alembic)
        # This tells TimescaleDB to partition by 'time' column
        {"comment": "TimescaleDB hypertable: partitioned by time (monthly chunks)"},
    )

    # Relationship to asset (for query convenience)
    # Note: No FK constraint for performance; denormalized design
    asset = relationship("Asset", foreign_keys=[symbol], primaryjoin="Asset.symbol==MarketData.symbol", back_populates="market_data")

    def __repr__(self) -> str:
        return f"<MarketData(symbol={self.symbol}, time={self.time}, close={self.close})>"


class CorporateAction(Base):
    """
    Corporate Actions (Splits & Dividends).

    Tracks splits and dividends that affect adjusted_close calculation.
    Needed to understand why adjusted_close differs from close.

    Columns:
        date: Action date (affects trading on this date)
        symbol: Stock ticker
        action_type: 'SPLIT' or 'DIVIDEND'
        value: Split ratio (e.g., 2.0 for 2-for-1) or dividend amount
        currency: USD, GBP, etc. (for dividend dividends)
    """

    __tablename__ = "corporate_actions"

    date = Column(Date, primary_key=True, nullable=False)
    symbol = Column(String(20), primary_key=True, nullable=False)
    action_type = Column(String(20), nullable=False)  # SPLIT, DIVIDEND, ISIN_CHANGE, etc.
    value = Column(Numeric(precision=12, scale=6), nullable=False)
    currency = Column(String(3), nullable=True, default="USD")

    __table_args__ = (
        # Index for efficient symbol-date lookups
        Index("idx_corp_actions_symbol_date", "symbol", "date"),
    )

    # Relationship to asset (for query convenience)
    asset = relationship("Asset", foreign_keys=[symbol], primaryjoin="Asset.symbol==CorporateAction.symbol", back_populates="corporate_actions")

    def __repr__(self) -> str:
        return f"<CorporateAction(symbol={self.symbol}, date={self.date}, type={self.action_type}, value={self.value})>"
