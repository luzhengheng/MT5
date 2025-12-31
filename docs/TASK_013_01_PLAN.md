# Task #013.01: 批量特征工程管道
## 实现计划

**日期**: 2025-12-31
**协议**: v2.2 (文档即代码)
**角色**: Quant 开发者
**状态**: 进行中

---

## 1. 任务目标

### 1.1 主要目标
将 Task #012.05 摄取的原始 OHLCV 数据 (66,296 行) 转换为技术特征，存储在专用特征存储表中。

### 1.2 成功指标
- ✅ `market_features` 表创建并启用为 Hypertable
- ✅ 管道成功处理所有 7 个资产
- ✅ 生成 ~500k 特征行 (66k 原始行 × ~8 个特征)
- ✅ 查询验证特征存在 (例如: `COUNT(*) WHERE feature='rsi_14'`)
- ✅ 审计检查 33+ 通过 (Protocol v2.2)

---

## 2. 技术架构

### 2.1 数据流管道

```
market_data_ohlcv (66,296 rows)
│ 7 symbols (EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, GSPC, DJI)
│ Columns: time, symbol, open, high, low, close, volume
│
├─ [Symbol Loop: EURUSD → DJI]
│  │
│  └─ [Per-Symbol Processing]
│     │
│     ├─ Fetch OHLCV by symbol
│     ├─ Calculate Indicators
│     │  ├─ SMA (20, 50, 200)
│     │  ├─ RSI (14)
│     │  ├─ MACD (12, 26, 9) → 3 features
│     │  ├─ ATR (14)
│     │  └─ Bollinger Bands (20, 2) → 3 features
│     │  (Total: 11 features per symbol)
│     │
│     ├─ Melt/Reshape to Long Format
│     │  Format: (time, symbol, feature, value)
│     │
│     └─ Bulk Insert via COPY
│
└─ market_features (Expected: ~500k rows)
   Columns: time, symbol, feature, value
   Long format for flexibility
```

### 2.2 特征列表

| 特征类别 | 特征名 | 参数 | 说明 |
|---------|------|------|------|
| **移动平均线** | `sma_20` | 20 | 20 期简单移动平均 |
| | `sma_50` | 50 | 50 期简单移动平均 |
| | `sma_200` | 200 | 200 期简单移动平均 |
| **动量指标** | `rsi_14` | 14 | 14 期相对强度指数 |
| **趋势跟踪** | `macd_line` | (12,26) | MACD 主线 |
| | `macd_signal` | (12,26,9) | MACD 信号线 |
| | `macd_histogram` | (12,26,9) | MACD 柱状图 |
| **波动率** | `atr_14` | 14 | 14 期平均真实范围 |
| | `bb_upper` | (20,2) | Bollinger 带上轨 |
| | `bb_middle` | (20,2) | Bollinger 带中轨 (SMA) |
| | `bb_lower` | (20,2) | Bollinger 带下轨 |

**特征总数**: 11 个特征/符号

### 2.3 数据库架构

#### 目标表: `market_features`

```sql
CREATE TABLE market_features (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    feature TEXT NOT NULL,
    value DOUBLE PRECISION,

    CONSTRAINT market_features_time_symbol_feature_unique
        UNIQUE (time, symbol, feature)
);

-- 启用 TimescaleDB Hypertable
SELECT create_hypertable('market_features', 'time', if_not_exists => TRUE);

-- 优化索引
CREATE INDEX idx_market_features_symbol_time
    ON market_features (symbol, time DESC, feature);
```

#### 约束说明
- **主时间轴**: `time` (TIMESTAMPTZ) - TimescaleDB 自动分区
- **唯一约束**: `(time, symbol, feature)` - 防止重复特征
- **索引策略**: `(symbol, time DESC, feature)` - 优化按符号查询

---

## 3. 实现步骤

### 步骤 1: 文档与规划 (本文档) ✅
- ✅ 创建详细实现计划
- ✅ 定义特征列表和数据库架构
- ✅ 设计批处理逻辑流程

### 步骤 2: 数据库初始化
**文件**: `scripts/init_feature_db.py`

**功能**:
1. 连接到 TimescaleDB
2. 创建 `market_features` 表
3. 创建 Hypertable 分区
4. 创建优化索引
5. 验证表创建成功

**执行**: `python3 scripts/init_feature_db.py`

### 步骤 3: 批处理器实现
**文件**: `src/feature_engineering/batch_processor.py`

