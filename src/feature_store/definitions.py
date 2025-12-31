#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feast Feature Store Definitions
=================================

定义 market_features 表的 Entity 和 FeatureView，将 EAV 长格式转换为宽格式。

协议: v2.2 (本地存储，文档优先)
"""

from datetime import timedelta
from feast import Entity, FeatureView, FeatureService, Field
from feast.infra.offline_stores.postgres import PostgreSQLOfflineStoreConfig
from feast.types import Float64, String
import yaml
from pathlib import Path

# ============================================================================
# 配置加载
# ============================================================================

def load_config():
    """加载 feature_store.yaml 配置"""
    config_path = Path(__file__).parent / "feature_store.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

config = load_config()

# ============================================================================
# Entity: 交易对符号 (symbol)
# ============================================================================

symbol_entity = Entity(
    name="symbol",
    description="交易对符号 (EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, GSPC, DJI)",
    join_keys=["symbol"],
)

# ============================================================================
# FeatureView: 市场特征视图
# ============================================================================

# SQL 查询: 将 EAV 长格式转换为宽格式
MARKET_FEATURES_WIDE_SQL = """
SELECT
    time,
    symbol,
    MAX(CASE WHEN feature='sma_20' THEN value END)::double precision as sma_20,
    MAX(CASE WHEN feature='sma_50' THEN value END)::double precision as sma_50,
    MAX(CASE WHEN feature='sma_200' THEN value END)::double precision as sma_200,
    MAX(CASE WHEN feature='rsi_14' THEN value END)::double precision as rsi_14,
    MAX(CASE WHEN feature='macd_line' THEN value END)::double precision as macd_line,
    MAX(CASE WHEN feature='macd_signal' THEN value END)::double precision as macd_signal,
    MAX(CASE WHEN feature='macd_histogram' THEN value END)::double precision as macd_histogram,
    MAX(CASE WHEN feature='atr_14' THEN value END)::double precision as atr_14,
    MAX(CASE WHEN feature='bb_upper' THEN value END)::double precision as bb_upper,
    MAX(CASE WHEN feature='bb_middle' THEN value END)::double precision as bb_middle,
    MAX(CASE WHEN feature='bb_lower' THEN value END)::double precision as bb_lower
FROM market_features
GROUP BY time, symbol
"""

market_features_view = FeatureView(
    name="market_features",
    entities=[symbol_entity],
    ttl=timedelta(days=90),
    tags={
        "data_source": "TimescaleDB/market_features",
        "feature_type": "technical_indicators",
        "num_features": "11",
        "assets": "7"
    },
    schema=[
        Field(name="time", dtype=String),
        Field(name="sma_20", dtype=Float64),
        Field(name="sma_50", dtype=Float64),
        Field(name="sma_200", dtype=Float64),
        Field(name="rsi_14", dtype=Float64),
        Field(name="macd_line", dtype=Float64),
        Field(name="macd_signal", dtype=Float64),
        Field(name="macd_histogram", dtype=Float64),
        Field(name="atr_14", dtype=Float64),
        Field(name="bb_upper", dtype=Float64),
        Field(name="bb_middle", dtype=Float64),
        Field(name="bb_lower", dtype=Float64),
    ],
    # 使用 SQL 查询读取转换后的宽格式数据
    online=False,  # 仅离线存储
)

# ============================================================================
# Feature Service: 批量特征服务
# ============================================================================

market_features_service = FeatureService(
    name="market_features_service",
    features=[market_features_view],
    tags={
        "team": "trading_research",
        "sla": "batch_processing"
    }
)

# ============================================================================
# 导出符号
# ============================================================================

__all__ = [
    "symbol_entity",
    "market_features_view",
    "market_features_service",
    "MARKET_FEATURES_WIDE_SQL"
]
