-- TASK #065: TimescaleDB Initialization Script
-- Phase 2 Data Infrastructure - Cold Path Factory
-- Protocol: v4.3 (Zero-Trust Edition)

-- ============================================================================
-- 1. Enable Required Extensions
-- ============================================================================

-- Enable TimescaleDB extension (required for hypertables)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- 2. Create Schemas
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS market_data;
COMMENT ON SCHEMA market_data IS 'EODHD market data (OHLCV, ticks)';

CREATE SCHEMA IF NOT EXISTS features;
COMMENT ON SCHEMA features IS 'Engineered features for ML models';

CREATE SCHEMA IF NOT EXISTS backtest;
COMMENT ON SCHEMA backtest IS 'Backtest results and performance metrics';

-- ============================================================================
-- 3. Create Tables - Market Data Layer
-- ============================================================================

-- Daily OHLCV data (cold path - bulk ingestion)
CREATE TABLE IF NOT EXISTS market_data.ohlcv_daily (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open NUMERIC(20, 8) NOT NULL,
    high NUMERIC(20, 8) NOT NULL,
    low NUMERIC(20, 8) NOT NULL,
    close NUMERIC(20, 8) NOT NULL,
    volume BIGINT NOT NULL,
    metadata JSONB
);

COMMENT ON TABLE market_data.ohlcv_daily IS 'Daily OHLCV data from EODHD bulk API';

-- Create indexes
CREATE INDEX idx_ohlcv_daily_symbol_time ON market_data.ohlcv_daily (symbol, time DESC);
CREATE INDEX idx_ohlcv_daily_time ON market_data.ohlcv_daily (time DESC);

-- Intraday tick data (high-frequency for strategy testing)
CREATE TABLE IF NOT EXISTS market_data.ticks (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price NUMERIC(20, 8) NOT NULL,
    volume BIGINT NOT NULL,
    bid NUMERIC(20, 8),
    ask NUMERIC(20, 8)
);

COMMENT ON TABLE market_data.ticks IS 'Intraday tick data for backtesting';

CREATE INDEX idx_ticks_symbol_time ON market_data.ticks (symbol, time DESC);

-- ============================================================================
-- 4. Convert to TimescaleDB Hypertables
-- ============================================================================

-- Convert OHLCV to hypertable with 1-week partitioning
SELECT create_hypertable(
    'market_data.ohlcv_daily',
    'time',
    if_not_exists => TRUE,
    time_partitioning_func => 'date_trunc'
);

-- Compression policy for older data (compress after 4 weeks)
SELECT add_compression_policy(
    'market_data.ohlcv_daily',
    INTERVAL '4 weeks',
    if_not_exists => TRUE
);

-- Convert ticks to hypertable with 1-day partitioning
SELECT create_hypertable(
    'market_data.ticks',
    'time',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 day'
);

-- ============================================================================
-- 5. Create Tables - Features Layer
-- ============================================================================

-- Technical indicators (engineered features)
CREATE TABLE IF NOT EXISTS features.technical_indicators (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    -- Momentum indicators
    rsi_14 NUMERIC(10, 4),
    macd NUMERIC(15, 8),
    macd_signal NUMERIC(15, 8),
    macd_hist NUMERIC(15, 8),

    -- Volatility indicators
    atr_14 NUMERIC(20, 8),
    bbands_upper NUMERIC(20, 8),
    bbands_middle NUMERIC(20, 8),
    bbands_lower NUMERIC(20, 8),

    -- Trend indicators
    sma_20 NUMERIC(20, 8),
    sma_50 NUMERIC(20, 8),
    sma_200 NUMERIC(20, 8),
    ema_12 NUMERIC(20, 8),
    ema_26 NUMERIC(20, 8),

    -- Volume indicators
    obv BIGINT,
    adx_14 NUMERIC(10, 4),

    -- Metadata
    calculated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

COMMENT ON TABLE features.technical_indicators IS 'Calculated technical indicators for all symbols';

-- Create hypertable
SELECT create_hypertable(
    'features.technical_indicators',
    'time',
    if_not_exists => TRUE
);

CREATE INDEX idx_technical_symbols_time ON features.technical_indicators (symbol, time DESC);

-- Sentiment features (to be populated from NLP models)
CREATE TABLE IF NOT EXISTS features.sentiment_scores (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    -- Sentiment from FinBERT
    finbert_sentiment NUMERIC(5, 4),
    finbert_confidence NUMERIC(5, 4),

    -- News sentiment aggregates
    daily_sentiment_mean NUMERIC(5, 4),
    daily_sentiment_std NUMERIC(5, 4),
    daily_news_count INTEGER,

    metadata JSONB
);

COMMENT ON TABLE features.sentiment_scores IS 'NLP-derived sentiment features from FinBERT';

SELECT create_hypertable(
    'features.sentiment_scores',
    'time',
    if_not_exists => TRUE
);

-- ============================================================================
-- 6. Create Tables - Backtest Results
-- ============================================================================

CREATE TABLE IF NOT EXISTS backtest.results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    -- Performance metrics
    total_return NUMERIC(10, 4),
    sharpe_ratio NUMERIC(8, 4),
    max_drawdown NUMERIC(10, 4),
    win_rate NUMERIC(5, 4),
    num_trades INTEGER,

    -- Execution details
    parameters JSONB,
    executed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,

    -- Metadata
    metadata JSONB
);

