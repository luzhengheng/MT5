from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource, ValueType
from feast.types import Float32

# 定义实体 (关键修复: value_type 必须使用 ValueType.STRING 枚举)
ticker = Entity(
    name="ticker", 
    value_type=ValueType.STRING, 
    description="Financial Instrument Ticker"
)

# 定义数据源 (指向样本 parquet)
batch_source = FileSource(
    path="/opt/mt5-crs/data/sample_features.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)

# 定义特征视图 (Schema 中继续使用新版 Float32 类型)
market_features = FeatureView(
    name="market_features",
    entities=[ticker],
    ttl=timedelta(days=1),
    schema=[
        Field(name="price_close", dtype=Float32),
        Field(name="volatility", dtype=Float32),
    ],
    online=True,
    source=batch_source,
    tags={"team": "quant"},
)