**核心功能**:
```python
class FeatureBatchProcessor:
    """批量特征处理引擎"""

    def __init__(self, db_config):
        """初始化数据库连接池"""

    async def fetch_ohlcv_by_symbol(symbol: str) -> DataFrame:
        """从 market_data_ohlcv 获取符号数据"""
        # SELECT time, open, high, low, close, volume
        # FROM market_data_ohlcv WHERE symbol = ?

    def calculate_indicators(df: DataFrame) -> DataFrame:
        """计算所有技术指标"""
        # 使用 pandas_ta 或 ta-lib
        # 返回 DataFrame with columns: [time, symbol, 11_features]

    def melt_to_long_format(df: DataFrame) -> DataFrame:
        """将宽格式转换为长格式 (EAV)"""
        # 输入: (time, symbol, sma_20, sma_50, ..., bb_lower)
        # 输出: (time, symbol, feature, value)

    async def bulk_insert_features(df_long: DataFrame) -> int:
        """使用 COPY 协议批量插入特征"""
        # 返回: 插入的行数

    async def process_symbol(symbol: str) -> tuple:
        """完整管道: 获取 → 计算 → 转换 → 插入"""
        # 返回: (rows_processed, elapsed_time)
```

**关键库**:
- `pandas_ta`: 技术指标计算
- `asyncpg`: 异步数据库操作
- `pandas`: 数据处理和转换

### 步骤 4: 执行脚本
**文件**: `scripts/run_feature_pipeline.py`

**功能**:
1. 加载 YAML 配置获取 7 个资产
2. 初始化 FeatureBatchProcessor
3. 循环处理每个符号:
   ```
   for symbol in [EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, GSPC, DJI]:
       rows, elapsed = await processor.process_symbol(symbol)
       total_rows += rows
   ```
4. 生成最终报告 (总行数、速度、错误)
5. 验证审计检查通过

**执行**: `python3 scripts/run_feature_pipeline.py`

### 步骤 5: 审计更新
**文件**: `scripts/audit_current_task.py`

**新增检查 Section 8/9**:
```python
# [8/9] TASK #013.01 特征存储审计 (关键)
checks:
    1. os.path.exists("docs/TASK_013_01_PLAN.md") ✅
    2. src.feature_engineering.batch_processor 可导入 ✅
    3. 数据库表 market_features 存在 ✅
    4. market_features 是 Hypertable ✅
    5. 表中存在特征数据 (COUNT > 0) ✅
```

---

## 4. 特征计算逻辑

### 4.1 简单移动平均 (SMA)
```python
# SMA_20 = 最后 20 期收盘价的平均值
sma_20 = df['close'].rolling(window=20).mean()
sma_50 = df['close'].rolling(window=50).mean()
sma_200 = df['close'].rolling(window=200).mean()
```

### 4.2 相对强度指数 (RSI)
```python
# RSI_14 = 100 - (100 / (1 + RS))
# 其中 RS = 平均涨幅 / 平均跌幅 (14 期)
rsi_14 = ta.momentum.rsi(df['close'], length=14)
```

### 4.3 MACD (移动平均收敛发散)
```python
# MACD 主线 = 12期EMA - 26期EMA
# MACD 信号线 = MACD主线的9期EMA
# MACD 柱状图 = MACD主线 - 信号线
macd = ta.trend.macd(df['close'], fast=12, slow=26, signal=9)
# 返回: macd_line, macd_signal, macd_histogram
```

### 4.4 平均真实范围 (ATR)
```python
# ATR_14 = 真实范围的 14 期平均
# 真实范围 = max(high - low, |high - close_prev|, |low - close_prev|)
atr_14 = ta.volatility.average_true_range(
    high=df['high'], low=df['low'], close=df['close'], length=14
)
```

### 4.5 Bollinger Bands
```python
# BB = SMA ± (标准差 × 标准差倍数)
# 使用 20期SMA, 2倍标准差
bb = ta.volatility.bollinger_bands(df['close'], length=20, std=2)
# 返回: bb_upper, bb_middle, bb_lower
```

### 4.6 长格式转换 (Melting)
```python
# 输入 (宽格式):
# time | symbol | sma_20 | sma_50 | sma_200 | rsi_14 | ... | bb_lower
#
# 输出 (长格式 EAV):
# time | symbol | feature    | value
# 2025-01-01 | EURUSD | sma_20     | 1.0850
# 2025-01-01 | EURUSD | sma_50     | 1.0840
# 2025-01-01 | EURUSD | rsi_14     | 65.32
# ...

df_long = df.melt(
    id_vars=['time', 'symbol'],
    value_vars=['sma_20', 'sma_50', 'sma_200', 'rsi_14', ...],
    var_name='feature',
    value_name='value'
)
```

---

## 5. 性能估算

### 5.1 处理规模
```
输入数据:
  - 原始行数: 66,296 (market_data_ohlcv)
  - 符号数: 7 (EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, GSPC, DJI)
  - 平均每符号: ~9,470 行

特征计算:
  - 特征数: 11 per symbol
  - 输出行数: 66,296 × 11 = ~729,256 行 (理论最大)

实际估算:
  - 去除 NaN (指标预热期): ~80% 有效
  - 预期输出: ~583,404 行
  - 目标: ~500k 行 (保守估算)
```