COMMENT ON TABLE backtest.results IS 'Vectorized backtest results from VectorBT';

CREATE INDEX idx_backtest_results_strategy_date ON backtest.results (strategy_name, start_date DESC);
CREATE INDEX idx_backtest_results_symbol_date ON backtest.results (symbol, start_date DESC);

-- Detailed trade log
CREATE TABLE IF NOT EXISTS backtest.trade_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtest_id UUID NOT NULL REFERENCES backtest.results(id) ON DELETE CASCADE,

    entry_time TIMESTAMPTZ NOT NULL,
    entry_price NUMERIC(20, 8) NOT NULL,
    entry_type TEXT NOT NULL, -- 'LONG' or 'SHORT'

    exit_time TIMESTAMPTZ,
    exit_price NUMERIC(20, 8),
    exit_type TEXT,

    quantity NUMERIC(15, 8) NOT NULL,
    commission NUMERIC(20, 8),
    pnl NUMERIC(20, 8),
    pnl_percent NUMERIC(10, 4),

    metadata JSONB
);

COMMENT ON TABLE backtest.trade_log IS 'Detailed per-trade execution log from backtest results';

CREATE INDEX idx_trade_log_backtest_time ON backtest.trade_log (backtest_id, entry_time DESC);

-- ============================================================================
-- 7. Create Role-Based Access Control (RBAC)
-- ============================================================================

-- Reader role (for feature queries)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'feature_reader') THEN
        CREATE ROLE feature_reader;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE mt5_data TO feature_reader;
GRANT USAGE ON SCHEMA market_data, features, backtest TO feature_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA market_data, features, backtest TO feature_reader;

-- Writer role (for ingestion)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_ingester') THEN
        CREATE ROLE data_ingester;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE mt5_data TO data_ingester;
GRANT USAGE ON SCHEMA market_data, features, backtest TO data_ingester;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA market_data, features, backtest TO data_ingester;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA backtest TO data_ingester;

-- ============================================================================
-- 8. Create Utility Functions
-- ============================================================================

-- Function to get latest price for a symbol
CREATE OR REPLACE FUNCTION market_data.get_latest_price(p_symbol TEXT)
RETURNS TABLE(price NUMERIC, time TIMESTAMPTZ) AS $$
    SELECT close, time
    FROM market_data.ohlcv_daily
    WHERE symbol = p_symbol
    ORDER BY time DESC
    LIMIT 1;
$$ LANGUAGE SQL;

-- Function to calculate daily returns
CREATE OR REPLACE FUNCTION features.calculate_daily_returns(
    p_symbol TEXT,
    p_days INTEGER DEFAULT 252
)
RETURNS TABLE(
    trading_date DATE,
    daily_return NUMERIC,
    cumulative_return NUMERIC
) AS $$
    WITH daily_data AS (
        SELECT
            DATE(time) as trading_date,
            close,
            LAG(close) OVER (ORDER BY time) as prev_close
        FROM market_data.ohlcv_daily
        WHERE symbol = p_symbol
        ORDER BY time DESC
        LIMIT p_days
    )
    SELECT
        trading_date,
        CASE WHEN prev_close IS NOT NULL
            THEN (close - prev_close) / prev_close
            ELSE NULL
        END as daily_return,
        EXP(SUM(LN(close / NULLIF(prev_close, 0))) OVER (ORDER BY trading_date)) as cumulative_return
    FROM daily_data
    WHERE prev_close IS NOT NULL;
$$ LANGUAGE SQL;

-- ============================================================================
-- 9. Create Materialized Views for Common Queries
-- ============================================================================

-- Latest daily snapshot for all symbols
CREATE MATERIALIZED VIEW IF NOT EXISTS market_data.latest_snapshot AS
SELECT DISTINCT ON (symbol)
    symbol,
    time,
    close as price,
    volume,
    (close - open) / open * 100 as daily_change_pct
FROM market_data.ohlcv_daily
ORDER BY symbol, time DESC;

COMMENT ON MATERIALIZED VIEW market_data.latest_snapshot IS 'Latest price snapshot for all symbols';

-- ============================================================================
-- 10. Display Summary
-- ============================================================================

-- Print confirmation message
SELECT
    'TimescaleDB Initialization Complete' as status,
    COUNT(*) as extensions_loaded
FROM pg_extension
WHERE extname IN ('timescaledb', 'uuid-ossp', 'pgcrypto');
