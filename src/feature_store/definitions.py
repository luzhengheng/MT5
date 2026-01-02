from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource, ValueType
from feast.types import Float32

# 定义实体 (Entity)
ticker = Entity(
    name="ticker",
    value_type=ValueType.STRING,
    description="Financial Instrument Ticker (e.g., EURUSD, BTCUSD)"
)

# 定义数据源 (Batch Source)
batch_source = FileSource(
    path="data/sample_features.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)

# FeatureView 1: 移动平均线 (Moving Averages)
sma_features = FeatureView(
    name="sma_features",
    entities=[ticker],
    ttl=timedelta(hours=24),
    schema=[
        Field(name="sma_7", dtype=Float32),
        Field(name="sma_14", dtype=Float32),
        Field(name="sma_30", dtype=Float32),
    ],
    online=True,
    source=batch_source,
    tags={"category": "trend", "team": "quant"},
)

# FeatureView 2: RSI 指标 (Relative Strength Index)
rsi_features = FeatureView(
    name="rsi_features",
    entities=[ticker],
    ttl=timedelta(hours=24),
    schema=[
        Field(name="rsi_14", dtype=Float32),
        Field(name="rsi_21", dtype=Float32),
    ],
    online=True,
    source=batch_source,
    tags={"category": "momentum", "team": "quant"},
)

# FeatureView 3: MACD 指标
macd_features = FeatureView(
    name="macd_features",
    entities=[ticker],
    ttl=timedelta(hours=24),
    schema=[
        Field(name="macd", dtype=Float32),
        Field(name="macd_signal", dtype=Float32),
        Field(name="macd_hist", dtype=Float32),
    ],
    online=True,
    source=batch_source,
    tags={"category": "momentum", "team": "quant"},
)

# FeatureView 4: 布林带 (Bollinger Bands)
bbands_features = FeatureView(
    name="bbands_features",
    entities=[ticker],
    ttl=timedelta(hours=24),
    schema=[
        Field(name="bbands_upper", dtype=Float32),
        Field(name="bbands_middle", dtype=Float32),
        Field(name="bbands_lower", dtype=Float32),
        Field(name="bbands_width", dtype=Float32),
    ],
    online=True,
    source=batch_source,
    tags={"category": "volatility", "team": "quant"},
)

# FeatureView 5: ATR 波动率 (Average True Range)
atr_features = FeatureView(
    name="atr_features",
    entities=[ticker],
    ttl=timedelta(hours=24),
    schema=[
        Field(name="atr_14", dtype=Float32),
    ],
    online=True,
    source=batch_source,
    tags={"category": "volatility", "team": "quant"},
)

# FeatureView 6: 随机震荡指标 (Stochastic)
stochastic_features = FeatureView(
    name="stochastic_features",
    entities=[ticker],
    ttl=timedelta(hours=24),
    schema=[
        Field(name="stochastic_k", dtype=Float32),
        Field(name="stochastic_d", dtype=Float32),
    ],
    online=True,
    source=batch_source,
    tags={"category": "momentum", "team": "quant"},
)
