# 工单 #008 迭代实施计划

**目标**: 完整落实工单 #008 的所有任务
**策略**: 敏捷迭代，从 MVP 到完整版，逐步实现

---

## 📋 迭代概览

| 迭代 | 目标 | 预计时间 | 状态 |
|------|------|---------|------|
| 迭代 1 | MVP - 基础数据采集 | 2 天 | 🟢 进行中 |
| 迭代 2 | 基础特征工程（30维） | 2 天 | ⚪ 待开始 |
| 迭代 3 | 高级特征工程（40维） | 3 天 | ⚪ 待开始 |
| 迭代 4 | 数据质量监控系统 | 2 天 | ⚪ 待开始 |
| 迭代 5 | 完善文档和测试 | 2 天 | ⚪ 待开始 |
| 迭代 6 | 性能优化和最终验收 | 2 天 | ⚪ 待开始 |

**总计**: 13 天（含缓冲时间）

---

## 🚀 迭代 1: MVP 版本 - 基础数据采集

### 目标
实现基础的数据采集功能，验证技术方案可行性

### 交付物

#### ✅ 已完成

1. **项目结构** ✅
   ```
   /opt/mt5-crs/
   ├── config/              # 配置文件
   │   ├── assets.yaml      # 55 个资产配置
   │   ├── features.yaml    # 特征工程配置
   │   └── news_historical.yaml  # 新闻采集配置
   ├── data_lake/           # 数据湖目录
   │   ├── news_raw/
   │   ├── news_processed/
   │   ├── price_daily/
   │   └── features_daily/
   └── src/                 # 源代码
       ├── market_data/
       │   └── price_fetcher.py         ✅ 价格采集器
       ├── sentiment_service/
       │   └── sentiment_analyzer.py    ✅ 情感分析器
       └── news_service/
           └── historical_fetcher.py    ✅ 新闻采集器
   ```

2. **核心模块** ✅
   - `PriceDataFetcher`: Yahoo Finance 价格数据采集
   - `HistoricalNewsFetcher`: 历史新闻数据采集（支持断点续拉）
   - `SentimentAnalyzer`: FinBERT 情感分析

3. **完整流程脚本** ✅
   - `bin/iteration1_data_pipeline.py`: 迭代 1 完整流程

### 技术实现

#### 1. 价格数据采集
```python
fetcher = PriceDataFetcher()
data = fetcher.fetch_multiple_symbols(symbols, start_date)
fetcher.save_to_parquet(data)
```

**特性**:
- ✅ 支持 55 个资产（股票、加密、外汇、商品、指数）
- ✅ 自动符号格式转换（AAPL.US -> AAPL）
- ✅ OHLC 逻辑验证
- ✅ 异常值检测
- ✅ Parquet 压缩存储
- ✅ 数据质量报告

#### 2. 新闻数据采集
```python
fetcher = HistoricalNewsFetcher(config)
news_df = fetcher.fetch_historical_news(start_date, end_date)
fetcher.save_to_parquet(news_df)
```

**特性**:
- ✅ 断点续拉（checkpoint）
- ✅ 智能限流（60 req/min）
- ✅ 指数退避重试（1s/2s/4s）
- ✅ 分页处理
- ✅ Ticker 提取

#### 3. 情感分析
```python
analyzer = SentimentAnalyzer(model_path, device='cpu')
news_df = analyzer.analyze_news_dataframe(news_df)
news_df = analyzer.analyze_ticker_level_sentiment(news_df)
```

**特性**:
- ✅ FinBERT 模型（ProsusAI/finbert）
- ✅ 批处理优化（batch_size=32）
- ✅ CPU/GPU 自适应
- ✅ 置信度评分
- ✅ Ticker 级别情感

### 验收标准

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 价格数据采集成功率 | > 90% | - | ⏳ 待测试 |
| 新闻数据采集（示例） | 5 条 | - | ⏳ 待测试 |
| 情感分析成功率 | > 95% | - | ⏳ 待测试 |
| 代码质量 | 可运行 | ✅ | ✅ |

### 已知限制

1. **新闻采集**：需要 EODHD API Key（当前使用示例数据）
2. **FinBERT**：首次使用会从 HuggingFace 下载模型（~400MB）
3. **依赖安装**：需要安装完整的 requirements.txt
4. **GPU**：当前服务器无 GPU，使用 CPU 推理

### 下一步（迭代 2）

- 实现基础技术指标（EMA, RSI, MACD, ATR 等）
- 整合价格 + 情感数据
- 生成特征向量

---

## 🎯 迭代 2: 基础特征工程（30维）

### 目标
实现 30 维基础技术指标特征

### 计划交付物

1. **FeatureEngineer 类**
   ```python
   class FeatureEngineer:
       def compute_basic_features(df) -> pd.DataFrame
       def merge_price_sentiment(price_df, news_df) -> pd.DataFrame
       def validate_features(df) -> dict
   ```

2. **基础特征（30 维）**
   - 趋势: EMA12/26/50/200, SMA20/60
   - 动量: RSI14, MACD, ROC, Stochastic
   - 波动: ATR14, Bollinger Bands
   - 成交量: Volume SMA, OBV
   - 回报: return_1d/3d/5d/10d/20d