### 5.2 处理时间
```
单符号处理 (平均 ~9,470 行):
  - OHLCV 获取: ~500ms
  - 指标计算: ~800ms (pandas_ta 向量化)
  - 长格式转换: ~200ms (melt 操作)
  - 数据库插入: ~2秒 (COPY 协议, ~4,700 rows/sec)
  ────────────────────────────
  总计: ~3.5秒/符号

7 符号总耗时:
  - 顺序处理: ~24.5秒
  - 速率限制 (1秒间隔): +6秒
  - 数据库预热: +5秒
  ────────────────────────────
  预期总耗时: ~35-40秒
```

### 5.3 资源利用
```
内存:
  - 单符号 OHLCV: ~600KB (9,470 rows × 5 columns × 8 bytes)
  - 扩展数据 (11 features): ~7.2MB
  - 长格式 (EAV): ~8.5MB
  - 峰值内存: ~10-15MB

存储:
  - market_features 表: ~50MB (500k rows × 100 bytes/row)
  - Hypertable 索引: ~20MB
  - 总计: ~70MB
```

---

## 6. 错误处理与恢复

### 6.1 三层保护机制

**Layer 1: 符号级隔离**
```python
for symbol in symbols:
    try:
        rows, elapsed = await processor.process_symbol(symbol)
        total_rows += rows
    except Exception as e:
        logger.error(f"Symbol {symbol} failed: {e}")
        failed_symbols.append(symbol)
        # 继续处理下一个符号
```

**Layer 2: 数据库约束**
- 唯一约束 `(time, symbol, feature)` 自动防止重复
- 违反约束的行自动跳过，记录警告

**Layer 3: 批次重试**
```python
max_retries = 3
for attempt in range(max_retries):
    try:
        await processor.bulk_insert_features(df_long)
        break
    except Exception as e:
        if attempt < max_retries - 1:
            await asyncio.sleep(5 * (attempt + 1))  # 指数退避
        else:
            raise
```

### 6.2 恢复策略
- **失败符号**: 记录到日志，继续处理其他符号
- **部分插入**: 数据库约束防止不完整数据
- **幂等性**: 重新运行同一符号不会产生重复

---

## 7. 验收标准 (DoD)

### 必须满足
| # | 标准 | 状态 |
|---|------|------|
| 1 | `docs/TASK_013_01_PLAN.md` 存在 | ⏳ |
| 2 | `scripts/init_feature_db.py` 成功运行 | ⏳ |
| 3 | `market_features` Hypertable 创建 | ⏳ |
| 4 | `src/feature_engineering/batch_processor.py` 可导入 | ⏳ |
| 5 | 管道成功处理所有 7 个资产 | ⏳ |
| 6 | 特征行数: ~500k (至少 400k) | ⏳ |
| 7 | 查询验证特征存在 (rsi_14, sma_20, etc) | ⏳ |
| 8 | `audit_current_task.py` 33+ 通过 | ⏳ |
| 9 | 零错误失败 (resilience check) | ⏳ |

---

## 8. 集成点

### 与 Task #012.05 的关系
- **输入**: `market_data_ohlcv` 表 (66,296 行)
- **符号**: 相同的 7 个资产 (EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, GSPC, DJI)
- **时间范围**: 1990-01-02 ~ 2025-12-30

### 与 Feast Feature Store 的关系 (Task #042)
- **目标**: Task #013.01 创建的 `market_features` 可作为 Feast 的数据源
- **后续**: 集成到 Feast `FeatureView` 中作为动态特征

### 与实时管道的关系 (Task #012.01)
- **冷路径** (已完成): Task #012.05 + Task #013.01
- **热路径** (未来): Task #012.01 ZMQ 实时特征计算

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解策略 |
|------|------|---------|
| **pandas_ta 不可用** | 无法计算指标 | 预装依赖检查，回退至 ta-lib |
| **符号数据不完整** | 特征计算失败 | 符号级隔离，失败符号记录 |
| **数据库连接超时** | 插入失败 | 连接池配置，3 次重试机制 |
| **内存溢出** | 进程崩溃 | 流式处理，单符号一次性加载 |
| **重复特征** | 数据不一致 | 唯一约束自动去重 |

---

## 10. 后续步骤 (Protocol v2.2 执行)

1. ✅ **创建本文档** (docs/TASK_013_01_PLAN.md)
2. ⏳ **执行 init_feature_db.py** - 初始化数据库
3. ⏳ **实现 batch_processor.py** - 特征计算引擎
4. ⏳ **创建 run_feature_pipeline.py** - 管道编排
5. ⏳ **更新 audit_current_task.py** - Protocol v2.2 审计
6. ⏳ **运行管道** - 处理所有 7 个资产
7. ⏳ **验证数据** - 确认 ~500k 特征行
8. ⏳ **完成任务** - `python3 scripts/project_cli.py finish`

---

**完成日期**: 2025-12-31
**协议**: v2.2 (文档即代码)
**作者**: Claude Sonnet 4.5
**状态**: ✅ 计划完成，准备实现