3. **脚本**
   - `bin/iteration2_basic_features.py`

### 验收标准
- 30 维特征计算正确
- 特征完整率 > 99%
- 数值范围合理

---

## 🔬 迭代 3: 高级特征工程（40维）

### 目标
实现 40 维高级金融时序特征

### 计划交付物

1. **高级特征模块**
   ```python
   class AdvancedFeatures:
       def fractional_diff(series, d) -> pd.Series
       def rolling_statistics(df, windows) -> pd.DataFrame
       def cross_sectional_rank(df) -> pd.DataFrame
       def sentiment_momentum(df) -> pd.DataFrame
       def triple_barrier_labels(df) -> pd.DataFrame
   ```

2. **高级特征（40 维）**
   - Fractional Differentiation (6 维)
   - Rolling Statistics (12 维)
   - Cross-Sectional Rank (6 维)
   - Sentiment Momentum (8 维)
   - 自适应窗口 (3 维)
   - 跨资产特征 (5 维)

3. **标签体系**
   - Triple Barrier Labeling
   - 多期限回报标签

### 验收标准
- 40 维高级特征计算正确
- IC > 0.03 的特征占比 > 30%
- 标签生成成功率 100%

---

## 📊 迭代 4: 数据质量监控系统

### 目标
实现完整的数据质量监控和告警系统

### 计划交付物

1. **DQ Score 系统**
   ```python
   def calculate_dq_score(metrics) -> float:
       # 完整性 40% + 准确性 30% + 时效性 20% + 一致性 10%
       pass
   ```

2. **Prometheus 指标导出器**
   ```python
   class DataQualityExporter:
       def export_news_metrics()
       def export_price_metrics()
       def export_feature_metrics()
   ```

3. **Grafana Dashboard**
   - `etc/monitoring/grafana/dashboards/data_pipeline.json`
   - `etc/monitoring/grafana/dashboards/feature_quality.json`

4. **Prometheus 告警规则**
   - `etc/monitoring/prometheus/rules/data_alerts.yml`

### 验收标准
- Grafana Dashboard 可访问
- 告警规则生效
- DQ Score 计算准确

---

## 📚 迭代 5: 完善文档和测试

### 目标
完善文档和测试覆盖

### 计划交付物

1. **文档**
   - `docs/data_pipeline/README.md`
   - `docs/features/FEATURE_LIST_v2.md`
   - `docs/features/ADVANCED_TECHNIQUES.md`
   - `docs/monitoring/DATA_QUALITY.md`

2. **测试**
   - `tests/unit/test_feature_engineer.py`
   - `tests/integration/test_data_pipeline.py`
   - `tests/validation/test_data_quality.py`

3. **示例脚本**
   - `bin/generate_historical_features.py`
   - `bin/demo_feature_preview.py`
   - `bin/test_feature_quality.py`

### 验收标准
- 单元测试覆盖率 > 80%
- 集成测试通过率 100%
- 文档完整度 100%

---

## ⚡ 迭代 6: 性能优化和最终验收

### 目标
性能优化和最终验收

### 计划交付物

1. **性能优化**
   - Dask 并行计算
   - 增量计算优化
   - Redis 缓存

2. **最终验收**
   - 运行完整 25 项验收标准
   - 生成验收报告
   - 提交工单 #008 完成报告

### 验收标准
- 全量特征生成 < 30 分钟
- 单日增量特征生成 < 5 分钟
- 所有 25 项验收标准通过

---

## 📝 执行说明

### 迭代 1 快速开始

```bash
# 1. 安装依赖（Python 3.6+ 兼容版本）
cd /opt/mt5-crs
pip3 install --user pyyaml pandas pyarrow yfinance transformers torch tqdm

# 2. 创建必要目录
mkdir -p var/cache/models var/checkpoints var/logs var/reports

# 3. 运行迭代 1 脚本
python3 bin/iteration1_data_pipeline.py

# 4. 查看结果
cat var/reports/iteration1_report.txt
ls -lh data_lake/price_daily/
ls -lh data_lake/news_processed/
```

### 注意事项

1. **首次运行**：FinBERT 模型会自动下载（~400MB），需要良好的网络
2. **API Key**：如果有 EODHD API Key，设置环境变量：
   ```bash
   export EODHD_API_KEY="your_api_key"
   ```
3. **Python 版本**：当前服务器 Python 3.6.8，部分包版本需要调整
4. **依赖冲突**：torch 和 transformers 版本需要兼容

---

## 🎉 成功标准

### 迭代 1
- ✅ 价格数据成功采集（≥ 9 个资产）
- ✅ 新闻数据示例创建（5 条）
- ✅ 情感分析成功运行
- ✅ 生成汇总报告

### 最终（迭代 6）
- ✅ 70+ 维特征生成
- ✅ 数据质量监控上线
- ✅ 完整文档交付
- ✅ 所有验收标准通过

---

**当前状态**: 🟢 迭代 1 代码实现完成，等待测试运行

**下一步**: 运行 `iteration1_data_pipeline.py` 验证 MVP 功能
